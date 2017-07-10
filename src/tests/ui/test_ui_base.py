import os.path as op
import sys
import time
import unittest
from functools import partial

from kivy.clock import Clock

# TODO: hardcoded path, refs:
# https://github.com/KeyWeeUsr/KivyUnitTest/issues/3
main_path = op.dirname(op.dirname(op.dirname(op.abspath(__file__))))
sys.path.append(main_path)

from main import PyWalletApp    # NOQA: F402 # isort:skip


class Test(unittest.TestCase):
    # sleep function that catches `dt` from Clock
    def pause(*args):
        time.sleep(0.000001)

    # main test function
    def run_test(self, app, *args):
        Clock.schedule_interval(self.pause, 0.000001)

        # Do something
        # app.my_button.dispatch('on_release')
        self.assertEqual('', app.controller.toolbar.title)

        # Comment out if you are editing the test, it'll leave the
        # Window opened.
        app.stop()

    # same named function as the filename(!)
    def test_example(self):
        app = PyWalletApp()
        p = partial(self.run_test, app)
        Clock.schedule_once(p, 0.000001)
        app.run()


if __name__ == '__main__':
    unittest.main()
