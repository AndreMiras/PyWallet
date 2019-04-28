#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
import shutil
from os.path import expanduser
from enum import Enum

import requests
import rlp
from devp2p.app import BaseApp
from eth_utils import to_checksum_address
from ethereum.tools.keys import PBKDF2_CONSTANTS
from ethereum.transactions import Transaction
from ethereum.utils import denoms, normalize_address
# from pyethapp.accounts import Account, AccountsService
from web3 import HTTPProvider, Web3
from pyethapp_accounts import Account
from eth_account import Account as EthAccount
from ethereum_utils import AccountUtils

ETHERSCAN_API_KEY = None
ROUND_DIGITS = 3
KEYSTORE_DIR_PREFIX = expanduser("~")
# default pyethapp keystore path
KEYSTORE_DIR_SUFFIX = ".config/pyethapp/keystore/"


class UnknownEtherscanException(Exception):
    pass


class InsufficientFundsException(UnknownEtherscanException):
    pass


class NoTransactionFoundException(UnknownEtherscanException):
    pass


class ChainID(Enum):
    MAINNET = 1
    MORDEN = 2
    ROPSTEN = 3


class PyWalib(object):

    def __init__(self, keystore_dir=None):
        if keystore_dir is None:
            keystore_dir = PyWalib.get_default_keystore_path()
        self.account_utils = AccountUtils(keystore_dir=keystore_dir)
        self.chain_id = ChainID.MAINNET
        self.provider = HTTPProvider('https://mainnet.infura.io')
        self.web3 = Web3(self.provider)
        # TODO: not needed anymore
        self.app = BaseApp(
            config=dict(accounts=dict(keystore_dir=keystore_dir)))
        # AccountsService.register_with_app(self.app)

    @staticmethod
    def handle_etherscan_error(response_json):
        """
        Raises an exception on unexpected response.
        """
        status = response_json["status"]
        message = response_json["message"]
        if status != "1":
            if message == "No transactions found":
                raise NoTransactionFoundException()
            else:
                raise UnknownEtherscanException(response_json)
        assert message == "OK"

    @staticmethod
    def address_hex(address):
        """
        Normalizes address.
        """
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
        # TODO: handle 504 timeout, 403 and other errors from etherscan
        response = requests.get(url)
        response_json = response.json()
        PyWalib.handle_etherscan_error(response_json)
        balance_wei = int(response_json["result"])
        balance_eth = balance_wei / float(pow(10, 18))
        balance_eth = round(balance_eth, ROUND_DIGITS)
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
        # TODO: handle 504 timeout, 403 and other errors from etherscan
        response = requests.get(url)
        response_json = response.json()
        PyWalib.handle_etherscan_error(response_json)
        transactions = response_json['result']
        for transaction in transactions:
            value_wei = int(transaction['value'])
            value_eth = value_wei / float(pow(10, 18))
            value_eth = round(value_eth, ROUND_DIGITS)
            from_address = PyWalib.address_hex(transaction['from'])
            to_address = transaction['to']
            # on contract creation, "to" is replaced by the "contractAddress"
            if not to_address:
                to_address = transaction['contractAddress']
            to_address = PyWalib.address_hex(to_address)
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
        transactions.sort(key=lambda x: x['timeStamp'])
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

    # TODO: can be removed since the migration to web3
    @staticmethod
    def get_nonce(address):
        """
        Gets the nonce by counting the list of outbound transactions from
        Etherscan.
        """
        try:
            out_transactions = PyWalib.get_out_transaction_history(address)
        except NoTransactionFoundException:
            out_transactions = []
        nonce = len(out_transactions)
        return nonce

    # TODO: is this still used after web3 migration?
    @staticmethod
    def handle_etherscan_tx_error(response_json):
        """
        Raises an exception on unexpected response.
        """
        error = response_json.get("error")
        if error is not None:
            code = error.get("code")
            if code in [-32000, -32010]:
                raise InsufficientFundsException()
            else:
                raise UnknownEtherscanException(response_json)

    # TODO: is this still used after web3 migration?
    @staticmethod
    def handle_web3_exception(exception):
        """
        TODO
        """
        error = exception.args[0]
        if error is not None:
            code = error.get("code")
            if code in [-32000, -32010]:
                raise InsufficientFundsException()
            else:
                raise UnknownEtherscanException(response_json)

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
        # TODO: handle 504 timeout, 403 and other errors from etherscan
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

    def transact(self, to, value=0, data='', sender=None, gas=25000,
                 gasprice=60 * denoms.shannon):
        """
        Signs and broadcasts a transaction.
        Returns transaction hash.
        """
        """
        # TODO:
        # sender -> wallet_path
        wallet_path = wallet_info[sender]['path']
        # wallet_info[sender]['password']
        wallet_path = 'TODO'
        wallet_encrypted = load_keyfile(wallet_path)
        address = wallet_encrypted['address']
        """
        sender = sender or web3.eth.coinbase
        address = sender
        from_address_normalized = to_checksum_address(address)
        nonce = self.web3.eth.getTransactionCount(from_address_normalized)
        transaction = {
            'chainId': self.chain_id.value,
            'gas': gas,
            'gasPrice': gasprice,
            'nonce': nonce,
            'value': value,
        }
        # TODO
        # private_key = EthAccount.decrypt(wallet_encrypted, wallet_password)
        account = self.account_utils.get_by_address(address)
        private_key = account.privkey
        signed_tx = self.web3.eth.account.signTransaction(
            transaction, private_key)
        try:
            tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        except ValueError as e:
            self.handle_web3_exception(e)
        """
        sender = sender or web3.eth.coinbase
        transaction = {
            'to': to,
            'value': value,
            'data': data,
            'from': sender,
            'gas': gas,
            'gasPrice': gasprice,
        }
        tx_hash = web3.eth.sendTransaction(transaction)
        """
        return tx_hash


    def transact_old(self, to, value=0, data='', sender=None, gas=25000,
                 gasprice=60 * denoms.shannon):
        """
        Inspired from pyethapp/console_service.py except that we use
        Etherscan for retrieving the nonce as we as for broadcasting the
        transaction.
        Arg value is in Wei.
        """
        # account.unlock(password)
        sender = normalize_address(sender or self.get_main_account().address)
        to = normalize_address(to, allow_blank=True)
        nonce = PyWalib.get_nonce(sender)
        # creates the transaction
        tx = Transaction(nonce, gasprice, gas, to, value, data)


        signed_tx = self.web3.eth.account.signTransaction(
            transaction, private_key)
        tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return tx_hash

        # TODO: migration to web3
        # then signs it
        self.app.services.accounts.sign_tx(sender, tx)
        # TODO: not needed anymore after web3
        assert tx.sender == sender
        PyWalib.add_transaction(tx)
        return tx

    # TODO: AccountUtils.new_account()
    # TODO: update security_ratio param
    @staticmethod
    def new_account_helper(password, security_ratio=None):
        """
        Helper method for creating an account in memory.
        Returns the created account.
        security_ratio is a ratio of the default PBKDF2 iterations.
        Ranging from 1 to 100 means 100% of the iterations.
        """
        account = self.account_utils.new_account(password=password)
        return account

    @staticmethod
    def new_account_helper_old(password, security_ratio=None):
        """
        Helper method for creating an account in memory.
        Returns the created account.
        security_ratio is a ratio of the default PBKDF2 iterations.
        Ranging from 1 to 100 means 100% of the iterations.
        """
        # TODO: perform validation on security_ratio (within allowed range)
        if security_ratio:
            default_iterations = PBKDF2_CONSTANTS["c"]
            new_iterations = int((default_iterations * security_ratio) / 100)
            PBKDF2_CONSTANTS["c"] = new_iterations
        uuid = None
        account = Account.new(password, uuid=uuid)
        # reverts to previous iterations
        if security_ratio:
            PBKDF2_CONSTANTS["c"] = default_iterations
        return account

    @staticmethod
    def deleted_account_dir(keystore_dir):
        """
        Given a `keystore_dir`, returns the corresponding
        `deleted_keystore_dir`.
        >>> keystore_dir = '/tmp/keystore'
        >>> PyWalib.deleted_account_dir(keystore_dir)
        u'/tmp/keystore-deleted'
        >>> keystore_dir = '/tmp/keystore/'
        >>> PyWalib.deleted_account_dir(keystore_dir)
        u'/tmp/keystore-deleted'
        """
        keystore_dir = keystore_dir.rstrip('/')
        keystore_dir_name = os.path.basename(keystore_dir)
        deleted_keystore_dir_name = "%s-deleted" % (keystore_dir_name)
        deleted_keystore_dir = os.path.join(
            os.path.dirname(keystore_dir),
            deleted_keystore_dir_name)
        return deleted_keystore_dir

    # TODO: update docstring
    # TODO: update security_ratio
    def new_account(self, password, security_ratio=None):
        """
        Creates an account on the disk and returns it.
        security_ratio is a ratio of the default PBKDF2 iterations.
        Ranging from 1 to 100 means 100% of the iterations.
        """
        account = self.account_utils.new_account(password=password)
        return account

    def new_account_old(self, password, security_ratio=None):
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

    def delete_account(self, account):
        """
        Deletes the given `account` from the `keystore_dir` directory.
        Then deletes it from the `AccountsService` account manager instance.
        In fact, moves it to another location; another directory at the same
        level.
        """
        app = self.app
        keystore_dir = app.services.accounts.keystore_dir
        deleted_keystore_dir = PyWalib.deleted_account_dir(keystore_dir)
        # create the deleted account dir if required
        if not os.path.exists(deleted_keystore_dir):
            os.makedirs(deleted_keystore_dir)
        # "removes" it from the file system
        account_filename = os.path.basename(account.path)
        deleted_account_path = os.path.join(
            deleted_keystore_dir, account_filename)
        shutil.move(account.path, deleted_account_path)
        # deletes it from the `AccountsService` account manager instance
        account_service = self.get_account_list()
        account_service.accounts.remove(account)

    def update_account_password(
            self, account, new_password, current_password=None):
        """
        The current_password is optional if the account is already unlocked.
        """
        self.account_utils.update_account_password(
            account, new_password, current_password)

    def update_account_password_old(
            self, account, new_password, current_password=None):
        """
        The current_password is optional if the account is already unlocked.
        """
        if current_password is not None:
            account.unlock(current_password)
        # make sure the PBKDF2 param stays the same
        default_iterations = PBKDF2_CONSTANTS["c"]
        account_iterations = account.keystore["crypto"]["kdfparams"]["c"]
        PBKDF2_CONSTANTS["c"] = account_iterations
        self.app.services.accounts.update_account(account, new_password)
        # reverts to previous iterations
        PBKDF2_CONSTANTS["c"] = default_iterations

    @staticmethod
    def get_default_keystore_path():
        """
        Returns the keystore path, which is the same as the default pyethapp
        one.
        """
        keystore_dir = os.path.join(KEYSTORE_DIR_PREFIX, KEYSTORE_DIR_SUFFIX)
        return keystore_dir

    def get_account_list(self):
        """
        Returns the Account list.
        """
        accounts = self.account_utils.get_account_list()
        return accounts

    def get_main_account(self):
        """
        Returns the main Account.
        """
        account = self.get_account_list()[0]
        return account
