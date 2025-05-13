# language_profiles.py (Modified)

from __future__ import annotations
import re
import json
import os
import difflib
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Pattern, TypedDict, Any, Tuple

from kivy.logger import Logger
from time import time

# --- Type Definitions ---
class LanguageDefinition(TypedDict):
    language: str
    comment: Optional[str]
    block_comment: List[Optional[str]]
    indent: str
    indent_triggers: List[str]
    dedent_triggers: List[str]
    definitions: Dict[str, Optional[str]]
    symbol_patterns: Dict[str, Optional[str]]
    syntax_tokens: Dict[str, str]
    suggestions_categorized: Dict[str, List[str]]

CompiledPatterns = Dict[str, Optional[Pattern]]
TriggerPatterns = List[Optional[Pattern]]

class LanguageProfile(TypedDict):
    language: str
    comment: Optional[str]
    block_comment: List[Optional[str]]
    indent: str
    indent_triggers: TriggerPatterns
    dedent_triggers: TriggerPatterns
    definitions: CompiledPatterns
    symbol_patterns: CompiledPatterns
    syntax_tokens: CompiledPatterns
    suggestions_categorized: Dict[str, List[str]]

class SymbolInfo(TypedDict):
    type: str
    scope: int
    line_num: int
    name: str
    metadata: Dict[str, Any]

# --- Constants ---
ASSETS_DIR = Path(__file__).parent.parent / "assets" / "language_profiles"

