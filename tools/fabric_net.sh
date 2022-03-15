#!/usr/bin/env bash

# SPDX-License-Identifier: GPL-3.0-or-later

# fabric_net - Hyperledger fabric network, helper script.

# Copyright (C) 2022 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
# Universidad Carlos III de Madrid.

# This file is part of autoauditor.

# autoauditor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# autoauditor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with GNU Emacs.  If not, see <https://www.gnu.org/licenses/>.

_R="\033[91m"
_G="\033[92m"
_Y="\033[93m"
_B="\033[94m"
_N="\033[0m"

# Orderer/Peer listen ports: PORTS + offset
# Offsets => CA: 50, General: 0, Admin: 10, Operation: 20, Couch (Peer only): 30
declare -A PORTS=([orderer]=7000 [org1]=8000 [org2]=9000)
# Containers configuration order
ORGS=(orderer org1 org2)
declare -A CMDS=([package]=chaincode_package
                 [install]=chaincode_install
                 [installed]=chaincode_installed
                 [approve]=chaincode_approve
                 [commit]=chaincode_commit
                 [help]=chaincode_help
                 [store]=chaincode_store
                 [delete]=chaincode_delete
                 [query]=chaincode_query
                 [qhash]=chaincode_query
                 [qorg]=chaincode_query
                 [qtotalorg]=chaincode_query_org_bulk
                 [qidsorg]=chaincode_query_org_bulk
                 [qdate]=chaincode_query_date
                 [qtotaldate]=chaincode_query_date_bulk
                 [qidsdate]=chaincode_query_date_bulk)
declare -A CC_CMD=([help]=Help
                   [store]=NewReport
                   [delete]=DeleteReport
                   [query]=GetReportById
                   [qhash]=GetReportHash
                   [qorg]=GetReportsByOrganization
                   [qtotalorg]=GetTotalReportsByOrganization
                   [qidsorg]=GetReportsIdByOrganization
                   [qdate]=GetReportsByDate
                   [qtotaldate]=GetTotalReportsByDate
                   [qidsdate]=GetReportsIdByDate)
declare -A ARG=([trans]=report [trans_del]=report_delete)

OUT=/dev/null
BIN=$PWD/third_party/fabric
ROOT=$PWD/tools/fabric_net
CONFIG=$ROOT/config
NET=$ROOT/network
YAML=$ROOT/docker-compose.yaml
CA_YAML=$ROOT/docker-compose-ca.yaml

DELAY=1
MAX_RETRY=5
PEER=org1
DOMAIN=example.com
CHANNEL=channel1
PROFILE=TwoOrgsApplicationGenesis

# chaincode defaults
CC=autoauditor
CC_VER=1
CC_LANG=golang
CC_PATH=$ROOT/chaincode
CC_CFG=$CC_PATH/collections_config.json
CC_TAR=$NET/${CC}.tar.gz
CC_POLICY="OR('Org1MSP.member','Org2MSP.member')"

# chaincode query defaults
QID=report007
QORG=org1
QDATE="2020-05-21 17:37:27.910352+02:00"

log ()
{
    case $1 in
        info)
            echo -e "$_B[*]$_N $2"
            ;;
        succ)
            echo -e "$_G[+]$_N $2"
            ;;
        error)
            echo -e "$_R[!]$_N $2"
            ;;
        warn)
            echo -e "$_Y[-]$_N $2"
    esac
}

disable_ansi_color ()
{
    NO_COLOR=--no-ansi
    _R=
    _G=
    _Y=
    _B=
    _N=
}

