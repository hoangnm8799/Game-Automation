"""
features/auto_craft/ui.py

Tkinter window for the auto-craft feature: currency steps, target,
regex rules, max attempts, start/stop/pause, live status - and registers
the feature into the main menu via @register.
"""

import re
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Optional

from core import config_store
from core.app_context import AppContext
from core.position import Position
from core.regex_rules import GroupRule, SingleRule
from features.auto_craft.config import CraftConfig, CraftStep, CraftTarget
from features.auto_craft.engine import CraftEngine, CraftStatus
from features.base_feature import BaseFeature
from features.registry import register
from ui.widgets import PositionRow

START_HOTKEY = "<f6>"
STOP_HOTKEY = "<f7>"
PAUSE_HOTKEY = "<f10>"


@register
class AutoCraftFeature(BaseFeature):
    key = "auto_craft"
    display_name = "Auto Craft"
    description = "Spam currency vào target tới khi match regex"

    _open_window: Optional[tk.Toplevel] = None

    def open(self, ctx: AppContext) -> tk.Toplevel:
        # Only one Auto Craft window at a time - a second one would silently
        # steal the F6/F7/F10 hotkey bindings from the first.
        existing = AutoCraftFeature._open_window
        if existing is not None and existing.winfo_exists():
            existing.lift()
            existing.focus_force()
            return existing

        win = tk.Toplevel(ctx.root)
        win.title("Auto Craft")
        AutoCraftWindow(win, ctx)
        AutoCraftFeature._open_window = win
        return win


