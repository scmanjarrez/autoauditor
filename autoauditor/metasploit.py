# metasploit - Metasploit helper module.

# Copyright (C) 2020 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
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

from pymetasploit3.msfrpc import MsfRpcClient, MsfRpcError, MsfAuthError
from requests.exceptions import ConnectionError
from datetime import datetime
from io import BytesIO
import constants as const
import utils
import json
import os
import sys
import docker
import time



def ispayloadoption(opt, check=True):
    if isinstance(opt, str):
        pay = opt.split('.')
        if len(pay) == 2 and pay[0] == 'PAYLOAD' and pay[1]:
            if check:
                return True
            else:
                return pay[1]

def get_msf_connection(passwd):
    try:
        return MsfRpcClient(passwd, ssl=True)
    except ConnectionError:
        utils.log(
            'error', "Metasploit container connection error. Check container is running.", errcode=const.EMSCONN)
    except MsfAuthError:
        utils.log(
            'error', "Metasploit container authentication error. Check password.", errcode=const.EMSPASS)


def start_msfrpcd(loot_dir, ovpn=False, stop=False):
    dockercl = docker.from_env()
    msfcont = None

    utils.log('succb', const.MSSTAT, end='\r')

    try:
        image = dockercl.images.get('msfrpci')
        utils.log('succg', const.MSEXIST)
    except docker.errors.ImageNotFound:
        utils.log('warn', const.MSDOWN, end='\r')

        dckf = BytesIO(b'FROM phocean/msf\n'
                       b'RUN apt update && apt install -y iproute2 iputils-ping traceroute\n'
                       b'CMD ./msfrpcd -P dummypass && tail -f /dev/null')
        try:
            image, _ = dockercl.images.build(fileobj=dckf, tag='msfrpci')
        except docker.errors.BuildError:
            utils.log('error', "Building error.", errcode=const.EBUILD)

        utils.log('succg', const.MSDONE)

    utils.log('succb', const.MSCSTAT, end='\r')

    cont_l = dockercl.containers.list(filters={'name': 'msfrpc'})
    if cont_l:
        utils.log('succg', const.MSCR)
        msfcont = cont_l[0]
    else:
        if stop:  # if want to stop but already stopped, don't start again
            utils.log('succg', const.MSCNR)
        else:
            utils.log('warn', const.MSCSTART, end='\r')

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
            utils.log('succg', const.MSCDONE)
    return msfcont


def launch_metasploit(msfcl, rc_file, log_file):
    with open(rc_file, 'r') as f:
        try:
            rc = json.load(f)
        except json.JSONDecodeError:
            utils.log('error', "Wrong resources script file format. Check {}.".format(
                utils.RC_TEMPLATE), errcode=const.EBADRCFMT)

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
                    payload = None
                    for opt in expl:
                        try:
                            if opt == "ACTION":
                                mod.action = expl[opt]
                            elif opt == "PAYLOAD":
                                payload = msfcl.modules.use('payload', expl[opt])
                            elif ispayloadoption(opt):
                                if payload is None:
                                    utils.log('error', "Payload must be placed before payload options in {}.".format(
                                        opt, rc_file))
                                else:
                                    payload[ispayloadoption(opt, check=False)] = expl[opt]
                            else:
                                mod[opt] = expl[opt]
                        except KeyError:
                            utils.log('error', "Invalid option: {}. Check {}.".format(
                                opt, rc_file))
                    cid = msfcl.consoles.console().cid
                    exp = "{}/{}".format(mtype, mname)
                    utils.log('succg', "Logging output: {}".format(exp))
                    f.write("##### {} #####\n\n".format(exp))
                    f.write(msfcl.consoles.console(
                        cid).run_module_with_output(mod, payload=payload))
                    f.write("\n######{}######\n\n".format("#"*len(exp)))
                    msfcl.consoles.destroy(cid)


if __name__ == '__main__':
    utils.log('error', "Not standalone module. Run again from autoauditor.py.",
              errcode=const.EMODNR)
