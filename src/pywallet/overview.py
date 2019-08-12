from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

from pywallet.utils import load_kv_from_py

load_kv_from_py(__file__)


class OverviewScreen(Screen):

    title_property = StringProperty()

    def set_title(self, title):
        self.title_property = title


class Overview(BoxLayout):

    current_account = ObjectProperty(allownone=True)
    current_account_string = StringProperty()

    def __init__(self, **kwargs):
        super(Overview, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Binds Controller current_account and on_alias_updated.
        """
        self.controller = App.get_running_app().controller
        self.controller.bind(current_account=self.setter('current_account'))
        self.controller.bind(on_alias_updated=self.on_alias_updated)
        # triggers the update
        self.current_account = self.controller.current_account

    def update_current_account_string(self):
        """
        Updates current_account_string from current_account.
        """
        if self.current_account is None:
            return
        account = self.current_account
        address = "0x" + account.address.hex()
        self.current_account_string = address

    def on_current_account(self, instance, account):
        """
        Updates current_account_string and fetches the new account balance.
        """
        self.update_current_account_string()
        self.controller.fetch_balance()

    def on_alias_updated(self, instance, alias):
        """
        Forces account string update, which will triggers an
        AddressButton.on_address_property event.
        """
        self.current_account_string = ""
        self.update_current_account_string()
