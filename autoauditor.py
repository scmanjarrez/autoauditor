#!/usr/bin/env python3
from pymetasploit3.msfrpc import MsfRpcClient, MsfRpcError
from io import BytesIO as fobj
from distutils.util import strtobool
import subprocess
import json
import readline
import docker
import time
import argparse
import sys
import os
import grp
import pwd

OKG = '\033[92m'
OKB = '\033[94m'
WARN = '\033[93m'
FAIL = '\033[91m'
END = '\033[0m'
P = OKG+'[+] '+END
S = '[*] '
M = '[-] '

def check_privileges():
    user = pwd.getpwuid(os.geteuid()).pw_name
    groups = [group.gr_name for group in grp.getgrall() if user in group.gr_mem]

    if 'docker' not in groups:
        print(FAIL+M+"User '{}' must belong to 'docker' group to communicate with docker API, or execute as root.".format(user)+END)
        sys.exit(1)

def correct_type(value):
    if value.isdigit():
        return int(value)
    if value.lower() in ('true', 'false'):
        return bool(strtobool(value))
    return value

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

def gen_resource_file(client, rc_out):
    more_mod = True
    rc_file = {}
    while more_mod:
        try:
            mod = None
            while mod is None:
                mtype = input(P+"Module type to use [exploit/auxiliary/payload/encoder/post/nop]: ")
                mname = input(P+"Module to use: ")
                try:
                    mod = client.modules.use(mtype, mname)
                except MsfRpcError:
                    print(FAIL+M+"Invalid module type: {}. Check rc file.".format(mtype)+END)
                except TypeError:
                    print(FAIL+M+"Invalid module: {}. Check rc file.".format(mname)+END)
                else:
                    if mtype not in rc_file:
                        rc_file[mtype] = {}
                    if mname not in rc_file[mtype]:
                        rc_file[mtype][mname] = []

            adv = str.lower(input(P+"Show advanced options?[y/n] ")) == 'y'

            print(P+"Current options (required in yellow, missing in red)")
            print_options(mod, adv)
            eof = False
            correct = str.lower(input(P+"Correct?[y/n] ")) == 'y'
            opt_l = []
            while not correct:
                try:
                    print(OKB+S+"Send EOF on finish (Ctrl+D)"+END)
                    while True:
                        opt = input(P+"Option (case sensitive): ")
                        val = correct_type(input(P+"Value for {}: ".format(opt)))
                        try:
                            mod[opt] = val
                        except KeyError:
                            print(FAIL+M+"Invalid option: {}".format(opt)+END)
                        else:
                            opt_l.append((opt, val))
                        eof = False
                except EOFError:
                    print()
                    # avoid infinite loop if consecutives Ctrl+D
                    if eof:
                        break
                    print(P+"Final options")
                    print_options(mod, adv)
                    eof = True

                correct = str.lower(input(P+"Correct?[y/n] ")) == 'y'
                eof = False

            rc_file[mtype][mname].append(opt_l)

            if str.lower(input(P+"Add more modules?[y/n] ")) == 'n':
                more_mod = False
        except EOFError:
            print()
            break

    with open(rc_out, 'w') as f:
        json.dump(rc_file, f, indent=2)
        print(P+"Resource script file generated at {}".format(rc_out))

def setup_vpn(ovpn_file):
    client = docker.from_env()

    print(OKB+S+"Verifying if VPN client image exists..."+END)

    try:
        image = client.images.get('dperson/openvpn-client')
        print(P+"VPN client image exists, skipping...")
    except docker.errors.ImageNotFound:
        print(P+"VPN client image does not exist, pulling from docker hub...")
        image = client.images.pull('dperson/openvpn-client', 'latest')

    print(OKB+S+"Checking if VPN client container is already running..."+END)

    vpn_l = client.containers.list(filters={'name':'vpncl'})
    if not vpn_l:
        print(P+"VPN client container is not running, starting...")
        of = os.path.abspath(ovpn_file)

        ipam_pool = docker.types.IPAMPool(subnet='10.10.20.0/24')
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        try:
            net = client.networks.get('attacker_network')
        except docker.errors.NotFound:
            net = client.networks.create('attacker_network', driver='bridge', ipam=ipam_config)

        vpncont = client.containers.run(image, 'sh -c "sleep 5 && /sbin/tini -- /usr/bin/openvpn.sh"',
                                        auto_remove=True,
                                        stdin_open=True, tty=True,
                                        detach=True, cap_add='NET_ADMIN',
                                        security_opt=['label:disable'],
                                        tmpfs={'/run': '', '/tmp':''},
                                        name='vpncl',
                                        network='attacker_network',
                                        volumes={'/dev/net': {'bind': '/dev/net', 'mode': 'z'},
                                                 of: {'bind': '/vpn/vpn.ovpn'}},
                                        environment={'ROUTE': '10.10.20.0/24'})
        try:
            net = client.networks.get('bridge')
        except docker.errors.NotFound:
            print(FAIL+M+"Could not find docker 'bridge' network"+END)
            sys.exit(1)
        else:
            net.connect('vpncl')
    else:
        print(P+"VPN client container is running, skipping...")
        vpncont = vpn_l[0]

    return vpncont

