#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later

# wizard - Wizard module.

# Copyright (C) 2022 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
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

from pymetasploit3.msfrpc import MsfRpcError, ExploitModule
from autoauditor import constants as ct
from autoauditor import utils as ut
from copy import deepcopy

import readline # noqa
import json


YES = ['y', 'yes']


def get_modules(client, mtype):
    if mtype in ['encoder', 'exploit', 'payload', 'nop']:
        mtype = mtype + 's'
    return getattr(client.modules, mtype)


def get_module(client, mtype, mname):
    return client.modules.use(mtype, mname)


def get_module_info(module):
    info = deepcopy(module.info)
    del info['options']
    return info


def get_module_references(module):
    info = get_module_info(module)
    if 'references' in info:
        ref = ["-".join(rf) for rf in info['references']
               if rf[0].lower() == 'cve']
    return ref if ref else ['CVE info not present']


def get_module_options(module):
    opts = {opt: module[opt] if module[opt] is not None else ''
            for opt in module.options}
    ropts = module.required
    return opts, ropts


def get_option_info(module, option):
    if option == 'ACTION':
        return module.actions
    return module.optioninfo(option)


def get_option_desc(module, option):
    try:
        if option == 'ACTION':
            return 'Specifiy the action for this module'
        return module.optioninfo(option)['desc']
    except KeyError:
        return ''


def has_payloads(module):
    return isinstance(module, ExploitModule) and len(module.payloads) > 0


def get_module_payloads(module):
    return module.payloads


def get_payload(client, payload):
    return client.modules.use('payload', payload)


def set_options(mod):
    mod_options = {}
    adv = str.lower(input("[*] Advanced options [y/N]: ")) in YES
    ut.log('succg',
           "Current options: missing and required => red, required => yellow")
    ut.print_options(mod, adv)
    eof = False
    modify = str.lower(input("[*] Modify [y/N]: ")) in YES
    if not modify and mod.missing_required:
        modify = str.lower(input((f"[!] Following options missing: "
                                  f"{', '.join(mod.missing_required)}.\n"
                                  f"[*] Modify [y/N]: "))
                           ) in YES
    while modify:
        try:
            ut.log(
                'succb',
                "Finish with EOF (Ctrl+D)")
            while True:
                opt = input("[*] Option (case sensitive): ")
                try:
                    opt_info = get_option_info(mod, opt)
                except KeyError:
                    ut.log('error', f"Invalid option: {opt}")
                    continue
                val = ut.correct_type(
                    input(f"[*] {opt} value: "),
                    opt_info)
                if val.startswith(('Invalid', 'Missing')):
                    ut.log('error',
                           (f"Invalid or missing value, "
                            f"must be {opt_info['type']}: {opt}"))
                    continue
                try:
                    mod[opt] = val
                except KeyError:
                    ut.log('error',
                           f"Unexpected error: option = {opt} value = {val}")
                else:
                    mod_options[opt] = val
                eof = False
        except EOFError:
            print()
            if eof:  # avoid infinite loop if consecutives Ctrl+D
                break
            ut.log('succb',
                   ("Final options: missing and required => red, "
                    "required => yellow"))
            ut.print_options(mod, adv)
            eof = True
        modify = str.lower(input("[*] Modify [y/N]: ")) in YES
        if not modify and mod.missing_required:
            modify = str.lower(input((f"[!] Following options missing: "
                                      f"{', '.join(mod.missing_required)}.\n"
                                      f"[*] Modify [y/N]: ")
                                     )
                               ) in YES
        eof = False
    return mod_options


def generate_resources_file(client, rc_out):
    more_mod = True
    modules = {}
    mod_opts = {}
    while more_mod:
        try:
            mod = None
            while mod is None:
                mtype = input(
                    f"[*] Module type ({'|'.join(ct.MOD_TYPES)}): ")
                mname = input("[*] Module: ")
                try:
                    mod = get_module(client, mtype, mname)
                except MsfRpcError:
                    ut.log(
                        'error',
                        f"Invalid module type: {mtype}.")
                except TypeError:
                    ut.log(
                        'error',
                        f"Invalid module: {mname}.")
                else:
                    if mtype not in modules:
                        modules[mtype] = {}
                    if mname not in modules[mtype]:
                        modules[mtype][mname] = []
            mod_opts = set_options(mod)
            if mtype == 'exploit':
                if str.lower(input("[*] Add payload [y/N]: ")) in YES:
                    payload = None
                    while payload is None:
                        pname = input("[*] Payload: ")
                        try:
                            payload = get_module(client, 'payload', pname)
                        except TypeError:
                            ut.log(
                                'error',
                                f"Invalid payload: {pname}")
                    pay_opts = set_options(payload)
                    mod_opts['PAYLOAD'] = {'NAME': pname,
                                           'OPTIONS': pay_opts}
            modules[mtype][mname].append(mod_opts)
            if str.lower(input("[*] More modules [y/N]: ")) not in YES:
                more_mod = False
        except EOFError:
            print()
            break
    with open(rc_out, 'w') as f:
        json.dump(modules, f, indent=2)
        ut.log('succg',
               f"Resource script correctly generated in {rc_out}")
