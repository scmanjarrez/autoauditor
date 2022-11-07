#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later

# wizard - Wizard module.

# Copyright (C) 2020-2022 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from pymetasploit3.msfrpc import MsfRpcError, ExploitModule
from autoauditor import constants as ct
from autoauditor import utils as ut
from copy import deepcopy

import readline
import json


readline.parse_and_bind("tab: complete")
readline.set_completer_delims(' ')

YES = ['y', 'yes']
QUEST = {
    'mod': "[*] Modify [y/N]: ",
    'pay': "[*] Add payload [y/N]: ",
    'end': "[*] Finish [y/N]: ",
    'trc': "[!] Resources script file not empty. Truncate [y/N]: "
}


class Completer:
    def set_client(self, client):
        self.client = client

    def complete_mtypes(self):
        self.completions = ct.MOD_TYPES

    def complete_yes_no(self):
        self.completions = ['y', 'n']

    def complete_mnames(self, mtype):
        self.completions = mnames(self.client, mtype)

    def complete_options(self, module):
        self.completions = module.options()

    def complete_optvalues(self, opt_info, action=False):
        if action:
            self.completions = opt_info.values()
        else:
            if opt_info['type'] == 'enum':
                self.completions = opt_info['enums']
            elif opt_info['type'] == 'bool':
                self.completions = ['True', 'False']
            else:
                self.completions = []

    def complete_payloads(self, module):
        self.completions = module.payloads()

    def complete(self, text, state):
        res = None
        comp = [x for x in self.completions if x.startswith(text)]
        if state < len(comp):
            res = comp[state]
        return res


completer = Completer()
readline.set_completer(completer.complete)


def mnames(client, mtype):
    if mtype in ['encoder', 'exploit', 'payload', 'nop']:
        mtype = mtype + 's'
    return getattr(client.modules, mtype)


class Module:
    _sym = {
        'good': '- ',
        'req': (f'{ut.LOG["colors"]["warn"]}* '
                f'{ut.LOG["colors"]["reset"]}'),
        'mreq': (f'{ut.LOG["colors"]["error"]}! '
                 f'{ut.LOG["colors"]["reset"]}')
    }

    def __init__(self, client, mtype, mname):
        self.mod = client.modules.use(mtype, mname)
        self.client = client

    def info(self):
        minfo = deepcopy(self.mod.info)
        del minfo['options']
        return minfo

    def references(self):
        minfo = self.info()
        ref = ["CVE info not present"]
        if 'references' in minfo:
            ref = ["-".join(rf) for rf in minfo['references']
                   if rf[0].lower() == 'cve']
        return ref

    def options(self):
        return self.mod.options

    def opt_info(self, opt):
        if opt == 'ACTION':
            return self.mod.actions
        return self.mod.optioninfo(opt)

    def opt_desc(self, opt):
        if opt == 'ACTION':
            return 'Specifiy the action for this module'
        try:
            return self.mod.optioninfo(opt)['desc']
        except KeyError:
            return ''

    def required(self):
        return self.mod.required

    def missing(self):
        return self.mod.missing_required

    def has_payloads(self):
        return (isinstance(self.mod, ExploitModule) and
                len(self.mod.payloads) > 0)

    def payloads(self):
        return self.mod.payloads

    def payload(self, payload):
        return self.client.modules.use('payload', payload)

    def print_options(self):
        ut.log('succ',
               "Current options (required: yellow, required & missing: red)")
        opts = self.options()
        opts_req = self.required()
        opts_mreq = self.missing()
        for opt in sorted(opts):
            sym = self._sym['good']
            if opt == 'ACTION':
                print(f"    {self._sym['req']}{opt} (enum): {self.mod.action}")
            else:
                if opt in opts_req:
                    sym = self._sym['req']
                    if opt in opts_mreq:
                        sym = self._sym['mreq']
                val = self.mod[opt] if self.mod[opt] is not None else ''
                print(f"    {sym}{opt} ({self.opt_info(opt)['type']}): {val}")


def ask(atype='mod'):
    completer.complete_yes_no()
    return input(QUEST[atype]).lower() in YES


def check_modify(mod):
    modify = ask()
    missing = mod.missing()
    if not modify and missing:
        ut.log('error', f"Following options missing: {', '.join(missing)}")
        modify = ask()
    return modify


def set_options(module):
    mod_options = {}
    module.print_options()
    eof = False
    modify = check_modify(module)
    while modify:
        try:
            ut.log(
                'info',
                "Finish with EOF (Ctrl+D)")
            while True:
                completer.complete_options(module)
                opt = input("[*] Option: ")
                try:
                    opt_info = module.opt_info(opt)
                except KeyError:
                    ut.log('error', f"Invalid option: {opt}")
                    continue
                if opt == 'ACTION':
                    completer.complete_optvalues(opt_info, True)
                else:
                    completer.complete_optvalues(opt_info)
                corr, val = ut.correct_type(input(f"[*] {opt} value: "),
                                            opt_info)
                if not corr:
                    ut.log('error', val)
                    continue
                try:
                    if opt == 'ACTION':
                        module.mod.action = val
                    else:
                        module.mod[opt] = val
                except KeyError:
                    ut.log('error',
                           f"Unexpected error: option = {opt}, value = {val}")
                else:
                    mod_options[opt] = val
                eof = False
        except EOFError:
            print()
            if eof:  # avoid infinite loop if consecutive Ctrl+D
                break
            module.print_options()
            eof = True
        modify = check_modify(module)
        eof = False
    return mod_options


