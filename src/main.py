#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import re
from threading import Thread

import kivy
from ethereum.utils import normalize_address
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.metrics import dp
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.utils import platform
from kivymd.button import MDIconButton
from kivymd.dialog import MDDialog
from kivymd.label import MDLabel
from kivymd.list import ILeftBodyTouch, OneLineListItem, TwoLineIconListItem
from kivymd.snackbar import Snackbar
from kivymd.textfields import MDTextField
from kivymd.theming import ThemeManager
from kivymd.toolbar import Toolbar
from requests.exceptions import ConnectionError

from pywalib import (InsufficientFundsException, NoTransactionFoundException,
                     PyWalib, UnknownEtherscanException)

kivy.require('1.10.0')


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
        Controller.snackbar_message("Sent!")

    def _start_unlock_send_transaction_thread(self):
        """
        Runs unlock_send_transaction() in a thread.
        """
        thread = Thread(target=self.unlock_send_transaction)
        thread.start()

    def on_password(self, instance, password):
        self._start_unlock_send_transaction_thread()


class Receive(BoxLayout):

    current_account = ObjectProperty(None, allownone=True)
    current_account_string = StringProperty()

    def __init__(self, **kwargs):
        super(Receive, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Default state setup.
        """
        self.controller = App.get_running_app().controller
        self.current_account = self.controller.pywalib.get_main_account()

    def show_address(self, address):
        self.ids.qr_code_id.data = address

    def on_current_account_string(self, instance, address):
        self.show_address(address)

    def on_current_account(self, instance, account):
        address = "0x" + account.address.encode("hex")
        self.current_account_string = address

    def open_account_list(self):
        def on_selected_item(instance, value):
            self.current_account = value.account
        self.controller.open_account_list_helper(on_selected_item)


class History(BoxLayout):

    current_account = ObjectProperty(None, allownone=True)

    def on_current_account(self, instance, account):
        print("History.on_current_account:")
        self._start_load_history_thread()

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

    def _load_history(self):
        account = self.current_account
        address = '0x' + account.address.encode("hex")
        try:
            transactions = PyWalib.get_transaction_history(address)
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

    def _start_load_history_thread(self):
        """
        Runs _load_history() in a thread.
        """
        load_history_thread = Thread(target=self._load_history)
        load_history_thread.start()


class Overview(BoxLayout):

    current_account = ObjectProperty(None, allownone=True)
    current_account_string = StringProperty()

    def on_current_account(self, instance, account):
        address = "0x" + account.address.encode("hex")
        self.current_account_string = address

    def open_account_list(self):
        controller = App.get_running_app().controller
        controller.open_account_list_overview()


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


class ManageExisting(BoxLayout):

    current_account = ObjectProperty(None, allownone=True)
    current_account_string = StringProperty()

    def __init__(self, **kwargs):
        super(ManageExisting, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Default state setup.
        """
        self.controller = App.get_running_app().controller
        self.current_account = self.controller.pywalib.get_main_account()

    def on_current_account(self, instance, account):
        address = "0x" + account.address.encode("hex")
        self.current_account_string = address

    def open_account_list(self):
        def on_selected_item(instance, value):
            self.current_account = value.account
        self.controller.open_account_list_helper(on_selected_item)


class ManageKeystore(BoxLayout):

    keystore_path = StringProperty()

    def __init__(self, **kwargs):
        super(ManageKeystore, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        pass


class CreateNewAccount(BoxLayout):
    """
    PBKDF2 iterations choice is a security vs speed trade off:
    https://security.stackexchange.com/q/3959
    """

    password1 = StringProperty()
    password2 = StringProperty()

    def __init__(self, **kwargs):
        super(CreateNewAccount, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Sets security vs speed default values.
        """
        self.security_slider = self.ids.security_slider_id
        self.speed_slider = self.ids.speed_slider_id
        self.security_slider.value = self.speed_slider.value = 50
        self.controller = App.get_running_app().controller

    def verify_password_field(self):
        """
        Makes sure passwords are matching.
        """
        # if self.password1 != self.password2:
        #     raise ValueError("Password not matching")
        return self.password1 == self.password2

    def verify_fields(self):
        """
        Verifies password fields are valid.
        """
        return self.verify_password_field()

    @property
    def security_slider_value(self):
        return self.security_slider.value

    def try_unlock(self, account, password):
        """
        Just as a security measure, verifies we can unlock
        the newly created account with provided password.
        """
        # making sure it's locked first
        account.lock()
        Controller.snackbar_message("Unlocking account...")
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
        Controller.snackbar_message("Unlocked!")

    def create_account(self):
        """
        Creates an account from provided form.
        Verify we can unlock it.
        """
        if not self.verify_fields():
            Controller.show_invalid_form_dialog()
            return
        pywalib = self.controller.pywalib
        password = self.password1
        security_ratio = self.security_slider_value
        Controller.snackbar_message("Creating account...")
        account = pywalib.new_account(
                password=password, security_ratio=security_ratio)
        self.try_unlock(account, password)
        return account

    def start_create_account_thread(self):
        """
        Runs create_account() in a thread.
        """
        load_balance_thread = Thread(target=self.create_account)
        load_balance_thread.start()


class PWToolbar(Toolbar):

    def __init__(self, **kwargs):
        super(PWToolbar, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        self.controller = App.get_running_app().controller
        self.navigation = self.controller.ids.navigation_id
        self.screen_manager = self.controller.ids.screen_manager_id
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


class About(BoxLayout):

    project_page_property = StringProperty(
        "https://github.com/AndreMiras/PyWallet")
    about_text_property = StringProperty()

    def __init__(self, **kwargs):
        super(About, self).__init__(**kwargs)
        self.about_text_property = "" + \
            "Project source code and info available on GitHub at: \n" + \
            "[color=00BFFF][ref=github]" + \
            self.project_page_property + \
            "[/ref][/color]"


class Controller(FloatLayout):

    current_account = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
        keystore_path = Controller.get_keystore_path()
        self.pywalib = PyWalib(keystore_path)
        self.load_landing_page()

    @property
    def overview(self):
        return self.ids.overview_id

    @property
    def history(self):
        return self.overview.ids.history_id

    def open_account_list_helper(self, on_selected_item):
        title = "Select account"
        items = []
        pywalib = self.pywalib
        account_list = pywalib.get_account_list()
        for account in account_list:
            address = '0x' + account.address.encode("hex")
            item = OneLineListItem(text=address)
            item.account = account
            items.append(item)
        dialog = Controller.create_list_dialog(
            title, items, on_selected_item)
        dialog.open()

    def open_account_list_overview(self):
        def on_selected_item(instance, value):
            self.set_current_account(value.account)
        self.open_account_list_helper(on_selected_item)

    def set_current_account(self, account):
        self.current_account = account

    def on_current_account(self, instance, value):
        """
        Updates Overview.current_account and History.current_account,
        then fetch account data.
        """
        self.overview.current_account = value
        self.history.current_account = value
        self._start_load_balance_thread()

    @staticmethod
    def show_invalid_form_dialog():
        title = "Invalid form"
        body = "Please check form fields."
        dialog = Controller.create_dialog(title, body)
        dialog.open()

    @staticmethod
    def get_keystore_path():
        """
        This is the Kivy default keystore path.
        """
        default_keystore_path = PyWalib.get_default_keystore_path()
        if platform != "android":
            return default_keystore_path
        # makes sure the leading slash gets removed
        default_keystore_path = default_keystore_path.strip('/')
        user_data_dir = App.get_running_app().user_data_dir
        # preprends with kivy user_data_dir
        keystore_path = os.path.join(
            user_data_dir, default_keystore_path)
        return keystore_path

    @staticmethod
    def create_list_dialog(title, items, on_selected_item):
        """
        Creates a dialog from given title and list.
        items is a list of BaseListItem objects.
        """
        # select_list = PWSelectList(items=items, on_release=on_release)
        select_list = PWSelectList(items=items)
        select_list.bind(selected_item=on_selected_item)
        content = select_list
        dialog = MDDialog(
                        title=title,
                        content=content,
                        size_hint=(.8, .8))
        # workaround for MDDialog container size (too small by default)
        dialog.ids.container.size_hint_y = 1
        # close the dialog as we select the element
        select_list.bind(
            selected_item=lambda instance, value: dialog.dismiss())
        dialog.add_action_button(
                "Dismiss",
                action=lambda *x: dialog.dismiss())
        return dialog

    @staticmethod
    def create_dialog(title, body):
        """
        Creates a dialog from given title and body.
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
                        height=dp(200),
                        auto_dismiss=False)
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
    def update_balance_label(self, balance):
        overview_id = self.ids.overview_id
        balance_label_id = overview_id.ids.balance_label_id
        balance_label_id.text = '%s ETH' % balance

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
            self.ids.screen_manager_id.current = "overview"
            self.ids.screen_manager_id.transition.direction = "right"
        except IndexError:
            self.load_manage_keystores()

    def _load_balance(self):
        account = self.current_account
        try:
            balance = self.pywalib.get_balance(account.address.encode("hex"))
        except ConnectionError:
            Controller.on_balance_connection_error()
            return
        self.update_balance_label(balance)

    def _start_load_balance_thread(self):
        """
        Runs _load_balance() in a thread.
        """
        load_balance_thread = Thread(target=self._load_balance)
        load_balance_thread.start()

    def load_manage_keystores(self):
        """
        Loads the manage keystores screen.
        """
        self.ids.screen_manager_id.transition.direction = "left"
        self.ids.screen_manager_id.current = 'manage_keystores'

    def load_about_screen(self):
        """
        Loads the about screen.
        """
        self.ids.screen_manager_id.transition.direction = "left"
        self.ids.screen_manager_id.current = "about"


class ControllerApp(App):
    theme_cls = ThemeManager()

    def __init__(self, **kwargs):
        super(ControllerApp, self).__init__(**kwargs)
        self._controller = None

    def build(self):
        self._controller = Controller(info='PyWallet')
        return self._controller

    @property
    def controller(self):
        return self._controller


if __name__ == '__main__':
    ControllerApp().run()
