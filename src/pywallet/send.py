import re

from eth_utils import to_checksum_address
from kivy.app import App
from kivy.logger import Logger
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.textfields import MDTextField

from pywalib import InsufficientFundsException, UnknownEtherscanException
from pywallet.passwordform import PasswordForm
from pywallet.settings import Settings
from pywallet.utils import Dialog, load_kv_from_py, run_in_thread

load_kv_from_py(__file__)


def is_number(s):
    try:
        float(s)
    except ValueError:
        return False
    return True


class MDFloatInput(MDTextField):

    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super().insert_text(s, from_undo=from_undo)


class Send(BoxLayout):

    password = StringProperty("")
    send_to_address = StringProperty("")

    def verify_to_address_field(self):
        title = "Input error"
        body = "Invalid address field"
        try:
            to_checksum_address(self.send_to_address)
        except ValueError:
            dialog = Dialog.create_dialog(title, body)
            dialog.open()
            return False
        return True

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
        if not self.verify_to_address_field():
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
        address = to_checksum_address(self.send_to_address)
        amount_eth = float(self.ids.send_amount_id.text)
        amount_wei = int(amount_eth * pow(10, 18))
        gas_price_gwei = Settings.get_stored_gas_price()
        gas_price_wei = int(gas_price_gwei * (10 ** 9))
        account = controller.current_account
        Dialog.snackbar_message("Unlocking account...")
        try:
            account.unlock(self.password)
        except ValueError:
            Dialog.snackbar_message("Could not unlock account")
            return

        Dialog.snackbar_message("Unlocked! Sending transaction...")
        sender = account.address
        try:
            pywalib.transact(
                address, value=amount_wei, data='', sender=sender,
                gasprice=gas_price_wei)
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
