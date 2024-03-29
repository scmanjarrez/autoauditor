#!/bin/bash

# SPDX-License-Identifier: GPL-3.0-or-later

# vulnerable_net - Vulnerable network, helper script.

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

ROOT=$PWD/tools/vulnerable_net
YAML=$ROOT/docker-compose.yaml
CFG=$ROOT/examples/vpn.example.ovpn
GSIG=$PWD/third_party/libgroupsig/libgroupsig
VENV=venv

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
    NO_COLOR='--ansi never'
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
    echo "    $name                  Start vulnerable network."
    echo "    $name -d|--down        Stop vulnerable network."
    echo "    $name -v|--verbose     Enable verbose output."
    echo "    $name -n|--no-color    No ANSI colors."
    echo "    $name -h|--help        Show this help."

    exit
}

check_privileges ()
{
    id -Gn `whoami` | grep '\bdocker\b' > /dev/null
    if [ $? -ne 0 ]; then
        log error "User '`whoami`' must belong to 'docker' group to communicate with docker API"
        exit
    fi
}

network_up ()
{
    check_privileges

    log info "Starting docker containers"

    docker compose $NO_COLOR -f $YAML up -d
    local vpns=autoauditor_vpn_server
    local val=$(docker network connect bridge $vpns 2>&1)
    echo $val | grep "already exists" > /dev/null
    if [ $? -eq 0 ]; then
        log warn "VPN server $vpns already connected to bridge network"
    fi

    local ip=$(docker inspect -f '{{.NetworkSettings.Networks.bridge.IPAddress}}' $vpns)
    if [ -f $CFG ]; then
        sed -i "s/remote.*1194 udp/remote "$ip" 1194 udp/" $CFG
    fi

    log info "Adding route to redirect traffic through VPN server"
    log warn "Command: sudo ip route add 10.10.20.0/25 via 10.10.0.2"
    sudo ip route add 10.10.20.0/25 via 10.10.0.2

    create_venv
}

network_down ()
{
    log info "Stopping docker containers"
    docker compose $NO_COLOR -f $YAML down -v

    log info "Removing vulnerable network files"
    rm -rf $VENV build autoauditor.egg-info
}

pkg_info ()
{
    local default_spaces=25
    local spaces=$(printf ' %.0s' $(seq 1 $(($default_spaces-${#1}))))
    if [ $2 -eq 0 ]; then
        echo -e "$1$spaces... ${_G}installed$_N"
    else
        echo -e "$1$spaces... ${_R}missing$_N"
    fi
}

check_required_pkgs ()
{
    log info "Checking packages"
    local all_pk=0

    local pkg=docker
    command -v $pkg > /dev/null 2>&1
    [ $? -eq 0 ] \
        && pkg_info $pkg 0  \
            || { pkg_info $pkg 1; all_pk=1; }

    pkg='docker-compose-plugin'
    docker compose > /dev/null 2>&1
    [ $? -eq 0 ] \
        && pkg_info $pkg 0  \
            || { pkg_info $pkg 1; all_pk=1; }

    pkg=git
    command -v $pkg > /dev/null 2>&1
    [ $? -eq 0 ] \
        && pkg_info $pkg 0  \
            || { pkg_info $pkg 1; all_pk=1; }

    pkg=go
    command -v $pkg > /dev/null 2>&1
    [ $? -eq 0 ] \
        && pkg_info $pkg 0  \
            || { pkg_info $pkg 1; all_pk=1; }

    pkg=python3-dev
    dpkg -s $pkg > /dev/null 2>&1
    [ $? -eq 0 ] \
        && pkg_info $pkg 0  \
            || { pkg_info $pkg 1; all_pk=1; }

    pkg=python3-venv
    python3 -c 'import ensurepip' > /dev/null 2>&1
    [ $? -eq 0 ] \
        && pkg_info $pkg 0  \
            || { pkg_info $pkg 1; all_pk=1; }

    if [ -n "$_groupsig" ]; then
        pkg=build-essential
        dpkg -s $pkg > /dev/null 2>&1
        [ $? -eq 0 ] \
            && pkg_info $pkg 0  \
                || { pkg_info $pkg 1; all_pk=1; }

        pkg=cmake
        dpkg -s $pkg > /dev/null 2>&1
        [ $? -eq 0 ] \
            && pkg_info $pkg 0  \
                || { pkg_info $pkg 1; all_pk=1; }

        pkg=libssl-dev
        dpkg -s $pkg > /dev/null 2>&1
        [ $? -eq 0 ] \
            && pkg_info $pkg 0  \
                || { pkg_info $pkg 1; all_pk=1; }

        pkg=perl
        command -v $pkg > /dev/null 2>&1
        [ $? -eq 0 ] \
            && pkg_info $pkg 0  \
                || { pkg_info $pkg 1; all_pk=1; }
    fi

    if [ $all_pk -ne 0 ]; then
        log error "Mandatory package missing"
        exit 1
    fi
}

create_venv ()
{
    log info "Generating virtual environment"
    local errorf=/tmp/autoauditor.venv.error

    if [ ! -d $VENV ]; then
        python3 -m venv $VENV > $errorf
        if [ $? -ne 0 ]; then
            cat $errorf
            exit
        fi
    fi

    source $VENV/bin/activate
    if [ $? -ne 0 ]; then
        log error "Virtual environment could not be created"
        exit
    fi

    log info "Installing dependencies"
    python -m pip install -U pip wheel --no-cache-dir
    python -m pip install --no-cache-dir .

    if [ -n "$_groupsig" ]; then
        if [ -z "$(ls $GSIG)" ]; then
            log warn "libgroupsig not downloaded. Use 'git submodule update --init --recursive' to download it"
        else
            if [ ! -d "$GSIG/build" ]; then
                mkdir -p $GSIG/build
            fi
            if [ ! -d "$GSIG/build/lib" ] \
                   || [ -z "$(ls $GSIG/build/lib)" ] \
                   || [ ! -d "$GSIG/build/external/lib" ] \
                   || [ -z "$(ls $GSIG/build/external/lib)" ]; then
                log info "Compiling libgroupsig"
                perl -0777 -i -pe 's/(set \(CMAKE_CXX_FLAGS .*?\))/\1\nadd_link_options("LINKER:--allow-multiple-definition")/' $GSIG/CMakeLists.txt
                perl -0777 -i -pe 's/\],\n\)/], extra_link_args=["-Wl,--allow-multiple-definition"]\n)/' $GSIG/src/wrappers/python/pygroupsig/libgroupsig_build.py
                cd $GSIG/build && cmake .. && make
            fi
            log info "Installing libgroupsig"
            cd $GSIG && python -m pip install src/wrappers/python
        fi
    fi

    log succ "Enable virtual environment with 'source $VENV/bin/activate' and run 'python3 -m autoauditor'"
}

while [ $# -gt 0 ]; do
    case $1 in
        -d|--down)
            _down=SET
            shift
            ;;
        -r|--restart)
            _restart=SET
            shift
            ;;
        -n|--no-color)
            disable_ansi_color
            shift
            ;;
        --with-groupsig)
            _groupsig=SET
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

check_required_pkgs

if [ -n "$_down" ]; then
    network_down
else
    if [ -n "$_restart" ]; then
        network_down
        network_up
    else
        up=($(docker ps -aq --filter label=autoauditor=vulnerable_net))
        cnt=$(docker compose -f $YAML config --services | wc -l)
        if [ ${#up[@]} -ne $cnt ]; then
            network_up
        fi
    fi
fi