# --- Core Implementation ---
class LanguageProfileManager:
    _instance: Optional[LanguageProfileManager] = None
    _pattern_cache: Dict[str, Optional[Pattern]] = {}

    def __new__(cls) -> LanguageProfileManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._profiles: Dict[str, LanguageProfile] = {}
            cls._instance._load_profiles()
            Logger.info("LanguageProfileManager initialized and profiles loaded.")
        return cls._instance

    def _load_profiles(self) -> None:
        Logger.info(f"Attempting to load profiles from: {ASSETS_DIR}")
        if not ASSETS_DIR.exists():
            Logger.error(f"Language profiles directory not found: {ASSETS_DIR}")
            if 'generic' not in self._profiles:
                Logger.warning("No profiles loaded from assets. Creating dummy generic profile.")
                self._create_dummy_profiles()
            return

        loaded_count = 0
        for profile_file in sorted(ASSETS_DIR.glob("*.json")):
            try:
                Logger.debug(f"Attempting to load file: {profile_file}")
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data: Dict[str, Any] = json.load(f)

                if not self._validate_profile_data(profile_data):
                    Logger.warning(f"Skipping invalid profile: {profile_file.name}")
                    continue

                compiled_profile = self._compile_patterns(profile_data)
                self._profiles[compiled_profile['language']] = compiled_profile
                loaded_count += 1
                Logger.info(f"Loaded language profile: {compiled_profile['language']}")

            except json.JSONDecodeError as e:
                Logger.error(f"Invalid JSON in {profile_file.name}: {e}")
            except Exception as e:
                Logger.error(f"Error loading {profile_file.name}: {str(e)}")

        if 'generic' not in self._profiles:
            Logger.warning("'generic' profile not found after file loading - creating fallback.")
            self._create_generic_profile()


    def _validate_profile_data(self, profile_data: Dict[str, Any]) -> bool:
        required_keys = [
            'language', 'comment', 'block_comment', 'indent',
            'indent_triggers', 'dedent_triggers', 'definitions',
            'symbol_patterns', 'syntax_tokens', 'suggestions_categorized'
        ]
        if not all(key in profile_data for key in required_keys):
            return False

        if not isinstance(profile_data.get('language'), str) or not profile_data.get('language'):
             return False

        block_comment = profile_data.get('block_comment')
        if not isinstance(block_comment, list) or len(block_comment) != 2 or \
           not all(isinstance(x, (str, type(None))) for x in block_comment):
            return False

        indent_value = profile_data.get('indent')
        if not isinstance(indent_value, str) or not indent_value:
            return False

        for trigger_list_key in ['indent_triggers', 'dedent_triggers']:
            triggers = profile_data.get(trigger_list_key, [])
            if not isinstance(triggers, list) or not all(isinstance(x, (str, type(None))) for x in triggers):
                return False

        for pattern_dict_key in ['definitions', 'symbol_patterns', 'syntax_tokens']:
            pattern_dict = profile_data.get(pattern_dict_key, {})
            if not isinstance(pattern_dict, dict) or not all(isinstance(k, str) and isinstance(v, (str, type(None))) for k, v in pattern_dict.items()):
                return False

        suggestions_dict = profile_data.get('suggestions_categorized', {})
        if not isinstance(suggestions_dict, dict) or not all(isinstance(v, list) for v in suggestions_dict.values()):
            return False

        return True

    def _compile_patterns(self, profile_data: Dict[str, Any]) -> LanguageProfile:
        indent_string = profile_data.get('indent', '    ')
        return {
            'language': profile_data['language'],
            'comment': profile_data.get('comment'),
            'block_comment': profile_data.get('block_comment', [None, None]),
            'indent': indent_string,
            'indent_triggers': [self._safe_compile(p) for p in profile_data.get('indent_triggers', []) if isinstance(p, str)],
            'dedent_triggers': [self._safe_compile(p) for p in profile_data.get('dedent_triggers', []) if isinstance(p, str)],
            'definitions': {k: self._safe_compile(v) for k, v in profile_data.get('definitions', {}).items() if isinstance(k, str) and isinstance(v, str)},
            'symbol_patterns': {k: self._safe_compile(v) for k, v in profile_data.get('symbol_patterns', {}).items() if isinstance(k, str) and isinstance(v, str)},
            'syntax_tokens': {k: self._safe_compile(v) for k, v in profile_data.get('syntax_tokens', {}).items() if isinstance(k, str) and isinstance(v, str)},
            'suggestions_categorized': profile_data.get('suggestions_categorized', {})
        }

    def _safe_compile(self, pattern: Optional[str]) -> Optional[Pattern]:
        if pattern is None:
            return None
        if pattern in self._pattern_cache:
            return self._pattern_cache[pattern]

        try:
            compiled = re.compile(pattern, re.DOTALL)
            self._pattern_cache[pattern] = compiled
            return compiled
        except (re.error, TypeError) as e:
            Logger.debug(f"Pattern compilation failed: {pattern[:30]}... - {str(e)}")
            self._pattern_cache[pattern] = None
            return None

    def _create_dummy_profiles(self) -> None:
        """Creates minimal dummy profiles if assets directory is not found."""
        Logger.warning("Creating dummy generic profile as assets directory was not found.")

        generic_profile_data: LanguageDefinition = {
             'language': 'generic',
            'comment': '//',
            'block_comment': ['/*', '*/'],
            'indent': '    ',
            'indent_triggers': ['{'],
            'dedent_triggers': ['}'],
            'definitions': {},
            'symbol_patterns': {},
            'syntax_tokens': {
                "keyword": r'\b(if|else|for|while|return)\b',
                "operator": r'[+\-*/%&|^~<>!=]+',
                "comment": r'//.*',
                "string": r'"[^"]*"|\'[^\']*\''
            },
            'suggestions_categorized': {
                'keywords': ["if", "else", "for", "while", "return"]
            }
        }
        self._profiles['generic'] = self._compile_patterns(generic_profile_data)


    def _create_generic_profile(self) -> None:
        """Creates a minimal generic profile as a fallback if generic.json is missing."""
        Logger.warning("Creating fallback generic profile.")
        generic_syntax_tokens = {
            "keyword": r'\b(if|else|for|while|do|begin|end|function|procedure|return|break|continue|true|false|null)\b',
            "operator": r'[+\-*/%&|^~<>!=]+',
            "comment": r'#.*',
            "string": r'"[^"]*"|\'[^\']*\''
        }
        compiled_generic_syntax = {k: self._safe_compile(v) for k, v in generic_syntax_tokens.items()}

        self._profiles['generic'] = {
            'language': 'generic',
            'comment': '#',
            'block_comment': ['', ''],
            'indent': '    ',
            'indent_triggers': [],
            'dedent_triggers': [],
            'definitions': {},
            'symbol_patterns': {},
            'syntax_tokens': compiled_generic_syntax,
            'suggestions_categorized': {
                'keywords': [],
                'operators': [],
                'builtins': [],
                'exceptions': []
            }
        }


    def get_profile(self, language: str) -> LanguageProfile:
        """Retrieves the compiled profile for a language, or the generic profile as a fallback."""
        requested_language = language.lower()
        profile = self._profiles.get(requested_language)

        if profile:
            Logger.debug(f"Found profile for language: {requested_language}")
            return profile

        generic_profile = self._profiles.get('generic')
        if generic_profile:
            Logger.warning(f"Profile for '{language}' not found, using 'generic'.")
            return generic_profile

        Logger.critical("Generic language profile not found and no requested profile found! Returning a minimal fallback profile.")
        return {
            'language': 'minimal_fallback',
            'comment': '#',
            'block_comment': ['', ''],
            'indent': '    ',
            'indent_triggers': [],
            'dedent_triggers': [],
            'definitions': {},
            'symbol_patterns': {},
            'syntax_tokens': {},
            'suggestions_categorized': {}
        }


    def get_available_languages(self) -> List[str]:
        """Returns a sorted list of available language profile names."""
        return sorted(self._profiles.keys())