class AutoCraftWindow:
    def __init__(self, win: tk.Toplevel, ctx: AppContext):
        self.win = win
        self.ctx = ctx
        self.config = CraftConfig(targets=[CraftTarget(label="target")])
        self.engine: Optional[CraftEngine] = None

        self._build_ui()
        self._register_hotkeys()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------- build --
    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}

        steps_frame = ttk.LabelFrame(self.win, text="Currency steps (thứ tự spam, lặp vòng)")
        steps_frame.pack(fill="x", **pad)
        self.steps_list_frame = ttk.Frame(steps_frame)
        self.steps_list_frame.pack(fill="x")
        ttk.Button(steps_frame, text="+ Thêm currency step", command=self._add_step).pack(anchor="w", padx=4, pady=4)

        target_frame = ttk.LabelFrame(self.win, text="Target craft")
        target_frame.pack(fill="x", **pad)
        self.target_row = PositionRow(
            target_frame, self.ctx, "Target",
            initial=self.config.targets[0].pos,
            on_change=self._on_target_change,
        )
        self.target_row.pack(fill="x", padx=4, pady=4)

        rules_frame = ttk.LabelFrame(self.win, text="Regex rules (rule lẻ = AND với nhau, group = OR nội bộ)")
        rules_frame.pack(fill="x", **pad)
        self.rules_list_frame = ttk.Frame(rules_frame)
        self.rules_list_frame.pack(fill="x")
        rule_btns = ttk.Frame(rules_frame)
        rule_btns.pack(fill="x", padx=4, pady=4)
        ttk.Button(rule_btns, text="+ Rule riêng lẻ", command=self._add_single_rule).pack(side="left")
        ttk.Button(rule_btns, text="+ Group", command=self._add_group_rule).pack(side="left", padx=6)

        attempts_frame = ttk.Frame(self.win)
        attempts_frame.pack(fill="x", **pad)
        ttk.Label(attempts_frame, text="Số lần craft tối đa:").pack(side="left")
        self.max_attempts_var = tk.IntVar(value=self.config.max_attempts)
        ttk.Spinbox(attempts_frame, from_=1, to=100000, textvariable=self.max_attempts_var, width=8).pack(side="left", padx=4)

        profile_frame = ttk.Frame(self.win)
        profile_frame.pack(fill="x", **pad)
        ttk.Label(profile_frame, text="Profile:").pack(side="left")
        existing_profiles = config_store.list_profiles(AutoCraftFeature.key)
        self.profile_var = tk.StringVar(value=existing_profiles[0] if existing_profiles else "default")
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var, values=existing_profiles, width=14)
        self.profile_combo.pack(side="left", padx=4)
        ttk.Button(profile_frame, text="Lưu", command=self._save_profile).pack(side="left")
        ttk.Button(profile_frame, text="Tải", command=self._load_profile).pack(side="left", padx=4)
        ttk.Button(profile_frame, text="Xoá", command=self._delete_profile).pack(side="left")

        ctrl_frame = ttk.Frame(self.win)
        ctrl_frame.pack(fill="x", **pad)
        ttk.Button(ctrl_frame, text="Start (F6)", command=self._start).pack(side="left")
        ttk.Button(ctrl_frame, text="Pause (F10)", command=self._toggle_pause).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="Stop (F7)", command=self._stop).pack(side="left")

        self.status_var = tk.StringVar(
            value="Sẵn sàng. Đưa chuột vào góc màn hình bất kỳ lúc nào để dừng khẩn cấp (fail-safe)."
        )
        ttk.Label(self.win, textvariable=self.status_var, foreground="blue", wraplength=440).pack(
            fill="x", padx=8, pady=(0, 8)
        )

        self._redraw_steps()
        self._redraw_rules()

    # --- currency steps -----------------------------------------------------
    def _redraw_steps(self) -> None:
        for w in self.steps_list_frame.winfo_children():
            w.destroy()
        for i, step in enumerate(self.config.steps):
            row = ttk.Frame(self.steps_list_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"Step {i + 1}:", width=7).pack(side="left")
            pos_row = PositionRow(
                row, self.ctx, step.label or "currency",
                initial=step.currency_pos,
                on_change=lambda pos, s=step: setattr(s, "currency_pos", pos),
            )
            pos_row.pack(side="left", fill="x", expand=True)
            ttk.Button(row, text="x", width=2, command=lambda s=step: self._remove_step(s)).pack(side="right")

    def _add_step(self) -> None:
        self.config.steps.append(CraftStep(label=f"currency {len(self.config.steps) + 1}"))
        self._redraw_steps()

    def _remove_step(self, step: CraftStep) -> None:
        self.config.steps.remove(step)
        self._redraw_steps()

    def _on_target_change(self, pos: Position) -> None:
        self.config.targets[0].pos = pos

    # --- regex rules ---------------------------------------------------------
    def _redraw_rules(self) -> None:
        for w in self.rules_list_frame.winfo_children():
            w.destroy()
        for i, node in enumerate(self.config.rules.nodes):
            if isinstance(node, GroupRule):
                box = ttk.LabelFrame(self.rules_list_frame, text="Group (khớp 1 trong các dòng = OR)")
                box.pack(fill="x", pady=3, padx=2)
                for p in node.patterns:
                    prow = ttk.Frame(box)
                    prow.pack(fill="x")
                    ttk.Label(prow, text=p.pattern).pack(side="left", padx=4)
                addrow = ttk.Frame(box)
                addrow.pack(fill="x")
                ttk.Button(addrow, text="+ dòng trong group",
                           command=lambda g=node: self._add_line_to_group(g)).pack(side="left", padx=4, pady=2)
                ttk.Button(addrow, text="Xoá cả group",
                           command=lambda idx=i: self._remove_rule(idx)).pack(side="right", padx=4)
            else:
                row = ttk.Frame(self.rules_list_frame)
                row.pack(fill="x", pady=1)
                ttk.Label(row, text=f"[Rule lẻ] {node.pattern}").pack(side="left", padx=4)
                ttk.Button(row, text="x", width=2, command=lambda idx=i: self._remove_rule(idx)).pack(side="right")

    def _ask_pattern(self, title: str) -> Optional[str]:
        pattern = simpledialog.askstring(title, "Nhập regex:", parent=self.win)
        if not pattern:
            return None
        try:
            re.compile(pattern)
        except re.error as e:
            messagebox.showerror("Regex không hợp lệ", str(e))
            return None
        return pattern

    def _add_single_rule(self) -> None:
        pattern = self._ask_pattern("Rule riêng lẻ")
        if pattern:
            self.config.rules.add_single(pattern)
            self._redraw_rules()

    def _add_group_rule(self) -> None:
        self.config.rules.add_group([])
        self._redraw_rules()

    def _add_line_to_group(self, group: GroupRule) -> None:
        pattern = self._ask_pattern("Thêm dòng vào group")
        if pattern:
            group.patterns.append(SingleRule(pattern=pattern))
            self._redraw_rules()

    def _remove_rule(self, index: int) -> None:
        self.config.rules.remove_at(index)
        self._redraw_rules()

    # -------------------------------------------------------------- engine --
    def _hard_errors(self) -> list:
        errors = []
        if not self.config.steps or any(s.currency_pos is None for s in self.config.steps):
            errors.append("Cần ít nhất 1 currency step, và mọi step phải capture vị trí.")
        if not self.config.targets or self.config.targets[0].pos is None:
            errors.append("Chưa capture vị trí target.")
        return errors

    def _soft_warnings(self) -> list:
        warnings = []
        if not self.config.rules.nodes:
            warnings.append("Chưa có regex rule nào - craft sẽ chạy tới max attempts mà không tự dừng do match.")
        return warnings

    def _start(self) -> None:
        if self.engine and self.engine.is_running:
            return
        errors = self._hard_errors()
        if errors:
            messagebox.showwarning("Thiếu thông tin", "\n".join(errors))
            return
        warnings = self._soft_warnings()
        if warnings and not messagebox.askyesno("Xác nhận", "\n".join(warnings) + "\nVẫn chạy?"):
            return

        self.config.max_attempts = self.max_attempts_var.get()
        self.engine = CraftEngine(self.config, on_progress=self._on_progress)
        self.engine.start()
        self.status_var.set("Đang chạy...")

    def _stop(self) -> None:
        if self.engine:
            self.engine.stop()

    def _toggle_pause(self) -> None:
        if self.engine and self.engine.is_running:
            self.engine.toggle_pause()
            self.status_var.set(
                "Đã tạm dừng (Pause/F10 lần nữa để tiếp tục)" if self.engine.is_paused else "Đang chạy..."
            )

    def _on_progress(self, progress) -> None:
        # Called from the engine's background thread - marshal to the Tk main
        # thread. The window may already be gone if the user closed it while
        # this last iteration was still in flight (stop() only signals, it
        # doesn't block) - guard instead of letting a TclError escape on the
        # engine's own thread.
        try:
            if self.win.winfo_exists():
                self.win.after(0, self._apply_progress, progress)
        except tk.TclError:
            pass

    def _apply_progress(self, progress) -> None:
        if progress.status == CraftStatus.RUNNING:
            self.status_var.set(f"Đang craft... lần {progress.attempts} ({progress.step_label})")
        elif progress.status == CraftStatus.SUCCESS:
            self.status_var.set(f"✅ Match sau {progress.attempts} lần!")
            messagebox.showinfo("Thành công", f"Craft thành công sau {progress.attempts} lần!")
        elif progress.status == CraftStatus.MAX_ATTEMPTS_REACHED:
            self.status_var.set(f"⚠️ Hết {progress.attempts} lần vẫn chưa match.")
            messagebox.showwarning(
                "Hết lượt",
                f"Đã thử {progress.attempts} lần mà chưa match regex nào - bạn craft tiếp thủ công nhé.",
            )
        elif progress.status == CraftStatus.STOPPED:
            self.status_var.set(f"Đã dừng ở lần {progress.attempts}. {progress.message}".strip())

    # ------------------------------------------------------------ hotkeys --
    def _register_hotkeys(self) -> None:
        self.ctx.hotkeys.register(START_HOTKEY, lambda: self.win.after(0, self._start))
        self.ctx.hotkeys.register(STOP_HOTKEY, lambda: self.win.after(0, self._stop))
        self.ctx.hotkeys.register(PAUSE_HOTKEY, lambda: self.win.after(0, self._toggle_pause))

    def _unregister_hotkeys(self) -> None:
        self.ctx.hotkeys.unregister(START_HOTKEY)
        self.ctx.hotkeys.unregister(STOP_HOTKEY)
        self.ctx.hotkeys.unregister(PAUSE_HOTKEY)

    # ------------------------------------------------------------ profile --
    def _save_profile(self) -> None:
        name = self.profile_var.get().strip()
        if not name:
            messagebox.showwarning("Thiếu tên", "Nhập tên profile trước khi lưu.")
            return
        self.config.max_attempts = self.max_attempts_var.get()
        try:
            config_store.save_profile(AutoCraftFeature.key, name, self.config.to_dict())
        except OSError as e:
            messagebox.showerror("Lỗi", f"Không lưu được profile '{name}':\n{e}")
            return
        self.profile_combo["values"] = config_store.list_profiles(AutoCraftFeature.key)
        messagebox.showinfo("Đã lưu", f"Đã lưu profile '{name}'")

    def _load_profile(self) -> None:
        name = self.profile_var.get().strip()
        if not name:
            messagebox.showwarning("Thiếu tên", "Nhập hoặc chọn tên profile trước khi tải.")
            return

        try:
            data = config_store.load_profile(AutoCraftFeature.key, name)
            loaded_config = CraftConfig.from_dict(data)
        except FileNotFoundError:
            messagebox.showerror(
                "Lỗi",
                f"Chưa có profile tên '{name}'.\nBấm 'Lưu' trước để tạo profile này, rồi mới 'Tải' được.",
            )
            return
        except Exception as e:  # file JSON hỏng/định dạng lạ - không để crash, báo rõ nguyên nhân
            messagebox.showerror("Lỗi", f"Không đọc được profile '{name}':\n{e}")
            return

        self.config = loaded_config
        if not self.config.targets:
            self.config.targets = [CraftTarget(label="target")]

        self.max_attempts_var.set(self.config.max_attempts)
        self.target_row.set_position(self.config.targets[0].pos)
        self._redraw_steps()
        self._redraw_rules()

    def _delete_profile(self) -> None:
        name = self.profile_var.get().strip()
        if not name:
            return
        if not messagebox.askyesno("Xác nhận", f"Xoá profile '{name}'?"):
            return
        config_store.delete_profile(AutoCraftFeature.key, name)
        self.profile_combo["values"] = config_store.list_profiles(AutoCraftFeature.key)
        messagebox.showinfo("Đã xoá", f"Đã xoá profile '{name}'")

    # -------------------------------------------------------------- close --
    def _on_close(self) -> None:
        if self.engine:
            self.engine.stop()
            self.engine.wait_until_stopped(timeout=2.0)
        self._unregister_hotkeys()
        AutoCraftFeature._open_window = None
        self.win.destroy()
