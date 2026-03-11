"""
Main Screen - UI Logic for MC Mod Converter
"""

import os
import threading
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform
from kivy.properties import StringProperty, BooleanProperty, ListProperty

from utils.converter import ModConverter
from utils.file_picker import pick_file

Builder.load_string("""
#:import MDBoxLayout kivymd.uix.boxlayout.MDBoxLayout
#:import MDCard kivymd.uix.card.MDCard
#:import MDLabel kivymd.uix.label.MDLabel
#:import MDRaisedButton kivymd.uix.button.MDRaisedButton
#:import MDFlatButton kivymd.uix.button.MDFlatButton
#:import MDProgressBar kivymd.uix.progressbar.MDProgressBar
#:import MDIcon kivymd.uix.label.MDIcon
#:import dp kivy.metrics.dp
#:import get_color_from_hex kivy.utils.get_color_from_hex

<StatusItem@MDBoxLayout>:
    text: ""
    icon: "information"
    icon_color: 0.2, 0.8, 0.2, 1
    size_hint_y: None
    height: dp(32)
    spacing: dp(8)
    padding: dp(4), 0
    MDIcon:
        icon: root.icon
        theme_text_color: "Custom"
        text_color: root.icon_color
        size_hint_x: None
        width: dp(24)
        font_size: dp(16)
    MDLabel:
        text: root.text
        font_style: "Caption"
        theme_text_color: "Custom"
        text_color: 0.85, 0.85, 0.85, 1

<MainScreen>:
    canvas.before:
        Color:
            rgba: 0.08, 0.08, 0.12, 1
        Rectangle:
            pos: self.pos
            size: self.size

    ScrollView:
        do_scroll_x: False

        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            padding: dp(16)
            spacing: dp(12)

            # ── Header ──
            MDCard:
                size_hint_y: None
                height: dp(90)
                md_bg_color: 0.05, 0.55, 0.15, 1
                radius: [dp(16)]
                padding: dp(16)
                MDBoxLayout:
                    orientation: "vertical"
                    MDBoxLayout:
                        spacing: dp(10)
                        MDIcon:
                            icon: "minecraft"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                            size_hint_x: None
                            width: dp(36)
                            font_size: dp(32)
                        MDLabel:
                            text: "MC Mod Converter"
                            font_style: "H6"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                            bold: True
                    MDLabel:
                        text: "Convert & Install Bedrock Mods Instantly"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.85, 1, 0.85, 1

            # ── File Picker Card ──
            MDCard:
                size_hint_y: None
                height: dp(130)
                md_bg_color: 0.13, 0.13, 0.18, 1
                radius: [dp(12)]
                padding: dp(16)
                MDBoxLayout:
                    orientation: "vertical"
                    spacing: dp(8)
                    MDLabel:
                        text: "📁  Select Mod File or Folder"
                        font_style: "Subtitle1"
                        theme_text_color: "Custom"
                        text_color: 0.9, 0.9, 0.9, 1
                        bold: True
                    MDLabel:
                        id: selected_label
                        text: root.selected_file_label
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.6, 0.6, 0.6, 1
                        shorten: True
                        shorten_from: "left"
                    MDRaisedButton:
                        text: "Browse File (.zip / folder)"
                        md_bg_color: 0.15, 0.5, 0.8, 1
                        size_hint_x: 1
                        on_release: root.browse_file()

            # ── Options Card ──
            MDCard:
                size_hint_y: None
                height: dp(110)
                md_bg_color: 0.13, 0.13, 0.18, 1
                radius: [dp(12)]
                padding: dp(16)
                MDBoxLayout:
                    orientation: "vertical"
                    spacing: dp(6)
                    MDLabel:
                        text: "⚙️  Output Format"
                        font_style: "Subtitle1"
                        theme_text_color: "Custom"
                        text_color: 0.9, 0.9, 0.9, 1
                        bold: True
                    MDBoxLayout:
                        spacing: dp(10)
                        MDRaisedButton:
                            id: btn_mcaddon
                            text: ".mcaddon"
                            md_bg_color: 0.1, 0.65, 0.3, 1
                            size_hint_x: 1
                            on_release: root.set_format("mcaddon")
                        MDRaisedButton:
                            id: btn_mcpack
                            text: ".mcpack"
                            md_bg_color: 0.2, 0.2, 0.3, 1
                            size_hint_x: 1
                            on_release: root.set_format("mcpack")

            # ── Convert Button ──
            MDRaisedButton:
                text: "🔄  Convert Mod"
                md_bg_color: 0.1, 0.65, 0.3, 1
                size_hint_x: 1
                size_hint_y: None
                height: dp(52)
                font_size: "16sp"
                on_release: root.start_conversion()
                disabled: root.is_converting

            # ── Progress Bar ──
            MDProgressBar:
                id: progress_bar
                value: root.progress_value
                color: 0.1, 0.8, 0.3, 1
                size_hint_y: None
                height: dp(8)

            # ── Status Log Card ──
            MDCard:
                size_hint_y: None
                height: dp(220)
                md_bg_color: 0.06, 0.06, 0.10, 1
                radius: [dp(12)]
                padding: dp(12)
                MDBoxLayout:
                    orientation: "vertical"
                    spacing: dp(4)
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(30)
                        MDLabel:
                            text: "📋  Status Log"
                            font_style: "Subtitle2"
                            theme_text_color: "Custom"
                            text_color: 0.7, 0.7, 0.7, 1
                            bold: True
                        MDFlatButton:
                            text: "Clear"
                            theme_text_color: "Custom"
                            text_color: 0.5, 0.5, 0.5, 1
                            size_hint_x: None
                            width: dp(60)
                            on_release: root.clear_log()
                    ScrollView:
                        id: log_scroll
                        MDBoxLayout:
                            id: log_box
                            orientation: "vertical"
                            size_hint_y: None
                            height: self.minimum_height
                            spacing: dp(2)

            # ── Install Button ──
            MDRaisedButton:
                id: install_btn
                text: "🚀  Install in Minecraft"
                md_bg_color: 0.85, 0.4, 0.05, 1
                size_hint_x: 1
                size_hint_y: None
                height: dp(56)
                font_size: "17sp"
                disabled: not root.ready_to_install
                on_release: root.install_mod()

            # ── Footer ──
            MDLabel:
                text: "Supports Android 11–14 Scoped Storage"
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.4, 0.4, 0.4, 1
                halign: "center"
                size_hint_y: None
                height: dp(24)
""")


