#!/usr/bin/env python3

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf import hkdf
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.fernet import Fernet, InvalidToken
from cryptography import x509
import argparse
import requests
import urllib3
import base64
import errno
import json
import sys
import re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


B64 = re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}=='
                 r'|[A-Za-z0-9+/]{3}=)?$')
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


def gen_ephemeral(ecdhe, skey):
    ecpk = serialization.load_pem_public_key(
        f'-----BEGIN PUBLIC KEY-----\n'
        f'{ecdhe}\n'
        f'-----END PUBLIC KEY-----\n'.encode())
    shared_key = skey.exchange(
        ec.ECDH(), ecpk)
    derived_key = hkdf.HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'ephemeral').derive(shared_key)
    return base64.b64encode(derived_key)


def http_get(session, url):
    try:
        resp = session.get(url)
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
    def __init__(self, bridge, cert):
        self.url = f'https://{bridge[0]}:{bridge[1]}'
        self.session = requests.Session()
        self.session.verify = False
        self.cert = cert
        self.keypair = [None, None]
        self.load()

    def load(self):
        with open(self.cert[0], 'rb') as f:
            self.keypair[0] = x509.load_pem_x509_certificate(f.read())
        with open(self.cert[1], 'rb') as f:
            self.keypair[1] = serialization.load_pem_private_key(
                f.read(), password=None)

    def cert_sid(self):
        return (f'x509::'
                f'{self.keypair[0].subject.rfc4514_string()}::'
                f'{self.keypair[0].issuer.rfc4514_string()}').encode()

    def retrieve_blows(self):
        if self.keypair[0] is not None and self.keypair[1] is not None:
            resp = http_get(self.session, f'{self.url}/blows')
            if resp.status_code == 200:
                try:
                    data = json.loads(resp.text)
                except json.JSONDecodeError:
                    log('error',
                        "Error decoding groupkey message.", err=1)
                else:
                    blows = json.loads(data['msg'])
                    ownblows = 0
                    for blow in blows:
                        if B64.match(blow['blow']):
                            b64 = json.loads(
                                base64.b64decode(blow['blow'].encode()))
                            env = json.loads(
                                base64.b64decode(b64['envelope']))
                            if self.cert_sid() == base64.b64decode(env['sid']):
                                cnt = b64['content'].encode()
                                ecdhe = env['ecdhe']
                                derived_key = gen_ephemeral(
                                    ecdhe, self.keypair[1])
                                fer = Fernet(derived_key)
                                try:
                                    decrypted = json.loads(
                                        fer.decrypt(cnt).decode())
                                except InvalidToken:
                                    log('warn',
                                        ("Content can not be decrypted "
                                         "with derived key."))
                                else:
                                    date = env['date']
                                    nonce = env['nonce']
                                    if date != decrypted['date']:
                                        log('error',
                                            ("Content date does not match "
                                             "envelope date."),
                                            err=1)
                                    elif nonce != decrypted['nonce']:
                                        log('error',
                                            ("Content nonce does not match "
                                             "envelope nonce."),
                                            err=1)
                                    else:
                                        log('succ',
                                            f"Blow: {decrypted['blow']}")
                                        ownblows += 1
                    if ownblows == 0:
                        log('warn',
                            "No blows assigned to your credentials.")
            else:
                log('error',
                    "Error on GET: grpkey (provider).", err=1)


def main():
    parser = argparse.ArgumentParser(
        description="autoauditor group signature demo3: read a blow")
    parser.add_argument('-u',
                        metavar='usr_dir',
                        default='fabric_credentials',
                        help="Fabric credentials path.")
    parser.add_argument('--usr-crt',
                        metavar='usr_crt',
                        default='user.crt',
                        help="User crt for blow verification.")
    parser.add_argument('--usr-key',
                        metavar='usr_key',
                        default='user.key',
                        help="User key for blow decryption.")
    parser.add_argument('-a',
                        metavar='address',
                        default='127.0.0.1',
                        help="Group signature (bridge) server address.")
    parser.add_argument('-p',
                        metavar='port', type=int,
                        default=5050,
                        help="Group signature (bridge) server port.")
    args = parser.parse_args()
    member = FabricMember((args.a, args.p),
                          (f'{args.u}/{args.usr_crt}',
                           f'{args.u}/{args.usr_key}'))
    member.retrieve_blows()


if __name__ == '__main__':
    main()
