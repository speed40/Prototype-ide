# line_number.py
# This file has been updated to use manual calculation for line number positioning
# based on TextInput properties, drawing top-to-bottom, and fixing the crash.

from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.properties import (StringProperty, NumericProperty,
                           BooleanProperty, ObjectProperty, ReferenceListProperty)
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.logger import Logger

# Import ThemableBehavior from kivymd.theming
from kivymd.theming import ThemableBehavior
from kivymd.app import MDApp

# Import tuple for type checking (not strictly needed for _lines_labels but kept for safety)
from builtins import tuple


class LineNumber(Widget, ThemableBehavior):
    """
    A widget that displays line numbers alongside a KivyMD TextInput.
    It dynamically adjusts its width and updates line numbers based on the TextInput's content and scroll.
    Uses manual calculation for line number positioning, drawing from top to bottom.
    Displays visual line numbers (1 to visual_lines_count).
    """
    text_input = ObjectProperty(None)
    line_spacing = NumericProperty(sp(2)) # Not directly used in this manual drawing method
    preferred_width = NumericProperty(dp(40)) # Initial guess, updated based on logical line count

    # Internal properties to track TextInput's size and padding for accurate line number placement
    _text_input_height = NumericProperty(0) # Used to match height
    _text_input_padding = ReferenceListProperty(NumericProperty(0), NumericProperty(0), NumericProperty(0), NumericProperty(0)) # Used for vertical alignment

    _line_number_labels = [] # List to keep track of Label widgets

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__text_input = None
        # Use TextInput's font size for consistency, set during binding
        self.line_number_font_size = sp(16) # Default, will be updated

        # Bind to the 'text_input' property of this LineNumber widget
        self.bind(text_input=self._on_text_input_changed)

        # If text_input is already set during initialization (e.g., in KV or direct instantiation)
        if self.text_input:
            self._on_text_input_changed(self, self.text_input)

        # Bind to theme changes to update line number colors
        app = MDApp.get_running_app()
        if app and hasattr(app, 'theme_cls'):
            app.theme_cls.bind(
                theme_style=self._trigger_line_number_update,
                primary_palette=self._trigger_line_number_update
            )
        Logger.info("LineNumber: Initialized.")

    def _on_text_input_changed(self, instance, value):
        """
        Handles changes to the text_input property, binding/unbinding events
        to keep line numbers in sync with the TextInput.
        """
        # Unbind from old TextInput if it exists to prevent memory leaks
        if self.__text_input:
            self.__text_input.unbind(
                text=self._trigger_line_number_update,
                size=self._trigger_line_number_update,
                # Height and padding are now bound in CodeEditor's _setup_ui
                font_size=self._update_preferred_width, # Font size affects line count/width
                scroll_y=self._on_text_input_scroll # Unbind existing scroll_y
            )
            Logger.info("LineNumber: Unbound from old TextInput.")

        # Assign the new TextInput instance
        self.__text_input = value

        # Bind to new TextInput properties for continuous updates
        if self.__text_input:
            self.__text_input.bind(
                text=self._trigger_line_number_update,
                size=self._trigger_line_number_update,
                # Bind height and padding in CodeEditor for simpler hierarchy management
                font_size=self._update_preferred_width, # Font size affects line count/width
                scroll_y=self._on_text_input_scroll # Bind scroll_y here
            )
            Logger.info("LineNumber: Bound to new TextInput.")

            # Initial updates based on TextInput's current state
            # Get initial height and padding from TextInput (they are bound in CodeEditor)
            self._text_input_height = self.__text_input.height
            self._text_input_padding = self.__text_input.padding
            self.line_number_font_size = self.__text_input.font_size

            self._update_preferred_width()
            self._trigger_line_number_update() # Trigger initial drawing

    def _on_text_input_scroll(self, instance, value):
        """
        Handles scroll events from the TextInput to update line number positions.
        """
        # Logger.info(f"LineNumber: TextInput scrolled to {value}. Triggering update.") # Keep logging minimal
        self._trigger_line_number_update() # Trigger redraw on scroll

    def _update_preferred_width(self, *args):
        """
        Calculates and updates the preferred width of the line number widget
        based on the number of LOGICAL lines in the TextInput and its font size.
        This ensures enough space for the largest line number.
        """
        if not self.__text_input:
            Logger.warning("LineNumber: _update_preferred_width called without text_input.")
            return

        # Use logical lines count to determine required width for numbers
        logical_lines = self.__text_input.text.splitlines()
        num_logical_lines = len(logical_lines)

        # Account for the last line if it doesn't end with a newline
        if self.__text_input.text != '' and not self.__text_input.text.endswith('\n'):
            num_logical_lines += 1
        # Handle a completely empty TextInput
        elif self.__text_input.text == '':
             num_logical_lines = 1 # Always show line 1


        num_digits = len(str(num_logical_lines))
        # Optional: ensure width for future lines, e.g., up to 999 lines need 3 digits
        # num_digits = max(3, num_digits)

        # Estimate character width based on TextInput's font size (adjust if needed for monospaced font)
        # Assumes TextInput.font_size is set and reasonable.
        char_width_estimate = self.__text_input.font_size * 0.65 if self.__text_input and self.__text_input.font_size else sp(16) * 0.65 # Use a default if font_size is zero/None

        padding_right = dp(10) # Padding on the right of the numbers
        padding_left = dp(5)  # Padding on the left of the numbers

        # Calculate required width: digits * char_width + total padding
        calculated_width = (num_digits * char_width_estimate) + padding_left + padding_right
        self.preferred_width = max(dp(30), calculated_width) # Ensure minimum sensible width
        self.width = self.preferred_width # Set the width of the LineNumber widget

        # Logger.info(f"LineNumber: Preferred width calculated: {self.preferred_width}. (Digits: {num_digits}, Logical Lines: {num_logical_lines})") # Keep logging minimal
        self._trigger_line_number_update() # Trigger redraw as width changed


    def _trigger_line_number_update(self, *args):
        """
        Schedules an update to the line numbers on the next frame.
        This prevents excessive updates during rapid changes to TextInput (e.g., typing).
        """
        Clock.unschedule(self._update_line_numbers)
        Clock.schedule_once(self._update_line_numbers, 0)
        # Logger.info("LineNumber: Scheduled line number update.") # Keep logging minimal for loop detection


    # --- CodeFu Enhancement: Corrected Line Number Positioning (Top to Bottom) ---
    def _update_line_numbers(self, *_):
        """
        Main function to update and redraw the line numbers using manual positioning.
        This method is called when TextInput properties change.
        Positions line numbers from top to bottom, aligned with visual lines.
        Displays visual line numbers (1 to visual_lines_count).
        """
        if not self.__text_input:
            Logger.warning("LineNumber: _update_line_numbers called without text_input.")
            return

        # Clear all existing line number labels
        for label_widget in self._line_number_labels:
            self.remove_widget(label_widget)
        self._line_number_labels.clear()
        # Logger.info("LineNumber: Cleared old line number labels.") # Keep logging minimal

        # Clear old graphics and redraw the separator line
        self.canvas.clear()
        with self.canvas:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'theme_cls'):
                theme_cls = app.theme_cls
                is_dark = theme_cls.theme_style == "Dark"
                line_number_color = theme_cls.text_color[:3] + [0.6] if is_dark else theme_cls.primary_color[:3] + [0.8]
                Color(*line_number_color)
            else:
                Color(0.5, 0.5, 0.5, 1.0) # Default color if theme is not available
                Logger.warning("LineNumber: MDApp or theme_cls not found. Using default line number color.")

            # Draw the vertical separator line to the right of the numbers
            Line(points=[self.x + self.preferred_width - dp(0.8), self.y, # Adjusted x slightly for the line
                         self.x + self.preferred_width - dp(0.8), self.top], # Adjusted x slightly for the line
                 width=dp(0.8))

        # Ensure LineNumber widget's position and height match TextInput's for proper alignment
        # These are bound in CodeEditor's _setup_ui, but we set internal properties here
        # to ensure we have the correct values for calculations.
        self._text_input_height = self.__text_input.height
        self._text_input_padding = self.__text_input.padding
        self.height = self._text_input_height # Ensure LineNumber height matches TextInput

        # Get the visual lines from TextInput's internal structure (_lines is a list of strings)
        visual_lines_count = len(self.__text_input._lines)

        # Handle empty text: always show line 1
        if visual_lines_count == 0 and self.__text_input.text.strip() == '':
            Logger.info("LineNumber: TextInput is empty, drawing line '1'.")
            # Position '1' aligned with the bottom padding when empty
            # Use the height of the first visual line position from the top for alignment
            drawing_y_empty = self.height - self.__text_input.padding[1] - self.__text_input.line_height
            if self.__text_input.line_height <= 0:
                # Fallback if line_height is not set yet
                 drawing_y_empty = self.height - self.__text_input.padding[1] - sp(20)

            self.__draw_line_number(1, drawing_y_empty)
            return # Exit if empty, only draw line 1

        # Handle case with text but no visual lines yet (rare)
        if visual_lines_count == 0 and self.__text_input.text.strip() != '':
             visual_lines_count = 1 # Assume at least one visual line if text exists

        # Iterate through the VISUAL lines for positioning and display (1 to visual_lines_count)
        for i in range(visual_lines_count):
            visual_line_num = i + 1 # Human-readable visual line number (1-based)

            # Calculate the y position for the bottom of the label, from the TOP of the TextInput's visible area.
            # This y_pos is relative to the BOTTOM of the LineNumber widget.
            # Start from the top of the TextInput's visible area (relative to LineNumber's bottom, self.y): self.height - self.__text_input.padding[1]
            # Subtract the distance from the top of the visible area to the bottom of the i-th visual line: (i + 1) * self.__text_input.line_height
            # This positions the bottom of the label correctly from top to bottom, aligned with visual lines.
            drawing_y = self.height - self.__text_input.padding[1] - (i + 1) * self.__text_input.line_height


            # Ensure line_height is not zero before drawing
            if self.__text_input.line_height > 0:
                 # Use the visual line number for display
                 self.__draw_line_number(visual_line_num, drawing_y) # Draw visual line number at visual line position
            else:
                Logger.warning(f"LineNumber: Skipping draw for visual line {i+1} due to zero line height.")

    # Removed the incomplete _get_logical_line_numbers_for_visual_lines method entirely for now.
    # We can revisit accurate logical line numbering display with wrapping as a separate feature.

    # --- End CodeFu Enhancement ---

    def __draw_line_number(self, line_num, y_pos):
        """
        Creates and adds a Label widget for a single line number.
        Positioning and sizing are calculated to align with the TextInput's lines.
        `y_pos` is the calculated y-coordinate for the bottom of the line number label, relative to LineNumber's self.y.
        """
        # Use TextInput's line_height for line number label height for consistent spacing
        actual_line_height = self.__text_input.line_height if self.__text_input and self.__text_input.line_height > 0 else sp(20)

        label_widget = Label(
            text=str(line_num),
            font_name='InriaSans-Regular', # Ensure this font is available and registered
            font_size=self.__text_input.font_size, # Use TextInput's font size for consistent visual scale
            halign='right', # Align text to the right within the label's bounds
            valign='middle', # Vertically center text within its bounds
            size_hint=(None, None), # Important for setting custom size/pos
        )

        # Set the color of the Label widget based on the current KivyMD theme
        app = MDApp.get_running_app()
        if app and hasattr(app, 'theme_cls'):
            theme_cls = app.theme_cls
            is_dark = theme_cls.theme_style == "Dark"
            # Use a slightly less opaque color for line numbers
            line_number_color_rgba = theme_cls.text_color[:3] + [0.6] if is_dark else theme_cls.primary_color[:3] + [0.8]
            label_widget.color = line_number_color_rgba
        else:
            label_widget.color = [0.5, 0.5, 0.5, 1.0] # Default color if theme is not available

        # Set Label widget's size to occupy the entire preferred_width of LineNumber and actual line height.
        label_widget.size = (self.preferred_width, actual_line_height)
        # Position Label widget at LineNumber's x and the calculated y_pos
        # `self.x` is the LineNumber widget's x-position (its left edge).
        # `self.y + y_pos` positions the label relative to the LineNumber widget's bottom-left corner.
        label_widget.pos = (self.x, self.y + y_pos)

        # Set text_size for alignment and padding within the label_widget's bounds.
        # This creates an internal box for the text. With halign='right', the text
        # will align to the right, providing dp(5) padding on both left and right.
        # We are using dp(10) total horizontal padding for the text within the label_widget.
        label_widget.text_size = (self.preferred_width - dp(10), actual_line_height)

        self.add_widget(label_widget)
        self._line_number_labels.append(label_widget)