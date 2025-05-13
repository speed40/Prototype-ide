# ui/settings_screen.py

from typing import Dict, Tuple, Any, Optional, List
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager

from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior # Keep this if ThemableBehavior is used by other classes imported here
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import OneLineListItem, IRightBodyTouch
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.behaviors import RectangularRippleBehavior # Keep this if used by other classes imported here

# Import ConfigManager and ThemeManager
from core.config_manager import ConfigManager
from core.themes import ThemeManager, get_registered_font_names

# Import dialogs for confirmation
from .dialogs import ConfirmDialog

from kivy.logger import Logger

# --- New Custom Dropdown Caller Widget (Manual Theme Handling) ---
class ThemeAwareDropdownCaller(MDBoxLayout):
    """
    A custom widget that acts as a theme-aware, non-editable caller for a dropdown menu.
    Looks like a text field with a dropdown icon but is not a text input.
    Handles theme changes manually and uses property handlers for text updates.
    """
    # Property to display the selected text
    text = StringProperty("")
    # Property to hold the hint text (e.e., "Select Font")
    hint_text = StringProperty("")

    # Define the required default handlers for the registered events
    def on_press(self, *args):
        """Default handler for the custom 'on_press' event."""
        pass

    def on_release(self, *args):
        """Default handler for the custom 'on_release' event."""
        pass

    # --- Kivy Property Event Handlers ---
    # These methods are called automatically when the 'text' or 'hint_text' properties change
    def on_text(self, instance, value):
        """Updates the label's text when the 'text' property changes."""
        Logger.info(f"ThemeAwareDropdownCaller: on_text called. value='{value}', self.hint_text='{self.hint_text}'")
        # Update the label's text to the new value if it's not empty, otherwise show hint text
        if hasattr(self, 'label') and self.label is not None:
             self.label.text = value if value else self.hint_text
             # Determine label text color based on whether text is set or hint is shown
             if value: # If text is set, use primary color
                  self.label.theme_text_color = "Primary"
             else: # If text is empty (showing hint), use hint color
                  self.label.theme_text_color = "Hint"
             Logger.info(f"ThemeAwareDropdownCaller: Label text updated to '{self.label.text}'")
        else:
             Logger.warning("ThemeAwareDropdownCaller: on_text called, but self.label is not available.")


    def on_hint_text(self, instance, value):
        """Updates the label's text if the 'text' property is empty and 'hint_text' changes."""
        Logger.info(f"ThemeAwareDropdownCaller: on_hint_text called. value='{value}', self.text='{self.text}'")
        # Update the label's text to the hint text only if the 'text' property is empty
        if not self.text:
             if hasattr(self, 'label') and self.label is not None:
                  self.label.text = value
                  self.label.theme_text_color = "Hint" # Ensure hint color is applied
                  Logger.info(f"ThemeAwareDropdownCaller: Label text updated to hint '{self.label.text}'")
             else:
                  Logger.warning("ThemeAwareDropdownCaller: on_hint_text called, but self.label is not available.")


    # Method to update colors based on the current theme
    def _update_theme_colors(self, instance=None, value=None):
        """Manually updates the colors of the label and icon based on the current theme."""
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'theme_cls'):
                theme_cls = app.theme_cls

                # Determine label text color based on whether text is set or hint is shown
                if hasattr(self, 'label') and self.label is not None:
                     if self.text: # If text is set, use primary color
                          self.label.theme_text_color = "Primary"
                     else: # If text is empty (showing hint), use hint color
                          self.label.theme_text_color = "Hint"
                else:
                     Logger.warning("ThemeAwareDropdownCaller: Could not update label theme color, self.label not available.")


                # Determine icon color - often based on primary or accent palette
                if hasattr(self, 'icon') and self.icon is not None:
                     self.icon.theme_text_color = "Primary" # Or "Accent" if preferred
                else:
                     Logger.warning("ThemeAwareDropdownCaller: Could not update icon theme color, self.icon not available.")


        except Exception as e:
             Logger.warning(f"ThemeAwareDropdownCaller: Could not update theme colors: {e}")


    def __init__(self, hint_text="", **kwargs):
        super().__init__(**kwargs)
        # Set hint_text first so on_hint_text might be called if text is initially empty
        self.hint_text = hint_text

        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(48) # Standard height for a setting row widget
        self.padding = dp(10), 0 # Standard padding
        self.spacing = dp(10) # Standard spacing


        # === CREATE THE LABEL AND ICON WIDGETS FIRST ===
        # Initial text is set here; subsequent changes handled by on_text/on_hint_text
        self.label = MDLabel(
            text=self.text if self.text else self.hint_text,
            size_hint_x=1,
            valign="center",
            theme_text_color="Hint" if not self.text else "Primary" # Initial color based on text state
        )
        self.icon = MDIconButton(
            icon="menu-down",
            size_hint_x=None,
            width=dp(48),
            theme_text_color="Primary" # Initial icon color
        )

        # === ADD WIDGETS TO THE LAYOUT ===
        self.add_widget(self.label)
        self.add_widget(self.icon)

        # --- REMOVED DIRECT BINDINGS HERE ---
        # The text and hint_text properties will now automatically call on_text and on_hint_text


        # Register event types for custom press/release events
        self.register_event_type('on_press')
        self.register_event_type('on_release')

        # --- Manual Theme Binding ---
        app = MDApp.get_running_app()
        if app and hasattr(app, 'theme_cls'):
            app.theme_cls.bind(
                theme_style=self._update_theme_colors,
                primary_palette=self._update_theme_colors,
                accent_palette=self._update_theme_colors,
                primary_hue=self._update_theme_colors
            )
            self._update_theme_colors() # Initial call


    # Override touch methods to dispatch custom events and consume touch
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            Logger.info(f"ThemeAwareDropdownCaller: Touch Down on {self.hint_text or 'Dropdown Caller'}.")
            self.dispatch('on_press')
            touch.grab(self)
            return True

        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current == self:
            Logger.info(f"ThemeAwareDropdownCaller: Touch Up on {self.hint_text or 'Dropdown Caller'}.")
            touch.ungrab(self)
            if self.collide_point(*touch.pos):
                self.dispatch('on_release')
            return True

        return super().on_touch_up(touch)


    def on_parent(self, instance, value):
        """Handle parent changes to unbind from theme_cls when removed."""
        # Ensure unbinding happens *before* super call removes the widget
        if value is None:
             Logger.info("ThemeAwareDropdownCaller: Widget removed from parent. Unbinding theme_cls.")
             app = MDApp.get_running_app()
             if app and hasattr(app, 'theme_cls'):
                  # Ensure the bound method exists before unbinding
                  if hasattr(self, '_update_theme_colors'):
                       app.theme_cls.unbind(
                            theme_style=self._update_theme_colors,
                            primary_palette=self._update_theme_colors,
                            accent_palette=self._update_theme_colors,
                            primary_hue=self._update_theme_colors
                       )
                  else:
                       Logger.warning("ThemeAwareDropdownCaller: _update_theme_colors method not found for unbinding.")

        # REMOVED: super().on_parent(instance, value) # Corrected: Remove this line causing AttributeError


