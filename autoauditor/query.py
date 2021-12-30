#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later

# query - Blockchain Query module.

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

from autoauditor import blockchain as bc
from autoauditor import utils as ut

import argparse
import asyncio
import json


loop = asyncio.get_event_loop()

QTYPE = {
    'query': 'GetReportById',
    'qorg': 'GetReportsByOrganization',
    'qtotalorg': 'GetTotalReportsByOrganization',
    'qidsorg': 'GetReportsIdByOrganization',
    'qdate': 'GetReportsByDate',
    'qtotaldate': 'GetTotalReportsByDate',
    'qidsdate': 'GetReportsIdByDate'
}
QSET = {
    'id': ['query'],
    'org': ['qorg', 'qtotalorg', 'qidsorg'],
    'date': ['qdate', 'qtotaldate', 'qidsdate']
}


def query(info, args):
    user, client, peer, channel = info

    cc_args = []
    cc_fcn = QTYPE[args.query]
    if args.query in QSET['org']:
        cc_args.append(args.qo)
    elif args.query in QSET['date']:
        cc_args.append(args.qd)
        if args.qo:
            cc_args.append(args.qo)
    else:
        cc_args.append(args.qi)

    if args.qb:
        cc_args.append(args.qb)

    try:
        response = loop.run_until_complete(client.chaincode_query(
            requestor=user,
            channel_name=channel,
            peers=[peer],
            fcn=cc_fcn,
            args=cc_args,
            cc_name=bc.CC
        ))
    except Exception as e:
        ut.log('error', f"Error querying report {cc_args}: {e}")
    else:
        if not args.pretty:
            print(response)
        else:
            reports = json.loads(response)
            rep_list = []
            for rep in reports:
                try:
                    rep['report'] = json.loads(rep['report'])
                except json.decoder.JSONDecodeError:
                    pass
                rep_list.append(rep)
            print(json.dumps(rep_list, indent=2))


def verify_arguments(parser, args):
    if args.query in QSET['org']:
        if not args.qo:
            parser.error("the following arguments are required: -qo")
    elif args.query in QSET['date']:
        if not args.qd:
            parser.error("the following arguments are required: -qd")
    else:
        if not args.qi:
            parser.error("the following arguments are required: -qi")


    ut.check_readf(args.b)


def main():
    parser = argparse.ArgumentParser(
        description="Autoauditor submodule to query reports in blockchain.")
    cmds = parser.add_argument_group("commands")
    cmds.add_argument('-q', '--query', required=True,
                      choices=QTYPE.keys(),
                      help=(f"Type of query. "
                            f"Values: {', '.join(QTYPE.keys())}"))
    cmd_opt = parser.add_argument_group("command options")
    cmd_opt.add_argument('-b', required=True,
                         metavar='bc_cfg',
                         help="Blockchain network configuration.")
    cmd_opt.add_argument('-qi',
                         metavar='report_id',
                         help="Report ID filter.")
    cmd_opt.add_argument('-qo',
                         metavar='org_name',
                         help="Organization name filter.")
    cmd_opt.add_argument('-qd',
                         metavar='YYYY-MM',
                         help="Date filter. Use the format YYYY-MM.")
    cmd_opt.add_argument('-qb',
                         choices=['public', 'private'],
                         help=("Database filter. "
                               "Choose between public or private."))
    misc_opt = parser.add_argument_group("misc options")
    misc_opt.add_argument('--pretty',
                          action='store_true',
                          help="Prettify JSON output.")
    misc_opt.add_argument('--no-color',
                          action='store_true',
                          help="Disable colored output.")
    args = parser.parse_args()
    verify_arguments(parser, args)

    if args.no_color:
        ut.disable_ansi_colors()

    ut.copyright()

    info = bc.load_config(args.b)
    query(info, args)


if __name__ == '__main__':
    main()
