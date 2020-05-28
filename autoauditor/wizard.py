#!/usr/bin/env python3
from pymetasploit3.msfrpc import MsfRpcError
import utils
import json
import argparse
import metasploit
import readline


def gen_resource_file(client, rc_out):
    more_mod = True
    rc_file = {}
    yes_ans = ['y', 'yes']

    while more_mod:
        try:
            mod = None
            while mod is None:
                mtype = input("[*] Module type (exploit|auxiliary|payload|encoder|post|nop): ")
                mname = input("[*] Module: ")
                try:
                    mod = client.modules.use(mtype, mname)
                except MsfRpcError:
                    utils.log('error', "Invalid module type: {}.".format(mtype))
                except TypeError:
                    utils.log('error', "Invalid module: {}.".format(mname))
                else:
                    if mtype not in rc_file:
                        rc_file[mtype] = {}
                    if mname not in rc_file[mtype]:
                        rc_file[mtype][mname] = []

            adv = str.lower(input("[*] Advanced options [y/N]: ")) in yes_ans

            utils.log('succg', "Current options: required=yellow mark, missing=red mark")
            utils.print_options(mod, adv)

            eof = False
            modify = str.lower(input("[*] Modify [y/N]: ")) in yes_ans
            opt_l = []
            while modify:
                try:
                    utils.log('succb', "Finish with EOF (Ctrl+D)")
                    while True:
                        opt = input("[*] Option (case sensitive): ")
                        val = utils.correct_type(input("[*] {} value: ".format(opt)))
                        try:
                            mod[opt] = val
                        except KeyError:
                            utils.log('error', "Invalid option: {}".format(opt))
                        else:
                            opt_l.append((opt, val))
                        eof = False
                except EOFError:
                    print()
                    if eof:  # avoid infinite loop if consecutives Ctrl+D
                        break
                    utils.log('succb', "Final options:")
                    utils.print_options(mod, adv)
                    eof = True

                modify = str.lower(input("[*] Modify [y/N]: ")) in yes_ans
                eof = False

            rc_file[mtype][mname].append(opt_l)

            if str.lower(input("[*] More modules [y/N]: ")) not in yes_ans:
                more_mod = False
        except EOFError:
            print()
            break

    with open(rc_out, 'w') as f:
        json.dump(rc_file, f, indent=2)
        utils.log('succg', "Resource script file generated at {}".format(rc_out))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tool to run metasploit automatically given a resource script.")

    parser.add_argument('-o', '--outrc', metavar='out_rcfile',
                        help="Run wizard and generate out_rcfile.")

    parser.add_argument('-p', '--pwd', metavar='mscontpass',
                        help="Use mscontpass as msfrpc password.")

    args = parser.parse_args()

    msfclient = metasploit.get_msf_connection(args.pwd if args.pwd is not None else 'dummypass')

    outf = args.outrc if args.outrc is not None else 'rc.json'
    utils.check_file_dir(outf)

    gen_resource_file(msfclient, outf)
