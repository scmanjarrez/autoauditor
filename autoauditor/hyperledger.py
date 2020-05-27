#!/usr/bin/env python3
import requests
from html.parser import HTMLParser
from bs4 import BeautifulSoup
import re


ENDPOINT = "https://www.rapid7.com/db/modules/"
CVEDETAILS = "https://www.cvedetails.com/cve/"


def get_cve(exploit):
    req = requests.get(ENDPOINT + exploit)
    soup = BeautifulSoup(req.text, features="html.parser")
    references = soup.find('section', attrs={'class': 'vulndb__references'}).find_all('a')
    cve_vuln = [(ref.string, CVEDETAILS + ref.string) for ref in references if re.match('^CVE-\d+-\d+', ref.string) is not None]
    # print(cve_vuln)
    return cve_vuln

def commit_to_blockchain():
    pass

def parse_report():
    pass


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(
    #     description="Tool to run metasploit automatically given a resource script.")

    # parser.add_argument('-f', '--reportfile', metavar='report_file', required=True,
    #                     help="Commit report to blockchain.")

    # parser.add_argument('-n', '--networkfile', metavar='network_file', required=True,
    #                     help="Load blockchain network configuration.")
    exploit = "auxiliary/scanner/ssh/ssh_enumusers"
    get_cve(exploit)
