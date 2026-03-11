"""
Minecraft Bedrock Mod Auto-Converter & Installer
Main Application Entry Point
"""

import os
import sys

# Force Android storage permission requests early
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock

from ui.main_screen import MainScreen

# Set window size for desktop testing
if platform != "android":
    Window.size = (400, 720)

KV = """
#:import get_color_from_hex kivy.utils.get_color_from_hex

ScreenManager:
    MainScreen:
        name: "main"
"""


class MCModConverterApp(App):
    title = "MC Mod Converter"

    def build(self):
        self.theme_cls_primary_palette = "Green"
        return Builder.load_string(KV)

    def on_start(self):
        # Request Android permissions on startup
        if platform == "android":
            self._request_android_permissions()

    def _request_android_permissions(self):
        try:
            from android.permissions import request_permissions, Permission
            perms = [
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ]
            # Android 13+ uses granular permissions
            try:
                perms += [
                    "android.permission.READ_MEDIA_IMAGES",
                    "android.permission.READ_MEDIA_VIDEO",
                    "android.permission.READ_MEDIA_AUDIO",
                ]
            except Exception:
                pass
            request_permissions(perms)
        except Exception as e:
            print(f"Permission request error: {e}")


if __name__ == "__main__":
    MCModConverterApp().run()
