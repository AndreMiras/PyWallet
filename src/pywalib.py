#!/usr/bin/env python
# -*- coding: utf-8 -*-
import http
import math
import os
from enum import Enum
from os.path import expanduser

import requests
from eth_keyfile import keyfile
from eth_utils import to_checksum_address
from web3 import HTTPProvider, Web3

from ethereum_utils import AccountUtils

ETHERSCAN_API_KEY = "R796P9T31MEA24P8FNDZBCA88UHW8YCNVW"
ROUND_DIGITS = 3
KEYSTORE_DIR_PREFIX = expanduser("~")
# default pyethapp keystore path
KEYSTORE_DIR_SUFFIX = ".config/pyethapp/keystore/"
DEFAULT_GAS_PRICE_GWEI = 4
REQUESTS_HEADERS = {
    "User-Agent": "https://github.com/AndreMiras/PyWallet",
}


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


class HTTPProviderFactory:

    PROVIDER_URLS = {
        # ChainID.MAINNET: 'https://api.myetherapi.com/eth',
        ChainID.MAINNET: 'https://mainnet.infura.io',
        # ChainID.ROPSTEN: 'https://api.myetherapi.com/rop',
        ChainID.ROPSTEN: 'https://ropsten.infura.io',
    }

    @classmethod
    def create(cls, chain_id=ChainID.MAINNET) -> HTTPProvider:
        url = cls.PROVIDER_URLS[chain_id]
        return HTTPProvider(url)


def get_etherscan_prefix(chain_id=ChainID.MAINNET) -> str:
    PREFIXES = {
        ChainID.MAINNET: 'https://api.etherscan.io/api',
        ChainID.ROPSTEN: 'https://api-ropsten.etherscan.io/api',
    }
    return PREFIXES[chain_id]


def handle_etherscan_response_json(response_json):
    """Raises an exception on unexpected response json."""
    status = response_json["status"]
    message = response_json["message"]
    if status != "1":
        if message == "No transactions found":
            raise NoTransactionFoundException()
        else:
            raise UnknownEtherscanException(response_json)
    assert message == "OK"


def handle_etherscan_response_status(status_code):
    """Raises an exception on unexpected response status."""
    if status_code != http.HTTPStatus.OK:
        raise UnknownEtherscanException(status_code)


def handle_etherscan_response(response):
    """Raises an exception on unexpected response."""
    handle_etherscan_response_status(response.status_code)
    handle_etherscan_response_json(response.json())


def requests_get(url):
    return requests.get(url, headers=REQUESTS_HEADERS)


