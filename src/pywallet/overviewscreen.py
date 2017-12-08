from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen

from pywallet.utils import load_kv_from_py

load_kv_from_py(__file__)


class OverviewScreen(Screen):

    title_property = StringProperty()

    def set_title(self, title):
        self.title_property = title
