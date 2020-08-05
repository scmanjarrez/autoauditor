# metasploit - Metasploit helper module.

# Copyright (C) 2020 Sergio Chica Manjarrez.

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

from pymetasploit3.msfrpc import MsfRpcClient, MsfRpcError, MsfAuthError
from requests.exceptions import ConnectionError
from datetime import datetime
from io import BytesIO
import utils
import json
import os
import sys
import docker
import time

_loot_dir = None

def get_msf_connection(passwd):
    try:
        return MsfRpcClient(passwd, ssl=True)
    except ConnectionError:
        utils.log(
            'error', "Metasploit container connection error. Check container is running.", errcode=utils.EMSCONN)
    except MsfAuthError:
        utils.log(
            'error', "Metasploit container authentication error. Check password.", errcode=utils.EMSPASS)


def start_msfrpcd(loot_dir, ovpn=False, stop=False):
    global _loot_dir
    _loot_dir = loot_dir

    dockercl = docker.from_env()
    msfcont = None

    utils.log('succb', utils.MSSTAT, end='\r')

    try:
        image = dockercl.images.get('msfrpci')
        utils.log('succg', utils.MSEXIST)
    except docker.errors.ImageNotFound:
        utils.log('warn', utils.MSDOWN, end='\r')

        dckf = BytesIO(b'FROM phocean/msf\n'
                       b'RUN apt update && apt install -y iproute2 iputils-ping traceroute\n'
                       b'CMD ./msfrpcd -P dummypass && tail -f /dev/null')
        try:
            image, _ = dockercl.images.build(fileobj=dckf, tag='msfrpci')
        except docker.errors.BuildError:
            utils.log('error', "Building error.", errcode=utils.EBUILD)

        utils.log('succg', utils.MSDONE)

    utils.log('succb', utils.MSCSTAT, end='\r')

    cont_l = dockercl.containers.list(filters={'name': 'msfrpc'})
    if cont_l:
        utils.log('succg', utils.MSCR)
        msfcont = cont_l[0]
    else:
        if stop:  # if want to stop but already stopped, don't start again
            utils.log('succg', utils.MSCNR)
        else:
            utils.log('warn', utils.MSCSTART, end='\r')

            loot = os.path.join(os.getcwd(), loot_dir)
            if ovpn:
                msfcont = dockercl.containers.run(image,
                                                  'sh -c "ip route replace default via 10.10.20.2 && ./msfrpcd -P dummypass && tail -f /dev/null"',
                                                  auto_remove=True, detach=True, name='msfrpc',
                                                  cap_add='NET_ADMIN', network='attacker_network',
                                                  volumes={
                                                      loot: {'bind': '/root/.msf4/loot'}},
                                                  ports={55553: 55553})
            else:
                msfcont = dockercl.containers.run(image, auto_remove=True,
                                                  detach=True, name='msfrpc',
                                                  volumes={
                                                      loot: {'bind': '/root/.msf4/loot'}},
                                                  ports={55553: 55553})
            time.sleep(10)
            utils.log('succg', utils.MSCDONE)
    return msfcont


def launch_metasploit(msfcl, rc_file, log_file):
    print(_loot_dir)
    with open(rc_file, 'r') as f:
        try:
            rc = json.load(f)
        except json.JSONDecodeError:
            utils.log('error', "Wrong resources script file format. Check {}.".format(
                utils.RC_TEMPLATE), errcode=utils.EBADRCFMT)

    with open(log_file, 'w') as f:
        header = "#" * 62
        off = "#" * 14
        f.write("{}\n".format(header))
        f.write("{off} {repdate} {off}\n".format(
            repdate=datetime.now().astimezone(), off=off))
        f.write("{}\n\n".format(header))
        utils.log('succb', "Metasploit output log: {}".format(log_file))
        for mtype in rc:
            for mname in rc[mtype]:
                try:
                    mod = msfcl.modules.use(mtype, mname)
                except MsfRpcError:
                    utils.log(
                        'error', "Invalid module type: {}. Check {}.".format(mtype, rc_file))
                    continue
                except TypeError:
                    utils.log(
                        'error', "Invalid module: {}. Check {}.".format(mname, rc_file))
                    continue

                for expl in rc[mtype][mname]:
                    for opt in expl:
                        try:
                            if opt == "ACTION":
                                mod.action = expl[opt]
                            else:
                                mod[opt] = expl[opt]
                        except KeyError:
                            utils.log('error', "Invalid option: {}. Check {}.".format(
                                opt[0], rc_file))
                    cid = msfcl.consoles.console().cid
                    exp = "{}/{}".format(mtype, mname)
                    utils.log('succg', "Logging output: {}".format(exp))
                    f.write("##### {} #####\n\n".format(exp))
                    f.write(msfcl.consoles.console(
                        cid).run_module_with_output(mod))
                    f.write("\n######{}######\n\n".format("#"*len(exp)))
                    msfcl.consoles.destroy(cid)


if __name__ == '__main__':
    utils.log('error', "Not standalone module. Run again from autoauditor.py.",
              errcode=utils.EMODNR)
