from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

from pywallet.utils import load_kv_from_py

load_kv_from_py(__file__)


class AliasForm(BoxLayout):

    alias = StringProperty()
    address = StringProperty()

    def __init__(self, account, **kwargs):
        """
        Setups the current alias for the given account.
        """
        # circular ref
        from pywallet.controller import Controller
        super(AliasForm, self).__init__(**kwargs)
        self.address = "0x" + account.address.encode("hex")
        try:
            self.alias = Controller.get_address_alias(self.address)
        except KeyError:
            self.alias = ''
