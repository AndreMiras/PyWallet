from kivy.app import App
from kivy.uix.screenmanager import Screen
from PIL import Image as PILImage

from pywallet.utils import load_kv_from_py

load_kv_from_py(__file__)

# monkey patching PIL, until it gets monkey patched upstream, refs:
# https://github.com/kivy/kivy/issues/5460
# and refs:
# https://github.com/AndreMiras/PyWallet/issues/104
try:
    # Pillow
    PILImage.frombytes
    PILImage.Image.tobytes
except AttributeError:
    # PIL
    PILImage.frombytes = PILImage.frombuffer
    PILImage.Image.tobytes = PILImage.Image.tostring


class FlashQrCodeScreen(Screen):

    @property
    def zbarcam(self):
        return self.ids.zbarcam_id

    def bind_on_symbols(self):
        """
        Since the camera doesn't seem to stop properly, we always bind/unbind
        on_pre_enter/on_pre_leave.
        """
        self.zbarcam.bind(symbols=self.on_symbols)

    def unbind_on_symbols(self):
        """
        Since the camera doesn't seem to stop properly, makes sure at least
        events are unbound.
        """
        self.zbarcam.unbind(symbols=self.on_symbols)

    def on_symbols(self, instance, symbols):
        # also ignores if more than 1 code were found since we don't want to
        # send to the wrong one
        if len(symbols) != 1:
            return
        symbol = symbols[0]
        # update Send screen address
        controller = App.get_running_app().controller
        controller.send.send_to_address = symbol.data.decode('utf-8')
        self.zbarcam.play = False
        controller.load_landing_page()