def start_msfrpcd(ovpn, loot_dir):
    client = docker.from_env()

    print(OKB+S+"Verifying if docker images exist..."+END)

    try:
        image = client.images.get('msfrpci')
        print(P+"Metasploit image exists, skipping...")
    except docker.errors.ImageNotFound:
        print(P+"Metasploit image does not exist, pulling from docker hub...")
        dckf = fobj(b'FROM phocean/msf\n'
                    b'RUN apt update && apt install -y iproute2 iputils-ping traceroute\n'
                    b'CMD ./msfrpcd -P dummypass && tail -f /dev/null')
        try:
            image, _ = client.images.build(fileobj=dckf, tag='msfrpci')
        except docker.errors.BuildError:
            print(FAIL+M+"Building error"+END)
            sys.exit(1)

    print(OKB+S+"Checking if metasploit container is already running..."+END)

    cont_l = client.containers.list(filters={'name':'msfrpc'})
    if not cont_l:
        print(P+"Metasploit container is not running, starting...")

        loot = os.path.join(os.getcwd(), loot_dir)
        if ovpn:
            msfcont = client.containers.run(image,
                                            'sh -c "ip route replace default via 10.10.20.2 && ./msfrpcd -P dummypass && tail -f /dev/null"',
                                            auto_remove=True, detach=True, name='msfrpc',
                                            cap_add='NET_ADMIN', network='attacker_network',
                                            volumes={loot: {'bind': '/root/.msf4/loot'}},
                                            ports={55553:55553})
        else:
            msfcont = client.containers.run(image, auto_remove=True,
                                            detach=True, name='msfrpc',
                                            volumes={loot: {'bind': '/root/.msf4/loot'}},
                                            ports={55553:55553})
        time.sleep(10)
    else:
        print(P+"Metasploit container is running, skipping...")
        msfcont = cont_l[0]

    return MsfRpcClient('dummypass', ssl=True), msfcont

def shutdown(vpncont, msfcont):
    client = docker.from_env()

    print(OKB+S+"Stopping metasploit container..."+END)
    msfcont.stop()

    if vpncont is not None:
        print(OKB+S+"Stopping VPN client container..."+END)
        vpncont.stop()

        print(OKB+S+"Removing attacker_network..."+END)
        try:
            net = client.networks.get('attacker_network')
        except docker.errors.NotFound:
            pass
        else:
            net.remove()

def launch_metasploit(client, rc_file, log_file):
    with open(rc_file, 'r') as f:
        rc = json.load(f)

    with open(log_file, 'w') as f:
        print(OKB+S+"Logging metasploit output to {}...".format(log_file)+END)
        for mtype in rc:
            for mname in rc[mtype]:
                try:
                    mod = client.modules.use(mtype, mname)
                except MsfRpcError:
                    print(FAIL+M+"Invalid module type: {}. Check {}.".format(mtype, rc_file)+END)
                    continue
                except TypeError:
                    print(FAIL+M+"Invalid module: {}. Check {}.".format(mname, rc_file)+END)
                    continue

                for expl in rc[mtype][mname]:
                    for opt in expl:
                        try:
                            if opt[0] == "ACTION":
                                mod.action = opt[1]
                            else:
                                mod[opt[0]] = opt[1]
                        except KeyError:
                            print(FAIL+M+"Invalid option: {}. Check {}.".format(opt[0], rc_file)+END)
                    cid = client.consoles.console().cid
                    exp = "{}/{}".format(mtype, mname)
                    print(P+"Logging output: {}".format(exp))
                    f.write('##### {} #####\n\n'.format(exp))
                    f.write(client.consoles.console(cid).run_module_with_output(mod))
                    f.write('\n######{}######\n\n'.format("#"*len(exp)))
                    client.consoles.destroy(cid)

if __name__ == '__main__':
    check_privileges()

    parser = argparse.ArgumentParser(
            description="Tool to run metasploit automatically given a resource script.")

    parser.add_argument('-v', '--ovpn', metavar='ovpn_file',
                        help="Run a vpn container in order to connect external subnet.")

    parser.add_argument('-o', '--outfile', metavar='log_file',
                        default='msf.log',
                        help="If present, log all output to log_file, otherwise log to msf.log file.")

    parser.add_argument('-d', '--outdir', metavar='gather_dir',
                        default='loot',
                        help="If present, store gathered data in gather_dir, otherwise store in loot directory.")

    parser.add_argument('-b', '--background', action='store_true',
                        help="Keep containers running in background.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-s', '--stop', action='store_true',
                       help="Stop any orphan container.")

    group.add_argument('-g', '--genrc', metavar='rc_out',
                       help="Start wizard helper to generate automated resource script file.")

    group.add_argument('-r', '--rcfile', metavar='rc_file',
                       default='rc.json',
                       help="Run metasploit using rc_file")

    args = parser.parse_args()
    vpncont = None
    msfcont = None

    if args.ovpn is not None:
        assert os.path.isfile(args.ovpn), "{} does not exist.".format(args.ovpn)
        vpncont = setup_vpn(args.ovpn)

    msfclient, msfcont = start_msfrpcd(args.ovpn is not None, args.outdir)

    if args.stop:
        shutdown(vpncont, msfcont)
        sys.exit()

    if args.genrc is not None:
        gen_resource_file(msfclient, args.genrc)
    else:
        assert os.path.isfile(args.rcfile), "{} does not exist, generate it using -g.".format(args.rcfile)
        launch_metasploit(msfclient, args.rcfile, args.outfile)

    if not args.background:
        shutdown(vpncont, msfcont)
