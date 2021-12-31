# SPDX-License-Identifier: GPL-3.0-or-later

# utils - Utilities module.

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

from autoauditor import constants as ct
from distutils.util import strtobool
from pathlib import Path

import ipaddress
import docker
import grp
import pwd
import os


_RED = '\033[91m'
_YELLOW = '\033[93m'
_BLUE = '\033[94m'
_GREEN = '\033[92m'
_CLEANC = '\033[0m'
_NC = ''

WINDOW = None


def disable_ansi_colors():
    global _GREEN, _BLUE, _YELLOW, _RED, _CLEANC
    _GREEN = _BLUE = _YELLOW = _RED = _CLEANC = _NC


def set_logger(window):
    global WINDOW
    if WINDOW is None:
        WINDOW = window
        disable_ansi_colors()


def log(color, string, end='\n', err=None):
    level = {
        'normal': '',
        'succg': f'{_GREEN}[+] {_CLEANC}',
        'succb': f'{_BLUE}[*] {_CLEANC}',
        'warn': f'{_YELLOW}[-] {_CLEANC}',
        'error': f'{_RED}[!] {_CLEANC}'
    }
    if WINDOW:
        WINDOW.write_event_value('LOG', f"{level[color]}{string}")
    else:
        print(f"{level[color]}{string}", end=end, flush=True)

    if not WINDOW and err is not None:
        exit(err)


def copyright():
    log('normal', ct.COPYRIGHT)


def check_privileges():
    user = pwd.getpwuid(os.geteuid()).pw_name
    groups = [group.gr_name for group in grp.getgrall()
              if user in group.gr_mem]

    if 'docker' not in groups:
        log('error',
            f"User '{user}' must belong to 'docker' group "
            f"to communicate with docker API.",
            err=ct.EDPERM)


def print_options(module, adv=False):
    opt_l = module.options
    if not adv:
        opt_l = [opt for opt in opt_l if opt not in module.advanced]

    for opt in opt_l:
        sym = ''
        if opt in module.required:
            sym = f'{_YELLOW}- {_CLEANC}'
            if opt in module.missing_required:
                sym = f'{_RED}* {_CLEANC}'

        print(
            f"\t{sym}{opt}: {module[opt] if module[opt] is not None else ''}")


def correct_type(value, info):
    try:
        value_type = info['type']
        value_required = info['required']
    except KeyError:
        if value in info.values():
            return value
        return f'Invalid. Expected {info}'
    else:
        if not value and not value_required:  # empty and not req -> ok
            return value

        if not value and value_required:  # empty and req -> error
            return f'Missing. Expected {value_type}'

        if value_type == 'bool':  # if not empty, check type
            try:
                return bool(strtobool(value))
            except ValueError:
                pass
        elif value_type in ('integer', 'port'):
            if value.isdigit():
                dig = int(value)
                if value_type == 'integer' or 0 < dig < 2 ** 16:
                    return dig
        elif value_type in ('address', 'addressrange'):
            try:
                ipaddress.ip_network(value, strict=False)
                return value
            except ValueError:
                pass
        elif value_type == 'enum':
            if value in info['enums']:
                return value
        elif value_type in ('string', 'path'):
            return value

        return f'Invalid. Expected {value_type}'


def shutdown():
    client = docker.from_env()
    label = list(ct.LABEL.items())[0]
    cnts = client.containers.list(
        filters={'label': f'{label[0]}={label[1]}'})
    good = True

    log('succb', ct.CNTSTOP, end='\r')
    for cnt in cnts:
        try:
            cnt.stop()
        except docker.errors.APIError:
            good = False
    if not good:
        log('error', ct.CNTSTOPERR, err=ct.EDAPI)
    else:
        log('succg', ct.CNTSTOPPED)

    try:
        net = client.networks.get(ct.NET_NAME)
    except docker.errors.NotFound:
        pass
    else:
        log('succb', ct.ATNET, end='\r')
        try:
            net.remove()
        except docker.errors.APIError:
            log('error', ct.ATNETAEND, err=ct.EDAPI)
        else:
            log('succg', ct.ATNETRM)

    log('succg', 'Exiting autoauditor.')
    return 0 if good else ct.EDAPI


def check_readf(file):
    try:
        Path(file).read_text()
    except PermissionError as ex:
        log('error', f"{ex.strerror}: {ex.filename}.", err=ex.errno)
        return ex.errno
    except FileNotFoundError as ex:
        log('error', f"{ex.strerror}: {ex.filename}.", err=ex.errno)
        return ex.errno


def check_writef(file):
    path = Path(file)
    parent = path.parent
    if parent:
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except PermissionError as ex:
            log('error', f"{ex.strerror}: {ex.filename}.", err=ex.errno)
            return ex.errno
        else:
            try:
                with path.open('a') as p:
                    p.write('')
            except PermissionError as ex:
                log('error', f"{ex.strerror}: {ex.filename}.", err=ex.errno)
                return ex.errno


def check_writed(file):
    try:
        Path(file).mkdir(exist_ok=True)
    except PermissionError as ex:
        log('error', f"{ex.strerror}: {ex.filename}.", err=ex.errno)
        return ex.errno
