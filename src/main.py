#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
import re
import unittest
from io import StringIO
from threading import Thread

import kivy
from ethereum.utils import normalize_address
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.logger import LOG_LEVELS, Logger
from kivy.metrics import dp
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
from kivymd.button import MDFlatButton, MDIconButton
from kivymd.dialog import MDDialog
from kivymd.label import MDLabel
from kivymd.list import (ILeftBodyTouch, OneLineListItem, TwoLineIconListItem,
                         TwoLineListItem)
from kivymd.navigationdrawer import NavigationDrawerHeaderBase
from kivymd.snackbar import Snackbar
from kivymd.textfields import MDTextField
from kivymd.theming import ThemeManager
from kivymd.toolbar import Toolbar
from raven import Client
from requests.exceptions import ConnectionError

from pywalib import (InsufficientFundsException, NoTransactionFoundException,
                     PyWalib, UnknownEtherscanException)
from testsuite import suite

kivy.require('1.10.0')


def run_in_thread(fn):
    """
    Decorator to run a function in a thread.
    >>> 1 + 1
    2
    >>> @run_in_thread
    ... def threaded_sleep(seconds):
    ...     from time import sleep
    ...     sleep(seconds)
    >>> thread = threaded_sleep(0.1)
    >>> type(thread)
    <class 'threading.Thread'>
    >>> thread.is_alive()
    True
    >>> thread.join()
    >>> thread.is_alive()
    False
    """
    def run(*k, **kw):
        t = Thread(target=fn, args=k, kwargs=kw)
        t.start()
        return t
    return run


