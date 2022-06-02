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
declare -A PORTS=([orderer]=7000 [org1]=8000 [org2]=9000 [org3]=10000)
# Containers configuration order
ORGS=(orderer org1 org2 org3)
SCMDS=(package install installed approve commit
       help
       store delete
       query qhash
       qall qtotalall qidsall
       qorg qtotalorg qidsorg
       qdate qtotaldate qidsdate
       sub unsub
       qsubs qtotalsubs qidssubs
       qsubsid qcertid
       qsubsorg qtotalsubsorg qidssubsorg
       publishdisc qdisc
       qdiscs qtotaldiscs qhashdiscs)
declare -A CMDS=([package]=chaincode_package
                 [install]=chaincode_install
                 [installed]=chaincode_installed
                 [approve]=chaincode_approve
                 [commit]=chaincode_commit
                 [help]=chaincode_help
                 [store]=chaincode_store
                 [delete]=chaincode_delete
                 [query]=chaincode_query_1arg_and_rep_dbs
                 [qhash]=chaincode_query_1arg_and_rep_dbs
                 [qall]=chaincode_query_0args_and_rep_dbs
                 [qtotalall]=chaincode_query_0args
                 [qidsall]=chaincode_query_0args
                 [qorg]=chaincode_query_1arg_and_rep_dbs
                 [qtotalorg]=chaincode_query_1arg
                 [qidsorg]=chaincode_query_1arg
                 [qdate]=chaincode_query_1and2args_and_rep_dbs
                 [qtotaldate]=chaincode_query_1and2args
                 [qidsdate]=chaincode_query_1and2args
                 [sub]=chaincode_subscribe
                 [unsub]=chaincode_subscribe
                 [qsubs]=chaincode_query_0args
                 [qtotalsubs]=chaincode_query_0args
                 [qidssubs]=chaincode_query_0args
                 [qsubsid]=chaincode_query_1arg
                 [qcertid]=chaincode_query_1arg
                 [qsubsorg]=chaincode_query_1arg
                 [qtotalsubsorg]=chaincode_query_1arg
                 [qidssubsorg]=chaincode_query_1arg
                 [publishdisc]=chaincode_publish
                 [qdisc]=chaincode_query_1arg
                 [qdiscs]=chaincode_query_0args
                 [qtotaldiscs]=chaincode_query_0args
                 [qhashdiscs]=chaincode_query_0args)
declare -A CC_CMD=([help]=Help
                   [store]=StoreReport
                   [delete]=DeleteReport
                   [qall]=GetReports
                   [qtotalall]=GetTotalReports
                   [qidsall]=GetReportsId
                   [query]=GetReportById
                   [qhash]=GetReportHashById
                   [qorg]=GetReportsByOrganization
                   [qtotalorg]=GetTotalReportsByOrganization
                   [qidsorg]=GetReportsIdByOrganization
                   [qdate]=GetReportsByDate
                   [qtotaldate]=GetTotalReportsByDate
                   [qidsdate]=GetReportsIdByDate
                   [sub]=Subscribe
                   [unsub]=Unsubscribe
                   [qsubs]=GetSubscribers
                   [qtotalsubs]=GetTotalSubscribers
                   [qidssubs]=GetSubscribersId
                   [qsubsid]=GetSubscriberById
                   [qcertid]=GetCertificateById
                   [qsubsorg]=GetSubscribersByOrganization
                   [qtotalsubsorg]=GetTotalSubscribersByOrganization
                   [qidssubsorg]=GetSubscribersIdByOrganization
                   [publishdisc]=PublishDisclosure
                   [qdisc]=GetDisclosureByHash
                   [qdiscs]=GetDisclosures
                   [qtotaldiscs]=GetTotalDisclosures
                   [qhashdiscs]=GetDisclosuresHash)
declare -A ARG=([trans]=report_st [trans_del]=report_del)

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
CCS=(report whistleblower)
CC_VER=1
CC_LANG=golang

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

