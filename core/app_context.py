"""
core/app_context.py

Bundles the services every feature needs (hotkeys, position capture, the
root window) into one object. Adding a new shared service later means
adding one field here, not changing every feature's function signature.
"""

from dataclasses import dataclass
import tkinter as tk

from core.hotkeys import HotkeyManager
from core.capture import CaptureController
from core.hotkey_settings import HotkeySettings


@dataclass
class AppContext:
    root: tk.Tk
    hotkeys: HotkeyManager
    capture: CaptureController
    hotkey_settings: HotkeySettings
