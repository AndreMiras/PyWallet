from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

from pywallet.utils import load_kv_from_py

load_kv_from_py(__file__)


class PasswordForm(BoxLayout):
    password = StringProperty()
