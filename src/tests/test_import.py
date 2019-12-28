import unittest


class ModulesImportTestCase(unittest.TestCase):
    """
    Simple test cases, verifying core modules were installed properly.
    """

    def test_hashlib_sha3(self):
        import hashlib
        self.assertIsNotNone(hashlib.sha3_512())

    def test_zbarcam(self):
        from kivy_garden.zbarcam import zbarcam
        # zbarcam imports PIL and monkey patches it so it has
        # the same interfaces as Pillow
        self.assertTrue(hasattr(zbarcam, 'PIL'))
        self.assertTrue(hasattr(zbarcam.PIL.Image, 'frombytes'))
        self.assertTrue(hasattr(zbarcam.PIL.Image.Image, 'tobytes'))


if __name__ == '__main__':
    unittest.main()
