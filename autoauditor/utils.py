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
from ipaddress import IPv4Address, AddressValueError
import constants as const
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

CONSOLE = None
WINDOW = None


def disable_ansi_colors():
    global _GREEN, _BLUE, _YELLOW, _RED, _CLEANC
    _GREEN = _BLUE = _YELLOW = _RED = _CLEANC = _NC


def console_log(window, console):
    global CONSOLE, WINDOW
    CONSOLE = console
    WINDOW = window
    disable_ansi_colors()


def log(color, string, end='\n', errcode=None):
    level = {
        'normal': '',
        'succg': '{}[+] {}'.format(_GREEN, _CLEANC),
        'succb': '{}[*] {}'.format(_BLUE, _CLEANC),
        'warn': '{}[-] {}'.format(_YELLOW, _CLEANC),
        'error': '{}[!] {}'.format(_RED, _CLEANC)
    }
    if CONSOLE:
        CONSOLE.print(level.get(color) + string)
        WINDOW.refresh()
    else:
        print(level.get(color) + string, end=end, flush=True)

    if errcode is not None and errcode != const.NOERROR:
        if not CONSOLE:
            sys.exit(errcode)


def copyright():
    log('normal', const.COPYRIGHT)


def check_privileges():
    user = pwd.getpwuid(os.geteuid()).pw_name
    groups = [group.gr_name for group in grp.getgrall()
              if user in group.gr_mem]

    if 'docker' not in groups:
        log('error',
            ("User '{}' must belong to 'docker' group "
             "to communicate with docker API.")
            .format(user),
            errcode=const.ENOPERM)


def print_options(exploit, adv=False):
    opt_l = exploit.options
    if not adv:
        opt_l = [opt for opt in opt_l if opt not in exploit.advanced]

    for opt in opt_l:
        sym = ''
        if opt in exploit.required:
            sym = '{}- {}'.format(_YELLOW, _CLEANC)
            if opt in exploit.missing_required:
                sym = '{}* {}'.format(_RED, _CLEANC)

        print("\t{}{}: {}".format(
            sym, opt, exploit[opt] if exploit[opt] is not None else ''))


def correct_type(value, info):
    try:
        value_type = info['type']
        value_required = info['required']
    except KeyError:
        pass
    else:
        if not value and not value_required:  # empty and not req -> ok
            return value
        if not value and value_required:  # empty and req -> error
            return 'Missing'
        if value_type == 'bool':  # if not empty, check type
            try:
                return bool(strtobool(value))
            except ValueError:
                pass
        elif value_type in ('integer', 'port'):
            if value.isdigit():
                dig = int(value)
                if value_type == 'integer':
                    return dig
                elif 0 < dig < 2 ** 16:
                    return dig
        elif value_type in ('address', 'addressrange'):
            try:
                IPv4Address(value)
                return value
            except AddressValueError:
                pass
        elif value_type == 'enum':
            try:
                if value in info['enums']:
                    return value
            except KeyError:
                pass
        elif value_type == 'string':
            return value

    return 'Invalid'


def shutdown(msfcont, vpncont=None):
    client = docker.from_env()
    log('succb',
        const.MSSTOP,
        end='\r')
    if msfcont is not None:
        try:
            msfcont.stop()
        except docker.errors.APIError:
            log(
                'error',
                const.MSSTOPERR,
                errcode=const.EDOCKER)
        else:
            log(
                'succg',
                const.MSSTOPPED)
    else:
        log(
            'succg',
            const.MSNR)

    log(
        'succb',
        const.VPNSTOP,
        end='\r')
    if vpncont is not None:
        try:
            vpncont.stop()
        except docker.errors.APIError:
            log(
                'error',
                const.VPNSTOPERR,
                errcode=const.EDOCKER)
        else:
            log(
                'succg',
                const.VPNSTOPPED)
    else:
        log(
            'succg',
            const.VPNNR)

    log(
        'succb',
        const.ATNET,
        end='\r')
    try:
        net = client.networks.get('attacker_network')
    except docker.errors.NotFound:
        log(
            'succg',
            const.ATNETNF)
    else:
        try:
            net.remove()
        except docker.errors.APIError:
            log(
                'error',
                const.ATNETAEND,
                errcode=const.EDOCKER)
        else:
            log(
                'succg',
                const.ATNETRM)

    log('succg', 'Exiting autoauditor.', errcode=const.NOERROR)
    return const.NOERROR


def check_file_dir(outf, outd=None):
    dirname = os.path.dirname(outf)
    if dirname:
        try:
            os.makedirs(dirname, exist_ok=True)
        except PermissionError:
            log(
                'error',
                "Insufficient permission to create file path {}."
                .format(outf),
                errcode=const.EACCESS)
            return const.EACCESS

    if outd is not None:
        try:
            os.makedirs(outd, exist_ok=True)
        except PermissionError:
            log(
                'error',
                "Insufficient permission to create directory {}."
                .format(outd),
                errcode=const.EACCESS)
            return const.EACCESS


if __name__ == '__main__':
    log(
        'error',
        "Not standalone module. Run again from autoauditor.py.",
        errcode=const.EMODNR)
