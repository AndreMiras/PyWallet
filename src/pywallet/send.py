from ethereum.utils import normalize_address
from kivy.app import App
from kivy.logger import Logger
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

from pywalib import (ROUND_DIGITS, InsufficientFundsException,
                     UnknownEtherscanException)
from pywallet.passwordform import PasswordForm
from pywallet.utils import Dialog, load_kv_from_py, run_in_thread

load_kv_from_py(__file__)


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
            dialog = Dialog.create_dialog(title, body)
            dialog.open()
            return False
        return True

    def verify_amount_field(self):
        title = "Input error"
        body = "Invalid amount field"
        if self.send_amount == 0:
            dialog = Dialog.create_dialog(title, body)
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
        dialog = Dialog.create_dialog_content_helper(
                    title=title,
                    content=content)
        # workaround for MDDialog container size (too small by default)
        dialog.ids.container.size_hint_y = 1
        dialog.add_action_button(
            "Unlock",
            action=lambda *x: self.on_unlock_clicked(
                dialog, content.password))
        return dialog

    def on_send_click(self):
        if not self.verify_fields():
            Dialog.show_invalid_form_dialog()
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
        # TODO: not the main account, but the current account
        account = controller.pywalib.get_main_account()
        Dialog.snackbar_message("Unlocking account...")
        try:
            account.unlock(self.password)
        except ValueError:
            Dialog.snackbar_message("Could not unlock account")
            return

        Dialog.snackbar_message("Unlocked! Sending transaction...")
        sender = account.address
        try:
            pywalib.transact(address, value=amount_wei, data='', sender=sender)
        except InsufficientFundsException:
            Dialog.snackbar_message("Insufficient funds")
            return
        except UnknownEtherscanException:
            Dialog.snackbar_message("Unknown error")
            Logger.error('UnknownEtherscanException', exc_info=True)
            return
        # TODO: handle ConnectionError
        Dialog.snackbar_message("Sent!")

    def on_password(self, instance, password):
        self.unlock_send_transaction()
