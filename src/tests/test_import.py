import unittest


class ModulesImportTestCase(unittest.TestCase):
    """
    Simple test cases, verifying core modules were installed properly.
    """

    def test_pyethash(self):
        import pyethash
        self.assertIsNotNone(pyethash.get_seedhash(0))

    def test_hashlib_sha3(self):
        import hashlib
        import sha3
        self.assertIsNotNone(hashlib.sha3_512())
        self.assertIsNotNone(sha3.keccak_512())

    def test_scrypt(self):
        import scrypt
        # This will take at least 0.1 seconds
        data = scrypt.encrypt('a secret message', 'password', maxtime=0.1)
        self.assertIsNotNone(data)
        # 'scrypt\x00\r\x00\x00\x00\x08\x00\x00\x00\x01RX9H'
        # This will also take at least 0.1 seconds
        decrypted = scrypt.decrypt(data, 'password', maxtime=0.1)
        self.assertEqual(decrypted, 'a secret message')

    def test_pyethereum(self):
        from ethereum import compress, utils
        self.assertIsNotNone(compress)
        self.assertIsNotNone(utils)

    def test_pyethapp(self):
        from pyethapp.accounts import Account
        from ethereum.tools.keys import PBKDF2_CONSTANTS
        # backup iterations
        iterations_backup = PBKDF2_CONSTANTS['c']
        # speeds up the test
        PBKDF2_CONSTANTS['c'] = 100
        password = "foobar"
        uuid = None
        account = Account.new(password, uuid=uuid)
        # restore iterations
        PBKDF2_CONSTANTS['c'] = iterations_backup
        address = account.address.encode('hex')
        self.assertIsNotNone(account)
        self.assertIsNotNone(address)


if __name__ == '__main__':
    unittest.main()
