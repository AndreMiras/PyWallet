import unittest
from testsuite import suite


class TestSuitetTestCase(unittest.TestCase):
    """
    Simple test case, verifying the testsuite module works.
    """

    def test_testsuite(self):
        """
        Simply verifies the suite is created.
        """
        test_suite = suite()
        self.assertEqual(type(test_suite), unittest.suite.TestSuite)


if __name__ == '__main__':
    unittest.main()
