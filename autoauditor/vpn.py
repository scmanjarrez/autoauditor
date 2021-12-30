# SPDX-License-Identifier: GPL-3.0-or-later

# vpn - VPN module.

# Copyright (C) 2021 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
# Universidad Carlos III de Madrid.

# This file is part of AutoAuditor.

# AutoAuditor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# AutoAuditor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with GNU Emacs.  If not, see <https://www.gnu.org/licenses/>.

from autoauditor import constants as ct
from autoauditor import utils as ut

import docker
import os


def start_vpn(ovpn_file, stop=False):
    dcl = docker.from_env()
    vpncont = None
    ut.log('succb', ct.VPNSTAT, end='\r')
    try:
        image = dcl.images.get('dperson/openvpn-client')
        ut.log('succg', ct.VPNEXIST)
    except docker.errors.ImageNotFound:
        ut.log('warn', ct.VPNDOWN, end='\r')
        try:
            image = dcl.images.pull('dperson/openvpn-client', 'latest')
        except docker.errors.APIError:
            ut.log('error', "Downloading error.", err=ct.EDDOWN)
        ut.log('succg', ct.VPNDONE)
    ut.log('succb', ct.VPNCSTAT, end='\r')
    vpn_l = dcl.containers.list(filters={'name': ct.VPN_NAME})
    if vpn_l:
        ut.log('succg', ct.VPNCR)
        vpncont = vpn_l[0]
    else:
        if stop:  # if want to stop but already stopped, don't start again
            ut.log('succg', ct.VPNCNR)
        else:
            ut.log('warn', ct.VPNCSTART, end='\r')
            of = os.path.abspath(ovpn_file)
            ipam_pool = docker.types.IPAMPool(subnet='10.10.20.0/24')
            ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
            try:
                net = dcl.networks.get(ct.NET_NAME)
            except docker.errors.NotFound:
                net = dcl.networks.create(
                    ct.NET_NAME, driver='bridge', ipam=ipam_config)
            vpncont = dcl.containers.run(image, ('sh -c "sleep 5 && '
                                                 '/sbin/tini -- '
                                                 '/usr/bin/openvpn.sh"'),
                                         auto_remove=True,
                                         stdin_open=True, tty=True,
                                         detach=True, cap_add='NET_ADMIN',
                                         security_opt=['label:disable'],
                                         tmpfs={
                                             '/run': '',
                                             '/tmp': ''},
                                         name=ct.VPN_NAME,
                                         labels=ct.LABEL,
                                         network=ct.NET_NAME,
                                         volumes={
                                             '/dev/net': {
                                                 'bind': '/dev/net',
                                                 'mode': 'z'
                                             },
                                             of: {
                                                 'bind': '/vpn/vpn.ovpn'
                                             }
                                         },
                                         environment={
                                             'DEFAULT_GATEWAY': 'false',
                                             'ROUTE': '10.10.20.0/24'})
            try:
                net = dcl.networks.get('bridge')
            except docker.errors.NotFound:
                ut.log('error', "Docker 'bridge' network not found.",
                       err=ct.EDNONET)
            else:
                net.connect(ct.VPN_NAME)
            ut.log('succg', ct.VPNCDONE)
    return vpncont
