#!/usr/bin/env python3
from requests.exceptions import ConnectionError
from pymetasploit3.msfrpc import MsfRpcClient, MsfRpcError, MsfAuthError
import utils, json, argparse

def gen_resource_file(client, rc_out):
    more_mod = True
    rc_file = {}
    while more_mod:
        try:
            mod = None
            while mod is None:
                mtype = input("Module type to use [exploit/auxiliary/payload/encoder/post/nop]: ")
                mname = input("Module to use: ")
                try:
                    mod = client.modules.use(mtype, mname)
                except MsfRpcError:
                    utils.log('error', "Invalid module type: {}. Check rc file.".format(mtype))
                except TypeError:
                    utils.log('error', "Invalid module: {}. Check rc file.".format(mname))
                else:
                    if mtype not in rc_file:
                        rc_file[mtype] = {}
                    if mname not in rc_file[mtype]:
                        rc_file[mtype][mname] = []

            adv = str.lower(input(P+"Advanced options?[y/n] ")) == 'y'

            utils.log('succg', "Current options (required in yellow, missing in red):")
            print_options(mod, adv)
            eof = False
            correct = str.lower(input("Correct?[y/n] ")) == 'y'
            opt_l = []
            while not correct:
                try:
                    utils.log('succb', "Send EOF on finish (Ctrl+D)")
                    while True:
                        opt = input("Option (case sensitive): ")
                        val = correct_type(input("Value for {}: ".format(opt)))
                        try:
                            mod[opt] = val
                        except KeyError:
                            utils.log('error', "Invalid option: {}".format(opt))
                        else:
                            opt_l.append((opt, val))
                        eof = False
                except EOFError:
                    print()
                    # avoid infinite loop if consecutives Ctrl+D
                    if eof:
                        break
                    print("Final options")
                    print_options(mod, adv)
                    eof = True

                correct = str.lower(input("Correct?[y/n] ")) == 'y'
                eof = False

            rc_file[mtype][mname].append(opt_l)

            if str.lower(input("Add more modules?[y/n] ")) == 'n':
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
    try:
        msfclient = MsfRpcClient(args.pwd if args.pwd is not None else 'dummypass', ssl=True)
        gen_resource_file(msfclient, args.outrc if args.outrc is not None else 'rc.json')
    except ConnectionError:
        utils.log('error', "Metasploit container connection error. Check container is running.")
    except MsfAuthError:
        utils.log('error', "Metasploit container authentication error. Check password.")
