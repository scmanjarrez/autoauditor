#!/usr/bin/env python3

from cryptography.hazmat.primitives.serialization import (Encoding,
                                                          PublicFormat)
from pygroupsig import constants, groupsig, grpkey, memkey, signature
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf import hkdf
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
from cryptography import x509
from datetime import datetime
import argparse
import requests
import hashlib
import urllib3
import base64
import errno
import json
import sys
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


SID = ("eDUwOTo6Q049dXNlcjEsT1U9Y2xpZW50LE89SHlwZXJsZWRnZXIsU1Q9T"
       "m9ydGggQ2Fyb2xpbmEsQz1VUzo6Q049Y2Eub3JnMS5leGFtcGxlLmNvbS"
       "xPPW9yZzEuZXhhbXBsZS5jb20sTD1MZWdhbmVzLFNUPUNvbXVuaWRhZCB"
       "kZSBNYWRyaWQsQz1FUw==")
BLOW = "Leaked information in Org1 due to outdated systems: CVE-2022-21907"
CODE = constants.PS16_CODE
groupsig.init(CODE)

NONCE_SZ = 8
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


def gen_nonce():
    string = base64.b64encode(os.urandom(NONCE_SZ), altchars=b'-_')
    return string.decode()


def gen_ephemeral(certificate):
    cert = x509.load_pem_x509_certificate(
        f'-----BEGIN CERTIFICATE-----\n'
        f'{certificate}'
        f'-----END CERTIFICATE-----\n'.encode())
    ephemeral_ec = ec.generate_private_key(ec.SECP256R1())
    pkbytes = ephemeral_ec.public_key().public_bytes(
        Encoding.PEM,
        PublicFormat.SubjectPublicKeyInfo).decode()
    pkbytes_stripped = pkbytes.replace(
        '\n', '').replace(
            '-----BEGIN PUBLIC KEY-----', '').replace(
                '-----END PUBLIC KEY-----', '')
    shared_key = ephemeral_ec.exchange(ec.ECDH(),
                                       cert.public_key())
    derived_key = hkdf.HKDF(
        algorithm=hashes.SHA256(), length=32,
        salt=None, info=b'ephemeral').derive(shared_key)
    return pkbytes_stripped, base64.b64encode(derived_key)


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


class GroupMember:
    def __init__(self, provider, bridge, grp_dir):
        self.url_pvr = f'https://{provider[0]}:{provider[1]}'
        self.url_brg = f'https://{bridge[0]}:{bridge[1]}'
        self.session_pvr = requests.Session()
        self.session_pvr.verify = False
        self.session_pvr.cert = provider[2]
        self.session_brg = requests.Session()
        self.session_brg.verify = False
        self.grp_dir = grp_dir
        self.usk = None
        self.envelope = None
        self.content = None
        self.signature = None
        self.load()

    def load(self):
        with open(f'{self.grp_dir}/memkey') as f:
            self.usk = memkey.memkey_import(CODE, f.read())
        resp = http_req('get', self.session_pvr, f'{self.url_pvr}/grpkey')
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

    def create_envelope(self):
        resp = http_req('post', self.session_brg,
                        f'{self.url_brg}/pubkey',
                        {'sid': SID})
        if resp.status_code == 200:
            data = json.loads(resp.text)
            if not data['msg'].startswith('Error'):
                ephemeral_pk, shared_key = gen_ephemeral(data['msg'])
                self.key = shared_key
                self.plain_envelope = {
                    'sid': SID,
                    'date': datetime.utcnow().isoformat(),
                    'nonce': gen_nonce(),
                    'ecdhe': ephemeral_pk
                }
                self.envelope = base64.b64encode(
                    json.dumps(self.plain_envelope).encode())
            else:
                log('error', data['msg'], err=1)
        else:
            log('error', "Error on create envelope", err=1)

    def create_content(self):
        if self.envelope is not None:
            if self.key is not None:
                fer = Fernet(self.key)
                self.plain_content = {
                    'date': self.plain_envelope['date'],
                    'nonce': self.plain_envelope['nonce'],
                    'blow': BLOW
                }
                self.content = fer.encrypt(
                    json.dumps(self.plain_content).encode()
                )
            else:
                log('error',
                    "Ephemeral key does not exist. "
                    "Run create_envelope before creating content.",
                    err=1)
        else:
            log('error', "Create envelope first", err=1)

    def create_signature(self):
        if self.envelope is not None and self.content is not None:
            self.plain_signature = {
                'envelope': hashlib.sha256(self.envelope).hexdigest(),
                'content': hashlib.sha256(self.content).hexdigest()
            }
            self.signature = signature.signature_export(groupsig.sign(
                json.dumps(self.plain_signature).encode(),
                self.usk, self.grpkey))
        else:
            log('error', "Create envelope and content first", err=1)

    def publish_blow(self):
        if (self.envelope is not None and
            self.content is not None and
            self.signature is not None):  # noqa
            post = {
                'envelope': self.envelope.decode(),
                'content': self.content.decode(),
                'signature': self.signature
            }
            resp = http_req('post', self.session_brg,
                            f'{self.url_brg}/blow',
                            post)
            if resp.status_code == 200:
                data = json.loads(resp.text)
                if not data['msg'].startswith('Error'):
                    log('succ', data['msg'])
                else:
                    log('error', data['msg'], err=1)
            else:
                log('error', "Error on blow", err=1)
        else:
            log('error',
                "Create envelope, content and signature first", err=1)


def main():
    parser = argparse.ArgumentParser(
        description="autoauditor group signature demo2: publish a blow")
    parser.add_argument('-d',
                        metavar='dir',
                        default='credentials',
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
    parser.add_argument('--pvr-address',
                        metavar='address',
                        default='127.0.0.1',
                        help="Group signature provider address.")
    parser.add_argument('--pvr-port',
                        metavar='port', type=int,
                        default=5000,
                        help="Group signature provider port.")
    parser.add_argument('-a',
                        metavar='address',
                        default='127.0.0.1',
                        help="Group signature bridge address.")
    parser.add_argument('-p',
                        metavar='port', type=int,
                        default=5050,
                        help="Group signature bridge port.")
    args = parser.parse_args()
    member = GroupMember((args.pvr_address, args.pvr_port,
                          (f'{args.u}/{args.usr_crt}',
                           f'{args.u}/{args.usr_key}')),
                         (args.a, args.p),
                         args.d)
    member.create_envelope()
    member.create_content()
    member.create_signature()
    member.publish_blow()


if __name__ == '__main__':
    main()
    groupsig.clear(constants.GL19_CODE)
