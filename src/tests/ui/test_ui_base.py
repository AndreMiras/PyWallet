import os
import os.path as op
import shutil
import sys
import time
import unittest
from functools import partial
from tempfile import mkdtemp

from kivy.clock import Clock

# TODO: hardcoded path, refs:
# https://github.com/KeyWeeUsr/KivyUnitTest/issues/3
main_path = op.dirname(op.dirname(op.dirname(op.abspath(__file__))))
sys.path.append(main_path)

from main import PyWalletApp    # NOQA: F402 # isort:skip


class Test(unittest.TestCase):

    def setUp(self):
        """
        Sets a temporay KEYSTORE_PATH, so keystore directory and related
        application files will be stored here until tearDown().
        """
        self.keystore_path = mkdtemp()
        os.environ['KEYSTORE_PATH'] = self.keystore_path

    def tearDown(self):
        shutil.rmtree(self.keystore_path, ignore_errors=True)

    # sleep function that catches `dt` from Clock
    def pause(*args):
        time.sleep(0.000001)

    # main test function
    def run_test(self, app, *args):
        Clock.schedule_interval(self.pause, 0.000001)

        # Do something
        # app.my_button.dispatch('on_release')
        self.assertEqual('Create new account', app.controller.toolbar.title)

        # Comment out if you are editing the test, it'll leave the
        # Window opened.
        app.stop()

    # same named function as the filename(!)
    def test_ui_base(self):
        app = PyWalletApp()
        p = partial(self.run_test, app)
        # schedule_once() timeout is high here so the application has time
        # to initialize, refs #52
        Clock.schedule_once(p, 1.0)
        app.run()


if __name__ == '__main__':
    unittest.main()
