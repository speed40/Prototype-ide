# core/icons.py

# Import necessary components if needed for icon definitions (though not strictly required by the dict itself)
# from kivymd.icon_definitions import md_icons # This import is usually needed elsewhere when *using* the icon names

# --- Constants ---

# Mapping of internal keys to KivyMD icon names and descriptions
ICONS = {
    "menu": "dots-vertical",
    "menu_desc": "Menu or more options",
    "undo": "undo",
    "undo_desc": "Undo last action",
    "redo": "redo",
    "redo_desc": "Redo last undone action",
    "tab": "tab",
    "tab_desc": "Manage editor tabs",
    "play": "play",
    "play_desc": "Run or execute",
    "save": "content-save",
    "save_desc": "Save current work",
    "save_as": "content-save-as",
    "save_as_desc": "Save with new name",
    "folder_open": "folder-open",
    "folder_open_desc": "Open a file or project",
    "settings": "cog",
    "settings_desc": "Settings or preferences",
    "close": "close",
    "close_desc": "Close current item",
    "refresh": "refresh",
    "refresh_desc": "Reload or refresh",
    "exit": "exit-to-app",
    "exit_desc": "Exit or quit",
    "back": "keyboard-backspace",
    "back_desc": "Back or navigate up",
    "theme_light": "weather-sunny",
    "theme_dark": "weather-night",
}

# --- Icon Helper Functions ---

def get_icon(icon_key: str) -> str | None:
    """Retrieves the KivyMD icon name for a given internal icon key."""
    return ICONS.get(icon_key)


def get_icon_desc(icon_key: str) -> str | None:
    """Retrieves the description for a given internal icon key."""
    # Assumes descriptions follow the pattern icon_key + "_desc"
    return ICONS.get(f"{icon_key}_desc")