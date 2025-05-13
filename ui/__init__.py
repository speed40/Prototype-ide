# ui/__init__.py

from kivy.logger import Logger

# Import key components from modules within the ui package
from ui.dialogs import (
    BaseDialog,
    ErrorDialog,
    ConfirmDialog,
    InfoDialog,
    WarningDialog,
)
from .editor import CodeEditor
from .console import Console
# Import the SettingsScreen from the settings_screen module
from .settings_screen import SettingsScreen


# Define what gets imported when doing 'from ui import *'
__all__ = [
   # from dialogs
   'BaseDialog',
   'ErrorDialog',
   'ConfirmDialog',
   'InfoDialog',
   'WarningDialog',

   'CodeEditor',
   'Console',
   'SettingsScreen', # Add SettingsScreen to the exports
]


Logger.info("Initializing ui package...")