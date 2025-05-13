# editor.py
# Reverting keyboard detection to use Window.bind('on_keyboard')
# and a method similar to the user's initial proposal.
# Includes dynamic height, line numbers, history, auto-pairing, and an optional report bar.

import os
import sys
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import (StringProperty, NumericProperty,
                           BooleanProperty, ObjectProperty, ReferenceListProperty)
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.logger import Logger
from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.theming import ThemableBehavior
from kivymd.uix.boxlayout import MDBoxLayout

from ui.utilities.history_manager import HistoryManager
from ui.utilities.line_number import LineNumber

from kivy.clock import Clock
from kivy.utils import platform

# Import platform-specific keyboard handling if needed
if platform == 'android':
    try:
        from jnius import autoclass
        # Need cast for newer Android versions
        from cast import cast # Assuming 'cast' is available or you have your own cast utility
        Activity = autoclass('org.kivy.android.PythonActivity')
        Rect = autoclass('android.graphics.Rect')
        # Try casting to Activity explicitly if needed
        activity = cast('android.app.Activity', Activity.mActivity)
        Logger.info("CodeEditor: Loaded Android JNI keyboard classes.")
        android_kb_detection_available = True
    except Exception as e:
        Logger.error(f"CodeEditor: Failed to load Android JNI keyboard classes: {e}")
        android_kb_detection_available = False
else:
    android_kb_detection_available = False


class CodeInput(TextInput, ThemableBehavior):
    # ... (CodeInput class remains largely the same as the previous version)
    """
    The core text input widget for the code editor.
    Its height is managed externally by the parent CodeEditor based on available space.
    Adds auto-pairing and smart deletion for common characters.
    Dynamically calculates line_height based on font metrics.
    Relies on parent layout (ScrollView) for scrolling, which might be impacted by height management.
    """
    line_limit = NumericProperty(15)
    line_height = NumericProperty(0)

    AUTO_PAIRS = {
        '(': ')', '[': ']', '{': '}',
        '\"': '\"', "'": "'", '`': '`', '<': '>'
    }
    AUTO_CLOSE_CHARS = {')', ']', '}', '\"', "'", '`', '>'}

    parent_code_editor = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._update_line_height, 0)
        self.bind(font_name=self._update_line_height, font_size=self._update_line_height)
        self.bind(text=self.on_text_change)
        self.bind(cursor=self._update_last_cursor)

    def _update_last_cursor(self, instance, cursor_pos):
        self._last_cursor_col = cursor_pos[0]
        self._last_cursor_row = cursor_pos[1]

    def _update_line_height(self, *args):
        if not self.font_name or self.font_size <= 0:
            self.line_height = sp(20)
            Logger.warning("CodeInput: Font name or size not set, using default line_height.")
            return
        try:
            temp_label = CoreLabel(font_name=self.font_name, font_size=self.font_size, text="Line1\nLine2", lines_spacing=self.line_spacing)
            temp_label.refresh()
            if temp_label.texture_size[1] > 0 and temp_label.text.count('\n') >= 1:
                 estimated_line_height = (temp_label.texture_size[1] - self.line_spacing) / 2
                 if estimated_line_height <= 0:
                      estimated_line_height = self.font_size * 1.5
                 self.line_height = estimated_line_height
            else:
                 temp_label_single = CoreLabel(font_name=self.font_name, font_size=self.font_size, text="A")
                 temp_label_single.refresh()
                 if temp_label_single.texture_size[1] > 0:
                      self.line_height = temp_label_single.texture_size[1] + self.line_spacing
                 else:
                     self.line_height = self.font_size * 1.5 + self.line_spacing
        except Exception as e:
            Logger.error(f"CodeInput: Error calculating dynamic line_height: {e}. Using heuristic + spacing.")
            self.line_height = self.font_size * 1.5 + self.line_spacing

        if self.parent_code_editor and hasattr(self.parent_code_editor, 'update_available_space'):
             Clock.schedule_once(lambda dt: self.parent_code_editor.update_available_space(), 0)

    def on_text_change(self, instance, value):
        if self.parent_code_editor and self.parent_code_editor.history_manager:
            self.parent_code_editor.history_manager.commit_state_debounced(value)
        if self.parent_code_editor and self.parent_code_editor.line_number_gutter:
            self.parent_code_editor.line_number_gutter._update_preferred_width()
        if self.parent_code_editor and hasattr(self.parent_code_editor, 'update_available_space'):
             Clock.schedule_once(lambda dt: self.parent_code_editor.update_available_space(), 0)

    def on_paste(self, text, *largs):
        super().on_paste(text, *largs)
        if self.parent_code_editor and hasattr(self.parent_code_editor, 'update_available_space'):
             Clock.schedule_once(lambda dt: self.parent_code_editor.update_available_space(), 0.1)

    def on_key_down(self, keyboard, keycode, text, modifiers):
        if text in self.AUTO_PAIRS:
            paired_char = self.AUTO_PAIRS[text]
            original_cursor_index = self.cursor_index
            super().insert_text(text + paired_char, from_undo=False)
            self.cursor = self.get_cursor_from_index(original_cursor_index + 1)
            return True
        if keycode[1] == 'backspace' and self._last_cursor_col > 0:
            current_text = self.text
            cursor_index = self.cursor_index
            if cursor_index < len(current_text) and cursor_index > 0:
                char_before = current_text[cursor_index - 1]
                char_after = current_text[cursor_index]
                for open_char, close_char in self.AUTO_PAIRS.items():
                    if char_before == open_char and char_after == close_char:
                        self.do_backspace()
                        self.do_backspace()
                        return True
        if text in self.AUTO_CLOSE_CHARS:
            if self.cursor_index < len(self.text) and self.text[self.cursor_index] == text:
                self.cursor = self.get_cursor_from_index(self.cursor_index + 1)
                return True
        return super().on_key_down(keyboard, keycode, text, modifiers)

    def keyboard_on_key_up(self, window, keycode):
        if self.parent_code_editor and self.parent_code_editor.history_manager:
            self.parent_code_editor.history_manager.commit_state_debounced(self.text)
        return super().keyboard_on_key_up(window, keycode)

    def on_focus(self, instance, value):
        Logger.info(f"CodeInput: Focus changed to {value}. Window softinput_mode is handled externally.")
        if self.parent_code_editor and hasattr(self.parent_code_editor, 'update_available_space'):
             # Schedule update_available_space with a slight delay after focus change
             # to allow keyboard to potentially appear and update Window.keyboard_height
             Clock.schedule_once(lambda dt: self.parent_code_editor.update_available_space(), 0.1)


