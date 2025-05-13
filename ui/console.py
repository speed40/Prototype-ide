# File: ui/console.py
# Contains the Console widget definition and stream redirection.

import sys
import queue
import threading
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.core.window import Window
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.logger import Logger

# --- Stream Redirector Classes ---

class StdoutRedirector:
    """Redirects stdout to a Kivy Console widget."""
    # Pass the original stdout to the constructor
    def __init__(self, console, original_stdout):
        Logger.info("StdoutRedirector: Initialized")
        self._console = console
        self._original_stdout = original_stdout # Store original stdout
        self._buffer = []
        self._lock = threading.Lock()

    def write(self, text):
        Logger.debug(f"StdoutRedirector: Received text: '{text.strip()}'")
        with self._lock:
            self._buffer.append(text)
        Clock.schedule_once(self._process_buffer, 0.01)

    def _process_buffer(self, dt):
        with self._lock:
            if not self._buffer:
                return
            text_to_write = "".join(self._buffer)
            self._buffer = []

        if text_to_write:
            text_to_write = text_to_write.replace('\r\n', '\n').replace('\r', '\n')
            self._console.write(text_to_write)
            Logger.debug(f"StdoutRedirector: Processed buffer, wrote to console.")

    def flush(self):
        Logger.debug("StdoutRedirector: Flush called")
        # Optional: Force immediate buffer processing, scheduled to be safe
        # Clock.schedule_once(self._process_buffer, 0)

    def isatty(self):
        return False

    @property
    def encoding(self):
        # Return the encoding of the original stdout to prevent recursion
        return self._original_stdout.encoding


class StdinRedirector:
    """Redirects stdin from a Kivy Console widget."""
    # Pass the original stdin to the constructor
    def __init__(self, console, original_stdin):
        Logger.info("StdinRedirector: Initialized")
        self._console = console
        self._original_stdin = original_stdin # Store original stdin
        self._request_queue = queue.Queue()
        self._input_queue = queue.Queue()
        self._waiting_prompt = None

        self._monitor_thread = threading.Thread(target=self._monitor_requests, daemon=True)
        self._monitor_thread.start()

    def readline(self):
        Logger.info("StdinRedirector: readline called - Requesting input from GUI")
        prompt = "" # Prompt handling is more complex, assuming it's printed to stdout

        self._request_queue.put("REQUEST_INPUT")

        Logger.info("StdinRedirector: readline blocking for input...")
        try:
            user_input = self._input_queue.get()
            Logger.info(f"StdinRedirector: readline received input: '{user_input.strip()}'")
            return user_input
        except Exception as e:
            Logger.error(f"StdinRedirector: Error while getting input from queue: {e}")
            return ""

    def _monitor_requests(self):
        Logger.info("StdinRedirector: Monitor thread started")
        while True:
            try:
                request = self._request_queue.get()
                Logger.info(f"StdinRedirector: Monitor thread received request: {request}")
                if request == "REQUEST_INPUT":
                    Clock.schedule_once(lambda dt: self._console._request_input_from_redirector(), 0)
                    Logger.info("StdinRedirector: Scheduled console input request")
            except Exception as e:
                Logger.error(f"StdinRedirector: Error in monitor thread: {e}")
                break

    def read(self, size=-1):
        if size == -1:
            return self.readline()
        Logger.warning("StdinRedirector: read with size not fully implemented")
        return ""

    def isatty(self):
        return False

    @property
    def encoding(self):
        # Return the encoding of the original stdin to prevent recursion
        return self._original_stdin.encoding

# --- End Stream Redirector Classes ---


Window.softinput_mode = 'below_target'

