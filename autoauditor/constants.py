# SPDX-License-Identifier: GPL-3.0-or-later

# constants - Constant definitions file.

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

from pathlib import Path

# Error Codes
# Docker related errors
EDAPI = 201  # API
EDDOWN = 202  # Downloading from dockerhub
EDNONET = 203  # Network missing
EDPERM = 204  # Operation not permitted, are you in docker group?
# Format
ECFGRC = 205  # Bad resources script format
ECFGNET = 206  # Bad network configuration file (format)
EREP = 207  # Bad report (format)
# Fabric
EHLFST = 212  # Can not store report

# Attacker network
NET_NAME = 'autoauditor_attacker_net'
VPN_NAME = 'autoauditor_vpn_client'
MSF_NAME = 'autoauditor_msf'
LABEL = {'autoauditor': 'attacker_net'}


# Metasploit
DEF_MSFRPC_PWD = 'dummypass'

# Default paths
DEF_DIR = 'output'
DEF_OUT = f'{DEF_DIR}/msf.log'
DEF_BLOCK = f'{DEF_DIR}/blockchain.log'
DEF_TEMPLATE = 'tools/templates'

# Templates
RC_TEMPLATE = Path(f'{DEF_TEMPLATE}/rc.template').absolute()
VPN_TEMPLATE = Path(f'{DEF_TEMPLATE}/ovpn.template').absolute()
NET_TEMPLATE = Path(f'{DEF_TEMPLATE}/network.template').absolute()

# Log Messages

MSSTAT = "Metasploit image status:"
MSEXIST = "Metasploit image status: exists."
MSDOWN = "Metasploit image status: does not exist, downloading ..."
MSDONE = "Metasploit image status: does not exist, downloading ... done"
MSCSTAT = "Metasploit container status:"
MSCR = "Metasploit container status: running."
MSCSTART = "Metasploit container status: not running, starting ..."
MSCDONE = "Metasploit container status: not running, starting ... done"
VPNSTAT = "VPN client image status:"
VPNEXIST = "VPN client image status: exists."
VPNDOWN = "VPN client image status: does not exist, downloading ..."
VPNDONE = "VPN client image status: does not exist, downloading ... done"
VPNCSTAT = "VPN client container status:"
VPNCR = "VPN client container status: running."
VPNCSTART = "VPN client container status: not running, starting ..."
VPNCDONE = "VPN client container status: not running, starting ... done"
CNTSTOP = "Stopping containers ..."
CNTSTOPPED = "Stopping containers ... done"
CNTSTOPERR = "Stopping containers ... error. Some containers may be running."
ATNET = "Removing attacker_network ..."
ATNETRM = "Removing attacker_network ... done"
ATNETAEND = "Removing attacker_network ... error. Active endpoints."
PRSREP = "Parsing report ..."
PRSDREP = "Parsing report ... done"
PRSREPERR = "Parsing report ... error. Wrong report format."
MOD_TYPES = ['auxiliary', 'encoder', 'exploit', 'nop', 'payload', 'post']

# Copyright
COPYRIGHT = """
autoauditor  Copyright (C) 2022 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
Universidad Carlos III de Madrid.
This program comes with ABSOLUTELY NO WARRANTY; for details check below.
This is free software, and you are welcome to redistribute it
under certain conditions; check below for details.
"""
