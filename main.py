#!/usr/bin/env python
# -*- coding: utf-8 -*-
import kivy
kivy.require('1.10.0')

from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty
import pywalib


class Controller(FloatLayout):
    balance_label = ObjectProperty()

    def do_action(self):
        account = pywalib.get_main_account()
        balance = pywalib.get_balance(account.address.encode("hex"))
        self.balance_label.text = 'Balance: %s' % balance


class ControllerApp(App):

    def build(self):
        return Controller(info='Hello world')


if __name__ == '__main__':
    ControllerApp().run()
