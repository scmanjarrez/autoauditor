#!/bin/bash

aa_label="autoauditor"
aa_name="autoauditorsp"
aa_tar="autoauditor.tar.gz"
red="\033[0;91m[-] "
green="\033[0;92m[+] "
blue="\033[94m[*] "
nc="\033[0m"

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
        install) command=install_chaincode ;;
        approve) command=approve_chaincode_definition ;;
        commit) command=commit_and_initiate_chaincode_definition ;;
        store) command=store_data ;;
        query) command=query_data ;;
        delete) command=delete_data ;;
        *) echo -e "${red}Invalid command: package, install, approve, store, query, delete.$nc"; exit 1 ;;
    esac

    case "$2" in
        all) $command "org1"; $command "org2" ;;
        org1) $command "org1" ;;
        org2) $command "org2" ;;
        *) echo -e "${red}Invalid organization: all, org1, org2.$nc"; exit 1 ;;
    esac
}

package_chaincode ()
{
    as_org1

    peer lifecycle chaincode package autoauditor.tar.gz \
         --path ../chaincode/autoauditor_chaincode/ \
         --lang golang \
         --label $aa_label

    if [ $? -eq 0 ]; then
        echo -e "${green}Autoauditor chaincode packaged correctly in $aa_tar with label $aa_label.$nc"
    else
        echo -e "${red}Error during packaging of autoauditor chaincode by $1.$nc"
    fi
}

install_chaincode()
{
    as_$1

    peer lifecycle chaincode install $aa_tar

    if [ $? -eq 0 ]; then
        echo -e "${green}Autoauditor chaincode installed correctly in $1.$nc"
    else
        echo -e "${red}Error during installation of autoauditor chaincode in $1.$nc"
    fi
}

approve_chaincode_definition()
{
    as_$1

    export CC_PACKAGE_ID=$(peer lifecycle chaincode queryinstalled | grep -Eo "autoauditor:[a-z0-9]+")

    peer lifecycle chaincode approveformyorg \
         -o localhost:7050 \
         --ordererTLSHostnameOverride orderer.example.com \
         --channelID mychannel \
         --name $aa_name \
         --version 1.0 \
         --collections-config ../chaincode/autoauditor_chaincode/collections_config.json \
         --signature-policy "OR('Org1MSP.member','Org2MSP.member')" \
         --init-required \
         --package-id $CC_PACKAGE_ID \
         --sequence 1 \
         --tls true \
         --cafile $ORDERER_CA

    if [ $? -eq 0 ]; then
        echo -e "${green}Autoauditor chaincode approved correctly by $1.$nc"
    else
        echo -e "${red}Error during approval of autoauditor chaincode by $1.$nc"
    fi
}

commit_and_initiate_chaincode_definition()
{
    as_$1

    export ORG1_CA=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
    export ORG2_CA=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

    peer lifecycle chaincode commit \
         -o localhost:7050 \
         --ordererTLSHostnameOverride orderer.example.com \
         --channelID mychannel \
         --name $aa_name \
         --version 1.0 \
         --sequence 1 \
         --collections-config ../chaincode/autoauditor_chaincode/collections_config.json \
         --signature-policy "OR('Org1MSP.member','Org2MSP.member')" \
         --init-required \
         --tls true \
         --cafile $ORDERER_CA \
         --peerAddresses localhost:7051 \
         --tlsRootCertFiles $ORG1_CA \
         --peerAddresses localhost:9051 \
         --tlsRootCertFiles $ORG2_CA

    if [ $? -eq 0 ]; then
        echo -e "${green}Autoauditor chaincode committed correctly by $1.$nc"
    else
        echo -e "${red}Error when committing autoauditor chaincode by $1.$nc"
    fi

    peer chaincode invoke \
         -o localhost:7050 \
         --ordererTLSHostnameOverride orderer.example.com \
         --channelID mychannel \
         --name $aa_name --isInit \
         --tls true \
         --cafile $ORDERER_CA \
         --peerAddresses localhost:7051 \
         --tlsRootCertFiles $ORG1_CA -c '{"Args":["Init"]}'

    if [ $? -eq 0 ]; then
        echo -e "${green}Autoauditor chaincode initiated correctly by $1.$nc"
    else
        echo -e "${red}Error when initiating autoauditor chaincode by $1.$nc"
    fi
}

