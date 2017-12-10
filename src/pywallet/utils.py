import os
import threading
from io import StringIO

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.metrics import dp

from kivymd.dialog import MDDialog
from kivymd.label import MDLabel
from kivymd.snackbar import Snackbar


def run_in_thread(fn):
    """
    Decorator to run a function in a thread.
    >>> 1 + 1
    2
    >>> @run_in_thread
    ... def threaded_sleep(seconds):
    ...     from time import sleep
    ...     sleep(seconds)
    >>> thread = threaded_sleep(0.1)
    >>> type(thread)
    <class 'threading.Thread'>
    >>> thread.is_alive()
    True
    >>> thread.join()
    >>> thread.is_alive()
    False
    """
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw)
        t.start()
        return t
    return run


def load_kv_from_py(f):
    """
    Loads file.kv for given file.py.
    """
    filename = os.path.basename(os.path.splitext(f)[0])
    Builder.load_file(
        os.path.join(
            os.path.dirname(os.path.abspath(f)),
            filename + '.kv'
        )
    )


class StringIOCBWrite(StringIO):
    """
    Inherits StringIO, provides callback on write.
    """

    def __init__(self, initial_value='', newline='\n', callback_write=None):
        """
        Overloads the StringIO.__init__() makes it possible to hook a callback
        for write operations.
        """
        self.callback_write = callback_write
        super(StringIOCBWrite, self).__init__(initial_value, newline)

    def write(self, s):
        """
        Calls the StringIO.write() method then the callback_write with
        given string parameter.
        """
        # io.StringIO expects unicode
        s_unicode = s.decode('utf-8')
        super(StringIOCBWrite, self).write(s_unicode)
        if self.callback_write is not None:
            self.callback_write(s_unicode)


class Dialog(object):

    # keeps track of all dialogs alive
    dialogs = []
    __lock = threading.Lock()

    @staticmethod
    @mainthread
    def snackbar_message(text):
        Snackbar(text=text).show()

    @classmethod
    def show_invalid_form_dialog(cls):
        title = "Invalid form"
        body = "Please check form fields."
        dialog = cls.create_dialog(title, body)
        dialog.open()

    @classmethod
    def on_dialog_dismiss(cls, dialog):
        """
        Removes it from the dialogs track list.
        """
        with cls.__lock:
            try:
                cls.dialogs.remove(dialog)
            except ValueError:
                # fails silently if the dialog was dismissed twice, refs:
                # https://github.com/AndreMiras/PyWallet/issues/89
                pass

    @classmethod
    def dismiss_all_dialogs(cls):
        """
        Dispatches dismiss event for all dialogs.
        """
        # keeps a local copy since we're altering them as we iterate
        dialogs = cls.dialogs[:]
        for dialog in dialogs:
            dialog.dispatch('on_dismiss')

    @classmethod
    def create_dialog_helper(cls, title, body):
        """
        Creates a dialog from given title and body.
        Adds it to the dialogs track list.
        """
        content = MDLabel(
                    font_style='Body1',
                    theme_text_color='Secondary',
                    text=body,
                    size_hint_y=None,
                    valign='top')
        content.bind(texture_size=content.setter('size'))
        dialog = MDDialog(
                        title=title,
                        content=content,
                        size_hint=(.8, None),
                        height=dp(250),
                        auto_dismiss=False)
        dialog.bind(on_dismiss=cls.on_dialog_dismiss)
        with cls.__lock:
            cls.dialogs.append(dialog)
        return dialog

    @classmethod
    def create_dialog(cls, title, body):
        """
        Creates a dialog from given title and body.
        Adds it to the dialogs track list.
        Appends dismiss action.
        """
        dialog = cls.create_dialog_helper(title, body)
        dialog.add_action_button(
                "Dismiss",
                action=lambda *x: dialog.dismiss())
        return dialog

    @classmethod
    def on_balance_connection_error(cls):
        title = "Network error"
        body = "Couldn't load balance, no network access."
        dialog = cls.create_dialog(title, body)
        dialog.open()

    @classmethod
    def on_balance_value_error(cls):
        title = "Decode error"
        body = "Couldn't not decode balance data."
        dialog = cls.create_dialog(title, body)
        dialog.open()

    @classmethod
    def on_balance_unknown_error(cls):
        title = "Unknown error"
        body = "Unknown error while fetching balance."
        dialog = cls.create_dialog(title, body)
        dialog.open()

    @classmethod
    def on_history_connection_error(cls):
        title = "Network error"
        body = "Couldn't load history, no network access."
        dialog = cls.create_dialog(title, body)
        dialog.open()

    @classmethod
    def on_history_value_error(cls):
        title = "Decode error"
        body = "Couldn't not decode history data."
        dialog = cls.create_dialog(title, body)
        dialog.open()