class NavigationDrawerTwoLineListItem(
        TwoLineListItem, NavigationDrawerHeaderBase):

    address_property = StringProperty()

    def __init__(self, **kwargs):
        super(NavigationDrawerTwoLineListItem, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Binds Controller.current_account property.
        """
        self.controller = App.get_running_app().controller
        self.controller.bind(
            current_account=lambda _, value: self.on_current_account(value))

    def on_current_account(self, account):
        address = "0x" + account.address.encode("hex")
        self.address_property = address

    def _update_specific_text_color(self, instance, value):
        pass

    def _set_active(self, active, list):
        pass


class IconLeftWidget(ILeftBodyTouch, MDIconButton):
    pass


class FloatInput(MDTextField):
    """
    Accepts float numbers only.
    """

    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super(FloatInput, self).insert_text(s, from_undo=from_undo)


class PasswordForm(BoxLayout):

    password = StringProperty()

    def __init__(self, **kwargs):
        super(PasswordForm, self).__init__(**kwargs)


class Send(BoxLayout):

    password = StringProperty("")
    send_to_address = StringProperty("")
    send_amount = NumericProperty(0)

    def __init__(self, **kwargs):
        super(Send, self).__init__(**kwargs)

    def verify_to_address_field(self):
        title = "Input error"
        body = "Invalid address field"
        try:
            normalize_address(self.send_to_address)
        except Exception:
            dialog = Controller.create_dialog(title, body)
            dialog.open()
            return False
        return True

    def verify_amount_field(self):
        title = "Input error"
        body = "Invalid amount field"
        if self.send_amount == 0:
            dialog = Controller.create_dialog(title, body)
            dialog.open()
            return False
        return True

    def verify_fields(self):
        """
        Verifies address and amount fields are valid.
        """
        return self.verify_to_address_field() \
            and self.verify_amount_field()

    def on_unlock_clicked(self, dialog, password):
        self.password = password
        dialog.dismiss()

    def prompt_password_dialog(self):
        """
        Prompt the password dialog.
        """
        title = "Enter your password"
        content = PasswordForm()
        dialog = MDDialog(
                        title=title,
                        content=content,
                        size_hint=(.8, None),
                        height=dp(250),
                        auto_dismiss=False)
        # workaround for MDDialog container size (too small by default)
        dialog.ids.container.size_hint_y = 1
        dialog.add_action_button(
                "Unlock",
                action=lambda *x: self.on_unlock_clicked(
                    dialog, content.password))
        return dialog

    def on_send_click(self):
        if not self.verify_fields():
            Controller.show_invalid_form_dialog()
            return
        dialog = self.prompt_password_dialog()
        dialog.open()

    @run_in_thread
    def unlock_send_transaction(self):
        """
        Unlocks the account with password in order to sign and publish the
        transaction.
        """
        controller = App.get_running_app().controller
        pywalib = controller.pywalib
        address = normalize_address(self.send_to_address)
        amount_eth = self.send_amount
        amount_wei = int(amount_eth * pow(10, 18))
        account = controller.pywalib.get_main_account()
        Controller.snackbar_message("Unlocking account...")
        try:
            account.unlock(self.password)
        except ValueError:
            Controller.snackbar_message("Could not unlock account")
            return

        Controller.snackbar_message("Unlocked! Sending transaction...")
        sender = account.address
        try:
            pywalib.transact(address, value=amount_wei, data='', sender=sender)
        except InsufficientFundsException:
            Controller.snackbar_message("Insufficient funds")
            return
        except UnknownEtherscanException:
            Controller.snackbar_message("Unknown error")
            return
        # TODO: handle ConnectionError
        Controller.snackbar_message("Sent!")

    def on_password(self, instance, password):
        self.unlock_send_transaction()


class Receive(BoxLayout):

    current_account = ObjectProperty()
    address_property = StringProperty()

    def __init__(self, **kwargs):
        super(Receive, self).__init__(**kwargs)
        # for some reason setting the timeout to zero
        # crashes with:
        # 'super' object has no attribute '__getattr__'
        # only on first account creation (with auto redirect)
        # and we cannot yet reproduce in unit tests
        timeout = 1
        Clock.schedule_once(lambda dt: self.setup(), timeout)

    def setup(self):
        """
        Binds Controller.current_account property.
        """
        self.controller = App.get_running_app().controller
        self.controller.bind(current_account=self.setter('current_account'))
        # triggers the update
        self.current_account = self.controller.current_account

    def show_address(self, address):
        self.ids.qr_code_id.data = address

    def on_current_account(self, instance, account):
        address = "0x" + account.address.encode("hex")
        self.address_property = address

    def on_address_property(self, instance, value):
        self.show_address(value)


class History(BoxLayout):

    current_account = ObjectProperty()

    def __init__(self, **kwargs):
        super(History, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Binds Controller.current_account property.
        """
        self.controller = App.get_running_app().controller
        self.controller.bind(current_account=self.setter('current_account'))
        # triggers the update
        self.current_account = self.controller.current_account

    def on_current_account(self, instance, account):
        self._load_history()

    @staticmethod
    def create_item(sent, amount, from_to):
        """
        Creates a history list item from parameters.
        """
        send_receive = "Sent" if sent else "Received"
        text = "%s %sETH" % (send_receive, amount)
        secondary_text = from_to
        icon = "arrow-up-bold" if sent else "arrow-down-bold"
        list_item = TwoLineIconListItem(
            text=text, secondary_text=secondary_text)
        icon_widget = IconLeftWidget(icon=icon)
        list_item.add_widget(icon_widget)
        return list_item

    @staticmethod
    def create_item_from_dict(transaction_dict):
        """
        Creates a history list item from a transaction dictionary.
        """
        extra_dict = transaction_dict['extra_dict']
        sent = extra_dict['sent']
        amount = extra_dict['value_eth']
        from_address = extra_dict['from_address']
        to_address = extra_dict['to_address']
        from_to = to_address if sent else from_address
        list_item = History.create_item(sent, amount, from_to)
        return list_item

    @mainthread
    def update_history_list(self, list_items):
        history_list_id = self.ids.history_list_id
        history_list_id.clear_widgets()
        for list_item in list_items:
            history_list_id.add_widget(list_item)

    @run_in_thread
    def _load_history(self):
        account = self.current_account
        address = '0x' + account.address.encode("hex")
        try:
            transactions = PyWalib.get_transaction_history(address)
            # new transactions first
            transactions.reverse()
        except ConnectionError:
            Controller.on_history_connection_error()
            return
        except NoTransactionFoundException:
            transactions = []
        list_items = []
        for transaction in transactions:
            list_item = History.create_item_from_dict(transaction)
            list_items.append(list_item)
        self.update_history_list(list_items)


class SwitchAccount(BoxLayout):

    def __init__(self, **kwargs):
        super(SwitchAccount, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        self.controller = App.get_running_app().controller
        self.load_account_list()

    def on_release(self, list_item):
        """
        Sets Controller.current_account and switches to previous screen.
        """
        # sets Controller.current_account
        self.selected_list_item = list_item
        self.controller.current_account = list_item.account
        # switches to previous screen
        self.controller.screen_manager_previous()

    def create_item(self, account):
        """
        Creates an account list item from given account.
        """
        address = "0x" + account.address.encode("hex")
        list_item = OneLineListItem(text=address)
        # makes sure the address doesn't overlap on small screen
        list_item.ids._lbl_primary.shorten = True
        list_item.account = account
        list_item.bind(on_release=lambda x: self.on_release(x))
        return list_item

    def load_account_list(self):
        """
        Fills account list widget from library account list.
        """
        account_list_id = self.ids.account_list_id
        account_list_id.clear_widgets()
        accounts = self.controller.pywalib.get_account_list()
        for account in accounts:
            list_item = self.create_item(account)
            account_list_id.add_widget(list_item)


class Overview(BoxLayout):

    current_account = ObjectProperty()
    current_account_string = StringProperty()

    def __init__(self, **kwargs):
        super(Overview, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Binds Controller.current_account property.
        """
        self.controller = App.get_running_app().controller
        self.controller.bind(current_account=self.setter('current_account'))
        # triggers the update
        self.current_account = self.controller.current_account

    def is_selected(self):
        """
        Returns True if the overview sub-screen is selected,
        otherwise returns False.
        """
        return self.parent.manager.current == 'overview'

    def on_current_account(self, instance, account):
        address = "0x" + account.address.encode("hex")
        self.current_account_string = address
        if self.is_selected():
            self.controller.fetch_and_update_balance()


class PWSelectList(BoxLayout):

    selected_item = ObjectProperty()

    def __init__(self, **kwargs):
        self._items = kwargs.pop('items')
        super(PWSelectList, self).__init__(**kwargs)
        self._setup()

    def on_release(self, item):
        self.selected_item = item

    def _setup(self):
        address_list = self.ids.address_list_id
        for item in self._items:
            item.bind(on_release=lambda x: self.on_release(x))
            address_list.add_widget(item)


class ImportKeystore(BoxLayout):

    keystore_path = StringProperty()

    def __init__(self, **kwargs):
        super(ImportKeystore, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        self.controller = App.get_running_app().controller
        self.keystore_path = self.controller.get_keystore_path()
        accounts = self.controller.pywalib.get_account_list()
        if len(accounts) == 0:
            title = "No keystore found."
            body = "Import or create one."
            dialog = Controller.create_dialog(title, body)
            dialog.open()


# TODO: also make it possible to update PBKDF2
# TODO: create a generic password form
# TODO: create a generic account form
class ManageExisting(BoxLayout):

    current_account = ObjectProperty()
    address_property = StringProperty()
    current_password = StringProperty()
    new_password1 = StringProperty()
    new_password2 = StringProperty()

    def __init__(self, **kwargs):
        super(ManageExisting, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Binds Controller.current_account property.
        """
        self.controller = App.get_running_app().controller
        self.pywalib = self.controller.pywalib
        self.controller.bind(current_account=self.setter('current_account'))
        # triggers the update
        self.current_account = self.controller.current_account

    def verify_current_password_field(self):
        """
        Makes sure passwords are matching.
        """
        account = self.current_account
        password = self.current_password
        # making sure it's locked first
        account.lock()
        try:
            account.unlock(password)
        except ValueError:
            return False
        return True

    def verify_password_field(self):
        """
        Makes sure passwords are matching and are not void.
        """
        passwords_matching = self.new_password1 == self.new_password2
        passwords_not_void = self.new_password1 != ''
        return passwords_matching and passwords_not_void

    def verify_fields(self):
        """
        Verifies password fields are valid.
        """
        return self.verify_password_field()

    def show_redirect_dialog(self):
        title = "Account deleted, redirecting..."
        body = ""
        body += "Your account was deleted, "
        body += "you will be redirected to the overview."
        dialog = Controller.create_dialog(title, body)
        dialog.open()

    def on_delete_account_yes(self, dialog):
        """
        Deletes the account, discarts the warning dialog,
        shows an info popup and redirects to the landing page.
        """
        account = self.current_account
        self.pywalib.delete_account(account)
        dialog.dismiss()
        self.show_redirect_dialog()
        self.controller.load_landing_page()

    def prompt_delete_account_dialog(self):
        """
        Not yet implemented.
        """
        title = "Are you sure?"
        body = ""
        body += "This action cannot be undone.\n"
        body += "Are you sure you want to delete this account?\n"
        dialog = Controller.create_dialog_helper(title, body)
        dialog.add_action_button(
                "No",
                action=lambda *x: dialog.dismiss())
        dialog.add_action_button(
                "Yes",
                action=lambda *x: self.on_delete_account_yes(dialog))
        dialog.open()

    @run_in_thread
    def update_password(self):
        """
        Update account password with new password provided.
        """
        if not self.verify_fields():
            Controller.show_invalid_form_dialog()
            return
        Controller.snackbar_message("Verifying current password...")
        if not self.verify_current_password_field():
            Controller.snackbar_message("Wrong account password")
            return
        pywalib = self.controller.pywalib
        account = self.current_account
        new_password = self.new_password1
        Controller.snackbar_message("Updating account...")
        pywalib.update_account_password(account, new_password=new_password)
        Controller.snackbar_message("Updated!")

    def on_current_account(self, instance, account):
        address = "0x" + account.address.encode("hex")
        self.address_property = address


class CreateNewAccount(BoxLayout):
    """
    PBKDF2 iterations choice is a security vs speed trade off:
    https://security.stackexchange.com/q/3959
    """

    new_password1 = StringProperty()
    new_password2 = StringProperty()

    def __init__(self, **kwargs):
        super(CreateNewAccount, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Sets security vs speed default values.
        Plus hides the advanced widgets.
        """
        self.security_slider = self.ids.security_slider_id
        self.speed_slider = self.ids.speed_slider_id
        self.security_slider.value = self.speed_slider.value = 50
        self.controller = App.get_running_app().controller
        # self.toggle_advanced(False)

    def verify_password_field(self):
        """
        Makes sure passwords are matching and are not void.
        """
        passwords_matching = self.new_password1 == self.new_password2
        passwords_not_void = self.new_password1 != ''
        return passwords_matching and passwords_not_void

    def verify_fields(self):
        """
        Verifies password fields are valid.
        """
        return self.verify_password_field()

    @property
    def security_slider_value(self):
        return self.security_slider.value

    @staticmethod
    def try_unlock(account, password):
        """
        Just as a security measure, verifies we can unlock
        the newly created account with provided password.
        """
        # making sure it's locked first
        account.lock()
        try:
            account.unlock(password)
        except ValueError:
            title = "Unlock error"
            body = ""
            body += "Couldn't unlock your account.\n"
            body += "The issue should be reported."
            dialog = Controller.create_dialog(title, body)
            dialog.open()
            return

    @mainthread
    def on_account_created(self, account):
        """
        Switches to the newly created account.
        Clears the form.
        """
        self.controller.current_account = account
        self.new_password1 = ''
        self.new_password2 = ''

    @mainthread
    def toggle_widgets(self, enabled):
        """
        Enables/disables account creation widgets.
        """
        self.disabled = not enabled

    def show_redirect_dialog(self):
        title = "Account created, redirecting..."
        body = ""
        body += "Your account was created, "
        body += "you will be redirected to the overview."
        dialog = Controller.create_dialog(title, body)
        dialog.open()

    @run_in_thread
    def create_account(self):
        """
        Creates an account from provided form.
        Verify we can unlock it.
        Disables widgets during the process, so the user doesn't try
        to create another account during the process.
        """
        self.toggle_widgets(False)
        if not self.verify_fields():
            Controller.show_invalid_form_dialog()
            self.toggle_widgets(True)
            return
        pywalib = self.controller.pywalib
        password = self.new_password1
        security_ratio = self.security_slider_value
        # dividing again by 10, because otherwise it's
        # too slow on smart devices
        security_ratio /= 10.0
        Controller.snackbar_message("Creating account...")
        account = pywalib.new_account(
                password=password, security_ratio=security_ratio)
        Controller.snackbar_message("Created!")
        self.toggle_widgets(True)
        self.on_account_created(account)
        CreateNewAccount.try_unlock(account, password)
        self.show_redirect_dialog()
        self.controller.load_landing_page()
        return account

    def toggle_advanced(self, show):
        """
        Shows/hides advanced account creation widgets.
        https://stackoverflow.com/q/23211142/185510
        """
        advanced = self.ids.advanced_id
        if not show:
            # save the old y-coordinate
            advanced.saved_y = advanced.y
            # now move the widget offscreen
            advanced.y = 5000
        else:
            advanced.y = advanced.saved_y


class AddressButton(MDFlatButton):
    """
    Overrides MDFlatButton, makes the font slightly smaller on mobile
    by using "Body1" rather than "Button" style.
    Also shorten content size using ellipsis.
    """

    def __init__(self, **kwargs):
        super(AddressButton, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        content = self.ids.content
        content.font_style = 'Body1'
        content.shorten = True

        def on_parent_size(instance, size):
            # see BaseRectangularButton.width definition
            button_margin = dp(32)
            parent_width = instance.width
            # TODO: the new size should be a min() of
            # parent_width and actual content size
            content.width = parent_width - button_margin
        self.parent.bind(size=on_parent_size)
        # call it once manually, refs:
        # https://github.com/AndreMiras/PyWallet/issues/74
        on_parent_size(self.parent, None)


class PWToolbar(Toolbar):

    title_property = StringProperty()

    def __init__(self, **kwargs):
        super(PWToolbar, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        self.controller = App.get_running_app().controller
        self.navigation = self.controller.ids.navigation_id
        self.load_default_navigation()

    def load_default_navigation(self):
        self.left_action_items = [
            ['menu', lambda x: self.toggle_nav_drawer()]
        ]
        self.right_action_items = [
            ['dots-vertical', lambda x: self.toggle_nav_drawer()]
        ]

    def toggle_nav_drawer(self):
        self.navigation.toggle_nav_drawer()


class StringIOCBWrite(StringIO):
    """
    Inherits StringIO, provides callback on write.
    """

    def __init__(self, initial_value='', newline='\n', callback_write=None):
        """
        Overloads the StringIO.__init__() makes it possible to hook a callback
        for write operations.
        """
        self.callback_write = callback_write
        super(StringIOCBWrite, self).__init__(initial_value, newline)

    def write(self, s):
        """
        Calls the StringIO.write() method then the callback_write with
        given string parameter.
        """
        # io.StringIO expects unicode
        s_unicode = s.decode('utf-8')
        super(StringIOCBWrite, self).write(s_unicode)
        if self.callback_write is not None:
            self.callback_write(s_unicode)


class ScrollableLabel(ScrollView):
    """
    https://github.com/kivy/kivy/wiki/Scrollable-Label
    """
    text = StringProperty('')


class AboutChangelog(BoxLayout):
    changelog_text_property = StringProperty()

    def __init__(self, **kwargs):
        super(AboutChangelog, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.load_changelog())

    def load_changelog(self):
        changelog_path = os.path.join(
            Controller.src_dir(),
            'CHANGELOG.md')
        with open(changelog_path, 'r') as f:
            self.changelog_text_property = f.read()
        f.close()


class AboutOverview(BoxLayout):
    project_page_property = StringProperty(
        "https://github.com/AndreMiras/PyWallet")
    about_text_property = StringProperty()

    def __init__(self, **kwargs):
        super(AboutOverview, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.load_about())

    def load_about(self):
        self.about_text_property = "" + \
            "Project source code and info available on GitHub at: \n" + \
            "[color=00BFFF][ref=github]" + \
            self.project_page_property + \
            "[/ref][/color]"


class AboutDiagnostic(BoxLayout):
    stream_property = StringProperty()

    @mainthread
    def callback_write(self, s):
        """
        Updates the UI with test progress.
        """
        self.stream_property += s

    @run_in_thread
    def run_tests(self):
        """
        Loads the test suite and hook the callback for reporting progress.
        """
        Controller.patch_keystore_path()
        test_suite = suite()
        self.stream_property = ""
        stream = StringIOCBWrite(callback_write=self.callback_write)
        verbosity = 2
        unittest.TextTestRunner(
                stream=stream, verbosity=verbosity).run(test_suite)


class OverviewScreen(Screen):

    title_property = StringProperty()

    def set_title(self, title):
        self.title_property = title


class SwitchAccountScreen(Screen):
    pass


class ManageKeystoreScreen(Screen):
    pass


class AboutScreen(Screen):
    pass


class Controller(FloatLayout):

    current_account = ObjectProperty()
    current_account_balance = NumericProperty(0)
    # keeps track of all dialogs alive
    dialogs = []

    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
        keystore_path = Controller.get_keystore_path()
        self.pywalib = PyWalib(keystore_path)
        self.screen_history = []
        Clock.schedule_once(lambda dt: self.load_landing_page())

    @property
    def overview(self):
        overview_screen = self.ids.overview_screen_id
        overview_bnavigation = overview_screen.ids.overview_bnavigation_id
        return overview_bnavigation.ids.overview_id

    @property
    def history(self):
        return self.overview.ids.history_id

    @property
    def switch_account(self):
        screen_manager = self.screen_manager
        switch_account_screen = screen_manager.get_screen('switch_account')
        switch_account_id = switch_account_screen.ids.switch_account_id
        return switch_account_id

    @property
    def send(self):
        screen_manager = self.screen_manager
        overview_screen = screen_manager.get_screen('overview')
        overview_bnavigation_id = overview_screen.ids.overview_bnavigation_id
        return overview_bnavigation_id.ids.send_id

    @property
    def manage_keystores(self):
        screen_manager = self.screen_manager
        manage_keystores_screen = screen_manager.get_screen('manage_keystores')
        manage_keystores_bnavigation_id = \
            manage_keystores_screen.ids.manage_keystores_id
        return manage_keystores_bnavigation_id

    @property
    def manage_existing(self):
        manage_keystores = self.manage_keystores
        return manage_keystores.ids.manage_existing_id

    @property
    def create_new_account(self):
        manage_keystores = self.manage_keystores
        return manage_keystores.ids.create_new_account_id

    @property
    def toolbar(self):
        return self.ids.toolbar_id

    @property
    def screen_manager(self):
        return self.ids.screen_manager_id

    def set_toolbar_title(self, title):
        self.toolbar.title_property = title

    def screen_manager_current(self, current, direction=None):
        screens = {
            'overview': OverviewScreen,
            'switch_account': SwitchAccountScreen,
            'manage_keystores': ManageKeystoreScreen,
            'about': AboutScreen,
        }
        screen_manager = self.screen_manager
        if not screen_manager.has_screen(current):
            screen = screens[current](name=current)
            screen_manager.add_widget(screen)
        if direction is not None:
            screen_manager.transition.direction = direction
        screen_manager.current = current
        self.screen_history.append(current)

    def screen_manager_previous(self):
        try:
            previous_screen = self.screen_history[-2]
        except IndexError:
            previous_screen = 'overview'
        self.screen_manager_current(previous_screen, direction='right')

    @staticmethod
    def show_invalid_form_dialog():
        title = "Invalid form"
        body = "Please check form fields."
        dialog = Controller.create_dialog(title, body)
        dialog.open()

    @staticmethod
    def patch_keystore_path():
        """
        Changes pywalib default keystore path depending on platform.
        Currently only updates it on Android.
        """
        if platform != "android":
            return
        import pywalib
        # uses kivy user_data_dir (/sdcard/<app_name>)
        pywalib.KEYSTORE_DIR_PREFIX = App.get_running_app().user_data_dir

    @staticmethod
    def get_keystore_path():
        """
        This is the Kivy default keystore path.
        """
        keystore_path = os.environ.get('KEYSTORE_PATH')
        if keystore_path is None:
            Controller.patch_keystore_path()
            keystore_path = PyWalib.get_default_keystore_path()
        return keystore_path

    @staticmethod
    def src_dir():
        return os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def on_dialog_dismiss(dialog):
        """
        Removes it from the dialogs track list.
        """
        Controller.dialogs.remove(dialog)

    @staticmethod
    def dismiss_all_dialogs():
        """
        Dispatches dismiss event for all dialogs.
        """
        dialogs = Controller.dialogs[:]
        for dialog in dialogs:
            dialog.dispatch('on_dismiss')

    @staticmethod
    def create_dialog_helper(title, body):
        """
        Creates a dialog from given title and body.
        Adds it to the dialogs track list.
        """
        content = MDLabel(
                    font_style='Body1',
                    theme_text_color='Secondary',
                    text=body,
                    size_hint_y=None,
                    valign='top')
        content.bind(texture_size=content.setter('size'))
        dialog = MDDialog(
                        title=title,
                        content=content,
                        size_hint=(.8, None),
                        height=dp(250),
                        auto_dismiss=False)
        dialog.bind(on_dismiss=Controller.on_dialog_dismiss)
        Controller.dialogs.append(dialog)
        return dialog

    @staticmethod
    def create_dialog(title, body):
        """
        Creates a dialog from given title and body.
        Adds it to the dialogs track list.
        Appends dismiss action.
        """
        dialog = Controller.create_dialog_helper(title, body)
        dialog.add_action_button(
                "Dismiss",
                action=lambda *x: dialog.dismiss())
        return dialog

    @staticmethod
    def on_balance_connection_error():
        title = "Network error"
        body = "Couldn't load balance, no network access."
        dialog = Controller.create_dialog(title, body)
        dialog.open()

    @staticmethod
    def on_history_connection_error():
        title = "Network error"
        body = "Couldn't load history, no network access."
        dialog = Controller.create_dialog(title, body)
        dialog.open()

    @staticmethod
    def show_not_implemented_dialog():
        title = "Not implemented"
        body = "This feature is not yet implemented."
        dialog = Controller.create_dialog(title, body)
        dialog.open()

    @mainthread
    def update_toolbar_title_balance(self):
        title = "%s ETH" % (self.current_account_balance)
        self.set_toolbar_title(title)

    @staticmethod
    @mainthread
    def snackbar_message(text):
        Snackbar(text=text).show()

    def load_landing_page(self):
        """
        Loads the landing page.
        """
        try:
            # will trigger account data fetching
            self.current_account = self.pywalib.get_main_account()
            self.screen_manager_current('overview')
        except IndexError:
            self.load_create_new_account()

    @run_in_thread
    def fetch_and_update_balance(self):
        """
        Fetches the new balance and updates the UI.
        """
        # pre-updates balance with last known value
        self.update_toolbar_title_balance()
        account = self.current_account
        try:
            self.current_account_balance = self.pywalib.get_balance(
                account.address.encode("hex"))
        except ConnectionError:
            Controller.on_balance_connection_error()
            return
        self.update_toolbar_title_balance()

    def load_switch_account(self):
        """
        Loads the switch account screen.
        """
        # loads the switch account screen
        self.screen_manager_current('switch_account', direction='left')

    def load_manage_keystores(self):
        """
        Loads the manage keystores screen.
        """
        # loads the manage keystores screen
        self.screen_manager_current('manage_keystores', direction='left')

    def load_create_new_account(self):
        """
        Loads the create new account tab from the maage keystores screen.
        """
        self.load_manage_keystores()
        # loads the create new account tab
        manage_keystores = self.manage_keystores
        create_new_account_nav_item = \
            manage_keystores.ids.create_new_account_nav_item_id
        create_new_account_nav_item.dispatch('on_tab_press')

    def load_about_screen(self):
        """
        Loads the about screen.
        """
        self.screen_manager_current('about', direction='left')


class DebugRavenClient(object):
    """
    The DebugRavenClient should be used in debug mode, it just raises
    the exception rather than capturing it.
    """

    def captureException(self):
        raise


class PyWalletApp(App):
    theme_cls = ThemeManager()

    def build(self):
        self.icon = "docs/images/icon.png"
        return Controller(info='PyWallet')

    @property
    def controller(self):
        return self.root


def configure_sentry(in_debug=False):
    """
    Configure the Raven client, or create a dummy one if `in_debug` is `True`.
    """
    key = 'eaee971c463b49678f6f352dfec497a9'
    # the public DSN URL is not available on the Python client
    # so we're exposing the secret and will be revoking it on abuse
    # https://github.com/getsentry/raven-python/issues/569
    secret = '4f37fdbde03a4753b78abb84d11f45ab'
    project_id = '191660'
    dsn = 'https://{key}:{secret}@sentry.io/{project_id}'.format(
        key=key, secret=secret, project_id=project_id)
    if in_debug:
        client = DebugRavenClient()
    else:
        client = Client(dsn)
    return client


if __name__ == '__main__':
    # when the -d/--debug flag is set, Kivy sets log level to debug
    level = Logger.getEffectiveLevel()
    in_debug = level == LOG_LEVELS.get('debug')
    client = configure_sentry(in_debug)
    try:
        PyWalletApp().run()
    except:
        client.captureException()
