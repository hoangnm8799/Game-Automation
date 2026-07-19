"""
ui/main_menu.py

Main menu window - creates the shared AppContext (hotkeys + position
capture) once, then reads features/registry.py so it never has to import
feature classes by name. Add a feature module (with @register) and it
shows up here automatically.
"""

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from core import updater
from core.app_context import AppContext
from core.capture import CaptureController
from core.hotkeys import HotkeyManager
from core.hotkey_settings import HotkeySettings
from core.version import APP_VERSION
from features.registry import all_features
from ui.hotkey_settings import HotkeySettingsDialog


class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QOL Tool - Menu")
        self.geometry("360x300")

        hotkeys = HotkeyManager()
        hotkey_settings = HotkeySettings()
        capture = CaptureController(self, hotkeys, hotkey_settings.get("capture"))
        self.ctx = AppContext(
            root=self,
            hotkeys=hotkeys,
            capture=capture,
            hotkey_settings=hotkey_settings,
        )
        hotkey_settings.subscribe(self._on_hotkey_settings_changed)

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
        ttk.Button(row, text="Cài đặt hotkey", command=self._open_hotkey_settings).pack(
            side="right", padx=(0, 6)
        )

    def _open_hotkey_settings(self) -> None:
        HotkeySettingsDialog(self, self.ctx.hotkey_settings)

    def _on_hotkey_settings_changed(self, values: dict) -> None:
        # Remove Capture first so an Auto Craft window can safely swap keys
        # (for example Start=Space and Capture=F6) in its own callback.
        self.ctx.capture.unbind_hotkey()
        self.after_idle(self.ctx.capture.set_hotkey, values["capture"])

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
            self._download_update(info)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Cập nhật thất bại:\n{e}")
            self.update_btn.config(state="normal", text="Kiểm tra update")

    def _download_update(self, info: updater.UpdateInfo) -> None:
        """Download in a worker so the progress window remains responsive."""
        dialog = tk.Toplevel(self)
        dialog.title("Đang cập nhật")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)
        status = ttk.Label(body, text=f"Đang tải bản {info.version}...")
        status.pack(anchor="w")
        progress = ttk.Progressbar(body, mode="indeterminate", length=300)
        progress.pack(fill="x", pady=(10, 6))
        progress.start(10)
        ttk.Label(
            body,
            text="Cửa sổ sẽ đóng và mở lại sau khi tải xong.",
            foreground="gray",
        ).pack(anchor="w")

        events: queue.Queue = queue.Queue()

        def report_progress(downloaded: int, total: Optional[int]) -> None:
            events.put(("progress", downloaded, total))

        def download() -> None:
            try:
                downloaded_exe = updater.download_update(info, report_progress)
            except Exception as error:
                events.put(("error", error))
            else:
                events.put(("complete", downloaded_exe))

        threading.Thread(target=download, name="update-download", daemon=True).start()
        self._poll_update_events(info, dialog, status, progress, events, False)

    def _poll_update_events(
        self,
        info: updater.UpdateInfo,
        dialog: tk.Toplevel,
        status: ttk.Label,
        progress: ttk.Progressbar,
        events: queue.Queue,
        has_total: bool,
    ) -> None:
        try:
            while True:
                kind, *data = events.get_nowait()
                if kind == "progress":
                    downloaded, total = data
                    if total:
                        if not has_total:
                            progress.stop()
                            progress.config(mode="determinate", maximum=100)
                            has_total = True
                        percent = downloaded / total * 100
                        progress["value"] = percent
                        status.config(
                            text=(
                                f"Đang tải bản {info.version}: {percent:.0f}% "
                                f"({downloaded / 1024 / 1024:.1f}/{total / 1024 / 1024:.1f} MB)"
                            )
                        )
                elif kind == "error":
                    dialog.destroy()
                    messagebox.showerror("Lỗi", f"Cập nhật thất bại:\n{data[0]}")
                    self.update_btn.config(state="normal", text="Kiểm tra update")
                    return
                elif kind == "complete":
                    progress.stop()
                    progress.config(mode="determinate", maximum=100, value=100)
                    status.config(text="Đã tải xong. Đang khởi động lại...")
                    self.after(500, self._install_update, info, data[0], dialog)
                    return
        except queue.Empty:
            pass

        self.after(
            75,
            self._poll_update_events,
            info,
            dialog,
            status,
            progress,
            events,
            has_total,
        )

    def _install_update(
        self, info: updater.UpdateInfo, downloaded_exe: object, dialog: tk.Toplevel
    ) -> None:
        try:
            updater.apply_update(info, downloaded_exe)
        except Exception as error:
            dialog.destroy()
            messagebox.showerror("Lỗi", f"Cập nhật thất bại:\n{error}")
            self.update_btn.config(state="normal", text="Kiểm tra update")

    def _on_close(self) -> None:
        self.ctx.hotkey_settings.unsubscribe(self._on_hotkey_settings_changed)
        self.ctx.hotkeys.stop_all()
        self.destroy()
