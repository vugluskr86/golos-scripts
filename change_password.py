#!/usr/bin/env python

import sys
import json
import argparse
import logging
import yaml

from pprint import pprint
from piston import Steem
from piston.account import Account
from pistonbase.account import PasswordKey, PublicKey
from pistonbase import operations

import functions

log = logging.getLogger('functions')

key_types = [
    'posting',
    'active',
    'owner',
    'memo'
]

def main():

    parser = argparse.ArgumentParser(
            description='This script is for changing account keys. By default, random password are geneeated.',
            epilog='Report bugs to: https://github.com/bitfag/golos-scripts/issues')
    parser.add_argument('-d', '--debug', action='store_true',
            help='enable debug output'),
    parser.add_argument('-c', '--config', default='./common.yml',
            help='specify custom path for config file')
    parser.add_argument('account',
            help='account name'),
    parser.add_argument('-p', '--password',
            help='manually specify a password'),
    args = parser.parse_args()

    # create logger
    if args.debug == True:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)

    # parse config
    with open(args.config, 'r') as ymlfile:
        conf = yaml.load(ymlfile)

    golos = Steem(node=conf['nodes_old'], nobroadcast=False, keys=conf['keys'])
    account_name = args.account
    account = Account(args.account, steem_instance=golos)

    # random password
    if args.password:
        password = args.password
    else:
        password = functions.generate_password()

    print('password: {}\n'.format(password))

    key = dict()
    for key_type in key_types:

        # PasswordKey object
        k = PasswordKey(account_name, password, role=key_type)

        privkey = k.get_private_key()
        print('{} private: {}'.format(key_type, str(privkey))) # we need explicit str() conversion!

        # pubkey with default prefix GPH
        pubkey = k.get_public_key()

        # pubkey with correct prefix
        key[key_type] = format(pubkey, golos.rpc.chain_params["prefix"])
        print('{} public: {}\n'.format(key_type, key[key_type]))



    # prepare for json format
    owner_key_authority = [[key['owner'], 1]]
    active_key_authority = [[key['active'], 1]]
    posting_key_authority = [[key['posting'], 1]]
    owner_accounts_authority = []
    active_accounts_authority = []
    posting_accounts_authority = []

    s = {
            'account': account_name,
            'memo_key': key['memo'],
            'owner': {'account_auths': owner_accounts_authority,
                   'key_auths': owner_key_authority,
                   'weight_threshold': 1},
            'active': {'account_auths': active_accounts_authority,
                    'key_auths': active_key_authority,
                    'weight_threshold': 1},
            'posting': {'account_auths': posting_accounts_authority,
                     'key_auths': posting_key_authority,
                     'weight_threshold': 1},
            'prefix': golos.rpc.chain_params["prefix"]
         }


    #pprint(s)
    op = operations.Account_update(**s)

    golos.finalizeOp(op, args.account, "owner")

if __name__ == '__main__':
    main()
