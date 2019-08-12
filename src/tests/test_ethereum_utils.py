import os
import shutil
import unittest
from tempfile import TemporaryDirectory, mkdtemp
from unittest import mock

from ethereum_utils import AccountUtils
from pyethapp_accounts import Account

PASSWORD = "password"


class TestAccountUtils(unittest.TestCase):

    def setUp(self):
        self.keystore_dir = mkdtemp()
        self.account_utils = AccountUtils(self.keystore_dir)

    def tearDown(self):
        shutil.rmtree(self.keystore_dir, ignore_errors=True)

    def test_new_account(self):
        """
        Simple account creation test case.
        1) verifies the current account list is empty
        2) creates a new account and verify we can retrieve it
        3) tries to unlock the account
        """
        # 1) verifies the current account list is empty
        self.assertEqual(self.account_utils.get_account_list(), [])
        # 2) creates a new account and verify we can retrieve it
        password = PASSWORD
        account = self.account_utils.new_account(password, iterations=1)
        self.assertEqual(len(self.account_utils.get_account_list()), 1)
        self.assertEqual(account, self.account_utils.get_account_list()[0])
        # 3) tries to unlock the account
        # it's unlocked by default after creation
        self.assertFalse(account.locked)
        # let's lock it and unlock it back
        account.lock()
        self.assertTrue(account.locked)
        account.unlock(password)
        self.assertFalse(account.locked)

    def test_get_account_list(self):
        """
        Makes sure get_account_list() loads properly accounts from file system.
        """
        password = PASSWORD
        self.assertEqual(self.account_utils.get_account_list(), [])
        account = self.account_utils.new_account(password, iterations=1)
        self.assertEqual(len(self.account_utils.get_account_list()), 1)
        account = self.account_utils.get_account_list()[0]
        self.assertIsNotNone(account.path)
        # removes the cache copy and checks again if it gets loaded
        self.account_utils._accounts = None
        self.assertEqual(len(self.account_utils.get_account_list()), 1)
        account = self.account_utils.get_account_list()[0]
        self.assertIsNotNone(account.path)

    def test_get_account_list_error(self):
        """
        get_account_list() should not cache empty account on PermissionError.
        """
        # creates a temporary account that we'll try to list
        password = PASSWORD
        account = Account.new(password, uuid=None, iterations=1)
        account.path = os.path.join(self.keystore_dir, account.address.hex())
        with open(account.path, 'w') as f:
            f.write(account.dump())
        # `listdir()` can raise a `PermissionError`
        with mock.patch('os.listdir') as mock_listdir:
            mock_listdir.side_effect = PermissionError
            with self.assertRaises(PermissionError):
                self.account_utils.get_account_list()
        # the empty account list should not be catched and loading it again
        # should show the existing account on file system
        self.assertEqual(len(self.account_utils.get_account_list()), 1)
        self.assertEqual(
            self.account_utils.get_account_list()[0].address, account.address)

    def test_get_account_list_no_dir(self):
        """
        The keystore directory should be created if it doesn't exist, refs:
        https://github.com/AndreMiras/PyWallet/issues/133
        """
        # nominal case when the directory already exists
        with TemporaryDirectory() as keystore_dir:
            self.assertTrue(os.path.isdir(keystore_dir))
            account_utils = AccountUtils(keystore_dir)
            self.assertEqual(account_utils.get_account_list(), [])
        # when the directory doesn't exist it should also be created
        self.assertFalse(os.path.isdir(keystore_dir))
        account_utils = AccountUtils(keystore_dir)
        self.assertTrue(os.path.isdir(keystore_dir))
        self.assertEqual(account_utils.get_account_list(), [])
        shutil.rmtree(keystore_dir, ignore_errors=True)

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
                AccountUtils.deleted_account_dir(keystore_dir),
                expected_deleted_keystore_dir)

    def test_delete_account(self):
        """
        Creates a new account and delete it.
        Then verify we can load the account from the backup/trash location.
        """
        password = PASSWORD
        account = self.account_utils.new_account(password, iterations=1)
        address = account.address
        self.assertEqual(len(self.account_utils.get_account_list()), 1)
        # deletes the account and verifies it's not loaded anymore
        self.account_utils.delete_account(account)
        self.assertEqual(len(self.account_utils.get_account_list()), 0)
        # even recreating the AccountUtils object
        self.account_utils = AccountUtils(self.keystore_dir)
        self.assertEqual(len(self.account_utils.get_account_list()), 0)
        # tries to reload it from the backup/trash location
        deleted_keystore_dir = AccountUtils.deleted_account_dir(
            self.keystore_dir)
        self.account_utils = AccountUtils(deleted_keystore_dir)
        self.assertEqual(len(self.account_utils.get_account_list()), 1)
        self.assertEqual(
            self.account_utils.get_account_list()[0].address, address)

    def test_delete_account_already_exists(self):
        """
        If the destination (backup/trash) directory where the account is moved
        already exists, it should be handled gracefully.
        This could happens if the account gets deleted, then reimported and
        deleted again, refs:
        https://github.com/AndreMiras/PyWallet/issues/88
        """
        password = PASSWORD
        account = self.account_utils.new_account(password, iterations=1)
        # creates a file in the backup/trash folder that would conflict
        # with the deleted account
        deleted_keystore_dir = AccountUtils.deleted_account_dir(
            self.keystore_dir)
        os.makedirs(deleted_keystore_dir)
        account_filename = os.path.basename(account.path)
        deleted_account_path = os.path.join(
            deleted_keystore_dir, account_filename)
        # create that file
        open(deleted_account_path, 'a').close()
        # then deletes the account and verifies it worked
        self.assertEqual(len(self.account_utils.get_account_list()), 1)
        self.account_utils.delete_account(account)
        self.assertEqual(len(self.account_utils.get_account_list()), 0)