class PyWalib:

    def __init__(self, keystore_dir=None, chain_id=ChainID.MAINNET):
        if keystore_dir is None:
            keystore_dir = PyWalib.get_default_keystore_path()
        self.keystore_dir = keystore_dir
        self.account_utils = AccountUtils(keystore_dir=self.keystore_dir)
        self.chain_id = chain_id
        self.provider = HTTPProviderFactory.create(self.chain_id)
        self.web3 = Web3(self.provider)

    @staticmethod
    def get_balance(address, chain_id=ChainID.MAINNET):
        """
        Retrieves the balance from etherscan.io.
        The balance is returned in ETH rounded to the second decimal.
        """
        address = to_checksum_address(address)
        url = get_etherscan_prefix(chain_id)
        url += (
            '?module=account&action=balance'
            '&tag=latest'
            f'&address={address}'
            f'&apikey={ETHERSCAN_API_KEY}'
        )
        response = requests_get(url)
        handle_etherscan_response(response)
        response_json = response.json()
        balance_wei = int(response_json["result"])
        balance_eth = balance_wei / float(pow(10, 18))
        balance_eth = round(balance_eth, ROUND_DIGITS)
        return balance_eth

    def get_balance_web3(self, address):
        """
        The balance is returned in ETH rounded to the second decimal.
        """
        address = to_checksum_address(address)
        balance_wei = self.web3.eth.getBalance(address)
        balance_eth = balance_wei / float(pow(10, 18))
        balance_eth = round(balance_eth, ROUND_DIGITS)
        return balance_eth

    @staticmethod
    def get_transaction_history(address, chain_id=ChainID.MAINNET):
        """
        Retrieves the transaction history from etherscan.io.
        """
        address = to_checksum_address(address)
        url = get_etherscan_prefix(chain_id)
        url += (
            '?module=account&action=txlist'
            '&sort=asc'
            f'&address={address}'
            f'&apikey={ETHERSCAN_API_KEY}'
        )
        response = requests_get(url)
        handle_etherscan_response(response)
        response_json = response.json()
        transactions = response_json['result']
        for transaction in transactions:
            value_wei = int(transaction['value'])
            value_eth = value_wei / float(pow(10, 18))
            value_eth = round(value_eth, ROUND_DIGITS)
            from_address = to_checksum_address(transaction['from'])
            to_address = transaction['to']
            # on contract creation, "to" is replaced by the "contractAddress"
            if not to_address:
                to_address = transaction['contractAddress']
            to_address = to_checksum_address(to_address)
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
    def get_out_transaction_history(address, chain_id=ChainID.MAINNET):
        """
        Retrieves the outbound transaction history from Etherscan.
        """
        transactions = PyWalib.get_transaction_history(address, chain_id)
        out_transactions = []
        for transaction in transactions:
            if transaction['extra_dict']['sent']:
                out_transactions.append(transaction)
        return out_transactions

    # TODO: can be removed since the migration to web3
    @staticmethod
    def get_nonce(address, chain_id=ChainID.MAINNET):
        """
        Gets the nonce by counting the list of outbound transactions from
        Etherscan.
        """
        try:
            out_transactions = PyWalib.get_out_transaction_history(
                address, chain_id)
        except NoTransactionFoundException:
            out_transactions = []
        nonce = len(out_transactions)
        return nonce

    @staticmethod
    def handle_web3_exception(exception: ValueError):
        """
        Raises the appropriated typed exception on web3 ValueError exception.
        """
        error = exception.args[0]
        code = error.get("code")
        if code in [-32000, -32010]:
            raise InsufficientFundsException(error)
        else:
            raise UnknownEtherscanException(error)

    def transact(self, to, value=0, data='', sender=None, gas=25000,
                 gasprice=DEFAULT_GAS_PRICE_GWEI * (10 ** 9)):
        """
        Signs and broadcasts a transaction.
        Returns transaction hash.
        """
        address = sender or self.get_main_account().address
        from_address_normalized = to_checksum_address(address)
        nonce = self.web3.eth.getTransactionCount(from_address_normalized)
        transaction = {
            'chainId': self.chain_id.value,
            'gas': gas,
            'gasPrice': gasprice,
            'nonce': nonce,
            'value': value,
        }
        account = self.account_utils.get_by_address(address)
        private_key = account.privkey
        signed_tx = self.web3.eth.account.signTransaction(
            transaction, private_key)
        try:
            tx_hash = self.web3.eth.sendRawTransaction(
                signed_tx.rawTransaction)
        except ValueError as e:
            self.handle_web3_exception(e)
        return tx_hash

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

    @staticmethod
    def _get_pbkdf2_iterations(security_ratio=None):
        """
        Returns the work-factor/iterations based on the security_ratio.
        """
        iterations = None
        min_security_ratio = 1
        max_security_ratio = 100
        if security_ratio is not None:
            if not min_security_ratio <= security_ratio <= max_security_ratio:
                raise ValueError(
                    f'security_ratio must be within {min_security_ratio} and '
                    f'{max_security_ratio}')
            kdf = 'pbkdf2'
            default_iterations = keyfile.get_default_work_factor_for_kdf(kdf)
            iterations = (default_iterations * security_ratio) / 100.0
            iterations = math.ceil(iterations)
        return iterations

    # TODO: update docstring
    def new_account(self, password, security_ratio=None):
        """
        Creates an account on the disk and returns it.
        security_ratio is a ratio of the default PBKDF2 iterations.
        Ranging from 1 to 100 means 100% of the iterations.
        """
        iterations = self._get_pbkdf2_iterations(security_ratio)
        account = self.account_utils.new_account(
            password=password, iterations=iterations)
        return account

    def delete_account(self, account):
        """
        Deletes the given `account` from the `keystore_dir` directory.
        In fact, moves it to another location; another directory at the same
        level.
        """
        self.account_utils.delete_account(account)

    def update_account_password(
            self, account, new_password, current_password=None):
        """
        The current_password is optional if the account is already unlocked.
        """
        self.account_utils.update_account_password(
            account, new_password, current_password)

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
