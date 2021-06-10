#!/bin/bash

CHANNEL_NAME="mychannel"
CC_NAME="autoauditor"
CC_TAR="${CC_NAME}.tar.gz"
CC_RUNTIME_LANGUAGE="golang"
CC_PATH="../chaincode/autoauditor"
CC_COLLECTION_CONFIG="$CC_PATH/collections_config.json"
CC_VERSION="1"
CC_POLICY="OR('Org1MSP.member','Org2MSP.member')"
ORDERER_HOSTNAME="orderer.example.com"
ORDERER_URL="localhost:7050"
ORDERER_CA_FILE="${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"
PEER1_URL="localhost:7051"
PEER2_URL="localhost:9051"
RED="\033[0;91m[!] ERROR:"
GREEN="\033[0;92m[+] SUCCESS:"
BLUE="\033[94m[*] INFO:"
NC="\033[0m"
FN_HELP="Help"
FN_STORE="NewReport"
FN_DELETE="DeleteReport"
FN_QUERY="GetReportById"
FN_QUERYHASH="GetReportHash"
FN_QUERYORG="GetReportsByOrganization"
FN_QUERYTOTALORG="GetTotalReportsByOrganization"
FN_QUERYORGIDS="GetReportsIdByOrganization"
FN_QUERYDATE="GetReportsByDate"
FN_QUERYTOTALDATE="GetTotalReportsByDate"
FN_QUERYDATEIDS="GetReportsIdByDate"
TRANS_STORE="report"
TRANS_DELETE="report_delete"


export PATH=${PWD}/../bin:${PWD}:$PATH
export FABRIC_CFG_PATH=$PWD/../config/
export CORE_PEER_TLS_ENABLED=true
export ORDERER_CA=${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

as_org1()
{
    export CORE_PEER_LOCALMSPID="Org1MSP"
    export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
    export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
    export CORE_PEER_ADDRESS=localhost:7051
}

as_org2()
{
    export CORE_PEER_LOCALMSPID="Org2MSP"
    export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
    export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
    export CORE_PEER_ADDRESS=localhost:9051
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
        *) echo -e "${RED} Invalid command: package, install, approve, store, query, queryhash\n" \
                "\t   queryorg, querytotalorg, queryorgids, querydate, querytotaldate, querydateids, delete.$NC"; exit 1 ;;
    esac

    case "$2" in
        all) "$command" "org1" "$3" "$4" "$5"; "$command" "org2" "$3" "$4" "$5" ;;
        org1) "$command" "org1" "$3" "$4" "$5" ;;
        org2) "$command" "org2" "$3" "$4" "$5" ;;
        *) echo -e "${RED} Invalid organization: all, org1, org2.$NC"; exit 1 ;;
    esac
}

show_help ()
{
    as_$1

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_HELP\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_HELP -> $1.$NC"
}

package_chaincode ()
{
    as_org1

    peer lifecycle chaincode package $CC_TAR \
        --path $CC_PATH \
        --lang $CC_RUNTIME_LANGUAGE \
        --label ${CC_NAME}_$CC_VERSION

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED

    echo -e "${prefix} Package ($CC_NAME) -> $CC_TAR.$NC"
}

install_chaincode()
{
    as_$1

    peer lifecycle chaincode install $CC_TAR

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} Install ($CC_NAME) -> $1.$NC"
}

installed_chaincode()
{
    as_$1

    peer lifecycle chaincode queryinstalled | grep ${CC_NAME}_$CC_VERSION

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} QueryInstalled ($CC_NAME) -> $1.$NC"
}

approve_chaincode_definition()
{
    as_$1

    export CC_PACKAGE_ID=$(peer lifecycle chaincode queryinstalled | grep -Eo "${CC_NAME}_${CC_VERSION}:[a-z0-9]+")

    peer lifecycle chaincode approveformyorg \
        -o $ORDERER_URL \
        --ordererTLSHostnameOverride $ORDERER_HOSTNAME \
        --channelID $CHANNEL_NAME \
        --name $CC_NAME \
        --version $CC_VERSION \
        --sequence $CC_VERSION \
        --collections-config $CC_COLLECTION_CONFIG \
        --signature-policy $CC_POLICY \
        --package-id $CC_PACKAGE_ID \
        --tls true \
        --cafile $ORDERER_CA

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} ApproveDefinition ($CC_NAME) -> $1.$NC"
}

