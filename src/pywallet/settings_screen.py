import os
import shutil

from kivy.properties import BooleanProperty, NumericProperty
from pyetheroll.constants import ChainID

from etheroll.constants import KEYSTORE_DIR_SUFFIX
from etheroll.settings import Settings
from etheroll.ui_utils import SubScreen, load_kv_from_py
from etheroll.utils import (check_request_write_permission,
                            check_write_permission)

load_kv_from_py(__file__)


class SettingsScreen(SubScreen):
    """
    Screen for configuring network, gas price...
    """

    is_stored_mainnet = BooleanProperty()
    is_stored_testnet = BooleanProperty()
    stored_gas_price = NumericProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def store_network(self):
        """
        Saves selected network to the store.
        """
        network = self.get_ui_network()
        Settings.set_stored_network(network)

    def store_gas_price(self):
        """
        Saves gas price value to the store.
        """
        gas_price = self.get_ui_gas_price()
        Settings.set_stored_gas_price(gas_price)

    def store_is_persistent_keystore(self):
        """
        Saves the persistency option to the store.
        Note that to save `True` we also check if we have write permissions.
        """
        persist_keystore = self.is_ui_persistent_keystore()
        persist_keystore = persist_keystore and check_write_permission()
        persistency_toggled = (
            Settings.is_persistent_keystore() != persist_keystore)
        if persistency_toggled:
            self.sync_keystore(persist_keystore)
        Settings.set_is_persistent_keystore(persist_keystore)

    def sync_to_directory(source_dir, destination_dir):
        """
        Copy source dir content to the destination dir one.
        Files already existing get overriden.
        """
        os.makedirs(destination_dir, exist_ok=True)
        files = os.listdir(source_dir)
        for f in files:
            source_file = os.path.join(source_dir, f)
            # file path is given rather than the dir so it gets overriden
            destination_file = os.path.join(destination_dir, f)
            try:
                shutil.copy(source_file, destination_file)
            except PermissionError:
                # `copymode()` may have fail, fallback to simple copy
                shutil.copyfile(source_file, destination_file)

    @classmethod
    def sync_keystore_to_persistent(cls):
        """
        Copies keystore from non persistent to persistent storage.
        """
        # TODO: handle dir doesn't exist
        source_dir = os.path.join(
            Settings.get_non_persistent_keystore_path(),
            KEYSTORE_DIR_SUFFIX)
        destination_dir = os.path.join(
            Settings.get_persistent_keystore_path(),
            KEYSTORE_DIR_SUFFIX)
        cls.sync_to_directory(source_dir, destination_dir)

    @classmethod
    def sync_keystore_to_non_persistent(cls):
        """
        Copies keystore from persistent to non persistent storage.
        """
        # TODO: handle dir doesn't exist
        source_dir = os.path.join(
            Settings.get_persistent_keystore_path(),
            KEYSTORE_DIR_SUFFIX)
        destination_dir = os.path.join(
            Settings.get_non_persistent_keystore_path(),
            KEYSTORE_DIR_SUFFIX)
        cls.sync_to_directory(source_dir, destination_dir)

    @classmethod
    def sync_keystore(cls, to_persistent):
        if to_persistent:
            cls.sync_keystore_to_persistent()
        else:
            cls.sync_keystore_to_non_persistent()

    def set_persist_keystore_switch_state(self, active):
        """
        The MDSwitch UI look doesn't seem to be binded to its status.
        Here the UI look will be updated depending on the "active" status.
        """
        mdswitch = self.ids.persist_keystore_switch_id
        if self.is_ui_persistent_keystore() != active:
            mdswitch.ids.thumb.trigger_action()

    def load_settings(self):
        """
        Load json store settings to UI properties.
        """
        self.is_stored_mainnet = Settings.is_stored_mainnet()
        self.is_stored_testnet = Settings.is_stored_testnet()
        self.stored_gas_price = Settings.get_stored_gas_price()
        is_persistent_keystore = (
            Settings.is_persistent_keystore() and check_write_permission())
        self.set_persist_keystore_switch_state(is_persistent_keystore)

    def store_settings(self):
        """
        Stores settings to json store.
        """
        self.store_gas_price()
        self.store_network()
        self.store_is_persistent_keystore()

    def get_ui_network(self):
        """
        Retrieves network values from UI.
        """
        if self.is_ui_mainnet():
            network = ChainID.MAINNET
        else:
            network = ChainID.ROPSTEN
        return network

    def is_ui_mainnet(self):
        return self.ids.mainnet_checkbox_id.active

    def is_ui_testnet(self):
        return self.ids.testnet_checkbox_id.active

    def get_ui_gas_price(self):
        return self.ids.gas_price_slider_id.value

    def is_ui_persistent_keystore(self):
        return self.ids.persist_keystore_switch_id.active

    def check_request_write_permission(self):
        # previous state before the toggle
        if self.is_ui_persistent_keystore():
            check_request_write_permission()
