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

    def __init__(self, **kwargs):
        super(FlashQrCodeScreen, self).__init__(**kwargs)
        self.setup()

    def setup(self):
        """
        Configures scanner to handle only QRCodes.
        """
        self.controller = App.get_running_app().controller
        self.zbarcam = self.ids.zbarcam_id
        # loads ZBarCam only when needed, refs:
        # https://github.com/AndreMiras/PyWallet/issues/94
        import zbar
        # enables QRCode scanning only
        self.zbarcam.scanner.set_config(
            zbar.Symbol.NONE, zbar.Config.ENABLE, 0)
        self.zbarcam.scanner.set_config(
            zbar.Symbol.QRCODE, zbar.Config.ENABLE, 1)

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
        self.controller.send.send_to_address = symbol.data
        self.zbarcam.play = False
        self.controller.load_landing_page()
