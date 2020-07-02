#!/bin/bash

CHANNEL_NAME="mychannel"
CC_NAME="autoauditor"
CC_TAR="${CC_NAME}.tar.gz"
CC_RUNTIME_LANGUAGE="golang"
CC_PATH="../chaincode/autoauditor_chaincode/"
CC_COLLECTION_CONFIG="$CC_PATH/collections_config.json"
CC_VERSION="1"
CC_POLICY="OR('Org1MSP.member','Org2MSP.member')"
ORDERER_HOSTNAME="orderer.example.com"
ORDERER_URL="localhost:7050"
ORDERER_CA_FILE="${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"
PEER1_URL="localhost:7051"
PEER2_URL="localhost:9051"
RED="\033[0;91m[-] "
GREEN="\033[0;92m[+] "
BLUE="\033[94m[*] "
NC="\033[0m"

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
        commit) command=commit_and_initiate_chaincode_definition ;;
        store) command=store_data ;;
        query) command=query_data ;;
        queryhash) command=query_data_hash ;;
        queryorg) command=query_data_org ;;
        delete) command=delete_data ;;
        *) echo -e "${RED}Invalid command: package, install, approve, store, query, queryhash, queryorg, delete.$NC"; exit 1 ;;
    esac

    case "$2" in
        all) $command "org1" $3; $command "org2" $3 ;;
        org1) $command "org1" $3 ;;
        org2) $command "org2" $3 ;;
        *) echo -e "${RED}Invalid organization: all, org1, org2.$NC"; exit 1 ;;
    esac
}

package_chaincode ()
{
    as_org1

    peer lifecycle chaincode package $CC_TAR \
        --path $CC_PATH \
        --lang $CC_RUNTIME_LANGUAGE \
        --label ${CC_NAME}_$CC_VERSION

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Autoauditor chaincode packaged correctly in $CC_TAR with name $CC_NAME.$NC"
    else
        echo -e "${RED}Error during packaging of autoauditor chaincode by $1.$NC"
    fi
}

install_chaincode()
{
    as_$1

    peer lifecycle chaincode install $CC_TAR

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Autoauditor chaincode installed correctly in $1.$NC"
    else
        echo -e "${RED}Error during installation of autoauditor chaincode in $1.$NC"
    fi
}

installed_chaincode()
{
    as_$1

    peer lifecycle chaincode queryinstalled | grep ${CC_NAME}

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Chaincode correctly installed in $1.$NC"
    else
        echo -e "${RED}Chaincode not installed in $1.$NC"
    fi
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
        --init-required \
        --package-id $CC_PACKAGE_ID \
        --tls true \
        --cafile $ORDERER_CA

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Autoauditor chaincode approved correctly by $1.$NC"
    else
        echo -e "${RED}Error during approval of autoauditor chaincode by $1.$NC"
    fi
}

commit_and_initiate_chaincode_definition()
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
        --init-required \
        --tls true \
        --cafile $ORDERER_CA \
        --peerAddresses $PEER1_URL \
        --tlsRootCertFiles $ORG1_CA \
        --peerAddresses $PEER2_URL \
        --tlsRootCertFiles $ORG2_CA

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Autoauditor chaincode committed correctly by $1.$NC"
    else
        echo -e "${RED}Error when committing autoauditor chaincode by $1.$NC"
    fi

    peer chaincode invoke \
        -o $ORDERER_URL \
        --ordererTLSHostnameOverride $ORDERER_HOSTNAME \
        --channelID $CHANNEL_NAME \
        --name $CC_NAME --isInit \
        --tls true \
        --cafile $ORDERER_CA \
        --peerAddresses $PEER1_URL \
        --tlsRootCertFiles $ORG1_CA -c '{"Args":["Init"]}'

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Autoauditor chaincode initiated correctly by $1.$NC"
    else
        echo -e "${RED}Error when initiating autoauditor chaincode by $1.$NC"
    fi
}

