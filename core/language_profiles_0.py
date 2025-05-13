"""
language_profiles.py - Language definition and syntax analysis system.
"""

import re
import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Pattern, TypedDict, Any
from kivy.logger import Logger

# --- Type Definitions ---
# Using Dict[str, Any] in validation/compilation functions as we check structure dynamically
# LanguageDefinition TypedDict serves as the ideal structure we aim for *after* validation/compilation
class LanguageDefinition(TypedDict):
    language: str
    comment: Optional[str]
    block_comment: List[Optional[str]]
    indent: str # Assuming 'indent' is still expected by the Analyzer logic
    indent_triggers: List[str] # Store as strings before compilation
    dedent_triggers: List[str] # Store as strings before compilation
    definitions: Dict[str, Optional[str]] # Store as strings before compilation
    symbol_patterns: Dict[str, Optional[str]] # Store as strings before compilation
    syntax_tokens: Dict[str, str] # Store as strings before compilation
    suggestions_categorized: Dict[str, List[str]]

# Define types for compiled patterns to improve clarity
CompiledPatterns = Dict[str, Optional[Pattern]]
TriggerPatterns = List[Optional[Pattern]]

class LanguageProfile(TypedDict):
    """Represents a loaded language profile with compiled patterns."""
    language: str
    comment: Optional[str]
    block_comment: List[Optional[str]]
    indent: str # Store the indent string
    indent_triggers: TriggerPatterns # Store as compiled patterns
    dedent_triggers: TriggerPatterns # Store as compiled patterns
    definitions: CompiledPatterns # Store as compiled patterns
    symbol_patterns: CompiledPatterns # Store as compiled patterns
    syntax_tokens: CompiledPatterns # Store as compiled patterns
    suggestions_categorized: Dict[str, List[str]]


class SymbolInfo(TypedDict):
    type: str
    scope: int
    metadata: Dict[str, Any]

# --- Constants ---
# Use __file__ safely with Pathlib - Adjusted to go up two levels based on observed structure
ASSETS_DIR = Path(__file__).parent.parent / "assets" / "language_profiles"

