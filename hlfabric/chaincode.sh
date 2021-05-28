#!/bin/bash

export PATH=${PWD}/bin:${PWD}:$PATH
export FABRIC_CFG_PATH=$PWD/groupsig/config/
export CORE_PEER_TLS_ENABLED=true

RED="\033[0;91m[!] ERROR:"
GREEN="\033[0;92m[+] SUCCESS:"
BLUE="\033[94m[*] INFO:"
NC="\033[0m"

URL=localhost:
PORT=(["orderer"]=7050 ["allsafe"]=8051 ["ecorp"]=9051)

CHANNEL_NAME="evidences"

CC_RUN_LANG=golang
CC_PATH=chaincode/
CC_CFG=${CC_PATH}/collections_config.json
CC_NAME=autoauditor
CC_TAR=${CC_NAME}.tar.gz
CC_VER=1
CC_POLICY="OR('allsafeMSP.member','ecorpMSP.member')"

ORDERER="orderer.deus-group.com"
ORDERER_CA=${PWD}/organizations/ordererOrganizations/deus-group.com/orderers/orderer.deus-group.com/msp/tlscacerts/tlsca.deus-group.com-cert.pem

declare -A FN=(["help"]="Help" ["store"]="NewReport" ["delete"]="DeleteReport" ["hash"]="GetReportHash" ["id"]="GetReportById"
               ["org"]="GetReportsByOrganization" ["torg"]="GetTotalReportsByOrganization" ["orgid"]="GetReportsIdByOrganization"
               ["date"]="GetReportsByDate" ["tdate"]="GetTotalReportsByDate" ["dateid"]="GetReportsIdByDate")

T_STORE="report"
T_DELETE="report_delete"

tls ()
{
    echo ${PWD}/groupsig/organizations/peerOrganizations/${1}.com/peers/peer0.${1}.com/tls/ca.crt
}

msp ()
{
    echo ${PWD}/groupsig/organizations/peerOrganizations/${1}.com/users/Admin@${1}.com/msp
}

set_globals ()
{
    export CORE_PEER_LOCALMSPID="${1}MSP"
    export CORE_PEER_TLS_ROOTCERT_FILE=$(tls $1)
    export CORE_PEER_MSPCONFIGPATH=$(msp $1)
    export CORE_PEER_ADDRESS=$URL${PORTS[$1]}
}

execute ()
{
    case $1 in
        help) command=show_help ;;
        pack) command=pack_cc ;;
        install) command=install_cc ;;
        installed) command=installed_cc ;;
        approve) command=approve_cc_definition ;;
        commit) command=commit_cc_definition ;;
        store) command=store ;;
        delete) command=delete ;;
        queryhash) command=query_hash ;;
        queryid) command=query_id ;;
        queryorg) command=query_org ;;
        querytorg) command=query_torg ;;
        queryorgid) command=query_orgid ;;
        querydate) command=query_date ;;
        querytdate) command=query_tdate ;;
        querydateid) command=query_dateid ;;
        *) echo -e "$RED Invalid command.$NC"; usage 1;;
    esac

    case $2 in
        all) $command allsafe; $command ecorp ;;
        allsafe) $command allsafe ;;
        ecorp) $command ecorp ;;
        *) echo -e "$RED Invalid organization.$NC"; usage 1 ;;
    esac
}

show_help ()
{
    set_globals $1
    fn=${FN["help"]}

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$fn\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "$prefix $fn -> $1.$NC"
}

pack_cc ()
{
    set_globals $1

    peer lifecycle chaincode package $CC_TAR \
        --path $CC_PATH \
        --lang $CC_RUN_LANG \
        --label ${CC_NAME}_$CC_VER

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED

    echo -e "$prefix Package ($CC_NAME) -> $CC_TAR.$NC"
}

install_cc ()
{
    set_globals $1

    peer lifecycle chaincode install $CC_TAR

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED
    echo -e "$prefix Install ($CC_NAME) -> $1.$NC"
}