check_chaincode ()
{
    if [[ ! "${CCS[@]}" =~ $1( |$) ]]; then
        local ccs=$(echo "${CCS[@]}" | sed 's/ /, /g')
        log error "Chaincode must be: $ccs"
        exit 1
    fi
}

chaincode_update ()
{
    check_chaincode $1
    CC=$1
    CC_PATH=$ROOT/smart_contracts/$CC
    if [ "$CC" = "report" ]; then
        CC_CFG="--collections-config $CC_PATH/collections_config.json"
    else
        CC_CFG=
    fi
    CC_TAR=$NET/${CC}.tar.gz
}

chaincode_update report

# chaincode query defaults
QID=report007
QORG=Org1MSP
QDATE="2020-05-21 17:37:27.910352+02:00"
# QSID from user1@Org1MSP
QSID="eDUwOTo6Q049dXNlcjEsT1U9Y2xpZW50LE89SHlwZXJsZWRnZXIsU1Q9Tm9ydGggQ2Fyb2xpbmEsQz1VUzo6Q049Y2Eub3JnMS5leGFtcGxlLmNvbSxPPW9yZzEuZXhhbXBsZS5jb20sTD1MZWdhbmVzLFNUPUNvbXVuaWRhZCBkZSBNYWRyaWQsQz1FUw=="
DISC="encryptedDisclosure"
# echo -n "encryptedDisclosure" | sha256sum
QDHASH="08dfc3eac27e0c4c2f992f8c619314fdc81ad0f0a3dc0a0ca7bcbfe912c546c9"

