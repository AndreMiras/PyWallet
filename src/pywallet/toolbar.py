from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivymd.toolbar import Toolbar

from pywallet.utils import load_kv_from_py

load_kv_from_py(__file__)


class PWToolbar(Toolbar):

    title_property = StringProperty()

    def __init__(self, **kwargs):
        super(PWToolbar, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        self.controller = App.get_running_app().controller
        self.navigation = self.controller.ids.navigation_id
        self.load_default_navigation()

    def load_default_navigation(self):
        self.left_action_items = [
            ['menu', lambda x: self.toggle_nav_drawer()]
        ]
        self.right_action_items = [
            ['dots-vertical', lambda x: self.toggle_nav_drawer()]
        ]

    def toggle_nav_drawer(self):
        self.navigation.toggle_nav_drawer()
