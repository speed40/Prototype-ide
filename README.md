# Prototype IDE

A functional and customizable open-source IDE snippets built with KivyMD. It provides a modern, cross-platform development environment with extensive customization options, syntax highlighting, and a modular architecture.

**License:** MIT Licensed - Ready to tweak, hack, and extend.

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Development](#development)
- [Contributing](#contributing)
- [Showcases](#showcases)

## ✨ Features

### Core Features
- **Multi-tab editor** with syntax highlighting support
- **Integrated file manager** with project navigation
- **Interactive console** for code execution and debugging
- **Customizable themes** with dark/light mode support
- **Language profiles** for multiple programming languages
- **History management** for tracking file and project history
- **Dialog system** for user interactions and notifications

### Customization
- **Theme system** with customizable color palettes
- **Font configuration** with support for popular coding fonts
- **Layout customization** for optimal workflow
- **Language-specific settings** and syntax highlighting
- **Configurable editor behavior** (tab spaces, line limits, etc.)

### Extensibility
- **Modular architecture** for easy extension
- **Plugin-ready structure** for future enhancements
- **Comprehensive configuration system** with JSON-based settings
- **Showcase applications** demonstrating component usage

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Required Dependencies
```bash
pip install kivymd kivy
```

### Additional Font Support
The IDE supports JetBrains Mono font by default. Ensure you have the font installed on your system for optimal experience.

### Installation Steps
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd kt-ide
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt  # If available
   # Or manually install:
   pip install kivymd kivy
   ```

3. Run the IDE:
   ```bash
   python main.py  # Check for main entry point
   ```

## 🏗️ Architecture

KT IDE follows a modular architecture with clear separation of concerns:

### Core Structure
```
kt-ide/
├── core/                    # Core functionality and managers
│   ├── config_manager.py    # Configuration management system
│   ├── language_profiles.py # Language-specific configurations
│   └── themes.py           # Theme management system
├── ui/                     # User interface components
│   ├── editor.py          # Code editor component
│   ├── console.py         # Interactive console
│   ├── dialogs.py         # Dialog system
│   ├── settings_screen.py (NOT INCLUDED)
│   ├── tabs.py           # Tab management
│   └── utilities/        # UI utility components
├── showcases/             # Demo applications
├── data/                  # Configuration and data files
└── assets/               # Fonts, themes, and resources
```

### Key Components

#### Configuration Manager (`core/config_manager.py`)
- Handles loading and saving of user preferences
- Supports default and user-specific configurations
- Provides hierarchical settings management
- Supports configuration reset and reload functionality

#### UI Components (`ui/`)
- **Editor**: Full-featured code editor with syntax highlighting
- **Console**: Interactive console for code execution
- **Dialogs**: Modal dialogs for user interactions
- **File Manager**: Project and file navigation system

#### Theme System (`core/themes.py`)
- Dynamic theme switching
- Support for custom color palettes
- Dark/Light mode toggling
- Material Design integration

## ⚙️ Configuration

### Configuration Files
- `data/config.json` - Default configuration settings
- `data/user_config.json` - User-specific overrides (auto-created)

### Configuration Structure
```json
{
    "theme": {
        "current_theme": "default",
        "theme_style": "Dark",
        "primary_palette": "Blue",
        "accent_palette": "Blue"
    },
    "language": {
        "current_language": "python",
        "ui_language": "en"
    },
    "editor": {
        "tab_spaces": 4,
        "font_name": "JetBrains Mono",
        "font_size": 16,
        "line_limit": 15
    },
    "console": {
        "font_name": "JetBrains Mono",
        "font_size": 14
    },
    "general": {
        "auto_save": true
    }
}
```

### Customizing Settings
1. **Through UI**: Use the Settings Screen in the IDE
2. **Direct File Editing**: Modify `data/user_config.json`
3. **Programmatic**: Use the ConfigManager API

## 📖 Usage Guide

### Opening Projects
1. Launch KT IDE
2. Use the File Manager to navigate to your project
3. Open files in the multi-tab editor

### Editor Features
- **Syntax Highlighting**: Automatic language detection
- **Multi-tab Support**: Work on multiple files simultaneously
- **Line Numbers**: Toggle line number display
- **Auto-save**: Automatic file saving (configurable)

### Console Usage
- **Interactive Execution**: Run code snippets directly
- **Debugging**: Use for debugging and testing
- **Output Display**: View execution results and errors

### Theme CUSTOMIZATION (If setting screen is crafted)
1. Open Settings Screen
2. Navigate to Theme section
3. Select theme style (Dark/Light)
4. Choose color palettes
5. Apply changes instantly

## 🛠️ Development

### Project Structure for Developers

#### Core Modules
- **ConfigManager**: Centralized configuration handling
- **LanguageProfiles**: Language-specific syntax and behavior
- **ThemeManager**: Dynamic theme system

#### UI Architecture
- Built on KivyMD framework
- Component-based design
- Event-driven architecture
- Responsive layouts

#### Adding New Features
1. Create components in appropriate directories
2. Update `__init__.py` files for proper imports
3. Add configuration options if needed
4. Create showcase examples for testing

#### Extending Language Support
1. Add language profile in `core/language_profiles.py`
2. Define syntax highlighting rules
3. Configure language-specific settings
4. Test with showcase applications

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a development branch
3. Install development dependencies
4. Run tests using showcase applications

### Contribution Guidelines
- Follow PEP 8 style guidelines
- Add documentation for new features
- Create showcase examples for new components
- Test thoroughly before submitting pull requests

### Testing
Use the showcase applications in the `showcases/` directory to test individual components:
- `showcase_editor.py` - Test editor functionality
- `showcase_console.py` - Test console features  
- `showcase_themes.py` - Test theme system
- `showcase_dialogs.py` - Test dialog system
- `showcase_file_manager.py` - Test file management
- `showcase_history_manager.py` - Test history features

## 🎭 Showcases

The `showcases/` directory contains standalone demo applications that demonstrate individual components:

```bash
# Run individual showcases
python showcases/showcase_editor.py
python showcases/showcase_console.py
python showcases/showcase_themes.py
# ... and more
```

These showcases serve as:
- **Testing tools** for development
- **Documentation** through example
- **Feature demonstrations** for users
- **Integration guides** for developers

## 📄 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

Built with:
- [KivyMD](https://kivymd.readthedocs.io/) - Material Design components
- [Kivy](https://kivy.org/) - Cross-platform GUI framework

---

**Ready to start coding?** Launch KT IDE and begin your development journey with a modern, customizable IDE experience!
