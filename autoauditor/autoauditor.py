#!/usr/bin/env python3
import sys
import os
import argparse
import metasploit
import wizard
import vpn
import utils


if __name__ == '__main__':
    utils.check_privileges()

    parser = argparse.ArgumentParser(
        description="Tool to run metasploit automatically given a resource script.")

    parser.add_argument('-v', '--ovpn', metavar='ovpn_file',
                        help="Run a vpn container in order to connect external subnet.")

    parser.add_argument('-o', '--outfile', metavar='log_file',
                        default='output/msf.log',
                        help="If present, log all output to log_file, otherwise log to output/msf.log file.")

    parser.add_argument('-d', '--outdir', metavar='gather_dir',
                        default='output/loot',
                        help="If present, store gathered data in gather_dir, otherwise store in output/loot directory.")

    parser.add_argument('-b', '--background', action='store_true',
                        help="Keep containers running in background.")

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('-r', '--rcfile', metavar='rc_file',
                       help="Run metasploit using rc_file")

    group.add_argument('-g', '--genrc', metavar='rc_out',
                       help="Start wizard helper to generate automated resource script file.")

    group.add_argument('-s', '--stop', action='store_true',
                       help="Stop any orphan container.")

    args = parser.parse_args()

    vpncont = None
    msfcont = None

    if args.ovpn is not None:
        assert os.path.isfile(args.ovpn), "{} does not exist.".format(args.ovpn)
        vpncont = vpn.setup_vpn(args.ovpn, args.stop)

    utils.check_file_dir(args.outfile, args.outdir)

    msfcont = metasploit.start_msfrpcd(args.ovpn is not None, args.outdir, args.stop)

    if args.stop:
        utils.shutdown(vpncont, msfcont)

    if args.genrc is not None:
        msfclient = metasploit.get_msf_connection('dummypass')
        wizard.gen_resource_file(msfclient, args.genrc)
    else:
        assert os.path.isfile(args.rcfile), "{} does not exist. Generate with -g.".format(args.rcfile)
        metasploit.launch_metasploit(args.rcfile, args.outfile)

    if not args.background:
        utils.shutdown(vpncont, msfcont)
