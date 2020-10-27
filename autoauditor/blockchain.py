#!/usr/bin/env python3

# blockchain - Blockchain module.

# Copyright (C) 2020 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
# Universidad Carlos III de Madrid.

# This file is part of AutoAuditor.

# AutoAuditor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# AutoAuditor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with GNU Emacs.  If not, see <https://www.gnu.org/licenses/>.

from hfc.fabric import Client
from hfc.fabric_network import wallet
from hfc.fabric_ca.caservice import Enrollment
from hfc.fabric.peer import create_peer
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from bs4 import BeautifulSoup
import constants as const
import argparse
import requests
import re
import os
import utils
import hashlib
import json
import sys
import asyncio
import logging
import sqlite3


RAPID7 = "https://www.rapid7.com/db/modules/"
CVEDETAILS = "https://www.cvedetails.com/cve/"

CHAINCODENAME = "autoauditor"
NEWREPORTFUNC = "NewReport"
NEWREPKEYWORD = "report"

cveregex = re.compile(r'^CVE-\d+-\d+')
modregex = re.compile(r'^\#{5}\s(?P<modname>[\w\d_\/]+)\s#{5}$')
modendregex = re.compile(r'^#{10,}$')
rprtdateregex = re.compile(r'^#{14}\s(?P<date>[\d:\-\s\+\.]+)\s#{14}$')
rhostregex = re.compile(r'^RHOSTS?\s+=>\s+(?P<ip>[\d\.]+)$')
affected1 = re.compile(r'^\[\+\].*$')
affected2 = re.compile(
    r'^((?=.*\bmeterpreter\b)|(?=.*\bsession\b))(?=.*\bopen(ed)?\b).*$',
    re.IGNORECASE)
affected3 = re.compile(
    (r'uid=\d+\([a-z_][a-z0-9_-]*\)\s+'
     r'gid=\d+\([a-z_][a-z0-9_-]*\)\s+'
     r'groups=\d+\([a-z_][a-z0-9_-]*\)(?:,\d+\([a-z_][a-z0-9_-]*\))*'),
    re.IGNORECASE)
affected4 = re.compile(
    (r'stor(ed|ing)|sav(ed|ing)|succe(ed|ss)|extract(ed|ing)|writt?(en|ing)|'
     r'retriev(ed|ing)|logg(ed|ing)|download(ed|ing)|st(ea|o)l(en|ing)|'
     r'add(ed|ing)|captur(ed|ing)|keylogg(ed|ing)|migrat(ed|ing)|'
     r'obtain(ed|ing)|dump(ed|ing)?[^_]'),
    re.IGNORECASE)
affected5 = re.compile(
    r'^(?=.*\b(credentials?|users?|account)\b)(?=.*\bfound\b).*$',
    re.IGNORECASE)

loop = asyncio.get_event_loop()


