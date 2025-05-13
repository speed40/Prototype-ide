"""
showcase_themes.py - Theme showcase with proper syntax highlighting
"""

import os
import sys
import re
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import StringProperty, ColorProperty
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock

from core.themes import ThemeManager

KV = '''
<CodeCard>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: dp(8)
    radius: [dp(12)]
    elevation: 4
    md_bg_color: app.card_bg_color

    MDLabel:
        text: root.card_title
        font_style: "H6"
        halign: "center"
        theme_text_color: "Custom"
        text_color: app.theme_cls.primary_color
        size_hint_y: None
        height: dp(48)

    ScrollView:
        size_hint_y: 1
        bar_width: dp(4)
        bar_color: app.theme_cls.primary_light

        SyntaxHighlightLabel:
            id: code_label
            text: root.code_text
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.width, None
            padding: dp(10), dp(10)
            halign: 'left'
            valign: 'top'

<SyntaxHighlightLabel>:
    font_name: "RobotoMono-Regular"
    font_size: sp(14)
    line_height: 1.2
    markup: True
    theme_text_color: "Custom"
    text_color: app.text_color

MDScreen:
    md_bg_color: app.bg_color

    MDTopAppBar:
        id: toolbar
        title: "Theme Showcase"
        pos_hint: {"top": 1}
        elevation: 4
        left_action_items: [["menu", lambda x: None]]
        md_bg_color: app.theme_cls.primary_color

    MDBoxLayout:
        orientation: "vertical"
        padding: dp(20)
        spacing: dp(20)

        CodeCard:
            id: code_card
            card_title: "Python Code Example"
            size_hint_y: 0.7
            size_hint_x: 1
            padding: dp(10)

        MDGridLayout:
            id: theme_grid
            cols: 3
            adaptive_height: True
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(10)
            padding: dp(10)
'''

class SyntaxHighlightLabel(MDLabel):
    pass

class CodeCard(MDCard):
    card_title = StringProperty()
    code_text = StringProperty()

class ThemeShowcaseApp(MDApp):
    text_color = ColorProperty()
    bg_color = ColorProperty()
    card_bg_color = ColorProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_manager = ThemeManager()
        self.current_code = '''def factorial(n):
    """Calculate factorial recursively"""
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)

class MyClass:
    def __init__(self):
        self.value = 42  # This is a number
        self.text = "Hello"  # This is a string

    def display(self):
        print(f"Value: {self.value}")'''
        
        # Default colors before theme loads
        self.text_color = get_color_from_hex("#EEEEEE")
        self.bg_color = get_color_from_hex("#121212")
        self.card_bg_color = get_color_from_hex("#1E1E1E")

    def build(self):
        self.theme_cls.primary_palette = "Purple"
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)

    def on_start(self):
        # Load themes and initialize UI
        self.theme_manager.load_themes()
        self.load_theme_buttons()
        self.update_code_display()

    def load_theme_buttons(self):
        """Populate theme selection buttons"""
        grid = self.root.ids.theme_grid
        grid.clear_widgets()
        
        for theme_name in self.theme_manager.get_theme_names():
            btn = MDRaisedButton(
                text=theme_name.replace("_", " ").title(),
                on_release=lambda x, name=theme_name: self.apply_theme(name),
                size_hint_x=None,
                width=dp(120)
            )
            grid.add_widget(btn)

    def apply_theme(self, theme_name):
        """Apply selected theme and update UI"""
        if not self.theme_manager.apply_theme(theme_name):
            return
            
        theme = self.theme_manager.get_current_theme()
        if not theme:
            return
            
        # Update KivyMD theme
        self.theme_cls.primary_palette = theme['primary_palette']
        self.theme_cls.theme_style = theme['theme_style']
        
        # Update syntax colors
        syntax = theme['syntax']
        self.bg_color = get_color_from_hex(syntax['background'])
        self.card_bg_color = self.bg_color
        self.text_color = get_color_from_hex(syntax['text']['color'])
        
        self.update_code_display()

    def update_code_display(self):
        """Apply syntax highlighting to the code display"""
        theme = self.theme_manager.get_current_theme()
        if not theme:
            return
            
        syntax = theme['syntax']
        colors = {
            'keyword': syntax['keyword']['color'],
            'string': syntax['string']['color'],
            'number': syntax['number']['color'],
            'comment': syntax['comment']['color'],
            'builtin': syntax['builtin']['color'],
            'function': syntax['definition']['color'],
            'class': syntax['definition']['color']
        }

        highlighted = self.highlight_code(self.current_code, colors)
        self.root.ids.code_card.code_text = highlighted

    def highlight_code(self, code, colors):
        """Properly formatted syntax highlighting"""
        rules = [
            # Comments (single-line first)
            (r'(#[^\n]*)', 'comment'),
            
            # Strings (triple-quoted first)
            (r'(\"{3}[\s\S]*?\"{3}|\'{3}[\s\S]*?\'{3})', 'string'),
            (r'(\"[^\n\"\\]*(?:\\.[^\n\"\\]*)*\"|\'[^\n\'\\]*(?:\\.[^\n\'\\]*)*\')', 'string'),
            
            # Numbers
            (r'\b(\d+\.?\d*)\b', 'number'),
            
            # Keywords and special values
            (r'\b(self|True|False|None)\b', 'builtin'),
            
            # Definitions (functions/classes)
            (r'\b(def)\s+(\w+)', 'keyword', 'function'),
            (r'\b(class)\s+(\w+)', 'keyword', 'class'),
            
            # Other keywords
            (r'\b(if|else|elif|return|print|for|while|import|from|as|try|except|finally|with|async|await|lambda)\b', 'keyword')
        ]

        def process_line(line):
            # Convert tabs to spaces
            line = line.replace('\t', '    ')
            
            for rule in rules:
                if len(rule) == 2:
                    pattern, color = rule
                    line = re.sub(
                        pattern,
                        lambda m: f'[color={colors[color]}]{m.group(0)}[/color]',
                        line
                    )
                elif len(rule) == 3:
                    pattern, color1, color2 = rule
                    line = re.sub(
                        pattern,
                        lambda m: (
                            f'[color={colors[color1]}]{m.group(1)}[/color] '
                            f'[color={colors[color2]}]{m.group(2)}[/color]'
                        ),
                        line
                    )
            return line

        # Process each line individually
        lines = code.split('\n')
        highlighted_lines = [process_line(line) for line in lines]
        
        # Rejoin with proper newlines
        return '\n'.join(highlighted_lines)

if __name__ == "__main__":
    ThemeShowcaseApp().run()