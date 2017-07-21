from __future__ import unicode_literals

import os
import os.path as op
import shutil
import sys
import threading
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

    def helper_test_empty_account(self, app):
        """
        Verifies the UI behaves as expected on empty account list.
        """
        controller = app.controller
        pywalib = controller.pywalib
        # loading the app with empty account directory
        self.assertEqual(len(pywalib.get_account_list()), 0)
        # should open the trigger the "Create new account" view to be open
        self.assertEqual('Create new account', app.controller.toolbar.title)
        dialogs = controller.dialogs
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'No keystore found.')
        dialog.dismiss()
        self.assertEqual(len(dialogs), 0)

    def helper_test_create_first_account(self, app):
        """
        Creates the first account.
        """
        controller = app.controller
        pywalib = controller.pywalib
        # makes sure no account are loaded
        self.assertEqual(len(pywalib.get_account_list()), 0)
        # retrieves the create_new_account widget
        controller = app.controller
        create_new_account = controller.create_new_account
        # retrieves password fields
        # self.assertEqual("create_new_account.ids", create_new_account.ids)
        new_password1_id = create_new_account.ids.new_password1_id
        new_password2_id = create_new_account.ids.new_password2_id
        # fill them up with same password
        new_password1_id.text = new_password2_id.text = "password"
        # before clicking the create account button,
        # only the main thread is running
        self.assertEqual(len(threading.enumerate()), 1)
        main_thread = threading.enumerate()[0]
        self.assertEqual(type(main_thread), threading._MainThread)
        # retrieves button widget and click it
        create_account_button_id = \
            create_new_account.ids.create_account_button_id
        create_account_button_id.dispatch('on_release')
        # after submitting the account creation thread should run
        self.assertEqual(len(threading.enumerate()), 2)
        create_account_thread = threading.enumerate()[1]
        self.assertEqual(type(create_account_thread), threading.Thread)
        self.assertEqual(
            create_account_thread._Thread__target.func_name, "create_account")
        # waits for the end of the thread
        create_account_thread.join()
        # and verifies the account was created
        self.assertEqual(len(pywalib.get_account_list()), 1)

    def helper_test_on_send_click(self, app):
        """
        This is a regression test for #63, verify clicking "Send" Ethers works
        as expected.
        https://github.com/AndreMiras/PyWallet/issues/63
        """
        controller = app.controller
        send = controller.send
        send_button_id = send.ids.send_button_id
        # verifies clicking send button doesn't crash the application
        send_button_id.dispatch('on_release')
        dialogs = controller.dialogs
        # but it would still raise some popups since the form is invalid
        self.assertEqual(len(dialogs), 2)
        self.assertEqual(dialogs[0].title, 'Input error')
        self.assertEqual(dialogs[1].title, 'Invalid form')
        controller.dismiss_all_dialogs()
        self.assertEqual(len(dialogs), 0)

    # main test function
    def run_test(self, app, *args):
        Clock.schedule_interval(self.pause, 0.000001)
        self.helper_test_empty_account(app)
        self.helper_test_create_first_account(app)
        self.helper_test_on_send_click(app)

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
