from kivy.properties import StringProperty
from kivy.uix.scrollview import ScrollView

from pywallet.utils import load_kv_from_py

load_kv_from_py(__file__)


class ScrollableLabel(ScrollView):
    """
    https://github.com/kivy/kivy/wiki/Scrollable-Label
    """
    text = StringProperty('')
