import os

from kivy.app import App
from kivy.utils import platform
from pyetheroll.constants import DEFAULT_GAS_PRICE_GWEI, ChainID

from etheroll.constants import KEYSTORE_DIR_SUFFIX
from etheroll.store import Store

NETWORK_SETTINGS = 'network'
GAS_PRICE_SETTINGS = 'gas_price'
PERSIST_KEYSTORE_SETTINGS = 'persist_keystore'


class Settings:
    """
    Screen for configuring network, gas price...
    """

    @classmethod
    def get_stored_network(cls):
        """
        Retrieves last stored network value, defaults to Mainnet.
        """
        store = Store.get_store()
        try:
            network_dict = store[NETWORK_SETTINGS]
        except KeyError:
            network_dict = {}
        network_name = network_dict.get(
            'value', ChainID.MAINNET.name)
        network = ChainID[network_name]
        return network

    @classmethod
    def set_stored_network(cls, network: ChainID):
        """
        Persists network settings.
        """
        store = Store.get_store()
        store.put(NETWORK_SETTINGS, value=network.name)

    @classmethod
    def is_stored_mainnet(cls):
        network = cls.get_stored_network()
        return network == ChainID.MAINNET

    @classmethod
    def is_stored_testnet(cls):
        network = cls.get_stored_network()
        return network == ChainID.ROPSTEN

    @classmethod
    def get_stored_gas_price(cls):
        """
        Retrieves stored gas price value, defaults to DEFAULT_GAS_PRICE_GWEI.
        """
        store = Store.get_store()
        try:
            gas_price_dict = store[GAS_PRICE_SETTINGS]
        except KeyError:
            gas_price_dict = {}
        gas_price = gas_price_dict.get(
            'value', DEFAULT_GAS_PRICE_GWEI)
        return gas_price

    @classmethod
    def set_stored_gas_price(cls, gas_price: int):
        """
        Persists gas price settings.
        """
        store = Store.get_store()
        store.put(GAS_PRICE_SETTINGS, value=gas_price)

    @classmethod
    def is_persistent_keystore(cls):
        """
        Retrieves the settings value regarding the keystore persistency.
        Defaults to False.
        """
        store = Store.get_store()
        try:
            persist_keystore_dict = store[PERSIST_KEYSTORE_SETTINGS]
        except KeyError:
            persist_keystore_dict = {}
        persist_keystore = persist_keystore_dict.get(
            'value', False)
        return persist_keystore

    @classmethod
    def set_is_persistent_keystore(cls, persist_keystore: bool):
        """
        Saves keystore persistency settings.
        """
        store = Store.get_store()
        store.put(PERSIST_KEYSTORE_SETTINGS, value=persist_keystore)

    @staticmethod
    def get_persistent_keystore_path():
        app = App.get_running_app()
        # TODO: hardcoded path, refs:
        # https://github.com/AndreMiras/EtherollApp/issues/145
        return os.path.join('/sdcard', app.name)

    @staticmethod
    def get_non_persistent_keystore_path():
        app = App.get_running_app()
        return app.user_data_dir

    @classmethod
    def _get_android_keystore_prefix(cls):
        """
        Returns the Android keystore path prefix.
        The location differs based on the persistency user settings.
        """
        if cls.is_persistent_keystore():
            keystore_dir_prefix = cls.get_persistent_keystore_path()
        else:
            keystore_dir_prefix = cls.get_non_persistent_keystore_path()
        return keystore_dir_prefix

    @classmethod
    def get_keystore_path(cls):
        """
        Returns the keystore directory path.
        This can be overriden by the `KEYSTORE_PATH` environment variable.
        """
        keystore_path = os.environ.get('KEYSTORE_PATH')
        if keystore_path is not None:
            return keystore_path
        KEYSTORE_DIR_PREFIX = os.path.expanduser("~")
        if platform == "android":
            KEYSTORE_DIR_PREFIX = cls._get_android_keystore_prefix()
        keystore_path = os.path.join(
            KEYSTORE_DIR_PREFIX, KEYSTORE_DIR_SUFFIX)
        return keystore_path
