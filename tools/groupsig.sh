#!/usr/bin/env bash

# SPDX-License-Identifier: GPL-3.0-or-later

# groupsig - Groupsig, helper script.

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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

_R="\033[91m"
_G="\033[92m"
_Y="\033[93m"
_B="\033[94m"
_N="\033[0m"

OUT=/dev/null
ROOT=$PWD/tools/groupsig
NET=$PWD/tools/fabric_net/network
PRV=$ROOT/provider
VRF=$ROOT/verifier
INF=$ROOT/informer
RCP=$ROOT/recipient
FCA=fabric_ca_certs
CRDS=credentials
FCRDS=fabric_credentials
WALLET=wallet

disable_ansi_color ()
{
    NO_COLOR=--no-ansi
    _R=
    _G=
    _Y=
    _B=
    _N=
}

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

clean_crypto ()
{
    log info "Removing crypto material"
    # clean provider
    rm -rf $PRV/$FCA $PRV/$CRDS
    # clean verifier
    rm -rf $VRF/$FCRDS $VRF/$WALLET
    # clean informer
    rm -rf $INF/$FCRDS $INF/$CRDS
    # clean recipient
    rm -rf $RCP/$FCRDS
}

generate_crypto ()
{
    log info "Generating crypto material"
    # generate provider crypto material
    mkdir -p $PRV/$FCA
    ln -s $NET/ca/org1/ca-cert.pem $PRV/$FCA/ca-org1.pem
    ln -s $NET/ca/org2/ca-cert.pem $PRV/$FCA/ca-org2.pem
    ln -s $NET/ca/org3/ca-cert.pem $PRV/$FCA/ca-org3.pem
    c_rehash $PRV/$FCA > $OUT 2>&1
    # generate verifier crypto material
    mkdir -p $VRF/$FCRDS
    ln -s $NET/org3/peers/peer0.org3.example.com/tls/ca.crt $VRF/$FCRDS/peer.crt
    ln -s $NET/org3/users/user1@org3.example.com/msp/signcerts/cert.pem $VRF/$FCRDS/user.crt
    ln -s $NET/org3/users/user1@org3.example.com/msp/keystore/priv_sk $VRF/$FCRDS/user.key
    # generate informer crypto material
    mkdir -p $INF/$FCRDS
    ln -s $NET/org2/users/user1@org2.example.com/msp/signcerts/cert.pem $INF/$FCRDS/user.crt
    ln -s $NET/org2/users/user1@org2.example.com/msp/keystore/priv_sk $INF/$FCRDS/user.key
    # generate reader crypto material
    mkdir -p $RCP/$FCRDS
    ln -s $NET/org1/users/user1@org1.example.com/msp/signcerts/cert.pem $RCP/$FCRDS/user.crt
    ln -s $NET/org1/users/user1@org1.example.com/msp/keystore/priv_sk $RCP/$FCRDS/user.key
}

usage ()
{
    echo "Usage:"
    echo "    $name                 Generate crypto material from fabric_net"
    echo "    $name -c|--clean      Remove crypto crypto material"
    echo "    $name --no-color      No ANSI colors"
    echo "    $name --verbose       Enable verbose output"
    echo "    $name -h|--help       Show this help."

    if [ -n "$1" ]; then
        exit $1
    fi
    exit
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--clean)
            _clean=SET
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
            log error "Parameter $1 not recognized"
            usage 1
            ;;
    esac
done

if [ -n "$_clean" ]; then
    clean_crypto
else
    generate_crypto
fi