class SettingsScreen(MDScreen):
    """
    A screen for viewing and modifying application settings.
    Interacts with the ConfigManager and ThemeManager.
    """

    # ConfigManager will now be passed in __init__ and manage paths internally
    config_manager = ObjectProperty(None)

    # Removed theme_manager attribute - instantiated locally

    # Removed DEFAULT_CONFIG_PATH - ConfigManager handles paths

    # Accept the ConfigManager instance - NO ThemeManager parameter needed now
    def __init__(self, config_manager: ConfigManager, **kwargs):
        super().__init__(**kwargs)
        Logger.info("SettingsScreen: Initializing with config manager")

        # Accept the ConfigManager instance from the caller
        self.config_manager = config_manager

        # Instantiate ThemeManager locally
        self.theme_manager = ThemeManager()
        self.theme_manager.load_themes_from_json() # Load themes on init

        # Initialize storage for UI components
        self._setting_widgets: Dict[Tuple[str, str], Any] = {}
        # Updated type hint to use the new caller widget
        self._dropdown_callers: Dict[Tuple[str, str], ThemeAwareDropdownCaller] = {}
        self._dropdown_menus: Dict[Tuple[str, str], MDDropdownMenu] = {}

        self._setup_ui()
        # Bind to on_enter to load settings when screen becomes active
        self.bind(on_enter=self._load_settings_into_ui)
        # Bind to on_pre_leave to dismiss dropdowns before leaving
        self.bind(on_pre_leave=self._dismiss_dropdowns)


    def _setup_ui(self) -> None:
        """Builds the initial UI structure of the settings screen."""
        Logger.debug("SettingsScreen: Building UI structure")

        self.main_layout = MDBoxLayout(orientation="vertical")

        # --- Toolbar ---
        self._setup_toolbar()

        # --- Scrollable Content Area ---
        self._setup_scrollable_content()

        self.add_widget(self.main_layout)

    def _setup_toolbar(self) -> None:
        """Configures the top app bar, including the reset button."""
        self.toolbar = MDTopAppBar(title="Settings")
        self.toolbar.left_action_items = [
            ["arrow-left", lambda x: self._close_settings()]
        ]
        # Added a 'Reset' icon button to the right action items
        self.toolbar.right_action_items = [
            ["content-save", lambda x: self._save_settings()],
            ["reload", lambda x: self._reload_settings()],
            # Add the reset button that triggers the confirmation dialog
            ["undo", lambda x: self._show_reset_confirmation()] # Using 'undo' icon for reset
        ]
        self.main_layout.add_widget(self.toolbar)

    def _setup_scrollable_content(self) -> None:
        """Configures the scrollable settings content area."""
        self.settings_scrollview = MDScrollView()
        self.settings_content_layout = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=dp(10),
            spacing=dp(15),
            adaptive_height=True
        )
        self.settings_content_layout.bind(
            minimum_height=self.settings_content_layout.setter("height")
        )

        self._populate_settings_ui()
        self.settings_scrollview.add_widget(self.settings_content_layout)
        self.main_layout.add_widget(self.settings_scrollview)

    def _populate_settings_ui(self) -> None:
        """Populates the settings_content_layout with UI elements."""
        Logger.debug("SettingsScreen: Populating settings UI")

        self.settings_content_layout.clear_widgets()
        self._clear_ui_references()

        # Add sections with their settings
        self._add_theme_settings_section()
        self._add_editor_settings_section()
        self._add_console_settings_section()
        self._add_general_settings_section()

        # Add spacer at bottom
        self.settings_content_layout.add_widget(
            Widget(size_hint_y=None, height=dp(20))
        )

        self._initialize_dropdowns()

    def _clear_ui_references(self) -> None:
        """Clears all references to UI components."""
        self._setting_widgets.clear()
        self._dropdown_callers.clear()

        # Properly clean up existing dropdown menus
        for menu in self._dropdown_menus.values():
            if menu:
                menu.dismiss()
        self._dropdown_menus.clear()

    def _add_theme_settings_section(self) -> None:
        """Adds theme-related settings to the UI."""
        self.settings_content_layout.add_widget(
            self._create_section_label("Theme Settings")
        )

        # Theme Style Switch
        self._setting_widgets[("theme", "theme_style")] = self._add_setting_row(
            "Theme Style:",
            self._create_switch(),
            "theme",
            "theme_style"
        )

        # Theme Name Dropdown - Use the new ThemeAwareDropdownCaller
        theme_name_caller = self._create_dropdown_caller("theme", "current_theme")
        self._dropdown_callers[("theme", "current_theme")] = theme_name_caller
        self._add_setting_row(
            "Theme Name:",
            theme_name_caller,
            "theme",
            "current_theme"
        )

    def _add_editor_settings_section(self) -> None:
        """Adds editor-related settings to the UI."""
        self.settings_content_layout.add_widget(
            self._create_section_label("Editor Settings")
        )

        # Editor settings rows
        self._setting_widgets[("editor", "tab_spaces")] = self._add_setting_row(
            "Tab Spaces:",
            self._create_numeric_textfield("editor", "tab_spaces"),
            "editor",
            "tab_spaces"
        )

        # Editor Font Name Dropdown - Use the new ThemeAwareDropdownCaller
        editor_font_name_caller = self._create_dropdown_caller("editor", "font_name")
        self._dropdown_callers[("editor", "font_name")] = editor_font_name_caller
        self._add_setting_row(
            "Font Name:",
            editor_font_name_caller,
            "editor",
            "font_name"
        )

        self._setting_widgets[("editor", "font_size")] = self._add_setting_row(
            "Font Size:",
            self._create_numeric_textfield("editor", "font_size"),
            "editor",
            "font_size"
        )

        self._setting_widgets[("editor", "line_limit")] = self._add_setting_row(
            "Line Limit:",
            self._create_numeric_textfield("editor", "line_limit"),
            "editor",
            "line_limit"
        )

    def _add_console_settings_section(self) -> None:
        """Adds console-related settings to the UI."""
        self.settings_content_layout.add_widget(
            self._create_section_label("Console Settings")
        )

        # Console Font Name Dropdown - Use the new ThemeAwareDropdownCaller
        console_font_name_caller = self._create_dropdown_caller("console", "font_name")
        self._dropdown_callers[("console", "font_name")] = console_font_name_caller
        self._add_setting_row(
            "Font Name:",
            console_font_name_caller,
            "console",
            "font_name"
        )

        self._setting_widgets[("console", "font_size")] = self._add_setting_row(
            "Font Size:",
            self._create_numeric_textfield("console", "font_size"),
            "console",
            "font_size"
        )

    def _add_general_settings_section(self) -> None:
        """Adds general settings to the UI."""
        self.settings_content_layout.add_widget(
            self._create_section_label("General Settings")
        )

        self._setting_widgets[("general", "auto_save")] = self._add_setting_row(
            "Auto Save:",
            self._create_switch(),
            "general",
            "auto_save"
        )

    def _create_section_label(self, text: str) -> MDLabel:
        """Creates a styled section header label."""
        return MDLabel(
            text=f"[b]{text}[/b]",
            size_hint_y=None,
            height=dp(30),
            font_style="H6",
            markup=True
        )

    def _create_switch(self) -> MDSwitch:
        """Creates a standardized switch widget."""
        return MDSwitch(size_hint_x=0.2)

    def _create_textfield(self, hint_text: str, editable: bool = True) -> MDTextField:
        """Creates a standardized text field widget."""
        return MDTextField(
            size_hint_x=1,
            hint_text=hint_text,
            readonly=not editable,
            mode="rectangle",
            disabled=False
        )

    def _create_numeric_textfield(self, section: str, key: str) -> MDTextField:
        """Creates a numeric input text field."""
        textfield = self._create_textfield(
            hint_text=f"Enter {key.replace('_', ' ').title()}",
            editable=True
        )
        textfield.input_filter = "int"
        return textfield

    # New method to create the custom dropdown caller widget
    def _create_dropdown_caller(self, section: str, key: str) -> ThemeAwareDropdownCaller:
        """Creates a theme-aware dropdown caller widget."""
        # The hint_text for the caller is set by its own property
        return ThemeAwareDropdownCaller(
            hint_text=f"Select {key.replace('_', ' ').title()}"
        )


    def _add_setting_row(self, label_text: str, setting_widget: Widget,
                         section: str, key: str) -> Widget:
        """
        Creates a horizontal layout for a single setting row.
        Returns the setting widget for further configuration.
        """
        row_layout = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(10),
            padding=(dp(10), 0)
        )

        row_layout.add_widget(MDLabel(
            text=label_text,
            size_hint_x=None,
            width=dp(150),
            valign="center",
            markup=True
        ))

        row_layout.add_widget(setting_widget)
        self.settings_content_layout.add_widget(row_layout)

        # Set up appropriate bindings based on widget type
        if isinstance(setting_widget, MDSwitch):
            setting_widget.bind(
                active=lambda instance, value: self._on_setting_changed(section, key, value)
            )
        elif isinstance(setting_widget, MDTextField):
            # Regular text fields
            setting_widget.bind(
                on_text_validate=lambda instance: self._on_setting_changed(section, key, instance.text)
            )
            setting_widget.bind(
                focus=lambda instance, focus: self._on_setting_textfield_focus(instance, focus, section, key)
            )
        elif isinstance(setting_widget, ThemeAwareDropdownCaller):
             # Bind the custom on_release event for the new dropdown caller
             setting_widget.bind(
                 on_release=lambda instance: self._open_dropdown(section, key)
             )


        return setting_widget

    def _initialize_dropdowns(self) -> None:
        """Initializes MDDropdownMenu instances for settings that use them."""
        Logger.debug("SettingsScreen: Initializing dropdown menus")

        # Initialize theme dropdown - using the locally instantiated theme_manager
        theme_names = self.theme_manager.get_available_themes()
        theme_name_caller = self._dropdown_callers.get(("theme", "current_theme"))

        if theme_name_caller:
             theme_items = [
                 {
                     "viewclass": "OneLineListItem",
                     "text": theme_name,
                     "height": dp(48),
                     "on_release": lambda x=theme_name: self._select_dropdown_item("theme", "current_theme", x),
                 } for theme_name in theme_names
             ]

             self._create_or_update_dropdown(
                 ("theme", "current_theme"),
                 theme_name_caller,
                 theme_items,
                 max(4, len(max(theme_names, key=len)) // 5) if theme_names else 4
             )


        # Initialize font dropdowns - getting font names directly
        font_names = get_registered_font_names()
        editor_font_name_caller = self._dropdown_callers.get(("editor", "font_name"))
        console_font_name_caller = self._dropdown_callers.get(("console", "font_name"))


        if editor_font_name_caller:
             font_items = [
                 {
                     "viewclass": "OneLineListItem",
                     "text": font_name,
                     "height": dp(48),
                     "on_release": lambda x=font_name: self._select_dropdown_item("editor", "font_name", x),
                 } for font_name in font_names
             ]

             self._create_or_update_dropdown(
                 ("editor", "font_name"),
                 editor_font_name_caller,
                 font_items,
                 max(4, len(max(font_names, key=len)) // 5) if font_names else 4
             )

        if console_font_name_caller:
             font_items = [
                 {
                     "viewclass": "OneLineListItem",
                     "text": font_name,
                     "height": dp(48),
                     "on_release": lambda x=font_name: self._select_dropdown_item("console", "font_name", x),
                 } for font_name in font_names
             ]

             self._create_or_update_dropdown(
                 ("console", "font_name"),
                 console_font_name_caller,
                 font_items,
                 max(4, len(max(font_names, key=len)) // 5) if font_names else 4
             )


    def _create_or_update_dropdown(self, key: Tuple[str, str], caller: Widget,
                                  items: List[Dict], width_mult: int) -> None:
        """Creates or updates a dropdown menu."""
        # Use MDApp.get_running_app() to access the theme_cls
        app = MDApp.get_running_app()
        bg_color = app.theme_cls.bg_dark if app.theme_cls.theme_style == "Dark" else app.theme_cls.bg_light


        if key in self._dropdown_menus and self._dropdown_menus[key].caller == caller:
            # Menu exists and caller is the same, just update items and width
            self._dropdown_menus[key].items = items
            self._dropdown_menus[key].width_mult = width_mult
            self._dropdown_menus[key].background_color = bg_color # Update color on theme change
        else:
            # Create new menu
            if key in self._dropdown_menus and self._dropdown_menus[key]:
                self._dropdown_menus[key].dismiss()

            self._dropdown_menus[key] = MDDropdownMenu(
                caller=caller,
                items=items,
                width_mult=width_mult,
                position="bottom",
                ver_growth="down",
                on_dismiss=self._on_menu_dismiss,
                background_color=bg_color # Set initial color
            )
            # Bind to theme_cls changes to update dropdown background color
            if app and hasattr(app, 'theme_cls'):
                 app.theme_cls.bind(theme_style=self._update_dropdown_menu_colors)

    # Removed _handle_dropdown_caller_touch as the new widget handles its own touch

    def _on_menu_dismiss(self, *args) -> None:
        """Handler for when any MDDropdownMenu is dismissed."""
        Logger.debug("SettingsScreen: Dropdown menu dismissed")

    def _open_dropdown(self, section: str, key: str) -> None:
        """Opens the dropdown menu associated with a setting."""
        Logger.debug(f"SettingsScreen: Opening dropdown for '{section}.{key}'")
        dropdown_menu = self._dropdown_menus.get((section, key))
        if dropdown_menu:
            dropdown_menu.open()

    def _select_dropdown_item(self, section: str, key: str, text: str) -> None:
        """Handler for selecting an item from a dropdown menu."""
        Logger.debug(f"SettingsScreen: Selected '{text}' for '{section}.{key}'")

        caller_widget = self._dropdown_callers.get((section, key))
        if caller_widget:
            # For the new ThemeAwareDropdownCaller, set its 'text' property
            caller_widget.text = text

        dropdown_menu = self._dropdown_menus.get((section, key))
        if dropdown_menu:
            dropdown_menu.dismiss()

        self._on_setting_changed(section, key, text)

        if section == "theme" and key == "current_theme":
            self._apply_theme_settings(text)

    def _apply_theme_settings(self, theme_name: str) -> None:
        """Applies the selected theme settings to the KivyMD app."""
        Logger.debug(f"SettingsScreen: Applying theme settings for '{theme_name}'")
        # Use the locally instantiated theme_manager
        theme_data = self.theme_manager.get_theme_settings(theme_name)
        if not theme_data:
            Logger.warning(f"SettingsScreen: No theme data found for '{theme_name}'")
            return

        kivymd_settings = theme_data.get('kivymd_settings', {})
        app = MDApp.get_running_app()
        if hasattr(app, 'theme_cls'):
            for attr, value in kivymd_settings.items():
                if hasattr(app.theme_cls, attr):
                    setattr(app.theme_cls, attr, value)
                    Logger.debug(f"SettingsScreen: Set theme_cls.{attr} = '{value}'")

        # Update dropdown menu colors (this binding is now handled in _create_or_update_dropdown)
        # self._update_dropdown_menu_colors()


    def _update_dropdown_menu_colors(self, *args) -> None:
        """Updates all dropdown menu colors to match current theme."""
        app = MDApp.get_running_app()
        if not hasattr(app, 'theme_cls'):
             return

        bg_color = app.theme_cls.bg_dark if app.theme_cls.theme_style == "Dark" else app.theme_cls.bg_light
        Logger.debug(f"SettingsScreen: Updating dropdown menu colors to {bg_color}")
        for menu in self._dropdown_menus.values():
            if menu and hasattr(menu, 'background_color'):
                 menu.background_color = bg_color


    def _dismiss_dropdowns(self, *args) -> None:
        """Dismisses any open dropdown menus when the screen is left."""
        Logger.debug("SettingsScreen: Dismissing all dropdowns")
        for menu in self._dropdown_menus.values():
            if menu and menu.parent:
                menu.dismiss()
        # Also unbind theme_cls color updates when screen is left to avoid memory leaks
        app = MDApp.get_running_app()
        if app and hasattr(app, 'theme_cls'):
             if hasattr(self, '_update_dropdown_menu_colors'):
                  try:
                      app.theme_cls.unbind(theme_style=self._update_dropdown_menu_colors)
                      Logger.debug("SettingsScreen: Unbound dropdown menu color updates.")
                  except ReferenceError:
                       Logger.warning("SettingsScreen: Unbind failed, _update_dropdown_menu_colors no longer referenced.")


    def _on_setting_changed(self, section: str, key: str, value: Any) -> None:
        """Generic handler for setting changes that updates config."""
        Logger.debug(f"SettingsScreen: Setting change '{section}.{key}' = '{value}'")

        # Get expected type from current config value
        current_value = self.config_manager.get_setting(section, key)
        # Attempt to infer type from the *current* config value, default to string if not found
        expected_type = type(current_value) if current_value is not None else str

        try:
            # Convert value to expected type
            if expected_type is bool:
                # MDSwitch provides boolean value directly
                converted_value = bool(value)
            elif expected_type is int:
                 # Handle potential empty string from textfield before conversion
                 if isinstance(value, str) and value.strip() == "":
                      converted_value = 0 # Or handle as None/error depending on desired behavior
                 else:
                      converted_value = int(value)
            elif expected_type is float:
                 # Handle potential empty string from textfield before conversion
                 if isinstance(value, str) and value.strip() == "":
                      converted_value = 0.0 # Or handle as None/error
                 else:
                      converted_value = float(value)
            else: # Default to string conversion for others, including dropdown values
                 converted_value = str(value)


            # Update config
            self.config_manager.set_setting(section, key, converted_value)

            # Auto-save if enabled
            if self.config_manager.get_setting("general", "auto_save", False):
                self.config_manager.save_config()
                Logger.debug("SettingsScreen: Auto-saved config")

            # Special handling for theme-related settings
            if section == "theme" and key == "current_theme":
                self._apply_theme_settings(converted_value)
            elif section == "theme" and key == "theme_style":
                 # theme_style change also needs to re-apply theme settings to update colors
                 current_theme = self.config_manager.get_setting("theme", "current_theme")
                 self._apply_theme_settings(current_theme)


        except (ValueError, TypeError) as e:
            Logger.error(f"SettingsScreen: Failed to convert value '{value}' for '{section}.{key}': {e}")
            # Revert UI to current config value
            self._update_setting_widget(section, key, current_value)
        except Exception as e:
             Logger.error(f"SettingsScreen: Unexpected error handling setting change '{section}.{key}' = '{value}': {e}")
             # Revert UI on unexpected errors too
             self._update_setting_widget(section, key, current_value)


    def _on_setting_textfield_focus(self, instance: MDTextField,
                                     focus: bool, section: str, key: str) -> None:
        """Handler for text field focus changes to save on focus loss."""
        if not focus:
            Logger.debug(f"SettingsScreen: TextField for '{section}.{key}' lost focus")
            # Trigger change handler when focus is lost for text fields
            self._on_setting_changed(section, key, instance.text)

    def _update_setting_widget(self, section: str, key: str, value: Any) -> None:
        """Updates a setting widget with the given value."""
        widget = self._setting_widgets.get((section, key))
        if not widget:
             # Also check dropdown callers for updates
             widget = self._dropdown_callers.get((section, key))
             if not widget:
                Logger.warning(f"SettingsScreen: Widget not found for setting '{section}.{key}' to update.")
                return


        if isinstance(widget, MDSwitch):
            widget.active = bool(value)
            Logger.debug(f"SettingsScreen: Updated Switch '{section}.{key}' to {value}")
        elif isinstance(widget, MDTextField):
            widget.text = str(value)
            Logger.debug(f"SettingsScreen: Updated TextField '{section}.{key}' to '{value}'")
        elif isinstance(widget, ThemeAwareDropdownCaller):
             # For the new dropdown caller, update its 'text' property
             widget.text = str(value)
             Logger.debug(f"SettingsScreen: Updated DropdownCaller '{section}.{key}' text to '{value}'")

    def _load_settings_into_ui(self, *args) -> None:
        """Loads current settings from ConfigManager into UI widgets."""
        Logger.debug("SettingsScreen: Loading settings into UI")

        # Load values into all registered widgets (switches, text fields)
        for (section, key), widget in self._setting_widgets.items():
            value = self.config_manager.get_setting(section, key)
            self._update_setting_widget(section, key, value)

        # Load values into dropdown caller widgets
        for (section, key), caller in self._dropdown_callers.items():
            value = self.config_manager.get_setting(section, key)
            # Update the 'text' property of the new dropdown caller
            caller.text = str(value)
            Logger.debug(f"SettingsScreen: Loaded dropdown caller '{section}.{key}' with text '{value}'")


        # Reinitialize dropdowns to ensure they're up-to-date with available themes/fonts
        self._initialize_dropdowns()

        # Apply current theme settings from config to KivyMD app when entering the screen
        current_theme = self.config_manager.get_setting("theme", "current_theme", "default")
        self._apply_theme_settings(current_theme)


    def _save_settings(self) -> None:
        """Explicitly saves the current settings from the UI to the config file."""
        Logger.debug("SettingsScreen: Explicit save triggered")

        # Force save any focused text fields by triggering focus loss
        # Iterate over _setting_widgets to find MDTextFields
        for (section, key), widget in self._setting_widgets.items():
            if isinstance(widget, MDTextField) and widget.focus:
                 Logger.debug(f"SettingsScreen: Forcing save on focused TextField '{section}.{key}'")
                 # Call the focus loss handler directly, setting focus to False
                 self._on_setting_textfield_focus(widget, False, section, key)

        # Note: ThemeAwareDropdownCallers don't use focus or have text_validate,
        # their value is saved immediately when an item is selected via _select_dropdown_item,
        # or when _on_setting_changed is triggered by the MDSwitch or MDTextField.

        # Final save of the config file
        self.config_manager.save_config()
        Logger.info("SettingsScreen: Config saved explicitly")

    def _show_reset_confirmation(self) -> None:
        """Shows a confirmation dialog before resetting settings."""
        Logger.debug("SettingsScreen: Showing reset confirmation dialog.")
        # Instantiate ConfirmDialog (it handles its own theme colors based on app theme)
        # Check if dialog already exists and is open, dismiss if so
        if hasattr(self, '_confirm_dialog') and self._confirm_dialog:
             self._confirm_dialog.dismiss()

        self._confirm_dialog = ConfirmDialog(
            title="Reset Settings?",
            text="Are you sure you want to reset all settings to their default values?\n\nThis action cannot be undone."
        )
        # Open the dialog and pass the callback for when confirmed
        self._confirm_dialog.open(confirm_callback=self._reset_settings)

    def _reset_settings(self) -> None:
        """Resets settings to default via ConfigManager and updates the UI."""
        Logger.info("SettingsScreen: Resetting settings to defaults.")
        if self.config_manager:
             # Call the new reset method on the ConfigManager
             reset_config_data = self.config_manager.reset_to_defaults()
             Logger.info("SettingsScreen: Settings reset by ConfigManager.")
             # Reload the UI with the new default settings
             self._load_settings_into_ui()
             Logger.info("SettingsScreen: UI updated after reset.")
             # TODO: Potentially show a small notification to the user (e.g., toast)

             # Apply theme settings after reset, as current_theme might have changed
             current_theme = reset_config_data.get("theme", {}).get("current_theme", "default")
             self._apply_theme_settings(current_theme)

        else:
             Logger.error("SettingsScreen: ConfigManager is not available. Cannot reset settings.")


    def _reload_settings(self) -> None:
        """Reloads settings from the config file and updates the UI."""
        Logger.debug("SettingsScreen: Reloading settings")
        self._dismiss_dropdowns()
        self.config_manager.reload_config()
        self._load_settings_into_ui()

    def _close_settings(self) -> None:
        """Dismisses the settings screen by navigating back."""
        Logger.debug("SettingsScreen: Closing settings screen")
        # Explicitly save settings before closing if auto_save is false or to be safe
        self._save_settings() # Ensure settings are saved

        if self.manager:
            from kivy.uix.screenmanager import SwapTransition
            self.manager.transition = SwapTransition()
            self.manager.current = 'main'
            Logger.info("SettingsScreen: Navigated back to 'main'.")
        else:
            Logger.warning("SettingsScreen: Manager is None. Cannot navigate back.")

# The ThemeAwareDropdownText class is no longer needed if only ThemeAwareDropdownCaller is used.
# Depending on other parts of the application, it might be removed entirely.
# For now, commenting it out.
# class ThemeAwareDropdownText(MDTextField, ThemableBehavior, RectangularRippleBehavior):
#     """A theme-aware text field used for dropdown callers."""
#     pass