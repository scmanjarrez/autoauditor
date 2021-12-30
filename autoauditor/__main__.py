#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later

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

from autoauditor import blockchain as bc
from autoauditor import metasploit as ms
from autoauditor import constants as ct
from autoauditor import wizard as wz
from autoauditor import utils as ut
from autoauditor import gui
from autoauditor import vpn

import argparse
import errno


def start_containers(args):
    if args.v is not None:
        vpn.start_vpn(args.v, args.cmd == 'stop')
    return ms.start_msf(
        args.od, args.v is not None, args.cmd == 'stop')


def verify_arguments(parser, args):
    if args.cmd in ('cli', 'wizard') and args.r is None:
        parser.error("the following arguments are required: -r")
    if args.cmd == 'store':
        if args.of is None:
            parser.error("the following arguments are required: -of")
        if args.od is None:
            parser.error("the following arguments are required: -od")
        if args.b is None:
            parser.error("the following arguments are required: -b")

    if args.cmd == 'cli':
        ut.check_readf(args.r)
        ut.check_writef(args.of)
        ut.check_writed(args.od)
        if args.v:
            ut.check_readf(args.v)
        if args.b:
            ut.check_readf(args.b)
            ut.check_writef(args.ob)

    if args.cmd == 'wizard':
        ut.check_writef(args.r)
        ut.check_writed(args.od)
        if args.v:
            ut.check_readf(args.v)

    if args.cmd == 'store':
        ut.check_readf(args.b)
        ut.check_readf(args.of)
        ut.check_writef(args.ob)


def set_arguments():
    parser = argparse.ArgumentParser(
        description=("Semi-automatic scanner and vulnerability exploiter."))
    cmds = parser.add_argument_group("commands")
    group = cmds.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--cli',
                       action='store_const', dest='cmd',
                       const='cli',
                       help="Launch CLI submodule.")
    group.add_argument('-g', '--gui',
                       action='store_const', dest='cmd',
                       const='gui',
                       help="Launch GUI submodule.")
    group.add_argument('-s', '--store',
                       action='store_const', dest='cmd',
                       const='store',
                       help="Launch store submodule.")
    group.add_argument('-t', '--stop',
                       action='store_const', dest='cmd',
                       const='stop',
                       help="Stop orphan containers.")
    group.add_argument('-w', '--wizard',
                       action='store_const', dest='cmd',
                       const='wizard',
                       help="Launch wizard submodule.")
    cmd_opt = parser.add_argument_group("command options")
    cmd_opt.add_argument('-r',
                         metavar='rc_file',
                         help="Path to resources script.")
    cmd_opt.add_argument('-v',
                         metavar='vpn_cfg',
                         help="Launch vpn container using given config.")
    cmd_opt.add_argument('-b',
                         metavar='bc_cfg',
                         help=("Store reports in blockchain using "
                               "given config."))
    log_opt = parser.add_argument_group("log options")
    log_opt.add_argument('-of',
                         metavar='log_file', default=ct.DEF_OUT,
                         help=f"Path to log file. Default: {ct.DEF_OUT}.")
    log_opt.add_argument('-od',
                         metavar='log_dir', default=ct.DEF_DIR,
                         help=f"Path to log directory. Default: {ct.DEF_DIR}.")
    log_opt.add_argument('-ob',
                         metavar='bc_log_file', default=ct.DEF_BLOCK,
                         help=(f"Path to blockchain log file. "
                               f"Default: {ct.DEF_BLOCK}."))
    misc_opt = parser.add_argument_group("misc options")
    misc_opt.add_argument('--background',
                          action='store_true',
                          help="Keep containers running in background.")
    misc_opt.add_argument('--no-color',
                          action='store_true',
                          help="Disable ANSI color output.")
    return parser, parser.parse_args()


def main():
    ut.check_privileges()
    parser, args = set_arguments()
    verify_arguments(parser, args)

    if args.no_color:
        ut.disable_ansi_colors()

    if args.cmd != 'gui':
        ut.copyright()
        msf = start_containers(args)
        if msf is not None:
            msfclient = ms.get_msf_connection(ct.DEF_MSFRPC_PWD)
            if args.cmd == 'cli':
                ms.launch_metasploit(msfclient, args.r, args.of)
            elif args.cmd == 'wizard':
                wz.generate_resources_file(msfclient, args.r)

            if args.cmd in ('cli', 'store') and args.b:
                info = bc.load_config(args.b)
                if info is not None:
                    bc.store_report(info, args.of, args.ob)
        if not args.background:
            ut.shutdown()
    else:
        gui.main()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        ut.log('normal', '\n')
        ut.log('error',
               "Interrupted, exiting program. "
               "Containers still running ...")
        exit(errno.EINTR)
