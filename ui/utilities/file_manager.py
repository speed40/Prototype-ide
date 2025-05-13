import os
from threading import Thread
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.metrics import dp
from kivymd.uix.button import MDRaisedButton
from kivymd.theming import ThemableBehavior

from ..dialogs import ErrorDialog

DOCUMENTS_PATH = "/storage/emulated/0/Documents"
INCLUDE_FILTER = ["*.txt", "*.json", "*.csv", "*.md"]

class ThemeAwarePopup(ThemableBehavior, Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._bind_theme, 0)

    def _bind_theme(self, dt):
        self.theme_cls.bind(theme_style=self._on_theme_change)
        self._apply_theme()

    def _on_theme_change(self, *args):
        self._apply_theme()

    def _apply_theme(self):
        if self.content:
            for widget in self.content.walk():
                if isinstance(widget, MDRaisedButton):
                    widget.md_bg_color = self.theme_cls.primary_color

class FileManager(ThemableBehavior):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._running_app = App.get_running_app()

    def write_file(self, content, file_path=None, callback=None, prompt=True):
        if prompt and file_path is None:
            self._show_file_saver(content, callback)
        else:
            Thread(target=self._write_threaded, args=(content, file_path, callback), daemon=True).start()

    def read_file(self, file_path=None, callback=None, prompt=True):
        if prompt and file_path is None:
            self._show_file_loader(callback)
        else:
            Thread(target=self._read_threaded, args=(file_path, callback), daemon=True).start()

    def _write_threaded(self, content, file_path, callback):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self._run_callback(callback, True, file_path)
        except Exception as e:
            self._show_error("Save Error", str(e), callback)

    def _read_threaded(self, file_path, callback):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self._run_callback(callback, True, content)
        except Exception as e:
            self._show_error("Load Error", str(e), callback)

    def _show_file_saver(self, content, callback):
        box = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))

        chooser = FileChooserListView(path=DOCUMENTS_PATH, filters=INCLUDE_FILTER)

        filename_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        filename_box.add_widget(Label(text="Filename:", size_hint_x=None, width=dp(80)))
        
        filename_input = TextInput(
            text="untitled.txt",
            hint_text="Enter filename",
            size_hint_x=1,
            multiline=False,
            padding=[10, 10]
        )
        filename_box.add_widget(filename_input)

        btn_box = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(15))
        popup = ThemeAwarePopup(title='Save File', content=None, size_hint=(0.95, 0.95))

        btn_box.add_widget(MDRaisedButton(text='CANCEL', on_release=lambda x: popup.dismiss()))
        btn_box.add_widget(MDRaisedButton(
            text='SAVE',
            on_release=lambda x: self._save_file(chooser, filename_input, content, callback, popup),
        ))

        box.add_widget(chooser)
        box.add_widget(filename_box)
        box.add_widget(btn_box)
        popup.content = box
        popup.open()

    def _save_file(self, chooser, filename_input, content, callback, popup):
        filename = filename_input.text.strip()
        if not filename:
            ErrorDialog(title="Error", text="Filename cannot be empty").open()
            return

        file_path = os.path.join(chooser.path, filename)
        popup.dismiss()
        self.write_file(content, file_path, callback, prompt=False)

    def _show_file_loader(self, callback):
        box = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))

        chooser = FileChooserListView(path=DOCUMENTS_PATH, filters=INCLUDE_FILTER)

        btn_box = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(15))
        popup = ThemeAwarePopup(title='Load File', content=None, size_hint=(0.95, 0.95))

        btn_box.add_widget(MDRaisedButton(text='CANCEL', on_release=lambda x: popup.dismiss()))
        btn_box.add_widget(MDRaisedButton(text='LOAD', on_release=lambda x: self._load_file(chooser, callback, popup)))

        box.add_widget(chooser)
        box.add_widget(btn_box)
        popup.content = box
        popup.open()

    def _load_file(self, chooser, callback, popup):
        if chooser.selection:
            file_path = chooser.selection[0]
            popup.dismiss()
            self.read_file(file_path, callback, prompt=False)

    def _show_error(self, title, message, callback):
        Clock.schedule_once(lambda dt: (
            ErrorDialog(title=title, text=message).open(),
            callback and callback(False, None)
        ))

    def _run_callback(self, callback, *args):
        if callback:
            Clock.schedule_once(lambda dt: callback(*args))

    def write_file_mainthread(self, content, file_path):
        result = [None]
        self._write_threaded(content, file_path, lambda s, p: result.__setitem__(0, s))
        return result[0]

    def read_file_mainthread(self, file_path):
        result = [None]
        self._read_threaded(file_path, lambda s, c: result.__setitem__(0, c if s else None))
        return result[0]