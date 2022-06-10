#!/usr/bin/env python3

from pygroupsig import constants, gml, groupsig, grpkey, message, mgrkey
from flask import Flask, render_template, request
from uuid import uuid4

import werkzeug.serving
import argparse
import OpenSSL
import errno
import json
import ssl
import sys
import os


app = Flask(__name__)
CODE = constants.PS16_CODE
groupsig.init(CODE)

CRED_DIR = 'tools/groupsig/provider/credentials'
PVR = None
TOKENS = {}
F_IMP = {
    'mgrkey': mgrkey.mgrkey_import,
    'grpkey': grpkey.grpkey_import,
    'gml': gml.gml_import
}
F_EXP = {
    'mgrkey': mgrkey.mgrkey_export,
    'grpkey': grpkey.grpkey_export,
    'gml': gml.gml_export
}
FILES = ['mgrkey', 'grpkey', 'gml']
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


# https://www.ajg.id.au/2018/01/01/mutual-tls-with-python-flask-and-werkzeug/
class PeerCertWSGIRequestHandler(werkzeug.serving.WSGIRequestHandler):
    def make_environ(self):
        environ = super(PeerCertWSGIRequestHandler, self).make_environ()
        x509_binary = self.connection.getpeercert(True)
        x509 = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_ASN1, x509_binary)
        environ['clientcrt'] = x509
        return environ


class Provider:
    def __init__(self, grp_dir):
        self.grp_dir = grp_dir
        if self.grp_dir is None:
            self.group = groupsig.setup(CODE)
        else:
            self.load()

    def load(self):
        self.group = {}
        for file in FILES:
            try:
                with open(f'{self.grp_dir}/{file}') as f:
                    if file != 'gml':
                        self.group[file] = F_IMP[file](CODE, f.read())
                        if file == 'grpkey':
                            print(grpkey.grpkey_export(self.group['grpkey']))
                    else:
                        try:
                            self.group[file] = F_IMP[file](CODE, f.read())
                        except Exception:
                            self.group[file] = gml.gml_init(CODE)
            except FileNotFoundError:
                log('error',
                    f"File {self.grp_dir}/{file} missing.",
                    err=errno.ENOENT)
                sys.exit(1)
            except PermissionError:
                log('error',
                    f"Can not open {self.grp_dir}/{file}",
                    err=errno.EACCES)
        global TOKENS
        try:
            with open(f'{self.grp_dir}/tokens') as f:
                TOKENS = json.load(f)
        except FileNotFoundError:
            TOKENS = {}

    def export_grpkey(self):
        return F_EXP['grpkey'](self.group['grpkey'])

    def save_credentials(self):
        try:
            os.makedirs(CRED_DIR, exist_ok=True)
        except PermissionError:
            log('error',
                f"Can not create {CRED_DIR}",
                err=errno.EACCES)
        for file in FILES:
            with open(f'{CRED_DIR}/{file}', 'w') as f:
                f.write(F_EXP[file](self.group[file]))
        with open(f'{CRED_DIR}/tokens', 'w') as f:
            json.dump(TOKENS, f, indent=2)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/grpkey')
def grp_key():
    return {'msg': PVR.export_grpkey()}


@app.route('/join')
def join_step1():
    client_sha = request.environ[
        'clientcrt'].digest('sha256').decode()
    res = {
        'msg': ("Error: You already received a token. "
                "Continue the process in /join/<token>"),
        'token': None
    }
    if client_sha not in TOKENS:
        TOKENS[client_sha] = [False, '']
        msg1 = groupsig.join_mgr(0,
                                 PVR.group['mgrkey'],
                                 PVR.group['grpkey'],
                                 gml=PVR.group['gml'])
        token = str(uuid4())
        TOKENS[client_sha][1] = token
        res['msg'] = message.message_to_base64(msg1)
        res['token'] = token
    return res


@app.route('/join/<token>', methods=['POST'])
def join_step2(token):
    client_sha = request.environ[
        'clientcrt'].digest('sha256').decode()
    res = {
        'msg': ("Error: You are not registered. "
                "Start the process in /join")
    }
    if client_sha in TOKENS:
        if token == TOKENS[client_sha][1]:
            if not TOKENS[client_sha][0]:
                TOKENS[client_sha][0] = True
                data = request.get_json()
                msgin = message.message_from_base64(data['msg'])
                msg3 = groupsig.join_mgr(2,
                                         PVR.group['mgrkey'],
                                         PVR.group['grpkey'],
                                         msgin=msgin,
                                         gml=PVR.group['gml'])
                res['msg'] = message.message_to_base64(msg3)
            else:
                res['msg'] = ("Error: You already completed "
                              "the join process.")
        else:
            res['msg'] = ("Error: Invalid token. "
                          "Use the token provided in /join")
    return res


def main():
    parser = argparse.ArgumentParser(
        description="autoauditor group signature provider")
    parser.add_argument('-d',
                        metavar='dir',
                        help="Group credentials path.")
    parser.add_argument('--ca-dir',
                        metavar='ca_dir',
                        default='tools/groupsig/provider/fabric_ca_certs',
                        help=("CA certificates path. "
                              "Certificates must be in format HHHHHHHH.D."
                              "Check man c_rehash."))
    parser.add_argument('--crt',
                        metavar='crt',
                        default='tools/groupsig/provider/provider.crt',
                        help="Server certificate for TLS connection.")
    parser.add_argument('--key',
                        metavar='key',
                        default='tools/groupsig/provider/provider.key',
                        help="Server key for TLS connection.")
    parser.add_argument('-p',
                        metavar='port', type=int,
                        default=5000,
                        help="Server listening port.")
    args = parser.parse_args()
    global PVR
    PVR = Provider(args.d)
    ssl_context = ssl.create_default_context(
        purpose=ssl.Purpose.CLIENT_AUTH, capath=args.ca_dir)

    # Server certificate and key for TLS connection
    ssl_context.load_cert_chain(
        certfile=args.crt, keyfile=args.key)
    # Force client certificate authentication
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    app.run(ssl_context=ssl_context,
            request_handler=PeerCertWSGIRequestHandler,
            port=args.p)
    PVR.save_credentials()


if __name__ == '__main__':
    main()
    groupsig.clear(constants.GL19_CODE)
