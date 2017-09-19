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

import kivymd
import mock
from kivy.clock import Clock

# TODO: hardcoded path, refs:
# https://github.com/KeyWeeUsr/KivyUnitTest/issues/3
main_path = op.dirname(op.dirname(op.dirname(op.abspath(__file__))))
sys.path.append(main_path)

import main    # NOQA: F402 # isort:skip


class Test(unittest.TestCase):

    def setUp(self):
        """
        Sets a temporay KEYSTORE_PATH, so keystore directory and related
        application files will be stored here until tearDown().
        """
        self.temp_path = mkdtemp()
        os.environ['KEYSTORE_PATH'] = self.temp_path

    def tearDown(self):
        shutil.rmtree(self.temp_path, ignore_errors=True)

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
        self.assertEqual(controller.screen_manager.current, 'manage_keystores')
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
        self.assertEqual('Create new account', app.controller.toolbar.title)
        self.assertEqual(controller.current_account, None)
        # retrieves the create_new_account widget
        controller = app.controller
        create_new_account = controller.create_new_account
        # retrieves widgets (password fields, sliders and buttons)
        new_password1_id = create_new_account.ids.new_password1_id
        new_password2_id = create_new_account.ids.new_password2_id
        speed_slider_id = create_new_account.ids.speed_slider_id
        create_account_button_id = \
            create_new_account.ids.create_account_button_id
        # fills them up with same password
        new_password1_id.text = new_password2_id.text = "password"
        # makes the account creation fast
        speed_slider_id.value = speed_slider_id.max
        # before clicking the create account button,
        # only the main thread is running
        self.assertEqual(len(threading.enumerate()), 1)
        main_thread = threading.enumerate()[0]
        self.assertEqual(type(main_thread), threading._MainThread)
        # click the create account button
        create_account_button_id.dispatch('on_release')
        # after submitting the account creation thread should run
        self.assertEqual(len(threading.enumerate()), 2)
        create_account_thread = threading.enumerate()[1]
        self.assertEqual(type(create_account_thread), threading.Thread)
        self.assertEqual(
            create_account_thread._Thread__target.func_name, "create_account")
        # waits for the end of the thread
        create_account_thread.join()
        # thread has ended and the main thread is running alone again
        self.assertEqual(len(threading.enumerate()), 1)
        main_thread = threading.enumerate()[0]
        self.assertEqual(type(main_thread), threading._MainThread)
        # and verifies the account was created
        self.assertEqual(len(pywalib.get_account_list()), 1)
        # TODO verify the form fields were voided
        # self.assertEqual(new_password1_id.text, '')
        # self.assertEqual(new_password2_id.text, '')
        # we should get redirected to the overview page
        self.assertEqual(controller.screen_manager.current, 'overview')
        # the new account should be loaded in the controller
        self.assertEqual(
            controller.current_account,
            pywalib.get_account_list()[0])
        # TODO: also verify the Toolbar title was updated correctly
        # self.assertEqual('TODO', app.controller.toolbar.title)
        # check the redirect dialog
        dialogs = controller.dialogs
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'Account created, redirecting...')
        dialog.dismiss()
        self.assertEqual(len(dialogs), 0)

    def helper_test_create_account_form(self, app):
        """
        Create account form validation checks.
        Testing both not matching and empty passwords.
        """
        controller = app.controller
        pywalib = controller.pywalib
        # number of existing accounts before the test
        account_count_before = len(pywalib.get_account_list())
        # TODO: use dispatch('on_release') on navigation drawer
        controller.load_create_new_account()
        self.assertEqual('Create new account', app.controller.toolbar.title)
        self.assertEqual(controller.screen_manager.current, 'manage_keystores')
        # retrieves the create_new_account widget
        controller = app.controller
        create_new_account = controller.create_new_account
        # retrieves widgets (password fields, sliders and buttons)
        new_password1_id = create_new_account.ids.new_password1_id
        new_password2_id = create_new_account.ids.new_password2_id
        create_account_button_id = \
            create_new_account.ids.create_account_button_id
        passwords_to_try = [
            # passwords not matching
            {
                'new_password1': 'not matching1',
                'new_password2': 'not matching2'
            },
            # passwords empty
            {
                'new_password1': '',
                'new_password2': ''
            },
        ]
        for password_dict in passwords_to_try:
            new_password1_id.text = password_dict['new_password1']
            new_password2_id.text = password_dict['new_password2']
            # makes the account creation fast
            # before clicking the create account button,
            # only the main thread is running
            self.assertEqual(len(threading.enumerate()), 1)
            main_thread = threading.enumerate()[0]
            self.assertEqual(type(main_thread), threading._MainThread)
            # click the create account button
            create_account_button_id.dispatch('on_release')
            # after submitting the account verification thread should run
            self.assertEqual(len(threading.enumerate()), 2)
            create_account_thread = threading.enumerate()[1]
            self.assertEqual(type(create_account_thread), threading.Thread)
            self.assertEqual(
                create_account_thread._Thread__target.func_name,
                "create_account")
            # waits for the end of the thread
            create_account_thread.join()
            # the form should popup an error dialog
            dialogs = controller.dialogs
            self.assertEqual(len(dialogs), 1)
            dialog = dialogs[0]
            self.assertEqual(dialog.title, 'Invalid form')
            dialog.dismiss()
            self.assertEqual(len(dialogs), 0)
            # no account were created
            self.assertEqual(
                account_count_before,
                len(pywalib.get_account_list()))

    def helper_test_on_send_click(self, app):
        """
        This is a regression test for #63, verify clicking "Send" Ethers works
        as expected.
        https://github.com/AndreMiras/PyWallet/issues/63
        """
        controller = app.controller
        # TODO: use dispatch('on_release') on navigation drawer
        controller.load_landing_page()
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

    def helper_load_switch_account(self, app):
        """
        Helper method for loading the switch account screen and returning
        the class handling this view.
        """
        controller = app.controller
        # TODO: use dispatch('on_release') on navigation drawer
        controller.load_switch_account()
        switch_account = controller.switch_account
        self.assertEqual(switch_account.__class__, main.SwitchAccount)
        return switch_account

    def helper_test_address_alias(self, app):
        """
        Creates, updates and deletes account address aliases.
        """
        controller = app.controller
        pywalib = controller.pywalib
        account1 = pywalib.get_account_list()[0]
        # creates a second account
        account2 = pywalib.new_account(password="password", security_ratio=1)
        address1 = '0x' + account1.address.encode("hex")
        address2 = '0x' + account2.address.encode("hex")
        Controller = main.Controller

        @staticmethod
        def get_store_path():
            """
            Makes sure we don't mess up with actual store config file.
            """
            os.environ['KEYSTORE_PATH'] = self.temp_path
            store_path = os.path.join(self.temp_path, 'store.json')
            return store_path
        with mock.patch.object(Controller, 'get_store_path', get_store_path):
            # no alias by default
            with self.assertRaises(KeyError):
                Controller.get_account_alias(account1)
            with self.assertRaises(KeyError):
                Controller.get_address_alias(address1)
            # sets some aliases
            alias1 = 'alias1'
            alias2 = 'alias2'
            Controller.set_account_alias(account1, alias1)
            Controller.set_account_alias(account2, alias2)
            # checks we can retrieve them
            self.assertEqual(
                Controller.get_account_alias(account1), alias1)
            self.assertEqual(
                Controller.get_account_alias(account2), alias2)
            self.assertEqual(
                Controller.get_address_alias(address1), alias1)
            self.assertEqual(
                Controller.get_address_alias(address2), alias2)
            # updates an alias
            alias1 = 'alias0'
            Controller.set_account_alias(account1, alias1)
            self.assertEqual(
                Controller.get_account_alias(account1), alias1)
            # deletes one and see if it worked
            Controller.delete_account_alias(account1)
            with self.assertRaises(KeyError):
                Controller.get_account_alias(account1)
            # the second one should still be there
            self.assertEqual(
                Controller.get_address_alias(address2), alias2)
        # tears down
        pywalib.delete_account(account2)

    # TODO:
    # also test we're getting invited to create a new account
    # when all accounts were deleted
    def helper_test_delete_account(self, app):
        """
        Deletes account from the UI.
        """
        controller = app.controller
        pywalib = controller.pywalib
        # makes sure we have an account to play with
        self.assertEqual(len(pywalib.get_account_list()), 1)
        # makes sure the account appears in the switch account view
        switch_account = self.helper_load_switch_account(app)
        account_list_id = switch_account.ids.account_list_id
        children = account_list_id.children
        self.assertEqual(len(children), 1)
        item = children[0]
        self.assertEqual(type(item), kivymd.list.OneLineListItem)
        self.assertEqual(item.account, pywalib.get_account_list()[0])
        # go to the manage account screen
        # TODO: use dispatch('on_release') on navigation drawer
        controller.load_manage_keystores()
        self.assertEqual('Manage existing', app.controller.toolbar.title)
        # verifies an account is showing
        manage_existing = controller.manage_existing
        account_address_id = manage_existing.ids.account_address_id
        account = pywalib.get_account_list()[0]
        account_address = '0x' + account.address.encode("hex")
        self.assertEqual(account_address_id.text, account_address)
        # clicks delete
        delete_button_id = manage_existing.ids.delete_button_id
        delete_button_id.dispatch('on_release')
        # a confirmation popup should show
        dialogs = controller.dialogs
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'Are you sure?')
        # confirm it
        # TODO: click on the dialog action button itself
        manage_existing.on_delete_account_yes(dialog)
        # the dialog should be replaced by another one
        dialogs = controller.dialogs
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'Account deleted, redirecting...')
        controller.dismiss_all_dialogs()
        # and the account deleted
        self.assertEqual(len(pywalib.get_account_list()), 0)
        # makes sure the account was also cleared from the selection view
        switch_account = self.helper_load_switch_account(app)
        account_list_id = switch_account.ids.account_list_id
        self.assertEqual(len(account_list_id.children), 0)

    # main test function
    def run_test(self, app, *args):
        Clock.schedule_interval(self.pause, 0.000001)
        self.helper_test_empty_account(app)
        self.helper_test_create_first_account(app)
        self.helper_test_create_account_form(app)
        self.helper_test_on_send_click(app)
        self.helper_test_address_alias(app)
        self.helper_test_delete_account(app)

        # Comment out if you are editing the test, it'll leave the
        # Window opened.
        app.stop()

    # same named function as the filename(!)
    def test_ui_base(self):
        app = main.PyWalletApp()
        p = partial(self.run_test, app)
        # schedule_once() timeout is high here so the application has time
        # to initialize, refs #52
        Clock.schedule_once(p, 2.0)
        app.run()


if __name__ == '__main__':
    unittest.main()
