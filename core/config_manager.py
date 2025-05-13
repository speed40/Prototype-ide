# core/config_manager.py

import json
import os
from pathlib import Path
from typing import Dict, Any
from kivy.logger import Logger

class ConfigManager:
    """
    Manages application configuration, loading from default and user JSON files.
    Supports getting, setting, and resetting configuration values.
    """

    def __init__(self, user_config_filepath: str | Path = "data/user_config.json",
                 default_config_filepath: str | Path = "data/config.json"):
        Logger.info("ConfigManager: Initializing.")
        self._config: Dict[str, Any] = {}
        self._user_config_filepath = Path(user_config_filepath)
        self._default_config_filepath = Path(default_config_filepath)

        # Ensure the data directory for user config exists
        self._user_config_filepath.parent.mkdir(parents=True, exist_ok=True)

        # Define internal default config structure as a fallback if the default file is missing
        self._internal_default_config = self._define_internal_default_config()

        # Load configuration on initialization (defaults + user override)
        self.load_config()
        Logger.info(f"ConfigManager: Initialized with user config file: {self._user_config_filepath} and default config file: {self._default_config_filepath}")


    def _define_internal_default_config(self) -> Dict:
        """
        Defines a fallback default configuration structure and values internally.
        Used if the default config file cannot be loaded.
        """
        Logger.info("ConfigManager: Defining internal default configuration.")
        # --- Default Configuration Structure (Internal Fallback) ---
        # This defines the keys and default values for all settings.
        # Add new settings here with their default values.
        return {
            "theme": {
                "current_theme": "default", # Name of the currently selected theme
                "theme_style": "Dark",      # Dark or Light (Corrected default from 'false')
                "primary_palette": "BlueGray", # Default KivyMD primary
                "accent_palette": "BlueGray" # Default KivyMD accent
            },
            "language": {
                "current_language": "python",
                "ui_language": "en"
            },
            "editor": {
                "tab_spaces": 4,
                "font_name": "JetBrains Mono", # Assuming JetBrains Mono is registered
                "font_size": 16,
                "line_limit": 15
            },
            "console": {
                "font_name": "JetBrains Mono", # Assuming JetBrains Mono is registered
                "font_size": 14
            },
             "general": {
                "auto_save": True
            }
        }

    def load_config(self) -> None:
        """
        Loads the configuration from the default config file, then merges
        the user config file over the defaults if it exists.
        """
        Logger.info("ConfigManager: Loading configuration.")
        default_config = self._internal_default_config.copy() # Start with internal defaults

        # 1. Load from default config file if it exists
        if self._default_config_filepath.is_file():
            try:
                with open(self._default_config_filepath, 'r') as f:
                    file_defaults = json.load(f)
                    # Merge file defaults over internal defaults
                    self._recursive_update(default_config, file_defaults)
                Logger.debug(f"ConfigManager: Loaded defaults from {self._default_config_filepath}.")
            except json.JSONDecodeError as e:
                Logger.error(f"Error decoding JSON from default config file {self._default_config_filepath}: {e}. Using internal defaults.")
            except FileNotFoundError:
                 # Should not happen due to is_file() check, but good practice
                 Logger.warning(f"Default config file not found at {self._default_config_filepath}. Using internal defaults.")
            except Exception as e:
                Logger.error(f"Unexpected error loading default config from {self._default_config_filepath}: {e}. Using internal defaults.")

        # 2. Load from user config file if it exists and merge
        if self._user_config_filepath.is_file():
            try:
                with open(self._user_config_filepath, 'r') as f:
                    user_config = json.load(f)
                    # Merge user config over the loaded defaults
                    self._recursive_update(default_config, user_config)
                Logger.debug(f"ConfigManager: Merged user config from {self._user_config_filepath}.")
            except json.JSONDecodeError as e:
                Logger.error(f"Error decoding JSON from user config file {self._user_config_filepath}: {e}. Using defaults.")
            except FileNotFoundError:
                 # Should not happen due to is_file() check, but good practice
                 Logger.warning(f"User config file not found at {self._user_config_filepath}. Using loaded defaults.")
            except Exception as e:
                Logger.error(f"Unexpected error loading user config from {self._user_config_filepath}: {e}. Using loaded defaults.")

        self._config = default_config # The final merged config becomes the active config
        Logger.info("ConfigManager: Configuration loaded successfully.")


    def save_config(self) -> None:
        """Saves the current configuration to the user config file."""
        Logger.info(f"ConfigManager: Saving configuration to {self._user_config_filepath}.")
        try:
            # Ensure the directory exists before saving
            self._user_config_filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self._user_config_filepath, 'w') as f:
                json.dump(self._config, f, indent=4)
            Logger.info("ConfigManager: Configuration saved.")
        except Exception as e:
            Logger.error(f"Error saving configuration to {self._user_config_filepath}: {e}")

    def reset_to_defaults(self) -> Dict:
        """
        Loads the configuration from the default config file (or internal defaults)
        and saves it to the user config file, effectively resetting user settings.

        Returns:
             Dict: The newly loaded default configuration.
        """
        Logger.info("ConfigManager: Resetting configuration to defaults.")
        default_config = self._internal_default_config.copy() # Start with internal defaults

        # Load from default config file if it exists
        if self._default_config_filepath.is_file():
            try:
                with open(self._default_config_filepath, 'r') as f:
                    file_defaults = json.load(f)
                    # Merge file defaults over internal defaults
                    self._recursive_update(default_config, file_defaults)
                Logger.debug(f"ConfigManager: Loaded defaults from {self._default_config_filepath} for reset.")
            except json.JSONDecodeError as e:
                Logger.error(f"Error decoding JSON from default config file {self._default_config_filepath} during reset: {e}. Using internal defaults.")
            except FileNotFoundError:
                 Logger.warning(f"Default config file not found at {self._default_config_filepath} during reset. Using internal defaults.")
            except Exception as e:
                Logger.error(f"Unexpected error loading default config from {self._default_config_filepath} during reset: {e}. Using internal defaults.")

        self._config = default_config # Set the active config to defaults
        self.save_config() # Immediately save these defaults to user config file
        Logger.info("ConfigManager: Configuration reset to defaults and saved.")
        return self._config.copy()


    def get_setting(self, section: str, key: str, default_value: Any = None) -> Any:
        """
        Retrieves a specific setting value.

        Args:
            section (str): The section name.
            key (str): The setting key.
            default_value: The value to return if the section or key is not found.

        Returns:
            Any: The setting value or the default_value.
        """
        # Fallback first to internal default config, then to provided default_value
        section_defaults = self._internal_default_config.get(section, {})
        key_default = section_defaults.get(key, default_value)

        return self._config.get(section, {}).get(key, key_default)


    def set_setting(self, section: str, key: str, value: Any) -> None:
        """
        Sets a specific setting value in the current configuration (in memory).

        Args:
            section (str): The section name.
            key (str): The setting key.
            value: The value to set.
        """
        Logger.info(f"ConfigManager: Attempting to set setting '{section}.{key}' to '{value}'")
        if section not in self._config:
            # If the section doesn't exist in the current config, create it.
            # It's better to initialize it with default values for that section
            # from either the loaded defaults or internal defaults.
             section_defaults = self._internal_default_config.get(section, {})
             # Consider merging with defaults loaded from default file if necessary,
             # but for simplicity here, we'll just use internal defaults as structure.
             self._config[section] = section_defaults.copy()

             Logger.debug(f"ConfigManager: Created new section '{section}' in config (based on defaults).")

        self._config[section][key] = value
        Logger.info(f"ConfigManager: Setting '{section}.{key}' updated in memory.")

        # Note: save_config must be called explicitly to persist changes.


    def get_all_settings(self) -> Dict:
        """Returns a copy of the entire current configuration dictionary."""
        return self._config.copy()

    def reload_config(self) -> None:
        """
        Forces a reload of the configuration from the user file, merging with defaults.
        Discards any unsaved changes in memory.
        """
        Logger.info("ConfigManager: Reloading configuration.")
        # Simply call load_config again, which handles defaults + user merge
        self.load_config()
        Logger.info("ConfigManager: Configuration reloaded.")

    def _recursive_update(self, d: Dict, u: Dict) -> Dict:
        """Recursively update dictionary d with dictionary u."""
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._recursive_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d