disable_ansi_color ()
{
    NO_COLOR=--no-ansi
    _R=
    _G=
    _Y=
    _B=
    _N=
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

peers_agree ()
{
    if [ "$1" = "query" ]; then
        if [ "$CC" = "report" ]; then
            echo "--peerAddresses $(url org1) --tlsRootCertFiles $(ca_org org1)"
        else
            echo "--peerAddresses $(url org3) --tlsRootCertFiles $(ca_org org3)"
        fi
    else
        if [ "$CC" = "report" ]; then
            echo "--peerAddresses $(url org1) --tlsRootCertFiles $(ca_org org1) --peerAddresses $(url org2) --tlsRootCertFiles $(ca_org org2)"
        else
            echo "--peerAddresses $(url org1) --tlsRootCertFiles $(ca_org org1) --peerAddresses $(url org3) --tlsRootCertFiles $(ca_org org3)"
        fi
    fi
}

empty_argument ()
{
    if [[ $1 == -* ]] || [ -z "$1" ]; then
        echo 0
    else
        echo 1
    fi
}

check_argument ()
{
    if [[ $2 == -* ]] || [ -z "$2" ]; then
        log error "Parameter $1 requires an argument"
        exit 1
    fi
}

check_binaries ()
{
    log info "Checking fabric binaries"
    if [ ! -d third_party/fabric ]; then
        command -v wget > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            log error "Package not installed: wget"
            exit 1
        fi
        command -v tar > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            log error "Package not installed: tar"
            exit 1
        fi
        local bin=third_party/fabric
        mkdir -p $bin

        log warn "Downloading fabric binaries"
        wget -P $bin -q https://github.com/hyperledger/fabric/releases/download/v2.4.0/hyperledger-fabric-linux-amd64-2.4.0.tar.gz
        tar -C $bin --strip-components 1 -xf third_party/fabric/hyperledger-fabric-linux-amd64-2.4.0.tar.gz bin/configtxgen bin/osnadmin bin/peer

        log warn "Downloading fabric-ca binaries"
        wget -P $bin -q https://github.com/hyperledger/fabric-ca/releases/download/v1.5.2/hyperledger-fabric-ca-linux-amd64-1.5.2.tar.gz
        tar -C $bin --strip-components 1 -xf third_party/fabric/hyperledger-fabric-ca-linux-amd64-1.5.2.tar.gz bin/fabric-ca-client
    fi
}

check_org ()
{
    if [[ ! "${ORGS[@]/orderer}" =~ $1( |$) ]]; then
        local org=$(echo "${ORGS[@]/orderer}" | sed 's/ // ; s/ /, /g')
        log error "Peer organization must be: $org"
        exit 1
    fi
}

check_org_msp ()
{
    local msp=$(echo "${ORGS[@]/orderer}" | sed 's/ // ; s/org\([0-9]\)/Org\1MSP/g')
    if [[ ! "$msp" =~ $1( |$) ]]; then
        local cmsp=$(echo "$msp" | sed 's/ /, /g')
        log error "Query organization must be: $cmsp"
        exit 1
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
    if [ "$2" = "cli" ]; then
        # Called from cli container
        net=$PWD/fabric_net/network/
    fi
    export CORE_PEER_TLS_ROOTCERT_FILE=$net/$1/peers/$(host $1)/tls/ca.crt

    if [ "$2" = "user" ]; then
        export CORE_PEER_MSPCONFIGPATH=$net/$1/users/user1@$1.$DOMAIN/msp
    else
        export CORE_PEER_MSPCONFIGPATH=$net/$1/users/admin@$1.$DOMAIN/msp
    fi
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
    # Registering user1
    $BIN/fabric-ca-client register --caname ca-$1 --id.name user1 --id.secret user1pw --id.type client --tls.certfiles $tlscert
    # Registering user2
    $BIN/fabric-ca-client register --caname ca-$1 --id.name user2 --id.secret user2pw --id.type client --tls.certfiles $tlscert
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

    # Generating user1 msp
    $BIN/fabric-ca-client enroll -u https://user1:user1pw@$(url $1 ca) --caname ca-$1 -M $org_users/user1@$1.$DOMAIN/msp --tls.certfiles $tlscert
    cp $org_users/user1@$1.$DOMAIN/msp/keystore/*_sk $org_users/user1@$1.$DOMAIN/msp/keystore/priv_sk
    cp $org_msp/config.yaml $org_users/user1@$1.$DOMAIN/msp/config.yaml

    # Generating user2 msp
    $BIN/fabric-ca-client enroll -u https://user2:user2pw@$(url $1 ca) --caname ca-$1 -M $org_users/user2@$1.$DOMAIN/msp --tls.certfiles $tlscert
    cp $org_users/user2@$1.$DOMAIN/msp/keystore/*_sk $org_users/user2@$1.$DOMAIN/msp/keystore/priv_sk
    cp $org_msp/config.yaml $org_users/user2@$1.$DOMAIN/msp/config.yaml

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
        log error "Command '$2' not found. Command must be: ${!CMDS[*]}"
        exit 1
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
              $CC_CFG \
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
              $CC_CFG \
              --tls --cafile $(ca_ord) \
              $(peers_agree)
    if [ $? -eq 0 ]; then
        otype=succ
    fi
    log $otype "Command: peer lifecycle chaincode commit, CC: $CC, PEER: $1"
}

_cc_invoke ()
{
    if [ $# -eq 2 ]; then
        q_cmd="{\"Args\":[\"$2\"]}"
        q_msg="none"
    elif [ $# -eq 3 ]; then
        q_cmd="{\"Args\":[\"$2\", \"$3\"]}"
        q_msg="($3)"
    fi
    local otype=error
    $BIN/peer chaincode invoke \
              -o $(url orderer) \
              --ordererTLSHostnameOverride $(host orderer) \
              --tls --cafile $(ca_ord) \
              -C $CHANNEL -n $CC \
              -c "$q_cmd" \
              $(peers_agree)
    if [ $? -eq 0 ]; then
        otype=succ
    fi
    log $otype "Command: $2, ARGS: $q_msg, ORG: $1"
}

_cc_invoke_trans ()
{
    local otype=error
    $BIN/peer chaincode invoke \
              -o $(url orderer) \
              --ordererTLSHostnameOverride $(host orderer) \
              --tls --cafile $(ca_ord) \
              -C $CHANNEL -n $CC \
              -c "{\"Args\":[\"$2\"]}" \
              --transient "{\"$3\":\"$4\"}" \
              $(peers_agree)
    if [ $? -eq 0 ]; then
        otype=succ
    fi
    log $otype "Command: $2, Transient: $3, ORG: $1"
    echo $4 | base64 -d && echo
}

chaincode_store ()
{
    set_variables $1 user

    local rep=$(echo -n "{\"rid\": \"$QID\", \"date\": \"$QDATE\", \"nVuln\": 5, \"report\": \"public_report\"}" | base64 | tr -d \\n)
    local priv=$(echo -n "{\"rid\": \"$QID\", \"date\": \"$QDATE\", \"nVuln\": 5, \"report\": \"private_report\", \"private\": true}" | base64 | tr -d \\n)

    _cc_invoke_trans $1 ${CC_CMD[$2]} ${ARG[trans]} $rep
    _cc_invoke_trans $1 ${CC_CMD[$2]} ${ARG[trans]} $priv
}

chaincode_delete ()
{
    set_variables $1 user

    local rep=$(echo -n "{\"rid\": \"$QID\"}" | base64 | tr -d \\n)

    _cc_invoke_trans $1 ${CC_CMD[$2]} ${ARG[trans_del]} $rep
}

chaincode_subscribe ()
{
    set_variables $1 user

    _cc_invoke $1 ${CC_CMD[$2]}
}

chaincode_publish ()
{
    set_variables $1 user

    _cc_invoke $1 ${CC_CMD[$2]} $3
}

_cc_query ()
{
    local q_cmd
    local q_msg
    if [ $# -eq 2 ]; then
        q_cmd="{\"Args\":[\"$2\"]}"
        q_msg="none"
    elif [ $# -eq 3 ]; then
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
              -c "$q_cmd" $(peers_agree query)> $okf 2> $errorf
    if [ -s $okf ]; then
        otype=succ
    fi
    log $otype "Command: $2, ARGS: $q_msg, ORG: $1"
    if [ $otype == succ ]; then
        if [ -n "$PRETTY" ] &&
               [ "$2" != "GetReportHash" ] &&
               [ "$2" != "GetCertificateById" ]; then
            jq . $okf
        else
            cat $okf
        fi
    else
        cat $errorf
    fi
}

chaincode_help ()
{
    set_variables $1 user

    _cc_query $1 help
}

chaincode_query_0args ()
{
    set_variables $1 user

    _cc_query $1 ${CC_CMD[$2]}
}

chaincode_query_0args_and_rep_dbs ()
{
    set_variables $1 user

    _cc_query $1 ${CC_CMD[$2]}
    _cc_query $1 ${CC_CMD[$2]} public
    _cc_query $1 ${CC_CMD[$2]} private
}


chaincode_query_1arg ()
{
    set_variables $1 user

    _cc_query $1 ${CC_CMD[$2]} $3
}

chaincode_query_1arg_and_rep_dbs ()
{
    set_variables $1 user

    _cc_query $1 ${CC_CMD[$2]} $3
    _cc_query $1 ${CC_CMD[$2]} $3 public
    _cc_query $1 ${CC_CMD[$2]} $3 private
}

chaincode_query_1and2args ()
{
    set_variables $1 user

    _cc_query $1 ${CC_CMD[$2]} $3
    _cc_query $1 ${CC_CMD[$2]} $3 $4
}

chaincode_query_1and2args_and_rep_dbs ()
{
    set_variables $1 user

    _cc_query $1 ${CC_CMD[$2]} $3
    _cc_query $1 ${CC_CMD[$2]} $3 public
    _cc_query $1 ${CC_CMD[$2]} $3 private

    _cc_query $1 ${CC_CMD[$2]} $3 $4
    _cc_query $1 ${CC_CMD[$2]} $3 $4 public
    _cc_query $1 ${CC_CMD[$2]} $3 $4 private
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
    log info "Joining Org3 to channel '$CHANNEL'"
    join_channel org3

    log info "Setting anchor peer for Org1 on channel '$CHANNEL'"
    set_anchor_peer org1 $CHANNEL
    log info "Setting anchor peer for Org2 on channel '$CHANNEL'"
    set_anchor_peer org2 $CHANNEL
    log info "Setting anchor peer for Org3 on channel '$CHANNEL'"
    set_anchor_peer org3 $CHANNEL
}

smartcontract_install ()
{
    log info "Installing report chaincode"
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

    log info "Installing whistleblower chaincode"
    chaincode_update whistleblower
    chaincode_exec org3 package
    chaincode_exec org1 install
    chaincode_exec org3 install
    chaincode_exec org1 installed
    chaincode_exec org3 installed
    chaincode_exec org1 approve
    chaincode_exec org3 approve
    chaincode_exec org3 commit

    log warn "Waiting processing"
    # Transaction process time
    sleep 3
}

smartcontract_fill_report ()
{
    log info "Storing test data as org1"
    chaincode_exec org1 store

    log warn "Waiting processing"
    # Transaction process time
    sleep 3
}

smartcontract_query_report ()
{
    log info "Querying test data as org1"
    chaincode_exec org1 query $QID
    chaincode_exec org1 qhash $QID
    chaincode_exec org1 qall
    chaincode_exec org1 qtotalall
    chaincode_exec org1 qidsall
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
    chaincode_exec org2 qall
    chaincode_exec org2 qtotalall
    chaincode_exec org2 qidsall
    chaincode_exec org2 qorg $QORG
    chaincode_exec org2 qtotalorg $QORG
    chaincode_exec org2 qidsorg $QORG
    chaincode_exec org2 qdate ${QDATE:0:7} $QORG
    chaincode_exec org2 qtotaldate ${QDATE:0:7} $QORG
    chaincode_exec org2 qidsdate ${QDATE:0:7} $QORG
}

smartcontract_fill_whistleblower ()
{
    log info "Subscribing org1 to receive disclosures"
    chaincode_exec org1 sub

    log info "Publishing disclosure as org3"
    chaincode_exec org3 publishdisc $DISC

    log warn "Waiting processing"
    # Transaction process time
    sleep 3
}

smartcontract_query_whistleblower ()
{
    log info "Querying test data as org3"
    chaincode_exec org3 qsubs
    chaincode_exec org3 qtotalsubs
    chaincode_exec org3 qidssubs
    chaincode_exec org3 qsubsid $QSID
    chaincode_exec org3 qcertid $QSID
    chaincode_exec org3 qsubsorg $QORG
    chaincode_exec org3 qtotalsubsorg $QORG
    chaincode_exec org3 qidssubsorg $QORG
    chaincode_exec org3 qdiscs
    chaincode_exec org3 qtotaldiscs
    chaincode_exec org3 qhashdiscs
    chaincode_exec org3 qdisc $QDHASH
}

usage ()
{
    local name=$(basename $0)
    local peer=$(echo "${ORGS[@]/orderer}" | sed 's/ // ; s/ /, /g')
    local msp=$(echo "${ORGS[@]/orderer}" | sed 's/ // ; s/org\([0-9]\)/Org\1MSP/g ; s/ /, /g')
    local cc=$(echo "${CCS[@]}" | sed 's/ /, /g')
    local cmds=$(echo "${SCMDS[@]}" | sed 's/ /, /g')
    echo "Usage:"
    echo "    $name                       Start fabric network containers if down"
    echo "    $name -d|--down             Stop containers and remove created files"
    echo "    $name -r|--restart          Restart fabric network"
    echo "    $name --anchor              Execute anchor peer functions"
    echo "    $name --no-install          Skip chaincode install"
    echo "    $name --fill CC             Fill CC with test data. Def: $CC. CC: $cc"
    echo "    $name --query CC            Query CC test data. Def: $CC. CC: $cc"
    echo "    $name -P|--peer P           Set peer. Def: $PEER. P: $peer"
    echo "    $name -CC|--chaincode CC    Set chaincode. Def: $CC. CC: $cc"
    echo "    $name -C|--channel C        Set channel. Def: $CHANNEL. C: $CHANNEL"
    echo "    $name -V|--version V        Set chaincode version. Def: $CC_VER"
    echo "    $name -D|--disc DISC        Set disclosure. Def: $DISC"
    echo "    $name -e|--exec CMD         Execute command: $cmds"
    echo "    $name -qi|--qid QID         Set query report id. Def: $QID"
    echo "    $name -qo|--qorg QORG       Set query org. Def: $QORG. QORG: $msp"
    echo "    $name -qd|--qdate QDATE     Set query date. Def: ${QDATE:0:7}"
    echo "    $name -qsi|--qsid QSID      Set query subscriber id. Def: ${QSID::10}...${QSID: -10}"
    echo "    $name -qdh|--qdhash QDHASH  Set query disclosure hash. Def: ${QDHASH::10}...${QDHASH: -10}"
    echo "    $name --no-color            No ANSI colors"
    echo "    $name --pretty              Show prettified output. Requires jq"
    echo "    $name --verbose             Enable verbose output"
    echo "    $name -h|--help             Show this help"

    if [ -n "$1" ]; then
        exit $1
    fi
    exit
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
        --fill)
            arg=1
            if [ $(empty_argument $2) -eq 0 ]; then
                _fill_whistleblower=SET
                _fill_report=SET
            else
                check_chaincode $2
                if [ "$2" = "whistleblower" ]; then
                    _fill_whistleblower=SET
                else
                    _fill_report=SET
                fi
                arg=2
            fi
            shift $arg
            ;;
        --query)
            arg=1
            if [ $(empty_argument $2) -eq 0 ]; then
                _query_whistleblower=SET
                _query_report=SET
            else
                check_chaincode $2
                if [ "$2" = "whistleblower" ]; then
                    _query_whistleblower=SET
                else
                    _query_report=SET
                fi
                arg=2
            fi
            shift $arg
            ;;
        -P|--peer)
            check_argument $1 $2
            PEER=$2
            shift 2
            check_org $PEER
            ;;
        -CC|--chaincode)
            check_argument $1 $2
            chaincode_update $2
            shift 2
            ;;
        -C|--channel)
            check_argument $1 $2
            CHANNEL=$2
            shift 2
            ;;
        -V|--version)
            check_argument $1 $2
            CC_VER=$2
            shift 2
            ;;
        -D|--disc)
            check_argument $1 $2
            DISC=$2
            shift 2
            ;;
        -e|--exec)
            check_argument $1 $2
            _exec=$2
            shift 2
            ;;
        -qi|--qid)
            check_argument $1 $2
            QID=$2
            shift 2
            ;;
        -qo|--qorg)
            check_argument $1 $2
            QORG=$2
            shift 2
            check_org_msp $QORG
            ;;
        -qd|--qdate)
            check_argument $1 $2
            QDATE=$2
            shift 2
            ;;
        -qsi|--qsid)
            check_argument $1 $2
            QSID=$2
            shift 2
            ;;
        -qdh|--qdhash)
            check_argument $1 $2
            QDHASH=$2
            shift 2
            ;;
        --no-color)
            disable_ansi_color
            shift
            ;;
        --pretty)
            command -v jq > /dev/null 2>&1
            [[ $? -eq 0 ]] \
                && PRETTY=SET \
                    || log warn "Package 'jq' not installed. Ignoring --pretty."
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
            log error "Parameter $1 not recognized"
            usage 1
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
    elif [ $_exec == qsubid ] || [ $_exec == qcertid ]; then
        chaincode_exec $PEER $_exec $QSID
    elif [ $_exec == publishdisc ]; then
        chaincode_exec $PEER $_exec $DISC
    elif [ $_exec == qdisc ]; then
        chaincode_exec $PEER $_exec $QDHASH
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
    if [ -n "$_fill_report" ]; then
        chaincode_update report
        smartcontract_fill_report
    fi
    if [ -n "$_query_report" ]; then
        chaincode_update report
        smartcontract_query_report
    fi
    if [ -n "$_fill_whistleblower" ]; then
        chaincode_update whistleblower
        smartcontract_fill_whistleblower
    fi
    if [ -n "$_query_whistleblower" ]; then
        chaincode_update whistleblower
        smartcontract_query_whistleblower
    fi
fi
