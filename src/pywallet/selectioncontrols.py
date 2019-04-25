from kivy.utils import get_color_from_hex
from kivymd.color_definitions import colors
from kivymd.selectioncontrols import MDSwitch


class CustomMDSwitch(MDSwitch):
    """
    Work around for a MDSwitch bug, refs:
    https://gitlab.com/kivymd/KivyMD/issues/99
    """

    def _set_colors(self, *args):
        """
        Overrides `MDSwitch._set_colors()` fixes missing attribute
        `thumb_color_disabled`, refs:
        https://gitlab.com/kivymd/KivyMD/issues/99
        """
        super(CustomMDSwitch, self)._set_colors(*args)
        self.thumb_color_disabled = get_color_from_hex(colors['Grey']['800'])
