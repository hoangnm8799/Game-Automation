"""The in-app dialog for configuring and saving global hotkeys."""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict

from core.hotkey_settings import HotkeySettings


class HotkeySettingsDialog(tk.Toplevel):
    _LABELS = {
        "start": "Start Auto Craft",
        "stop": "Stop Auto Craft",
        "pause": "Pause / Resume",
        "capture": "Capture vị trí",
    }

    def __init__(self, parent: tk.Misc, settings: HotkeySettings):
        super().__init__(parent)
        self._settings = settings
        self._vars: Dict[str, tk.StringVar] = {
            name: tk.StringVar(value=value)
            for name, value in settings.values().items()
        }

        self.title("Cài đặt hotkey")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        body = ttk.Frame(self, padding=16)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Hotkey toàn cục", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            body,
            text="Ví dụ: F8, Space, Ctrl+F8. Các hotkey phải khác nhau.",
            foreground="gray",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 10))

        for row, (name, label) in enumerate(self._LABELS.items(), start=2):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", pady=3)
            ttk.Entry(body, textvariable=self._vars[name], width=20).grid(
                row=row, column=1, sticky="ew", padx=(12, 0), pady=3
            )

        buttons = ttk.Frame(body)
        buttons.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Hủy", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Lưu và áp dụng", command=self._save).pack(side="right", padx=(0, 6))

    def _save(self) -> None:
        try:
            self._settings.update({name: var.get() for name, var in self._vars.items()})
        except (OSError, ValueError) as error:
            messagebox.showerror("Không thể lưu hotkey", str(error), parent=self)
            return
        self.destroy()
