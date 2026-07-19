"""
ui/widgets.py

Small reusable Tkinter widgets shared across features. Currently just
PositionRow (label + captured position + "Capture" button, wired to the
shared CaptureController) - add more here as future features need them.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from core.app_context import AppContext
from core.position import Position


class PositionRow(ttk.Frame):
    """<label>  (x, y)  [Capture (hover + <CAPTURE_KEY_LABEL>)]

    Wraps AppContext.capture so any feature can drop this in instead of
    wiring up hover-and-hotkey capture by hand each time."""

    def __init__(
        self,
        parent,
        ctx: AppContext,
        label: str,
        initial: Optional[Position] = None,
        on_change: Optional[Callable[[Position], None]] = None,
        label_width: int = 10,
        value_width: int = 14,
    ):
        super().__init__(parent)
        self.ctx = ctx
        self.on_change = on_change
        self.position = initial
        self._hotkey_listener = self._on_hotkey_settings_changed

        ttk.Label(self, text=label, width=label_width).pack(side="left")
        self.value_var = tk.StringVar(value=self._fmt(initial))
        ttk.Label(self, textvariable=self.value_var, width=value_width).pack(side="left", padx=4)
        self.capture_btn = ttk.Button(self, command=self._start_capture)
        self.capture_btn.pack(side="left")
        self._refresh_capture_label()
        self.ctx.hotkey_settings.subscribe(self._hotkey_listener)
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _fmt(self, pos: Optional[Position]) -> str:
        return f"({pos.x}, {pos.y})" if pos else "(chưa capture)"

    def _start_capture(self) -> None:
        def on_captured(pos: Position) -> None:
            self.position = pos
            self.value_var.set(self._fmt(pos))
            if self.on_change:
                self.on_change(pos)

        self.ctx.capture.begin_capture(on_captured)

    def _refresh_capture_label(self) -> None:
        hotkey = self.ctx.hotkey_settings.get("capture").upper()
        self.capture_btn.config(text=f"Capture (hover + {hotkey})")

    def _on_hotkey_settings_changed(self, _values: dict) -> None:
        if self.winfo_exists():
            self._refresh_capture_label()

    def _on_destroy(self, event) -> None:
        if event.widget is self:
            self.ctx.hotkey_settings.unsubscribe(self._hotkey_listener)

    def set_position(self, pos: Optional[Position]) -> None:
        self.position = pos
        self.value_var.set(self._fmt(pos))
