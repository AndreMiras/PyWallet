import os
import shutil
import unittest
from tempfile import mkdtemp
from unittest import mock

from pywalib import (InsufficientFundsException, NoTransactionFoundException,
                     PyWalib, UnknownEtherscanException)

ADDRESS = "0xab5801a7d398351b8be11c439e05c5b3259aec9b"
VOID_ADDRESS = "0x0000000000000000000000000000000000000000"
PASSWORD = "password"


class PywalibTestCase(unittest.TestCase):
    """
    Simple test cases, verifying pywalib works as expected.
    """

    def setUp(self):
        self.keystore_dir = mkdtemp()
        self.pywalib = PyWalib(self.keystore_dir)

    def tearDown(self):
        shutil.rmtree(self.keystore_dir, ignore_errors=True)

    def helper_new_account(self, password=PASSWORD, security_ratio=1):
        """
        Helper method for fast account creation.
        """
        account = self.pywalib.new_account(password, security_ratio)
        return account

    def test_new_account(self):
        """
        Simple account creation test case.
        1) verifies the current account list is empty
        2) creates a new account and verify we can retrieve it
        3) tries to unlock the account
        """
        pywalib = self.pywalib
        # 1) verifies the current account list is empty
        account_list = pywalib.get_account_list()
        self.assertEqual(len(account_list), 0)
        # 2) creates a new account and verify we can retrieve it
        password = PASSWORD
        # weak account, but fast creation
        security_ratio = 1
        account = pywalib.new_account(password, security_ratio)
        account_list = pywalib.get_account_list()
        self.assertEqual(len(account_list), 1)
        self.assertEqual(account, pywalib.get_main_account())
        # 3) tries to unlock the account
        # it's unlocked by default after creation
        self.assertFalse(account.locked)
        # let's lock it and unlock it back
        account.lock()
        self.assertTrue(account.locked)
        account.unlock(password)
        self.assertFalse(account.locked)

    def test_update_account_password(self):
        """
        Verifies updating account password works.
        """
        pywalib = self.pywalib
        current_password = "password"
        # weak account, but fast creation
        security_ratio = 1
        account = pywalib.new_account(current_password, security_ratio)
        # first try when the account is already unlocked
        self.assertFalse(account.locked)
        new_password = "new_password"
        # on unlocked account the current_password is optional
        pywalib.update_account_password(
            account, new_password, current_password=None)
        # verify it worked
        account.lock()
        account.unlock(new_password)
        self.assertFalse(account.locked)
        # now try when the account is first locked
        account.lock()
        current_password = "wrong password"
        with self.assertRaises(ValueError):
            pywalib.update_account_password(
                account, new_password, current_password)
        current_password = new_password
        pywalib.update_account_password(
            account, new_password, current_password)
        self.assertFalse(account.locked)

    def test_deleted_account_dir(self):
        """
        The deleted_account_dir() helper method should be working
        with and without trailing slash.
        """
        expected_deleted_keystore_dir = '/tmp/keystore-deleted'
        keystore_dirs = [
            # without trailing slash
            '/tmp/keystore',
            # with one trailing slash
            '/tmp/keystore/',
            # with two trailing slashes
            '/tmp/keystore//',
        ]
        for keystore_dir in keystore_dirs:
            self.assertEqual(
                PyWalib.deleted_account_dir(keystore_dir),
                expected_deleted_keystore_dir)

    def test_delete_account(self):
        """
        Creates a new account and delete it.
        Then verify we can load the account from the backup/trash location.
        """
        pywalib = self.pywalib
        account = self.helper_new_account()
        address = account.address
        self.assertEqual(len(pywalib.get_account_list()), 1)
        # deletes the account and verifies it's not loaded anymore
        pywalib.delete_account(account)
        self.assertEqual(len(pywalib.get_account_list()), 0)
        # even recreating the PyWalib object
        pywalib = PyWalib(self.keystore_dir)
        self.assertEqual(len(pywalib.get_account_list()), 0)
        # tries to reload it from the backup/trash location
        deleted_keystore_dir = PyWalib.deleted_account_dir(self.keystore_dir)
        pywalib = PyWalib(deleted_keystore_dir)
        self.assertEqual(len(pywalib.get_account_list()), 1)
        self.assertEqual(pywalib.get_account_list()[0].address, address)

    def test_delete_account_already_exists(self):
        """
        If the destination (backup/trash) directory where the account is moved
        already exists, it should be handled gracefully.
        This could happens if the account gets deleted, then reimported and
        deleted again, refs:
        https://github.com/AndreMiras/PyWallet/issues/88
        """
        pywalib = self.pywalib
        account = self.helper_new_account()
        # creates a file in the backup/trash folder that would conflict
        # with the deleted account
        deleted_keystore_dir = PyWalib.deleted_account_dir(self.keystore_dir)
        os.makedirs(deleted_keystore_dir)
        account_filename = os.path.basename(account.path)
        deleted_account_path = os.path.join(
            deleted_keystore_dir, account_filename)
        # create that file
        open(deleted_account_path, 'a').close()
        # then deletes the account and verifies it worked
        self.assertEqual(len(pywalib.get_account_list()), 1)
        pywalib.delete_account(account)
        self.assertEqual(len(pywalib.get_account_list()), 0)

    def test_handle_etherscan_error(self):
        """
        Checks handle_etherscan_error() error handling.
        """
        # no transaction found
        response_json = {
            'message': 'No transactions found', 'result': [], 'status': '0'
        }
        with self.assertRaises(NoTransactionFoundException):
            PyWalib.handle_etherscan_error(response_json)
        # unknown error
        response_json = {
            'message': 'Unknown error', 'result': [], 'status': '0'
        }
        with self.assertRaises(UnknownEtherscanException) as e:
            PyWalib.handle_etherscan_error(response_json)
        self.assertEqual(e.exception.args[0], response_json)
        # no error
        response_json = {
            'message': 'OK', 'result': [], 'status': '1'
        }
        self.assertEqual(
            PyWalib.handle_etherscan_error(response_json),
            None)

    def test_address_hex(self):
        """
        Checks handle_etherscan_error() error handling.
        """
        expected_addresss = ADDRESS
        # no 0x prefix
        address_no_prefix = ADDRESS.lower().strip("0x")
        address = address_no_prefix
        normalized = PyWalib.address_hex(address)
        self.assertEqual(normalized, expected_addresss)
        # uppercase
        address = "0x" + address_no_prefix.upper()
        normalized = PyWalib.address_hex(address)
        self.assertEqual(normalized, expected_addresss)
        # prefix cannot be uppercase
        address = "0X" + address_no_prefix.upper()
        with self.assertRaises(Exception) as context:
            PyWalib.address_hex(address)
        self.assertEqual(
            context.exception.args[0],
            "Invalid address format: '%s'" % (address))

    def test_get_balance(self):
        """
        Checks get_balance() returns a float.
        """
        address = ADDRESS
        balance_eth = PyWalib.get_balance(address)
        self.assertTrue(type(balance_eth), float)

    def helper_get_history(self, transactions):
        """
        Helper method to test history related methods.
        """
        self.assertEqual(type(transactions), list)
        self.assertTrue(len(transactions) > 1)
        # ordered by timeStamp
        self.assertTrue(
            transactions[0]['timeStamp'] < transactions[1]['timeStamp'])
        # and a bunch of other things
        self.assertEqual(
            set(transactions[0].keys()),
            set([
                'nonce', 'contractAddress', 'cumulativeGasUsed', 'hash',
                'blockHash', 'extra_dict', 'timeStamp', 'gas', 'value',
                'blockNumber', 'to', 'confirmations', 'input', 'from',
                'transactionIndex', 'isError', 'gasPrice', 'gasUsed',
                'txreceipt_status',
            ]))

    def test_get_transaction_history(self):
        """
        Checks get_transaction_history() works as expected.
        """
        address = ADDRESS
        transactions = PyWalib.get_transaction_history(address)
        self.helper_get_history(transactions)
        # value is stored in Wei
        self.assertEqual(transactions[1]['value'], '200000000000000000')
        # but converted to Ether is also accessible
        self.assertEqual(transactions[1]['extra_dict']['value_eth'], 0.2)
        # history contains all send or received transactions
        self.assertEqual(transactions[1]['extra_dict']['sent'], False)
        self.assertEqual(transactions[1]['extra_dict']['received'], True)
        self.assertEqual(transactions[2]['extra_dict']['sent'], True)
        self.assertEqual(transactions[2]['extra_dict']['received'], False)

    def test_get_out_transaction_history(self):
        """
        Checks get_out_transaction_history() works as expected.
        """
        address = ADDRESS
        transactions = PyWalib.get_out_transaction_history(address)
        self.helper_get_history(transactions)
        for i in range(len(transactions)):
            transaction = transactions[i]
            extra_dict = transaction['extra_dict']
            # this is only sent transactions
            self.assertEqual(extra_dict['sent'], True)
            self.assertEqual(extra_dict['received'], False)
            # nonce should be incremented each time
            self.assertEqual(transaction['nonce'], str(i))

    def test_get_nonce(self):
        """
        Checks get_nonce() returns the next nonce, i.e. transaction count.
        """
        address = ADDRESS
        nonce = PyWalib.get_nonce(address)
        transactions = PyWalib.get_out_transaction_history(address)
        last_transaction = transactions[-1]
        last_nonce = int(last_transaction['nonce'])
        self.assertEqual(nonce, last_nonce + 1)

    def test_get_nonce_no_out_transaction(self):
        """
        Makes sure get_nonce() doesn't crash on no out transaction,
        but just returns 0.
        """
        # the VOID_ADDRESS has a lot of in transactions,
        # but no out ones, so the nonce should be 0
        address = VOID_ADDRESS
        nonce = PyWalib.get_nonce(address)
        self.assertEqual(nonce, 0)

    def test_get_nonce_no_transaction(self):
        """
        Makes sure get_nonce() doesn't crash on no transaction,
        but just returns 0.
        """
        # the newly created address has no in or out transaction history
        account = self.helper_new_account()
        address = account.address
        nonce = PyWalib.get_nonce(address)
        self.assertEqual(nonce, 0)

    def test_handle_etherscan_tx_error(self):
        """
        Checks handle_etherscan_tx_error() error handling.
        """
        # no transaction found
        response_json = {
            'jsonrpc': '2.0', 'id': 1, 'error': {
                'message':
                    'Insufficient funds. '
                    'The account you tried to send transaction from does not '
                    'have enough funds. Required 10001500000000000000 and'
                    'got: 53856999715015294.',
                    'code': -32010, 'data': None
                }
        }
        with self.assertRaises(InsufficientFundsException):
            PyWalib.handle_etherscan_tx_error(response_json)
        # unknown error
        response_json = {
            'jsonrpc': '2.0', 'id': 1, 'error': {
                'message':
                    'Unknown error',
                    'code': 0, 'data': None
                }
        }
        with self.assertRaises(UnknownEtherscanException) as e:
            PyWalib.handle_etherscan_tx_error(response_json)
        self.assertEqual(e.exception.args[0], response_json)
        # no error
        response_json = {'jsonrpc': '2.0', 'id': 1}
        self.assertEqual(
            PyWalib.handle_etherscan_tx_error(response_json),
            None)

    def test_transact(self):
        """
        Basic transact() test, makes sure web3 sendRawTransaction gets called.
        """
        pywalib = self.pywalib
        account = self.helper_new_account()
        to = ADDRESS
        sender = account.address
        value_wei = 100
        with mock.patch('web3.eth.Eth.sendRawTransaction') \
                as m_sendRawTransaction:
            pywalib.transact(to=to, value=value_wei, sender=sender)
        self.assertTrue(m_sendRawTransaction.called)

    def test_transact_no_funds(self):
        """
        Tries to send a transaction from an address with no funds.
        """
        pywalib = self.pywalib
        account = self.helper_new_account()
        to = ADDRESS
        sender = account.address
        value_wei = 100
        with self.assertRaises(InsufficientFundsException):
            pywalib.transact(to=to, value=value_wei, sender=sender)

    def test_get_default_keystore_path(self):
        """
        Checks we the default keystore directory exists or create it.
        Verify the path is correct and that we have read/write access to it.
        """
        keystore_dir = PyWalib.get_default_keystore_path()
        if not os.path.exists(keystore_dir):
            os.makedirs(keystore_dir)
        # checks path correctness
        self.assertTrue(keystore_dir.endswith(".config/pyethapp/keystore/"))
        # checks read/write access
        self.assertEqual(os.access(keystore_dir, os.R_OK), True)
        self.assertEqual(os.access(keystore_dir, os.W_OK), True)
