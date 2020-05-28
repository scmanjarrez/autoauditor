#!/usr/bin/env python3
from bs4 import BeautifulSoup
import argparse
import requests
import re
import os


RAPID7 = "https://www.rapid7.com/db/modules/"
CVEDETAILS = "https://www.cvedetails.com/cve/"

cveregex = re.compile(r'^CVE-\d+-\d+')
modregex = re.compile(r'^#{5} (?P<modname>[\w/_]+) #{5}$')
modendregex = re.compile(r'^#{10,}$')
rprtdateregex = re.compile(r'^RPRTDATE\s+=>\s+(?P<date>[\d:\-\s\+\.]+)$')
rhostregex = re.compile(r'^RHOSTS?\s+=>\s+(?P<ip>[\d\.]+)$')


def get_cve(exploit):
    req = requests.get(RAPID7 + exploit)
    soup = BeautifulSoup(req.text, features='html.parser')
    references = soup.find('section', attrs={'class': 'vulndb__references'}).find_all('a')
    cve_vuln = [ref.string for ref in references if cveregex.match(ref.string) is not None]
    return cve_vuln

def get_score(exploit):
    req = requests.get(exploit_url)
    soup = BeautifulSoup(req.text, features='html.parser')
    score = soup.find('div', attrs={'class': 'cvssbox'}).string
    return score

def commit_to_blockchain():
    pass

def parse_report(rep_file):
    mod = {}
    with open(rep_file, 'r') as f:
        firstl = None
        while firstl != '':
            firstl = f.readline()
            mrm = modregex.match(firstl)
            if mrm is None:
                continue
            mname = mrm.group('modname').strip()
            if mname not in mod:
                mod[mname] = []
            line = ""
            date = None
            host = None
            while modendregex.match(line) is None:
                execut = []
                line = f.readline()
                nfo = []
                if date is not None and host is not None:
                    continue
                rrm = rprtdateregex.match(line)
                if rrm is not None:
                    date = rrm.group('date').strip()
                    nfo
                hrm = rhostregex.match(line)
                if hrm is not None:
                    host = hrm.group('ip').strip()
            mod[mname].append((date, host))
    return mod

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Tool to run metasploit automatically given a resource script.")

    parser.add_argument('-f', '--reportfile', metavar='report_file', required=True,
                        help="Commit report to blockchain.")

    # parser.add_argument('-n', '--networkfile', metavar='network_file', required=True,
    #                     help="Load blockchain network configuration.")

    args = parser.parse_args()
    assert os.path.isfile(args.reportfile), "{} does not exist.".format(args.reportfile)
    # assert os.path.isfile(args.reportfile), "{} does not exist.".format(args.reportfile)
    prprt = parse_report(args.reportfile)

        # exploit = "https://www.cvedetails.com/cve/CVE-2014-0160/"
    # print(get_score(exploit))
    # exploit = "auxiliary/scanner/ssh/ssh_enumusers"
    # print(get_cve(exploit))
    print(prprt)
