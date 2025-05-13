# File: showcases/showcase_console.py
# Demonstrates the usage of the Console widget with stdout/stdin redirection.

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Place window configurations at the top
from kivy.core.window import Window
Window.softinput_mode = 'below_target'

from kivymd.app import MDApp
from kivy.clock import Clock
from ui.console import Console
from kivymd.uix.screen import MDScreen
from kivy.logger import Logger

import threading # Import threading to run the demo code in a separate thread
import time      # Import time for delays in the demo

class ConsoleDemoApp(MDApp):
    def build(self):
        Logger.info("ConsoleDemoApp: build method called")
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Dark"

        # Create a root screen
        screen = MDScreen()
        Logger.info("ConsoleDemoApp: MDScreen created")

        # Create main console
        self.console = Console()
        Logger.info("ConsoleDemoApp: Console widget created")

        # Set the size_hint and pos_hint directly on the console widget
        self.console.size_hint = (0.95, 0.65)
        self.console.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        Logger.info(f"ConsoleDemoApp: Console size_hint set to {self.console.size_hint}")
        Logger.info(f"ConsoleDemoApp: Console pos_hint set to {self.console.pos_hint}")

        # Add the console to the screen
        screen.add_widget(self.console)
        Logger.info("ConsoleDemoApp: Console widget added to screen")

        # Schedule the demo runner function to start AFTER the console has been sized
        # Bind the console's 'size' property to a method
        self.console.bind(size=self._on_console_sized)
        Logger.info("ConsoleDemoApp: Bound console.size to _on_console_sized")

        # Removed: Initial demo input request is now handled by the runner thread
        # Clock.schedule_once(self.demo_input_request, 2)

        Logger.info("ConsoleDemoApp: build method finished, returning screen")
        return screen

    def _on_console_sized(self, instance, size):
        """Called once after the console widget has received its size."""
        Logger.info(f"ConsoleDemoApp: _on_console_sized called. Console size: {size}")
        # Unbind the event to ensure this only runs once
        instance.unbind(size=self._on_console_sized)
        Logger.info("ConsoleDemoApp: Unbound console.size")

        # Now that the console is sized, start the demo runner function in a separate thread
        Logger.info("ConsoleDemoApp: Starting demo runner thread...")
        demo_thread = threading.Thread(target=self.demo_runner_function, daemon=True)
        demo_thread.start()
        Logger.info("ConsoleDemoApp: Demo runner thread started.")


    def demo_runner_function(self):
        """A simple function to run in a separate thread to test stdout/stdin redirection."""
        Logger.info("ConsoleDemoApp: demo_runner_function started.")
        print("Hello from the runner thread!")
        time.sleep(1) # Pause for a moment
        print("This output should appear in the console.")
        time.sleep(1)

        # Request input using the standard input() function
        try:
            user_input = input("Please enter something: ")
            print(f"You entered: {user_input}")

            another_input = input("Enter another line: ")
            print(f"Second input: {another_input}")

        except Exception as e:
            print(f"Error during input: {e}") # Print errors to the console too

        print("Demo runner function finished.")
        Logger.info("ConsoleDemoApp: demo_runner_function finished.")


    # Removed the old demo_input_request method
    # def demo_input_request(self, dt):
    #     Logger.info(f"ConsoleDemoApp: demo_input_request executing after delay {dt}")
    #     self.console.request_input(
    #         "Enter your name:",
    #         lambda name: self.console.write(f"Hello, {name}!", color=(0, 1, 0, 1))
    #     )
    #     Logger.info("ConsoleDemoApp: demo_input_request finished")


if __name__ == '__main__':
    Logger.info("ConsoleDemoApp: Starting application run")
    ConsoleDemoApp().run()
    Logger.info("ConsoleDemoApp: Application run finished")