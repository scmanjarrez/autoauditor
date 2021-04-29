# metasploit - Metasploit helper module.

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

from pymetasploit3.msfrpc import MsfRpcClient, MsfRpcError, MsfAuthError
from datetime import datetime
from io import BytesIO
import constants as cst
import requests
import docker
import utils
import json
import time
import os


def get_msf_connection(passwd):
    try:
        return MsfRpcClient(passwd, ssl=True)
    except requests.ConnectionError:
        utils.log(
            'error',
            ("Metasploit container connection error. "
             "Check container is running."), errcode=cst.EMSCONN)
    except MsfAuthError:
        utils.log(
            'error',
            "Metasploit container authentication error. Check password.",
            errcode=cst.EMSPASS)


def start_msfrpcd(loot_dir, ovpn=False, stop=False):
    dockercl = docker.from_env()
    msfcont = None

    utils.log('succb', cst.MSSTAT, end='\r')

    try:
        image = dockercl.images.get('msfrpci')
        utils.log('succg', cst.MSEXIST)
    except docker.errors.ImageNotFound:
        utils.log('warn', cst.MSDOWN, end='\r')

        dckf = BytesIO(b'FROM phocean/msf\n'
                       b'RUN apt update && apt install -y '
                       b'iproute2 iputils-ping traceroute\n'
                       b'CMD ./msfrpcd -P dummypass '
                       b'&& tail -f /dev/null')
        try:
            image, _ = dockercl.images.build(fileobj=dckf, tag='msfrpci')
        except docker.errors.BuildError:
            utils.log('error', "Building error.", errcode=cst.EBUILD)

        utils.log('succg', cst.MSDONE)

    utils.log('succb', cst.MSCSTAT, end='\r')

    cont_l = dockercl.containers.list(filters={'name': 'msfrpc'})
    if cont_l:
        utils.log('succg', cst.MSCR)
        msfcont = cont_l[0]
    else:
        if stop:  # if want to stop but already stopped, don't start again
            utils.log('succg', cst.MSCNR)
        else:
            utils.log('warn', cst.MSCSTART, end='\r')

            loot = os.path.join(os.getcwd(), loot_dir)
            if ovpn:
                msfcont = dockercl.containers.run(image,
                                                  ('sh -c "ip route replace '
                                                   'default via 10.10.20.2 && '
                                                   './msfrpcd -P dummypass && '
                                                   'tail -f /dev/null"'),
                                                  auto_remove=True,
                                                  detach=True, name='msfrpc',
                                                  cap_add='NET_ADMIN',
                                                  network='attacker_network',
                                                  volumes={
                                                      loot: {
                                                          'bind': ('/root/'
                                                                   '.msf4/'
                                                                   'loot')
                                                      }
                                                  },
                                                  ports={
                                                      55553: 55553
                                                  })
            else:
                msfcont = dockercl.containers.run(image, auto_remove=True,
                                                  detach=True, name='msfrpc',
                                                  volumes={
                                                      loot: {'bind': ('/root/'
                                                                      '.msf4/'
                                                                      'loot')}
                                                  },
                                                  ports={55553: 55553})
            time.sleep(10)
            utils.log('succg', cst.MSCDONE)
    return msfcont


def launch_metasploit(msfcl, rc_file, log_file):
    with open(rc_file, 'r') as f:
        try:
            rc = json.load(f)
        except json.JSONDecodeError:
            utils.log('error',
                      (f"Wrong resources script file format. "
                       f"Check {utils.RC_TEMPLATE}."),
                      errcode=cst.EBADRCFMT)

    with open(log_file, 'w') as f:
        header = "#" * 62
        off = "#" * 14
        f.write(f"{header}\n")
        f.write(f"{off} {datetime.now().astimezone()} {off}\n")
        f.write(f"{header}\n\n")
        utils.log('succb', f"Metasploit output log: {log_file}")
        for mtype in rc:
            for mname in rc[mtype]:
                for opts in rc[mtype][mname]:
                    try:
                        mod = msfcl.modules.use(mtype, mname)
                    except MsfRpcError:
                        utils.log(
                            'error',
                            f"Invalid module type: {mtype}. Check {rc_file}.")
                        continue
                    except TypeError:
                        utils.log(
                            'error',
                            (f"Invalid module: {mname}. Check {rc_file}."))
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
                                utils.log('error',
                                          (f"Invalid option: {opt}. "
                                           f"Check {rc_file}."))
                        cid = msfcl.consoles.console().cid
                        exp = f"{mtype}/{mname}"
                        utils.log('succg', f"Logging output: {exp}")
                        f.write(f"##### {exp} #####\n\n")
                        f.write(msfcl.consoles.console(
                            cid).run_module_with_output(mod, payload=pay))
                        f.write(f"\n######{'#'*len(exp)}######\n\n")
                        msfcl.consoles.destroy(cid)


if __name__ == '__main__':
    utils.log('error', "Not standalone module. Run again from autoauditor.py.",
              errcode=cst.EMODNR)
