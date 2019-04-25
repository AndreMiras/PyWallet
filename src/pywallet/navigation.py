# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivymd.list import TwoLineListItem
from kivymd.navigationdrawer import NavigationDrawerHeaderBase

from pywallet.utils import load_kv_from_py


load_kv_from_py(__file__)


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
        # e.g. deleting the last account, would set
        # Controller.current_account to None
        if account is None:
            return
        address = "0x" + account.address.encode("hex")
        self.address_property = address

    def _update_specific_text_color(self, instance, value):
        pass

    def _set_active(self, active, list):
        pass
