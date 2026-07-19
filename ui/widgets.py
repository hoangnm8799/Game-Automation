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
from core.capture import CAPTURE_HOTKEY
from core.position import Position

# "<space>" -> "SPACE", "<f9>" -> "F9" - derived once so the button text
# can never drift out of sync with the actual bound key again.
_CAPTURE_KEY_LABEL = CAPTURE_HOTKEY.strip("<>").upper()


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

        ttk.Label(self, text=label, width=label_width).pack(side="left")
        self.value_var = tk.StringVar(value=self._fmt(initial))
        ttk.Label(self, textvariable=self.value_var, width=value_width).pack(side="left", padx=4)
        ttk.Button(self, text=f"Capture (hover + {_CAPTURE_KEY_LABEL})", command=self._start_capture).pack(side="left")

    def _fmt(self, pos: Optional[Position]) -> str:
        return f"({pos.x}, {pos.y})" if pos else "(chưa capture)"

    def _start_capture(self) -> None:
        def on_captured(pos: Position) -> None:
            self.position = pos
            self.value_var.set(self._fmt(pos))
            if self.on_change:
                self.on_change(pos)

        self.ctx.capture.begin_capture(on_captured)

    def set_position(self, pos: Optional[Position]) -> None:
        self.position = pos
        self.value_var.set(self._fmt(pos))
