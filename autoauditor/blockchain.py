#!/usr/bin/env python3

# blockchain - Blockchain module.

# Copyright (C) 2021 Sergio Chica Manjarrez @ pervasive.it.uc3m.es.
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

from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
from hfc.fabric_ca.caservice import Enrollment
from hfc.fabric.peer import create_peer
from hfc.fabric_network import wallet
from hfc.fabric import Client
from bs4 import BeautifulSoup
import asyncio as _asyncio
import constants as cst
import otsclient.args
import metasploit
import argparse
import requests
import hashlib
import logging
import sqlite3
import wizard
import utils
import copy
import json
import os
import re
import sys


CVEDETAILS = "https://www.cvedetails.com/cve/"

CHAINCODENAME = "autoauditor"
NEWREPORTFUNC = "NewReport"
NEWREPKEYWORD = "report"

_tmp_outf = None
_tmp_outd = None
_tmp_msfcont = None
_tmp_shutdown = False

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
    global _tmp_msfcont
    if _tmp_msfcont is None:
        utils.check_file_dir(_tmp_outf, _tmp_outd)
        _tmp_msfcont = metasploit.start_msfrpcd(_tmp_outd)

    exp = exploit.split('/')
    cl = metasploit.get_msf_connection(cst.DEF_MSFRPC_PWD)
    mod = wizard.get_module(cl, exp[0], "/".join(exp[1:]))

    return wizard.get_module_references(mod)


def get_score(cve):
    try:
        req = requests.get(CVEDETAILS + cve)
    except requests.exceptions.ConnectionError:
        utils.log(
            'error',
            'Connection error. Check internet connection.',
            errcode=cst.ECONN)

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
                  errcode=cst.EBADREPFMT)

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


def store_report(info, rep_file, out_file, update_cache=False, loop=None):
    if loop is None:
        loop = _asyncio.get_event_loop()
    user, client, peer, channel_name = info

    utils.log('succb', cst.GENREP, end='\r')
    reports = generate_reports(rep_file, update_cache)
    utils.log('succg', cst.GENREPDONE)

    privdate = reports.pop('date')  # yyyy-mm-dd hh:mm:ss.ffffff+tt:zz
    pubdate = privdate[:7]  # yyyy-mm

    nvuln = reports.pop('nvuln')

    rid = user.org + privdate
    rhash = hashlib.sha256(rid.encode('utf-8')).hexdigest()

    rep = {'id': rhash,
           'org': user.org,
           'date': privdate,
           'nvuln': nvuln,
           'report': {},
           'private': True}

    uploaded = 0

    log_rep = {"public": None, "private": None}

    for r in reports:
        tmp_rep = rep.copy()
        _type = 'private'
        tmp_rep['report'] = reports[r]  # dump report to log file

        if r == 'pubrep':
            tmp_rep['private'] = False
            tmp_rep['date'] = pubdate
            _type = 'public'

        log_rep[_type] = copy.deepcopy(tmp_rep)

        tmp_rep['report'] = json.dumps(reports[r])  # must be serialized
        trans_map = json.dumps(tmp_rep).encode()

        utils.log(
            'succb',
            f"Storing {_type} report: {rhash}")

        try:
            resp = loop.run_until_complete(client.chaincode_invoke(
                requestor=user,
                channel_name=channel_name,
                peers=[peer],
                fcn=NEWREPORTFUNC,
                args=None,
                cc_name=CHAINCODENAME,
                transient_map={NEWREPKEYWORD: trans_map}
            ))
        except Exception as e:
            utils.log(
                'error',
                f"Error storing {_type} report {rhash}: {e}",
                errcode=cst.EHLFCONN)
        else:
            if not resp:
                utils.log(
                    'succg',
                    f"{_type.capitalize()} report stored successfully.")
                uploaded += 1
            elif 'already' in resp:
                utils.log(
                    'warn',
                    f"{_type.capitalize()} report already in blockchain.")
            elif 'failed' in resp:
                utils.log(
                    'error',
                    f"Error storing {_type} report {rhash}: {resp}",
                    errcode=cst.EHLFCONN)
            else:
                utils.log(
                    'error',
                    "Unknown error storing {_type} report {rhash}: {resp}",
                    errcode=cst.EHLFCONN)
    utils.log(
        'succb',
        f"Blockchain output log: {out_file}")

    with open(out_file, 'w') as out:
        out.write(json.dumps(log_rep, indent=4))

    if uploaded == 2:
        opentimestamp_format()
        utils.log('succb', "Creating report timestamp...")
        args = otsclient.args.parse_ots_args(['stamp', out_file])
        args.cmd_func(args)


def _get_network_info(config, *key_path):
    if config:
        for k in key_path:
            try:
                config = config[k]
            except KeyError:
                utils.log(
                    'error',
                    "No key path {key_path} exists in network info",
                    errcode=cst.EBADNETFMT)
        return config


