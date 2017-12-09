from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

from kivymd.list import OneLineListItem

from pywallet.utils import load_kv_from_py

load_kv_from_py(__file__)


class SwitchAccountScreen(Screen):
    pass


class SwitchAccount(BoxLayout):

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
        # circular ref
        from pywallet.controller import Controller
        address = "0x" + account.address.encode("hex")
        # gets the alias if exists
        try:
            text = Controller.get_address_alias(address)
        except KeyError:
            text = address
        list_item = OneLineListItem(text=text)
        # makes sure the address doesn't overlap on small screen
        list_item.ids._lbl_primary.shorten = True
        list_item.account = account
        list_item.bind(on_release=lambda x: self.on_release(x))
        return list_item

    def load_account_list(self):
        """
        Fills account list widget from library account list.
        """
        self.controller = App.get_running_app().controller
        account_list_id = self.ids.account_list_id
        account_list_id.clear_widgets()
        accounts = self.controller.pywalib.get_account_list()
        for account in accounts:
            list_item = self.create_item(account)
            account_list_id.add_widget(list_item)
