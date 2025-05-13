# ui/tabs.py
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import (
    NumericProperty, 
    BooleanProperty,
    StringProperty,
    ColorProperty,
    ObjectProperty,
    DictProperty
)
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
import os
from weakref import ref
from typing import Optional, Any, Callable

class TabHeader(BoxLayout):
    """
    Widget representing a single tab header in the scrollable list.
    """
    tab_id = NumericProperty(-1)
    is_active = BooleanProperty(False)
    file_path = StringProperty(None, allownone=True)
    modified = BooleanProperty(False)

    active_bg = ColorProperty((0.3, 0.4, 0.5, 1))
    inactive_bg = ColorProperty((0.2, 0.2, 0.25, 1))
    active_text = ColorProperty((1, 1, 1, 1))
    inactive_text = ColorProperty((0.8, 0.8, 0.8, 1))

    on_close = ObjectProperty(None, allownone=True)
    on_select = ObjectProperty(None, allownone=True)

    def __init__(self, tab_id: int, parent: Optional[Any] = None, file_path: Optional[str] = None, modified: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = dp(0)
        self.padding = [dp(10), dp(5)]
        self.size_hint_x = None
        self.bind(minimum_width=self.setter('width'))

        self.tab_id = tab_id
        self.file_path = file_path
        self.modified = modified
        self._parent_ref = ref(parent) if parent else None

        self._tab_label = Label(
            text=self._get_display_text(),
            size_hint_x=None,
            halign='left',
            valign='middle',
            color=self.inactive_text,
            font_size=sp(14),
            text_size=(None, None))
        self._tab_label.bind(texture_size=lambda instance, size: setattr(instance, 'width', size[0]))
        self.add_widget(self._tab_label)

        with self.canvas.before:
            self.bg_color_instruction = Color(*self.inactive_bg)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas,
            file_path=self._update_display_text,
            modified=self._update_display_text,
            is_active=self._update_visual_state
        )

    def _update_canvas(self, instance, value):
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = instance.pos
            self.bg_rect.size = instance.size

    def _get_display_text(self) -> str:
        name = os.path.basename(str(self.file_path)) if self.file_path else f"Untitled {self.tab_id}"
        return f"{name}{' *' if self.modified else ''}"

    def _update_display_text(self, instance, value):
        if hasattr(self, '_tab_label'):
            self._tab_label.text = self._get_display_text()

    def _update_visual_state(self, instance, value):
        if hasattr(self, 'bg_color_instruction') and hasattr(self, '_tab_label'):
            if self.is_active:
                self.bg_color_instruction.rgba = self.active_bg
                self._tab_label.color = self.active_text
            else:
                self.bg_color_instruction.rgba = self.inactive_bg
                self._tab_label.color = self.inactive_text

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current == self and self.collide_point(*touch.pos):
            touch.ungrab(self)
            if self.on_select:
                self.on_select(self.tab_id)
            return True
        return super().on_touch_up(touch)

    def cleanup(self):
        """Clean up resources when tab is removed"""
        if hasattr(self, '_tab_label'):
            if self._tab_label.parent:
                self._tab_label.parent.remove_widget(self._tab_label)
            self._tab_label = None

        if hasattr(self, 'bg_color_instruction') and self.canvas.before:
            self.canvas.before.remove(self.bg_color_instruction)
        if hasattr(self, 'bg_rect') and self.canvas.before:
            self.canvas.before.remove(self.bg_rect)

        self.unbind(
            pos=self._update_canvas,
            size=self._update_canvas,
            file_path=self._update_display_text,
            modified=self._update_display_text,
            is_active=self._update_visual_state
        )

class TabManager(BoxLayout):
    current_tab_id = NumericProperty(-1)
    tabs = DictProperty({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(2)
        self.next_tab_id = 1
        
        # Header Scroll View
        self.headers_scroll = ScrollView(
            size_hint=(1, None),
            height=dp(40),
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=dp(4),
            scroll_type=['bars', 'content']
        )
        
        self.headers_container = BoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            spacing=dp(2),
            padding=dp(2)
        )
        self.headers_container.bind(minimum_width=self.headers_container.setter('width'))
        self.headers_scroll.add_widget(self.headers_container)
        self.add_widget(self.headers_scroll)

        # Content Area
        self.content_area = BoxLayout(size_hint=(1, 1))
        self.add_widget(self.content_area)

    def add_tab(self, file_path=None, content=None):
        tab_id = self.next_tab_id
        self.next_tab_id += 1
        
        header = TabHeader(
            tab_id=tab_id,
            parent=self.headers_container,
            file_path=file_path
        )
        header.on_select = lambda tab_id=tab_id: self.switch_tab(tab_id)
        
        content = content if content else Label(text=f"Tab {tab_id} Content")
        
        self.tabs[tab_id] = {
            'header': header,
            'content': content,
            'file_path': file_path,
            'modified': False
        }
        
        self.headers_container.add_widget(header)
        self.switch_tab(tab_id)
        return tab_id

    def remove_tab(self, tab_id):
        if tab_id in self.tabs:
            self.headers_container.remove_widget(self.tabs[tab_id]['header'])
            if self.tabs[tab_id]['content'].parent:
                self.content_area.remove_widget(self.tabs[tab_id]['content'])
            
            self.tabs[tab_id]['header'].cleanup()
            del self.tabs[tab_id]
            
            if self.tabs:
                self.switch_tab(next(iter(self.tabs.keys())))
            else:
                self.current_tab_id = -1

    def switch_tab(self, tab_id):
        if self.current_tab_id == tab_id:
            return
        
        if self.current_tab_id in self.tabs:
            self.content_area.remove_widget(self.tabs[self.current_tab_id]['content'])
            self.tabs[self.current_tab_id]['header'].is_active = False
        
        self.content_area.add_widget(self.tabs[tab_id]['content'])
        self.tabs[tab_id]['header'].is_active = True
        self.current_tab_id = tab_id

        # Scroll to make the tab header visible
        header = self.tabs[tab_id]['header']
        self.headers_scroll.scroll_to(header)