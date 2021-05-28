export PATH=${PWD}/bin:${PWD}:$PATH
export FABRIC_CFG_PATH=$PWD/../config/own
export CORE_PEER_TLS_ENABLED=true

export ORDERER_CA=${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

export CORE_PEER_LOCALMSPID="allsafeMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/allsafe.com/peers/peer0.allsafe.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/allsafe.com/users/Admin@allsafe.com/msp
export CORE_PEER_ADDRESS=localhost:8051
