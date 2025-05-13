# ui/utilities/__init__.py

from kivy.logger import Logger 

# Import key components from modules within the ui.utilities package
from .file_manager import FileManager
from .history_manager import HistoryManager

try:
    from .icons import get_icon, get_icon_desc, ICONS
except ImportError:
    # Define dummy versions if icons.py is missing to prevent import errors
    ICONS = {}
    def get_icon(icon_key):
        Logger.warning(f"[UI.Utilities] icons.py not imported. get_icon('{icon_key}') call failed.")
        return None
    def get_icon_desc(icon_key):
        Logger.warning(f"[UI.Utilities] icons.py not imported. get_icon_desc('{icon_key}') call failed.")
        return None
    Logger.warning("[UI.Utilities] Could not import icons.py. Icon utilities will not function.")


# Define what gets imported when doing 'from ui.utilities import *'
__all__ = [
    'FileManager',
    'HistoryManager',

    'get_icon',
    'get_icon_desc',
    'ICONS',
]


Logger.info("Initializing ui.utilities package...")