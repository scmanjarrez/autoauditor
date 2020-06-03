#!/usr/bin/env python3
from bs4 import BeautifulSoup
import argparse
import requests
import re
import os
import sys
import utils


RAPID7 = "https://www.rapid7.com/db/modules/"
CVEDETAILS = "https://www.cvedetails.com/cve/"

cveregex = re.compile(r'^CVE-\d+-\d+')
modregex = re.compile(r'^#{5} (?P<modname>[\w/_]+) #{5}$')
modendregex = re.compile(r'^#{10,}$')
rprtdateregex = re.compile(r'^#{14}\s(?P<date>[\d:\-\s\+\.]+)\s#{14}$')
rhostregex = re.compile(r'^RHOSTS?\s+=>\s+(?P<ip>[\d\.]+)$')
affected1 = re.compile(r'^\[\+\].*$')
affected2 = re.compile(r'session\s\d+\sopened')


def set_environment(fabric_cfg, root_cert, local_msp, msp_config, peer):
    os.environ["FABRIC_CFG_PATH"] = fabric_cfg
    os.environ["CORE_PEER_LOCALMSPID"] = local_msp
    os.environ["CORE_PEER_TLS_ROOTCERT_FILE"] = root_cert
    os.environ["CORE_PEER_MSPCONFIGPATH"] = msp_config
    os.environ["CORE_PEER_ADDRESS"] = peer

def get_cve(exploit):
    req = requests.get(RAPID7 + exploit)
    soup = BeautifulSoup(req.text, features='html.parser')
    references = soup.find('section', attrs={'class': 'vulndb__references'}).find_all('a')
    cve_vuln = [ref.string for ref in references if cveregex.match(ref.string) is not None]
    return cve_vuln

def get_score(cve):
    req = requests.get(CVEDETAILS + cve)
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

            if affected1.search(line) is not None or affected2.search(line) is not None:
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
    fullrep = {}
    simplerep = {}
    try:
        date = info.pop('date')
        fullrep['Date'] = date
    except KeyError:
        utils.log('error', 'Wrong report format.', errcode=utils.EBADREPFMT)

    for mod in info:
        cve_sc = [(cve, get_score(cve)) for cve in get_cve(mod)]
        for elem in cve_sc:
            cve, score = elem
            fullrep[cve] = {'Score': score, 'MSFmodule': mod, 'AffectedMachines': [mach[0] for mach in info[mod] if mach[1]]}
            simplerep[cve] = {'Score': score, 'AffectedMachines': len([mach[0] for mach in info[mod] if mach[1]])}
    return fullrep, simplerep


def store_report(rep_file):
    full, simple = generate_reports(rep_file)
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Autoauditor submodule to store reports in blockchain.")

    parser.add_argument('-f', '--reportfile', metavar='report_file', required=True,
                        help="Path to the report file.")

    # parser.add_argument('-c', '--fabriccfg', metavar='fabric_cfg_path', required=True,
    #                     help="Fabric configuration directory path, i.e. core.yaml, configtx.yaml, orderer.yaml")

    # parser.add_argument('-t', '--corepeertlsrootcrt', metavar='root_cert_file', required=True,
    #                     help="TLS root certification file path.")

    # parser.add_argument('-l', '--corepeerlocalmspid', metavar='local_msp_id', required=True,
    #                     help="Local MSP ID.")

    # parser.add_argument('-m', '--corepeermspconf', metavar='msp_config_path', required=True,
    #                     help="MSP configuration directory path.")

    # parser.add_argument('-a', '--corepeeraddress', metavar='peer_address', required=True,
    #                     help="Peer address.")

    args = parser.parse_args()
    assert os.path.isfile(args.reportfile), "File {} does not exist.".format(args.reportfile)

    # set_env(args.fabriccfg, args.corepeertlsrootcrt, args.corepeerlocalmspid, args.corepeermspconf, args.corepeeraddress)

    # print(generate_reports(args.reportfile))
