# showcases/showcase_history_manager.py

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from ui.utilities.history_manager import HistoryManager


from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty
from kivy.logger import Logger

Window.softinput_mode = 'below_target'

class ShowcaseHistoryManager(App):
    status_text = StringProperty("Ready")
    pointer_text = StringProperty("")
    state_count = NumericProperty(0)
    history = None


    def build(self):
        # Instantiate HistoryManager from the new module and INJECT the Kivy Clock instance
        self.history = HistoryManager(app_clock=Clock)

        self.current_text = ""

        layout = BoxLayout(orientation='vertical', spacing=5, padding=5)

        # Toolbar
        toolbar = BoxLayout(size_hint=(1, None), height=50, spacing=5)
        self.undo_btn = Button(text="Undo", disabled=True)
        self.undo_btn.bind(on_press=self.do_undo)
        self.redo_btn = Button(text="Redo", disabled=True)
        self.redo_btn.bind(on_press=self.do_redo)
        toolbar.add_widget(self.undo_btn)
        toolbar.add_widget(self.redo_btn)
        layout.add_widget(toolbar)

        # Status bar
        status_layout = BoxLayout(size_hint=(1, None), height=30)
        self.status_label = Label(text=self.status_text)
        self.state_label = Label(text=f"States: {self.state_count}")
        status_layout.add_widget(self.status_label)
        status_layout.add_widget(self.state_label)
        layout.add_widget(status_layout)

        # History pointer
        self.pointer_label = Label(
            text=self.pointer_text,
            size_hint=(1, None),
            height=20,
            font_size='14sp'
        )
        layout.add_widget(self.pointer_label)

        # Text editor
        self.editor = TextInput(
            size_hint=(1, 1),
            font_size='16sp'
        )
        self.editor.bind(text=self.on_text_change)
        layout.add_widget(self.editor)

        # Schedule initial state capture
        Clock.schedule_once(lambda dt: self._capture_initial_state(), 0.1)

        # Schedule UI updates
        Clock.schedule_interval(self.update_ui, 0.1)

        return layout

    def _capture_initial_state(self):
        """Capture the initial state of the editor."""
        self.history.add_state(self.editor.text)
        self.current_text = self.editor.text
        self.status_text = "Initial state capture scheduled."

    def on_text_change(self, instance, text):
        """Handles text changes in the editor."""
        if text != self.current_text:
            self.current_text = text
            self.history.add_state(text)

    def do_undo(self, *args):
        """Trigger undo action."""
        Logger.info("ShowcaseHistoryManager: Undo button pressed.")
        text = self.history.undo()
        if text is not None:
            self._set_text(text)
            self.status_text = f"Undid to state {self.history.current_index + 1}"
            Logger.info(f"ShowcaseHistoryManager: Undid to state index {self.history.current_index}.")
        else:
            self.status_text = "Cannot Undo"
            Logger.info("ShowcaseHistoryManager: Undo not possible.")

    def do_redo(self, *args):
        """Trigger redo action."""
        Logger.info("ShowcaseHistoryManager: Redo button pressed.")
        text = self.history.redo()
        if text is not None:
            self._set_text(text)
            self.status_text = f"Redid to state {self.history.current_index + 1}"
            Logger.info(f"ShowcaseHistoryManager: Redid to state index {self.history.current_index}.")
        else:
             self.status_text = "Cannot Redo"
             Logger.info("ShowcaseHistoryManager: Redo not possible.")

    def _set_text(self, text):
        """Set editor text programmatically without triggering on_text_change."""
        Logger.info("ShowcaseHistoryManager: Setting text programmatically.")
        self.editor.unbind(text=self.on_text_change)
        self.editor.text = text
        self.current_text = text
        self.editor.bind(text=self.on_text_change)
        Logger.info("ShowcaseHistoryManager: Programmatic text set and handler re-bound.")

    def update_ui(self, dt):
        """Update UI elements periodically based on history state."""
        self.state_count = len(self.history.states)
        self.state_label.text = f"States: {self.state_count}"

        self.pointer_text = self.history.get_pointer()
        self.pointer_label.text = self.pointer_text

        self.undo_btn.disabled = self.history.current_index <= 0
        self.redo_btn.disabled = self.history.current_index >= len(self.history.states) - 1

        if self.history.pending_text is None and self.status_text not in ["Cannot Undo", "Cannot Redo", "Initial state capture scheduled."]:
             if len(self.history.states) > 0:
                 self.status_text = f"Ready. State {self.history.current_index + 1} of {len(self.history.states)}."
             else:
                 self.status_text = "Ready. No states."
        elif self.history.pending_text is not None:
             self.status_text = "Editing..."

    def on_stop(self):
        """Clean up when app stops."""
        Logger.info("ShowcaseHistoryManager: App stopping, calling history cleanup.")
        if self.history:
            self.history.cleanup()


if __name__ == '__main__':
    Logger.info("ShowcaseHistoryManager: Running the prototype app.")
    ShowcaseHistoryManager().run()