class SymbolTable:
    """Manages symbols and their scopes."""
    def __init__(self):
        self.symbols: Dict[int, Dict[str, SymbolInfo]] = defaultdict(dict)
        # self._symbol_by_name_and_scope: Dict[Tuple[str, int], SymbolInfo] = {}
        Logger.info("SymbolTable initialized.")

    def clear(self) -> None:
        """Clears all symbols from the table."""
        self.symbols.clear()
        # self._symbol_by_name_and_scope.clear()
        Logger.debug("SymbolTable cleared.")

    def enter_scope(self, scope_id: int) -> None:
        """Notifies the symbol table that a new scope is being entered."""
        if scope_id not in self.symbols:
            self.symbols[scope_id] = {}

    def exit_scope(self) -> None:
        """Notifies the symbol table that a scope is being exited."""
        pass

    def add_symbol(self, name: str, symbol_type: str,
                  scope_id: int, line_num: int,
                  metadata: Optional[Dict[str, Any]] = None) -> None:
        """Adds a symbol to the table."""
        if not metadata:
            metadata = {}

        symbol_key = name

        if scope_id not in self.symbols:
            self.symbols[scope_id] = {}

        existing_symbol = self.symbols[scope_id].get(symbol_key)
        if existing_symbol and existing_symbol['line_num'] == line_num:
            return

        self.symbols[scope_id][symbol_key] = {
            'name': name,
            'type': symbol_type,
            'scope': scope_id,
            'line_num': line_num,
            'metadata': metadata.copy()
        }
        # self._symbol_by_name_and_scope[(name, scope_id)] = self.symbols[scope_id][symbol_key]
        # Logger.debug(f"Added symbol: {name} ({symbol_type}) at scope {scope_id}, line {line_num}")


    def remove_symbols_in_range(self, start_line: int, end_line: int) -> None:
        """Removes symbols defined within a specific line range."""
        Logger.debug(f"SymbolTable: Attempting to remove symbols in line range [{start_line}, {end_line})")
        removed_count = 0
        for scope_id in list(self.symbols.keys()):
            symbols_in_scope = self.symbols[scope_id]
            for symbol_key in list(symbols_in_scope.keys()):
                symbol_info = symbols_in_scope[symbol_key]
                if start_line <= symbol_info.get('line_num', -1) < end_line:
                    del symbols_in_scope[symbol_key]
                    # if (symbol_info['name'], scope_id) in self._symbol_by_name_and_scope:
                    #     del self._symbol_by_name_and_scope[(symbol_info['name'], scope_id)]
                    removed_count += 1
                    Logger.debug(f"Removed symbol '{symbol_info.get('name', symbol_key)}' from scope {scope_id} (defined on line {symbol_info.get('line_num', -1)}).")
            if not symbols_in_scope:
                del self.symbols[scope_id]
                Logger.debug(f"Removed empty scope {scope_id}.")

        Logger.debug(f"SymbolTable: Finished removing {removed_count} symbols in range [{start_line}, {end_line}).")

    def get_symbols_in_scope(self, scope_id: int) -> Dict[str, SymbolInfo]:
        """Gets all symbols within a specific scope ID."""
        return self.symbols.get(scope_id, {})

    def get_visible_symbols(self, scope_stack: List[int]) -> List[SymbolInfo]:
        """Gets all symbols visible from the current scope stack."""
        visible_symbols: Dict[str, SymbolInfo] = {}
        for scope_id in reversed(scope_stack):
            if scope_id in self.symbols:
                for symbol_name, symbol_info in self.symbols[scope_id].items():
                    if symbol_name not in visible_symbols:
                        visible_symbols[symbol_name] = symbol_info

        return sorted(visible_symbols.values(), key=lambda x: x['name'])

    def get_all_symbols(self) -> List[SymbolInfo]:
        """Returns all symbols in the table, regardless of scope."""
        all_symbols: List[SymbolInfo] = []
        for scope_id in self.symbols:
            all_symbols.extend(self.symbols[scope_id].values())

        return sorted(all_symbols, key=lambda x: (x['line_num'], x['scope'], x['name']))