# --- Core Implementation ---
class LanguageProfileManager:
    """Central manager for all language profiles."""

    _instance: Optional["LanguageProfileManager"] = None

    def __new__(cls) -> "LanguageProfileManager":
        """Ensure only one instance of LanguageProfileManager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._profiles: Dict[str, LanguageProfile] = {}
            # Load profiles immediately upon instantiation
            cls._instance.load_profiles()
            Logger.info("LanguageProfileManager initialized and profiles loaded.")
        return cls._instance

    def load_profiles(self) -> None:
        """Load all language profiles from JSON files."""
        Logger.info(f"Attempting to load profiles from: {ASSETS_DIR}")
        if not ASSETS_DIR.exists():
            Logger.error(f"Language profiles directory not found: {ASSETS_DIR}")
            # If directory not found, ensure at least a generic profile is created
            if 'generic' not in self._profiles:
                 self._create_generic_profile()
            return

        loaded_count = 0
        # Sort files for consistent loading order (optional but good practice)
        for profile_file in sorted(ASSETS_DIR.glob("*.json")):
            try:
                Logger.debug(f"Attempting to load file: {profile_file}")
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data: Dict[str, Any] = json.load(f) # Load as generic dict first

                # --- ADDED DEBUG LOGGING HERE ---
                # Logger.debug(f"Successfully loaded data from {profile_file.name}: {profile_data}") # Too noisy
                # --- END ADDED DEBUG LOGGING ---

                if not self._validate_profile_data(profile_data):
                    Logger.warning(f"Skipping invalid profile: {profile_file.name}")
                    continue

                # Compile regex patterns and create a LanguageProfile
                # Assumes profile_data is valid after validation
                compiled_profile = self._compile_patterns(profile_data)
                self._profiles[compiled_profile['language']] = compiled_profile
                loaded_count += 1
                Logger.info(f"Loaded language profile: {compiled_profile['language']}")

            except json.JSONDecodeError as e:
                Logger.error(f"Invalid JSON in {profile_file.name}: {e}")
            except KeyError as e:
                 # This specific KeyError during loading might indicate accessing
                 # a required key that was expected during parsing but wasn't there,
                 # or an issue before _validate_profile_data catches it.
                 # It's less likely now with safer validation/compilation.
                 Logger.error(f"KeyError during loading {profile_file.name}: {e}")
            except Exception as e:
                Logger.error(f"Error loading {profile_file.name}: {str(e)}")

        # After attempting to load all files, ensure generic profile exists
        if 'generic' not in self._profiles:
             Logger.warning("'generic' profile not found after file loading - creating fallback.")
             self._create_generic_profile()


    def _validate_profile_data(self, profile_data: Dict[str, Any]) -> bool:
         """Validate the raw data loaded from a profile JSON."""
         # Note: Using Dict[str, Any] here as input because we are validating
         # its structure before we can confidently treat it as LanguageDefinition.

         # IMPORTANT: This list MUST match the keys expected by the rest of the
         # CodeAnalyzer and _compile_patterns logic for a LanguageProfile.
         # If you change this list, you MUST update the code that uses the profile.
         required_keys: List[str] = [
             'language', 'comment', 'block_comment', 'indent', # 'indent' is REQUIRED by CodeAnalyzer logic
             'indent_triggers', 'dedent_triggers', 'definitions',
             'symbol_patterns', 'syntax_tokens', 'suggestions_categorized'
         ]
         missing_keys = [key for key in required_keys if key not in profile_data]
         if missing_keys:
             # Modified error message to show missing keys
             Logger.error(f"Profile missing required keys. Needs: {required_keys}. Missing: {missing_keys}")
             return False

         # --- Additional Type and Structure Checks (can be expanded) ---
         # These checks assume the required keys are present based on the check above.
         # Using .get() with appropriate type checks for safety.

         if not isinstance(profile_data.get('language'), str) or not profile_data.get('language'):
             Logger.error("Profile 'language' must be a non-empty string.")
             return False
         # Check block_comment is a list of two strings or None
         block_comment = profile_data.get('block_comment')
         if not isinstance(block_comment, list) or len(block_comment) != 2 or \
            not all(isinstance(x, (str, type(None))) for x in block_comment):
              Logger.error("Profile 'block_comment' must be a list of two strings or None.")
              return False

         # 'indent' is required, so direct access might be okay if validation passes,
         # but using .get is still safer if logic changes later.
         # Ensure indent is a non-empty string
         indent_value = profile_data.get('indent')
         if not isinstance(indent_value, str) or not indent_value:
              Logger.error("Profile 'indent' must be a non-empty string.")
              # Return False here if indent is required and invalid type
              # The 'missing_keys' check already handles it if it's completely absent.
              # This check handles it if it's present but wrong type.
              return False # Validation fails if indent is wrong type

         # Check trigger lists are lists of strings (or None)
         for trigger_list_key in ['indent_triggers', 'dedent_triggers']:
             triggers = profile_data.get(trigger_list_key, [])
             if not isinstance(triggers, list) or not all(isinstance(x, (str, type(None))) for x in triggers):
                 Logger.error(f"Profile '{trigger_list_key}' must be a list of strings or None.")
                 return False

         # Check definition, symbol, syntax token dictionaries are dicts with string keys and string/None values
         for pattern_dict_key in ['definitions', 'symbol_patterns', 'syntax_tokens']:
              pattern_dict = profile_data.get(pattern_dict_key, {})
              if not isinstance(pattern_dict, dict) or not all(isinstance(k, str) and isinstance(v, (str, type(None))) for k, v in pattern_dict.items()):
                   Logger.error(f"Profile '{pattern_dict_key}' must be a dictionary with string keys and string/None values.")
                   return False


         # Check suggestions_categorized is a dictionary with list values
         suggestions_dict = profile_data.get('suggestions_categorized', {})
         if not isinstance(suggestions_dict, dict) or not all(isinstance(v, list) for v in suggestions_dict.values()):
             Logger.error("Profile 'suggestions_categorized' must be a dictionary with list values.")
             return False


         Logger.debug("Profile data validation successful.")
         return True


    def _compile_patterns(self, profile_data: Dict[str, Any]) -> LanguageProfile:
        """Compile regex patterns from loaded profile data."""
        # Assumes profile_data has passed _validate_profile_data, so required keys exist and have basic types.
        # Use .get() with defaults for safety when accessing potentially optional nested data or compiling.

        # Safely get indent string after validation
        indent_string = profile_data.get('indent', '    ')

        compiled_profile: LanguageProfile = {
            'language': profile_data['language'], # 'language' is guaranteed by validation
            'comment': profile_data.get('comment'),
            'block_comment': profile_data.get('block_comment', [None, None]),
            'indent': indent_string, # Use the validated indent string
            # Compile patterns, ensuring the source lists/dicts are treated as potentially missing or having None values
            'indent_triggers': [self._safe_compile(p) for p in profile_data.get('indent_triggers', []) if isinstance(p, str)],
            'dedent_triggers': [self._safe_compile(p) for p in profile_data.get('dedent_triggers', []) if isinstance(p, str)],
            'definitions': {k: self._safe_compile(v) for k, v in profile_data.get('definitions', {}).items() if isinstance(k, str) and isinstance(v, str)},
            'symbol_patterns': {k: self._safe_compile(v) for k, v in profile_data.get('symbol_patterns', {}).items() if isinstance(k, str) and isinstance(v, str)},
            'syntax_tokens': {k: self._safe_compile(v) for k, v in profile_data.get('syntax_tokens', {}).items() if isinstance(k, str) and isinstance(v, str)},
            'suggestions_categorized': profile_data.get('suggestions_categorized', {}) # Use .get with default
        }
        return compiled_profile

    def _safe_compile(self, pattern: Optional[str]) -> Optional[Pattern]:
        """Safely compile a regex pattern with error handling."""
        if not isinstance(pattern, str) or not pattern: # Explicitly check for string type and if it's empty
            # Logger.debug(f"Skipping compilation for non-string/empty pattern: {pattern}") # Too noisy
            return None
        try:
            return re.compile(pattern)
        except re.error as e:
            Logger.error(f"Invalid regex pattern '{pattern}': {str(e)}")
            return None
        except TypeError as e:
             Logger.error(f"TypeError compiling pattern '{pattern}': {str(e)}")
             return None


    def _create_generic_profile(self) -> None:
        """Create a minimal fallback generic profile."""
        Logger.warning("Creating fallback generic profile...")
        self._profiles['generic'] = {
            'language': 'generic',
            'comment': '#', # Provide a default comment marker
            'block_comment': ['', ''],
            'indent': '    ', # Use 4 spaces as standard generic indent
            'indent_triggers': [], # Compiled empty list
            'dedent_triggers': [], # Compiled empty list
            'definitions': {}, # Compiled empty dict
            'symbol_patterns': {}, # Compiled empty dict
            # Include syntax_tokens even if empty, as it's a required key
            'syntax_tokens': {}, # Compiled empty dict
            'suggestions_categorized': {
                'keywords': [],
                'operators': [],
                'builtins': [],
                'exceptions': [] # Add common categories
            }
        }
        # Patterns are already empty lists/dicts, no need to compile
        Logger.warning("Created fallback generic profile.")

    def get_profile(self, language: str) -> LanguageProfile:
        """Get a language profile with fallback to generic."""
        requested_language = language.lower()
        # Try to get the requested language profile
        profile = self._profiles.get(requested_language)

        if profile:
            Logger.debug(f"Found profile for language: {requested_language}")
            return profile
        else:
            # If requested profile not found, try to get the generic profile safely
            generic_profile = self._profiles.get('generic')
            if generic_profile:
                 Logger.warning(f"Profile for '{language}' not found, using 'generic'.")
                 return generic_profile
            else:
                 # If even the generic profile is missing, this is a critical error.
                 # Return a minimal, safe fallback structure to prevent crashes.
                 Logger.critical("Generic language profile not found and no requested profile found! Returning a minimal fallback profile.")
                 # This minimal profile must satisfy the structure expected by CodeAnalyzer
                 return {
                     'language': 'minimal_fallback',
                     'comment': '#',
                     'block_comment': ['', ''],
                     'indent': '    ',
                     'indent_triggers': [], # Must be a list of compiled patterns (empty)
                     'dedent_triggers': [], # Must be a list of compiled patterns (empty)
                     'definitions': {}, # Must be a dict of compiled patterns (empty)
                     'symbol_patterns': {}, # Must be a dict of compiled patterns (empty)
                     'syntax_tokens': {}, # Must be a dict of compiled patterns (empty)
                     'suggestions_categorized': {} # Must be a dict with list values (empty)
                 }

    def get_available_languages(self) -> List[str]:
        """Get sorted list of available language names."""
        return sorted(self._profiles.keys())

class CodeAnalyzer:
    """Real-time code analyzer with symbol tracking and scope management."""

    def __init__(self, language: str = 'python'):
        self.language = language.lower()
        # Get the profile from the singleton manager
        self.profile = LanguageProfileManager().get_profile(self.language)
        self.symbol_table = SymbolTable()
        self._reset_state()
        Logger.info(f"CodeAnalyzer initialized for language: {self.language}")


    def _reset_state(self):
        """Reset analysis state for new document."""
        self.current_scope = 0
        # Stack stores expected minimum indent for each scope level
        self.scope_stack: List[int] = [0]
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None
        # Store state per line: {line_num: {'indent': int, 'scope': int}}
        # Use -1 as a key for the "state before the first line" for easier lookup
        self.line_states: Dict[int, Dict[str, int]] = {-1: {'indent': 0, 'scope': 0}}
        # Clear symbol table for a fresh analysis
        self.symbol_table.clear() # ADDED: Clear symbol table on reset
        Logger.info("CodeAnalyzer state reset.")


    def analyze_text(self, text: str) -> None:
        """Analyze the entire text line by line."""
        Logger.info(f"CodeAnalyzer: Analyzing full text for language: {self.language}")
        self._reset_state() # Reset state before analyzing new text

        # Analyze line by line
        for i, line in enumerate(text.split('\n')):
            self.analyze_line(i, line)

        Logger.info(f"CodeAnalyzer: Finished analyzing full text.")


    def analyze_line(self, line_num: int, line_text: str) -> None:
        """Analyze a single line of code."""
        # Add line number to the log for easier debugging
        Logger.debug(f"Analyzing line {line_num}: '{line_text.rstrip()}'") # rstrip to avoid logging trailing newline

        # Get previous line's state (handle line_num 0 by checking line_num - 1)
        # The line_states is initialized with state for line -1.
        prev_line_num = line_num - 1
        # Ensure default dictionary includes 'indent' and 'scope' to prevent KeyError
        # Access state of the *previous* line.
        prev_state = self.line_states.get(prev_line_num, {'indent': 0, 'scope': 0})
        prev_indent = prev_state.get('indent', 0) # Use .get for safety, though default dict should prevent KeyError


        # Handle empty lines - carry over state from previous line
        if not line_text.strip():
             # Store state for the current empty line, inheriting scope from previous line
             self.line_states[line_num] = {'indent': len(line_text) - len(line_text.lstrip()), 'scope': prev_state.get('scope', 0)} # Carry over previous scope
             Logger.debug(f"Line {line_num}: Empty, carrying scope {self.line_states[line_num]['scope']}")
             return


        # Calculate current indent
        current_indent = len(line_text) - len(line_text.lstrip())
        # Compare current indent to the expected indent of the innermost scope on the stack
        # Make sure scope_stack is not empty before accessing [-1]
        expected_stack_indent = self.scope_stack[-1] if self.scope_stack else 0

        # --- ADDED DEBUG LOGGING HERE ---
        # Logger.debug(f"Line {line_num}: Current indent = {current_indent} (type: {type(current_indent)})")
        # if self.scope_stack:
        #     Logger.debug(f"Line {line_num}: Scope stack top = {self.scope_stack[-1]} (type: {type(self.scope_stack[-1])})")
        #     Logger.debug(f"Line {line_num}: Full Scope stack = {self.scope_stack}")
        # else:
        #      Logger.debug(f"Line {line_num}: Scope stack is empty.")
        # --- END ADDED DEBUG LOGGING ---


        # --- Scope Management ---
        # Deding happens when the current line's indent is less than the expected indent
        # of the current innermost scope on the stack.
        # Pop scopes if current indent is less than the indent of the top of the stack.
        # ERROR LIKELY OCCURS IN THE COMPARISON BELOW IF self.scope_stack[-1] IS NOT AN INT
        while self.scope_stack and current_indent < self.scope_stack[-1]:
             self.scope_stack.pop()
             self.current_scope = max(0, self.current_scope - 1)
             self.symbol_table.exit_scope()
             Logger.debug(f"Line {line_num}: Dedented, current scope {self.current_scope}. Scope stack: {self.scope_stack}")


        # Check for indent triggers on the current line
        # Indenting typically happens *after* a line with an indent trigger,
        # meaning the *next* lines will have a higher indent and scope.
        # We push the expected indent for the *next* scope level onto the stack.
        # Check if profile and triggers exist before iterating
        if self.profile and self.profile.get('indent_triggers'):
            # Logger.debug(f"Line {line_num}: Checking indent triggers...") # Too noisy
            if any(trigger and trigger.search(line_text) for trigger in self.profile['indent_triggers']):
                # The expected indent for the *next* scope level is the current line's
                # indent plus the language's standard indent size.
                # Use profile['indent'] here as it's required and validated to be a non-empty string
                # Fallback to 4 spaces just in case, though validation should prevent this.
                indent_string = self.profile.get('indent', '    ')
                expected_next_indent = current_indent + len(indent_string)
                self.scope_stack.append(expected_next_indent)
                # Increment current_scope and enter symbol table scope
                self.current_scope += 1
                self.symbol_table.enter_scope(self.current_scope)
                Logger.debug(f"Line {line_num}: Indent trigger fired, pushed {expected_next_indent} (type: {type(expected_next_indent)}), new scope {self.current_scope}. Scope stack: {self.scope_stack}")
            # else:
                 # Logger.debug(f"Line {line_num}: No indent trigger matched.")


        # After updating scope based on triggers and dedents, the current line's
        # scope is the top of the stack.

        # --- Analyze Code Constructs ---
        self._analyze_constructs(line_text)

        # --- Store Current Line State ---
        # Store the final scope for this line after all checks
        self.line_states[line_num] = {
            'indent': current_indent,
            'scope': self.current_scope
        }
        # Logger.debug(f"Line {line_num}: Processed, stored state: {self.line_states[line_num]}. Final scope {self.current_scope}. Scope stack: {self.scope_stack}") # Too noisy


    def _analyze_constructs(self, line_text: str) -> None:
        """Analyze language constructs in a line of code."""
        stripped = line_text.lstrip()
        # Logger.debug(f"Analyzing constructs in stripped line: '{stripped}'") # Too noisy

        # Check if profile and definitions exist before iterating
        if self.profile and self.profile.get('definitions'):
            # Check definitions (functions, classes, etc.)
            # Iterate through compiled patterns
            for construct, pattern in self.profile['definitions'].items():
                if not pattern: # Skip if pattern failed to compile (will be None)
                    # Logger.debug(f" Skipping definition check for '{construct}': pattern is None.") # Too noisy
                    continue

                # Use .search() as definitions can appear anywhere on a line after leading whitespace
                if match := pattern.search(stripped):
                    # Logger.debug(f" Definition pattern '{construct}' matched.") # Too noisy
                    self._handle_definition(construct, match)
                    # Assuming only one definition per line, break after the first match
                    # If multiple definitions per line are possible, remove break.
                    break # Optimization: assuming one major definition per line


        # Check if profile and symbol_patterns exist before iterating
        if self.profile and self.profile.get('symbol_patterns'):
            # Check symbol patterns (variables, imports, etc.)
            # Iterate through compiled patterns
            for symbol_type, pattern in self.profile['symbol_patterns'].items():
                if not pattern: # Skip if pattern failed to compile (will be None)
                     # Logger.debug(f" Skipping symbol pattern check for '{symbol_type}': pattern is None.") # Too noisy
                     continue

                # Use .search() as symbols can appear anywhere on a line after leading whitespace
                if match := pattern.search(stripped):
                    # Logger.debug(f" Symbol pattern '{symbol_type}' matched.") # Too noisy
                    self._handle_symbol(symbol_type, match)
                    # Assuming multiple symbols per line are possible, don't break here.
                    # For example, 'import os, sys' has two symbols.
                    # If only one symbol per line is expected, add break.


    def _handle_definition(self, construct: str, match: re.Match) -> None:
        """Handle a language construct definition."""
        # Logger.debug(f"Handling definition: '{construct}' with match {match.groups()}") # Too noisy
        if construct == 'function':
            self._handle_function_def(match)
        elif construct == 'class':
            self._handle_class_def(match)
        # Add handling for other definition types here as needed
        # TODO: Consider passing line_num here if needed for symbol location metadata


    def _handle_function_def(self, match: re.Match) -> None:
        """Process a function definition."""
        # --- CORRECTED GROUP CHECK HERE ---
        # Ensure group 1 (function name) exists and is not empty
        func_name = match.group(1) if match.lastindex is not None and match.lastindex >= 1 and match.group(1) else None # Updated check
        # Logger.debug(f" Processing function definition, name candidate: {func_name}") # Too noisy
        if func_name:
            # Update current function context
            self.current_function = func_name
            self.current_class = None # Functions within a class will update current_class separately

            # Add function symbol to the symbol table at the current scope
            self.symbol_table.add_symbol(func_name, 'function', {'scope': self.current_scope})
            Logger.debug(f" Found function: {func_name} at scope {self.current_scope}")

            # --- CORRECTED PARAMETER GROUP CHECK HERE ---
            # Handle parameters (check if group 2 exists and is not None/empty string)
            if match.lastindex is not None and match.lastindex >= 2 and (params_str := match.group(2)):
                # Logger.debug(f" Found parameters string: '{params_str}'") # Too noisy
                for param in self._parse_parameters(params_str):
                    # Add parameter symbol to the symbol table at the current scope
                    self.symbol_table.add_symbol(param, 'parameter', {
                        'function': func_name, # Link parameter to its function
                        'scope': self.current_scope
                    })
                    Logger.debug(f" Found parameter: {param}")
            # else:
                 # Logger.debug(" No parameters found.")

    def _handle_class_def(self, match: re.Match) -> None:
        """Process a class definition."""
        # --- CORRECTED GROUP CHECK HERE ---
        # Ensure group 1 (class name) exists and is not empty
        class_name = match.group(1) if match.lastindex is not None and match.lastindex >= 1 and match.group(1) else None # Updated check
        # Logger.debug(f" Processing class definition, name candidate: {class_name}") # Too noisy
        if class_name:
            # Update current class context
            self.current_class = class_name
            self.current_function = None # Reset function context when entering class

            # Add class symbol to the symbol table at the current scope
            self.symbol_table.add_symbol(class_name, 'class', {'scope': self.current_scope})
            Logger.debug(f"Found class: {class_name} at scope {self.current_scope}")
            # TODO: Handle inheritance (assuming group 2 is base classes string)


    def _parse_parameters(self, param_str: str) -> List[str]:
        """Extract parameter names from a parameter string (handles common Python syntax)."""
        # Logger.debug(f" Parsing parameters from string: '{param_str}'") # Too noisy
        if not isinstance(param_str, str) or not param_str.strip(): # Check for None or empty string
            # Logger.debug(" Parameter string is empty or None, returning empty list.") # Too noisy
            return []

        params: List[str] = []
        # Split by commas, try to be smart about commas in default values or type hints
        # A robust solution might require a more sophisticated parser.
        # Simple split for now:
        for param in re.split(r',\s*', param_str.strip()):
            # Remove type hints (e.g., ": int") and default values (e.g., "= None")
            # This regex `[:=].*$` matches from `:` or `=` to the end of the string.
            clean_param = re.sub(r'[:=].*$', '', param).strip()
            if clean_param:
                # Also handle *args and **kwargs by stripping leading *
                clean_param = clean_param.lstrip('*')
                if clean_param: # Check if not empty after stripping '*'
                     params.append(clean_param)
                     # Logger.debug(f"  Extracted clean parameter: {clean_param}") # Too noisy

        return params


    def _handle_symbol(self, symbol_type: str, match: re.Match) -> None:
        """Process a symbol (variable, import, etc.)."""
        # Logger.debug(f"Handling symbol type: '{symbol_type}' with match {match.groups()}") # Too noisy
        # Find the first non-None and non-empty captured group as the symbol name
        # Use match.lastindex to safely check for groups
        if match.lastindex is not None and match.lastindex > 0:
             symbol_name = next((match.group(i) for i in range(1, match.lastindex + 1) if match.group(i) is not None and match.group(i) != ''), None)
        else:
             symbol_name = None


        if symbol_name:
            # Add symbol to the symbol table at the current scope
            self.symbol_table.add_symbol(symbol_name, symbol_type, {
                'scope': self.current_scope,
                'function': self.current_function, # Link symbol to current function/class if applicable
                'class': self.current_class
            })
            Logger.debug(f" Found symbol: {symbol_name} ({symbol_type}) at scope {self.current_scope}")
        # else:
             # Logger.debug(f" No symbol name found for type '{symbol_type}'.")


    def get_suggestions(self) -> List[str]:
        """Get all relevant code suggestions from language profile and current scope."""
        Logger.info("Generating suggestions...")
        suggestions: set[str] = set() # Use a set to automatically handle uniqueness

        # Add language-specific suggestions from the profile, if profile exists and has suggestions
        if self.profile and self.profile.get('suggestions_categorized'):
            Logger.debug(" Adding language-specific suggestions.")
            for category, category_list in self.profile['suggestions_categorized'].items():
                if isinstance(category_list, list): # Ensure the value is a list
                    suggestions.update(category_list) # Add to the set
                    Logger.debug(f"  Added {len(category_list)} suggestions from category '{category}'.")
                else:
                     Logger.warning(f" Suggestions category '{category}' is not a list: {category_list}")


        # Add symbols from the current context (current scope and parent scopes)
        # Pass the analyzer's current scope ID to the symbol table
        Logger.debug(f" Getting symbols from current scope ({self.current_scope}) and visible parent scopes.")
        context_symbols = self.symbol_table.get_symbols(self.current_scope)
        suggestions.update(context_symbols) # Add to the set
        Logger.debug(f" Added {len(context_symbols)} symbols from context.")


        # Return sorted list of unique suggestions
        sorted_suggestions = sorted(list(suggestions))
        Logger.info(f" Generated {len(sorted_suggestions)} unique suggestions.")
        return sorted_suggestions


class SymbolTable:
    """Hierarchical symbol table with scope support."""

    def __init__(self):
        # symbols: {scope_id: {symbol_name: SymbolInfo}}
        self.symbols: Dict[int, Dict[str, SymbolInfo]] = defaultdict(dict)
        # scopes: Stack of active scope IDs (integers) - This stack is managed by CodeAnalyzer.
        # The SymbolTable just needs to store symbols by scope ID.
        Logger.info("SymbolTable initialized.")

    def clear(self) -> None:
        """Clears the symbol table for a new analysis."""
        self.symbols.clear()
        Logger.debug("SymbolTable cleared.")


    def enter_scope(self, scope_id: int) -> None:
        """Enter a new scope (create a dictionary entry for the scope ID if it doesn't exist)."""
        if scope_id not in self.symbols:
            self.symbols[scope_id] = {}
            Logger.debug(f" Created dictionary for scope ID {scope_id} in SymbolTable.")
        # Note: This method doesn't manage a stack here; the analyzer does.
        Logger.debug(f"SymbolTable informed of entering scope {scope_id}")


    def exit_scope(self) -> None:
        """Exit the current scope (no action needed in SymbolTable's storage here)."""
        # The analyzer manages the scope stack. SymbolTable just stores data.
        Logger.debug("SymbolTable informed of exiting scope.")


    def add_symbol(self, name: str, symbol_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a symbol to a specific scope."""
        if metadata is None:
            metadata = {}

        # Get the scope ID from metadata, or assume global scope (0) as a fallback
        scope_id = metadata.get('scope', 0)

        if scope_id not in self.symbols:
             self.symbols[scope_id] = {} # Ensure scope exists before adding symbol
             Logger.debug(f" Created dictionary for scope ID {scope_id} in SymbolTable.")


        if name not in self.symbols[scope_id]:
            self.symbols[scope_id][name] = {
                'type': symbol_type,
                'scope': scope_id, # Store the scope ID where the symbol was defined
                'metadata': metadata or {}
            }
            Logger.debug(f" Added symbol '{name}' ({symbol_type}) to scope {scope_id}")
        # else:
             # Logger.debug(f" Symbol '{name}' already exists in scope {scope_id}.")


    def get_symbols(self, current_scope_id: int) -> List[str]:
        """Get symbols accessible from the current scope, including parent scopes."""
        Logger.debug(f" SymbolTable: Getting symbols visible from scope {current_scope_id}")
        visible_symbols_names: set[str] = set()

        # A proper scope hierarchy lookup is needed here.
        # For this simplified version, let's just return symbols from the global scope (0)
        # and the current scope. This is not fully correct for nested scopes but works
        # for simple cases and avoids the KeyError.

        # Get symbols from global scope (ID 0)
        global_scope_symbols = self.symbols.get(0, {}).keys()
        visible_symbols_names.update(global_scope_symbols)
        Logger.debug(f"  Added {len(global_scope_symbols)} symbols from global scope (0).")

        # Get symbols from the current scope ID if it's not the global scope
        if current_scope_id != 0:
            current_scope_symbols = self.symbols.get(current_scope_id, {}).keys()
            visible_symbols_names.update(current_scope_symbols)
            Logger.debug(f"  Added {len(current_scope_symbols)} symbols from current scope ({current_scope_id}).")

        # TODO: Implement proper scope traversal for accurate symbol lookup based on the analyzer's scope stack.
        # This method might need access to the analyzer's scope stack or a parent scope mapping.

        sorted_symbols = sorted(list(visible_symbols_names))
        Logger.debug(f" SymbolTable: Returning {len(sorted_symbols)} visible symbols.")
        return sorted_symbols


# Initialize the global profile manager instance when the module is imported
# This ensures profiles are loaded when the module is first used.
Logger.info("Initializing LanguageProfileManager singleton...")
profile_manager = LanguageProfileManager()
Logger.info("LanguageProfileManager singleton initialized.")

# Example Usage Block (moved and updated to use LanguageProfileManager singleton)
if __name__ == '__main__':
    Logger.info("--- Language Profiles Example Usage ---")

    # Access the singleton profile manager
    manager = LanguageProfileManager()
    available_languages = manager.get_available_languages()
    Logger.info(f"Available languages: {available_languages}")

    # Create an analyzer for Python
    analyzer = CodeAnalyzer('python')

    code = '''
def factorial(n):
    """Calculate factorial recursively"""
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)

class MyClass:
    def __init__(self):
        self.value = 42 # A number
        self.text = "Hello" # A string

    def display(self):
        Logger.info(f"Value: {self.value}") # Original print, now should use Logger in a real app

# Global variable
global_var = 100

def another_func():
    local_var = 50
    Logger.info(global_var + local_var) # Original print

if True:
    block_var = "inside if"
    Logger.info(block_var) # Original print

'''

    # Analyze the code line by line, passing line number
    # enumerate provides line number starting from 0
    Logger.info("Starting code analysis...")
    # Use the new analyze_text method
    analyzer.analyze_text(code)


    # Get suggestions after analysis
    suggestions = analyzer.get_suggestions()
    Logger.info(f"Suggestions: {suggestions}") # Replaced print with Logger

    Logger.info("--- Example Usage End ---")