import unittest
from tests import test_import, test_pywalib


def suite():
    modules = [test_import, test_pywalib]
    test_suite = unittest.TestSuite()
    for module in modules:
        print("addTest:", module)
        test_suite.addTest(unittest.TestLoader().loadTestsFromModule(module))
    return test_suite
