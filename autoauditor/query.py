#!/usr/bin/env python3
from blockchain import load_config
import argparse
import utils
import os
import asyncio
import json


CHAINCODENAME = "autoauditor"

loop = asyncio.get_event_loop()

def query(info, pretty, qtype, rid=None, org=None, date=None, db=None):
    user, client, peer, channel_name = info

    if qtype == 'id':
        fcn='GetReportById'
        args=[rid]
        if db: args.append(db)
    elif qtype == 'org':
        fcn='GetReportsByOrganization'
        args=[org]
        if db: args.append(db)
    else:
        fcn='GetReportsByDate'
        args=[date]
        if org: args.append(org)
        if db: args.append(db)

    try:
        response = loop.run_until_complete(client.chaincode_query(
            requestor=user,
            channel_name=channel_name,
            peers=[peer],
            fcn=fcn,
            args=args,
            cc_name=CHAINCODENAME
        ))
    except Exception as e:
        utils.log('error', "Error querying report {}: {}".format(rid, str(e)))
    else:
        if not pretty:
            print(response)
        else:
            print(json.dumps(json.loads(response), indent=4))

def verify_arguments(args):
    if args.query == 'id':
        if not args.reportid:
            utils.log('error', "Missing argument: reportid.", errcode=utils.EMISSINGARG)
    elif args.query == 'org':
        if not args.orgname:
            utils.log('error', "Missing argument: orgname.", errcode=utils.EMISSINGARG)
    else:
        if not args.date:
            utils.log('error', "Missing argument: date.", errcode=utils.EMISSINGARG)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Autoauditor submodule to store reports in blockchain.")

    parser.add_argument('-q', '--query', required=True,
                        choices=['id', 'org', 'date'],
                        help="Type of query. Choose between id, org, or date.")

    parser.add_argument('-i', '--reportid', metavar='report_id',
                        help="Report ID filter.")

    parser.add_argument('-o', '--orgname', metavar='org_name',
                        help="Organization name filter.")

    parser.add_argument('-t', '--date', metavar='YYYY-MM',
                        help="Date filter. Use the format YYYY-MM.")

    parser.add_argument('-d', '--database', choices=['public', 'private'],
                        help="Database filter. Choose between public or private.")

    parser.add_argument('-p', '--pretty', action='store_true',
                        help="Prettify JSON output.")

    parser.add_argument('-c', '--netconfigfile', metavar='network_cfg_file', required=True,
                        help="Network configuration file.")

    args = parser.parse_args()
    verify_arguments(args)

    assert os.path.isfile(args.netconfigfile), "File {} does not exist.".format(args.netconfigfile)

    info = load_config(args.netconfigfile)
    query(info, args.pretty, args.query, args.reportid, args.orgname, args.date, args.database)
