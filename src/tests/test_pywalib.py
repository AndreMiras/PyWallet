import shutil
import unittest
from tempfile import mkdtemp

from pywalib import (NoTransactionFoundException, PyWalib,
                     UnknownEtherscanException)

ADDRESS = "0xab5801a7d398351b8be11c439e05c5b3259aec9b"


class PywalibTestCase(unittest.TestCase):
    """
    Simple test cases, verifying pywalib works as expected.
    """

    @classmethod
    def setUpClass(cls):
        cls.keystore_dir = mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.keystore_dir, ignore_errors=True)

    def test_new_account(self):
        """
        Simple account creation test case.
        1) verifies the current account list is empty
        2) creates a new account and verify we can retrieve it
        3) tries to unlock the account
        """
        # 1) verifies the current account list is empty
        pywalib = PyWalib(PywalibTestCase.keystore_dir)
        account_list = pywalib.get_account_list()
        self.assertEqual(len(account_list), 0)
        # 2) creates a new account and verify we can retrieve it
        password = "password"
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
        pywalib = PyWalib(PywalibTestCase.keystore_dir)
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
        with self.assertRaises(UnknownEtherscanException):
            PyWalib.handle_etherscan_error(response_json)
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
            context.exception.message,
            "Invalid address format: '%s'" % (address))

    def test_get_balance(self):
        """
        Checks get_balance() returns a float.
        """
        address = ADDRESS
        balance_eth = PyWalib.get_balance(address)
        self.assertTrue(type(balance_eth), float)

    def test_get_transaction_history(self):
        """
        Checks get_transaction_history() works as expected.
        """
        address = ADDRESS
        transactions = PyWalib.get_transaction_history(address)
        self.assertEqual(type(transactions), list)
        self.assertTrue(len(transactions) > 1)
        # ordered by timeStamp
        self.assertTrue(
            transactions[0]['timeStamp'] < transactions[1]['timeStamp'])
        # value is stored in Wei
        self.assertEqual(transactions[1]['value'], '200000000000000000')
        # but converted to Ether is also accessible
        self.assertEqual(transactions[1]['extra_dict']['value_eth'], 0.2)
        # as well as info suchs as if it was sent or received
        self.assertEqual(transactions[1]['extra_dict']['sent'], False)
        self.assertEqual(transactions[1]['extra_dict']['received'], True)
        self.assertEqual(transactions[2]['extra_dict']['sent'], True)
        self.assertEqual(transactions[2]['extra_dict']['received'], False)
        # and a bunch of other things
        self.assertEqual(
            set(transactions[0].keys()),
            set([
                'nonce', 'contractAddress', 'cumulativeGasUsed', 'hash',
                'blockHash', 'extra_dict', 'timeStamp', 'gas', 'value',
                'blockNumber', 'to', 'confirmations', 'input', 'from',
                'transactionIndex', 'isError', 'gasPrice', 'gasUsed'
            ]))


if __name__ == '__main__':
    unittest.main()
