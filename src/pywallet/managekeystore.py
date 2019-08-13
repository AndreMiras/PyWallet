from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

from pywallet.settings import Settings
from pywallet.utils import Dialog, load_kv_from_py, run_in_thread

load_kv_from_py(__file__)


class ManageKeystoreScreen(Screen):
    pass


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
        dialog = Dialog.create_dialog(title, body)
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
        dialog = Dialog.create_dialog(title, body)
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
        dialog = Dialog.create_dialog_helper(title, body)
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
            Dialog.show_invalid_form_dialog()
            return
        Dialog.snackbar_message("Verifying current password...")
        if not self.verify_current_password_field():
            Dialog.snackbar_message("Wrong account password")
            return
        pywalib = self.controller.pywalib
        account = self.current_account
        new_password = self.new_password1
        Dialog.snackbar_message("Updating account...")
        pywalib.update_account_password(account, new_password=new_password)
        Dialog.snackbar_message("Updated!")

    def on_current_account(self, instance, account):
        # e.g. deleting the last account, would set
        # Controller.current_account to None
        if account is None:
            return
        address = "0x" + account.address.hex()
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
            dialog = Dialog.create_dialog(title, body)
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
        dialog = Dialog.create_dialog(title, body)
        dialog.open()

    @run_in_thread
    def create_account(self):
        """
        Creates an account from provided form.
        Verify we can unlock it.
        Disables widgets during the process, so the user doesn't try
        to create another account during the process.
        """
        # circular ref
        from pywallet.controller import Controller
        self.toggle_widgets(False)
        if not self.verify_fields():
            Dialog.show_invalid_form_dialog()
            self.toggle_widgets(True)
            return
        pywalib = self.controller.pywalib
        password = self.new_password1
        security_ratio = self.security_slider_value
        Dialog.snackbar_message("Creating account...")
        account = pywalib.new_account(
                password=password, security_ratio=security_ratio)
        Dialog.snackbar_message("Created!")
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


class ImportKeystore(BoxLayout):

    keystore_path = StringProperty()

    def __init__(self, **kwargs):
        super(ImportKeystore, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.setup())

    def setup(self):
        self.controller = App.get_running_app().controller
        self.keystore_path = Settings.get_keystore_path()
        accounts = self.controller.pywalib.get_account_list()
        if len(accounts) == 0:
            title = "No keystore found."
            body = "Import or create one."
            dialog = Dialog.create_dialog(title, body)
            dialog.open()
