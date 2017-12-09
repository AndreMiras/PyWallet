#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import kivy
from ethereum.utils import normalize_address
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.logger import LOG_LEVELS, Logger
from kivy.metrics import dp
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
from kivymd.button import MDFlatButton
from kivymd.dialog import MDDialog
from kivymd.list import OneLineListItem, TwoLineIconListItem
from kivymd.theming import ThemeManager
from kivymd.toolbar import Toolbar
from PIL import Image as PILImage
from raven import Client
from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler
from requests.exceptions import ConnectionError

from pywalib import (ROUND_DIGITS, InsufficientFundsException,
                     NoTransactionFoundException, PyWalib,
                     UnknownEtherscanException)
from pywallet.controller import Controller, run_in_thread
from pywallet.list import IconLeftWidget
from pywallet.passwordform import PasswordForm
from version import __version__

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

kivy.require('1.10.0')


class Send(BoxLayout):

    password = StringProperty("")
    send_to_address = StringProperty("")
    send_amount = NumericProperty(0)

    def __init__(self, **kwargs):
        super(Send, self).__init__(**kwargs)

    def verify_to_address_field(self):
        title = "Input error"
        body = "Invalid address field"
        try:
            normalize_address(self.send_to_address)
        except Exception:
            dialog = Controller.create_dialog(title, body)
            dialog.open()
            return False
        return True

    def verify_amount_field(self):
        title = "Input error"
        body = "Invalid amount field"
        if self.send_amount == 0:
            dialog = Controller.create_dialog(title, body)
            dialog.open()
            return False
        return True

    def verify_fields(self):
        """
        Verifies address and amount fields are valid.
        """
        return self.verify_to_address_field() \
            and self.verify_amount_field()

    def on_unlock_clicked(self, dialog, password):
        self.password = password
        dialog.dismiss()

    def prompt_password_dialog(self):
        """
        Prompt the password dialog.
        """
        title = "Enter your password"
        content = PasswordForm()
        dialog = MDDialog(
                        title=title,
                        content=content,
                        size_hint=(.8, None),
                        height=dp(250),
                        auto_dismiss=False)
        # workaround for MDDialog container size (too small by default)
        dialog.ids.container.size_hint_y = 1
        dialog.add_action_button(
                "Unlock",
                action=lambda *x: self.on_unlock_clicked(
                    dialog, content.password))
        return dialog

    def on_send_click(self):
        if not self.verify_fields():
            Controller.show_invalid_form_dialog()
            return
        dialog = self.prompt_password_dialog()
        dialog.open()

    @run_in_thread
    def unlock_send_transaction(self):
        """
        Unlocks the account with password in order to sign and publish the
        transaction.
        """
        controller = App.get_running_app().controller
        pywalib = controller.pywalib
        address = normalize_address(self.send_to_address)
        amount_eth = round(self.send_amount, ROUND_DIGITS)
        amount_wei = int(amount_eth * pow(10, 18))
        account = controller.pywalib.get_main_account()
        Controller.snackbar_message("Unlocking account...")
        try:
            account.unlock(self.password)
        except ValueError:
            Controller.snackbar_message("Could not unlock account")
            return

        Controller.snackbar_message("Unlocked! Sending transaction...")
        sender = account.address
        try:
            pywalib.transact(address, value=amount_wei, data='', sender=sender)
        except InsufficientFundsException:
            Controller.snackbar_message("Insufficient funds")
            return
        except UnknownEtherscanException:
            Controller.snackbar_message("Unknown error")
            Logger.error('UnknownEtherscanException', exc_info=True)
            return
        # TODO: handle ConnectionError
        Controller.snackbar_message("Sent!")

    def on_password(self, instance, password):
        self.unlock_send_transaction()


