#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later

# groupsig_inform - Member (informer) component.

# Copyright (C) 2022 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
# Universidad Carlos III de Madrid.

# This file is part of autoauditor.

# autoauditor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# autoauditor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with GNU Emacs.  If not, see <https://www.gnu.org/licenses/>.

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


DISC = "Leaked information in Org1 due to outdated systems: CVE-2022-21907"
CODE = constants.PS16_CODE
groupsig.init(CODE)

NONCE_SZ = 9
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


class Informer:
    def __init__(self, provider, verifier, grp_dir):
        self.url_pvr = f'https://{provider[0]}:{provider[1]}'
        self.url_vfr = f'https://{verifier[0]}:{verifier[1]}'
        self.session_pvr = requests.Session()
        self.session_pvr.verify = False
        self.session_pvr.cert = provider[2]
        self.session_vfr = requests.Session()
        self.session_vfr.verify = False
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
        resp = http_req('get', self.session_vfr,
                        f'{self.url_vfr}/sids')
        if resp.status_code == 200:
            data = json.loads(resp.text)
            if not data['msg'].startswith('Error'):
                sids = json.loads(data['msg'])
                resp = http_req('post', self.session_vfr,
                                f'{self.url_vfr}/pubkey',
                                {'sid': sids[0]})
                if resp.status_code == 200:
                    data = json.loads(resp.text)
                    if not data['msg'].startswith('Error'):
                        ephemeral_pk, shared_key = gen_ephemeral(data['msg'])
                        self.key = shared_key
                        self.plain_envelope = {
                            'sid': sids[0],
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
            else:
                log('error', data['msg'], err=1)
        else:
            log('error', "Error retrieving SIDs", err=1)

    def create_content(self):
        if self.envelope is not None:
            if self.key is not None:
                fer = Fernet(self.key)
                self.plain_content = {
                    'date': self.plain_envelope['date'],
                    'nonce': self.plain_envelope['nonce'],
                    'disclosure': DISC
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

    def publish_disclosure(self):
        if (self.envelope is not None and
            self.content is not None and
            self.signature is not None):  # noqa
            post = {
                'envelope': self.envelope.decode(),
                'content': self.content.decode(),
                'signature': self.signature
            }
            resp = http_req('post', self.session_vfr,
                            f'{self.url_vfr}/disclosure',
                            post)
            if resp.status_code == 200:
                data = json.loads(resp.text)
                if not data['msg'].startswith('Error'):
                    log('succ', data['msg'])
                else:
                    log('error', data['msg'], err=1)
            else:
                log('error', "Error on disclosure", err=1)
        else:
            log('error',
                "Create envelope, content and signature first", err=1)


def main():
    parser = argparse.ArgumentParser(
        description="autoauditor group signature demo2: publish a disclosure")
    parser.add_argument('-d',
                        metavar='dir',
                        default='tools/groupsig/informer/credentials',
                        help="Group credentials path.")
    parser.add_argument('-u',
                        metavar='usr_dir',
                        default='tools/groupsig/informer/fabric_credentials',
                        help="Fabric credentials path.")
    parser.add_argument('--crt',
                        metavar='crt',
                        default='user.crt',
                        help="User certificate for TLS authentication.")
    parser.add_argument('--key',
                        metavar='key',
                        default='user.key',
                        help="User key for TLS authentication.")
    parser.add_argument('--pvr-address',
                        metavar='address',
                        default='127.0.0.1',
                        help="Group signature (provider) address.")
    parser.add_argument('--pvr-port',
                        metavar='port', type=int,
                        default=5000,
                        help="Group signature (provider) port.")
    parser.add_argument('-a',
                        metavar='address',
                        default='127.0.0.1',
                        help="Group signature (verifier) address.")
    parser.add_argument('-p',
                        metavar='port', type=int,
                        default=5050,
                        help="Group signature (verifier) port.")
    args = parser.parse_args()
    informer = Informer((args.pvr_address, args.pvr_port,
                         (f'{args.u}/{args.crt}',
                          f'{args.u}/{args.key}')),
                        (args.a, args.p),
                        args.d)
    informer.create_envelope()
    informer.create_content()
    informer.create_signature()
    informer.publish_disclosure()


if __name__ == '__main__':
    main()
    groupsig.clear(constants.GL19_CODE)
