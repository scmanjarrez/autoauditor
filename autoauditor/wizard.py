#!/usr/bin/env python3

# wizard - Wizard module.

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

from pymetasploit3.msfrpc import MsfRpcError, PayloadModule, ExploitModule
import constants as const
import utils
import json
import argparse
import metasploit
import readline
import sys
import os


YES = ['y', 'yes']


def _get_module(client, mtype, mname):
    return client.modules.use(mtype, mname)


def _get_modules(client, mtype):
    if mtype in ['encoder', 'exploit', 'payload', 'nop']:
        mtype = mtype + 's'
    return getattr(client.modules, mtype)


def _get_option_info(module, option):
    if option == 'ACTION':
        return module.actions
    return module.optioninfo(option)


def _get_option_desc(module, option):
    try:
        return module.optioninfo(option)['desc']
    except:
        return ''


def _get_module_options(module):
    opts = {opt: module[opt] if module[opt] is not None else ''
            for opt in module.options}
    ropts = module.required
    return opts, ropts

def _has_payloads(module):
    return isinstance(module, ExploitModule) and len(module.payloads) > 0


def _get_module_payloads(module):
    return module.payloads

def _get_payload(client, payload):
    return client.modules.use('payload', payload)


def set_options(mod, opt_d={}):
    ispayload = isinstance(mod, PayloadModule)

    adv = str.lower(input("[*] Advanced options [y/N]: ")) in YES

    utils.log(
        'succg', "Current options: missing and required => red, required => yellow")
    utils.print_options(mod, adv)

    eof = False
    modify = str.lower(input("[*] Modify [y/N]: ")) in YES

    while modify:
        try:
            utils.log('succb', "Finish with EOF (Ctrl+D)")
            while True:
                opt = input("[*] Option (case sensitive): ")
                val = utils.correct_type(
                    input("[*] {} value: ".format(opt)))
                try:
                    mod[opt] = val
                except KeyError:
                    utils.log(
                        'error', "Invalid option: {}".format(opt))
                else:
                    if ispayload:
                        opt_d['PAYLOAD.' + opt] = val
                    else:
                        opt_d[opt] = val
                eof = False
        except EOFError:
            print()
            if eof:  # avoid infinite loop if consecutives Ctrl+D
                break
            utils.log(
                'succb', "Final options: missing and required => red, required => yellow")
            utils.print_options(mod, adv)
            eof = True

        modify = str.lower(input("[*] Modify [y/N]: ")) in YES
        eof = False

    return opt_d


def generate_resources_file(client, rc_out):
    more_mod = True
    rc_file = {}

    while more_mod:
        try:
            mod = None
            while mod is None:
                mtype = input(
                    "[*] Module type ({}): ".format("|".join(const.MODULE_TYPES)))
                mname = input("[*] Module: ")
                try:
                    mod = _get_module(client, mtype, mname)
                except MsfRpcError:
                    utils.log('error', "Invalid module type: {}.".format(mtype))
                except TypeError:
                    utils.log('error', "Invalid module: {}.".format(mname))
                else:
                    if mtype not in rc_file:
                        rc_file[mtype] = {}
                    if mname not in rc_file[mtype]:
                        rc_file[mtype][mname] = []

            opt_d = set_options(mod)

            if str.lower(input("[*] Add payload [y/N]: ")) in YES:
                payload = None
                while payload is None:
                    pname = input("[*] Payload: ")
                    try:
                        payload = _get_module(client, 'payload', pname)
                    except TypeError:
                        utils.log(
                            'error', "Invalid payload: {}".format(pname))
                opt_d['PAYLOAD'] = pname
                opt_d = set_options(payload, opt_d)

            rc_file[mtype][mname].append(opt_d)

            if str.lower(input("[*] More modules [y/N]: ")) not in YES:
                more_mod = False
        except EOFError:
            print()
            break

    with open(rc_out, 'w') as f:
        json.dump(rc_file, f, indent=2)
        utils.log('succg', "Resource script correctly generated in {}".format(rc_out))


def main():
    parser = argparse.ArgumentParser(
        description="Tool to run metasploit automatically given a resource script.")

    parser.add_argument('-g', '--genrc', metavar='rc_file',
                        default='rc.json',
                        help="Run wizard and generate out_rcfile.")

    parser.add_argument('-d', '--outdir', metavar='gather_dir',
                        default='/tmp/output',
                        help="Temporary metasploit RPC service directory.")

    args = parser.parse_args()

    utils.copyright()

    msfcont = metasploit.start_msfrpcd(args.outdir)
    msfclient = metasploit.get_msf_connection(const.DEFAULT_MSFRPC_PASSWD)

    utils.check_file_dir(args.genrc)

    generate_resources_file(msfclient, args.genrc)

    utils.shutdown(msfcont)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        utils.log('normal', '\n')
        utils.log(
            'error', 'Interrupted, exiting program. Containers will keep running ...')
        try:
            sys.exit(1)
        except SystemExit:
            os._exit(1)