class CodeEditor(MDBoxLayout):
    """
    The main code editor widget, calculating available height and setting
    its TextInput's height based on window and keyboard state.
    Includes line numbers, history, auto-pairing, and an optional report bar.
    Uses Window.bind('on_keyboard') for keyboard detection.
    """
    show_report = BooleanProperty(True)
    report_height = NumericProperty(dp(60))
    keyboard_height = NumericProperty(0) # Track keyboard height internally
    buffer_space = NumericProperty(dp(40)) # Buffer between keyboard and text input

    history_manager = ObjectProperty(None)
    line_number_gutter = ObjectProperty(None)
    code_input = ObjectProperty(None)
    editor_scroll = ObjectProperty(None)
    report_bar = ObjectProperty(None)

    def __init__(self, app_clock=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(0)
        self.padding = [dp(5), dp(5), dp(5), dp(0)]

        self.app_clock = app_clock if app_clock else Clock
        self.history_manager = HistoryManager(app_clock=self.app_clock)

        Clock.schedule_once(self._setup_ui, 0)

        # Bind to window size changes
        Window.bind(size=self._on_window_size)
        # Bind to the 'on_keyboard' event for keyboard presence and height
        # The handler needs to accept the arguments provided by 'on_keyboard'
        Window.bind(on_keyboard=self._on_keyboard)


        # Schedule initial space update
        Clock.schedule_once(self.update_available_space)


    def _setup_ui(self, dt):
        app = MDApp.get_running_app()
        if not app:
            Logger.error("CodeEditor: MDApp not running. UI setup deferred.")
            Clock.schedule_once(self._setup_ui, 0.1)
            return

        if self.show_report:
            self._create_report_bar(app.theme_cls)
            self.add_widget(self.report_bar)

        self.code_area_container = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            spacing=dp(5),
            padding=[0, 0, 0, 0]
        )

        self.line_number_gutter = LineNumber(
            size_hint_x=None,
            width=dp(50),
            size_hint_y=1
        )
        self.code_area_container.add_widget(self.line_number_gutter)

        self.code_input = CodeInput(
            multiline=True,
            font_name='JetBrainsMono-Regular',
            font_size=sp(18),
            background_color=app.theme_cls.bg_dark,
            foreground_color=app.theme_cls.text_color,
            cursor_color=app.theme_cls.primary_color,
            size_hint_x=1,
            size_hint_y=None,
            write_tab=False,
            tab_width=int(dp(20)),
            parent_code_editor=self
        )
        self.code_area_container.add_widget(self.code_input)

        self.line_number_gutter.text_input = self.code_input

        self.code_input.bind(height=self.code_area_container.setter('height'))
        self.code_input.bind(height=self.line_number_gutter.setter('height'))


        self.editor_scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=True,
            do_scroll_y=True,
            bar_width='10dp',
            bar_color=app.theme_cls.primary_color,
            bar_inactive_color=app.theme_cls.primary_light,
            scroll_type=['content'],
        )

        self.editor_scroll.add_widget(self.code_area_container)
        self.add_widget(self.editor_scroll)

        Logger.info("CodeEditor: UI setup complete.")
        Clock.schedule_once(self.update_available_space, 0.1)


    def _create_report_bar(self, theme_cls):
        self.report_bar = BoxLayout(
            size_hint_y=None,
            height=self.report_height,
            orientation='vertical',
            padding=[dp(5), dp(2)]
        )
        with self.report_bar.canvas.before:
            Color(*theme_cls.primary_color)
            self.bg_rect = Rectangle(pos=self.report_bar.pos, size=self.report_bar.size)
        self.report_bar.bind(pos=self._update_bg_rect, size=self._update_bg_rect)
        self.report_bar.add_widget(Label(text="", halign='left', color=(1, 1, 1, 1), bold=True, font_size=sp(12), text_size=(self.report_bar.width - dp(10), None)))
        self.report_bar.add_widget(Label(text="", halign='left', color=(1, 1, 1, 1), bold=True, font_size=sp(12), text_size=(self.report_bar.width - dp(10), None)))
        self.report_bar.bind(size=self._update_report_label_text_size)


    def _update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _update_report_label_text_size(self, instance, value):
         for label in self.report_bar.children:
              if isinstance(label, Label):
                   label.text_size = (self.report_bar.width - dp(10), None)

    # Re-implementing keyboard detection using Window.bind('on_keyboard')
    def _on_keyboard(self, window, key, scancode, codepoint, modifiers):
        """
        Handles the 'on_keyboard' event to detect keyboard presence and height.
        Uses platform-specific methods if necessary.
        """
        Logger.info(f"CodeEditor: Window.on_keyboard event received. Key: {key}, Scancode: {scancode}, Codepoint: {codepoint}, Modifiers: {modifiers}")

        # Attempt to get keyboard height using the user's proposed logic
        kb_height = 0
        if platform == 'android' and android_kb_detection_available:
             try:
                 # Re-using the Android JNI logic from the user's proposed snippet
                 rect = Rect()
                 view = activity.getWindow().getDecorView()
                 view.getWindowVisibleDisplayFrame(rect)
                 # Calculate keyboard height as the difference between Window height and visible frame bottom
                 kb_height_px = Window.height - rect.bottom
                 kb_height = dp(kb_height_px) # Convert pixels to dp
                 Logger.info(f"CodeEditor: Android JNI keyboard height detected: {kb_height_px}px ({kb_height}dp)")
             except Exception as e:
                 Logger.error(f"CodeEditor: Error in Android JNI keyboard height detection: {e}")
                 # Fallback to Kivy's keyboard_height if JNI fails
                 kb_height = Window.keyboard_height
                 Logger.warning(f"CodeEditor: Falling back to Window.keyboard_height: {kb_height}dp")
        else:
            # For other platforms or if Android JNI is not available, use Kivy's property
            kb_height = Window.keyboard_height
            Logger.info(f"CodeEditor: Using Window.keyboard_height: {kb_height}dp")


        # Update the internal keyboard_height property
        self.keyboard_height = kb_height

        # Schedule an update for available space
        Clock.schedule_once(self.update_available_space, 0)

        # Return False to allow other widgets (like TextInput) to also receive keyboard events
        return False


    def _on_window_size(self, instance, size):
        """Handles window size changes and updates available space."""
        Logger.info(f"CodeEditor: Window size changed to {size}. Updating available space.")
        self.update_available_space()


    def calculate_available_height(self):
        """Calculates the available height for the TextInput based on window and keyboard."""
        win_h = Window.height
        report_h = self.report_height if self.show_report else 0
        # Adjust buffer space calculation based on keyboard presence and size
        # Use a threshold slightly higher than 0 to avoid buffer when keyboard is not truly "open"
        buffer = self.buffer_space if self.keyboard_height > dp(10) else 0

        # Subtract report bar height, keyboard height, and buffer from window height
        available_h = max(dp(100), win_h - report_h - self.keyboard_height - buffer) # Minimum height

        # Also account for padding within the CodeEditor itself
        available_h -= (self.padding[1] + self.padding[3])

        Logger.info(f"CodeEditor: Available height calculation: Window H={win_h}, Report H={report_h}, Keyboard H={self.keyboard_height}, Buffer={buffer}, Calculated Available H={available_h}")

        return available_h


    def update_available_space(self, *args):
        """Updates the height of the TextInput based on available space."""
        if not self.code_input or not self.editor_scroll:
            Logger.warning("CodeEditor: CodeInput or ScrollView not initialized yet, cannot update space.")
            return

        available_h = self.calculate_available_height()

        # Set the height of the ScrollView and its child (TextInput) to the calculated available height.
        # This is the core of the user's proposed approach for self-sizing.
        self.code_input.height = available_h
        self.editor_scroll.height = available_h

        Logger.info(f"CodeEditor: Setting CodeInput height to {self.code_input.height}. ScrollView height set to {self.editor_scroll.height}")

        # Update report if enabled
        if self.show_report:
            self._update_report()

        # Trigger a line number update after space is adjusted
        if self.line_number_gutter:
            self.line_number_gutter._trigger_line_number_update()


    def _update_report(self):
        """Updates the text in the status report bar."""
        if not self.report_bar or not self.code_input:
            return

        win_w, win_h = Window.size
        kb_h = self.keyboard_height # Use the internally tracked keyboard height
        buffer_val = self.buffer_space if kb_h > dp(10) else 0
        report_h_val = self.report_height if self.show_report else 0
        available_h = self.code_input.height

        if len(self.report_bar.children) >= 2:
            line2_label = self.report_bar.children[0]
            line1_label = self.report_bar.children[1]

            line1_label.text = (
                f"Window: {int(win_w)}x{int(win_h)}dp | "
                f"Editor Space: {int(available_h)}dp"
            )

            line2_label.text = (
                f"Keyboard: {'OPEN' if kb_h > dp(10) else 'CLOSED'} "
                f"({int(kb_h)}dp) | "
                f"Buffer: {int(buffer_val)}dp | "
                f"Report H: {int(report_h_val)}dp"
            )


    def undo(self):
        if self.history_manager and self.code_input:
            state = self.history_manager.undo()
            if state is not None:
                self.code_input.text = state
                self.code_input.cursor = self.code_input.get_cursor_from_index(len(state))

    def redo(self):
        if self.history_manager and self.code_input:
            state = self.history_manager.redo()
            if state is not None:
                self.code_input.text = state
                self.code_input.cursor = self.code_input.get_cursor_from_index(len(state))