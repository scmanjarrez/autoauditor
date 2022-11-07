#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later

# grupsig_verifier - Verifier component.

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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from pygroupsig import constants, groupsig, grpkey, signature
from flask import Flask, render_template, request
from autoauditor import blockchain as bc

import argparse
import requests
import asyncio
import hashlib
import base64
import errno
import json
import sys


loop = asyncio.get_event_loop()
app = Flask(__name__)
CODE = constants.PS16_CODE
groupsig.init(CODE)

VRF = None
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


def http_get(session, url):
    try:
        resp = session.get(url)
    except requests.exceptions.InvalidURL as e:
        log('error',
            f"Invalid '{url}': {e.__context__}",
            err=errno.EDESTADDRREQ)
    except requests.exceptions.ConnectionError as e:
        log('error',
            f"Can not connect to '{url}': {e.__context__}",
            err=errno.ECONNREFUSED)
    return resp


class Verifier:
    def __init__(self, provider, blockchain):
        self.info = bc.load_config(blockchain)
        self.url = f'https://{provider[0]}:{provider[1]}'
        self.session = requests.Session()
        self.session.verify = False
        self.session.cert = self.extract_credentials(blockchain)
        self.retrieve_grpkey()

    def extract_credentials(self, config):
        with open(config) as f:
            try:
                network = json.load(f)
            except json.JSONDecodeError:
                log('error',
                    "Bad network format",
                    err=1)
            else:
                try:
                    return (network['client']['credentials']['cert'],
                            network['client']['credentials']['private_key'])
                except KeyError:
                    log('error',
                        'Credentials not found in blockchain config',
                        err=1)

    def retrieve_grpkey(self):
        resp = http_get(self.session, f'{self.url}/grpkey')
        data = json.loads(resp.text)
        self.grpkey = grpkey.grpkey_import(CODE, data['msg'])

    def retrieve_sids(self):
        user, client, peer, channel = self.info
        res = {
            'msg': "Error:"
        }
        try:
            resp = loop.run_until_complete(client.chaincode_query(
                requestor=user,
                channel_name=channel,
                peers=[peer],
                fcn='GetSubscribersId',
                args=None,
                cc_name='whistleblower'
            ))
        except Exception as e:
            import grpc
            if isinstance(e, grpc._channel._MultiThreadedRendezvous):
                log('error',
                    ("Error querying blockchain. "
                     "Are you running updated credentials?"))
                res['msg'] = "Error: server running outdated credentials."
            else:
                res['msg'] = f"Error: {e.args[0][0].response.message}"
        else:
            res['msg'] = resp
        return res

    def retrieve_certificate(self, sid):
        user, client, peer, channel = self.info
        res = {
            'msg': "Error:"
        }
        try:
            resp = loop.run_until_complete(client.chaincode_query(
                requestor=user,
                channel_name=channel,
                peers=[peer],
                fcn='GetCertificateById',
                args=[sid],
                cc_name='whistleblower'
            ))
        except Exception as e:
            import grpc
            if isinstance(e, grpc._channel._MultiThreadedRendezvous):
                log('error',
                    ("Error querying blockchain. "
                     "Are you running updated credentials?"))
                res['msg'] = "Error: server running outdated credentials."
            else:
                res['msg'] = f"Error: {e.args[0][0].response.message}"
        else:
            res['msg'] = resp
        return res

    def publish_disclosure(self, envelope, content):
        user, client, peer, channel = self.info
        store = {
            'envelope': envelope,
            'content': content
        }
        res = {
            'msg': "Error:"
        }
        b64disc = base64.b64encode(json.dumps(store).encode()).decode()
        try:
            resp = loop.run_until_complete(client.chaincode_invoke(
                requestor=user,
                channel_name=channel,
                peers=[client.peers['peer0.org3.example.com'],
                       client.peers['peer0.org1.example.com']],
                fcn='PublishDisclosure',
                args=[b64disc],
                cc_name='whistleblower'
            ))
            print(resp)
        except Exception as e:
            res['msg'] = f"Error: {e.args[0][0].response.message}"
        else:
            if not resp:
                res['msg'] = "Disclosure stored successfully"
            elif 'already' in resp:
                res['msg'] = "Error: Disclosure already in blockchain"
            else:
                res['msg'] = f"Error: {resp}"
        return res

    def disclosures(self):
        user, client, peer, channel = self.info
        res = {
            'msg': "Error:"
        }
        try:
            resp = loop.run_until_complete(client.chaincode_query(
                requestor=user,
                channel_name=channel,
                peers=[peer],
                fcn='GetDisclosures',
                args=None,
                cc_name='whistleblower'
            ))
        except Exception as e:
            res['msg'] = f"Error: {e.args[0][0].response.message}"
        else:
            res['msg'] = resp
        return res


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/pubkey', methods=['POST'])
def pub_key():
    res = {
        'msg': ("Error: Invalid query format. "
                "Send a POST formatted as {\"sid\": \"subscriber_id\"}")
    }
    data = request.get_json()
    if 'sid' in data:
        res = VRF.retrieve_certificate(data['sid'])
    return res


@app.route('/disclosure', methods=['POST'])
def disclosure():
    res = {
        'msg': "Error: envelope/content/signature missing."
    }
    data = request.get_json()
    if ('envelope' in data and
        'content' in data and
        'signature' in data):  # noqa
        env = data['envelope']
        cnt = data['content']
        verify = {
            'envelope': hashlib.sha256(env.encode()).hexdigest(),
            'content': hashlib.sha256(cnt.encode()).hexdigest()
        }
        sig = data['signature']
        if groupsig.verify(
                signature.signature_import(CODE, sig),
                json.dumps(verify).encode(),
                VRF.grpkey):
            res = VRF.publish_disclosure(env, cnt)
        else:
            res['msg'] = "Error: invalid signature. Verification failed"
    return res


@app.route('/sids')
def sids():
    return VRF.retrieve_sids()


@app.route('/disclosures')
def disclosures():
    return VRF.disclosures()


def main():
    parser = argparse.ArgumentParser(
        description="autoauditor group signature provider")
    parser.add_argument('-b',
                        metavar='bc_cfg',
                        default='tools/groupsig/examples/network.example.json',
                        help="Group signature (provider) server address.")
    parser.add_argument('--pvr-address',
                        metavar='provider_address',
                        default='127.0.0.1',
                        help="Group signature (provider) server port.")
    parser.add_argument('--pvr-port',
                        metavar='provider_port', type=int,
                        default=5000,
                        help="Blockchain network configuration.")
    parser.add_argument('--crt',
                        metavar='crt',
                        default='tools/groupsig/verifier/verifier.crt',
                        help="Server certificate for TLS connection.")
    parser.add_argument('--key',
                        metavar='key',
                        default='tools/groupsig/verifier/verifier.key',
                        help="Server key for TLS connection.")
    parser.add_argument('-p',
                        metavar='port', type=int,
                        default=5050,
                        help="Server listening port.")
    args = parser.parse_args()
    global VRF
    VRF = Verifier((args.pvr_address, args.pvr_port), args.b)
    app.run(ssl_context=(args.crt, args.key),
            port=args.p)


if __name__ == '__main__':
    main()
    groupsig.clear(constants.GL19_CODE)
