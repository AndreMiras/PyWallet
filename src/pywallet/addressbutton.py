from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.button import MDFlatButton


class AddressButton(MDFlatButton):
    """
    Overrides MDFlatButton, makes the font slightly smaller on mobile
    by using "Body1" rather than "Button" style.
    Also shorten content size using ellipsis.
    """

    address_property = StringProperty()

    def __init__(self, **kwargs):
        super(AddressButton, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        self.controller = App.get_running_app().controller
        self.set_font_and_shorten()

    def set_font_and_shorten(self):
        """
        Makes the font slightly smaller on mobile
        by using "Body1" rather than "Button" style.
        Also shorten content size using ellipsis.
        """
        content = self.ids.content
        content.font_style = 'Body1'
        content.shorten = True

        def on_parent_size(instance, size):
            # see BaseRectangularButton.width definition
            button_margin = dp(32)
            parent_width = instance.width
            # TODO: the new size should be a min() of
            # parent_width and actual content size
            content.width = parent_width - button_margin
        self.parent.bind(size=on_parent_size)
        # call it once manually, refs:
        # https://github.com/AndreMiras/PyWallet/issues/74
        on_parent_size(self.parent, None)

    def on_address_property(self, instance, address):
        """
        Sets the address alias if it exists or defaults to the address itself.
        """
        # circular dep
        from pywallet.controller import Controller
        try:
            text = Controller.get_address_alias(address)
        except KeyError:
            text = address
        self.text = text
