import unittest


class ModulesImportTestCase(unittest.TestCase):
    """
    Simple test cases, verifying core modules were installed properly.
    """

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
        decrypted = scrypt.decrypt(data, 'password', maxtime=0.5)
        self.assertEqual(decrypted, 'a secret message')

    def test_zbarcam(self):
        from zbarcam import zbarcam
        # zbarcam imports PIL and monkey patches it so it has
        # the same interfaces as Pillow
        self.assertTrue(hasattr(zbarcam, 'PIL'))
        self.assertTrue(hasattr(zbarcam.PIL.Image, 'frombytes'))
        self.assertTrue(hasattr(zbarcam.PIL.Image.Image, 'tobytes'))


if __name__ == '__main__':
    unittest.main()
