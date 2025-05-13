# showcases/showcase_dialogs.py 

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kivy.lang import Builder
from kivy.animation import Animation
from kivy.properties import BooleanProperty
from kivymd.app import MDApp
from kivy.metrics import dp
from ui.dialogs import InfoDialog, ErrorDialog, ConfirmDialog, WarningDialog
from datetime import datetime
from kivy.core.window import Window
from kivymd.uix.button import MDRaisedButton

KV = '''
<FadeLabel@MDLabel>:
    opacity: 0
    canvas.before:
        Color:
            rgba: (0, 0, 0, 0.1) if root.theme_cls.theme_style == "Light" else (1, 1, 1, 0.1)
        Rectangle:
            pos: self.pos
            size: self.size

MDScreen:
    canvas.before:
        Color:
            rgba: app.theme_cls.bg_normal
        Rectangle:
            size: self.size
            pos: self.pos

    MDBoxLayout:
        id: main_box
        orientation: "vertical"
        spacing: dp(20)
        padding: dp(20)
        opacity: 1

        MDTopAppBar:
            id: toolbar
            title: "Dialog Showcase"
            elevation: 4
            left_action_items: [["theme-light-dark", lambda x: app.toggle_theme()]]
            md_bg_color: app.theme_cls.primary_color

        ScrollView:
            id: scroll
            bar_width: dp(4)
            scroll_type: ['bars', 'content']
            effect_cls: "ScrollEffect"

            MDBoxLayout:
                id: content_box
                orientation: "vertical"
                spacing: dp(10)
                padding: dp(20)
                adaptive_height: True
                size_hint_y: None

                MDRaisedButton:
                    id: info_btn
                    text: "Show Info Dialog"
                    on_release: app.show_info_dialog()
                    size_hint_y: None
                    height: dp(48)
                    md_bg_color: app.theme_cls.primary_color

                MDRaisedButton:
                    id: error_btn
                    text: "Show Error Dialog"
                    on_release: app.show_error_dialog()
                    size_hint_y: None
                    height: dp(48)
                    md_bg_color: app.theme_cls.primary_color

                MDRaisedButton:
                    id: confirm_btn
                    text: "Show Confirm Dialog"
                    on_release: app.show_confirm_dialog()
                    size_hint_y: None
                    height: dp(48)
                    md_bg_color: app.theme_cls.primary_color

                MDRaisedButton:
                    id: warning_btn
                    text: "Show Warning Dialog"
                    on_release: app.show_warning_dialog()
                    size_hint_y: None
                    height: dp(48)
                    md_bg_color: app.theme_cls.accent_color

                BoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(48)
                    spacing: dp(10)
                    padding: dp(10)

                    MDLabel:
                        text: "Dark Theme"
                        halign: "left"
                        valign: "center"
                        size_hint_x: 0.7

                    MDSwitch:
                        id: theme_switch
                        active: False
                        on_active: app.toggle_theme(self.active)

                FadeLabel:
                    id: result_label
                    text: "Dialog results will appear here"
                    halign: "center"
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: dp(40)
'''

class DialogShowcaseApp(MDApp):
    theme_changing = BooleanProperty(False)

    def build(self):
        Window.clearcolor = self.theme_cls.bg_normal
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Orange"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.theme_style_switch_duration = 0.3
        return Builder.load_string(KV)

    def toggle_theme(self, active=None):
        if self.theme_changing:
            return

        self.theme_changing = True
        if active is None:
            active = not self.root.ids.theme_switch.active
        self.root.ids.theme_switch.active = active

        self._switch_theme(active)

    def _switch_theme(self, active):
        self.theme_cls.theme_style = "Dark" if active else "Light"
        Window.clearcolor = self.theme_cls.bg_normal
        self.theme_changing = False

        Animation.cancel_all(self.root.ids.result_label)
        anim = Animation(opacity=1, duration=0.5, t='out_quad')
        anim.start(self.root.ids.result_label)

    def show_info_dialog(self):
        dialog = InfoDialog(
            title="Information",
            text="This is an informational message.\nYou should read this carefully."
        )
        self._animate_button_press(self.root.ids.info_btn)
        dialog.open()

    def show_error_dialog(self):
        dialog = ErrorDialog(
            title="Operation Failed",
            text="The requested operation could not be completed.\nPlease try again later."
        )
        self._animate_button_press(self.root.ids.error_btn)
        dialog.open()

    def show_confirm_dialog(self):
        def on_confirm():
            self.root.ids.result_label.text = f"Confirmed at {datetime.now().strftime('%H:%M:%S')}"
            self._animate_result_label()

        def on_cancel():
            self.root.ids.result_label.text = "Action cancelled"
            self._animate_result_label()

        dialog = ConfirmDialog(
            title="Confirm Action",
            text="Are you sure you want to proceed?\nThis cannot be undone.",
            confirm_text="CONFIRM",
            cancel_text="CANCEL"
        )
        self._animate_button_press(self.root.ids.confirm_btn)
        dialog.open(
            confirm_callback=on_confirm,
            cancel_callback=on_cancel
        )

    def show_warning_dialog(self):
        dialog = WarningDialog(
            title="Heads Up!",
            text="This is a warning message. Proceed with caution."
        )
        self._animate_button_press(self.root.ids.warning_btn)
        dialog.open()  # Removed the extra parentheses

    def _animate_button_press(self, button):
        Animation.cancel_all(button)
        anim = Animation(
            opacity=0.7,
            duration=0.1
        ) + Animation(
            opacity=1,
            duration=0.7,
            t='out_quad'
        )
        anim.start(button)

    def _animate_result_label(self):
        label = self.root.ids.result_label
        Animation.cancel_all(label)
        anim = Animation(
            opacity=0,
            duration=0.2
        ) + Animation(
            opacity=1,
            duration=0.5,
            t='out_quad'
        )
        anim.start(label)

if __name__ == "__main__":
    DialogShowcaseApp().run()