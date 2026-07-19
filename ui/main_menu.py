"""
ui/main_menu.py

Main menu window - creates the shared AppContext (hotkeys + position
capture) once, then reads features/registry.py so it never has to import
feature classes by name. Add a feature module (with @register) and it
shows up here automatically.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from core import updater
from core.app_context import AppContext
from core.capture import CaptureController
from core.hotkeys import HotkeyManager
from core.version import APP_VERSION
from features.registry import all_features


class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QOL Tool - Menu")
        self.geometry("360x300")

        hotkeys = HotkeyManager()
        capture = CaptureController(self, hotkeys)
        self.ctx = AppContext(root=self, hotkeys=hotkeys, capture=capture)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        ttk.Label(self, text="Chọn tính năng", font=("Segoe UI", 12, "bold")).pack(pady=10)
        for feature_cls in all_features():
            feature = feature_cls()
            frame = ttk.Frame(self)
            frame.pack(fill="x", padx=12, pady=4)
            ttk.Button(frame, text=feature.display_name,
                       command=lambda f=feature: self._open_feature(f)).pack(fill="x")
            if feature.description:
                ttk.Label(frame, text=feature.description, foreground="gray").pack(anchor="w")

        footer = ttk.Frame(self)
        footer.pack(side="bottom", fill="x", padx=12, pady=10)
        ttk.Separator(footer).pack(fill="x", pady=(0, 8))
        row = ttk.Frame(footer)
        row.pack(fill="x")
        ttk.Label(row, text=f"Bản {APP_VERSION}", foreground="gray").pack(side="left")
        self.update_btn = ttk.Button(row, text="Kiểm tra update", command=self._check_update)
        self.update_btn.pack(side="right")

    def _open_feature(self, feature) -> None:
        """Hide the menu while the feature window is open, show it again
        once that window closes. Generic on purpose - works for any future
        feature without that feature having to know the menu exists."""
        win = feature.open(self.ctx)
        self.withdraw()
        self.wait_window(win)  # blocks here only - hotkeys/timers keep running
        self.deiconify()

    def _check_update(self) -> None:
        self.update_btn.config(state="disabled", text="Đang kiểm tra...")
        self.update_idletasks()
        try:
            info = updater.check_for_update()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không kiểm tra được update:\n{e}")
            self.update_btn.config(state="normal", text="Kiểm tra update")
            return

        self.update_btn.config(state="normal", text="Kiểm tra update")

        if info is None:
            messagebox.showinfo("Update", "Bạn đang dùng bản mới nhất rồi.")
            return

        msg = f"Có bản mới: {info.version}\n\n{info.notes}".strip()
        if not messagebox.askyesno("Có bản cập nhật mới", msg + "\n\nCập nhật ngay?"):
            return

        self.update_btn.config(state="disabled", text="Đang tải bản mới...")
        self.update_idletasks()
        try:
            updater.apply_update(info)  # exits this process itself on success
        except Exception as e:
            messagebox.showerror("Lỗi", f"Cập nhật thất bại:\n{e}")
            self.update_btn.config(state="normal", text="Kiểm tra update")

    def _on_close(self) -> None:
        self.ctx.hotkeys.stop_all()
        self.destroy()