commit_chaincode_definition()
{
    as_$1

    export ORG1_CA=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
    export ORG2_CA=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

    peer lifecycle chaincode commit \
        -o $ORDERER_URL \
        --ordererTLSHostnameOverride $ORDERER_HOSTNAME \
        --channelID $CHANNEL_NAME \
        --name $CC_NAME \
        --version $CC_VERSION \
        --sequence $CC_VERSION \
        --collections-config $CC_COLLECTION_CONFIG \
        --signature-policy $CC_POLICY \
        --tls true \
        --cafile $ORDERER_CA \
        --peerAddresses $PEER1_URL \
        --tlsRootCertFiles $ORG1_CA \
        --peerAddresses $PEER2_URL \
        --tlsRootCertFiles $ORG2_CA

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} Commit ($CC_NAME) -> $1.$NC"
}

store_data()
{
    as_$1

    id=$2
    org=$3
    date=$4

    export REPORT=$(echo -n "{\"id\": \"$id\", \"org\": \"$org\", \"date\": \"${date:0:7}\", \"nvuln\": 5, \"report\": \"dummy_basic_report\"}" | base64 | tr -d \\n)
    export REPORTPRIVATE=$(echo -n "{\"id\": \"$id\", \"private\": true, \"org\": \"$org\", \"date\": \"$date\", \"nvuln\": 5, \"report\": \"dummy_private_report\"}" | base64 | tr -d \\n)

    peer chaincode invoke \
        -o $ORDERER_URL \
        --ordererTLSHostnameOverride $ORDERER_HOSTNAME \
        --tls \
        --cafile $ORDERER_CA_FILE \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_STORE\"]}" \
        --transient "{\"$TRANS_STORE\":\"$REPORT\"}"

    [[ $? -eq 0 ]] \
        && echo $REPORTPRIVATE | base64 -d && echo "" && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_STORE (Transient: report::PublicReport) -> $1.$NC"

    peer chaincode invoke \
        -o $ORDERER_URL \
        --ordererTLSHostnameOverride $ORDERER_HOSTNAME \
        --tls \
        --cafile $ORDERER_CA_FILE \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_STORE\"]}" \
        --transient "{\"$TRANS_STORE\":\"$REPORTPRIVATE\"}"

    [[ $? -eq 0 ]] \
        && echo $REPORTPRIVATE | base64 -d && echo "" && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_STORE (Transient: report::PrivateReport) -> $1.$NC"
}

delete_data()
{
    as_$1
    id=$2

    export REPORT_DELETE=$(echo -n "{\"id\":\"$id\"}" | base64 | tr -d \\n)

    peer chaincode invoke \
         -o $ORDERER_URL \
         --ordererTLSHostnameOverride $ORDERER_HOSTNAME \
         --tls \
         --cafile $ORDERER_CA_FILE \
         -C $CHANNEL_NAME \
         -n $CC_NAME \
         -c "{\"Args\":[\"$FN_DELETE\"]}" \
         --transient "{\"$TRANS_DELETE\":\"$REPORT_DELETE\"}"

    [[ $? -eq 0 ]] \
        && prefix=$GREEN \
        || prefix=$RED

    echo -e "${prefix} $FN_DELETE (Transient: report_delete) -> $1.$NC"
}

query_data()
{
    as_$1

    id=$2

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERY\", \"$id\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERY ($id) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERY\", \"$id\", \"public\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERY ($id, public) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERY\", \"$id\", \"private\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERY ($id, private) -> $1.$NC"
}

query_data_hash()
{
    as_$1

    id=$2

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYHASH\", \"$id\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYHASH ($id) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYHASH\", \"$id\", \"public\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYHASH ($id, public) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYHASH\", \"$id\", \"private\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYHASH ($id, private) -> $1.$NC"
}

