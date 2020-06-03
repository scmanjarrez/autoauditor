from distutils.util import strtobool
import sys
import pwd
import grp
import docker
import os


NOERROR = 0
EBUILD = 241
ENOBRDGNET = 242
EACCESS = 243
EMSCONN = 244
EMSPASS = 245
ENOPERM = 246
EMODNR = 247
EBADREPFMT = 248

MSSTAT = "Metasploit image status:"
MSEXIST = "Metasploit image status: exists."
MSDOWN = "Metasploit image status: does not exist, downloading ..."
MSDONE = "Metasploit image status: does not exist, downloading ... done"

MSCSTAT = "Metasploit container status:"
MSCR = "Metasploit container status: running."
MSCNR = "Metasploit container status: not running."
MSCSTART = "Metasploit container status: not running, starting ..."
MSCDONE = "Metasploit container status: not running, starting ... done"

MSSTOP = "Stopping metasploit container ..."
MSSTOPPED = "Stopping metasploit container ... done"
MSNR = "Stopping metasploit container ... not running"

VPNSTAT = "VPN client image status:"
VPNEXIST = "VPN client image status: exists."
VPNDOWN = "VPN client image status: does not exist, downloading ..."
VPNDONE = "VPN client image status: does not exist, downloading ... done"

VPNCSTAT = "VPN client container status:"
VPNCR = "VPN client container status: running."
VPNCNR = "VPN client container status: not running."
VPNCSTART = "VPN client container status: not running, starting ..."
VPNCDONE = "VPN client container status: not running, starting ... done"

VPNSTOP = "Stopping VPN client container ..."
VPNSTOPPED = "Stopping VPN client container ... done"
VPNNR = "Stopping VPN client container ... not running"

ATNET = "Removing attacker_network ..."
ATNETRM = "Removing attacker_network ... done"
ATNETNF = "Removing attacker_network ... not found"

def log(color, string, end='\n', errcode=None):
    level = {
        'normal': '',
        'succg' : '\033[92m[+] \033[0m',
        'succb' : '\033[94m[*] \033[0m',
        'warn'  : '\033[93m[-] \033[0m',
        'error' : '\033[91m[!] \033[0m',
    }

    print(level.get(color) + string, end=end, flush=True)

    if errcode is not None:
        sys.exit(errcode)

def check_privileges():
    user = pwd.getpwuid(os.geteuid()).pw_name
    groups = [group.gr_name for group in grp.getgrall() if user in group.gr_mem]

    if 'docker' not in groups:
        log('error', "User '{}' must belong to 'docker' group to communicate with docker API.".format(user), errcode=ENOPERM)

def print_options(exploit, adv=False):
    opt_l = exploit.options
    if not adv:
        opt_l = [opt for opt in opt_l if opt not in exploit.advanced]

    for opt in opt_l:
        sym = ''
        if opt in exploit.required:
            sym = '\033[93m- \033[0m'
            if opt in exploit.missing_required:
                sym = '\033[91m* \033[0m'

        print("\t{}{}: {}".format(sym, opt, exploit[opt] if exploit[opt] is not None else ''))

def correct_type(value):
    if value.isdigit():
        return int(value)
    if value.lower() in ('true', 'false'):
        return bool(strtobool(value))
    return value

def shutdown(vpncont, msfcont):
    client = docker.from_env()

    log('succb', MSSTOP, end='\r')
    if msfcont is not None:
        msfcont.stop()
        log('succg', MSSTOPPED)
    else:
        log('succg', MSNR)

    log('succb', VPNSTOP, end='\r')
    if vpncont is not None:
        vpncont.stop()
        log('succg', VPNSTOPPED)
    else:
        log('succg', VPNNR)

    log('succb', ATNET, end='\r')
    try:
        net = client.networks.get('attacker_network')
    except docker.errors.NotFound:
        log('succg', ATNETNF)
    else:
        net.remove()
        log('succg', ATNETRM)

    log('succg', 'Ending autoauditor.', errcode=NOERROR)

def check_file_dir(outf, outd=None):
    try:
        os.makedirs(os.path.dirname(outf), exist_ok=True)
    except PermissionError:
        log('error', "Insufficient permission to create file path {}.".format(outf), errcode=EACCESS)

    if outd is not None:
        try:
            os.makedirs(outd, exist_ok=True)
        except PermissionError:
            log('error', "Insufficient permission to create directory {}.".format(outd), errcode=EACCESS)

if __name__ == '__main__':
    log('error', "Helper module. Not runnable.", errcode=EMODNR)