store_data()
{
    as_$1

    report_id=$2

    export REPORT=$(echo -n "{\"id\": \"$report_id\", \"org\": \"ACME\", \"date\": \"2020-05\", \"nvuln\": 5, \"report\": \"basic_report\"}" | base64 | tr -d \\n)
    export REPORTPRIVATE=$(echo -n "{\"id\": \"$report_id\", \"private\": true, \"org\": \"ACME\", \"date\": \"2020-05-21 17:37:27.910352+02:00\", \"nvuln\": 5, \"report\": \"private_report\"}" | base64 | tr -d \\n)

    peer chaincode invoke \
        -o $ORDERER_URL \
        --ordererTLSHostnameOverride $ORDERER_HOSTNAME \
        --tls \
        --cafile $ORDERER_CA_FILE \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c '{"Args":["new"]}' \
        --transient "{\"aareport\":\"$REPORT\"}"

    if [ $? -eq 0 ]; then
        echo $REPORT | base64 -d
        echo ""
        echo -e "${GREEN}Storing public report correctly in blockchain by $1.$NC"
    else
        echo -e "${RED}Error storing public report in blockchain by $1.$NC"
    fi

    peer chaincode invoke \
        -o $ORDERER_URL \
        --ordererTLSHostnameOverride $ORDERER_HOSTNAME \
        --tls \
        --cafile $ORDERER_CA_FILE \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c '{"Args":["new"]}' \
        --transient "{\"aareport\":\"$REPORTPRIVATE\"}"

    if [ $? -eq 0 ]; then
        echo $REPORTPRIVATE | base64 -d
        echo ""
        echo -e "${GREEN}Storing private report correctly in blockchain by $1.$NC"
    else
        echo -e "${RED}Error storing private report in blockchain by $1.$NC"
    fi
}

query_data()
{
    as_$1

    report_id=$2

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"getReport\", \"$report_id\"]}")

    if [ -n "$output" ]; then
        echo $output
        echo -e "${GREEN}Querying highest permission report successfully by $1.$NC"
    else
        echo -e "${RED}Error querying highest permission report by $1.$NC"
    fi

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"getReport\", \"$report_id\", \"public\"]}")

    if [ -n "$output" ]; then
        echo $output
        echo -e "${GREEN}Querying public report successfully by $1.$NC"
    else
        echo -e "${RED}Error querying public report by $1.$NC"
    fi

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"getReport\", \"$report_id\", \"private\"]}")

    if [ -n "$output" ]; then
        echo $output
        echo -e "${GREEN}Querying private report successfully by $1.$NC"
    else
        echo -e "${RED}Error querying private report by $1.$NC"
    fi
}

query_data_hash()
{
    as_$1

    report_id=$2

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"getReportHash\", \"$report_id\"]}")

    if [ -n "$output" ]; then
        echo $output
        echo -e "${GREEN}Querying highest permission report hash successfully by $1.$NC"
    else
        echo -e "${RED}Error querying highest permission report hash by $1.$NC"
    fi

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"getReportHash\", \"$report_id\", \"public\"]}")

    if [ -n "$output" ]; then
        echo $output
        echo -e "${GREEN}Querying public report hash successfully by $1.$NC"
    else
        echo -e "${RED}Error querying public report hash by $1.$NC"
    fi

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"getReportHash\", \"$report_id\", \"private\"]}")

    if [ -n "$output" ]; then
        echo $output
        echo -e "${GREEN}Querying private report hash successfully by $1.$NC"
    else
        echo -e "${RED}Error querying private report hash by $1.$NC"
    fi
}

query_data_org()
{
    as_$1
    org=$2

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"getOrganizationReports\", \"$org\"]}")

    if [ -n "$output" ]; then
        echo $output
        echo -e "${GREEN}Querying highest permission reports of organization successfully by $1.$NC"
    else
        echo -e "${RED}Error querying highest permission reports of organization by $1.$NC"
    fi

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"getOrganizationReports\", \"$org\", \"public\"]}")

    if [ -n "$output" ]; then
        echo $output
        echo -e "${GREEN}Querying public reports of organization successfully by $1.$NC"
    else
        echo -e "${RED}Error querying public reports of organization by $1.$NC"
    fi

    output=$(peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c "{\"Args\":[\"getOrganizationReports\", \"$org\", \"private\"]}")

    if [ -n "$output" ]; then
        echo $output
        echo -e "${GREEN}Querying private report of organization successfully by $1.$NC"
    else
        echo -e "${RED}Error querying private report of organization by $1.$NC"
    fi
}

