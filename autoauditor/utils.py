from distutils.util import strtobool
import sys, pwd, grp, docker, os

NOERR = 0
EBUILD = 241
EBDGNET = 242
ENOPERM = 243
EFLEXST = 244


def log(color, string, end='\n', reset=False, errcode=NOERR):
    level = {
        'normal': '',
        'succg' : '\033[92m[+] \033[0m',
        'succb' : '\033[94m[*] \033[0m',
        'warn'  : '\033[93m[-] \033[0m',
        'error' : '\033[91m[-] \033[0m',
    }
    if reset:
        print(string, end='\r')
        sys.stdout.flush()
        print(level.get(color), end=end)
    else:
        print(level.get(color) + string, end=end)

    if color == 'error' and errcode != NOERR:
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
            sym = WARN+'- '
            if opt in exploit.missing_required:
                sym = FAIL+'* '

        print("\t{}{}: {}".format(sym, opt, exploit[opt] if exploit[opt] is not None else '')+END)

def correct_type(value):
    if value.isdigit():
        return int(value)
    if value.lower() in ('true', 'false'):
        return bool(strtobool(value))
    return value

def shutdown(vpncont, msfcont):
    client = docker.from_env()

    log('succb', "Stopping metasploit container...", end='')
    msfcont.stop()
    log('succg', 'stopped.', reset=True)

    if vpncont is not None:
        log('succb', "Stopping VPN client container...", end='')
        vpncont.stop()
        log('succg', 'stopped.', reset=True)

        log('succb', "Removing attacker_network...", end='')
        try:
            net = client.networks.get('attacker_network')
        except docker.errors.NotFound:
            pass
        else:
            net.remove()
        log('succg', 'removed.', reset=True)

    sys.exit()
