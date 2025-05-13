# showcases/showcase_settings_screen.py

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window

# Import Screen, ScreenManager, SwapTransition, and FadeTransition
from kivy.uix.screenmanager import Screen, ScreenManager, SwapTransition, FadeTransition

# Import the ConfigManager from core.config_manager
from core.config_manager import ConfigManager
# Import ThemeManager and register_fonts from core.themes
# Keep register_fonts as it's a global app setup task
from core.themes import ThemeManager, register_fonts

# Import SettingsScreen from ui.settings_screen
from ui.settings_screen import SettingsScreen


# Import KivyMD specific screen
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel

from kivy.logger import Logger

Window.softinput_mode = 'below_target'


# Create a simple MainScreen that will contain the button to open settings
class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Logger.info("MainScreen: Initializing.")
        layout = MDBoxLayout(orientation='vertical', spacing="15dp", padding="25dp",
                             pos_hint={"center_x": 0.5, "center_y": 0.5},
                             size_hint=(0.8, 0.6))
        layout.add_widget(MDLabel(text="Main Application Screen", halign="center", font_style="H5", size_hint_y=None))
        layout.add_widget(MDRaisedButton(
            text="Open Settings",
            pos_hint={"center_x": 0.5},
            on_release=self.go_to_settings
        ))
        self.add_widget(layout)
        Logger.info("MainScreen: Initialized.")

    def go_to_settings(self, instance):
        """Navigate to the settings screen using the ScreenManager with FadeTransition."""
        Logger.info("MainScreen: 'Open Settings' button pressed. Navigating to 'settings' with FadeTransition.")
        if self.manager:
            # Set transition to FadeTransition before navigating to settings
            self.manager.transition = FadeTransition()
            self.manager.current = 'settings'
            Logger.info("MainScreen: ScreenManager current set to 'settings'.")
        else:
            Logger.warning("MainScreen: Manager is None. Cannot navigate.")


class ShowcaseSettingsApp(MDApp):
    def build(self):
        Logger.info("ShowcaseSettingsApp: build method called.")

        # Initialize ConfigManager, providing both default and user config paths
        self.config_manager = ConfigManager()
        Logger.info("ShowcaseSettingsApp: ConfigManager initialized with both default and user paths.")

        # Initialize ThemeManager and register fonts early in the app lifecycle
        # The main app is still responsible for setting up foundational components
        # like theme managers and fonts before screens might need them.
        self.theme_manager = ThemeManager() # Keep theme manager here for initial app theme setup
        self.theme_manager.load_themes_from_json()
        register_fonts() # Call register_fonts
        Logger.info("ShowcaseSettingsApp: ThemeManager initialized, themes loaded, fonts registered.")

        # Apply initial theme settings from the loaded config on app startup
        # Read the initial theme name from the ConfigManager instance
        try:
            initial_theme_name = self.config_manager.get_setting("theme", "current_theme", "default")
            initial_theme_data = self.theme_manager.get_theme_settings(initial_theme_name)
            if initial_theme_data and hasattr(self, 'theme_cls'):
                 kivymd_settings = initial_theme_data.get('kivymd_settings', {})
                 # Apply all KivyMD theme settings from the loaded theme data
                 self.theme_cls.primary_palette = kivymd_settings.get('primary_palette', self.theme_cls.primary_palette)
                 self.theme_cls.primary_hue = kivymd_settings.get('primary_hue', self.theme_cls.primary_hue)
                 self.theme_cls.accent_palette = kivymd_settings.get('accent_palette', self.theme_cls.accent_palette)
                 self.theme_cls.theme_style = kivymd_settings.get('theme_style', self.theme_cls.theme_style)
                 Logger.info(f"ShowcaseSettingsApp: Applied initial theme settings for '{initial_theme_name}' from config.")
            else:
                 Logger.warning(f"ShowcaseSettingsApp: Could not apply initial theme '{initial_theme_name}'. Using default KivyMD theme.")


        except Exception as e:
             Logger.error(f"ShowcaseSettingsApp: Error applying initial theme from config: {e}. Using default KivyMD theme.")
             # Set a default KivyMD theme if config loading fails or theme data is missing
             if hasattr(self, 'theme_cls'):
                  self.theme_cls.primary_palette = "BlueGray"
                  self.theme_cls.theme_style = "Dark"


        # --- Use ScreenManager for screen navigation with initial transition (can be overridden) ---
        self.screen_manager = ScreenManager(transition=FadeTransition()) # Default to FadeTransition
        Logger.info("ShowcaseSettingsApp: ScreenManager created with FadeTransition.")

        # Create the MainScreen
        main_screen = MainScreen(name="main")
        Logger.info("ShowcaseSettingsApp: MainScreen created.")
        self.screen_manager.add_widget(main_screen)
        Logger.info("ShowcaseSettingsApp: MainScreen added to ScreenManager.")

        # Create the SettingsScreen, passing the initialized ConfigManager instance
        # SettingsScreen will instantiate its own ThemeManager
        self.settings_screen = SettingsScreen(
            config_manager=self.config_manager, # Pass the shared ConfigManager instance
            # REMOVED: theme_manager=self.theme_manager, # SettingsScreen instantiates its own
            name="settings"
        )
        Logger.info("ShowcaseSettingsApp: SettingsScreen created.")
        self.screen_manager.add_widget(self.settings_screen)
        Logger.info("ShowcaseSettingsApp: SettingsScreen added to ScreenManager.")

        # Set the ScreenManager as the root widget
        Logger.info("ShowcaseSettingsApp: build method finished, returning ScreenManager.")
        return self.screen_manager


if __name__ == '__main__':
    Logger.info("ShowcaseSettingsApp: Starting application run.")
    ShowcaseSettingsApp().run()
    Logger.info("ShowcaseSettingsApp: Application run finished.")