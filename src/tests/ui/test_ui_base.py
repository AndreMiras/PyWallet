import io
import os
import shutil
import threading
import time
import unittest
from functools import partial
from tempfile import mkdtemp
from unittest import mock

import kivymd
import requests
from kivy.clock import Clock
from kivy.core.image import Image

import main
import pywalib
from pywallet.switchaccount import SwitchAccount
from pywallet.utils import Dialog

ADDRESS = "0xab5801a7d398351b8be11c439e05c5b3259aec9b"
FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'fixtures')


def patch_get_store_path(temp_path):
    store_path = os.path.join(temp_path, 'store.json')
    return mock.patch(
        'pywallet.controller.Store.get_store_path', lambda: store_path)


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

    def advance_frames(self, count):
        """
        Borrowed from Kivy 1.10.0+ /kivy/tests/common.py
        GraphicUnitTest.advance_frames()
        Makes it possible to to wait for UI to process, refs #110.
        """
        from kivy.base import EventLoop
        for i in range(count):
            EventLoop.idle()

    def helper_setup(self, app):
        main.SCREEN_SWITCH_DELAY = 0.001

    def helper_test_empty_account(self, app):
        """
        Verifies the UI behaves as expected on empty account list.
        """
        controller = app.controller
        pywalib = controller.pywalib
        # loading the app with empty account directory
        self.assertEqual(len(pywalib.get_account_list()), 0)
        # should trigger the "Create new account" view to be open
        self.advance_frames(1)
        self.assertEqual('Create new account', app.controller.toolbar.title)
        self.assertEqual(controller.screen_manager.current, 'manage_keystores')
        dialogs = Dialog.dialogs
        self.advance_frames(1)
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'No keystore found.')
        dialog.dismiss()
        self.assertEqual(len(dialogs), 0)

    def helper_test_back_home_empty_account(self, app):
        """
        Loading the overview (back button) with no account should
        not crash the application, refs #115.
        """
        controller = app.controller
        pywalib = controller.pywalib
        # loading the app with empty account directory
        self.assertEqual(len(pywalib.get_account_list()), 0)
        # tries to go back to the home screen with escape key
        # def on_keyboard(self, window, key, *args):
        controller.on_keyboard(window=None, key=27)
        # loading the overview with empty account should not crash
        self.assertEqual('', app.controller.toolbar.title)
        self.assertEqual(controller.screen_manager.current, 'overview')

    def helper_test_create_first_account(self, app):
        """
        Creates the first account.
        """
        controller = app.controller
        pywalib = controller.pywalib
        # makes sure no account are loaded
        self.assertEqual(len(pywalib.get_account_list()), 0)
        controller.load_create_new_account()
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
        # let's not hit the network (speed up testing)
        with mock.patch('pywalib.PyWalib.get_balance'), \
                mock.patch('pywalib.PyWalib.get_transaction_history'):
            # click the create account button
            create_account_button_id.dispatch('on_release')
            # after submitting the account creation thread should run
            self.assertEqual(len(threading.enumerate()), 2)
            create_account_thread = threading.enumerate()[1]
            self.assertEqual(type(create_account_thread), threading.Thread)
            self.assertEqual(
                create_account_thread._target.__name__,
                "create_account")
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
            # TODO: broken in #124
            # self.advance_frames(1)
            self.advance_frames(30)
            self.assertEqual(controller.screen_manager.current, 'overview')
            # the new account should be loaded in the controller
            self.assertEqual(
                controller.current_account,
                pywalib.get_account_list()[0])
            # TODO: also verify the Toolbar title was updated correctly
            # self.assertEqual('TODO', app.controller.toolbar.title)
            # joins ongoing threads
            [t.join() for t in threading.enumerate()[1:]]
        # check the redirect dialog
        dialogs = Dialog.dialogs
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
            threads = threading.enumerate()
            # since we may run into race condition with threading.enumerate()
            # we make the test conditional
            if len(threads) == 2:
                create_account_thread = threading.enumerate()[1]
                self.assertEqual(
                    type(create_account_thread), threading.Thread)
                self.assertEqual(
                    create_account_thread._target.__name__,
                    "create_account")
                # waits for the end of the thread
                create_account_thread.join()
            # the form should popup an error dialog
            dialogs = Dialog.dialogs
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
        Verifies clicking "Send" Ethers works as expected, refs #63.
        Also checks for the amount field, refs #152.
        """
        controller = app.controller
        # TODO: use dispatch('on_release') on navigation drawer
        controller.load_landing_page()
        send = controller.send
        send_button_id = send.ids.send_button_id
        # verifies clicking send button doesn't crash the application
        send_button_id.dispatch('on_release')
        dialogs = Dialog.dialogs
        # but it would still raise a popup since the form is invalid
        self.assertEqual(len(dialogs), 1)
        self.assertEqual(dialogs[0].title, 'Input error')
        Dialog.dismiss_all_dialogs()
        self.assertEqual(len(dialogs), 0)

    def helper_test_send(self, app):
        """
        Verifies it's possible to send some Ethers through the UI.
        """
        controller = app.controller
        # TODO: use dispatch('on_release') on navigation drawer
        controller.load_landing_page()
        send = controller.send
        send_to_id = send.ids.send_to_id
        send_amount_id = send.ids.send_amount_id
        send_button_id = send.ids.send_button_id
        send_to_id.text = ADDRESS
        send_amount_id.text = '0.1'
        send_button_id.dispatch('on_release')
        dialogs = Dialog.dialogs
        # we should be asked for the password
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'Enter your password')
        # TODO: also perform the test with invalid password
        dialog.password = 'password'
        unlock_button = dialog._action_buttons[0]
        self.assertEqual(unlock_button.text, 'Unlock')
        with mock.patch('pywallet.utils.Dialog.snackbar_message') \
                as mock_snackbar_message:
            unlock_button.dispatch('on_release')
            # for some reason we need to trigger on_password manually in tests
            send.on_password(None, None)
            # password form got closed
            dialogs = Dialog.dialogs
            self.assertEqual(len(dialogs), 0)
            # unlock_send_transaction() thread should be running
            self.assertEqual(len(threading.enumerate()), 2)
            thread = threading.enumerate()[1]
            self.assertEqual(type(thread), threading.Thread)
            self.assertEqual(
                thread._target.__name__, 'unlock_send_transaction')
            thread.join()
            # checks snackbar messages
            self.assertEqual(
                mock_snackbar_message.call_args_list,
                [
                    mock.call('Unlocking account...'),
                    mock.call('Unlocked! Sending transaction...'),
                    mock.call('Insufficient funds'),
                ]
            )
        # TODO: also perform the test with enough funds (mocking the response)

    def helper_load_switch_account(self, app):
        """
        Helper method for loading the switch account screen and returning
        the class handling this view.
        """
        controller = app.controller
        # TODO: use dispatch('on_release') on navigation drawer
        controller.load_switch_account()
        # TODO: broken in #124
        # self.advance_frames(1)
        self.advance_frames(10)
        switch_account = controller.switch_account
        self.assertEqual(switch_account.__class__, SwitchAccount)
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
        address1 = '0x' + account1.address.hex()
        address2 = '0x' + account2.address.hex()
        Controller = main.Controller

        with patch_get_store_path(self.temp_path):
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
        # TODO: broken in #124
        # self.advance_frames(1)
        self.advance_frames(30)
        self.assertEqual('Manage existing', app.controller.toolbar.title)
        # verifies an account is showing
        manage_existing = controller.manage_existing
        account_address_id = manage_existing.ids.account_address_id
        account = pywalib.get_account_list()[0]
        account_address = '0x' + account.address.hex()
        self.assertEqual(account_address_id.text, account_address)
        # clicks delete
        delete_button_id = manage_existing.ids.delete_button_id
        delete_button_id.dispatch('on_release')
        # a confirmation popup should show
        dialogs = Dialog.dialogs
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'Are you sure?')
        # confirm it
        # TODO: click on the dialog action button itself
        manage_existing.on_delete_account_yes(dialog)
        # the dialog should be replaced by another one
        dialogs = Dialog.dialogs
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'Account deleted, redirecting...')
        Dialog.dismiss_all_dialogs()
        # and the account deleted
        self.assertEqual(len(pywalib.get_account_list()), 0)
        # makes sure the account was also cleared from the selection view
        switch_account = self.helper_load_switch_account(app)
        account_list_id = switch_account.ids.account_list_id
        # TODO: broken in #124
        self.advance_frames(30)
        self.assertEqual(len(account_list_id.children), 0)

    def helper_test_delete_account_none_selected(self, app):
        """
        Tries to delete account when none are selected, refs #90.
        """
        controller = app.controller
        pywalib = controller.pywalib
        manage_existing = controller.manage_existing
        # makes sure an account is selected
        pywalib.new_account(password="password", security_ratio=1)
        controller.current_account = pywalib.get_account_list()[0]
        # ManageExisting and Controller current_account should be in sync
        self.assertEqual(
            manage_existing.current_account, controller.current_account)
        # chaning in the Controller, should trigger the change on the other
        self.assertTrue(manage_existing.current_account is not None)
        controller.current_account = None
        self.assertIsNone(manage_existing.current_account)
        # let's try to delete this "None account"
        delete_button_id = manage_existing.ids.delete_button_id
        delete_button_id.dispatch('on_release')
        # an error dialog should pop
        dialogs = Dialog.dialogs
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'No account selected.')
        Dialog.dismiss_all_dialogs()

    def helper_confirm_account_deletion(self, app):
        """
        Helper method for confirming account deletion popups.
        """
        controller = app.controller
        manage_existing = controller.manage_existing
        # a confirmation popup should show
        dialogs = Dialog.dialogs
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'Are you sure?')
        # confirm it
        # TODO: click on the dialog action button itself
        manage_existing.on_delete_account_yes(dialog)
        # the dialog should be replaced by another one
        dialogs = Dialog.dialogs
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'Account deleted, redirecting...')
        Dialog.dismiss_all_dialogs()
        self.assertEqual(len(dialogs), 0)

    def helper_test_delete_account_twice(self, app):
        """
        Trying to delete the same account twice, shoult not crash the app,
        refs #51.
        """
        controller = app.controller
        pywalib = controller.pywalib
        manage_existing = controller.manage_existing
        # makes sure an account is selected
        pywalib.new_account(password="password", security_ratio=None)
        controller.current_account = pywalib.get_account_list()[0]
        self.assertTrue(manage_existing.current_account is not None)
        account_count_before = len(pywalib.get_account_list())
        # let's try to delete this account once
        delete_button_id = manage_existing.ids.delete_button_id
        delete_button_id.dispatch('on_release')
        self.helper_confirm_account_deletion(app)
        # the account should be deleted
        self.assertEqual(
            len(pywalib.get_account_list()), account_count_before - 1)
        # makes sure the account was also cleared from the selection view
        switch_account = self.helper_load_switch_account(app)
        account_list_id = switch_account.ids.account_list_id
        self.assertEqual(
            len(account_list_id.children), len(pywalib.get_account_list()))
        # TODO: the selected account should now be None
        # self.assertIsNone(manage_existing.current_account)
        # self.assertIsNone(controller.current_account)
        # let's try to delete this account a second time
        delete_button_id = manage_existing.ids.delete_button_id
        delete_button_id.dispatch('on_release')
        # TODO: the second time an error dialog should pop
        # dialogs = Dialog.dialogs
        # self.assertEqual(len(dialogs), 1)
        # dialog = dialogs[0]
        # self.assertEqual(dialog.title, 'No account selected.')
        Dialog.dismiss_all_dialogs()

    def helper_test_dismiss_dialog_twice(self, app):
        """
        If by some choice the dismiss event of a dialog created with
        Controller.create_dialog_helper() is fired twice, it should be
        handled gracefully, refs #89.
        """
        title = "title"
        body = "body"
        # makes sure the controller has no dialog
        self.assertEqual(Dialog.dialogs, [])
        # creates one and verifies it was created
        dialog = Dialog.create_dialog_helper(title, body)
        self.assertEqual(len(Dialog.dialogs), 1)
        # dimisses it once and verifies it was handled
        dialog.dispatch('on_dismiss')
        self.assertEqual(Dialog.dialogs, [])
        # then a second time and it should not crash
        dialog.dispatch('on_dismiss')
        self.assertEqual(Dialog.dialogs, [])

    def helper_test_controller_fetch_balance(self, app):
        """
        Verifies Controller.fetch_balance() works in most common cases.
        1) simple case, library PyWalib.get_balance() gets called
        2) ConnectionError should be handled
        3) handles 503 "service is unavailable", refs #91
        4) UnknownEtherscanException should be handled
        """
        controller = app.controller
        account = controller.current_account
        balance = 42
        # 1) simple case, library PyWalib.get_balance() gets called
        with mock.patch('pywalib.PyWalib.get_balance') as mock_get_balance, \
                patch_get_store_path(self.temp_path):
            mock_get_balance.return_value = balance
            thread = controller.fetch_balance()
            thread.join()
        address = '0x' + account.address.hex()
        mock_get_balance.assert_called_with(address, pywalib.ChainID.MAINNET)
        # and the balance updated
        self.assertEqual(
            controller.accounts_balance[address], balance)
        # 2) ConnectionError should be handled
        self.assertEqual(len(Dialog.dialogs), 0)
        with mock.patch('pywalib.PyWalib.get_balance') as mock_get_balance, \
                mock.patch('pywallet.controller.Logger') as mock_logger:
            mock_get_balance.side_effect = requests.exceptions.ConnectionError
            thread = controller.fetch_balance()
            thread.join()
        self.assertEqual(len(Dialog.dialogs), 1)
        dialog = Dialog.dialogs[0]
        self.assertEqual(dialog.title, 'Network error')
        Dialog.dismiss_all_dialogs()
        # the error should be logged
        mock_logger.warning.assert_called_with(
            'ConnectionError', exc_info=True)
        # 3) handles 503 "service is unavailable", refs #91
        self.assertEqual(len(Dialog.dialogs), 0)
        response = requests.Response()
        response.status_code = 503
        response.raw = io.BytesIO(b'The service is unavailable.')
        with mock.patch('requests.get') as mock_requests_get, \
                mock.patch('pywallet.controller.Logger') as mock_logger:
            mock_requests_get.return_value = response
            thread = controller.fetch_balance()
            thread.join()
        self.assertEqual(len(Dialog.dialogs), 1)
        dialog = Dialog.dialogs[0]
        self.assertEqual(dialog.title, 'Unknown error')
        Dialog.dismiss_all_dialogs()
        # the error should be logged
        mock_logger.error.assert_called_with(
            'UnknownEtherscanException', exc_info=True)
        # 4) UnknownEtherscanException should be handled
        self.assertEqual(len(Dialog.dialogs), 0)
        with mock.patch('pywalib.PyWalib.get_balance') as mock_get_balance, \
                mock.patch('pywallet.controller.Logger') as mock_logger:
            mock_get_balance.side_effect = pywalib.UnknownEtherscanException
            thread = controller.fetch_balance()
            thread.join()
        self.assertEqual(len(Dialog.dialogs), 1)
        dialog = Dialog.dialogs[0]
        self.assertEqual(dialog.title, 'Unknown error')
        Dialog.dismiss_all_dialogs()
        # the error should be logged
        mock_logger.error.assert_called_with(
            'UnknownEtherscanException', exc_info=True)

    def helper_test_delete_last_account(self, app):
        """
        Trying to delete the last account, should not crash the app,
        refs #120.
        """
        controller = app.controller
        pywalib = controller.pywalib
        manage_existing = controller.manage_existing
        # makes sure there's only one account left
        self.assertEqual(
            len(pywalib.get_account_list()), 1)
        # deletes it
        delete_button_id = manage_existing.ids.delete_button_id
        delete_button_id.dispatch('on_release')
        # a confirmation popup should show
        dialogs = Dialog.dialogs
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'Are you sure?')
        # confirm it
        manage_existing.on_delete_account_yes(dialog)
        # account was deleted dialog message
        dialogs = Dialog.dialogs
        self.assertEqual(len(dialogs), 1)
        dialog = dialogs[0]
        self.assertEqual(dialog.title, 'Account deleted, redirecting...')
        Dialog.dismiss_all_dialogs()
        self.advance_frames(1)
        # verifies the account was deleted
        self.assertEqual(len(pywalib.get_account_list()), 0)
        # this should be done by the events, but doesn't seem to happen
        # so we have to trigger it manually
        controller.history.current_account = None
        self.advance_frames(1)

    def helper_test_about(self, app):
        """
        Verifies the about screen loads properly, refs #126
        refs #120.
        """
        controller = app.controller
        controller.load_about_screen()
        self.advance_frames(60)
        # simply checking the about class loads
        self.assertEqual(
            str(controller.about.__class__), "<class 'kivy.factory.About'>")

    def helper_test_flashqrcode(self, app):
        """
        Verifies the flash QRCode screen loads and can flash codes.
        """
        controller = app.controller
        controller.load_flash_qr_code()
        self.advance_frames(1)
        screen_manager = controller.screen_manager
        self.assertEqual(screen_manager.current, 'flashqrcode')
        flashqrcode_screen = screen_manager.get_screen('flashqrcode')
        zbarcam = flashqrcode_screen.ids.zbarcam_id
        fixture_path = os.path.join(FIXTURE_DIR, 'one_qr_code.png')
        texture = Image(fixture_path).texture
        camera = mock.Mock(texture=texture)
        zbarcam._on_texture(camera)
        send = controller.send
        self.assertEqual(send.send_to_address, 'zbarlight test qr code')

    # main test function
    def run_test(self, app, *args):
        Clock.schedule_interval(self.pause, 0.000001)
        self.helper_setup(app)
        self.helper_test_empty_account(app)
        self.helper_test_back_home_empty_account(app)
        self.helper_test_create_first_account(app)
        self.helper_test_create_account_form(app)
        self.helper_test_on_send_click(app)
        self.helper_test_send(app)
        self.helper_test_address_alias(app)
        self.helper_test_delete_account(app)
        self.helper_test_delete_account_none_selected(app)
        self.helper_test_delete_account_twice(app)
        self.helper_test_dismiss_dialog_twice(app)
        self.helper_test_controller_fetch_balance(app)
        self.helper_test_delete_last_account(app)
        self.helper_test_about(app)
        self.helper_test_flashqrcode(app)
        # Comment out if you are editing the test, it'll leave the
        # Window opened.
        app.stop()

    # same named function as the filename(!)
    def test_ui_base(self):
        app = main.PyWalletApp()
        p = partial(self.run_test, app)
        Clock.schedule_once(p, 0.000001)
        app.run()


if __name__ == '__main__':
    unittest.main()
