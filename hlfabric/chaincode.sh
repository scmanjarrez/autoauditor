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

declare -A FN=(["help"]="Help" ["store"]="NewReport" ["delete"]="DeleteReport" ["hash"]="GetReportHash" ["id"]="GetReportById"
               ["org"]="GetReportsByOrganization" ["torg"]="GetTotalReportsByOrganization" ["orgid"]="GetReportsIdByOrganization"
               ["date"]="GetReportsByDate" ["tdate"]="GetTotalReportsByDate" ["dateid"]="GetReportsIdByDate")

T_STORE="report"
T_DELETE="report_delete"


export ORDERER_CA=${PWD}/organizations/ordererOrganizations/deus-group.com/orderers/orderer.deus-group.com/msp/tlscacerts/tlsca.deus-group.com-cert.pem

tls () {
    echo ${PWD}/groupsig/organizations/peerOrganizations/${1}.com/peers/peer0.${1}.com/tls/ca.crt
}

msp () {
    echo ${PWD}/groupsig/organizations/peerOrganizations/${1}.com/users/Admin@${1}.com/msp
}

set_globals ()
{
    export CORE_PEER_LOCALMSPID="${1}MSP"
    export CORE_PEER_TLS_ROOTCERT_FILE=$(tls $1)
    export CORE_PEER_MSPCONFIGPATH=$(msp $1)
    export CORE_PEER_ADDRESS=$URL${PORTS[$1]}
}

execute_as ()
{
    case "$1" in
        package) command=package_chaincode ;;
        installed) command=installed_chaincode ;;
        install) command=install_chaincode ;;
        approve) command=approve_chaincode_definition ;;
        commit) command=commit_chaincode_definition ;;
        store) command=store_data ;;
        help) command=show_help ;;
        query) command=query_data ;;
        queryhash) command=query_data_hash ;;
        queryorg) command=query_data_org ;;
        querytotalorg) command=query_total_data_org ;;
        queryorgids) command=query_data_org_ids ;;
        querydate) command=query_data_date ;;
        querytotaldate) command=query_total_data_date ;;
        querydateids) command=query_data_date_ids ;;
        delete) command=delete_data ;;
        *) echo -e "$RED Invalid command: package, install, approve, store, query, queryhash\n" \
                "\t   queryorg, querytotalorg, queryorgids, querydate, querytotaldate, querydateids, delete.$NC"; exit 1 ;;
    esac

    case "$2" in
        all) "$command" "allsafe" "$3" "$4" "$5"; "$command" "ecorp" "$3" "$4" "$5" ;;
        allsafe) "$command" "allsafe" "$3" "$4" "$5" ;;
        ecorp) "$command" "ecorp" "$3" "$4" "$5" ;;
        *) echo -e "$RED Invalid organization: all, allsafe, ecorp.$NC"; exit 1 ;;
    esac
}

show_help ()
{
    set_globals $1

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_HELP\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "$prefix $FN_HELP -> $1.$NC"
}

package_chaincode ()
{
    as_allsafe

    peer lifecycle chaincode package $CC_TAR \
        --path $CC_PATH \
        --lang $CC_RUN_LANG \
        --label ${CC_NAME}_$CC_VER

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED

    echo -e "$prefix Package ($CC_NAME) -> $CC_TAR.$NC"
}

install_chaincode ()
{
    set_globals $1

    peer lifecycle chaincode install $CC_TAR

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED
    echo -e "$prefix Install ($CC_NAME) -> $1.$NC"
}

installed_chaincode ()
{
    set_globals $1

    peer lifecycle chaincode queryinstalled | grep ${CC_NAME}_$CC_VER

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED
    echo -e "$prefix QueryInstalled ($CC_NAME) -> $1.$NC"
}

approve_chaincode_definition ()
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

commit_chaincode_definition ()
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