class Receive(BoxLayout):

    current_account = ObjectProperty(allownone=True)
    address_property = StringProperty()

    def __init__(self, **kwargs):
        super(Receive, self).__init__(**kwargs)
        # for some reason setting the timeout to zero
        # crashes with:
        # 'super' object has no attribute '__getattr__'
        # only on first account creation (with auto redirect)
        # and we cannot yet reproduce in unit tests
        timeout = 1
        Clock.schedule_once(lambda dt: self.setup(), timeout)

    def setup(self):
        """
        Binds Controller current_account and on_alias_updated.
        """
        self.controller = App.get_running_app().controller
        self.controller.bind(current_account=self.setter('current_account'))
        self.controller.bind(on_alias_updated=self.on_alias_updated)
        # triggers the update
        self.current_account = self.controller.current_account

    def show_address(self, address):
        self.ids.qr_code_id.data = address

    def update_address_property(self):
        """
        Updates address_property from current_account.
        """
        account = self.current_account
        address = "0x" + account.address.encode("hex")
        self.address_property = address

    def on_current_account(self, instance, account):
        if account is None:
            return
        self.update_address_property()

    def on_address_property(self, instance, value):
        self.show_address(value)

    def on_alias_updated(self, instance, alias):
        """
        Forces account string update, which will triggers an
        AddressButton.on_address_property event.
        """
        self.address_property = ""
        self.update_address_property()