delete_data()
{
    as_$1

    export REPORT_DELETE=$(echo -n "{\"id\":\report007\"}" | base64 | tr -d \\n)
    peer chaincode invoke \
        -C $CHANNEL_NAME \
        -n $CC_NAME \
        -c '{"Args":["delete"]}' \
        --transient "{\"aareport_delete\":\"$REPORT_DELETE\"}"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Report deleted correctly from blockchain by $1.$NC"
    fi
}

usage()
{
    echo "Usage:"
    echo "    $0 -a"
    echo "                       Generate chaincode package, install, approve, commit & initiate and finally, store and query test data."
    echo ""
    echo "    $0 -r"
    echo "                       Disable store and query execution from 'execute all' command."
    echo ""
    echo "    $0 -c cmd -o org [-i Id]"
    echo "                       Execute given cmd as org. Optionally, ID parameter allowed to store/query."
    echo ""
    echo "    $0 -u"
    echo "                       Test network up."
    echo ""
    echo "    $0 -d"
    echo "                       Test network down."
    echo "    $0 -q"
    echo "                       Executes all query examples."
    echo ""
    echo "    $0 -h"
    echo "                       Show this help."
    echo ""
    echo "Commands:"
    echo "       -c package      Package autoauditor chaincode."
    echo "       -c installed    Query installed chaincodes in peer."
    echo "       -c install      Install autoauditor chaincode."
    echo "       -c approve      Approve autoauditor chaincode definition."
    echo "       -c commit       Commit and initiate autoauditor chaincode definition."
    echo "       -c store        Store test data in blockchain."
    echo "       -c query        Query test data from blockchain."
    echo "       -c queryhash    Query test data hash from blockchain."
    echo "       -c queryorg     Query test data of organization from blockchain."
    echo "       -c delete       Delete test data from blockchain."
    echo ""
    echo "Organizations:"
    echo "       -o all          Execute command in all organizations."
    echo "       -o org1         Execute command in org1."
    echo "       -o org2         Execute command in org2."
    exit
}

start()
{
    ./network.sh up createChannel -s couchdb > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error during ./network.sh up createChannel -s couchdb.$NC"
        exit 1
    fi
}

stop()
{
    ./network.sh down > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error during ./network.sh down.$NC"
        exit 1
    fi

    exit 0
}

while getopts ":ac:o:hudri:q" opt; do
    case ${opt} in
        c) cmd=$OPTARG ;;
        o) org=$OPTARG ;;
        u) up="yes" ;;
        d) down="yes" ;;
        a) all="yes" ;;
        q) query="yes" ;;
        r) raw="yes" ;;
        i) queryid=$OPTARG ;;
        h) usage;;
        \?) usage;;
    esac
done

if [ -z "$queryid" ]; then
    queryid="report007"
    if [ "$cmd" == "queryorg" ]; then
        echo -e "${RED}Org name must be passed as ID argument.$NC"
        exit
    fi
fi

if [ -n "$query" ]; then
    execute_as "query" "all" $queryid
    execute_as "queryhash" "all" $queryid
    execute_as "queryorg" "all" "ACME"
    exit
fi

if [ -n "$cmd" ] && [ -n "$org" ]; then
    execute_as $cmd $org $queryid
    exit
fi

if [ -n "$up" ]; then
    start
fi

if [ -n "$all" ]; then
    execute_as "package" "org1"
    execute_as "install" "all"
    execute_as "installed" "all"
    execute_as "approve" "all"
    execute_as "commit" "org1"
    if [ -z "$raw" ]; then
        echo -e "${BLUE} Waiting transactions processing.$NC"; sleep 3 # wait time to process transaction
        execute_as "store" "org1" $queryid
        echo -e "${BLUE} Waiting transactions processing.$NC"; sleep 3 # wait time to process transaction
        execute_as "query" "all" $queryid
        execute_as "queryhash" "all" $queryid
        execute_as "queryorg" "all" "ACME"
    fi
fi

if [ -n "$down" ]; then
    stop
    exit
fi

if [ "$#" -eq 0 ]; then
    usage
fi
