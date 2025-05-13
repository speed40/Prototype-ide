# history_manager.py
# This file contains the HistoryManager class for managing undo/redo states.

import hashlib # Used for generating hashes to compare states efficiently
from collections import deque # Use deque for efficient appending and popping from ends
from kivy.clock import Clock # Import Clock for scheduling debounce
from kivy.properties import ObjectProperty # Keep for clarity if needed elsewhere, though not strictly used for binding here
from kivy.logger import Logger # For logging history actions

class HistoryManager:
    """
    Manages the history of text states for undo/redo functionality.
    Uses a deque for efficient state storage and a debounce mechanism
    to prevent excessive state commits on every key press.
    """
    # No Kivy properties needed since it's not a Kivy EventDispatcher

    # Accept the Kivy Clock instance directly in __init__ for injection
    def __init__(self, max_states=30, app_clock=None):
        """
        Initializes the HistoryManager.

        Args:
            max_states (int): The maximum number of states to store in history.
            app_clock (kivy.clock.Clock): The Kivy Clock instance for scheduling.
        """
        self.max_states = max_states
        # Use deque with maxlen for efficient limited history storage
        self.states = deque(maxlen=max_states)
        self.current_index = -1 # Index of the current state in the deque
        self._debounce_event = None # Reference to the scheduled debounce event
        self.debounce_time = 0.5  # Time in seconds to wait before committing state after last change
        self.pending_text = None # Stores the text that's waiting to be committed

        # Store the injected Kivy Clock instance
        self.app_clock = app_clock
        if not self.app_clock:
             Logger.warning("HistoryManager: No Kivy Clock instance provided! Debouncing will not work.")

    def _get_hash(self, text):
        """Generates SHA256 hash of the text for efficient state comparison."""
        if not isinstance(text, str):
            Logger.warning(f"HistoryManager: Attempted to hash non-string type: {type(text)}")
            return hashlib.sha256(b'').hexdigest() # Return hash of empty string for safety
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def add_state(self, text):
        """
        Adds a new text state to the history if it's different from the last state.
        If not at the end of history (due to undo), truncates future history.
        """
        text_hash = self._get_hash(text)
        # Check if the current state is identical to the last committed state
        if self.current_index >= 0 and text_hash == self._get_hash(self.states[self.current_index]):
            # Logger.info("HistoryManager: Text state is identical to current, not adding to history.") # Keep logging minimal
            return # Don't add duplicate states

        # If we're not at the end of the history (i.e., we've undone some steps),
        # adding a new state should truncate the "future" history.
        if self.current_index < len(self.states) - 1:
            # Ensure we are working with a list to truncate effectively, then convert back to deque
            self.states = deque(list(self.states)[:self.current_index + 1], maxlen=self.max_states)
            Logger.info(f"HistoryManager: Truncating history. New length: {len(self.states)}")

        # Add the new state to the end of the deque
        self.states.append(text)
        # Update the current index to point to the newly added state
        self.current_index = len(self.states) - 1
        # Logger.info(f"HistoryManager: State added. History size: {len(self.states)}, Index: {self.current_index}") # Keep logging minimal

    def commit_state_debounced(self, text):
        """
        Commits the state after a debounce period to avoid saving state on every key press.
        Cancels any pending commit and schedules a new one.
        """
        # If there's a pending debounce event, cancel it
        if self._debounce_event:
            self._debounce_event.cancel()
            self._debounce_event = None # Clear the event so a new one can be scheduled

        self.pending_text = text # Store the text to be committed
        if self.app_clock:
            # Schedule _perform_commit to be called after debounce_time
            self._debounce_event = self.app_clock.schedule_once(self._perform_commit, self.debounce_time)
            # Logger.info(f"HistoryManager: Scheduled commit for text: {text[:20]}... Debounce event: {self._debounce_event}") # Keep logging minimal
        else:
            Logger.warning("HistoryManager: No Kivy Clock instance provided. Debounced commit cannot be scheduled.")
            # As a fallback, if no clock is provided, commit immediately
            self.add_state(self.pending_text)
            self.pending_text = None

    def _perform_commit(self, dt):
        """
        Internal method to perform the actual state commit.
        Called by the debounce event after the specified time.
        """
        if self.pending_text is not None:
            self.add_state(self.pending_text)
            # Logger.info(f"HistoryManager: Performed debounced commit for text: {self.pending_text[:20]}... History size: {len(self.states)}, Index: {self.current_index}") # Keep logging minimal
            self.pending_text = None # Clear pending text after commit
        self._debounce_event = None # Clear the event reference after it's executed

    def undo(self):
        """
        Move backward in the history stack and return the text state.
        Returns None if there is no more undo history.
        """
        if self.current_index > 0:
            self.current_index -= 1
            Logger.info(f"HistoryManager: Undoing. New index: {self.current_index}")
            return self.states[self.current_index]
        Logger.info("HistoryManager: No more undo history.")
        return None

    def redo(self):
        """
        Move forward in the history stack and return the text state.
        Returns None if there is no more redo history.
        """
        if self.current_index < len(self.states) - 1:
            self.current_index += 1
            Logger.info(f"HistoryManager: Redoing. New index: {self.current_index}")
            return self.states[self.current_index]
        Logger.info("HistoryManager: No more redo history.")
        return None

    def get_pointer(self):
        """
        Generates a visual pointer string representing the current position in states.
        Uses '~' for states and '°' for the current state.
        """
        if not self.states:
            return ""

        pointer = []
        for i in range(len(self.states)):
            if i == self.current_index:
                pointer.append("°") # Degree sign for pointer
            else:
                pointer.append("~") # Tilde for states
        return " ".join(pointer)

    def cleanup(self):
        """
        Cancels any pending debounce timer.
        Should be called when the HistoryManager is no longer needed
        to prevent potential issues when the app closes.
        """
        Logger.info("HistoryManager: Running cleanup.")
        if self._debounce_event:
            self._debounce_event.cancel()
            self._debounce_event = None

# Note: The App and __main__ block should NOT be in this file
# This file only contains the reusable HistoryManager class
