#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import kivy
kivy.require('1.10.0')
from kivy.utils import platform
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivymd.list import MDList, OneLineListItem
from kivymd.theming import ThemeManager
from kivy.clock import Clock


from pywalib import PyWalib


class Receive(BoxLayout):

    def __init__(self, **kwargs):
        super(Receive, self).__init__(**kwargs)
        self.pywalib = PyWalib()
        Clock.schedule_once(self._load_address_list)

    def show_address(self, address):
        self.ids.qr_code_id.data = address

    def _load_address_list(self, dt=None):
        account_list = self.pywalib.get_account_list()
        for account in account_list:
            address = '0x' + account.address.encode("hex")
            item = OneLineListItem(text=address, on_release=lambda x: self.show_address(x.text))
            address_list_id = self.ids.address_list_id
            address_list_id.add_widget(item)


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
        pywalib_default_keystore_path = PyWalib.get_default_keystore_path()
        if platform != "android":
            return pywalib_default_keystore_path
        # makes sure the leading slash gets removed
        pywalib_default_keystore_path = pywalib_default_keystore_path.strip('/')
        user_data_dir = App.get_running_app().user_data_dir
        # preprends with kivy user_data_dir
        keystore_path = os.path.join(
            user_data_dir, pywalib_default_keystore_path)
        return keystore_path

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
        balance = self.pywalib.get_balance(account.address.encode("hex"))
        overview_id = self.ids.overview_id
        balance_label_id = overview_id.ids.balance_label_id
        balance_label_id.text = 'Balance: %s' % balance

    def _load_manage_keystores(self):
        """
        Loads the manage keystores screen.
        """
        self.ids.screen_manager_id.current = 'manage_keystores'


class ControllerApp(App):
    theme_cls = ThemeManager()

    def build(self):
        return Controller(info='Hello world')


if __name__ == '__main__':
    ControllerApp().run()
