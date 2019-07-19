import shutil
import unittest
from tempfile import mkdtemp
from unittest import mock

from kivy.app import App
from pyetheroll.constants import ChainID

from etheroll.settings import Settings
from service.main import EtherollApp


class TestSettings(unittest.TestCase):
    """
    Unit tests Settings methods.
    """
    @classmethod
    def setUpClass(cls):
        EtherollApp()

    def setUp(self):
        """
        Creates a temporary user data dir for storing the user config.
        """
        self.temp_path = mkdtemp(prefix='etheroll')
        self.app = App.get_running_app()
        self.app._user_data_dir = self.temp_path

    def tearDown(self):
        """
        Deletes temporary user data dir.
        """
        shutil.rmtree(self.temp_path, ignore_errors=True)

    def test_get_set_stored_network(self):
        """
        Checks default stored network and set method.
        """
        # checks default
        assert Settings.get_stored_network() == ChainID.MAINNET
        # checks set
        Settings.set_stored_network(ChainID.ROPSTEN)
        assert Settings.get_stored_network() == ChainID.ROPSTEN

    def test_is_stored_mainnet(self):
        Settings.set_stored_network(ChainID.MAINNET)
        assert Settings.is_stored_mainnet() is True
        Settings.set_stored_network(ChainID.ROPSTEN)
        assert Settings.is_stored_mainnet() is False

    def test_is_stored_testnet(self):
        Settings.set_stored_network(ChainID.MAINNET)
        assert Settings.is_stored_testnet() is False
        Settings.set_stored_network(ChainID.ROPSTEN)
        assert Settings.is_stored_testnet() is True

    def test_get_set_stored_gas_price(self):
        """
        Checks default stored gas price and set method.
        """
        # checks default
        assert Settings.get_stored_gas_price() == 4
        # checks set
        Settings.set_stored_gas_price(42)
        assert Settings.get_stored_gas_price() == 42

    def test_get_set_is_persistent_keystore(self):
        """
        Checks default persist value and set method.
        """
        # checks default
        assert Settings.is_persistent_keystore() is False
        # checks set
        Settings.set_is_persistent_keystore(True)
        assert Settings.is_persistent_keystore() is True

    def test_get_android_keystore_prefix(self):
        """
        The keystore prefix should be the same as user_data_dir by default.
        But it can also be persisted to the sdcard.
        """
        assert Settings.is_persistent_keystore() is False
        prefix = Settings._get_android_keystore_prefix()
        assert prefix == self.app.user_data_dir
        with mock.patch.object(
                Settings, 'is_persistent_keystore', return_value=True):
            prefix = Settings._get_android_keystore_prefix()
        assert prefix == '/sdcard/etheroll'
