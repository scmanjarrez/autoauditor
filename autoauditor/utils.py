# utils - Utilities module.

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

from distutils.util import strtobool
import ipaddress
import constants as cst
import sys
import pwd
import grp
import docker
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


def log(color, string, end='\n', errcode=None):
    level = {
        'normal': '',
        'succg': f'{_GREEN}[+] {_CLEANC}',
        'succb': f'{_BLUE}[*] {_CLEANC}',
        'warn': f'{_YELLOW}[-] {_CLEANC}',
        'error': f'{_RED}[!] {_CLEANC}'
    }
    if WINDOW:
        WINDOW.write_event_value('LOG', level.get(color) + string)
    else:
        print(level.get(color) + string, end=end, flush=True)

    if errcode is not None and errcode != cst.NOERROR:
        if not WINDOW:
            sys.exit(errcode)


def copyright():
    log('normal', cst.COPYRIGHT)


def check_privileges():
    user = pwd.getpwuid(os.geteuid()).pw_name
    groups = [group.gr_name for group in grp.getgrall()
              if user in group.gr_mem]

    if 'docker' not in groups:
        log('error',
            (f"User '{user}' must belong to 'docker' group "
             f"to communicate with docker API."),
            errcode=cst.ENOPERM)


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


def shutdown(msfcont, vpncont=None):
    client = docker.from_env()
    log('succb',
        cst.MSSTOP,
        end='\r')
    if msfcont is not None:
        try:
            msfcont.stop()
        except docker.errors.APIError:
            log(
                'error',
                cst.MSSTOPERR,
                errcode=cst.EDOCKER)
        else:
            log(
                'succg',
                cst.MSSTOPPED)
    else:
        log(
            'succg',
            cst.MSNR)

    log(
        'succb',
        cst.VPNSTOP,
        end='\r')
    if vpncont is not None:
        try:
            vpncont.stop()
        except docker.errors.APIError:
            log(
                'error',
                cst.VPNSTOPERR,
                errcode=cst.EDOCKER)
        else:
            log(
                'succg',
                cst.VPNSTOPPED)
    else:
        log(
            'succg',
            cst.VPNNR)

    log(
        'succb',
        cst.ATNET,
        end='\r')
    try:
        net = client.networks.get('attacker_network')
    except docker.errors.NotFound:
        log(
            'succg',
            cst.ATNETNF)
    else:
        try:
            net.remove()
        except docker.errors.APIError:
            log(
                'error',
                cst.ATNETAEND,
                errcode=cst.EDOCKER)
        else:
            log(
                'succg',
                cst.ATNETRM)

    log('succg', 'Exiting autoauditor.', errcode=cst.NOERROR)
    return cst.NOERROR


def check_file_dir(outf, outd=None):
    dirname = os.path.dirname(outf)
    if dirname:
        try:
            os.makedirs(dirname, exist_ok=True)
        except PermissionError:
            log(
                'error',
                f"Insufficient permission to create file path {outf}.",
                errcode=cst.EACCESS)
            return cst.EACCESS

    if outd is not None:
        try:
            os.makedirs(outd, exist_ok=True)
        except PermissionError:
            log(
                'error',
                f"Insufficient permission to create directory {outd}.",
                errcode=cst.EACCESS)
            return cst.EACCESS


if __name__ == '__main__':
    log(
        'error',
        "Not standalone module. Run again from autoauditor.py.",
        errcode=cst.EMODNR)