usage ()
{
    local name=$(basename $0)
    echo "Usage:"
    echo "    $name                  Start fabric network containers if down."
    echo "    $name -d|--down        Stop containers and remove created files."
    echo "    $name -r|--restart     Restart fabric network."
    echo "    $name --anchor         Execute anchor peer functions."
    echo "    $name --no-install     Do not install autoauditor smartcontract."
    echo "    $name --store          Store test data."
    echo "    $name --query          Check test data."
    echo "    $name -P|--peer        Change default peer. D: $PEER"
    echo "    $name -C|--channel     Change default channel name. D: $CHANNEL"
    echo "    $name -V|--version     Change default smartcontract version. D: $CC_VER"
    echo "    $name -e|--exec        Execute specific command: ${!CMDS[@]}."
    echo "    $name -qi|--qid        Change default query report id. D: $QID"
    echo "    $name -qo|--qorg       Change default query org. D: $QORG"
    echo "    $name -qd|--qdate      Change default query date. D: ${QDATE:0:7}"
    echo "    $name --no-color       No ANSI colors."
    echo "    $name --verbose         Enable verbose output."
    echo "    $name -h|--help        Show this help."

    exit
}

host ()
{
    local subd
    case "$2" in
        ca)
            subd=ca
            if [[ $1 =~ org ]]; then
                subd=ca.$1
            fi
            ;;
        "")
            subd=orderer
            if [[ $1 =~ org ]]; then
                subd=peer0.$1
            fi
            ;;
    esac
    echo $subd.$DOMAIN
}

port ()
{
    case "$2" in
        ca)
            echo $((${PORTS[$1]}+50))
            ;;
        admin)
            echo $((${PORTS[$1]}+10))
            ;;
        "")
            echo $((${PORTS[$1]}))
            ;;
    esac
}

ca_org ()
{
    echo $NET/$1/peers/$(host $1)/tls/ca.crt
}

ca_ord ()
{
    local orderer_msp=$NET/orderer/orderers/$(host orderer)/msp
    echo $orderer_msp/tlscacerts/tlsca.$(host orderer)-cert.pem
}

url ()
{
    case $2 in
        ca)
            echo $(host $1 ca):$(port $1 ca)
            ;;
        admin)
            echo $(host $1):$(port $1 admin)
            ;;
        config)
            local org
            if [[ $1 =~ org ]]; then
                org=-$1
            fi
            echo ca$org-${DOMAIN/./-}-$(port $1 ca)-ca-$1
            ;;
        "")
            echo $(host $1):$(port $1)
            ;;
    esac
}

check_binaries ()
{
    log info "Checking fabric binaries"
    if [ ! -d third_party/fabric ]; then
        command -v wget > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            log error "Package not installed: wget"
            exit
        fi
        command -v tar > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            log error "Package not installed: tar"
            exit
        fi
        local bin=third_party/fabric
        mkdir -p $bin

        log warn "Downloading fabric binaries"
        wget -P $bin -q https://github.com/hyperledger/fabric/releases/download/v2.4.3/hyperledger-fabric-linux-amd64-2.4.3.tar.gz
        tar -C $bin --strip-components 1 -xf third_party/fabric/hyperledger-fabric-linux-amd64-2.4.3.tar.gz bin/configtxgen bin/osnadmin bin/peer

        log warn "Downloading fabric-ca binaries"
        wget -P $bin -q https://github.com/hyperledger/fabric-ca/releases/download/v1.5.2/hyperledger-fabric-ca-linux-amd64-1.5.2.tar.gz
        tar -C $bin --strip-components 1 -xf third_party/fabric/hyperledger-fabric-ca-linux-amd64-1.5.2.tar.gz bin/fabric-ca-client
    fi
}

check_org ()
{
    if [[ ! "${ORGS[@]/orderer}" =~ $1 ]]; then
        log error "Organization must be:${ORGS[*]/orderer}"
        exit
    fi
}