def set_up_cache():
    db = sqlite3.connect('autoauditor.db')
    cur = db.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS vulnerability (
            vuln_id TEXT PRIMARY KEY,
            score REAL
        )'''
                )
    cur.execute('''
        CREATE TABLE IF NOT EXISTS module (
            mod_id TEXT,
            vuln_id TEXT,
            PRIMARY KEY (mod_id, vuln_id),
            FOREIGN KEY (vuln_id) REFERENCES vulnerability (vuln_id)
        )'''
                )
    cur.execute('PRAGMA foreign_keys = ON;')

    return db


def is_cached(db, mod):
    cur = db.cursor()
    cur.execute(
        ('SELECT EXISTS('
         'SELECT 1 '
         'FROM module '
         'WHERE mod_id = ?)'),
        [mod]
    )
    return cur.fetchone()[0]  # (1,) if exists, (0,) otherwise


def get_cached(db, mod):
    cur = db.cursor()
    cur.execute(
        ('SELECT V.vuln_id, V.score '
         'FROM module M '
         'INNER JOIN vulnerability V ON M.vuln_id = V.vuln_id '
         'WHERE mod_id = ?'),
        [mod]
    )
    return cur.fetchall()


def cache(db, mod, data, update_cache=False):
    cur = db.cursor()
    if not update_cache:
        for vuln in data:
            cve, cve_sc = vuln
            cur.execute(
                ('INSERT INTO vulnerability '
                 'VALUES (?, ?)'),
                [cve, cve_sc]
            )
            db.commit()

            cur.execute(
                ('INSERT INTO module '
                 'VALUES (?, ?)'),
                [mod, cve]
            )
            db.commit()
    else:
        cached = get_cached(db, mod)
        if cached != data.sort():
            cur.execute(
                ('DELETE FROM module '
                 'WHERE mod_id=?'),
                [mod]
            )
            db.commit()

            for vuln in data:
                cve, cve_sc = vuln
                cur.execute(
                    ('SELECT EXISTS('
                     'SELECT 1 FROM vulnerability '
                     'WHERE vuln_id = ?)'),
                    [cve]
                )
                aux = cur.fetchone()[0]
                if aux:
                    cur.execute(
                        ('UPDATE vulnerability '
                         'SET score = ? '
                         'WHERE vuln_id = ?'),
                        [cve_sc, cve]
                    )
                    db.commit()
                else:
                    cur.execute(
                        ('INSERT INTO vulnerability '
                         'VALUES (?, ?)'),
                        [cve, cve_sc]
                    )
                    db.commit()

                cur.execute(
                    ('INSERT INTO module '
                     'VALUES (?, ?)'),
                    [mod, cve]
                )
                db.commit()


def get_cve(exploit):
    try:
        req = requests.get(RAPID7 + exploit)
    except requests.exceptions.ConnectionError:
        utils.log(
            'error',
            'Connection error. Check internet connection.',
            errcode=const.ECONN)

    soup = BeautifulSoup(req.text, features='html.parser')
    references = soup.find(
        'section', attrs={'class': 'vulndb__references'}).find_all('a')
    cve_vuln = [ref.string for ref in references if cveregex.match(
        ref.string) is not None]
    return cve_vuln


def get_score(cve):
    try:
        req = requests.get(CVEDETAILS + cve)
    except requests.exceptions.ConnectionError:
        utils.log(
            'error',
            'Connection error. Check internet connection.',
            errcode=const.ECONN)

    soup = BeautifulSoup(req.text, features='html.parser')
    score = soup.find('div', attrs={'class': 'cvssbox'}).string
    return score


def parse_report(rep_file):
    mod = {}
    with open(rep_file, 'r') as f:
        lines = filter(None, (line.rstrip() for line in f))
        modname = None
        host = None
        affected = False
        for line in lines:
            drm = rprtdateregex.match(line)
            if drm is not None:
                mod['date'] = drm.group('date')

            mrm = modregex.match(line)
            if mrm is not None:
                modname = mrm.group('modname')
                if modname not in mod:
                    mod[modname] = []

            hrm = rhostregex.match(line)
            if hrm is not None:
                host = hrm.group('ip')

            if affected1.search(line) is not None or \
               affected2.search(line) is not None or \
               affected3.search(line) is not None or \
               affected4.search(line) is not None or \
               affected5.search(line) is not None:
                affected = True

            endrm = modendregex.match(line)
            if endrm is not None and modname is not None:
                mod[modname].append((host, affected))
                modname = None
                host = None
                affected = False
    return mod


def generate_reports(rep, update_cache):
    info = parse_report(rep)

    db = set_up_cache()

    report = {}
    report['privrep'] = {}
    report['pubrep'] = {}

    try:
        date = info.pop('date')
        report['date'] = date
    except KeyError:
        utils.log('error',
                  'Wrong report format.',
                  errcode=const.EBADREPFMT)

    nvuln = 0
    for mod in info:
        if is_cached(db, mod) and not update_cache:
            cve_sc = get_cached(db, mod)
        else:
            cve_sc = [(cve, get_score(cve)) for cve in get_cve(mod)]
            cache(db, mod, cve_sc, update_cache)

        nvuln += len(cve_sc)
        for elem in cve_sc:
            cve, score = elem
            # mach = (1.1.1.1, True)
            affected_mach = [mach[0] for mach in info[mod] if mach[1]]
            report['privrep'][cve] = {
                'Score': score,
                'MSFmodule': mod,
                'AffectedMachines': affected_mach}
            report['pubrep'][cve] = {'Score': score,
                                     'AffectedMachines': len(affected_mach)}

    report['nvuln'] = nvuln

    return report


def store_report(info, rep_file, out_file, update_cache=False):
    user, client, peer, channel_name = info

    utils.log('succb', const.GENREP, end='\r')
    report = generate_reports(rep_file, update_cache)
    utils.log('succg', const.GENREPDONE)

    privdate = report.pop('date')  # yyyy-mm-dd hh:mm:ss.ffffff+tt:zz
    pubdate = privdate[:7]  # yyyy-mm

    nvuln = report.pop('nvuln')

    repid = user.org + privdate
    rephash = hashlib.sha256(repid.encode('utf-8')).hexdigest()

    aarep = {'id': rephash,
             'org': user.org,
             'date': privdate,
             'nvuln': nvuln}

    with open(out_file, 'w') as out:
        utils.log(
            'succb',
            "Blockchain output log: {}"
            .format(out_file))

        for rep in report:
            aarep['report'] = report[rep]  # dump report to log file

            if rep == 'privrep':
                aarep['private'] = True
                out.write(json.dumps(aarep, indent=4) + ',\n')
            else:
                aarep['private'] = False
                aarep['date'] = pubdate
                out.write(json.dumps(aarep, indent=4) + '\n')

            aarep['report'] = json.dumps(report[rep])  # must be serialized
            tmprep = json.dumps(aarep).encode()

            utils.log(
                'succb',
                "Storing {} report: {}"
                .format("private" if aarep['private'] else "public", rephash))

            try:
                response = loop.run_until_complete(client.chaincode_invoke(
                    requestor=user,
                    channel_name=channel_name,
                    peers=[peer],
                    fcn=NEWREPORTFUNC,
                    args=None,
                    cc_name=CHAINCODENAME,
                    transient_map={NEWREPKEYWORD: tmprep}
                ))
            except Exception as e:
                utils.log(
                    'error',
                    "Error storing report {}: {}"
                    .format(rephash, str(e)),
                    errcode=const.EHLFCONN)
            else:
                if not response:
                    utils.log(
                        'succg',
                        "Report stored successfully in blockchain.")
                elif 'already' in response:
                    utils.log(
                        'warn',
                        "Report already stored in blockchain.")
                elif 'failed' in response:
                    utils.log(
                        'error',
                        "Error storing report {}: {}"
                        .format(rephash, response),
                        errcode=const.EHLFCONN)
                else:
                    utils.log(
                        'error',
                        "Unknown error storing report {}: {}"
                        .format(rephash, response),
                        errcode=const.EHLFCONN)


def get_net_info(config, *key_path):
    if config:
        for k in key_path:
            try:
                config = config[k]
            except KeyError:
                utils.log(
                    'error',
                    "No key path {key_path} exists in network info",
                    errcode=const.EBADNETFMT)
        return config


def load_config(config):
    _logger = logging.getLogger('hfc.fabric.client')
    _logger.setLevel(logging.NOTSET)

    client_discovery = Client()

    with open(config, 'r') as f:
        network = json.load(f)

    peer_config = get_net_info(network, 'network', 'organization', 'peer')
    tls_cacerts = peer_config['tls_cacerts']
    opts = (('grpc.ssl_target_name_override', peer_config['server_hostname']),)
    endpoint = peer_config['grpc_request_endpoint']

    peer = create_peer(endpoint=endpoint,
                       tls_cacerts=tls_cacerts,
                       opts=opts)

    channel_name = get_net_info(network, 'network', 'channel')

    wpath = get_net_info(network, 'client', 'wallet', 'path')
    userId = get_net_info(network, 'client', 'id')
    org = get_net_info(network, 'network', 'organization', 'name')
    mspId = get_net_info(network, 'network', 'organization', 'mspid')

    wal = wallet.FileSystenWallet(wpath)

    if wal.exists(userId):
        user = wal.create_user(userId, org, mspId)
    else:
        with open(
                get_net_info(network, 'client', 'credentials', 'cert'),
                'rb') as f:
            crt = f.read()
        with open(
                get_net_info(network, 'client', 'credentials', 'private_key'),
                'rb') as f:
            pk = load_pem_private_key(
                f.read(), password=None, backend=default_backend())

        enroll = Enrollment(private_key=pk, enrollmentCert=crt)

        uidentity = wallet.Identity(userId, enroll)
        uidentity.CreateIdentity(wal)

        user = wal.create_user(userId, org, mspId)

    loop.run_until_complete(
        client_discovery.init_with_discovery(user, peer,
                                             channel_name))

    return (user, client_discovery, peer, channel_name)


def main():
    parser = argparse.ArgumentParser(
        description="Autoauditor submodule to store reports in blockchain.")

    parser.add_argument('-f', '--reportfile',
                        metavar='log_file',
                        required=True,
                        help="AutoAuditor log file.")

    parser.add_argument('-ho', '--hyperledgerout',
                        metavar='hyperledger_log_file',
                        default='output/blockchain.log',
                        help="Blockchain report log file.")

    parser.add_argument('-hc', '--hyperledgercfg',
                        metavar='hyperledger_config_file',
                        required=True,
                        help="Blockchain network configuration file.")

    parser.add_argument('--force-update-cache',
                        action='store_true',
                        help=("Force cache update. "
                              "Data will be downloaded again."))

    args = parser.parse_args()

    utils.copyright()

    if not os.path.isfile(args.reportfile):
        utils.log(
            'error',
            "File {} does not exist."
            .format(args.reportfile),
            errcode=const.ENOENT)
    if not os.path.isfile(args.hyperledgercfg):
        utils.log(
            'error',
            "File {} does not exist."
            .format(args.hyperledgercfg),
            errcode=const.ENOENT)

    info = load_config(args.hyperledgercfg)

    utils.check_file_dir(args.hyperledgerout)

    store_report(info, args.reportfile, args.hyperledgerout,
                 args.force_update_cache)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        utils.log(
            'normal',
            '\n')
        utils.log(
            'error',
            "Interrupted, exiting program. Containers will keep running ...")

        sys.exit(const.EINTR)
