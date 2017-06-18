#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os

import re
import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.utils import platform
from kivymd.button import MDIconButton
from kivymd.dialog import MDDialog
from kivymd.label import MDLabel
from kivymd.list import ILeftBodyTouch, OneLineListItem, TwoLineIconListItem
from kivymd.textfields import MDTextField
from kivymd.theming import ThemeManager
from ethereum.utils import normalize_address
from requests.exceptions import ConnectionError

from pywalib import PyWalib

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


class Send(BoxLayout):

    def verify_to_address_field(self):
        send_to_address_id = self.ids.send_to_address_id
        title = "Input error"
        body = "Invalid address field"
        try:
            normalize_address(send_to_address_id.text)
        except Exception:
            dialog = Controller.create_dialog(title, body)
            dialog.open()
            return False
        return True

    def verify_amount_field(self):
        send_amount_id = self.ids.send_amount_id
        title = "Input error"
        body = "Invalid amount field"
        if float(send_amount_id) == 0:
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

    def on_send_click(self):
        # TODO
        if self.verify_fields():
            pass
        Controller.show_not_implemented_dialog()


class Receive(BoxLayout):

    def __init__(self, **kwargs):
        super(Receive, self).__init__(**kwargs)
        Clock.schedule_once(self._load_address_list)

    def show_address(self, address):
        self.ids.qr_code_id.data = address

    def _load_address_list(self, dt=None):
        pywalib = App.get_running_app().controller.pywalib
        account_list = pywalib.get_account_list()
        address_list_id = self.ids.address_list_id
        for account in account_list:
            address = '0x' + account.address.encode("hex")
            item = OneLineListItem(
                text=address, on_release=lambda x: self.show_address(x.text))
            address_list_id.add_widget(item)
        # by default select the first address
        address = '0x' + account_list[0].address.encode("hex")
        self.show_address(address)


class History(BoxLayout):

    def __init__(self, **kwargs):
        super(History, self).__init__(**kwargs)
        Clock.schedule_once(self._load_history)

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

    def _load_history(self, dt=None):
        pywalib = App.get_running_app().controller.pywalib
        account = pywalib.get_main_account()
        address = '0x' + account.address.encode("hex")
        try:
            transactions = pywalib.get_transaction_history(address)
        except ConnectionError:
            Controller.on_history_connection_error()
            return
        history_list_id = self.ids.history_list_id
        for transaction in transactions:
            list_item = History.create_item_from_dict(transaction)
            history_list_id.add_widget(list_item)


class Controller(FloatLayout):

    balance_label = ObjectProperty()

    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
        keystore_path = Controller.get_keystore_path()
        self.pywalib = PyWalib(keystore_path)
        Clock.schedule_once(self._load_landing_page)

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

    def _load_landing_page(self, dt=None):
        """
        Loads the landing page.
        """
        try:
            self._load_balance()
        except IndexError:
            self._load_manage_keystores()

    def _load_balance(self):
        account = self.pywalib.get_main_account()
        try:
            balance = self.pywalib.get_balance(account.address.encode("hex"))
        except ConnectionError:
            Controller.on_balance_connection_error()
            return
        overview_id = self.ids.overview_id
        balance_label_id = overview_id.ids.balance_label_id
        balance_label_id.text = '%s ETH' % balance

    def _load_manage_keystores(self):
        """
        Loads the manage keystores screen.
        """
        self.ids.screen_manager_id.current = 'manage_keystores'


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