class History(BoxLayout):

    current_account = ObjectProperty(allownone=True)

    def __init__(self, **kwargs):
        super(History, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Binds Controller.current_account property.
        """
        self.controller = App.get_running_app().controller
        self.controller.bind(current_account=self.setter('current_account'))
        # triggers the update
        self.current_account = self.controller.current_account
        self.controller.bind(accounts_history=self.update_history_list)

    def on_current_account(self, instance, account):
        """
        Updates with last known (cached values) and update the cache.
        """
        self.update_history_list()
        self.fetch_history()

    @staticmethod
    def create_item(sent, amount, from_to):
        """
        Creates a history list item from parameters.
        """
        send_receive = "Sent" if sent else "Received"
        text = "%s %sETH" % (send_receive, amount)
        secondary_text = from_to
        icon = "arrow-up-bold" if sent else "arrow-down-bold"
        list_item = TwoLineIconListItem(
            text=text, secondary_text=secondary_text)
        icon_widget = IconLeftWidget(icon=icon)
        list_item.add_widget(icon_widget)
        return list_item

    @classmethod
    def create_item_from_dict(cls, transaction_dict):
        """
        Creates a history list item from a transaction dictionary.
        """
        extra_dict = transaction_dict['extra_dict']
        sent = extra_dict['sent']
        amount = extra_dict['value_eth']
        from_address = extra_dict['from_address']
        to_address = extra_dict['to_address']
        from_to = to_address if sent else from_address
        list_item = cls.create_item(sent, amount, from_to)
        return list_item

    @mainthread
    def update_history_list(self, instance=None, value=None):
        """
        Updates the history list widget from last known (cached) values.
        """
        if self.current_account is None:
            return
        address = '0x' + self.current_account.address.encode("hex")
        try:
            transactions = self.controller.accounts_history[address]
        except KeyError:
            transactions = []
        # new transactions first, but do not change the list using reverse()
        transactions = transactions[::-1]
        history_list_id = self.ids.history_list_id
        history_list_id.clear_widgets()
        for transaction in transactions:
            list_item = History.create_item_from_dict(transaction)
            history_list_id.add_widget(list_item)

    @run_in_thread
    def fetch_history(self):
        if self.current_account is None:
            return
        address = '0x' + self.current_account.address.encode("hex")
        try:
            transactions = PyWalib.get_transaction_history(address)
        except ConnectionError:
            Controller.on_history_connection_error()
            Logger.warning('ConnectionError', exc_info=True)
            return
        except NoTransactionFoundException:
            transactions = []
        except ValueError:
            # most likely the JSON object could not be decoded, refs #91
            Controller.on_history_value_error()
            # currently logged as an error, because we want more insight
            # in order to eventually handle it more specifically
            Logger.error('ValueError', exc_info=True)
            return
        # triggers accounts_history observers update
        self.controller.accounts_history[address] = transactions


class SwitchAccount(BoxLayout):

    def on_release(self, list_item):
        """
        Sets Controller.current_account and switches to previous screen.
        """
        # sets Controller.current_account
        self.selected_list_item = list_item
        self.controller.current_account = list_item.account
        # switches to previous screen
        self.controller.screen_manager_previous()

    def create_item(self, account):
        """
        Creates an account list item from given account.
        """
        address = "0x" + account.address.encode("hex")
        # gets the alias if exists
        try:
            text = Controller.get_address_alias(address)
        except KeyError:
            text = address
        list_item = OneLineListItem(text=text)
        # makes sure the address doesn't overlap on small screen
        list_item.ids._lbl_primary.shorten = True
        list_item.account = account
        list_item.bind(on_release=lambda x: self.on_release(x))
        return list_item

    def load_account_list(self):
        """
        Fills account list widget from library account list.
        """
        self.controller = App.get_running_app().controller
        account_list_id = self.ids.account_list_id
        account_list_id.clear_widgets()
        accounts = self.controller.pywalib.get_account_list()
        for account in accounts:
            list_item = self.create_item(account)
            account_list_id.add_widget(list_item)


class PWSelectList(BoxLayout):

    selected_item = ObjectProperty()

    def __init__(self, **kwargs):
        self._items = kwargs.pop('items')
        super(PWSelectList, self).__init__(**kwargs)
        self._setup()

    def on_release(self, item):
        self.selected_item = item

    def _setup(self):
        address_list = self.ids.address_list_id
        for item in self._items:
            item.bind(on_release=lambda x: self.on_release(x))
            address_list.add_widget(item)


class ImportKeystore(BoxLayout):

    keystore_path = StringProperty()

    def __init__(self, **kwargs):
        super(ImportKeystore, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        self.controller = App.get_running_app().controller
        self.keystore_path = self.controller.get_keystore_path()
        accounts = self.controller.pywalib.get_account_list()
        if len(accounts) == 0:
            title = "No keystore found."
            body = "Import or create one."
            dialog = Controller.create_dialog(title, body)
            dialog.open()


# TODO: also make it possible to update PBKDF2
# TODO: create a generic password form
# TODO: create a generic account form
class ManageExisting(BoxLayout):

    # e.g. when the last account was deleted
    current_account = ObjectProperty(allownone=True)
    address_property = StringProperty()
    current_password = StringProperty()
    new_password1 = StringProperty()
    new_password2 = StringProperty()

    def __init__(self, **kwargs):
        super(ManageExisting, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Binds Controller.current_account property.
        """
        self.controller = App.get_running_app().controller
        self.pywalib = self.controller.pywalib
        self.controller.bind(current_account=self.setter('current_account'))
        # triggers the update
        self.current_account = self.controller.current_account

    def verify_current_password_field(self):
        """
        Makes sure passwords are matching.
        """
        account = self.current_account
        password = self.current_password
        # making sure it's locked first
        account.lock()
        try:
            account.unlock(password)
        except ValueError:
            return False
        return True

    def verify_password_field(self):
        """
        Makes sure passwords are matching and are not void.
        """
        passwords_matching = self.new_password1 == self.new_password2
        passwords_not_void = self.new_password1 != ''
        return passwords_matching and passwords_not_void

    def verify_fields(self):
        """
        Verifies password fields are valid.
        """
        return self.verify_password_field()

    def show_redirect_dialog(self):
        title = "Account deleted, redirecting..."
        body = ""
        body += "Your account was deleted, "
        body += "you will be redirected to the overview."
        dialog = Controller.create_dialog(title, body)
        dialog.open()

    def on_delete_account_yes(self, dialog):
        """
        Deletes the account, discarts the warning dialog,
        shows an info popup and redirects to the landing page.
        """
        account = self.current_account
        self.pywalib.delete_account(account)
        dialog.dismiss()
        self.controller.current_account = None
        self.show_redirect_dialog()
        self.controller.load_landing_page()

    def prompt_no_account_error(self):
        """
        Prompts an error since no account are selected for deletion, refs:
        https://github.com/AndreMiras/PyWallet/issues/90
        """
        title = "No account selected."
        body = "No account selected for deletion."
        dialog = Controller.create_dialog(title, body)
        dialog.open()

    def prompt_delete_account_dialog(self):
        """
        Prompt a confirmation dialog before deleting the account.
        """
        if self.current_account is None:
            self.prompt_no_account_error()
            return
        title = "Are you sure?"
        body = ""
        body += "This action cannot be undone.\n"
        body += "Are you sure you want to delete this account?\n"
        dialog = Controller.create_dialog_helper(title, body)
        dialog.add_action_button(
                "No",
                action=lambda *x: dialog.dismiss())
        dialog.add_action_button(
                "Yes",
                action=lambda *x: self.on_delete_account_yes(dialog))
        dialog.open()

    @run_in_thread
    def update_password(self):
        """
        Update account password with new password provided.
        """
        if not self.verify_fields():
            Controller.show_invalid_form_dialog()
            return
        Controller.snackbar_message("Verifying current password...")
        if not self.verify_current_password_field():
            Controller.snackbar_message("Wrong account password")
            return
        pywalib = self.controller.pywalib
        account = self.current_account
        new_password = self.new_password1
        Controller.snackbar_message("Updating account...")
        pywalib.update_account_password(account, new_password=new_password)
        Controller.snackbar_message("Updated!")

    def on_current_account(self, instance, account):
        # e.g. deleting the last account, would set
        # Controller.current_account to None
        if account is None:
            return
        address = "0x" + account.address.encode("hex")
        self.address_property = address


class CreateNewAccount(BoxLayout):
    """
    PBKDF2 iterations choice is a security vs speed trade off:
    https://security.stackexchange.com/q/3959
    """

    alias = StringProperty()
    new_password1 = StringProperty()
    new_password2 = StringProperty()

    def __init__(self, **kwargs):
        super(CreateNewAccount, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        """
        Sets security vs speed default values.
        Plus hides the advanced widgets.
        """
        self.security_slider = self.ids.security_slider_id
        self.speed_slider = self.ids.speed_slider_id
        self.security_slider.value = self.speed_slider.value = 50
        self.controller = App.get_running_app().controller
        self.toggle_advanced(False)

    def verify_password_field(self):
        """
        Makes sure passwords are matching and are not void.
        """
        passwords_matching = self.new_password1 == self.new_password2
        passwords_not_void = self.new_password1 != ''
        return passwords_matching and passwords_not_void

    def verify_fields(self):
        """
        Verifies password fields are valid.
        """
        return self.verify_password_field()

    @property
    def security_slider_value(self):
        return self.security_slider.value

    @staticmethod
    def try_unlock(account, password):
        """
        Just as a security measure, verifies we can unlock
        the newly created account with provided password.
        """
        # making sure it's locked first
        account.lock()
        try:
            account.unlock(password)
        except ValueError:
            title = "Unlock error"
            body = ""
            body += "Couldn't unlock your account.\n"
            body += "The issue should be reported."
            dialog = Controller.create_dialog(title, body)
            dialog.open()
            return

    @mainthread
    def on_account_created(self, account):
        """
        Switches to the newly created account.
        Clears the form.
        """
        self.controller.current_account = account
        self.new_password1 = ''
        self.new_password2 = ''

    @mainthread
    def toggle_widgets(self, enabled):
        """
        Enables/disables account creation widgets.
        """
        self.disabled = not enabled

    def show_redirect_dialog(self):
        title = "Account created, redirecting..."
        body = ""
        body += "Your account was created, "
        body += "you will be redirected to the overview."
        dialog = Controller.create_dialog(title, body)
        dialog.open()

    @run_in_thread
    def create_account(self):
        """
        Creates an account from provided form.
        Verify we can unlock it.
        Disables widgets during the process, so the user doesn't try
        to create another account during the process.
        """
        self.toggle_widgets(False)
        if not self.verify_fields():
            Controller.show_invalid_form_dialog()
            self.toggle_widgets(True)
            return
        pywalib = self.controller.pywalib
        password = self.new_password1
        security_ratio = self.security_slider_value
        # dividing again by 10, because otherwise it's
        # too slow on smart devices
        security_ratio /= 10.0
        Controller.snackbar_message("Creating account...")
        account = pywalib.new_account(
                password=password, security_ratio=security_ratio)
        Controller.snackbar_message("Created!")
        self.toggle_widgets(True)
        Controller.set_account_alias(account, self.alias)
        self.on_account_created(account)
        CreateNewAccount.try_unlock(account, password)
        self.show_redirect_dialog()
        self.controller.load_landing_page()
        return account

    def toggle_advanced(self, show):
        """
        Shows/hides advanced account creation widgets.
        https://stackoverflow.com/q/23211142/185510
        """
        advanced = self.ids.advanced_id
        alpha = 1 if show else 0
        for widget in advanced.children:
            widget.canvas.opacity = alpha
            widget.disabled = not show


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
        try:
            text = Controller.get_address_alias(address)
        except KeyError:
            text = address
        self.text = text


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


class ScrollableLabel(ScrollView):
    """
    https://github.com/kivy/kivy/wiki/Scrollable-Label
    """
    text = StringProperty('')


class SwitchAccountScreen(Screen):
    pass


class ManageKeystoreScreen(Screen):
    pass


class DebugRavenClient(object):
    """
    The DebugRavenClient should be used in debug mode, it just raises
    the exception rather than capturing it.
    """

    def captureException(self):
        raise


class PyWalletApp(App):
    theme_cls = ThemeManager()

    def build(self):
        self.icon = "docs/images/icon.png"
        return Controller(info='PyWallet')

    @property
    def controller(self):
        return self.root


def configure_sentry(in_debug=False):
    """
    Configure the Raven client, or create a dummy one if `in_debug` is `True`.
    """
    key = 'eaee971c463b49678f6f352dfec497a9'
    # the public DSN URL is not available on the Python client
    # so we're exposing the secret and will be revoking it on abuse
    # https://github.com/getsentry/raven-python/issues/569
    secret = '4f37fdbde03a4753b78abb84d11f45ab'
    project_id = '191660'
    dsn = 'https://{key}:{secret}@sentry.io/{project_id}'.format(
        key=key, secret=secret, project_id=project_id)
    if in_debug:
        client = DebugRavenClient()
    else:
        client = Client(dsn=dsn, release=__version__)
        # adds context for Android devices
        if platform == 'android':
            from jnius import autoclass
            Build = autoclass("android.os.Build")
            VERSION = autoclass('android.os.Build$VERSION')
            android_os_build = {
                'model': Build.MODEL,
                'brand': Build.BRAND,
                'device': Build.DEVICE,
                'manufacturer': Build.MANUFACTURER,
                'version_release': VERSION.RELEASE,
            }
            client.user_context({'android_os_build': android_os_build})
        # Logger.error() to Sentry
        # https://docs.sentry.io/clients/python/integrations/logging/
        handler = SentryHandler(client)
        handler.setLevel(LOG_LEVELS.get('error'))
        setup_logging(handler)
    return client


if __name__ == '__main__':
    # when the -d/--debug flag is set, Kivy sets log level to debug
    level = Logger.getEffectiveLevel()
    in_debug = level == LOG_LEVELS.get('debug')
    client = configure_sentry(in_debug)
    try:
        PyWalletApp().run()
    except:
        if type(client) == Client:
            Logger.info(
                'Errors will be sent to Sentry, run with "--debug" if you '
                'are a developper and want to the error in the shell.')
        client.captureException()
