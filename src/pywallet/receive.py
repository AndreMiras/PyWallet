from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

from pywallet.utils import load_kv_from_py

load_kv_from_py(__file__)


class Receive(BoxLayout):

    current_account = ObjectProperty(allownone=True)
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
        Binds Controller current_account and on_alias_updated.
        """
        self.controller = App.get_running_app().controller
        self.controller.bind(current_account=self.setter('current_account'))
        self.controller.bind(on_alias_updated=self.on_alias_updated)
        # triggers the update
        self.current_account = self.controller.current_account

    def show_address(self, address):
        self.ids.qr_code_id.data = address

    def update_address_property(self):
        """
        Updates address_property from current_account.
        """
        account = self.current_account
        address = "0x" + account.address.hex()
        self.address_property = address

    def on_current_account(self, instance, account):
        if account is None:
            return
        self.update_address_property()

    def on_address_property(self, instance, value):
        self.show_address(value)

    def on_alias_updated(self, instance, alias):
        """
        Forces account string update, which will triggers an
        AddressButton.on_address_property event.
        """
        self.address_property = ""
        self.update_address_property()
