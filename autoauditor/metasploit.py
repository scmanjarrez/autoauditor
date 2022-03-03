# SPDX-License-Identifier: GPL-3.0-or-later

# metasploit - Metasploit module.

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

from pymetasploit3.msfrpc import MsfRpcClient, MsfRpcError, MsfAuthError
from autoauditor import constants as ct
from autoauditor import utils as ut
from datetime import datetime

import requests
import docker
import errno
import json
import time


def get_msf_connection(passwd):
    try:
        return MsfRpcClient(passwd, ssl=True)
    except requests.ConnectionError:
        ut.log('error',
               ("Metasploit container: connection timed out. "
                "Check container is running."),
               err=errno.ETIMEDOUT)
    except MsfAuthError:
        ut.log('error',
               ("Metasploit container: authentication error. "
                "Check password."),
               err=errno.ECONNREFUSED)


def start_msf(loot_dir, ovpn=False):
    dcl = docker.from_env()
    msfcont = None
    ut.log('info', ct.MSSTAT, end='\r')
    try:
        image = dcl.images.get('metasploitframework/metasploit-framework')
        ut.log('succ', ct.MSEXIST)
    except docker.errors.ImageNotFound:
        ut.log('warn', ct.MSDOWN, end='\r')
        try:
            image = dcl.images.pull(
                'metasploitframework/metasploit-framework', 'latest')
        except docker.errors.APIError:
            ut.log('error', "Downloading error.", err=ct.EDDOWN)
        ut.log('succ', ct.MSDONE)
    ut.log('info', ct.MSCSTAT, end='\r')
    cont_l = dcl.containers.list(filters={'name': ct.MSF_NAME})
    if cont_l:
        ut.log('succ', ct.MSCR)
        msfcont = cont_l[0]
    else:
        ut.log('warn', ct.MSCSTART, end='\r')
        if ovpn:
            msfcont = dcl.containers.run(image,
                                         '-c "ip route replace '
                                         'default via 10.10.20.2 && '
                                         './msfrpcd -P dummypass && '
                                         'tail -f /dev/null"',
                                         entrypoint='bash',
                                         auto_remove=True,
                                         detach=True, name=ct.MSF_NAME,
                                         cap_add='NET_ADMIN',
                                         labels=ct.LABEL,
                                         network=ct.NET_NAME,
                                         volumes={
                                             loot_dir: {
                                                 'bind': ('/root/'
                                                          '.msf4/'
                                                          'loot')
                                             }
                                         },
                                         ports={
                                             55553: 55553
                                         })
        else:
            msfcont = dcl.containers.run(image,
                                         '-c "./msfrpcd -P dummypass && '
                                         'tail -f /dev/null"',
                                         entrypoint='bash',
                                         remove=True,
                                         detach=True, name=ct.MSF_NAME,
                                         labels=ct.LABEL,
                                         volumes={
                                             loot_dir: {'bind': ('/root/'
                                                                 '.msf4/'
                                                                 'loot')}
                                         },
                                         ports={55553: 55553})
        time.sleep(10)
        ut.log('succ', ct.MSCDONE)
    return msfcont


def launch_metasploit(msfcl, rc_file, log_file):
    with open(rc_file, 'r') as f:
        try:
            rc = json.load(f)
        except json.JSONDecodeError:
            ut.log('error',
                   (f"Bad resources script format: {rc_file}. "
                    f"Check {ct.RC_TEMPLATE}."),
                   err=ct.ECFGRC)
    with open(log_file, 'w') as f:
        header = "#" * 62
        off = "#" * 14
        f.write(f"{header}\n")
        f.write(f"{off} {datetime.now().astimezone()} {off}\n")
        f.write(f"{header}\n\n")
        ut.log('info', f"Metasploit output log: {log_file}")
        for mtype in rc:
            for mname in rc[mtype]:
                for opts in rc[mtype][mname]:
                    try:
                        mod = msfcl.modules.use(mtype, mname)
                    except MsfRpcError:
                        ut.log('error',
                               (f"Invalid module type: {mtype}. "
                                f"Check {rc_file}."))
                        continue
                    except TypeError:
                        ut.log(
                            'error',
                            (f"Invalid module: {mname}. "
                             f"Check {rc_file}."))
                        continue
                    else:
                        for opt in opts:
                            pay = None
                            try:
                                if opt == "ACTION":
                                    mod.action = opts[opt]
                                elif opt == "PAYLOAD":
                                    pay = msfcl.modules.use(
                                        'payload', opts[opt]['NAME'])
                                    for popt in opts[opt]['OPTIONS']:
                                        pay[popt] = (
                                            opts[opt]['OPTIONS'][popt])
                                else:
                                    mod[opt] = opts[opt]
                            except KeyError:
                                ut.log('error',
                                       (f"Invalid option: {opt}. "
                                        f"Check {rc_file}."))
                        cid = msfcl.consoles.console().cid
                        exp = f"{mtype}/{mname}"
                        ut.log('succ', f"Logging output: {exp}")
                        f.write(f"##### {exp} #####\n\n")
                        f.write(msfcl.consoles.console(
                            cid).run_module_with_output(mod, payload=pay))
                        f.write(f"\n######{'#'*len(exp)}######\n\n")
                        f.flush()
                        msfcl.consoles.destroy(cid)