start_containers ()
{
    log info "Starting CA containers"

    # Copy CA config
    for org in ${!PORTS[@]}; do
        mkdir -p $NET/ca/$org
        cp $CONFIG/ca-config-$org.yaml $NET/ca/$org/fabric-ca-server-config.yaml
    done

    docker-compose $NO_COLOR -f $CA_YAML up -d

    # Wait until tls certificates have been generated
    shopt -s nullglob
    while true; do
        local tlscerts=($NET/ca/*/tls-cert.pem)
        if [ ${#tlscerts[@]} -ne ${#PORTS[@]} ]; then
            sleep $DELAY
        else
            break
        fi
    done

    for org in ${ORGS[@]}; do
        log info "Configuring CA: ${org^}"
        if [[ $org =~ org ]]; then
            configure_ca_peer $org > $OUT 2>&1
        else
            configure_ca_orderer $org > $OUT 2>&1
        fi
    done

    mkdir -p $NET/channel-artifacts
    mkdir -p $NET/system-genesis-block

    docker-compose $NO_COLOR -f $YAML up -d
}

stop_containers ()
{
    log info "Stopping CA containers"
    docker-compose $NO_COLOR -f $CA_YAML -f $YAML down -v
    docker run --rm -v $ROOT:/fabric_net busybox sh -c 'rm -rf /fabric_net/network'
}

set_variables ()
{
    export CORE_PEER_TLS_ENABLED=true
    export CORE_PEER_LOCALMSPID=${1^}MSP
    export CORE_PEER_ADDRESS=$(url $1)
    local net=$NET
    if [ -n "$2" ]; then
        # Called from cli container
        net=$PWD/fabric_net/network/
    fi
    export CORE_PEER_TLS_ROOTCERT_FILE=$net/$1/peers/$(host $1)/tls/ca.crt
    export CORE_PEER_MSPCONFIGPATH=$net/$1/users/admin@$1.$DOMAIN/msp
}

gen_nodeous ()
{
    echo "NodeOUs:
    Enable: true
    ClientOUIdentifier:
      Certificate: cacerts/$(url $1 config).pem
      OrganizationalUnitIdentifier: client
    PeerOUIdentifier:
      Certificate: cacerts/$(url $1 config).pem
      OrganizationalUnitIdentifier: peer
    AdminOUIdentifier:
      Certificate: cacerts/$(url $1 config).pem
      OrganizationalUnitIdentifier: admin
    OrdererOUIdentifier:
      Certificate: cacerts/$(url $1 config).pem
      OrganizationalUnitIdentifier: orderer" > $2/config.yaml
}

configure_ca_peer ()
{
    local peer_host=$(host $1)
    local org_path=$NET/$1
    local org_ca=$NET/ca/$1
    local tlscert=$org_ca/tls-cert.pem
    local org_msp=$org_path/msp
    local org_peers=$org_path/peers
    local org_users=$org_path/users
    local peer_msp=$org_peers/$peer_host/msp
    local peer_tls=$org_peers/$peer_host/tls

    export FABRIC_CA_CLIENT_HOME=$org_path

    # Enrolling CA admin
    $BIN/fabric-ca-client enroll -u https://admin:adminpw@$(url $1 ca) --caname ca-$1 --tls.certfiles $tlscert
    # Registering peer0
    $BIN/fabric-ca-client register --caname ca-$1 --id.name peer0 --id.secret peer0pw --id.type peer --tls.certfiles $tlscert
    # Registering user
    $BIN/fabric-ca-client register --caname ca-$1 --id.name user1 --id.secret user1pw --id.type client --tls.certfiles $tlscert
    # Registering admin
    $BIN/fabric-ca-client register --caname ca-$1 --id.name $1admin --id.secret $1adminpw --id.type admin --tls.certfiles $tlscert
    # Generating peer0 msp
    $BIN/fabric-ca-client enroll -u https://peer0:peer0pw@$(url $1 ca) --caname ca-$1 -M $peer_msp --csr.hosts $peer_host --tls.certfiles $tlscert

    gen_nodeous $1 $org_msp
    cp $org_msp/config.yaml $peer_msp/config.yaml

    # Generating peer0-tls certificates
    $BIN/fabric-ca-client enroll -u https://peer0:peer0pw@$(url $1 ca) --caname ca-$1 -M $peer_tls --enrollment.profile tls --csr.hosts $peer_host --csr.hosts $(host $1 ca) --tls.certfiles $tlscert

    cp $peer_tls/tlscacerts/tls-$(url $1 config).pem $peer_tls/ca.crt
    cp $peer_tls/signcerts/cert.pem $peer_tls/server.crt
    cp $peer_tls/keystore/*_sk $peer_tls/server.key

    mkdir -p $org_msp/tlscacerts
    cp $peer_tls/tlscacerts/tls-$(url $1 config).pem $org_msp/tlscacerts/ca.crt

    mkdir -p $org_path/tlsca
    cp $peer_tls/tlscacerts/tls-$(url $1 config).pem $org_path/tlsca/tlsca.$1.$DOMAIN-cert.pem

    mkdir -p $org_path/ca
    cp $peer_msp/cacerts/$(host $1 ca)-$(port $1 ca).pem $org_path/ca/ca.$1.$DOMAIN-cert.pem

    # Generating user msp
    $BIN/fabric-ca-client enroll -u https://user1:user1pw@$(url $1 ca) --caname ca-$1 -M $org_users/user1@$1.$DOMAIN/msp --tls.certfiles $tlscert
    cp $org_users/user1@$1.$DOMAIN/msp/keystore/*_sk $org_users/user1@$1.$DOMAIN/msp/keystore/priv_sk
    cp $org_msp/config.yaml $org_users/user1@$1.$DOMAIN/msp/config.yaml

    # Generating admin msp
    $BIN/fabric-ca-client enroll -u https://$1admin:$1adminpw@$(url $1 ca) --caname ca-$1 -M $org_users/admin@$1.$DOMAIN/msp --tls.certfiles $tlscert
    cp $org_msp/config.yaml $org_users/admin@$1.$DOMAIN/msp/config.yaml
}

configure_ca_orderer ()
{
    local ord_host=$(host $1)
    local ord_path=$NET/$1
    local ord_ca=$NET/ca/$1
    local tlscert=$ord_ca/tls-cert.pem
    local ord_msp=$ord_path/msp
    local ord_ords=$ord_path/orderers
    local ord_users=$ord_path/users
    local orderer_msp=$ord_ords/$ord_host/msp
    local orderer_tls=$ord_ords/$ord_host/tls

    export FABRIC_CA_CLIENT_HOME=$ord_path

    # Enrolling CA admin
    $BIN/fabric-ca-client enroll -u https://admin:adminpw@$(url $1 ca) --caname ca-$1 --tls.certfiles $tlscert
    # Registering orderer
    $BIN/fabric-ca-client register --caname ca-$1 --id.name orderer --id.secret ordererpw --id.type orderer --tls.certfiles $tlscert
    # Registering admin
    $BIN/fabric-ca-client register --caname ca-$1 --id.name $1admin --id.secret $1adminpw --id.type admin --tls.certfiles $tlscert
    # Generating orderer msp
    $BIN/fabric-ca-client enroll -u https://orderer:ordererpw@$(url $1 ca) --caname ca-$1 -M $orderer_msp --csr.hosts $ord_host --tls.certfiles $tlscert

    gen_nodeous $1 $ord_msp
    cp $ord_msp/config.yaml $orderer_msp/config.yaml

    # Generating orderer-tls certificates
    $BIN/fabric-ca-client enroll -u https://orderer:ordererpw@$(url $1 ca) --caname ca-$1 -M $orderer_tls --enrollment.profile tls --csr.hosts $ord_host --csr.hosts $(host $1 ca) --tls.certfiles $tlscert

    cp $orderer_tls/tlscacerts/tls-$(url $1 config).pem $orderer_tls/ca.crt
    cp $orderer_tls/signcerts/cert.pem $orderer_tls/server.crt
    cp $orderer_tls/keystore/*_sk $orderer_tls/server.key

    mkdir -p $orderer_msp/tlscacerts
    cp $orderer_tls/tlscacerts/tls-$(url $1 config).pem $orderer_msp/tlscacerts/tlsca.$1.$DOMAIN-cert.pem

    mkdir -p $ord_msp/tlscacerts
    cp $orderer_tls/tlscacerts/tls-$(url $1 config).pem $ord_msp/tlscacerts/tlsca.$1.$DOMAIN-cert.pem

    # Generating admin msp
    $BIN/fabric-ca-client enroll -u https://$1admin:$1adminpw@$(url $1 ca) --caname ca-$1 -M $ord_users/admin@$1.$DOMAIN/msp --tls.certfiles $tlscert
    cp $ord_msp/config.yaml $ord_users/admin@$1.$DOMAIN/msp/config.yaml
}

create_channel ()
{
    local block=$NET/channel-artifacts/$CHANNEL.block
    local orderer_tls=$NET/orderer/orderers/$(host orderer)/tls
    local ord_adm_cert=$orderer_tls/server.crt
    local ord_adm_key=$orderer_tls/server.key

	$BIN/configtxgen -profile $PROFILE -outputBlock $block -channelID $CHANNEL
    if [ $? -ne 0 ]; then
        log error "Channel configuration transaction could not be generated"
    fi

    set_variables $1

	local res=1
	local cnt=1
	while [ $res -ne 0 ] && [ $cnt -lt $MAX_RETRY ]; do
		$BIN/osnadmin channel join --channelID $CHANNEL --config-block $block -o $(url orderer admin) --ca-file $(ca_ord) --client-cert $ord_adm_cert --client-key $ord_adm_key
		res=$?
		cnt=$(($cnt+1))
        sleep $DELAY
	done
    if [ $res -ne 0 ]; then
        log error "Channel could not be created"
    fi
}

join_channel ()
{
    local block=$NET/channel-artifacts/$CHANNEL.block

    set_variables $1

    local res=1
	local cnt=1
	while [ $res -ne 0 ] && [ $cnt -lt $MAX_RETRY ]; do
        $BIN/peer channel join -b $block
		res=$?
		cnt=$(($cnt+1))
        sleep $DELAY
	done
    if [ $res -ne 0 ]; then
	    log error "$(host $1) could not join channel $CHANNEL after $MAX_RETRY attempts"
    fi
}

set_anchor_peer ()
{
    if [ $OUT == /dev/tty ]; then
        verbose=--verbose
    fi
    docker exec autoauditor_cli ./fabric_net.sh --anchor --peer $1 --channel $2 $verbose
}

cli_anchor_peer ()
{
    local org=$1
    local channel=$2
    local ord_msp=$PWD/fabric_net/network/orderer/orderers/$(host orderer)/msp
    local ord_tls=$PWD/fabric_net/network/orderer/orderers/$(host orderer)/tls
    local ord_tlscacert=$ord_msp/tlscacerts/tlsca.$(host orderer)-cert.pem
    local out=${CORE_PEER_LOCALMSPID}config.json
    local outm=${CORE_PEER_LOCALMSPID}modified_config.json
    local anchortx=${CORE_PEER_LOCALMSPID}anchors.tx

    set_variables $org cli

    log info "Fetching the most recent configuration block for the channel $channel"
    peer channel fetch config config_block.pb -o $(url orderer) --ordererTLSHostnameOverride $(host orderer) -c $channel --tls --cafile $ord_tlscacert

    log info "Decoding config block to JSON and isolating config to $out"
    configtxlator proto_decode --input config_block.pb --type common.Block --output config_block.json
    jq .data.data[0].payload.data.config config_block.json > $out

    log info "Generating anchor peer update transaction for ${org^} on channel $channel"
    jq '.channel_group.groups.Application.groups.'${CORE_PEER_LOCALMSPID}'.values += {"AnchorPeers":{"mod_policy": "Admins","value":{"anchor_peers": [{"host": "'$(host $org)'","port": '$(port $org)'}]},"version": "0"}}' $out > $outm

    # Compute a config update, based on the differences between config.json and modified_config.json, write it as a transaction to anchors.tx
    configtxlator proto_encode --input $out --type common.Config --output original_config.pb
    configtxlator proto_encode --input $outm --type common.Config --output modified_config.pb
    configtxlator compute_update --channel_id $channel --original original_config.pb --updated modified_config.pb --output config_update.pb
    configtxlator proto_decode --input config_update.pb --type common.ConfigUpdate --output config_update.json
    echo '{"payload":{"header":{"channel_header":{"channel_id":"'$channel'", "type":2}},"data":{"config_update":'$(cat config_update.json)'}}}' | jq . > config_update_in_envelope.json
    configtxlator proto_encode --input config_update_in_envelope.json --type common.Envelope --output $anchortx

    peer channel update -o $(url orderer) --ordererTLSHostnameOverride $(host orderer) -c $channel -f $anchortx --tls --cafile $ord_tlscacert
}

chaincode_exec ()
{
    local cmd=${CMDS[$2]}
    if [ -z "$cmd" ]; then
        log error "Command must be: ${!CMDS[*]}"
        exit
    fi

    $cmd $1 $2 $3 $4
}

chaincode_package ()
{
    set_variables $1

    $BIN/peer lifecycle chaincode package $CC_TAR --path $CC_PATH \
              --lang $CC_LANG --label ${CC}_$CC_VER

    local otype=error
    if [ $? -eq 0 ]; then
        otype=succ
    fi
    log $otype "Command: peer lifecycle chaincode package, CC: $CC, TAR: $CC_TAR"
}

chaincode_install ()
{
    set_variables $1

    local otype=error
    $BIN/peer lifecycle chaincode install $CC_TAR
    if [ $? -eq 0 ]; then
        otype=succ
    fi
    log $otype "Command: peer lifecycle chaincode install, TAR: $CC_TARC, PEER: $1"
}

chaincode_installed ()
{
    set_variables $1

    local otype=error
    $BIN/peer lifecycle chaincode queryinstalled | grep ${CC}_$CC_VER
    if [ $? -eq 0 ]; then
        otype=succ
    fi
    log $otype "Command: peer lifecycle chaincode queryinstalled, CC: $CC, PEER: $1"
}

chaincode_approve ()
{
    set_variables $1

    local pkgid=$($BIN/peer lifecycle chaincode queryinstalled | grep -Eo "${CC}_${CC_VER}:[a-z0-9]+")
    local otype=error
    $BIN/peer lifecycle chaincode approveformyorg \
              -o $(url orderer) \
              --ordererTLSHostnameOverride $(host orderer) \
              --channelID $CHANNEL --name $CC \
              --version $CC_VER --sequence $CC_VER --package-id $pkgid \
              --signature-policy $CC_POLICY \
              --collections-config $CC_CFG \
              --tls --cafile $(ca_ord)
    if [ $? -eq 0 ]; then
        otype=succ
    fi
    log $otype "Command: peer lifecycle chaincode approveformyorg, CC: $CC, PEER: $1"
}

chaincode_commit ()
{
    set_variables $1

    local otype=error
    $BIN/peer lifecycle chaincode commit \
              -o $(url orderer) \
              --ordererTLSHostnameOverride $(host orderer) \
              --channelID $CHANNEL --name $CC \
              --version $CC_VER  --sequence $CC_VER \
              --signature-policy $CC_POLICY \
              --collections-config $CC_CFG \
              --tls --cafile $(ca_ord) \
              --peerAddresses $(url org1) \
              --tlsRootCertFiles $(ca_org org1) \
              --peerAddresses $(url org2) \
              --tlsRootCertFiles $(ca_org org2)
    if [ $? -eq 0 ]; then
        otype=succ
    fi
    log $otype "Command: peer lifecycle chaincode commit, CC: $CC, PEER: $1"
}

chaincode_help ()
{
    set_variables $1

    local otype=error
    local out=$($BIN/peer chaincode query -C $CHANNEL -n $CC \
                          -c "{\"Args\":[\"${CC_CMD[help]}\"]}")
    if [ -n "$out" ]; then
        otype=succ
    fi
    log $otype "Command: ${CC_CMD[help]}, PEER: $1"
    echo $out
}

_invoke ()
{
    local otype=error
    $BIN/peer chaincode invoke \
              -o $(url orderer) \
              --ordererTLSHostnameOverride $(host orderer) \
              --tls --cafile $(ca_ord) \
              -C $CHANNEL -n $CC \
              -c "{\"Args\":[\"$2\"]}" \
              --transient "{\"$3\":\"$4\"}" \
              --peerAddresses $(url org1) \
              --tlsRootCertFiles $(ca_org org1) \
              --peerAddresses $(url org2) \
              --tlsRootCertFiles $(ca_org org2)
    if [ $? -eq 0 ]; then
        otype=succ
    fi
    log $otype "Command: $2, Transient: $3, ORG: $1"
    echo $4 | base64 -d && echo
}

chaincode_store ()
{
    set_variables $1

    local rep=$(echo -n "{\"id\": \"$QID\", \"org\": \"$QORG\", \"date\": \"$QDATE\", \"nVuln\": 5, \"report\": \"public_report\"}" | base64 | tr -d \\n)
    local priv=$(echo -n "{\"id\": \"$QID\", \"org\": \"$QORG\", \"date\": \"$QDATE\", \"nVuln\": 5, \"report\": \"private_report\", \"private\": true}" | base64 | tr -d \\n)

    _invoke $1 ${CC_CMD[$2]} ${ARG[trans]} $rep
    _invoke $1 ${CC_CMD[$2]} ${ARG[trans]} $priv
}

_query ()
{
    local q_cmd
    local q_msg
    if [ $# -eq 3 ]; then
        q_cmd="{\"Args\":[\"$2\", \"$3\"]}"
        q_msg="($3)"
    elif [ $# -eq 4 ]; then
        q_cmd="{\"Args\":[\"$2\", \"$3\", \"$4\"]}"
        q_msg="($3, $4)"
    else
        q_cmd="{\"Args\":[\"$2\", \"$3\", \"$4\", \"$5\"]}"
        q_msg="($3, $4, $5)"
    fi
    local otype=error
    local errorf=/tmp/autoauditor.sc.error
    local okf=/tmp/autoauditor.sc.output
    $BIN/peer chaincode query -C $CHANNEL -n $CC \
              -c "$q_cmd" \
              --peerAddresses $(url org1) \
              --tlsRootCertFiles $(ca_org org1) > $okf 2> $errorf
    if [ -s $okf ]; then
        otype=succ
    fi
    log $otype "Command: $2, ARGS: $q_msg, ORG: $1"
    if [ $otype == succ ]; then
        cat $okf
    else
        cat $errorf
    fi
}

chaincode_query ()
{
    set_variables $1

    _query $1 ${CC_CMD[$2]} $3
    _query $1 ${CC_CMD[$2]} $3 public
    _query $1 ${CC_CMD[$2]} $3 private
}

chaincode_query_org_bulk ()
{
    set_variables $1

    _query $1 ${CC_CMD[$2]} $3
}

chaincode_query_date ()
{
    set_variables $1

    _query $1 ${CC_CMD[$2]} $3
    _query $1 ${CC_CMD[$2]} $3 public
    _query $1 ${CC_CMD[$2]} $3 private

    _query $1 ${CC_CMD[$2]} $3 $4
    _query $1 ${CC_CMD[$2]} $3 $4 public
    _query $1 ${CC_CMD[$2]} $3 $4 private
}

chaincode_query_date_bulk ()
{
    set_variables $1

    _query $1 ${CC_CMD[$2]} $3
    _query $1 ${CC_CMD[$2]} $3 $4
}

network_up ()
{
    check_binaries
    start_containers
    log info "Creating channel '$CHANNEL'"
    create_channel org1

    log info "Joining Org1 to channel '$CHANNEL'"
    join_channel org1

    log info "Joining Org2 to channel '$CHANNEL'"
    join_channel org2

    log info "Setting anchor peer for Org1 on channel '$CHANNEL'"
    set_anchor_peer org1 $CHANNEL

    log info "Setting anchor peer for Org2 on channel '$CHANNEL'"
    set_anchor_peer org2 $CHANNEL
}

smartcontract_install ()
{
    log info "Installing autoauditor smartcontract"
    chaincode_exec org1 package
    chaincode_exec org1 install
    chaincode_exec org2 install
    chaincode_exec org1 installed
    chaincode_exec org2 installed
    chaincode_exec org1 approve
    chaincode_exec org2 approve
    chaincode_exec org1 commit

    log warn "Waiting processing"
    # Transaction process time
    sleep 3
}

smartcontract_store ()
{
    log info "Storing test data as org1"
    chaincode_exec org1 store

    log warn "Waiting processing"
    # Transaction process time
    sleep 3
}

smartcontract_query ()
{
    log info "Querying test data as org1"
    chaincode_exec org1 query $QID
    chaincode_exec org1 qhash $QID
    chaincode_exec org1 qorg $QORG
    chaincode_exec org1 qtotalorg $QORG
    chaincode_exec org1 qidsorg $QORG
    chaincode_exec org1 qdate ${QDATE:0:7} $QORG
    chaincode_exec org1 qtotaldate ${QDATE:0:7} $QORG
    chaincode_exec org1 qidsdate ${QDATE:0:7} $QORG

    echo
    log info "Querying test data as org2"
    chaincode_exec org2 query $QID
    chaincode_exec org2 qhash $QID
    chaincode_exec org2 qorg $QORG
    chaincode_exec org2 qtotalorg $QORG
    chaincode_exec org2 qidsorg $QORG
    chaincode_exec org2 qdate ${QDATE:0:7} $QORG
    chaincode_exec org2 qtotaldate ${QDATE:0:7} $QORG
    chaincode_exec org2 qidsdate ${QDATE:0:7} $QORG
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--down)
            _down=SET
            shift
            ;;
        -r|--restart)
            _restart=SET
            shift
            ;;
        --anchor)
            _anchor=SET
            shift
            ;;
        --no-install)
            _no_install=SET
            shift
            ;;
        --store)
            _store=SET
            shift
            ;;
        --query)
            _query=SET
            shift
            ;;
        -P|--peer)
            PEER=$2
            shift
            shift
            check_org $PEER
            ;;
        -C|--channel)
            CHANNEL=$2
            shift
            shift
            ;;
        -V|--version)
            CC_VER=$2
            shift
            shift
            ;;
        -e|--exec)
            _exec=$2
            shift
            shift
            ;;
        -qi|--qid)
            QID=$2
            shift
            shift
            ;;
        -qo|--qorg)
            QORG=$2
            shift
            shift
            check_org $QORG
            ;;
        -qd|--qdate)
            QDATE=$2
            shift
            shift
            ;;
        --no-color)
            disable_ansi_color
            shift
            ;;
        --verbose)
            OUT=/dev/tty
            shift
            ;;
        --debug)
            set -x
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            usage
            ;;
    esac
done

export FABRIC_CFG_PATH=$CONFIG

if [ -n "$_down" ]; then
    stop_containers
elif [ -n "$_anchor" ]; then
    export FABRIC_CFG_PATH=$PWD/fabric_net/config
    cli_anchor_peer $PEER $CHANNEL
elif [ -n "$_exec" ]; then
    if [ $_exec == query ] || [ $_exec == qhash ]; then
        chaincode_exec $PEER $_exec $QID
    elif [ $_exec == qdate ] || [ $_exec == qtotaldate ] || [ $_exec == qidsdate ]; then
        chaincode_exec $PEER $_exec ${QDATE:0:7} $QORG
    else
        chaincode_exec $PEER $_exec $QORG
    fi
else
    if [ -n "$_restart" ]; then
        stop_containers
        network_up
    else
        up=($(docker ps -aq --filter label=autoauditor=fabric_net))
        cnt=$(docker-compose -f $CA_YAML -f $YAML ps --services | wc -l)
        if [ ${#up[@]} -ne $cnt ]; then
            network_up
        fi
    fi
    if [ -z "$_no_install" ]; then
        smartcontract_install
    fi
    if [ -n "$_store" ]; then
        smartcontract_store
    fi
    if [ -n "$_query" ]; then
        smartcontract_query
    fi
fi
