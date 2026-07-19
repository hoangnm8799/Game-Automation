"""
core/hotkeys.py

Global hotkey manager built on pynput - bindings fire even when the
Tkinter window doesn't have focus, which is required here since the
game window is what's focused while a craft loop is actually running.
"""

from typing import Callable, Dict, Optional

from pynput import keyboard


class HotkeyManager:
    def __init__(self):
        self._bindings: Dict[str, Callable] = {}
        self._listener: Optional[keyboard.GlobalHotKeys] = None

    def register(self, hotkey: str, callback: Callable) -> None:
        """hotkey uses pynput's GlobalHotKeys syntax, e.g. '<f6>'."""
        self._bindings[hotkey] = callback
        self._restart_listener()

    def unregister(self, hotkey: str) -> None:
        self._bindings.pop(hotkey, None)
        self._restart_listener()

    def stop_all(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self._bindings.clear()

    def _restart_listener(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        if self._bindings:
            self._listener = keyboard.GlobalHotKeys(dict(self._bindings))
            self._listener.start()