query_data_org()
{
    as_$1
    org=$3

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYORG\", \"$org\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYORG ($org) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYORG\", \"$org\", \"public\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYORG ($org, public) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYORG\", \"$org\", \"private\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYORG ($org, private) -> $1.$NC"
}

query_total_data_org()
{
    as_$1
    org=$3

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYTOTALORG\", \"$org\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYTOTALORG ($org) -> $1.$NC"
}

query_data_org_ids()
{
    as_$1
    org=$3

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYORGIDS\", \"$org\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYORGIDS ($org) -> $1.$NC"
}

query_data_date()
{
    as_$1
    org=$3
    date=${4:0:7}

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYDATE\", \"$date\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYDATE ($date) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYDATE\", \"$date\", \"public\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYDATE ($date, public) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYDATE\", \"$date\", \"private\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYDATE ($date, private) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYDATE\", \"$date\", \"$org\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYDATE ($date, $org) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYDATE\", \"$date\", \"$org\", \"public\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYDATE ($date, $org, public) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYDATE\", \"$date\", \"$org\", \"private\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYDATE ($date, $org, private) -> $1.$NC"
}

query_total_data_date()
{
    as_$1
    org=$3
    date=${4:0:7}

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYTOTALDATE\", \"$date\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYTOTALDATE ($date) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYTOTALDATE\", \"$date\", \"$org\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYTOTALDATE ($date, $org) -> $1.$NC"
}

query_data_date_ids()
{
    as_$1
    org=$3
    date=${4:0:7}

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYDATEIDS\", \"$date\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYDATEIDS ($date) -> $1.$NC"

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"$FN_QUERYDATEIDS\", \"$date\", \"$org\"]}")

    [[ -n "$output" ]] \
        && echo $output && prefix=$GREEN \
        || prefix=$RED
    echo -e "${prefix} $FN_QUERYDATEIDS ($date, $org) -> $1.$NC"
}

usage()
{
    echo "Usage:"
    echo "    $0 -a"
    echo "                             Generate chaincode package, install, approve, commit and finally, store and query test data."
    echo ""
    echo "    $0 -r"
    echo "                             Disable store and query execution from 'execute all' command."
    echo ""
    echo "    $0 -c cmd -o org [-i Id]"
    echo "                             Execute given cmd as org. Optionally, ID parameter allowed to store/query."
    echo ""
    echo "    $0 -u"
    echo "                             Test network up."
    echo ""
    echo "    $0 -d"
    echo "                             Test network down."
    echo ""
    echo "    $0 -q"
    echo "                             Executes all query examples."
    echo ""
    echo "    $0 -n"
    echo "                             Modify chaincode name."
    echo ""
    echo "    $0 -p"
    echo "                             Modify chaincode path."
    echo ""
    echo "    $0 -g"
    echo "                             Modify chaincode collection config path."
    echo ""
    echo "    $0 -v"
    echo "                             Modify chaincode version."
    echo ""
    echo "    $0 -h"
    echo "                             Show this help."
    echo ""
    echo "Commands:"
    echo "       -c help               Show $CC_NAME chaincode available functions."
    echo "       -c package            Package $CC_NAME chaincode."
    echo "       -c installed          Query installed chaincodes in peer."
    echo "       -c install            Install $CC_NAME chaincode."
    echo "       -c approve            Approve $CC_NAME chaincode definition."
    echo "       -c commit             Commit $CC_NAME chaincode definition."
    echo "       -c store              Store test report."
    echo "       -c query              Query test report."
    echo "       -c queryhash          Query test report hash."
    echo "       -c queryorg           Query test reports from organization."
    echo "       -c querytotalorg      Query total reports from organization."
    echo "       -c queryorgids        Query all reports id from organization."
    echo "       -c querydate          Query test reports from date [ and organization]."
    echo "       -c querytotaldate     Query total reports from date [ and organization]."
    echo "       -c querydateids       Query all reports id from date [ and organization]."
    echo "       -c delete             Delete test report."
    echo ""
    echo "Organizations:"
    echo "       -o all                Execute command as all organizations."
    echo "       -o org1               Execute command as org1."
    echo "       -o org2               Execute command as org2."
    exit
}

