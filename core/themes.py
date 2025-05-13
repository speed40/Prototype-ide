"""
Theme management system for KivyMD applications.

Handles:
- Font registration
- Theme loading and switching
- Color scheme management
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

from kivy.core import text
from kivy.logger import Logger
from kivy.utils import get_color_from_hex

# --- Type Definitions ---
class ThemeSettings(TypedDict):
    primary_palette: str
    primary_hue: str
    accent_palette: str
    theme_style: str

class SyntaxColors(TypedDict):
    background: str
    text: Dict[str, str]
    keyword: Dict[str, str]
    builtin: Dict[str, str]
    string: Dict[str, str]
    number: Dict[str, str]
    comment: Dict[str, str]
    operator: Dict[str, str]
    definition: Dict[str, str]
    line_numbers: Dict[str, str]
    current_line: Dict[str, str]
    selection: Dict[str, str]
    error: Dict[str, str]

class ThemeData(TypedDict):
    theme_name: str
    primary_palette: str
    primary_hue: str
    accent_palette: str
    theme_style: str
    syntax: SyntaxColors

# --- Constants ---
BASE_DIR = Path(__file__).parent.parent
FONT_DIR = BASE_DIR / "assets" / "fonts"
THEMES_DIR = BASE_DIR / "assets" / "themes"


# --- Font Management ---
def register_fonts(font_dir: Path = FONT_DIR) -> bool:
    """Register custom fonts from the given directory."""
    if not font_dir.exists():
        Logger.warning(f"Font directory not found: {font_dir}")
        return False

    success = True
    for font_file in font_dir.glob("*.ttf"):
        try:
            font_name = font_file.stem
            text.LabelBase.register(name=font_name, fn_regular=str(font_file))
            Logger.info(f"Registered font: {font_name}")
        except Exception as e:
            Logger.error(f"Failed to register font {font_file.name}: {e}")
            success = False

    return success

def get_registered_font_names() -> List[str]:
    """Get sorted list of all registered font families."""
    try:
        if hasattr(text.LabelBase, 'get_registered_fonts'):
            return sorted(text.LabelBase.get_registered_fonts().keys())
        return []
    except Exception as e:
        Logger.error(f"Error getting font names: {e}")
        return []

# --- Theme Management ---
class ThemeManager:
    """Core theme management system for KivyMD applications."""
    
    def __init__(self):
        self._themes: Dict[str, ThemeData] = {}
        self._current_theme = ""
        Logger.info("ThemeManager initialized")

    def load_themes(self, themes_dir: Path = THEMES_DIR) -> int:
        """Load all theme files from the specified directory.
        
        Args:
            themes_dir: Path to directory containing theme JSON files
            
        Returns:
            Number of themes successfully loaded
        """
        if not themes_dir.exists():
            Logger.error(f"Themes directory not found: {themes_dir}")
            return 0

        loaded = 0
        for theme_file in themes_dir.glob("*.json"):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    theme = json.load(f)
                
                if not self._validate_theme(theme):
                    continue
                
                theme_name = theme['theme_name']
                self._themes[theme_name] = theme
                loaded += 1
                Logger.info(f"Loaded theme: {theme_name}")

            except (json.JSONDecodeError, KeyError) as e:
                Logger.error(f"Invalid theme file {theme_file.name}: {e}")
            except Exception as e:
                Logger.error(f"Error loading theme {theme_file.name}: {e}")

        if not loaded:
            Logger.warning("No valid themes found - creating fallback")
            self._create_fallback_theme()

        return loaded

    def get_theme_names(self) -> List[str]:
        """Get sorted list of available theme names."""
        return sorted(self._themes.keys())

    def apply_theme(self, theme_name: str) -> bool:
        """Apply a theme by name.
        
        Args:
            theme_name: Name of theme to apply
            
        Returns:
            True if theme was applied successfully
        """
        if theme_name not in self._themes:
            Logger.warning(f"Theme '{theme_name}' not found")
            return False

        self._current_theme = theme_name
        Logger.info(f"Applied theme: {theme_name}")
        return True

    def get_current_theme(self) -> Optional[ThemeData]:
        """Get data for the currently active theme."""
        if not self._current_theme:
            return None
        return self._themes.get(self._current_theme)

    def get_theme_colors(self, theme_name: str) -> Optional[SyntaxColors]:
        """Get syntax colors for a specific theme."""
        theme = self._themes.get(theme_name)
        return theme.get('syntax') if theme else None

    def _validate_theme(self, theme: dict) -> bool:
        """Validate a theme dictionary has required fields."""
        required = ['theme_name', 'primary_palette', 'theme_style', 'syntax']
        if not all(key in theme for key in required):
            Logger.error("Theme missing required fields")
            return False
        
        if not isinstance(theme['syntax'], dict):
            Logger.error("Theme syntax must be a dictionary")
            return False
            
        return True

    def _create_fallback_theme(self) -> None:
        """Create a minimal fallback theme when no themes are loaded."""
        self._themes['fallback'] = {
            'theme_name': 'fallback',
            'primary_palette': 'Blue',
            'primary_hue': '500',
            'accent_palette': 'Amber',
            'theme_style': 'Light',
            'syntax': {
                'background': '#FFFFFF',
                'text': {'color': '#000000', 'style': 'normal'},
                'keyword': {'color': '#0000FF', 'style': 'bold'},
                'string': {'color': '#008000', 'style': 'normal'},
                'comment': {'color': '#808080', 'style': 'italic'}
            }
        }
        Logger.warning("Created fallback theme")

# Initialize fonts when module is imported
register_fonts()