class MainScreen(Screen):
    selected_file_label = StringProperty("No file selected")
    is_converting = BooleanProperty(False)
    ready_to_install = BooleanProperty(False)
    progress_value = StringProperty("0")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_path = None
        self.output_path = None
        self.output_format = "mcaddon"
        self.converter = ModConverter(status_callback=self.add_log)

    # ─────────────── File Picking ───────────────

    def browse_file(self):
        self.add_log("Opening file picker...", "folder-open", (0.4, 0.7, 1, 1))
        if platform == "android":
            pick_file(self._on_file_selected)
        else:
            # Desktop fallback – use tkinter file dialog
            self._desktop_file_pick()

    def _desktop_file_pick(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            path = filedialog.askopenfilename(
                filetypes=[("ZIP / MCAddon", "*.zip *.mcaddon *.mcpack"), ("All", "*")]
            )
            root.destroy()
            if path:
                self._on_file_selected(path)
        except Exception as e:
            self.add_log(f"File picker error: {e}", "alert", (1, 0.3, 0.3, 1))

    def _on_file_selected(self, path):
        if path:
            self.selected_path = path
            name = os.path.basename(path)
            self.selected_file_label = f"✅  {name}"
            self.add_log(f"Selected: {name}", "check-circle", (0.2, 0.9, 0.4, 1))
            self.ready_to_install = False
            self.output_path = None

    # ─────────────── Format Selection ───────────────

    def set_format(self, fmt):
        self.output_format = fmt
        self.add_log(f"Output format set to: .{fmt}", "cog", (0.6, 0.6, 1, 1))

    # ─────────────── Conversion ───────────────

    def start_conversion(self):
        if not self.selected_path:
            self.add_log("⚠️  Please select a file first!", "alert-circle", (1, 0.8, 0, 1))
            return
        self.is_converting = True
        self.ready_to_install = False
        self.progress_value = "10"
        thread = threading.Thread(target=self._run_conversion, daemon=True)
        thread.start()

    def _run_conversion(self):
        try:
            Clock.schedule_once(lambda dt: setattr(self, "progress_value", "30"), 0)
            output = self.converter.convert(
                source_path=self.selected_path,
                output_format=self.output_format,
            )
            Clock.schedule_once(lambda dt: setattr(self, "progress_value", "90"), 0)

            def _done(dt):
                if output:
                    self.output_path = output
                    self.ready_to_install = True
                    self.progress_value = "100"
                    self.add_log("✅  Ready to Install!", "check-decagram", (0.1, 1, 0.4, 1))
                else:
                    self.progress_value = "0"
                    self.add_log("❌  Conversion failed.", "close-circle", (1, 0.3, 0.3, 1))
                self.is_converting = False

            Clock.schedule_once(_done, 0)
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self.add_log(f"Error: {e}", "alert", (1, 0.3, 0.3, 1)), 0
            )
            Clock.schedule_once(lambda dt: setattr(self, "is_converting", False), 0)

    # ─────────────── Install ───────────────

    def install_mod(self):
        if not self.output_path or not os.path.exists(self.output_path):
            self.add_log("No converted file to install.", "alert", (1, 0.6, 0, 1))
            return

        self.add_log("Launching Minecraft import...", "minecraft", (0.2, 0.8, 1, 1))

        if platform == "android":
            self._android_open_file(self.output_path)
        else:
            self.add_log(
                f"Desktop: Open this file manually:\n{self.output_path}",
                "folder",
                (0.7, 0.7, 0.7, 1),
            )

    def _android_open_file(self, filepath):
        try:
            from jnius import autoclass
            from android import mActivity

            File = autoclass("java.io.File")
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            FileProvider = autoclass("androidx.core.content.FileProvider")
            Build = autoclass("android.os.Build")

            file_obj = File(filepath)
            intent = Intent(Intent.ACTION_VIEW)

            # Android 7+ requires FileProvider
            if Build.VERSION.SDK_INT >= 24:
                pkg = mActivity.getPackageName()
                authority = f"{pkg}.fileprovider"
                uri = FileProvider.getUriForFile(mActivity, authority, file_obj)
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            else:
                uri = Uri.fromFile(file_obj)

            # Try Minecraft MIME, fall back to octet-stream
            intent.setDataAndType(uri, "application/octet-stream")
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            mActivity.startActivity(intent)
            self.add_log("Minecraft opened! Accept the import prompt.", "check", (0.2, 1, 0.5, 1))

        except Exception as e:
            self.add_log(f"Install error: {e}", "alert-circle", (1, 0.3, 0.3, 1))

    # ─────────────── Log Helpers ───────────────

    def add_log(self, message, icon="information", color=(0.2, 0.8, 0.2, 1)):
        def _add(dt):
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.label import Label
            from kivy.metrics import dp
            from kivymd.uix.label import MDIcon

            row = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(28),
                spacing=dp(6),
                padding=(dp(2), 0),
            )
            ic = MDIcon(
                icon=icon,
                theme_text_color="Custom",
                text_color=color,
                size_hint_x=None,
                width=dp(22),
                font_size=dp(14),
            )
            lbl = Label(
                text=message,
                font_size="12sp",
                color=(0.85, 0.85, 0.85, 1),
                text_size=(None, None),
                halign="left",
                valign="middle",
            )
            row.add_widget(ic)
            row.add_widget(lbl)
            self.ids.log_box.add_widget(row)
            # Auto-scroll to bottom
            Clock.schedule_once(
                lambda dt: setattr(self.ids.log_scroll, "scroll_y", 0), 0.1
            )

        Clock.schedule_once(_add, 0)

    def clear_log(self):
        self.ids.log_box.clear_widgets()
        self.progress_value = "0"
        self.ready_to_install = False
        self.output_path = None
