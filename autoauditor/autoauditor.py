#!/usr/bin/env python3

# autoauditor - Main program.

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

import sys
import os
import argparse
import metasploit
import wizard
import vpn
import utils
import blockchain


if __name__ == '__main__':
    utils.check_privileges()

    parser = argparse.ArgumentParser(
        description="Tool to run metasploit automatically given a resource script.")

    parser.add_argument('-v', '--ovpn', metavar='ovpn_file',
                        help="Run a vpn container in order to connect external subnet.")

    parser.add_argument('-o', '--outfile', metavar='log_file',
                        default='output/msf.log',
                        help="If present, log all output to log_file, otherwise log to output/msf.log file.")

    parser.add_argument('-d', '--outdir', metavar='gather_dir',
                        default='output/loot',
                        help="If present, store gathered data in gather_dir, otherwise store in output/loot directory.")

    parser.add_argument('-b', '--background', action='store_true',
                        help="Keep containers running in background.")

    parser.add_argument('-hc', '--hyperledgercfg', metavar='hyperledger_config_file',
                        help="If present, store reports in hyperledger blockchain using configuration in hyperledger_config_file.")

    parser.add_argument('-ho', '--hyperledgerout', metavar='hyperledger_log_file',
                        default='output/blockchain.log',
                        help="If present, log blockchain output to hyperledger_log_file, otherwise log to output/blockchain.log file.")

    parser.add_argument('--no-color', action='store_true',
                        help="Disable ANSI color output.")

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('-r', '--runrc', metavar='rc_file',
                       help="Run metasploit using rc_file")

    group.add_argument('-g', '--genrc', metavar='rc_file',
                       help="Start wizard helper to generate automated resource script file.")

    group.add_argument('-s', '--stop', action='store_true',
                       help="Stop any orphan container.")

    args = parser.parse_args()

    utils.log('normal',
              """
AutoAuditor  Copyright (C) 2020  Sergio Chica Manjarrez
This program comes with ABSOLUTELY NO WARRANTY; for details check file LICENSE.
This is free software, and you are welcome to redistribute it
under certain conditions; check file LICENSE for details.
""")

    vpncont = msfcont = None

    if args.no_color:
        utils.disable_ansi_colors()

    if args.ovpn is not None:
        assert os.path.isfile(
            args.ovpn), "File {} does not exist.".format(args.ovpn)
        vpncont = vpn.setup_vpn(args.ovpn, args.stop)

    utils.check_file_dir(args.outfile, args.outdir)

    msfcont = metasploit.start_msfrpcd(
        args.outdir, args.ovpn is not None, args.stop)

    if args.stop:
        utils.shutdown(msfcont, vpncont)
    else:
        msfclient = metasploit.get_msf_connection(utils.DEFAULT_MSFRPC_PASSWD)

        if args.genrc:
            utils.check_file_dir(args.genrc)
            wizard.generate_resources_file(msfclient, args.genrc)

        if args.runrc:
            assert os.path.isfile(
                args.runrc), "File {} does not exist.".format(args.runrc)
            metasploit.launch_metasploit(msfclient, args.runrc, args.outfile)

        if args.hyperledgercfg:
            info = blockchain.load_config(args.hyperledgercfg)
            utils.check_file_dir(args.hyperledgerout)
            blockchain.store_report(info, args.outfile, args.hyperledgerout)

        if not args.background:
            utils.shutdown(msfcont, vpncont)