installed_cc ()
{
    set_globals $1

    peer lifecycle chaincode queryinstalled | grep ${CC_NAME}_$CC_VER

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED
    echo -e "$prefix QueryInstalled ($CC_NAME) -> $1.$NC"
}

approve_cc_definition ()
{
    set_globals $1

    export CC_PKG_ID=$(peer lifecycle chaincode queryinstalled | grep -Eo "${CC_NAME}_${CC_VER}:[a-z0-9]+")

    peer lifecycle chaincode approveformyorg \
        -o $URL${PORT["orderer"]} \
        --ordererTLSHostnameOverride $ORDERER \
        --channelID $CHANNEL_NAME \
        --name $CC_NAME \
        --version $CC_VER \
        --sequence $CC_VER \
        --collections-config $CC_CFG \
        --signature-policy $CC_POLICY \
        --package-id $CC_PKG_ID \
        --tls true \
        --cafile $ORDERER_CA

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED
    echo -e "$prefix ApproveDefinition ($CC_NAME) -> $1.$NC"
}

commit_cc_definition ()
{
    set_globals $1

    peer lifecycle chaincode commit \
        -o $URL${PORT["orderer"]} \
        --ordererTLSHostnameOverride $ORDERER \
        --channelID $CHANNEL_NAME \
        --name $CC_NAME \
        --version $CC_VER \
        --sequence $CC_VER \
        --collections-config $CC_CFG \
        --signature-policy $CC_POLICY \
        --tls true \
        --cafile $ORDERER_CA \
        --peerAddresses $URL${PORT["allsafe"]} \
        --tlsRootCertFiles $(tls "allsafe") \
        --peerAddresses $URL${PORT["ecorp"]} \
        --tlsRootCertFiles $(tls "ecorp")

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED
    echo -e "$prefix Commit ($CC_NAME) -> $1.$NC"
}

_invoke ()
{
    peer chaincode invoke \
         -o $URL${PORT["orderer"]} \
         --ordererTLSHostnameOverride $ORDERER \
         --tls \
         --cafile $ORDERER_CA \
         -C $CHANNEL_NAME \
         -n $CC_NAME \
         -c "{\"Args\":[\"$1\"]}" \
         --transient "{\"$2\":\"$3\"}"

    [[ $? -eq 0 ]] \
        && echo $REPORTPRIVATE | base64 -d && echo "" && prefix=$GREEN \
            || prefix=$RED

    echo -e "$prefix $1 (Transient: report::$4) -> $1.${NC}"
}

store ()
{
    set_globals $1

    rep=$(echo -n "{\"id\": \"$id\", \"org\": \"$org\", \"date\": \"${date:0:7}\", \"nvuln\": 5, \"report\": \"dummy_report\"}" | base64 | tr -d \\n)
    _invoke ${FN["store"]} $T_STORE $REP "report (public)"

    priv=$(echo -n "{\"id\": \"$id\", \"private\": true, \"org\": \"$org\", \"date\": \"$date\", \"nvuln\": 5, \"report\": \"dummy_report_priv\"}" | base64 | tr -d \\n)
    _invoke ${FN["store"]} $T_STORE $PRIV "report (private)"
}

delete ()
{
    set_globals $1

    del=$(echo -n "{\"id\":\"$id\"}" | base64 | tr -d \\n)
    _invoke ${FN["delete"]} $T_DELETE $del "report_delete"
}