store_data()
{
    as_$1

    # from datetime import datetime; print(datetime.now().astimezone()); 2020-05-21 17:37:27.910352+02:00
    export REPORTS=$(echo -n "{\"id\":\"report007\", \"role\":\"simple\", \"org\":\"ACME\", \"date\":\"2020-05\", \"nvuln\":5, \"report\":\"dummyreportS\"}" | base64 | tr -d \\n)
    export REPORTM=$(echo -n "{\"id\":\"report007\", \"role\":\"medium\", \"org\":\"ACME\", \"date\":\"2020-05\", \"nvuln\":5, \"report\":\"dummyreportM\"}" | base64 | tr -d \\n)
    export REPORTF=$(echo -n "{\"id\":\"report007\", \"role\":\"full\", \"org\":\"ACME\", \"date\":\"2020-05-21 17:37:27.910352+02:00\", \"nvuln\":5, \"report\":\"dummyreportF\"}" | base64 | tr -d \\n)

    peer chaincode invoke \
         -o localhost:7050 \
         --ordererTLSHostnameOverride orderer.example.com \
         --tls \
         --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
         -C mychannel \
         -n $aa_name \
         -c '{"Args":["new"]}' \
         --transient "{\"aareport\":\"$REPORTS\"}"

    if [ $? -eq 0 ]; then
        echo -e "${green}ReportS stored correctly in blockchain by $1.$nc"
    else
        echo -e "${red}Error storing REPORTS in blockchain by $1.$nc"
    fi

    peer chaincode invoke \
         -o localhost:7050 \
         --ordererTLSHostnameOverride orderer.example.com \
         --tls \
         --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
         -C mychannel \
         -n $aa_name \
         -c '{"Args":["new"]}' \
         --transient "{\"aareport\":\"$REPORTM\"}"

    if [ $? -eq 0 ]; then
        echo -e "${green}ReportM stored correctly in blockchain by $1.$nc"
    else
        echo -e "${red}Error storing REPORTM in blockchain by $1.$nc"
    fi

    peer chaincode invoke \
         -o localhost:7050 \
         --ordererTLSHostnameOverride orderer.example.com \
         --tls \
         --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
         -C mychannel \
         -n $aa_name \
         -c '{"Args":["new"]}' \
         --transient "{\"aareport\":\"$REPORTF\"}"

    if [ $? -eq 0 ]; then
        echo -e "${green}ReportF stored correctly in blockchain by $1.$nc"
    else
        echo -e "${red}Error storing REPORTF in blockchain by $1.$nc"
    fi
}

query_data()
{
    as_$1

    output=$(peer chaincode query \
                  -C mychannel \
                  -n $aa_name \
                  -c '{"Args":["searchReport","report007"]}')

    if [ -n "$output" ]; then
        echo $output
        echo -e "${green}Query high permission report successfully by $1.$nc"
    else
        echo -e "${red}Error querying high permission report by $1.$nc"
    fi

    output=$(peer chaincode query \
                  -C mychannel \
                  -n $aa_name \
                  -c '{"Args":["searchReport","report007", "simple"]}')

    if [ -n "$output" ]; then
        echo $output
        echo -e "${green}Query REPORTS successfully by $1.$nc"
    else
        echo -e "${red}Error querying REPORTS by $1.$nc"
    fi

    output=$(peer chaincode query \
                  -C mychannel \
                  -n $aa_name \
                  -c '{"Args":["searchReport","report007", "medium"]}')

    if [ -n "$output" ]; then
        echo $output
        echo -e "${green}Query REPORTM successfully by $1.$nc"
    else
        echo -e "${red}Error querying REPORTM by $1.$nc"
    fi

    output=$(peer chaincode query \
                  -C mychannel \
                  -n $aa_name \
                  -c '{"Args":["searchReport","report007", "full"]}')

    if [ -n "$output" ]; then
        echo $output
        echo -e "${green}Query REPORTF successfully by $1.$nc"
    else
        echo -e "${red}Error querying REPORTF by $1.$nc"
    fi
}

delete_data()
{
    as_$1

    export REPORT_DELETE=$(echo -n "{\"id\":\report007\"}" | base64 | tr -d \\n)
    peer chaincode invoke \
         -C mychannel \
         -n $aa_name \
         -c '{"Args":["delete"]}' \
         --transient "{\"aareport_delete\":\"$REPORT_DELETE\"}"

    if [ $? -eq 0 ]; then
        echo -e "${green}Report deleted correctly from blockchain by $1.$nc"
    fi
}

usage()
{
    echo "Usage:"
    echo "    $0 -a"
    echo "                       Generate chaincode package, install, approve and store test data."
    echo ""
    echo "    $0 -c cmd -o org"
    echo "                       Execute given cmd as org."
    echo ""
    echo "    $0 -h"
    echo "                       Show this help."
    echo ""
    echo "Commands:"
    echo "       -c package      Package autoauditor chaincode."
    echo "       -c install      Install autoauditor chaincode."
    echo "       -c approve      Approve autoauditor chaincode definition."
    echo "       -c commit       Commit and initiate autoauditor chaincode definition."
    echo "       -c store        Store test data in blockchain."
    echo "       -c query        Query test data from blockchain."
    echo "       -c delete       Delete test data from blockchain."
    echo ""
    echo "Organizations:"
    echo "       -o all          Execute command in all organizations."
    echo "       -o org1         Execute command in org1."
    echo "       -o org2         Execute command in org2."
    exit
}

stop()
{
    ./network.sh down > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${red}Error during ./network.sh down.$nc"
        exit 1
    fi

    exit 0
}

while getopts ":ac:o:hs" opt; do
    case ${opt} in
        s) stop ;;
        c) cmd=$OPTARG ;;
        o) org=$OPTARG ;;
        a) all="yes" ;;
        h) usage;;
        \?) usage;;
    esac
done

if [ -n "$cmd" ] && [ -n "$org" ]; then
    execute_as $cmd $org
    exit
fi

if [ -n "$all" ]; then
    ./network.sh up createChannel -s couchdb > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${red}Error during ./network.sh up createChannel -s couchdb.$nc"
        exit 1
    fi
    execute_as "package" "org1"
    execute_as "install" "all"
    execute_as "approve" "all"
    execute_as "commit" "org1"
    echo -e "${blue} Waiting transactions processing.$nc"; sleep 3 # wait time to process transaction
    execute_as "store" "org1"
    echo -e "${blue} Waiting transactions processing.$nc"; sleep 3 # wait time to process transaction
    execute_as "query" "all"
    exit
fi

usage
