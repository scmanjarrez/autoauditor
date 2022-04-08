#!/usr/bin/env python3

from pygroupsig import (constants, groupsig, grpkey,
                        memkey, message)
import argparse
import requests
import urllib3
import errno
import json
import sys
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


CODE = constants.PS16_CODE
groupsig.init(CODE)

CRED_DIR = 'credentials'
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
    print(f"{color}{msg}", end=end, flush=True)
    if err is not None:
        sys.exit(err)


def http_req(method, session, url, msg=None):
    try:
        if method == 'get':
            resp = session.get(url)
        elif method == 'post':
            resp = session.post(url, json=msg)
        # print(method, resp, resp.text)
    except requests.exceptions.InvalidURL as e:
        log('error',
            f"Invalid '{url}': {e.__context__}",
            err=errno.EDESTADDRREQ)
    except requests.exceptions.ConnectionError as e:
        log('error',
            f"Can not connect to '{url}': {e.__context__}",
            err=errno.ECONNREFUSED)
    return resp


class FabricMember:
    def __init__(self, provider, grp_dir, cert):
        self.url = f'https://{provider[0]}:{provider[1]}'
        self.session = requests.Session()
        self.session.verify = False
        self.session.cert = cert
        self.msg1 = None
        self.token = None
        self.usk = None
        self.grp_dir = grp_dir
        if self.grp_dir is not None:
            self.load()

    def load(self):
        with open(f'{self.grp_dir}/memkey') as f:
            self.usk = memkey.memkey_import(CODE, f.read())

    def save_credentials(self):
        if self.usk is not None:
            try:
                os.makedirs(CRED_DIR, exist_ok=True)
            except PermissionError:
                log('error',
                    f"Can not create {CRED_DIR}",
                    err=errno.EACCES)
            with open(f'{CRED_DIR}/memkey', 'w') as f:
                f.write(memkey.memkey_export(self.usk))

    def retrieve_grpkey(self):
        resp = http_req('get', self.session, f'{self.url}/grpkey')
        if resp.status_code == 200:
            try:
                data = json.loads(resp.text)
            except json.JSONDecodeError:
                log('error',
                    "Error decoding groupkey message.", err=1)
            else:
                self.grpkey = grpkey.grpkey_import(CODE, data['msg'])
        else:
            log('error',
                "Error on GET: grpkey (provider).", err=1)

    def join1(self):
        if self.usk is None:
            resp = http_req('get', self.session, f'{self.url}/join')
            if resp.status_code == 200:
                data = json.loads(resp.text)
                self.token = data['token']
                if not data['msg'].startswith('Error'):
                    self.msg1 = data['msg']
                else:
                    log('error', data['msg'], err=1)
            else:
                log('error', "Error on join1", err=1)

    def join2(self):
        if self.usk is None:
            if self.msg1 is not None and self.token is not None:
                msgin = message.message_from_base64(self.msg1)
                msg2 = groupsig.join_mem(1,
                                         self.grpkey,
                                         msgin=msgin)
                post = {
                    'msg': message.message_to_base64(msg2['msgout'])
                }
                resp = http_req('post', self.session,
                                f'{self.url}/join/{self.token}',
                                post)
                if resp.status_code == 200:
                    data = json.loads(resp.text)
                    if not data['msg'].startswith('Error'):
                        msgin2 = message.message_from_base64(data['msg'])
                        msg4 = groupsig.join_mem(3,
                                                 self.grpkey,
                                                 msgin=msgin2,
                                                 memkey=msg2['memkey'])
                        self.usk = msg4['memkey']
                    else:
                        log('error', data['msg'], err=1)
                else:
                    log('error', "Error on join2", err=1)
            else:
                log('error', "Run join1 before running join2", err=1)


def main():
    parser = argparse.ArgumentParser(
        description="autoauditor group signature demo1: retrieve credentials")
    parser.add_argument('-d',
                        metavar='dir',
                        help="Group credentials path.")
    parser.add_argument('-u',
                        metavar='usr_dir',
                        default='fabric_credentials',
                        help="Fabric credentials path.")
    parser.add_argument('--usr-crt',
                        metavar='usr_crt',
                        default='user.crt',
                        help="User certificate for TLS authentication.")
    parser.add_argument('--usr-key',
                        metavar='usr_key',
                        default='user.key',
                        help="User key for TLS authentication.")
    parser.add_argument('-a',
                        metavar='address',
                        default='127.0.0.1',
                        help="Group signature (provider) server address.")
    parser.add_argument('-p',
                        metavar='port', type=int,
                        default=5000,
                        help="Group signature (provider) server port.")
    args = parser.parse_args()
    member = FabricMember((args.a, args.p),
                          args.d, (f'{args.u}/{args.usr_crt}',
                                   f'{args.u}/{args.usr_key}'))
    member.retrieve_grpkey()
    member.join1()
    member.join2()
    member.save_credentials()


if __name__ == '__main__':
    main()
    groupsig.clear(constants.GL19_CODE)
