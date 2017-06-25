#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
from os.path import expanduser

import requests
import rlp
from devp2p.app import BaseApp
from ethereum.tools.keys import PBKDF2_CONSTANTS
from ethereum.transactions import Transaction
from ethereum.utils import denoms, normalize_address
from pyethapp.accounts import Account, AccountsService

ETHERSCAN_API_KEY = None


class InsufficientFundsException(Exception):
    pass


class UnknownEtherscanException(Exception):
    pass


class PyWalib(object):

    def __init__(self, keystore_dir=None):
        if keystore_dir is None:
            keystore_dir = PyWalib.get_default_keystore_path()
        self.app = BaseApp(
            config=dict(accounts=dict(keystore_dir=keystore_dir)))
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
    def address_hex(address):
        prefix = "0x"
        address_hex = prefix + normalize_address(address).encode("hex")
        return address_hex

    @staticmethod
    def get_balance(address):
        """
        Retrieves the balance from etherscan.io.
        The balance is returned in ETH rounded to the second decimal.
        """
        address = PyWalib.address_hex(address)
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
    def get_transaction_history(address):
        """
        Retrieves the transaction history from etherscan.io.
        """
        address = PyWalib.address_hex(address)
        url = 'https://api.etherscan.io/api'
        url += '?module=account&action=txlist'
        url += '&sort=asc'
        url += '&address=%s' % address
        if ETHERSCAN_API_KEY:
            '&apikey=%' % ETHERSCAN_API_KEY
        response = requests.get(url)
        response_json = response.json()
        PyWalib.handle_etherscan_error(response_json)
        transactions = response_json['result']
        for transaction in transactions:
            value_wei = int(transaction['value'])
            value_eth = value_wei / float(pow(10, 18))
            from_address = PyWalib.address_hex(transaction['from'])
            to_address = PyWalib.address_hex(transaction['to'])
            sent = from_address == address
            received = not sent
            extra_dict = {
                'value_eth': value_eth,
                'sent': sent,
                'received': received,
                'from_address': from_address,
                'to_address': to_address,
            }
            transaction.update({'extra_dict': extra_dict})
        # sort by timeStamp
        transactions.sort(key=lambda x: x['timeStamp'], reverse=True)
        return transactions

    @staticmethod
    def get_out_transaction_history(address):
        """
        Retrieves the outbound transaction history from Etherscan.
        """
        transactions = PyWalib.get_transaction_history(address)
        out_transactions = []
        for transaction in transactions:
            if transaction['extra_dict']['sent']:
                out_transactions.append(transaction)
        return out_transactions

    @staticmethod
    def get_nonce(address):
        """
        Gets the nonce by counting the list of outbound transactions from
        Etherscan.
        """
        out_transactions = PyWalib.get_out_transaction_history(address)
        nonce = len(out_transactions)
        return nonce

    @staticmethod
    def handle_etherscan_tx_error(response_json):
        """
        Raises an exception on unexpected response.
        """
        error = response_json.get("error")
        if error is not None:
            code = error.get("code")
            if code == -32010:
                raise InsufficientFundsException()
            else:
                raise UnknownEtherscanException()

    @staticmethod
    def add_transaction(tx):
        """
        POST transaction to etherscan.io.
        """
        tx_hex = rlp.encode(tx).encode("hex")
        # use https://etherscan.io/pushTx to debug
        print("tx_hex:", tx_hex)
        url = 'https://api.etherscan.io/api'
        url += '?module=proxy&action=eth_sendRawTransaction'
        if ETHERSCAN_API_KEY:
            '&apikey=%' % ETHERSCAN_API_KEY
        response = requests.post(url, data={'hex': tx_hex})
        # response is like:
        # {'jsonrpc': '2.0', 'result': '0x24a8...14ea', 'id': 1}
        # or on error like this:
        # {'jsonrpc': '2.0', 'id': 1, 'error': {
        #   'message': 'Insufficient funds...', 'code': -32010, 'data': None}}
        response_json = response.json()
        print("response_json:", response_json)
        PyWalib.handle_etherscan_tx_error(response_json)
        tx_hash = response_json['result']
        # the response differs from the other responses
        return tx_hash

    def transact(self, to, value=0, data='', sender=None, startgas=25000,
                 gasprice=60 * denoms.shannon):
        """
        Inspired from pyethapp/console_service.py except that we use
        Etherscan for retrieving the nonce as we as for broadcasting the
        transaction.
        """
        # account.unlock(password)
        sender = normalize_address(sender or self.get_main_account().address)
        to = normalize_address(to, allow_blank=True)
        nonce = PyWalib.get_nonce(sender)
        # creates the transaction
        tx = Transaction(nonce, gasprice, startgas, to, value, data)
        # then signs it
        self.app.services.accounts.sign_tx(sender, tx)
        assert tx.sender == sender
        PyWalib.add_transaction(tx)
        return tx

    @staticmethod
    def new_account_helper(password, security_ratio=None):
        """
        Helper method for creating an account in memory.
        Returns the created account.
        security_ratio is a ratio of the default PBKDF2 iterations.
        Ranging from 1 to 100 means 100% of the iterations.
        """
        # TODO: perform validation on security_ratio (within allowed range)
        if security_ratio:
            previous_iterations = PBKDF2_CONSTANTS["c"]
            new_iterations = int((previous_iterations * security_ratio) / 100)
            PBKDF2_CONSTANTS["c"] = new_iterations
        uuid = None
        account = Account.new(password, uuid=uuid)
        # reverts to previous iterations
        if security_ratio:
            PBKDF2_CONSTANTS["c"] = previous_iterations
        return account

    def new_account(self, password, security_ratio=None):
        """
        Creates an account on the disk and returns it.
        security_ratio is a ratio of the default PBKDF2 iterations.
        Ranging from 1 to 100 means 100% of the iterations.
        """
        account = PyWalib.new_account_helper(password, security_ratio)
        app = self.app
        account.path = os.path.join(
            app.services.accounts.keystore_dir, account.address.encode('hex'))
        self.app.services.accounts.add_account(account)
        return account

    @staticmethod
    def get_default_keystore_path():
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
    print("balance: %s" % balance)


if __name__ == '__main__':
    main()
