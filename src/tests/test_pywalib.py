import shutil
import unittest
from tempfile import mkdtemp

from pywalib import PyWalib


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


if __name__ == '__main__':
    unittest.main()
