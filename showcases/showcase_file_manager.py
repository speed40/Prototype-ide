# showcases/showcase_file_menu.py 

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.snackbar import Snackbar
from kivymd.toast import toast

from ui.utilities.file_manager import FileManager

Window.softinput_mode = "below_target"

KV = '''
<DemoScreen>:
    orientation: 'vertical'
    spacing: '10dp'

    MDTopAppBar:
        id: toolbar
        title: "File Manager Demo"
        elevation: 10
        left_action_items: [["theme-light-dark", lambda x: app.toggle_theme()]]
        right_action_items: [["information", lambda x: app.show_info()]]

    ScrollView:
        MDBoxLayout:
            orientation: 'vertical'
            spacing: '15dp'
            padding: '20dp'
            size_hint_y: None
            height: self.minimum_height

            MDRaisedButton:
                text: "Save Content"
                on_press: app.save_content()
                size_hint_y: None
                height: dp(50)

            MDRaisedButton:
                text: "Load File"
                on_press: app.load_file()
                size_hint_y: None
                height: dp(50)

            MDLabel:
                id: content_label
                text: "File content will appear here"
                size_hint_y: None
                height: self.texture_size[1]
                padding: ['10dp', '10dp']
                halign: 'center'
                theme_text_color: "Primary"
'''

Builder.load_string(KV)

class DemoScreen(MDBoxLayout):
    pass

class FileManagerDemo(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "DeepPurple"
        self.file_manager = FileManager()
        return DemoScreen()
    
    def toggle_theme(self):
        self.theme_cls.theme_style = "Dark" if self.theme_cls.theme_style == "Light" else "Light"
        mode = self.theme_cls.theme_style
        self.root.ids.content_label.text = f"Theme changed to: {mode}"
        # Use toast instead of Snackbar to avoid the initialization error
        toast(f"Theme: {mode}")
    
    def show_info(self):
        content = (
            "File Manager Demo\n\n"
            "• Save/Load files with theme support\n"
            "• Dark/Light mode toggle\n"
            "• Adaptive popup components"
        )
        from ui.dialogs import InfoDialog
        InfoDialog(title="About", text=content).open()
    
    def save_content(self):
        content = (
            "Custom file content\n" + "-"*40 +
            "\nSaved by FileManager demo\n\nℹ️ Modern file manager FTW"
        )

        def callback(success, path):
            self.root.ids.content_label.text = (
                f"File saved to:\n{path}\n\n{content}" if success
                else "Save operation failed"
            )

        self.file_manager.write_file(content, callback=callback)
    
    def load_file(self):
        def callback(success, content):
            self.root.ids.content_label.text = (
                content if success else "Failed to load file"
            )

        self.file_manager.read_file(callback=callback)

if __name__ == "__main__":
    FileManagerDemo().run()