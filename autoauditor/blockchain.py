#!/usr/bin/env python3
from hfc.fabric import Client
from hfc.fabric_network import wallet
from hfc.fabric_ca.caservice import Enrollment
from hfc.fabric.peer import create_peer
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from bs4 import BeautifulSoup
import argparse
import requests
import re
import os
import utils
import hashlib
import subprocess
import json
import base64
import sys
import asyncio
import logging


RAPID7 = "https://www.rapid7.com/db/modules/"
CVEDETAILS = "https://www.cvedetails.com/cve/"

CHAINCODENAME = "autoauditor"
NEWREPORTFUNC = "NewReport"
NEWREPKEYWORD = "report"

cveregex = re.compile(r'^CVE-\d+-\d+')
modregex = re.compile(r'^#{5} (?P<modname>[a-zA-Z/_]+) #{5}$')
modendregex = re.compile(r'^#{10,}$')
rprtdateregex = re.compile(r'^#{14}\s(?P<date>[\d:\-\s\+\.]+)\s#{14}$')
rhostregex = re.compile(r'^RHOSTS?\s+=>\s+(?P<ip>[\d\.]+)$')
affected1 = re.compile(r'^\[\+\].*$')
affected2 = re.compile(r'session\s\d+\sopened')
affected3 = re.compile(r'uid=\d+\([a-z_][a-z0-9_-]*\)\s+gid=\d+\([a-z_][a-z0-9_-]*\)\s+groups=\d+\([a-z_][a-z0-9_-]*\)(?:,\d+\([a-z_][a-z0-9_-]*\))*')

loop = asyncio.get_event_loop()

def get_cve(exploit):
    try:
        req = requests.get(RAPID7 + exploit)
    except requests.exceptions.ConnectionError:
        utils.log('error', 'Connection error. Check internet connection.', errcode=utils.ECONN)

    soup = BeautifulSoup(req.text, features='html.parser')
    references = soup.find('section', attrs={'class': 'vulndb__references'}).find_all('a')
    cve_vuln = [ref.string for ref in references if cveregex.match(ref.string) is not None]
    return cve_vuln

def get_score(cve):
    try:
        req = requests.get(CVEDETAILS + cve)
    except requests.exceptions.ConnectionError:
        utils.log('error', 'Connection error. Check internet connection.', errcode=utils.ECONN)

    soup = BeautifulSoup(req.text, features='html.parser')
    score = soup.find('div', attrs={'class': 'cvssbox'}).string
    return score

def parse_report(rep_file):
    mod = {}
    mach = {}
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
               affected3.search(line) is not None:
                affected = True

            endrm = modendregex.match(line)
            if endrm is not None and modname is not None:
                mod[modname].append((host, affected))
                modname = None
                host = None
                affected = False
    return mod

def generate_reports(rep):
    info = parse_report(rep)
    report = {}
    report['privrep'] = {}
    report['pubrep'] = {}

    try:
        date = info.pop('date')
        report['date'] = date
    except KeyError:
        utils.log('error', 'Wrong report format.', errcode=utils.EBADREPFMT)

    nvuln = 0
    for mod in info:
        cve_sc = [(cve, get_score(cve)) for cve in get_cve(mod)]
        nvuln += len(cve_sc)
        for elem in cve_sc:
            cve, score = elem
            affected_mach = [mach[0] for mach in info[mod] if mach[1]]  # (1.1.1.1, True)
            report['privrep'][cve] = {'Score': score, 'MSFmodule': mod, 'AffectedMachines': affected_mach}
            report['pubrep'][cve] = {'Score': score, 'AffectedMachines': len(affected_mach)}

    report['nvuln'] = nvuln

    return report

def store_report(info, rep_file, out_file):
    user, client, peer, channel_name = info

    utils.log('succb', utils.GENREP, end='\r')
    report = generate_reports(rep_file)
    utils.log('succg', utils.GENREPDONE)

    privdate = report.pop('date')  # yyyy-mm-dd hh:mm:ss.ffffff+tt:zz
    pubdate = privdate[:7]  # yyyy-mm

    nvuln = report.pop('nvuln')

    repid = user.org + privdate
    rephash = hashlib.sha256(repid.encode('utf-8')).hexdigest()

    aarep = {"id": rephash,
             "org": user.org,
             "date": privdate,
             "nvuln": nvuln}

    out = open(out_file, 'w')
    utils.log('succb', "Blockchain output log: {}".format(out_file))

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

        utils.log('succb', "Storing {} report: {}".format("private" if aarep['private'] else "public", rephash))

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
            utils.log('error', "Error storing report {}: {}".format(rephash, str(e)))
        else:
            if not response:
                utils.log('succg', "Report stored successfully in blockchain.")
            elif 'already' in response:
                utils.log('warn', "Report already stored in blockchain.")
            elif 'failed' in response:
                utils.log('error', "Error storing report {}: {}".format(rephash, response))
            else:
                utils.log('error', "Unknown error storing report {}: {}".format(rephash, response))
    out.close()

def get_net_info(config, *key_path):
    if config:
        for k in key_path:
            try:
                config = config[k]
            except KeyError:
                utils.log('error', "No key path {key_path} exists in network info", errcode=utils.EBADNETFMT)
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
        with open(get_net_info(network, 'client', 'credentials', 'cert'), 'rb') as f:
            crt = f.read()
        with open(get_net_info(network, 'client', 'credentials', 'private_key'), 'rb') as f:
            pk = load_pem_private_key(f.read(), password=None, backend=default_backend())

        enroll = Enrollment(private_key=pk, enrollmentCert=crt)

        uidentity = wallet.Identity(userId, enroll)
        uidentity.CreateIdentity(wal)

        user = wal.create_user(userId, org, mspId)

    loop.run_until_complete(
        client_discovery.init_with_discovery(user, peer,
                                             channel_name))

    return (user, client_discovery, peer, channel_name)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Autoauditor submodule to store reports in blockchain.")

    parser.add_argument('-f', '--reportfile', metavar='report_file', required=True,
                        help="Report file.")

    parser.add_argument('-b', '--blockchainlog', metavar='blockchain_log_file',
                        default='output/blockchain.log',
                        help="Blockchain report log file.")

    parser.add_argument('-c', '--netconfigfile', metavar='network_cfg_file', required=True,
                        help="Network configuration file.")

    args = parser.parse_args()
    assert os.path.isfile(args.reportfile), "File {} does not exist.".format(args.reportfile)
    assert os.path.isfile(args.netconfigfile), "File {} does not exist.".format(args.netconfigfile)

    info = load_config(args.netconfigfile)

    utils.check_file_dir(args.blockchainlog)

    store_report(info, args.reportfile, args.blockchainlog)
