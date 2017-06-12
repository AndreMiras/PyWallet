#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from os.path import expanduser
import requests
from pyethapp.accounts import AccountsService, Account
from devp2p.app import BaseApp
import os


ETHERSCAN_API_KEY = None


class PyWalib(object):

    def __init__(self):
        keystore_dir = PyWalib.get_keystore_path()
        self.app = BaseApp(config=dict(accounts=dict(keystore_dir=keystore_dir)))
        AccountsService.register_with_app(self.app)

    @staticmethod
    def handle_etherscan_error(response_json):
        """
        Raises an exception on unexpected response.
        """
        status = response_json["status"]
        message = response_json["message"]
        assert status == "1"
        assert message == "OK"


    @staticmethod
    def get_balance(address):
        """
        Retrieves the balance from etherscan.io.
        The balance is returned in ETH rounded to the second decimal.
        """
        url = 'https://api.etherscan.io/api'
        url += '?module=account&action=balance'
        url += '&address=%s' % address
        url += '&tag=latest'
        if ETHERSCAN_API_KEY:
            '&apikey=%' % ETHERSCAN_API_KEY
        response = requests.get(url)
        response_json = response.json()
        PyWalib.handle_etherscan_error(response_json)
        balance_wei = int(response_json["result"])
        balance_eth = balance_wei / float(pow(10, 18))
        balance_eth = round(balance_eth, 2)
        return balance_eth

    @staticmethod
    def create_and_sign_transaction(
            account, password, receiver_address, amount_eth):
        print "account.locked:", account.locked
        print("unlocking...")
        account.unlock(password)
        print("unlocked")
        print("sending...")
        transaction = None
        # TODO: convert from ETH to expected unit
        # transaction = eth.transact(receiver_address, sender=account, value=100)
        return transaction

    @staticmethod
    def new_account(password):
        uuid = None
        print("pyethapp Account.new")
        account = Account.new(password, uuid=uuid)
        print("Address: ", account.address.encode('hex'))


    @staticmethod
    def get_keystore_path():
        """
        Returns the keystore path.
        """
        home = expanduser("~")
        keystore_relative_dir = ".config/pyethapp/keystore/"
        keystore_dir = os.path.join(home, keystore_relative_dir)
        return keystore_dir

    def get_account_list(self):
        """
        Returns the Account list.
        """
        account = self.app.services.accounts
        return account

    def get_main_account(self):
        """
        Returns the main Account.
        """
        account = self.get_account_list()[0]
        return account


def main():
    pywalib = PyWalib()
    account = pywalib.get_main_account()
    balance = pywalib.get_balance(account.address.encode("hex"))
    print "balance:", balance


if __name__ == '__main__':
    main()
