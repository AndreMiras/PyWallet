from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.logger import Logger
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.list import TwoLineIconListItem
from requests.exceptions import ConnectionError

from pywalib import NoTransactionFoundException, PyWalib
from pywallet.utils import Dialog, load_kv_from_py, run_in_thread
from pywallet.list import IconLeftWidget


load_kv_from_py(__file__)


class History(BoxLayout):

    current_account = ObjectProperty(allownone=True)

    def __init__(self, **kwargs):
        super(History, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Binds Controller.current_account property.
        """
        self.controller = App.get_running_app().controller
        self.controller.bind(current_account=self.setter('current_account'))
        # triggers the update
        self.current_account = self.controller.current_account
        self.controller.bind(accounts_history=self.update_history_list)

    def on_current_account(self, instance, account):
        """
        Updates with last known (cached values) and update the cache.
        """
        self.update_history_list()
        self.fetch_history()

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

    @classmethod
    def create_item_from_dict(cls, transaction_dict):
        """
        Creates a history list item from a transaction dictionary.
        """
        extra_dict = transaction_dict['extra_dict']
        sent = extra_dict['sent']
        amount = extra_dict['value_eth']
        from_address = extra_dict['from_address']
        to_address = extra_dict['to_address']
        from_to = to_address if sent else from_address
        list_item = cls.create_item(sent, amount, from_to)
        return list_item

    @mainthread
    def update_history_list(self, instance=None, value=None):
        """
        Updates the history list widget from last known (cached) values.
        """
        if self.current_account is None:
            return
        address = '0x' + self.current_account.address.encode("hex")
        try:
            transactions = self.controller.accounts_history[address]
        except KeyError:
            transactions = []
        # new transactions first, but do not change the list using reverse()
        transactions = transactions[::-1]
        history_list_id = self.ids.history_list_id
        history_list_id.clear_widgets()
        for transaction in transactions:
            list_item = History.create_item_from_dict(transaction)
            history_list_id.add_widget(list_item)

    @run_in_thread
    def fetch_history(self):
        if self.current_account is None:
            return
        address = '0x' + self.current_account.address.encode("hex")
        try:
            transactions = PyWalib.get_transaction_history(address)
        except ConnectionError:
            Dialog.on_history_connection_error()
            Logger.warning('ConnectionError', exc_info=True)
            return
        except NoTransactionFoundException:
            transactions = []
        except ValueError:
            # most likely the JSON object could not be decoded, refs #91
            Dialog.on_history_value_error()
            # currently logged as an error, because we want more insight
            # in order to eventually handle it more specifically
            Logger.error('ValueError', exc_info=True)
            return
        # triggers accounts_history observers update
        self.controller.accounts_history[address] = transactions