class CodeAnalyzer:
    """Analyzes code text based on a language profile to find syntax tokens and symbols."""
    def __init__(self, language: str = 'python'):
        self.language = language.lower()
        self.profile = LanguageProfileManager().get_profile(self.language)
        self.symbol_table = SymbolTable()

        self.current_scope: int = 0
        self.scope_stack: List[int] = [0]
        self.line_states: Dict[int, Dict[str, int]] = {-1: {'indent': 0, 'scope': 0}}

        self.current_function: Optional[Tuple[str, str, int]] = None
        self.current_class: Optional[Tuple[str, str, int]] = None

        self._current_text: Optional[str] = None
        self._current_syntax_token_ranges: List[Tuple[int, int, str]] = []
        self._current_line_hashes: Dict[int, str] = {}

        self._previous_text: Optional[str] = None
        self._prev_line_hashes: Dict[int, str] = {}
        self._prev_line_states: Dict[int, Dict[str, int]] = {}
        self._prev_symbol_table_state: Dict[int, Dict[str, SymbolInfo]] = {}
        self._prev_syntax_token_ranges: List[Tuple[int, int, str]] = []

        self._reset_state()
        Logger.info(f"CodeAnalyzer initialized for language: {self.language}")

    def _reset_state(self):
        """Resets the analyzer's internal state for a new analysis."""
        Logger.debug("CodeAnalyzer: Resetting current analysis state.")
        self.current_scope = 0
        self.scope_stack: List[int] = [0]
        self.line_states: Dict[int, Dict[str, int]] = {-1: {'indent': 0, 'scope': 0}}
        self.current_function = None
        self.current_class = None
        self.symbol_table.clear()
        self._current_syntax_token_ranges = []
        self._current_line_hashes = {}
        self._previous_text = None
        self._prev_line_hashes = {}
        self._prev_line_states = {}
        self._prev_symbol_table_state = {}
        self._prev_syntax_token_ranges = []
        Logger.debug("CodeAnalyzer: Current analysis state reset.")

    def analyze_text(self, text: str) -> None:
        """Performs full or incremental analysis of the provided text."""
        Logger.info(f"Starting analysis for: {self.language}")
        start_time = time()

        self._previous_text = self._current_text if hasattr(self, '_current_text') else None
        self._prev_line_hashes = self._current_line_hashes.copy()
        self._prev_line_states = self.line_states.copy()
        self._prev_symbol_table_state = {
             k: v.copy() for k, v in self.symbol_table.symbols.items()
         } if self.symbol_table.symbols else {}
        self._prev_syntax_token_ranges = self._current_syntax_token_ranges[:]

        self._current_text = text
        current_lines = text.split('\n')
        self._current_line_hashes = {i: self._hash_line(line) for i, line in enumerate(current_lines)}

        if self._previous_text is not None and self._should_attempt_incremental(current_lines, self._previous_text.split('\n')):
            Logger.info("Attempting incremental analysis...")
            self._setup_incremental_analysis()
            matcher = difflib.SequenceMatcher(None, self._previous_text.split('\n'), current_lines)
            self._process_diff_operations(matcher, current_lines)
        else:
            Logger.info("Performing full analysis...")
            self._full_analysis(text)

        self._finalize_analysis(start_time)

    def _hash_line(self, line: str) -> str:
        """Calculates the MD5 hash of a line."""
        return hashlib.md5(line.encode('utf-8')).hexdigest()

    def _should_attempt_incremental(self, current_lines: List[str], prev_lines: List[str]) -> bool:
        """Heuristic to decide if incremental analysis is worthwhile based on hashing and line count changes."""
        if not self._prev_line_hashes or not prev_lines:
             return False

        changed_lines_current = {i for i, line in enumerate(current_lines) if self._current_line_hashes.get(i) != self._prev_line_hashes.get(i)}
        changed_lines_prev = {i for i, line in enumerate(prev_lines) if self._prev_line_hashes.get(i) != self._current_line_hashes.get(i)}

        change_ratio_current = len(changed_lines_current) / (len(current_lines) or 1)
        change_ratio_prev = len(changed_lines_prev) / (len(prev_lines) or 1)
        length_change_ratio = abs(len(current_lines) - len(prev_lines)) / (len(prev_lines) or 1)

        if change_ratio_current > 0.4 or change_ratio_prev > 0.4 or length_change_ratio > 0.15:
             return False

        return True

    def _full_analysis(self, text: str) -> None:
        """Performs a full analysis of the entire text."""
        self._reset_state()
        offset = 0
        lines = text.split('\n')
        for i, line in enumerate(lines):
            self._analyze_line_scope(i, line)
            self._analyze_syntax_tokens(line, offset)
            self._analyze_constructs(i, line, self.line_states[i]['scope'])
            offset += len(line) + (1 if i < len(lines) - 1 else 0)

    def _setup_incremental_analysis(self) -> None:
         """Sets up the state for incremental analysis (simplified)."""
         self.line_states = self._prev_line_states.copy()
         self.symbol_table.clear()
         self.symbol_table.symbols = {
              k: v.copy() for k, v in self._prev_symbol_table_state.items()
         }
         self._current_syntax_token_ranges = []
         self.current_scope = 0
         self.scope_stack = [0]
         self.current_function = None
         self.current_class = None
         Logger.warning("Incremental analysis setup is simplified: symbols/scopes/syntax are largely re-calculated.")


    def _process_diff_operations(self, matcher: difflib.SequenceMatcher, current_lines: List[str]) -> None:
        """Processes diff operations to perform incremental analysis (simplified)."""
        current_offset = 0
        for i, line in enumerate(current_lines):
             self._analyze_line_scope(i, line)
             self._analyze_syntax_tokens(line, current_offset)
             self._analyze_constructs(i, line, self.line_states[i]['scope'])
             current_offset += len(line) + (1 if i < len(current_lines) - 1 else 0)


    def _finalize_analysis(self, start_time: float) -> None:
        """Fin alizes the analysis process and logs summary information."""
        if not self.scope_stack:
            self.scope_stack.append(0)
            self.current_scope = 0
        else:
             self.current_scope = self.scope_stack[-1]

        Logger.info(f"Analysis completed in {time() - start_time:.3f}s")
        Logger.info(
             f"Lines analyzed: {len(self.line_states) -1}, "
             f"Detected Symbols: {len(self.symbol_table.get_all_symbols())}, "
             f"Syntax Tokens: {len(self._current_syntax_token_ranges)}"
        )


    def _analyze_line_scope(self, line_num: int, line_text: str) -> None:
        """Determines the scope for a given line based on indentation and triggers."""
        prev_state = self.line_states.get(line_num - 1, {'indent': 0, 'scope': 0})
        current_indent = len(line_text) - len(line_text.lstrip())

        if not line_text.strip():
            self.line_states[line_num] = {
                'indent': current_indent,
                'scope': prev_state['scope']
            }
            return

        while self.scope_stack and current_indent < self.scope_stack[-1]:
             self.scope_stack.pop()

        if self.profile.get('indent_triggers'):
            if any(trigger.search(line_text) for trigger in self.profile['indent_triggers'] if trigger):
                 next_potential_indent = current_indent + len(self.profile.get('indent', '    '))
                 if next_potential_indent > current_indent:
                      if not self.scope_stack or next_potential_indent > self.scope_stack[-1]:
                          self.scope_stack.append(next_potential_indent)

        if self.profile.get('dedent_triggers'):
            if any(trigger.search(line_text) for trigger in self.profile['dedent_triggers'] if trigger):
                 while self.scope_stack and current_indent <= self.scope_stack[-1]:
                      self.scope_stack.pop()
                 if not self.scope_stack:
                      self.scope_stack.append(0)

        if current_indent > (self.scope_stack[-1] if self.scope_stack else 0):
             prev_indent = self.line_states.get(line_num - 1, {'indent': -1})['indent']
             if current_indent > prev_indent and current_indent > (self.scope_stack[-1] if self.scope_stack else 0):
                 self.scope_stack.append(current_indent)

        if not self.scope_stack:
             self.scope_stack.append(0)

        self.current_scope = self.scope_stack[-1]

        if self.current_function and self.current_scope < self.current_function[2]:
             self.current_function = None

        if self.current_class and self.current_scope < self.current_class[2]:
             self.current_class = None
             if self.current_function:
                  self.current_function = None

        self.line_states[line_num] = {
            'indent': current_indent,
            'scope': self.current_scope
        }


    def _analyze_syntax_tokens(self, line_text: str, offset: int) -> None:
        """Analyzes a line to find and store syntax token ranges."""
        if not self.profile.get('syntax_tokens'):
            return

        for token_type, pattern in self.profile['syntax_tokens'].items():
            if not pattern:
                continue

            try:
                 for match in pattern.finditer(line_text):
                    start, end = match.span()
                    self._current_syntax_token_ranges.append((
                        offset + start,
                        offset + end,
                        token_type
                    ))
            except Exception as e:
                Logger.error(f"Error processing syntax token pattern '{token_type}': {e} for line: {line_text[:50]}...")


    def _analyze_constructs(self, line_num: int, line_text: str, scope_id: int) -> None:
        """Analyzes a line for definitions and symbols."""
        stripped = line_text.lstrip()

        definition_patterns = self.profile.get('definitions', {})
        definition_order = ['class', 'interface', 'struct', 'enum', 'function', 'method', 'variable_assignment', 'lambda', 'arrow']

        for construct_type in definition_order:
             if construct_type in definition_patterns and definition_patterns[construct_type]:
                  pattern = definition_patterns[construct_type]
                  if (match := pattern.search(stripped)):
                      self._handle_definition(line_num, construct_type, match, scope_id)

        symbol_patterns = self.profile.get('symbol_patterns', {})
        symbol_order = ['param', 'variable', 'import']

        for symbol_type in symbol_order:
             if symbol_type in symbol_patterns and symbol_patterns[symbol_type]:
                  pattern = symbol_patterns[symbol_type]
                  if (match := pattern.search(stripped)):
                       symbol_name_candidate = None
                       if symbol_type == 'variable' and match.lastindex is not None and match.lastindex >= 1: symbol_name_candidate = match.group(1)
                       elif symbol_type == 'param' and match.lastindex is not None and match.lastindex >= 1: symbol_name_candidate = match.group(1)

                       if symbol_name_candidate and symbol_name_candidate in self.symbol_table.get_symbols_in_scope(scope_id):
                           continue

                       self._handle_symbol(line_num, symbol_type, match, scope_id)


    def _handle_definition(self, line_num: int, construct_type: str, match: re.Match, scope_id: int) -> None:
        """Handles the detection of a definition (function, class, etc.) and adds to symbol table."""
        symbol_name: Optional[str] = None
        parent_info: Dict[str, Any] = {}

        if self.current_function:
             parent_info['parent_name'] = self.current_function[0]
             parent_info['parent_type'] = self.current_function[1]
        elif self.current_class:
             parent_info['parent_name'] = self.current_class[0]
             parent_info['parent_type'] = self.current_class[1]

        if construct_type in ['function', 'method', 'class', 'interface', 'struct', 'enum']:
             if match.lastindex is not None and match.lastindex >= 1:
                 symbol_name = match.group(1)

        elif construct_type == 'variable_assignment':
             if match.lastindex is not None and match.lastindex >= 1:
                 symbol_name = match.group(1)
             if symbol_name and symbol_name.isdigit():
                 symbol_name = None

        if symbol_name:
             self.symbol_table.add_symbol(symbol_name, construct_type, scope_id, line_num, parent_info)

             if construct_type in ['function', 'method']:
                  self.current_function = (symbol_name, construct_type, scope_id)
                  self.current_class = None

             elif construct_type in ['class', 'interface', 'struct', 'enum']:
                  self.current_class = (symbol_name, construct_type, scope_id)
                  self.current_function = None

        if construct_type in ['function', 'method', 'lambda', 'arrow']:
             params_str = None
             if construct_type in ['function', 'method'] and match.lastindex is not None and match.lastindex >= 2:
                  params_str = match.group(2)
             elif construct_type == 'lambda' and match.lastindex is not None and match.lastindex >= 1:
                  if match.lastindex >= 2: params_str = match.group(2)
                  else: params_str = match.group(1)
             elif construct_type == 'arrow' and match.lastindex is not None and match.lastindex >= 1:
                   if match.lastindex >= 2: params_str = match.group(2)
                   else: params_str = match.group(1)

             if params_str:
                  param_scope_id = scope_id + len(self.profile.get('indent', '    '))
                  for param in self._parse_parameters(params_str):
                       if param:
                            param_metadata = parent_info.copy()
                            if symbol_name: param_metadata['defined_in'] = (symbol_name, construct_type)
                            self.symbol_table.add_symbol(param, 'param', param_scope_id, line_num, param_metadata)


    def _handle_symbol(self, line_num: int, symbol_type: str, match: re.Match, scope_id: int) -> None:
        """Handles the detection of other symbols (variables not in definition line, imports)."""
        symbol_name: Optional[str] = None
        parent_info: Dict[str, Any] = {}

        if self.current_function:
             parent_info['parent_name'] = self.current_function[0]
             parent_info['parent_type'] = self.current_function[1]
        elif self.current_class:
             parent_info['parent_name'] = self.current_class[0]
             parent_info['parent_type'] = self.current_class[1]

        if symbol_type == 'variable':
             if match.lastindex is not None and match.lastindex >= 1:
                 symbol_name = match.group(1)
             if symbol_name and symbol_name.isdigit():
                 symbol_name = None

        elif symbol_type == 'param':
             if match.lastindex is not None and match.lastindex >= 1:
                 symbol_name = match.group(1)

        elif symbol_type == 'import':
             if match.lastindex is not None:
                  imported_names = []
                  for i in range(1, match.lastindex + 1):
                       if (name := match.group(i)) and name.strip():
                            imported_names.extend([n.strip() for n in name.split(',') if n.strip()])

                  for imported_name in imported_names:
                       self.symbol_table.add_symbol(imported_name, 'import', scope_id, line_num, parent_info)
                  return

        if symbol_name:
             self.symbol_table.add_symbol(symbol_name, symbol_type, scope_id, line_num, parent_info)


    def get_suggestions(self, exclude_categories: Optional[List[str]] = None) -> List[str]:
        """
        Generates context-aware code completion suggestions.

        Args:
            exclude_categories: A list of suggestion categories (from the profile) to exclude.
        Returns:
             A sorted list of all relevant suggestions.
        """
        Logger.info("\n=== Generating Contextual Suggestions ===")
        suggestions: set[str] = set()

        excluded_categories_set = set(exclude_categories) if exclude_categories else set()

        if self.profile and self.profile.get('suggestions_categorized'):
            for category, category_list in self.profile['suggestions_categorized'].items():
                # Check if the category should be excluded
                if category not in excluded_categories_set:
                    if isinstance(category_list, list):
                        suggestions.update(category_list)
                else:
                    Logger.debug(f"Excluding suggestion category: {category}")

        visible_symbols_info = self.symbol_table.get_visible_symbols(self.scope_stack)
        suggestions.update([sym['name'] for sym in visible_symbols_info])

        sorted_suggestions = sorted(list(suggestions))

        # Removed slicing based on limit

        Logger.debug(f"Generated {len(sorted_suggestions)} raw suggestions.")
        return sorted_suggestions


    def get_syntax_token_ranges(self) -> List[Tuple[int, int, str]]:
        """Returns the detected syntax token ranges."""
        return self._current_syntax_token_ranges


    def get_detected_symbols(self) -> List[SymbolInfo]:
        """Returns all detected symbols with their details and parent information."""
        all_symbols = self.symbol_table.get_all_symbols()

        return sorted(all_symbols, key=lambda x: (x['line_num'], x['scope'], x['name']))


    def _calculate_offset_of_line(self, lines: List[str], line_num: int) -> int:
        """Calculates the character offset at the beginning of a given line."""
        if line_num < 0 or line_num >= len(lines):
            return 0
        return sum(len(lines[i]) + 1 for i in range(line_num))


    def _parse_parameters(self, params_str: str) -> List[str]:
        """Parses a string of parameters (e.g., 'self, make, model') into a list of names."""
        if not params_str:
            return []
        return [param.strip() for param in params_str.split(',') if param.strip()]