def load_config(config, loop=None):
    if loop is None:
        loop = _asyncio.get_event_loop()
    _loggcl = logging.getLogger('hfc.fabric.client')
    _loggcl.setLevel(logging.WARN)

    _loggdisc = logging.getLogger('hfc.fabric.channel.channel')
    _loggdisc.setLevel(logging.WARN)

    client_discovery = Client()

    with open(config, 'r') as f:
        try:
            network = json.load(f)
        except json.JSONDecodeError:
            utils.log('error',
                      (f"Wrong network configuration file format. "
                       f"Check {utils.NET_TEMPLATE}."),
                      errcode=cst.EBADNETFMT)

    peer_config = _get_network_info(network,
                                    'network', 'organization', 'peer')
    tls_cacerts = peer_config['tls_cacerts']
    opts = (('grpc.ssl_target_name_override', peer_config['server_hostname']),)
    endpoint = peer_config['grpc_request_endpoint']

    try:
        peer = create_peer(endpoint=endpoint,
                           tls_cacerts=tls_cacerts,
                           opts=opts)
    except FileNotFoundError:
        utils.log('error', ("Check network configuration file. "
                            "TLS CA certs missing."), errcode=cst.ENOENT)
        return

    channel_name = _get_network_info(network,
                                     'network', 'channel')

    wpath = _get_network_info(network,
                              'client', 'wallet', 'path')
    userId = _get_network_info(network,
                               'client', 'id')
    org = _get_network_info(network,
                            'network', 'organization', 'name')
    mspId = _get_network_info(network,
                              'network', 'organization', 'mspid')

    wal = wallet.FileSystenWallet(wpath)

    if wal.exists(userId):
        user = wal.create_user(userId, org, mspId)
    else:
        with open(
                _get_network_info(network,
                                  'client', 'credentials', 'cert'),
                'rb') as f:
            crt = f.read()
        with open(
                _get_network_info(network,
                                  'client', 'credentials', 'private_key'),
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


def opentimestamp_format():
    class OpenTimeStampFormatter(logging.Formatter):
        err_fmt = f"{utils._RED}[!]{utils._CLEANC} %(msg)s"
        warn_fmt = f"{utils._YELLOW}[-]{utils._CLEANC} %(msg)s"
        dbg_fmt = f"{utils._BLUE}[*]{utils._CLEANC} %(msg)s"
        info_fmt = f"{utils._GREEN}[+]{utils._CLEANC} %(msg)s"

        def __init__(self):
            super().__init__(fmt="[*] %(msg)s", datefmt=None, style='%')

        def format(self, record):
            # Backup initial style
            format_orig = self._style._fmt

            if record.levelno == logging.DEBUG:
                self._style._fmt = OpenTimeStampFormatter.dbg_fmt

            elif record.levelno == logging.INFO:
                self._style._fmt = OpenTimeStampFormatter.info_fmt

            elif record.levelno == logging.WARN:
                self._style._fmt = OpenTimeStampFormatter.warn_fmt

            elif record.levelno == logging.ERROR:
                self._style._fmt = OpenTimeStampFormatter.err_fmt

            # Process log with custom format
            result = logging.Formatter.format(self, record)

            # Restore initial style
            self._style._fmt = format_orig

            return result

    class OpenTimeStampGUIHandler(logging.StreamHandler):
        def __init__(self):
            logging.StreamHandler.__init__(self)

        def emit(self, record):
            msg = self.format(record)
            utils.WINDOW.write_event_value('LOG', msg)

    ots = OpenTimeStampFormatter()
    if utils.WINDOW:
        ots_handler = OpenTimeStampGUIHandler()
    else:
        ots_handler = logging.StreamHandler(sys.stdout)

    ots_handler.setFormatter(ots)
    logging.root.addHandler(ots_handler)
    logging.root.setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(
        description="Autoauditor submodule to store reports in blockchain.")

    parser.add_argument('-o', '--outfile',
                        metavar='log_file',
                        default='output/msf.log',
                        help=("AutoAuditor log file."))

    parser.add_argument('-d', '--outdir',
                        metavar='gather_dir',
                        default='output/loot',
                        help=("AutoAuditor output directory."))

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

    parser.add_argument('--no-color',
                        action='store_true',
                        help="Disable ANSI color output.")

    args = parser.parse_args()

    utils.copyright()

    global _tmp_outd, _tmp_outf, _tmp_shutdown
    _tmp_outd = args.outdir
    _tmp_outf = args.outfile
    _tmp_shutdown = True

    if args.no_color:
        utils.disable_ansi_colors()

    if not os.path.isfile(args.outfile):
        utils.log(
            'error',
            f"File {args.outfile} does not exist.",
            errcode=cst.ENOENT)

    if not os.path.isfile(args.hyperledgercfg):
        utils.log(
            'error',
            f"File {args.hyperledgercfg} does not exist.",
            errcode=cst.ENOENT)

    info = load_config(args.hyperledgercfg)

    utils.check_file_dir(args.hyperledgerout)

    store_report(info, args.outfile, args.hyperledgerout,
                 args.force_update_cache)

    if _tmp_shutdown and _tmp_msfcont is not None:
        utils.shutdown(_tmp_msfcont)


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

        sys.exit(cst.EINTR)
