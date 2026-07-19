"""
core/capture.py

Bridges the global-hotkey thread and the Tkinter main thread for
"hover over something in the game, then press a key" position capture.
This is the one place in core/ that knows about Tkinter - bridging a
background thread into Tkinter's main loop is exactly its job.
"""

import queue
import tkinter as tk
from typing import Callable, Optional

from core.hotkeys import HotkeyManager
from core.position import Position
from core import input_actions

DEFAULT_CAPTURE_HOTKEY = "<space>"


class CaptureController:
    def __init__(
        self, root: tk.Tk, hotkeys: HotkeyManager, hotkey: str = DEFAULT_CAPTURE_HOTKEY
    ):
        self._root = root
        self._hotkeys = hotkeys
        self._hotkey = hotkey
        self._is_hotkey_bound = False
        self._queue: "queue.Queue[Position]" = queue.Queue()
        self._callback: Optional[Callable[[Position], None]] = None
        self.set_hotkey(hotkey)
        self._poll()

    @property
    def hotkey(self) -> str:
        return self._hotkey

    def set_hotkey(self, hotkey: str) -> None:
        if hotkey == self._hotkey and self._is_hotkey_bound:
            return
        self.unbind_hotkey()
        self._hotkeys.register(hotkey, self._on_hotkey)
        self._hotkey = hotkey
        self._is_hotkey_bound = True

    def unbind_hotkey(self) -> None:
        if self._is_hotkey_bound:
            self._hotkeys.unregister(self._hotkey)
            self._is_hotkey_bound = False

    def begin_capture(self, callback: Callable[[Position], None]) -> None:
        """The next CAPTURE_HOTKEY press calls `callback(position)` exactly once."""
        self._callback = callback

    def _on_hotkey(self) -> None:
        # Runs on the pynput listener thread - only touch the thread-safe queue here.
        self._queue.put(input_actions.get_current_mouse_position())

    def _poll(self) -> None:
        try:
            while True:
                pos = self._queue.get_nowait()
                if self._callback is not None:
                    cb, self._callback = self._callback, None
                    cb(pos)
        except queue.Empty:
            pass
        self._root.after(80, self._poll)