# --- Example Usage ---
if __name__ == '__main__':
    # Configure logging level for the example output
    Logger.setLevel('INFO')

    Logger.info("--- Language Profiles Example Usage ---")

    manager = LanguageProfileManager()
    available_languages = manager.get_available_languages()
    Logger.info(f"Available languages: {available_languages}")

    # Example using the Python profile
    analyzer = CodeAnalyzer('python')

    initial_code = '''
# This is a comment
class Vehicle:
    def __init__(self, make, model):
        self.make = make
        self.model = model

    def display(self):
        print(f"Vehicle: {self.make} {self.model}")

def calculate(x, y):
    result = x + y
    if result > 10:
        return result
    else:
        return 0

car = Vehicle("Toyota", "Camry")
value = calculate(5, 7)
f = lambda a : a + 1
'''

    Logger.info("Starting first code analysis...")
    analyzer.analyze_text(initial_code)
    Logger.info("First analysis complete.")

    # Get and print all suggestions, excluding 'operators'
    suggestions_first = analyzer.get_suggestions(exclude_categories=['operators'])
    Logger.info("\n=== All Contextual Suggestions (First Analysis - Operators Excluded) ===")
    for i, suggestion in enumerate(suggestions_first):
        Logger.info(f" {i+1}. {suggestion}")

    Logger.info("\n=== Key Syntax Tokens (First Analysis) ===")
    syntax_tokens_first = analyzer.get_syntax_token_ranges()
    lines_first = initial_code.split('\n')
    line_offsets_first = [0]
    for line in lines_first:
        line_offsets_first.append(line_offsets_first[-1] + len(line) + 1)

    token_info_for_display_first = []
    for start, end, token_type in syntax_tokens_first:
        line_num = -1
        for i in range(len(line_offsets_first) - 1):
            if line_offsets_first[i] <= start < line_offsets_first[i+1]:
                line_num = i
                break
        if line_num != -1:
             token_text = initial_code[start:end]
             token_info_for_display_first.append((line_num + 1, token_type, token_text, start, end))

    sorted_tokens_for_display_first = sorted(token_info_for_display_first, key=lambda x: (x[0], x[3]))

    display_types = [
        'keyword', 'string', 'number', 'comment', 'operator',
        'function', 'class', 'method', 'variable', 'param',
        'decorator', 'magic_method', 'attribute', 'type', 'regex', 'template',
        'lambda', 'arrow', 'import'
    ]

    for line_num, token_type, token_text, start, end in sorted_tokens_for_display_first:
         display_type = token_type
         if token_type in ['function', 'method'] and "__" in token_text:
              display_type = 'magic_method'

         if display_type in display_types:
             Logger.info(f" {display_type:<12} [line {line_num}]")


    Logger.info("\n=== Detected Symbols (First Analysis) ===")
    detected_symbols_first = analyzer.get_detected_symbols()
    for symbol in detected_symbols_first:
         parent_info_str = ""
         if 'parent_name' in symbol['metadata'] and 'parent_type' in symbol['metadata']:
              parent_info_str = f" (in {symbol['metadata']['parent_type']} '{symbol['metadata']['parent_name']}')"
         Logger.info(
              f" {symbol['name']:<10} {symbol['type']:<10} (line {symbol['line_num']}, scope {symbol['scope']}){parent_info_str}"
         )


    modified_code = initial_code.replace("return 1", "return 1 # Base case added")
    modified_code = modified_code.replace("result = x + y", "result = x + y # Simple sum")
    modified_code_lines = modified_code.splitlines()
    modified_code_lines.insert(12, "    # This is an inserted comment line")
    modified_code = "\n".join(modified_code_lines)

    Logger.info("\nStarting second code analysis (with modifications)...")
    analyzer.analyze_text(modified_code)
    Logger.info("Second analysis complete.")

    # Get and print all suggestions, excluding 'operators' and 'builtins'
    suggestions_second = analyzer.get_suggestions(exclude_categories=['operators', 'builtins'])
    Logger.info("\n=== All Contextual Suggestions (Second Analysis - Operators & Builtins Excluded) =====")
    for i, suggestion in enumerate(suggestions_second):
        Logger.info(f" {i+1}. {suggestion}")

    Logger.info("\n=== Key Syntax Tokens (Second Analysis) ===")
    syntax_tokens_second = analyzer.get_syntax_token_ranges()
    lines_second = modified_code.split('\n')
    line_offsets_second = [0]
    for line in lines_second:
        line_offsets_second.append(line_offsets_second[-1] + len(line) + 1)

    token_info_for_display_second = []
    for start, end, token_type in syntax_tokens_second:
        line_num = -1
        for i in range(len(line_offsets_second) - 1):
            if line_offsets_second[i] <= start < line_offsets_second[i+1]:
                line_num = i
                break
        if line_num != -1:
             token_text = modified_code[start:end]
             token_info_for_display_second.append((line_num + 1, token_type, token_text, start, end))

    sorted_tokens_for_display_second = sorted(token_info_for_display_second, key=lambda x: (x[0], x[3]))

    display_types = [
        'keyword', 'string', 'number', 'comment', 'operator',
        'function', 'class', 'method', 'variable', 'param',
        'decorator', 'magic_method', 'attribute', 'type', 'regex', 'template',
        'lambda', 'arrow', 'import'
    ]

    for line_num, token_type, token_text, start, end in sorted_tokens_for_display_second:
         display_type = token_type
         if token_type in ['function', 'method'] and "__" in token_text:
              display_type = 'magic_method'

         if display_type in display_types:
             Logger.info(f" {display_type:<12} [line {line_num}]")


    Logger.info("\n=== Detected Symbols (Second Analysis) ===")
    detected_symbols_second = analyzer.get_detected_symbols()
    for symbol in detected_symbols_second:
         parent_info_str = ""
         if 'parent_name' in symbol['metadata'] and 'parent_type' in symbol['metadata']:
              parent_info_str = f" (in {symbol['metadata']['parent_type']} '{symbol['metadata']['parent_name']}')"
         Logger.info(
              f" {symbol['name']:<10} {symbol['type']:<10} (line {symbol['line_num']}, scope {symbol['scope']}){parent_info_str}"
         )


    Logger.info("\n--- Example Usage End ---")