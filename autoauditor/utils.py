# SPDX-License-Identifier: GPL-3.0-or-later

# utils - Utilities module.

# Copyright (C) 2022 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
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
# along with GNU Emacs.  If not, see <https://www.gnu.org/licenses/>.

from autoauditor import constants as ct
from distutils.util import strtobool
from pathlib import Path

import ipaddress
import docker
import grp
import pwd
import sys
import os

COLORS = {
    'R': '\033[91m',
    'Y': '\033[93m',
    'B': '\033[94m',
    'G': '\033[92m',
    'N': '\033[0m',
    'E': ''
}

LOG = {
    'normal': '',
    'succ': '[+] ', 'info': '[*] ',
    'warn': '[-] ', 'error': '[!] '
}

WINDOW = None


def disable_ansi_colors():
    COLORS['R'] = COLORS['E']
    COLORS['Y'] = COLORS['E']
    COLORS['B'] = COLORS['E']
    COLORS['G'] = COLORS['E']
    COLORS['N'] = COLORS['E']


def set_logger(window):
    global WINDOW
    if WINDOW is None:
        WINDOW = window
        disable_ansi_colors()


def log(ltype, msg, end='\n', err=None):
    color = LOG[ltype]
    if ltype == 'succ':
        color = f'{COLORS["G"]}{color}{COLORS["N"]}'
    elif ltype == 'info':
        color = f'{COLORS["B"]}{color}{COLORS["N"]}'
    elif ltype == 'warn':
        color = f'{COLORS["Y"]}{color}{COLORS["N"]}'
    elif ltype == 'error':
        color = f'{COLORS["R"]}{color}{COLORS["N"]}'
    if WINDOW is not None:
        WINDOW.emit(f"{color}{msg}")
    else:
        print(f"{color}{msg}", end=end, flush=True)

    if WINDOW is None and err is not None:
        sys.exit(err)


def copyright_notice():
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


def correct_type(value, info):
    correct = True
    res = value
    if 0 in info:  # action
        if value not in info.values():
            correct = False
            res = f"Invalid: {value}. " f"Expected: {', '.join(info.values())}"
    else:
        value_type = info['type']
        value_required = info['required']
        error_msg = f"Invalid: {value}. Expected: {value_type}"
        if not value:
            if value_required:  # empty and req -> error
                correct = False
                res = f"Missing. Expected {value_type}"
        else:
            if value_type == 'bool':  # if not empty, check type
                try:
                    res = bool(strtobool(value))
                except ValueError:
                    correct = False
                    res = error_msg
            elif value_type in ('integer', 'port'):
                inv = True
                if (isinstance(value, str) and value.isdigit()
                    or isinstance(value, int)):  # noqa
                    dig = int(value)
                    if value_type == 'integer' or 0 < dig < 2 ** 16:
                        res = dig
                        inv = False
                if inv:
                    correct = False
                    res = error_msg
            elif value_type in ('address', 'addressrange'):
                try:
                    ipaddress.ip_network(value, strict=False)
                except ValueError:
                    correct = False
                    res = error_msg
            elif value_type == 'enum' and value not in info['enums']:
                correct = False
                res = f"Invalid. Expected: {', '.join(info['enums'])}"
    return correct, res


def running_containers():
    client = docker.from_env()
    label = list(ct.LABEL.items())[0]
    cnts = client.containers.list(
        filters={'label': f'{label[0]}={label[1]}'})
    return [cnt.name for cnt in cnts]


def shutdown():
    client = docker.from_env()
    label = list(ct.LABEL.items())[0]
    cnts = client.containers.list(
        filters={'label': f'{label[0]}={label[1]}'})
    good = True

    log('info', ct.CNTSTOP, end='\r')
    for cnt in cnts:
        try:
            cnt.stop()
        except docker.errors.APIError:
            good = False
    if not good:
        log('error', ct.CNTSTOPERR, err=ct.EDAPI)
    else:
        log('succ', ct.CNTSTOPPED)

    try:
        net = client.networks.get(ct.NET_NAME)
    except docker.errors.NotFound:
        pass
    else:
        log('info', ct.ATNET, end='\r')
        try:
            net.remove()
        except docker.errors.APIError:
            log('error', ct.ATNETAEND, err=ct.EDAPI)
        else:
            log('succ', ct.ATNETRM)

    log('succ', 'Exiting autoauditor.')
    return 0 if good else ct.EDAPI


def check_existf(file):
    return Path(file).exists()


def check_readf(file):
    if file:
        try:
            Path(file).read_text()
        except PermissionError as ex:
            log('error', f"{ex.strerror}: {ex.filename}.", err=ex.errno)
            return ex.errno
        except FileNotFoundError as ex:
            log('error', f"{ex.strerror}: {ex.filename}.", err=ex.errno)
            return ex.errno
    else:
        return "File name missing"


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
