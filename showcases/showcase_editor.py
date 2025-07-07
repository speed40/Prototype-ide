# showcases/showcase_editor.py - Simple App using Self-Sizing CodeEditor

import os
import sys

# Ensure the parent directory is in the Python path to import ui and ui.utilities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from kivy.core.window import Window
from kivy.metrics import dp
# Import KivyMD components
from kivymd.app import MDApp
from ui.editor import CodeEditor

Window.softinput_mode = 'below_target'

class EditorApp(MDApp):
    def build(self):
        # No complex layout needed here, the CodeEditor handles its own sizing and keyboard
        # The CodeEditor will take the full window space
        return CodeEditor(
            show_report=True,  # Toggle to False to hide report bar
            report_height=dp(60)  # Adjust report bar height as needed
        )
        
if __name__ == '__main__':
    EditorApp().run()
