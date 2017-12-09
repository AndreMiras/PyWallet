from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

from kivymd.dialog import MDDialog

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

    @classmethod
    def create_alias_dialog(cls, account):
        """
        Creates the update alias dialog.
        """
        title = "Update your alias"
        content = cls(account)
        dialog = MDDialog(
                        title=title,
                        content=content,
                        size_hint=(.8, None),
                        height=dp(250),
                        auto_dismiss=False)
        # workaround for MDDialog container size (too small by default)
        dialog.ids.container.size_hint_y = 1
        return dialog