invoke () {
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

store_data ()
{
    set_globals $1

    id=$2
    org=$3
    date=$4

    rep=$(echo -n "{\"id\": \"$id\", \"org\": \"$org\", \"date\": \"${date:0:7}\", \"nvuln\": 5, \"report\": \"dummy_report\"}" | base64 | tr -d \\n)
    invoke ${FN["store"]} $T_STORE $REP "report (public)"

    priv=$(echo -n "{\"id\": \"$id\", \"private\": true, \"org\": \"$org\", \"date\": \"$date\", \"nvuln\": 5, \"report\": \"dummy_report_priv\"}" | base64 | tr -d \\n)
    invoke ${FN["store"]} $T_STORE $PRIV "report (private)"
}

delete_data ()
{
    set_globals $1
    id=$2

    del=$(echo -n "{\"id\":\"$id\"}" | base64 | tr -d \\n)

    invoke ${FN["delete"]} $T_DELETE $del "report_delete"
}

query () {
    if [ $# -eq 2 ]; then
        cmd="{\"Args\":[\"$1\", \"$2\"]}"
        msg="($2)"
    elif [ $# -eq 3 ]; then
        cmd="{\"Args\":[\"$1\", \"$2\", \"$3\"]}"
        msg="($2, $3)"
    else
        cmd="{\"Args\":[\"$1\", \"$2\", \"$3\", \"$4\"]}"
        msg="($2, $3, $4)"
    fi
    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c $cmd)

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "$prefix $1 $msg -> $1.${NC}"
}

query_data ()
{
    set_globals $1

    id=$2

    query ${FN["id"]} $id
    query ${FN["id"]} $id "public"
    query ${FN["id"]} $id "private"
}

query_data_hash ()
{
    set_globals $1

    id=$2

    query ${FN["query"]} $id
    query ${FN["query"]} $id "public"
    query ${FN["query"]} $id "private"
}

query_data_org ()
{
    set_globals $1
    org=$3

    query ${FN["org"]} $org
    query ${FN["org"]} $org "public"
    query ${FN["org"]} $org "private"
}

query_total_data_org ()
{
    set_globals $1
    org=$3

    query ${FN["torg"]} $org
}

query_data_org_ids ()
{
    set_globals $1
    org=$3

    query ${FN["orgid"]} $org
}

query_data_date ()
{
    set_globals $1
    org=$3
    date=${4:0:7}

    query ${FN["date"]} $date
    query ${FN["date"]} $date "public"
    query ${FN["date"]} $date "private"

    query ${FN["date"]} $date $org
    query ${FN["date"]} $date $org "public"
    query ${FN["date"]} $date $org "private"
}

query_total_data_date ()
{
    set_globals $1
    org=$3
    date=${4:0:7}

    query ${FN["tdate"]} $date
    query ${FN["tdate"]} $date $org
}

query_data_date_ids ()
{
    set_globals $1
    org=$3
    date=${4:0:7}

    query ${FN["dateid"]} $date
    query ${FN["dateid"]} $date $org
}

usage ()
{
    echo "Usage:"
    echo "    $0 -h"
    echo "                             (Help): Show this help."
    echo ""
    echo "    $0 -u"
    echo "                             (Up): Test network up."
    echo ""
    echo "    $0 -d"
    echo "                             (Down): Test network down."
    echo ""
    echo "    $0 -a"
    echo "                             (All): Pack, install, approve and commit chaincode."
    echo ""
    echo "    $0 -f"
    echo "                             (Fill): Fill blockchain with test data."
    echo ""
    echo "    $0 -c CMD -n NODE [-i ID] [-o ORG] [-t date]"
    echo "                             (Command): Execute given CMD from peer NODE."
    echo ""
    echo "    $0 -q"
    echo "                             (Query): Execute QUERY functions."
    echo ""
    echo "    $0 -s"
    echo "                             (Store): Execute STORE function."
    echo ""
    echo "    $0 -m"
    echo "                             (naMe): Change chaincode name."
    echo ""
    echo "    $0 -p"
    echo "                             (Path): Change chaincode path."
    echo ""
    echo "    $0 -g"
    echo "                             (confiG): Modify chaincode collection config path."
    echo ""
    echo "    $0 -v"
    echo "                             (Version): Change chaincode version."
    echo ""
    echo "Commands:"
    echo "       -c help               Show $CC_NAME chaincode functions."
    echo "       -c package            Pack $CC_NAME chaincode."
    echo "       -c install            Install $CC_NAME chaincode."
    echo "       -c installed          Retrieve installed chaincodes in peer."
    echo "       -c approve            Approve $CC_NAME chaincode definition."
    echo "       -c commit             Commit $CC_NAME chaincode definition."
    echo "       -c store              Store report."
    echo "       -c query              Query report."
    echo "       -c queryhash          Query report hash."
    echo "       -c queryorg           Query reports by organization."
    echo "       -c querytotalorg      Query total reports by organization."
    echo "       -c queryorgids        Query reports ids by organization."
    echo "       -c querydate          Query reports by date [, organization]."
    echo "       -c querytotaldate     Query total reports by date [, organization]."
    echo "       -c querydateids       Query reports id by date [, organization]."
    echo "       -c delete             Delete report."
    echo ""
    echo "Nodes:"
    echo "       -n all                Execute command from all peers."
    echo "       -n allsafe            Execute command from allsafe peer."
    echo "       -n ecorp              Execute command from ecorp peer."
    exit
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

network_up () {
    echo -e "$BLUE Starting Hyperledger Fabric Groupsig Network.$NC"
    start
    echo -e "$BLUE Starting docker-resolver container.$NC"
    docker run --rm -d --name docker-resolver -v /var/run/docker.sock:/tmp/docker.sock -v /etc/hosts:/tmp/hosts dvdarias/docker-hoster > /dev/null
}

network_down () {
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

while [[ $# -gt 0 ]]; do
    key=$1
    case "$key" in
        -a|--all)
            deploy=YES
            shift
            ;;
        -f|--fill)
            fill=YES
            shift
            ;;
        -c|--cmd)
            cmd=$2
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
        -q|--query)
            query=YES
            shift
            ;;
        -s|--store)
            store=YES
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
    esac
done

# while getopts ":ac:o:hudfi:qv:g:p:n:sm:t:" opt; do
#     case ${opt} in
#         u) up="yes" ;;
#         d) down="yes" ;;
#         a) all="yes" ;;
#         f) full="yes" ;;
#         c) cmd=$OPTARG ;;
#         o) org=$OPTARG ;;
#         i) queryid=$OPTARG ;;

#         q) query="yes" ;;
#         s) store="yes" ;;
#         m) companyid=$OPTARG ;;
#         t) date=$OPTARG ;;
#         v) CC_VER=$OPTARG ;;
#         g) CC_CFG=$OPTARG ;;
#         n) CC_NAME=$OPTARG;CC_TAR="${CC_NAME}.tar.gz" ;;
#         p) CC_PATH=$OPTARG ;;
#         h) usage;;
#         \?) usage;;
#     esac
# done

# if [ -z "$queryid" ]; then
#     queryid="report007"
# fi

# if [ -z "$companyid" ]; then
#     companyid="allsafe"
# fi

# if [ -z "$date" ]; then
#     date="2020-05-21 17:37:27.910352+02:00"
# fi

# if [ -z "$org" ]; then
#     org="all"
# fi

# if [ -n "$store" ]; then
#     execute_as "store" "allsafe" "$queryid" "$companyid" "$date"
# fi

# if [ -n "$query" ]; then
#     execute_as "query" "$org" "$queryid"
#     execute_as "queryhash" "$org" "$queryid"
#     execute_as "queryorg" "$org" "$queryid" "$companyid"
#     execute_as "querytotalorg" "$org" "$queryid" "$companyid"
#     execute_as "queryorgids" "$org" "$queryid" "$companyid"
#     execute_as "querydate" "$org" "$queryid" "$companyid" "$date"
#     execute_as "querytotaldate" "$org" "$queryid" "$companyid" "$date"
#     execute_as "querydateids" "$org" "$queryid" "$companyid" "$date"
#     exit
# fi

# if [ -n "$cmd" ]; then
#     execute_as "$cmd" "$org" "$queryid" "$companyid" "$date"
#     exit
# fi


# if [ -n "$all" ]; then
#     execute_as "package" "allsafe"
#     execute_as "install" "all"
#     execute_as "installed" "all"
#     execute_as "approve" "all"
#     execute_as "commit" "allsafe"
#     if [ -z "$raw" ]; then
#         echo -e "$BLUE Waiting transactions processing.$NC"; sleep 3 # wait time to process transaction
#         execute_as "store" "allsafe" "$queryid" "$companyid" "$date"
#         echo -e "$BLUE Waiting transactions processing.$NC"; sleep 3 # wait time to process transaction
#         execute_as "query" "$org" "$queryid"
#         execute_as "queryhash" "$org" "$queryid"
#         execute_as "queryorg" "$org" "$queryid" "$companyid"
#         execute_as "querytotalorg" "$org" "$queryid" "$companyid"
#         execute_as "queryorgids" "$org" "$queryid" "$companyid"
#         execute_as "querydate" "$org" "$queryid" "$companyid" "$date"
#         execute_as "querytotaldate" "$org" "$queryid" "$companyid" "$date"
#         execute_as "querydateids" "$org" "$queryid" "$companyid" "$date"
#     fi
# fi
