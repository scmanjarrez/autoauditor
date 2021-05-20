#!/usr/bin/env python3

# autoauditor - Main program.

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

import constants as cst
import blockchain
import metasploit
import argparse
import wizard
import utils
import sys
import vpn
import os


def main():
    utils.check_privileges()

    parser = argparse.ArgumentParser(
        description=("Tool to run metasploit automatically "
                     "given a resource script."))

    parser.add_argument('-v', '--ovpn',
                        metavar='ovpn_file',
                        help=("Run a vpn container "
                              "in order to connect external subnet."))

    parser.add_argument('-o', '--outfile',
                        metavar='log_file',
                        default='output/msf.log',
                        help=("If present, log all output to log_file, "
                              "otherwise log to output/msf.log file."))

    parser.add_argument('-d', '--outdir',
                        metavar='gather_dir',
                        default='output/loot',
                        help=("If present, store gathered data in gather_dir, "
                              "otherwise store in output/loot directory."))

    parser.add_argument('-b', '--background',
                        action='store_true',
                        help="Keep containers running in background.")

    parser.add_argument('-hc', '--hyperledgercfg',
                        metavar='hyperledger_config_file',
                        help=("If present, store reports in "
                              "hyperledger blockchain using "
                              "configuration in hyperledger_config_file."))

    parser.add_argument('-ho', '--hyperledgerout',
                        metavar='hyperledger_log_file',
                        default='output/blockchain.log',
                        help=("If present, log blockchain output "
                              "to hyperledger_log_file, otherwise log "
                              "to output/blockchain.log file."))

    parser.add_argument('--no-color',
                        action='store_true',
                        help="Disable ANSI color output.")

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('-r', '--runrc',
                       metavar='rc_file',
                       help="Run metasploit using rc_file")

    group.add_argument('-g', '--genrc',
                       metavar='rc_file',
                       help=("Start wizard helper to generate "
                             "a resource script file."))

    group.add_argument('-s', '--stop',
                       action='store_true',
                       help="Stop any orphan container.")

    args = parser.parse_args()

    utils.copyright()

    vpncont = msfcont = None

    if args.no_color:
        utils.disable_ansi_colors()

    if args.ovpn is not None:
        if not os.path.isfile(args.ovpn):
            utils.log(
                'error',
                f"File {args.ovpn} does not exist.",
                errcode=cst.ENOENT)
        vpncont = vpn.setup_vpn(args.ovpn, args.stop)

    utils.check_file_dir(args.outfile, args.outdir)

    msfcont = metasploit.start_msfrpcd(
        args.outdir, args.ovpn is not None, args.stop)

    if args.stop:
        utils.shutdown(msfcont, vpncont)
    else:
        msfclient = metasploit.get_msf_connection(cst.DEF_MSFRPC_PWD)

        if args.genrc:
            utils.check_file_dir(args.genrc)
            wizard.generate_resources_file(msfclient, args.genrc)

        if args.runrc:
            if not os.path.isfile(args.runrc):
                utils.log('error',
                          f"File {args.runrc} does not exist.",
                          errcode=cst.ENOENT)
            metasploit.launch_metasploit(msfclient, args.runrc, args.outfile)

        if args.hyperledgercfg:
            info = blockchain.load_config(args.hyperledgercfg)
            if info is not None:
                utils.check_file_dir(args.hyperledgerout)
                blockchain.store_report(
                    info, args.outfile, args.hyperledgerout)

        if not args.background:
            utils.shutdown(msfcont, vpncont)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        utils.log(
            'normal',
            '\n')
        utils.log(
            'error',
            "Interrupted, exiting program. Containers will keep running ...")

        sys.exit(cst.EINTR)
