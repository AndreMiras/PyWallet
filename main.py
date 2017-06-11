#!/usr/bin/env python
# -*- coding: utf-8 -*-
import kivy
kivy.require('1.10.0')

from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty
from kivymd.theming import ThemeManager
from kivy.clock import Clock


import pywalib


class Controller(FloatLayout):

    balance_label = ObjectProperty()

    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
        Clock.schedule_once(self._load_balance)

    def _load_balance(self, dt=None):
        account = pywalib.get_main_account()
        balance = pywalib.get_balance(account.address.encode("hex"))
        overview_id = self.ids.overview_id
        balance_label_id = overview_id.ids.balance_label_id
        balance_label_id.text = 'Balance: %s' % balance


class ControllerApp(App):
    theme_cls = ThemeManager()

    def build(self):
        return Controller(info='Hello world')


if __name__ == '__main__':
    ControllerApp().run()
