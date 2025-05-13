from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.animation import Animation
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivy.core.clipboard import Clipboard
from kivymd.toast import toast
from plyer import vibrator
from kivy.logger import Logger
from kivy.core.window import Window

class BaseDialog:
    """Dialog base with properly contained buttons"""
    
    def __init__(self, title="", text="", buttons=None, separator_color=None, content_widget=None, include_copy=False):
        self.title = title
        self.text = text
        self.buttons = buttons or []
        self.separator_color = separator_color or "#448AFF"
        self.dialog = None
        self.content_widget = content_widget
        self.include_copy = include_copy

    def _vibrate(self, duration=0.05):
        try:
            vibrator.vibrate(duration)
        except Exception as e:
            Logger.warning(f"Vibration failed: {str(e)}")

    def _copy_to_clipboard(self):
        Clipboard.copy(self.text)
        self._vibrate(0.02)
        toast("Copied to clipboard")
        
    def _create_separator(self):
        sep = Widget(
            size_hint_y=None,
            height=dp(1),
            opacity=0,
        )
        try:
            color = get_color_from_hex(self.separator_color)
        except ValueError:
            color = get_color_from_hex("#448AFF")

        with sep.canvas.before:
            Color(*color)
            sep.rect = Rectangle(pos=sep.pos, size=sep.size)

        sep.bind(
            pos=lambda s, _: setattr(s.rect, 'pos', s.pos),
            size=lambda s, _: setattr(s.rect, 'size', s.size)
        )

        Animation(opacity=1, duration=0.2).start(sep)
        return sep

    def _create_copy_button(self):
        return MDRectangleFlatButton(
            text="COPY",
            size_hint=(None, None),
            size=(dp(80), dp(36)),
            line_color=(0, 0, 0, 0.2),
            on_release=lambda x: self._copy_to_clipboard()
        )

    def _create_button_box(self):
        # Calculate total button widths
        button_widths = [dp(80) for _ in self.buttons]
        if self.include_copy:
            button_widths.insert(0, dp(80))  # Add COPY button width
            
        total_button_width = sum(button_widths)
        total_spacing = dp(12) * (len(button_widths) - 1)
        
        # Calculate available width (85% of window width minus padding)
        available_width = Window.width * 0.85 - dp(48)  # 24dp padding on each side
        
        # Ensure buttons fit and calculate padding
        if total_button_width + total_spacing > available_width:
            # Scale down button widths if needed
            scale_factor = available_width / (total_button_width + total_spacing)
            button_widths = [w * scale_factor for w in button_widths]
            total_button_width = sum(button_widths)
        
        button_box = BoxLayout(
            padding=[dp(24), 0, dp(24), dp(16)],
            spacing=dp(12),
            size_hint_y=None,
            height=dp(48))
        
        if self.include_copy:
            button_box.add_widget(self._create_copy_button())
            
        # Add flexible spacer between buttons
        button_box.add_widget(Widget())
        
        # Add action buttons with proper widths
        for btn, width in zip(self.buttons, button_widths[-len(self.buttons):]):
            btn.size_hint = (None, None)
            btn.size = (width, dp(36))
            button_box.add_widget(btn)
            
        return button_box

    def _create_content(self):
        content = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[dp(24), dp(16), dp(24), 0],
            size_hint_y=None
        )
        
        content.add_widget(self._create_separator())

        if self.content_widget:
            content.add_widget(self.content_widget)
        else:
            label = MDLabel(
                text=self.text,
                halign="center",
                valign="center",
                size_hint_y=None,
                font_style="Body1",
                theme_text_color="Primary",
                font_size='16sp',
                padding=(dp(8), dp(16)),
                markup=True
            )
            label.bind(texture_size=lambda lbl, size: setattr(lbl, 'height', size[1] + dp(16)))
            content.add_widget(label)

        content.add_widget(self._create_button_box())
        content.bind(minimum_height=content.setter('height'))
        return content

    def open(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title=f"[b]{self.title}[/b]",
                type="custom",
                content_cls=self._create_content(),
                buttons=[],
                size_hint=(0.85, None),
                elevation=8,
                radius=[dp(12)]*4,
                auto_dismiss=False
            )
            
            content = self.dialog.content_cls
            content.opacity = 0
            Animation(opacity=1, duration=0.25, t='out_quad').start(content)
            self._vibrate(0.04)
            self.dialog.open()
        return self

    def dismiss(self):
        if self.dialog and self.dialog.content_cls:
            self._vibrate(0.02)
            anim = Animation(opacity=0, duration=0.18, t='out_quad')
            anim.bind(on_complete=lambda *x: self._final_dismiss())
            anim.start(self.dialog.content_cls)

    def _final_dismiss(self):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None


class InfoDialog(BaseDialog):
    def __init__(self, title="Info", text="", content_widget=None):
        buttons = [MDFlatButton(
            text="OK",
            theme_text_color="Custom",
            text_color=get_color_from_hex("#448AFF"),
            on_release=lambda x: self.dismiss()
        )]
        super().__init__(title, text, buttons, "#448AFF", content_widget, include_copy=False)


class ErrorDialog(BaseDialog):
    def __init__(self, title="Error", text="", content_widget=None):
        buttons = [MDFlatButton(
            text="CLOSE",
            theme_text_color="Custom",
            text_color=get_color_from_hex("#FF5252"),
            on_release=lambda x: self.dismiss()
        )]
        super().__init__(title, text, buttons, "#FF5252", content_widget, include_copy=True)


class ConfirmDialog(BaseDialog):
    def __init__(self, title="Confirm", text="", confirm_text="OK", cancel_text="CANCEL", content_widget=None):
        self._confirm_callback = None
        self._cancel_callback = None

        buttons = [
            MDFlatButton(
                text=cancel_text,
                theme_text_color="Custom",
                text_color=get_color_from_hex("#757575"),
                on_release=lambda x: self._handle_cancel()
            ),
            MDFlatButton(
                text=confirm_text,
                theme_text_color="Custom",
                text_color=get_color_from_hex("#4CAF50"),
                on_release=lambda x: self._handle_confirm()
            )
        ]
        super().__init__(title, text, buttons, "#4CAF50", content_widget, include_copy=False)

    def open(self, confirm_callback=None, cancel_callback=None):
        self._confirm_callback = confirm_callback
        self._cancel_callback = cancel_callback
        return super().open()

    def _handle_confirm(self):
        self._vibrate(0.08)
        if self._confirm_callback:
            self._confirm_callback()
        self.dismiss()

    def _handle_cancel(self):
        if self._cancel_callback:
            self._cancel_callback()
        self.dismiss()


class WarningDialog(BaseDialog):
    def __init__(self, title="Warning", text="", content_widget=None):
        buttons = [MDFlatButton(
            text="GOT IT",
            theme_text_color="Custom",
            text_color=get_color_from_hex("#FFC107"),
            on_release=lambda x: self.dismiss()
        )]
        super().__init__(title, text, buttons, "#FFC107", content_widget, include_copy=True)