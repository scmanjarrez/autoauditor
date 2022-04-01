#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later

# blockchain - Blockchain module.

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

from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
from hfc.fabric_ca.caservice import Enrollment
from autoauditor import metasploit as ms
from autoauditor import constants as ct
from hfc.fabric.peer import create_peer
from hfc.fabric_network import wallet
from autoauditor import wizard as wz
from autoauditor import utils as ut
from contextlib import closing
from hfc.fabric import Client
from bs4 import BeautifulSoup

import asyncio as _asyncio
import otsclient.args
import requests
import hashlib
import logging
import sqlite3
import errno
import json
import sys
import re


CVEDETAILS = "https://www.cvedetails.com/cve/"

CC = 'autoauditor'
CC_FUN = 'StoreReport'
CC_TRANS = 'report'

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
    with closing(db.cursor()) as cur:
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS cves (
                cve_id TEXT PRIMARY KEY,
                cvss REAL
            );

            CREATE TABLE IF NOT EXISTS modules (
                metasploit_id TEXT,
                cve_id TEXT,
                PRIMARY KEY (metasploit_id, cve_id),
                FOREIGN KEY (cve_id) REFERENCES cves (cve_id)
            );

            PRAGMA foreign_keys = ON;
            """
        )
    return db


def is_cached(db, mod):
    with closing(db.cursor()) as cur:
        cur.execute(
            'SELECT EXISTS('
            'SELECT 1 FROM modules '
            'WHERE metasploit_id = ?'
            ')',
            [mod])
        return cur.fetchone()[0]


def get_cached(db, mod):
    with closing(db.cursor()) as cur:
        cur.execute(
            'SELECT V.cve_id, V.cvss FROM modules M '
            'INNER JOIN cves V ON M.cve_id = V.cve_id '
            'WHERE metasploit_id = ?',
            [mod])
        return cur.fetchall()


def cache(db, mod, data, update_cache=False):
    with closing(db.cursor()) as cur:
        if not update_cache:
            for vuln in data:
                cve, cve_sc = vuln
                cur.execute(
                    'INSERT INTO cves VALUES (?, ?)',
                    [cve, cve_sc])
                db.commit()

                cur.execute(
                    'INSERT INTO modules VALUES (?, ?)',
                    [mod, cve])
                db.commit()
        else:
            cached = get_cached(db, mod)
            if cached != data.sort():
                cur.execute(
                    'DELETE FROM modules '
                    'WHERE metasploit_id = ?',
                    [mod])
                db.commit()
                for vuln in data:
                    cve, cve_sc = vuln
                    cur.execute(
                        'SELECT EXISTS('
                        'SELECT 1 FROM cves '
                        'WHERE cve_id = ?'
                        ')',
                        [cve])
                    aux = cur.fetchone()[0]
                    if aux:
                        cur.execute(
                            'UPDATE cves '
                            'SET cvss = ? '
                            'WHERE cve_id = ?',
                            [cve_sc, cve])
                        db.commit()
                    else:
                        cur.execute(
                            'INSERT INTO cves VALUES (?, ?)',
                            [cve, cve_sc])
                        db.commit()
                    cur.execute(
                        'INSERT INTO modules VALUES (?, ?)',
                        [mod, cve])
                    db.commit()


def get_cve(exploit):
    exp = exploit.split('/')
    cl = ms.get_msf_connection(ct.DEF_MSFRPC_PWD)
    mod = wz.Module(cl, exp[0], "/".join(exp[1:]))
    return mod.references()


def get_score(cve):
    try:
        req = requests.get(CVEDETAILS + cve)
    except requests.exceptions.ConnectionError:
        ut.log('error',
               'Connection to cvedetails: connection timed out. '
               'Check internet connection.',
               err=errno.ETIMEDOUT)
    soup = BeautifulSoup(req.text, features='html.parser')
    score = soup.find('div', attrs={'class': 'cvssbox'}).string
    return score


def parse_report(msf_log):
    mod = {}
    with open(msf_log) as f:
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


def generate_reports(outf, update_cache):
    info = parse_report(outf)
    db = set_up_cache()
    report = {'privrep': {}, 'pubrep': {}}
    try:
        date = info.pop('date')
        report['date'] = date
    except KeyError:
        ut.log('error', 'Wrong report format.', err=ct.EREP)
    nvuln = 0
    for mod in info:
        if is_cached(db, mod) and not update_cache:
            cve_sc = get_cached(db, mod)
        else:
            cve_sc = [(cve, get_score(cve)) for cve in get_cve(mod)]
            cache(db, mod, cve_sc, update_cache)
        nvuln += len(cve_sc)
        for elem in cve_sc:
            cve, cvss = elem
            affected_mach = [mach[0] for mach in info[mod] if mach[1]]
            report['privrep'][cve] = {
                'cvss': cvss,
                'metasploit_id': mod,
                'affected': affected_mach}
            report['pubrep'][cve] = {'cvss': cvss,
                                     'affected': len(affected_mach)}
    report['nvuln'] = nvuln
    return report


def store_report(info, outf, outbc, update_cache=False, loop=None):
    if loop is None:
        loop = _asyncio.get_event_loop()
    user, client, peer, channel = info

    ut.log('info', ct.GENREP, end='\r')
    reports = generate_reports(outf, update_cache)
    ut.log('succ', ct.GENREPDONE)

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
        _type = 'private'
        tmp_rep = rep.copy()
        tmp_rep['report'] = reports[r]  # dump report to log file
        if r == 'pubrep':
            _type = 'public'
            tmp_rep['private'] = False
            tmp_rep['date'] = pubdate
        log_rep[_type] = tmp_rep.copy()
        tmp_rep['report'] = json.dumps(reports[r])  # must be serialized
        trans_map = json.dumps(tmp_rep).encode()

        ut.log('info', f"Storing {_type} report: {rhash}")
        try:
            resp = loop.run_until_complete(client.chaincode_invoke(
                requestor=user,
                channel_name=channel,
                peers=[peer],
                fcn=CC_FUN,
                args=None,
                cc_name=CC,
                transient_map={CC_TRANS: trans_map}
            ))
        except Exception as e:
            ut.log(
                'error',
                f"Error storing {_type} report {rhash}: {e}",
                err=errno.ECONNREFUSED)
        else:
            if not resp:
                ut.log(
                    'succ',
                    f"{_type.capitalize()} report stored successfully.")
                uploaded += 1
            elif 'already' in resp:
                ut.log(
                    'warn',
                    f"{_type.capitalize()} report already in blockchain.")
            elif 'failed' in resp:
                ut.log('error',
                       f"Error storing {_type} report {rhash}: {resp}",
                       err=ct.EHLFST)
            else:
                ut.log('error',
                       "Unknown error storing {_type} report {rhash}: {resp}",
                       err=ct.EHLFST)
    ut.log('info', f"Blockchain output log: {outbc}")
    with open(outbc, 'w') as out:
        out.write(json.dumps(log_rep, indent=4))
    if uploaded == 2:
        if ut.check_existf(f'{outbc}.ots'):
            ut.log('warn', "Timestamp can not be created, already exists.")
        else:
            opentimestamp_format()
            ut.log('info', "Creating report timestamp...")
            args = otsclient.args.parse_ots_args(['stamp', outbc])
            args.cmd_func(args)


def _get_network_data(config, *key_path):
    if config:
        for k in key_path:
            try:
                config = config[k]
            except KeyError:
                ut.log('error',
                       "No key path {key_path} exists in network info",
                       err=ct.ECFGNET)
        return config


def _read_network(config):
    with open(config) as f:
        try:
            network = json.load(f)
        except json.JSONDecodeError:
            ut.log('error',
                   (f"Bad network format: {config}. "
                    f"Check {ct.NET_TEMPLATE}."),
                   err=ct.ECFGNET)
    return network


def load_config(config, loop=None):
    if loop is None:
        loop = _asyncio.get_event_loop()
    _loggcl = logging.getLogger('hfc.fabric.client')
    _loggcl.setLevel(logging.WARN)
    _loggdisc = logging.getLogger('hfc.fabric.channel.channel')
    _loggdisc.setLevel(logging.WARN)
    client_discovery = Client()
    network = _read_network(config)
    peer_config = _get_network_data(network, 'network', 'organization', 'peer')
    tls_cacerts = peer_config['tls_cacerts']
    opts = (('grpc.ssl_target_name_override', peer_config['server_hostname']),)
    endpoint = peer_config['grpc_request_endpoint']
    ut.check_readf(tls_cacerts)
    peer = create_peer(endpoint=endpoint,
                       tls_cacerts=tls_cacerts,
                       opts=opts)
    channel = _get_network_data(network, 'network', 'channel')
    wpath = _get_network_data(network, 'client', 'wallet', 'path')
    user_id = _get_network_data(network, 'client', 'id')
    org = _get_network_data(network, 'network', 'organization', 'name')
    msp_id = _get_network_data(network, 'network', 'organization', 'mspid')
    wal = wallet.FileSystenWallet(wpath)
    if wal.exists(user_id):
        user = wal.create_user(user_id, org, msp_id)
    else:
        _c = _get_network_data(network, 'client', 'credentials', 'cert')
        _k = _get_network_data(network, 'client', 'credentials', 'private_key')
        ut.check_readf(_c)
        ut.check_readf(_k)
        with open(_c, 'rb') as f:
            crt = f.read()
        with open(_k, 'rb') as f:
            pk = load_pem_private_key(f.read(), password=None,
                                      backend=default_backend())
        enroll = Enrollment(private_key=pk, enrollmentCert=crt)
        uidentity = wallet.Identity(user_id, enroll)
        uidentity.CreateIdentity(wal)
        user = wal.create_user(user_id, org, msp_id)
    loop.run_until_complete(
        client_discovery.init_with_discovery(user, peer, channel))
    return user, client_discovery, peer, channel


def opentimestamp_format():
    class OpenTimeStampFormatter(logging.Formatter):
        err_fmt = f"{ut.COLORS['R']}[!]{ut.COLORS['N']} %(msg)s"
        warn_fmt = f"{ut.COLORS['Y']}[-]{ut.COLORS['N']} %(msg)s"
        dbg_fmt = f"{ut.COLORS['B']}[*]{ut.COLORS['N']} %(msg)s"
        info_fmt = f"{ut.COLORS['G']}[+]{ut.COLORS['N']} %(msg)s"

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
            ut.WINDOW.emit(msg)
    ots = OpenTimeStampFormatter()
    if ut.WINDOW is not None:
        ots_handler = OpenTimeStampGUIHandler()
    else:
        ots_handler = logging.StreamHandler(sys.stdout)
    ots_handler.setFormatter(ots)
    logging.root.addHandler(ots_handler)
    logging.root.setLevel(logging.INFO)
