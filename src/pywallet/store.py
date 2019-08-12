import os

from kivy.app import App
from kivy.storage.jsonstore import JsonStore


class Store:

    @classmethod
    def get_store_path(cls):
        """
        Returns the full user store path.
        On Android, the store is purposely not stored on the sdcard.
        That way we don't need permission for handling user settings.
        Also losing it is not critical.
        """
        app = App.get_running_app()
        return os.path.join(app.user_data_dir, 'store.json')

    @classmethod
    def get_store(cls):
        """
        Returns user Store object.
        """
        store_path = cls.get_store_path()
        store = JsonStore(store_path)
        return store