class Console(MDBoxLayout):
    waiting_for_input = BooleanProperty(False)
    input_field = ObjectProperty()
    title = StringProperty("Console")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Logger.info("Console: __init__ called")
        self.orientation = "vertical"
        self.spacing = dp(5)
        self.padding = dp(5)

        self._on_input_callback = None
        self._focus_scheduled = False
        self._setup_ui()
        Logger.info("Console: __init__ finished")

        # --- Stream Redirection Setup ---
        self._original_stdout = sys.stdout
        self._original_stdin = sys.stdin
        # Pass the original streams when creating redirectors
        self._stdout_redirector = StdoutRedirector(self, self._original_stdout)
        self._stdin_redirector = StdinRedirector(self, self._original_stdin)
        sys.stdout = self._stdout_redirector
        sys.stdin = self._stdin_redirector
        Logger.info("Console: stdout and stdin redirected")
        # --- End Stream Redirection Setup ---

    def _setup_ui(self):
        Logger.info("Console: _setup_ui called")
        # Title bar layout (at the top)
        title_bar_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            padding=(dp(5), 0)
        )

        # Console Title Label
        self.title_label = MDLabel(
            text=self.title,
            size_hint_x=1,
            halign="left",
            valign="center",
            theme_text_color="Primary",
            font_style="H6"
        )
        self.bind(title=self.title_label.setter('text'))

        # Close console button
        self.close_button = MDIconButton(
            icon="close",
            size_hint_x=None,
            width=dp(40),
            on_release=self.close_console
        )

        title_bar_layout.add_widget(self.title_label)
        title_bar_layout.add_widget(self.close_button)

        self.add_widget(title_bar_layout)

        # Output area (fills the middle space)
        self.output_scroll = MDScrollView(
            size_hint=(1, 1),
            bar_width=dp(6),
            do_scroll_x=False
        )

        self.output_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(2),
            padding=(dp(5), 0),
            adaptive_height=True
        )
        self.output_layout.bind(minimum_height=self.output_layout.setter('height'))
        self.output_scroll.add_widget(self.output_layout)
        self.add_widget(self.output_scroll)

        # Input area (at the bottom)
        input_layout = BoxLayout(
            size_hint=(1, None),
            height=dp(60),
            spacing=dp(5)
        )

        self.input_field = MDTextField(
            size_hint=(0.85, 1),
            multiline=True,
            hint_text="Type here...",
            write_tab=False,
            on_text_validate=self._handle_input
        )

        self.send_button = MDRaisedButton(
            text="SEND",
            size_hint=(0.15, 1),
            on_release=self._handle_input
        )

        input_layout.add_widget(self.input_field)
        input_layout.add_widget(self.send_button)

        self.add_widget(input_layout)

        # Bind output_layout's width to update text_size of its children labels
        self.output_layout.bind(width=self._update_children_text_sizes)
        Logger.info("Console: Bound output_layout.width to _update_children_text_sizes")

        # Initial focus set directly
        self.input_field.focus = True
        Logger.info("Console: _setup_ui finished, initial focus set")

    def _update_children_text_sizes(self, instance, width):
        Logger.info(f"Console: _update_children_text_sizes called. New width: {width}")
        def update_sizes(_dt):
            for label in instance.children:
                if isinstance(label, MDLabel):
                    label.text_size = (width, None)
                    Logger.debug(f"Console: Updated text_size for a label to ({width}, None)")

        Clock.schedule_once(update_sizes, 0)
        Logger.debug("Console: Scheduled update_sizes for children")

    def write(self, text, color=None):
        Logger.debug(f"Console: write called with text: '{text.strip()[:50]}...'")
        label = MDLabel(
            text=text,
            size_hint_y=None,
            halign="left",
            valign="top",
            theme_text_color="Custom",
            text_color=color or (0.9, 0.9, 0.9, 1),
            padding=(dp(10), dp(5)),
        )
        Logger.debug("Console: Label created.")

        self.output_layout.add_widget(label)
        Logger.debug("Console: Label added to output_layout")

        self._scroll_to_bottom()
        Logger.debug("Console: _scroll_to_bottom called from write")

    def _scroll_to_bottom(self):
        Logger.debug("Console: _scroll_to_bottom executing")
        def _scroll(_dt):
            Logger.debug("Console: _scroll_to_bottom inner function executing")
            if self.output_layout.height > self.output_scroll.height:
                self.output_scroll.scroll_y = 0
                Logger.debug("Console: Scrolled to bottom")
        Clock.schedule_once(_scroll, 0.05)
        Logger.debug("Console: _scroll_to_bottom scheduled inner function")

    def _request_input_from_redirector(self):
        Logger.info("Console: Received input request from redirector")
        prompt = "" # Prompt handling is complex, assuming it's printed to stdout
        self.request_input(prompt, self._handle_redirected_input)

    def _handle_redirected_input(self, text):
        Logger.info(f"Console: Handling redirected input: '{text.strip()}'")
        # Add a newline character like input() does
        self._stdin_redirector._input_queue.put(text + '\n')
        Logger.info("Console: Put input onto stdin redirector queue")

    def _handle_input(self, *args):
        Logger.info("Console: _handle_input called")
        text = self.input_field.text.strip()
        if not text:
            Logger.info("Console: _handle_input - no text, returning")
            return

        if self.waiting_for_input and self._on_input_callback == self._handle_redirected_input:
            Logger.info("Console: _handle_input - processing redirected input")
            # Pass raw text including spaces, add newline in redirected handler
            self._handle_redirected_input(self.input_field.text)

            self.input_field.text = ""
            self.waiting_for_input = False
            self._on_input_callback = None
            Logger.info("Console: Redirected input processed and state reset")

        elif self.waiting_for_input and self._on_input_callback:
             Logger.info("Console: _handle_input - handling standard console input request")
             self.write(text)
             self._on_input_callback(text)

             self.input_field.text = ""
             self.waiting_for_input = False
             self._on_input_callback = None
             Logger.info("Console: Standard console input request processed and state reset")

        else:
            Logger.info(f"Console: _handle_input - echoing command: '{text[:50]}...'")
            self.write(f"> {text}")
            self.input_field.text = ""

        self._maintain_focus()
        Logger.info("Console: _maintain_focus called from _handle_input")


    def _maintain_focus(self):
        """Set focus directly to the input field."""
        Logger.debug("Console: _maintain_focus called")
        if self.input_field:
            self.input_field.focus = True
            Logger.debug("Console: Input field focus set to True")

    def request_input(self, prompt, callback):
        Logger.info(f"Console: request_input called with prompt: '{prompt[:50]}...'")
        self._on_input_callback = callback
        self.waiting_for_input = True
        self.write(prompt, color=(1, 1, 0.5, 1))
        self.input_field.text = ""
        Logger.debug("Console: Input field cleared and waiting_for_input set in request_input")
        self._maintain_focus()
        Logger.debug("Console: _maintain_focus called from request_input")


    def close_console(self, *args):
        Logger.info("Console: close_console called - Restoring stdout/stdin and stopping app")
        # --- Restore Stream Redirection ---
        sys.stdout = self._original_stdout
        sys.stdin = self._original_stdin
        Logger.info("Console: stdout and stdin restored")
        # --- End Restore Stream Redirection ---

        MDApp.get_running_app().stop()