start()
{
    ./network.sh up createChannel -s couchdb > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED} Network -> ./network.sh up createChannel -s couchdb.$NC"
        exit 1
    fi
}

stop()
{
    ./network.sh down > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED} Network -> ./network.sh down.$NC"
        exit 1
    fi
}

while getopts ":ac:o:hudri:qv:g:p:n:sm:t:" opt; do
    case ${opt} in
        c) cmd=$OPTARG ;;
        o) org=$OPTARG ;;
        u) up="yes" ;;
        d) down="yes" ;;
        a) all="yes" ;;
        q) query="yes" ;;
        s) store="yes" ;;
        r) raw="yes" ;;
        i) queryid=$OPTARG ;;
        m) companyid=$OPTARG ;;
        t) date=$OPTARG ;;
        v) CC_VERSION=$OPTARG ;;
        g) CC_COLLECTION_CONFIG=$OPTARG ;;
        n) CC_NAME=$OPTARG;CC_TAR="${CC_NAME}.tar.gz" ;;
        p) CC_PATH=$OPTARG ;;
        h) usage;;
        \?) usage;;
    esac
done

if [ -z "$queryid" ]; then
    queryid="report007"
fi

if [ -z "$companyid" ]; then
    companyid="org1"
fi

if [ -z "$date" ]; then
    date="2020-05-21 17:37:27.910352+02:00"
fi

if [ -z "$org" ]; then
    org="all"
fi

if [ -n "$store" ]; then
    execute_as "store" "org1" "$queryid" "$companyid" "$date"
fi

if [ -n "$query" ]; then
    execute_as "query" "$org" "$queryid"
    execute_as "queryhash" "$org" "$queryid"
    execute_as "queryorg" "$org" "$queryid" "$companyid"
    execute_as "querytotalorg" "$org" "$queryid" "$companyid"
    execute_as "queryorgids" "$org" "$queryid" "$companyid"
    execute_as "querydate" "$org" "$queryid" "$companyid" "$date"
    execute_as "querytotaldate" "$org" "$queryid" "$companyid" "$date"
    execute_as "querydateids" "$org" "$queryid" "$companyid" "$date"
    exit
fi

if [ -n "$cmd" ]; then
    execute_as "$cmd" "$org" "$queryid" "$companyid" "$date"
    exit
fi

if [ -n "$up" ]; then
    echo -e "${BLUE} Starting hyperledger fabric test-network.$NC"
    start
    echo -e "${BLUE} Starting docker-resolver container.$NC"
    docker run --rm -d --name docker-resolver -v /var/run/docker.sock:/tmp/docker.sock -v /etc/hosts:/tmp/hosts dvdarias/docker-hoster > /dev/null
fi

if [ -n "$all" ]; then
    execute_as "package" "org1"
    execute_as "install" "all"
    execute_as "installed" "all"
    execute_as "approve" "all"
    execute_as "commit" "org1"
    if [ -z "$raw" ]; then
        echo -e "${BLUE} Waiting transactions processing.$NC"; sleep 3 # wait time to process transaction
        execute_as "store" "org1" "$queryid" "$companyid" "$date"
        echo -e "${BLUE} Waiting transactions processing.$NC"; sleep 3 # wait time to process transaction
        execute_as "query" "$org" "$queryid"
        execute_as "queryhash" "$org" "$queryid"
        execute_as "queryorg" "$org" "$queryid" "$companyid"
        execute_as "querytotalorg" "$org" "$queryid" "$companyid"
        execute_as "queryorgids" "$org" "$queryid" "$companyid"
        execute_as "querydate" "$org" "$queryid" "$companyid" "$date"
        execute_as "querytotaldate" "$org" "$queryid" "$companyid" "$date"
        execute_as "querydateids" "$org" "$queryid" "$companyid" "$date"
    fi
fi

if [ -n "$down" ]; then
    echo -e "${BLUE} Stopping hyperledger fabric test-network.$NC"
    stop
    echo -e "${BLUE} Stopping docker-resolver container.$NC"
    docker container stop docker-resolver > /dev/null
    exit
fi

if [ "$#" -eq 0 ]; then
    usage
fi