def generate_resources_file(client, rc_out, cvescanner=None):
    more_mod = True
    modules = parse_rc(client, rc_out)
    if cvescanner is not None:
        exploits = parse_cvescanner(cvescanner)
        for mtype, mname in exploits:
            ut.initialize(modules, mtype, mname)
    completer.set_client(client)
    ut.log('info', "Generate the resources file with EOF (Ctrl+D)")
    ut.log('info', "Input can be autocompleted with TAB.")
    while more_mod:
        try:
            mod = None
            while mod is None:
                completer.complete_mtypes()
                mtype = input("[*] Module type: ")
                try:
                    completer.complete_mnames(mtype)
                except AttributeError:
                    ut.log(
                        'error',
                        f"Invalid module type: {mtype}.")
                else:
                    mname = input("[*] Module name: ")
                    try:
                        mod = Module(client, mtype, mname)
                    except MsfRpcError:
                        ut.log(
                            'error',
                            f"Invalid module type: {mtype}.")
                    except TypeError:
                        ut.log(
                            'error',
                            f"Invalid module name: {mname}.")
                    else:
                        ut.initialize(modules, mtype, mname)
            mod_opts = set_options(mod)
            if mtype == 'exploit' and ask('pay'):
                payload = None
                while payload is None:
                    completer.complete_payloads(mod)
                    pname = input("[*] Payload: ")
                    try:
                        payload = Module(client, 'payload', pname)
                    except TypeError:
                        ut.log(
                            'error',
                            f"Invalid payload: {pname}")
                pay_opts = set_options(payload)
                mod_opts['PAYLOAD'] = {'NAME': pname,
                                       'OPTIONS': pay_opts}
            modules[mtype][mname].append(mod_opts)
            if ask('end'):
                more_mod = False
        except EOFError:
            print()
            break
    with open(rc_out, 'w') as f:
        json.dump(modules, f, indent=2)
        ut.log('succ',
               f"Resource script correctly generated in {rc_out}")


def parse_rc(client, rc_out):
    with open(rc_out) as f:
        try:
            rc = json.load(f)
        except json.decoder.JSONDecodeError:
            ut.log('error',
                   "Resources script file cannot be parsed", err=ct.ECFGRC)
    modules = {}
    if rc:
        truncate = ask('trc')
        if truncate:
            return modules
    for mtype in rc:
        for mname in rc[mtype]:
            ut.initialize(modules, mtype, mname)
            tmp_mopts = {}
            for mod in rc[mtype][mname]:
                tmp_mod = Module(client, mtype, mname)
                for opt, val in mod.items():
                    if opt == 'PAYLOAD':
                        tmp_pay = Module(client,
                                         'payload', mod['PAYLOAD']['NAME'])
                        tmp_mopts['PAYLOAD'] = {
                            'NAME': mod['PAYLOAD']['NAME'],
                            'OPTIONS': {}
                        }
                        for popt, pval in mod['PAYLOAD']['OPTIONS'].items():
                            popt_info = tmp_pay.opt_info(popt)
                            pcorr, pcval = ut.correct_type(pval, popt_info)
                            if not pcorr:
                                ut.log('warn',
                                       f"Payload option error: {popt}. "
                                       f"Value error: {pval}. "
                                       f"{pcval}. Skipping...")
                                continue
                            tmp_mopts['PAYLOAD']['OPTIONS'][popt] = pval
                    else:
                        opt_info = tmp_mod.opt_info(opt)
                        try:
                            corr, cval = ut.correct_type(val, opt_info)
                        except KeyError:
                            ut.log('warn',
                                   f"Option error: {opt}. "
                                   f"Value error: {val}. "
                                   f"Skipping...")
                            continue
                        else:
                            if not corr:
                                ut.log('warn',
                                       f"Option error: {opt}. "
                                       f"Value error: {val}. "
                                       f"{cval}. Skipping...")
                                continue
                            tmp_mopts[opt] = val
            if tmp_mopts:
                modules[mtype][mname].append(tmp_mopts)
    return modules


def parse_cvescanner(cvescanner):
    with open(cvescanner) as f:
        try:
            scan = json.load(f)
        except json.decoder.JSONDecodeError:
            ut.log('warn',
                   "CVEScannerV2 report cannot be parsed. Skipping...")
            return
    exploits = set()
    for host, hinfo in scan.items():
        for port, pinfo in hinfo['ports'].items():
            for cve, cinfo in pinfo['vulnerabilities']['cves'].items():
                if 'metasploit' in cinfo:
                    for exploit in cinfo['metasploit']:
                        exp = exploit['name'].split('/')
                        exploits.add((exp[0], '/'.join(exp[1:])))
    return exploits
