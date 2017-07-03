import unittest
from tests import test_import, test_pywalib


def suite():
    modules = [test_import, test_pywalib]
    suite = unittest.TestSuite()
    for module in modules:
        print("addTest:", module)
        suite.addTest(unittest.TestLoader().loadTestsFromModule(module))
    return suite