_query ()
{
    if [ $# -eq 2 ]; then
        q_cmd="{\"Args\":[\"$1\", \"$2\"]}"
        q_msg="($2)"
    elif [ $# -eq 3 ]; then
        q_cmd="{\"Args\":[\"$1\", \"$2\", \"$3\"]}"
        q_msg="($2, $3)"
    else
        q_cmd="{\"Args\":[\"$1\", \"$2\", \"$3\", \"$4\"]}"
        q_msg="($2, $3, $4)"
    fi
    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c $q_cmd)

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "$prefix $1 $q_msg -> $1.${NC}"
}

query_hash ()
{
    set_globals $1

    _query${FN["hash"]} $id
    _query${FN["hash"]} $id "public"
    _query${FN["hash"]} $id "private"
}

query_id ()
{
    set_globals $1

    _query${FN["id"]} $id
    _query${FN["id"]} $id "public"
    _query${FN["id"]} $id "private"
}

query_org ()
{
    set_globals $1

    _query${FN["org"]} $org
    _query${FN["org"]} $org "public"
    _query${FN["org"]} $org "private"
}

query_torg ()
{
    set_globals $1

    _query${FN["torg"]} $org
}

query_orgid ()
{
    set_globals $1

    _query${FN["orgid"]} $org
}

query_date ()
{
    set_globals $1

    _query${FN["date"]} ${date:0:7}
    _query${FN["date"]} ${date:0:7} "public"
    _query${FN["date"]} ${date:0:7} "private"

    _query${FN["date"]} ${date:0:7} $org
    _query${FN["date"]} ${date:0:7} $org "public"
    _query${FN["date"]} ${date:0:7} $org "private"
}

query_tdate ()
{
    set_globals $1

    _query${FN["tdate"]} ${date:0:7}
    _query${FN["tdate"]} ${date:0:7} $org
}

query_dateid ()
{
    set_globals $1

    _query${FN["dateid"]} ${date:0:7}
    _query${FN["dateid"]} ${date:0:7} $org
}

query_all ()
{
    execute queryhash $node
    execute queryid $node
    execute queryorg $node
    execute querytorg $node
    execute queryorgid $node
    execute querydate $node
    execute querytdate $node
    execute querydateid $node
}

usage ()
{
    echo "Usage: $0 [MODE] FLAGS [BC_OPTIONS|CMD_OPTIONS]"
    echo "    -h, --help          Show this help."
    echo ""
    echo "MODE:"
    echo "    -u, --up            Network up."
    echo "    -d, --down          Network down."
    echo ""
    echo "FLAGS:"
    echo "    -a, --all           Pack, install, approve and commit chaincode."
    echo "    -c, --cmd           Execute given CMD from peer NODE."
    echo "    -q, --query         Execute QUERY functions."
    echo "    -s, --store         Execute STORE function."
    echo ""
    echo "BC_OPTIONS:"
    echo "    -f, --fill          Fill blockchain with test data."
    echo "    -m, --ccname        Chaincode name."
    echo "    -p, --ccpath        Chaincode path."
    echo "    -g, --cccfg         Chaincode collection config path."
    echo "    -v, --ccver         Chaincode version."
    echo ""
    echo "COMMANDS:"
    echo "     help               Show $CC_NAME chaincode functions."
    echo "     pack               Pack $CC_NAME chaincode."
    echo "     install            Install $CC_NAME chaincode."
    echo "     installed          Retrieve installed chaincodes in peer."
    echo "     approve            Approve $CC_NAME chaincode definition."
    echo "     commit             Commit $CC_NAME chaincode definition."
    echo "     store              Store report."
    echo "     delete             Delete report."
    echo "     queryhash          Query report hash."
    echo "     queryid            Query report."
    echo "     queryorg           Query reports by organization."
    echo "     querytorg          Query total reports by organization."
    echo "     queryorgid         Query reports ids by organization."
    echo "     querydate          Query reports by date [, organization]."
    echo "     querytdate         Query total reports by date [, organization]."
    echo "     querydateid        Query reports ids by date [, organization]."
    echo ""
    echo "CMD_OPTIONS:"
    echo "    -n                  Peer node. Possible values: all, allsafe, ecorp."
    echo "    -i                  Report ID. Format: sha256."
    echo "    -o                  Organization. Possible values: allsafe, ecorp."
    echo "    -t                  Date. Format: yyyy-mm-dd."
    echo ""
    exit $1
}

start ()
{
    ./network.sh up createChannel -s couchdb # > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "$RED Network -> ./network.sh up createChannel -s couchdb.$NC"
        exit 1
    fi
}

stop ()
{
    ./network.sh down # > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "$RED Network -> ./network.sh down.$NC"
        exit 1
    fi
}

network_up ()
{
    echo -e "$BLUE Starting Hyperledger Fabric Groupsig Network.$NC"
    start
    echo -e "$BLUE Starting docker-resolver container.$NC"
    docker run --rm -d --name docker-resolver -v /var/run/docker.sock:/tmp/docker.sock -v /etc/hosts:/tmp/hosts dvdarias/docker-hoster > /dev/null
}

network_down ()
{
    echo -e "$BLUE Stopping Hyperledger Fabric Groupsig Network.$NC"
    stop
    echo -e "$BLUE Stopping docker-resolver container.$NC"
    docker container stop docker-resolver > /dev/null
    exit
}


if [[ $1 == "-u" || $1 == "--up" ]]; then
    network_up
    shift
elif [[ $1 == "-d" || $1 == "--down" ]]; then
    network_down
elif [[ $1 == "-h" || $1 == "--help" ]]; then
    usage
fi

node=all
id=report007
org=allsafe
date="2020-05-21 17:37:27.910352+02:00"
f_cnt=0

while [[ $# -gt 0 ]]; do
    key=$1
    case "$key" in
        -a|--all)
            deploy=YES; ((f_cnt=f_cnt+1))
            shift
            ;;
        -c|--cmd)
            cmd=$2; ((f_cnt=f_cnt+1))
            shift
            shift
            ;;
        -q|--query)
            query=YES; ((f_cnt=f_cnt+1))
            shift
            ;;
        -s|--store)
            store=YES; ((f_cnt=f_cnt+1))
            shift
            ;;
        -f|--fill)
            fill=YES
            shift
            ;;
        -m|--ccname)
            CC_NAME=$2; CC_TAR=${CC_NAME}.tar.gz;
            shift
            shift
            ;;
        -p|--ccpath)
            CC_PATH=$2
            shift
            shift
            ;;
        -g|--cccfg)
            CC_CFG=$2
            shift
            shift
            ;;
        -v|--ccver)
            CC_VER=$2
            shift
            shift
            ;;
        -n|--node)
            node=$2
            shift
            shift
            ;;
        -i|--id)
            id=$2
            shift
            shift
            ;;
        -o|--org)
            org=$2
            shift
            shift
            ;;
        -t|--date)
            date=$2
            shift
            shift
            ;;
        *) shift ;;
    esac
done

if [[ $f_cnt -eq 0 ]]; then
    echo -e "$RED -a/-c/-q/-s required.\n$NC"
    usage 1
elif [[ $f_cnt -gt 1 ]]; then
    echo -e "$RED -a/-c/-q/-s are mutually exclusive.\n$NC"
    usage 1
fi

if [[ $node != all && $node != allsafe && $node != ecorp ]]; then
    echo -e "$RED NODE must be all, allsafe or ecorp.\n$NC"
    usage 1
fi

if [[ -n $all ]]; then
    execute pack allsafe
    execute install all
    execute installed all
    execute approve all
    execute commit allsafe
    if [[ -n $fill ]]; then
        echo -e "$BLUE Waiting transactions processing.$NC";
        sleep 3 # wait time to process transaction
        execute store allsafe
        echo -e "$BLUE Waiting transactions processing.$NC;"
        sleep 3 # wait time to process transaction
        query_all
    fi
elif [[ -n $cmd ]]; then
    execute $cmd $node $id $org $date
elif [[ -n $query ]]; then
    query_all
elif [[ -n $store ]]; then
    execute store allsafe $id $org $date
fi
