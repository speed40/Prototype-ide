# Contributing to KT IDE

Thank you for your interest in contributing to KT IDE! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Feature Requests](#feature-requests)
- [Bug Reports](#bug-reports)

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our code of conduct:
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professional communication

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Basic knowledge of KivyMD framework
- Familiarity with Material Design principles

### Setting Up Development Environment
1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/kt-ide.git
   cd kt-ide
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install kivymd kivy
   ```

4. **Test your setup**
   ```bash
   python showcases/showcase_editor.py
   ```

## 🏗️ Project Structure

Understanding the project structure is crucial for effective contributions:

```
kt-ide/
├── core/                    # Core functionality
│   ├── config_manager.py    # Configuration system
│   ├── language_profiles.py # Language definitions
│   └── themes.py           # Theme management
├── ui/                     # User interface components
│   ├── editor.py          # Main editor component
│   ├── console.py         # Interactive console
│   ├── dialogs.py         # Dialog systems
│   ├── settings_screen.py # Settings interface
│   └── utilities/         # UI utilities
├── showcases/             # Demo applications
├── data/                  # Configuration files
└── assets/               # Resources (fonts, themes)
```

### Key Design Principles
- **Modularity**: Each component should be self-contained
- **Configuration-driven**: Use ConfigManager for all settings
- **Showcase-first**: Create showcase examples for new features
- **KivyMD compliance**: Follow Material Design guidelines

## 📝 Coding Standards

### Python Style Guide
Follow PEP 8 with these specific guidelines:

#### Code Formatting
```python
# Good: Clear, descriptive names
class CodeEditor(MDTextFieldWidget):
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager

# Good: Proper docstrings
def load_file(self, file_path: str) -> bool:
    """
    Load a file into the editor.
    
    Args:
        file_path (str): Path to the file to load
        
    Returns:
        bool: True if successful, False otherwise
    """
```

#### Import Organization
```python
# Standard library imports
import json
import os
from pathlib import Path
from typing import Dict, Any

# Third-party imports
from kivy.logger import Logger
from kivymd.app import MDApp
from kivymd.uix.widget import MDWidget

# Local imports
from core.config_manager import ConfigManager
from ui.dialogs import ErrorDialog
```

#### Error Handling
```python
# Good: Specific exception handling with logging
try:
    with open(file_path, 'r') as f:
        content = f.read()
except FileNotFoundError:
    Logger.error(f"File not found: {file_path}")
    return False
except PermissionError:
    Logger.error(f"Permission denied: {file_path}")
    return False
```

### KivyMD Guidelines
- Use appropriate Material Design components
- Implement proper theme support
- Follow responsive design principles
- Ensure accessibility compliance

## 🧪 Testing

### Showcase Testing
Use showcase applications to test your changes:

```bash
# Test specific components
python showcases/showcase_editor.py      # Editor functionality
python showcases/showcase_console.py     # Console features
python showcases/showcase_themes.py      # Theme system
python showcases/showcase_settings_screen.py  # Settings
```

### Creating New Showcases
When adding new features, create corresponding showcase applications:

```python
# showcases/showcase_new_feature.py
from kivymd.app import MDApp
from ui.new_feature import NewFeature

class NewFeatureShowcase(MDApp):
    def build(self):
        return NewFeature()

if __name__ == "__main__":
    NewFeatureShowcase().run()
```

### Manual Testing Checklist
- [ ] Feature works in both dark and light themes
- [ ] Configuration changes persist correctly
- [ ] No console errors or warnings
- [ ] Responsive design on different screen sizes
- [ ] Proper keyboard navigation support

## 📤 Submitting Changes

### Pull Request Process
1. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-new-feature
   ```

2. **Make your changes**
   - Follow coding standards
   - Add tests (showcase applications)
   - Update documentation

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing new feature
   
   - Implement feature X with Y functionality
   - Add showcase application for testing
   - Update configuration system to support Z"
   ```

4. **Push and create PR**
   ```bash
   git push origin feature/amazing-new-feature
   ```

### Commit Message Guidelines
Use conventional commit format:

```
type(scope): description

Extended description if needed

- Bullet point 1
- Bullet point 2
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tested with relevant showcase applications
- [ ] Manual testing completed
- [ ] No new console errors

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Showcase application created/updated
```

## 💡 Feature Requests

### Before Requesting
1. Check existing issues and PRs
2. Consider if it fits the project's scope
3. Think about implementation complexity

### Creating Feature Requests
Use this template:

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Implementation
How should this be implemented?

## Alternatives Considered
What other approaches were considered?

## Additional Context
Any other relevant information
```

## 🐛 Bug Reports

### Creating Bug Reports
Include:
- **Environment**: OS, Python version, KivyMD version
- **Steps to reproduce**: Clear, step-by-step instructions
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Screenshots**: If applicable
- **Error logs**: Console output and error messages

### Bug Report Template
```markdown
## Bug Description
Brief description of the bug

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.9.2]
- KivyMD: [e.g., 1.1.1]

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Screenshots
If applicable

## Error Logs
Console output and error messages

## Additional Context
Any other relevant information
```

## 🔧 Development Tips

### Debugging
- Use Kivy Logger for consistent logging
- Test with showcase applications first
- Use KivyMD's debug tools
- Check console for warnings and errors

### Performance Considerations
- Minimize widget creation in loops
- Use proper event binding/unbinding
- Implement lazy loading for large datasets
- Profile performance-critical sections

### Configuration Integration
Always use ConfigManager for settings:

```python
from core.config_manager import ConfigManager

class MyComponent:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.font_size = config_manager.get_setting('editor', 'font_size', 16)
```

## 🎯 Areas for Contribution

We welcome contributions in these areas:

### High Priority
- Bug fixes and stability improvements
- Performance optimizations
- Accessibility enhancements
- Documentation improvements

### Medium Priority
- New language profile additions
- Theme enhancements
- UI/UX improvements
- Plugin system development

### Low Priority
- Advanced features
- Experimental functionality
- Platform-specific optimizations

## 💬 Getting Help

- **Issues**: Open a GitHub issue for questions
- **Discussions**: Use GitHub Discussions for general questions
- **Documentation**: Check the README and code comments

Thank you for contributing to KT IDE! 🚀