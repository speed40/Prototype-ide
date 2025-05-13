# showcases/showcase_editor.py - Simple App using Self-Sizing CodeEditor

import os
import sys
# Ensure the parent directory is in the Python path to import ui and ui.utilities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Removed App import, using MDApp
# from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
# Removed Clock import if not used elsewhere
# from kivy.clock import Clock
# Removed other imports not used in this simplified version
# from kivy.properties import StringProperty, NumericProperty, ObjectProperty
# from kivy.logger import Logger

# Import KivyMD components
from kivymd.app import MDApp
# Removed other KivyMD imports
# from kivymd.uix.boxlayout import MDBoxLayout
# from kivymd.uix.button import MDRaisedButton
# from kivymd.uix.label import MDLabel
# from kivymd.uix.floatlayout import MDFloatLayout

# Assuming ui/editor.py is in a 'ui' directory relative to this file
from ui.editor import CodeEditor


# Set soft input mode to 'pan' or 'below_target' - 'below_target' might work better with this approach
Window.softinput_mode = 'below_target' # Use 'below_target' as suggested by user's proposed code

class EditorApp(MDApp): # Changed from App to MDApp
    def build(self):
        # No complex layout needed here, the CodeEditor handles its own sizing and keyboard
        # The CodeEditor will take the full window space
        return CodeEditor(
            show_report=True,  # Toggle to False to hide report bar
            report_height=dp(60)  # Adjust report bar height as needed
        )

# Run the application if this script is executed directly
if __name__ == '__main__':
    EditorApp().run()