#!/usr/bin/env python3
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


RAPID7 = "https://www.rapid7.com/db/modules/"
CVEDETAILS = "https://www.cvedetails.com/cve/"

cveregex = re.compile(r'^CVE-\d+-\d+')
modregex = re.compile(r'^#{5} (?P<modname>[a-zA-Z/_]+) #{5}$')
modendregex = re.compile(r'^#{10,}$')
rprtdateregex = re.compile(r'^#{14}\s(?P<date>[\d:\-\s\+\.]+)\s#{14}$')
rhostregex = re.compile(r'^RHOSTS?\s+=>\s+(?P<ip>[\d\.]+)$')
affected1 = re.compile(r'^\[\+\].*$')
affected2 = re.compile(r'session\s\d+\sopened')
affected3 = re.compile(r'uid=\d+\([a-z_][a-z0-9_-]*\)\s+gid=\d+\([a-z_][a-z0-9_-]*\)\s+groups=\d+\([a-z_][a-z0-9_-]*\)(?:,\d+\([a-z_][a-z0-9_-]*\))*')


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

def parse_config(conf_file):
    with open(conf_file, 'r') as f:
        config = json.load(f)
        for var in config['envvars']:
            os.environ[var] = config['envvars'][var]
    return config['vars']

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

def store_report(rep_file, config_file):
    utils.log('succb', utils.GENREP, end='\r')
    report = generate_reports(rep_file)
    utils.log('succg', utils.GENREPDONE)
    # debug report
    # report = json.loads("{'privrep': {'CVE-2012-2122': {'Score': '5.1', 'MSFmodule': 'auxiliary/scanner/mysql/mysql_authbypass_hashdump', 'AffectedMachines': ['10.10.0.3']}, 'CVE-2014-0160': {'Score': '5.0', 'MSFmodule': 'auxiliary/scanner/ssl/openssl_heartbleed', 'AffectedMachines': ['10.10.0.4']}, 'CVE-2003-0190': {'Score': '5.0', 'MSFmodule': 'auxiliary/scanner/ssh/ssh_enumusers', 'AffectedMachines': ['10.10.0.5', '10.10.0.7']}, 'CVE-2006-5229': {'Score': '2.6', 'MSFmodule': 'auxiliary/scanner/ssh/ssh_enumusers', 'AffectedMachines': ['10.10.0.5', '10.10.0.7']}, 'CVE-2016-6210': {'Score': '4.3', 'MSFmodule': 'auxiliary/scanner/ssh/ssh_enumusers', 'AffectedMachines': ['10.10.0.5', '10.10.0.7']}, 'CVE-2018-15473': {'Score': '5.0', 'MSFmodule': 'auxiliary/scanner/ssh/ssh_enumusers', 'AffectedMachines': ['10.10.0.5', '10.10.0.7']}, 'CVE-2014-6271': {'Score': '10.0', 'MSFmodule': 'auxiliary/scanner/http/apache_mod_cgi_bash_env', 'AffectedMachines': ['10.10.0.6']}, 'CVE-2014-6278': {'Score': '10.0', 'MSFmodule': 'auxiliary/scanner/http/apache_mod_cgi_bash_env', 'AffectedMachines': ['10.10.0.6']}, 'CVE-2018-10933': {'Score': '6.4', 'MSFmodule': 'auxiliary/scanner/ssh/libssh_auth_bypass', 'AffectedMachines': ['10.10.0.7']}}, 'pubrep': {'CVE-2012-2122': {'Score': '5.1', 'AffectedMachines': 1}, 'CVE-2014-0160': {'Score': '5.0', 'AffectedMachines': 1}, 'CVE-2003-0190': {'Score': '5.0', 'AffectedMachines': 2}, 'CVE-2006-5229': {'Score': '2.6', 'AffectedMachines': 2}, 'CVE-2016-6210': {'Score': '4.3', 'AffectedMachines': 2}, 'CVE-2018-15473': {'Score': '5.0', 'AffectedMachines': 2}, 'CVE-2014-6271': {'Score': '10.0', 'AffectedMachines': 1}, 'CVE-2014-6278': {'Score': '10.0', 'AffectedMachines': 1}, 'CVE-2018-10933': {'Score': '6.4', 'AffectedMachines': 1}}, 'date': '2020-06-03 18:54:50.433043+02:00', 'nvuln': 9}".replace("\'", "\""))
    config = parse_config(config_file)

    privdate = report.pop('date')
    pubdate = privdate[:7]  # yyyy-mm

    nvuln = report.pop('nvuln')

    repid = config['orgName'] + privdate
    rephash = hashlib.sha256(repid.encode('utf-8')).hexdigest()

    for rep in report:
        if rep == 'privrep':
            tmprep = '{{"id": "{}", "org": "{}", "date": "{}", "nvuln": {}, "private": true, "report": "{}"}}'.format(rephash, config['orgName'], privdate, nvuln, report[rep])
        else:
            tmprep = '{{"id": "{}", "org": "{}", "date": "{}", "nvuln": {}, "report": "{}"}}'.format(rephash, config['orgName'], pubdate, nvuln, report[rep])

        utils.log('succb', "Storing report: {}".format(rephash))

        output = subprocess.run(['peer', 'chaincode', 'invoke', '-o', config['ordererIP'],
                                 '--ordererTLSHostnameOverride', config['ordererTLSHostnameOverride'],
                                 '--tls', '--cafile', config['ordererCACert'],
                                 '-C', config['channelName'], '-n', config['chaincodeName'],
                                 '-c', '{"Args":["new"]}',
                                 '--transient', '{{"aareport": "{}"}}'.format(base64.b64encode(tmprep.encode('utf-8')).decode('utf-8'))], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        stdout = output.stdout.decode('utf-8')
        if 'error' in stdout.lower():
            utils.log('error', stdout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Autoauditor submodule to store reports in blockchain.")

    parser.add_argument('-f', '--reportfile', metavar='report_file', required=True,
                        help="Report file path.")

    parser.add_argument('-c', '--configfile', metavar='config_file', required=True,
                        help="Network configuration file path.")

    args = parser.parse_args()
    assert os.path.isfile(args.reportfile), "File {} does not exist.".format(args.reportfile)
    assert os.path.isfile(args.configfile), "File {} does not exist.".format(args.configfile)

    store_report(args.reportfile, args.configfile)
