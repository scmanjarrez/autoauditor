#!/usr/bin/env python3

# query - Blockchain Query module.

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

from blockchain import load_config
import constants as const
import argparse
import utils
import os
import asyncio
import json


CHAINCODENAME = "autoauditor"

loop = asyncio.get_event_loop()


def query(qinfo, pretty, qtype, rid=None, org=None, date=None, db=None):
    user, client, peer, channel_name = qinfo

    if qtype == 'id':
        fcn = 'GetReportById'
        cli_args = [rid]
        if db:
            cli_args.append(db)
    elif qtype == 'org':
        fcn = 'GetReportsByOrganization'
        cli_args = [org]
        if db:
            cli_args.append(db)
    elif qtype == 'totalorg':
        fcn = 'GetTotalReportsByOrganization'
        cli_args = [org]
    elif qtype == 'orgids':
        fcn = 'GetReportsIdByOrganization'
        cli_args = [org]
    elif qtype == 'totaldate':
        fcn = 'GetTotalReportsByDate'
        cli_args = [date]
        if org:
            cli_args.append(org)
    elif qtype == 'dateids':
        fcn = 'GetReportsIdByDate'
        cli_args = [date]
        if org:
            cli_args.append(org)
    else:
        fcn = 'GetReportsByDate'
        cli_args = [date]
        if org:
            cli_args.append(org)
        if db:
            cli_args.append(db)

    try:
        response = loop.run_until_complete(client.chaincode_query(
            requestor=user,
            channel_name=channel_name,
            peers=[peer],
            fcn=fcn,
            args=cli_args,
            cc_name=CHAINCODENAME
        ))
    except Exception as e:
        utils.log('error', "Error querying report {}: {}".format(rid, str(e)))
    else:
        if not pretty:
            print(response)
        else:
            reports = json.loads(response)
            rep_list = []
            for r in reports:
                r['report'] = json.loads(r['report'])
                rep_list.append(r)
            print(json.dumps(rep_list, indent=4))


def verify_arguments(cli_args):
    if cli_args.query == 'id':
        if not cli_args.reportid:
            utils.log('error', "Missing argument: reportid (-i).",
                      errcode=const.EMISSINGARG)
    elif cli_args.query in ('org', 'totalorg', 'orgids'):
        if not cli_args.orgname:
            utils.log('error', "Missing argument: orgname (-o).",
                      errcode=const.EMISSINGARG)
    else:
        if not cli_args.date:
            utils.log('error', "Missing argument: date (-t).",
                      errcode=const.EMISSINGARG)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Autoauditor submodule to store reports in blockchain.")

    parser.add_argument('-q', '--query', required=True,
                        choices=['id',
                                 'org', 'totalorg', 'orgids',
                                 'date', 'totaldate', 'dateids'],
                        help=("Type of query. Choose between id, "
                              "org, totalorg, orgids, "
                              "date, totaldate, dateids."))

    parser.add_argument('-i', '--reportid', metavar='report_id',
                        help="Report ID filter.")

    parser.add_argument('-o', '--orgname', metavar='org_name',
                        help="Organization name filter.")

    parser.add_argument('-t', '--date', metavar='YYYY-MM',
                        help="Date filter. Use the format YYYY-MM.")

    parser.add_argument('-d', '--database', choices=['public', 'private'],
                        help=("Database filter. "
                              "Choose between public or private."))

    parser.add_argument('-p', '--pretty', action='store_true',
                        help="Prettify JSON output.")

    parser.add_argument('-hc', '--hyperledgercfg',
                        metavar='hyperledger_config_file', required=True,
                        help="Blockchain network configuration file.")

    args = parser.parse_args()
    verify_arguments(args)

    utils.copyright()

    if not os.path.isfile(args.hyperledgercfg):
        utils.log(
            'error',
            "File {} does not exist."
            .format(args.hyperledgercfg),
            errcode=const.ENOENT
        )

    info = load_config(args.hyperledgercfg)
    query(info, args.pretty, args.query, args.reportid,
          args.orgname, args.date, args.database)
