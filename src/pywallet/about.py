import os
import unittest

from kivy.clock import Clock, mainthread
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

from pywallet.utils import StringIOCBWrite, load_kv_from_py, run_in_thread
from testsuite import suite
from version import __version__

load_kv_from_py(__file__)


class AboutChangelog(BoxLayout):
    changelog_text_property = StringProperty()

    def __init__(self, **kwargs):
        super(AboutChangelog, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.load_changelog())

    def load_changelog(self):
        # circular dep
        from pywallet.controller import Controller
        changelog_path = os.path.join(
            Controller.src_dir(),
            'CHANGELOG.md')
        with open(changelog_path, 'r') as f:
            self.changelog_text_property = f.read()
        f.close()


class AboutOverview(BoxLayout):
    project_page_property = StringProperty(
        "https://github.com/AndreMiras/PyWallet")
    about_text_property = StringProperty()

    def __init__(self, **kwargs):
        super(AboutOverview, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.load_about())

    def load_about(self):
        self.about_text_property = "" + \
            "PyWallet version: %s\n" % (__version__) + \
            "Project source code and info available on GitHub at: \n" + \
            "[color=00BFFF][ref=github]" + \
            self.project_page_property + \
            "[/ref][/color]"


class AboutDiagnostic(BoxLayout):
    stream_property = StringProperty()

    @mainthread
    def callback_write(self, s):
        """
        Updates the UI with test progress.
        """
        self.stream_property += s

    @run_in_thread
    def run_tests(self):
        """
        Loads the test suite and hook the callback for reporting progress.
        """
        # circular dep
        from pywallet.controller import Controller
        Controller.patch_keystore_path()
        test_suite = suite()
        self.stream_property = ""
        stream = StringIOCBWrite(callback_write=self.callback_write)
        verbosity = 2
        unittest.TextTestRunner(
                stream=stream, verbosity=verbosity).run(test_suite)


class AboutScreen(Screen):
    pass
