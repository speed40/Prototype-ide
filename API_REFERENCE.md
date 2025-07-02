# KT IDE API Reference

This document provides detailed API documentation for KT IDE's core components and modules.

## 📋 Table of Contents

- [Core Module](#core-module)
  - [ConfigManager](#configmanager)
  - [LanguageProfiles](#languageprofiles)
  - [ThemeManager](#thememanager)
- [UI Module](#ui-module)
  - [CodeEditor](#codeeditor)
  - [Console](#console)
  - [Dialogs](#dialogs)
  - [SettingsScreen](#settingsscreen)
- [Utilities](#utilities)
- [Usage Examples](#usage-examples)

## 🔧 Core Module

### ConfigManager

The central configuration management system for KT IDE.

**Location**: `core/config_manager.py`

#### Class Definition
```python
class ConfigManager:
    def __init__(self, 
                 user_config_filepath: str | Path = "data/user_config.json",
                 default_config_filepath: str | Path = "data/config.json")
```

#### Methods

##### `load_config() -> None`
Loads configuration from default and user config files.

```python
config_manager = ConfigManager()
config_manager.load_config()
```

##### `save_config() -> None`
Saves current configuration to user config file.

```python
config_manager.save_config()
```

##### `get_setting(section: str, key: str, default_value: Any = None) -> Any`
Retrieves a specific setting value.

**Parameters:**
- `section` (str): Configuration section name
- `key` (str): Setting key within the section
- `default_value` (Any): Fallback value if setting not found

**Returns:** The setting value or default_value

```python
font_size = config_manager.get_setting('editor', 'font_size', 16)
theme_style = config_manager.get_setting('theme', 'theme_style', 'Dark')
```

##### `set_setting(section: str, key: str, value: Any) -> None`
Sets a specific setting value in memory.

**Parameters:**
- `section` (str): Configuration section name
- `key` (str): Setting key within the section
- `value` (Any): Value to set

```python
config_manager.set_setting('editor', 'font_size', 18)
config_manager.set_setting('theme', 'theme_style', 'Light')
```

##### `get_all_settings() -> Dict`
Returns a copy of the entire configuration dictionary.

```python
all_settings = config_manager.get_all_settings()
```

##### `reset_to_defaults() -> Dict`
Resets configuration to default values and saves.

**Returns:** The newly loaded default configuration

```python
defaults = config_manager.reset_to_defaults()
```

##### `reload_config() -> None`
Forces a reload of configuration from files.

```python
config_manager.reload_config()
```

#### Configuration Structure

```python
{
    "theme": {
        "current_theme": str,      # Theme name
        "theme_style": str,        # "Dark" or "Light"
        "primary_palette": str,    # Primary color palette
        "accent_palette": str      # Accent color palette
    },
    "language": {
        "current_language": str,   # Active programming language
        "ui_language": str         # UI language code
    },
    "editor": {
        "tab_spaces": int,         # Number of spaces per tab
        "font_name": str,          # Font family name
        "font_size": int,          # Font size in points
        "line_limit": int          # Maximum lines to display
    },
    "console": {
        "font_name": str,          # Console font family
        "font_size": int           # Console font size
    },
    "general": {
        "auto_save": bool          # Enable auto-save feature
    }
}
```

### LanguageProfiles

Manages language-specific configurations and syntax definitions.

**Location**: `core/language_profiles.py`

#### Key Features
- Syntax highlighting rules
- Language-specific settings
- File extension mappings
- Keyword definitions

### ThemeManager

Handles dynamic theme switching and customization.

**Location**: `core/themes.py`

#### Key Features
- Dynamic theme loading
- Color palette management
- Dark/Light mode switching
- Material Design integration

## 🎨 UI Module

### CodeEditor

The main code editing component with syntax highlighting and multi-tab support.

**Location**: `ui/editor.py`

#### Key Features
- Multi-tab editing
- Syntax highlighting
- Line number display
- Auto-save functionality
- Configurable fonts and themes

#### Integration Example
```python
from ui.editor import CodeEditor
from core.config_manager import ConfigManager

config_manager = ConfigManager()
editor = CodeEditor(config_manager)
```

### Console

Interactive console component for code execution and debugging.

**Location**: `ui/console.py`

#### Key Features
- Interactive Python console
- Command history
- Output display
- Error handling
- Configurable appearance

#### Integration Example
```python
from ui.console import Console
from core.config_manager import ConfigManager

config_manager = ConfigManager()
console = Console(config_manager)
```

### Dialogs

Comprehensive dialog system for user interactions.

**Location**: `ui/dialogs.py`

#### Available Dialog Types

##### BaseDialog
Base class for all dialogs.

##### ErrorDialog
Displays error messages to users.

```python
from ui.dialogs import ErrorDialog

error_dialog = ErrorDialog()
error_dialog.show_error("An error occurred", "Detailed error message")
```

##### ConfirmDialog
Confirmation dialogs for user actions.

```python
from ui.dialogs import ConfirmDialog

confirm_dialog = ConfirmDialog()
confirm_dialog.show_confirm("Delete file?", "This action cannot be undone")
```

##### InfoDialog
Information dialogs for notifications.

```python
from ui.dialogs import InfoDialog

info_dialog = InfoDialog()
info_dialog.show_info("Operation Complete", "File saved successfully")
```

##### WarningDialog
Warning dialogs for cautionary messages.

```python
from ui.dialogs import WarningDialog

warning_dialog = WarningDialog()
warning_dialog.show_warning("Unsaved Changes", "You have unsaved changes")
```

### SettingsScreen

Comprehensive settings management interface.

**Location**: `ui/settings_screen.py`

#### Key Features
- Theme customization
- Editor preferences
- Language settings
- Font configuration
- Real-time preview

#### Integration Example
```python
from ui.settings_screen import SettingsScreen
from core.config_manager import ConfigManager

config_manager = ConfigManager()
settings = SettingsScreen(config_manager)
```

## 🛠️ Utilities

### File Manager Utilities

**Location**: `ui/utilities/file_manager.py`

#### Key Features
- Project navigation
- File operations
- Directory browsing
- File type detection

### History Manager

**Location**: `ui/utilities/history_manager.py`

#### Key Features
- File access history
- Project history
- Recent items tracking
- History persistence

### Line Number Utilities

**Location**: `ui/utilities/line_number.py`

#### Key Features
- Line number display
- Syntax highlighting integration
- Performance optimization
- Configurable appearance

## 📚 Usage Examples

### Basic Application Setup

```python
from kivymd.app import MDApp
from core.config_manager import ConfigManager
from ui.editor import CodeEditor
from ui.console import Console
from ui.settings_screen import SettingsScreen

class KTIDEApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        
    def build(self):
        # Initialize components
        self.editor = CodeEditor(self.config_manager)
        self.console = Console(self.config_manager)
        self.settings = SettingsScreen(self.config_manager)
        
        # Build main interface
        return self.create_main_layout()
        
    def create_main_layout(self):
        # Implementation details...
        pass

if __name__ == "__main__":
    KTIDEApp().run()
```

### Configuration Management

```python
from core.config_manager import ConfigManager

# Initialize configuration manager
config = ConfigManager()

# Get settings
font_size = config.get_setting('editor', 'font_size', 16)
theme_style = config.get_setting('theme', 'theme_style', 'Dark')

# Update settings
config.set_setting('editor', 'font_size', 18)
config.set_setting('theme', 'theme_style', 'Light')

# Save changes
config.save_config()
```

### Theme Management

```python
from core.config_manager import ConfigManager

config = ConfigManager()

# Switch to light theme
config.set_setting('theme', 'theme_style', 'Light')
config.set_setting('theme', 'primary_palette', 'Blue')
config.save_config()

# Apply theme changes (implementation specific)
app.apply_theme_changes()
```

### Dialog Usage

```python
from ui.dialogs import ErrorDialog, ConfirmDialog, InfoDialog

# Show error dialog
error_dialog = ErrorDialog()
error_dialog.show_error("File Error", "Could not open file")

# Show confirmation dialog with callback
def on_confirm():
    # Handle confirmation
    pass
    
def on_cancel():
    # Handle cancellation
    pass

confirm_dialog = ConfirmDialog()
confirm_dialog.show_confirm(
    "Delete File?", 
    "This action cannot be undone",
    on_confirm,
    on_cancel
)

# Show info dialog
info_dialog = InfoDialog()
info_dialog.show_info("Success", "File saved successfully")
```

### Component Integration

```python
from core.config_manager import ConfigManager
from ui.editor import CodeEditor
from ui.console import Console

# Shared configuration
config_manager = ConfigManager()

# Initialize components with shared config
editor = CodeEditor(config_manager)
console = Console(config_manager)

# Components automatically sync with configuration changes
config_manager.set_setting('editor', 'font_size', 20)
config_manager.save_config()

# Editor will use new font size
editor.update_from_config()
```

## 🔗 Event System

### Configuration Events
Components can listen for configuration changes:

```python
class MyComponent:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        # Bind to configuration updates
        self.config_manager.bind(on_config_changed=self.on_config_changed)
    
    def on_config_changed(self, section, key, value):
        if section == 'theme' and key == 'theme_style':
            self.update_theme(value)
```

### Dialog Events
Handle dialog responses:

```python
def show_save_dialog(self):
    dialog = ConfirmDialog()
    dialog.bind(on_confirm=self.save_file)
    dialog.bind(on_cancel=self.cancel_save)
    dialog.show_confirm("Save Changes?", "Save before closing?")

def save_file(self, *args):
    # Handle save action
    pass

def cancel_save(self, *args):
    # Handle cancel action
    pass
```

This API reference provides the foundation for extending and customizing KT IDE. For additional examples, refer to the showcase applications in the `showcases/` directory.