"""
features/auto_craft/engine.py

Runs the craft loop: cycles through CraftConfig.steps, applying each
currency to the target, checking the rule set after every single
application, stopping on match or on hitting max_attempts.

Independent of any GUI toolkit - progress is reported through a plain
callback so any UI can subscribe (Tkinter today, something else later).
Runs on a background thread so it never blocks/freezes the UI.
"""

import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Optional

from core import input_actions
from features.auto_craft.config import CraftConfig


class CraftStatus(Enum):
    RUNNING = auto()
    SUCCESS = auto()
    MAX_ATTEMPTS_REACHED = auto()
    STOPPED = auto()


@dataclass
class CraftProgress:
    status: CraftStatus
    attempts: int
    last_text: str = ""
    step_label: str = ""
    message: str = ""


class CraftEngine:
    """One instance per running craft session - create a new one each Start."""

    def __init__(self, config: CraftConfig, on_progress: Callable[[CraftProgress], None]):
        self.config = config
        self.on_progress = on_progress
        self._thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()  # set == currently paused
        self.attempts = 0

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    @property
    def is_paused(self) -> bool:
        return self._pause_flag.is_set()

    # ---- public controls --------------------------------------------------
    def start(self) -> None:
        if self.is_running:
            return
        self._stop_flag.clear()
        self._pause_flag.clear()
        self.attempts = 0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_flag.set()

    def wait_until_stopped(self, timeout: Optional[float] = None) -> None:
        """Block until the background thread actually exits (or `timeout`
        elapses). Call after stop() when the caller is about to tear down
        anything the loop's on_progress callback touches (e.g. a Tkinter
        window) - stop() alone only *signals* the thread to stop, it
        doesn't wait, so without this there's a window where one last
        in-flight iteration can still fire on_progress after the window
        it was about to update is already destroyed."""
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def toggle_pause(self) -> None:
        if self._pause_flag.is_set():
            self._pause_flag.clear()
        else:
            self._pause_flag.set()

    # ---- internal -----------------------------------------------------------
    def _run(self) -> None:
        if not self.config.steps or any(s.currency_pos is None for s in self.config.steps):
            self._report(CraftStatus.STOPPED, message="Chưa đủ currency step (thiếu vị trí)")
            return
        if not self.config.targets or self.config.targets[0].pos is None:
            self._report(CraftStatus.STOPPED, message="Chưa có vị trí target")
            return

        target = self.config.target
        step_index = 0

        try:
            while self.attempts < self.config.max_attempts:
                if self._stop_flag.is_set():
                    self._report(CraftStatus.STOPPED)
                    return

                while self._pause_flag.is_set():
                    if self._stop_flag.is_set():
                        self._report(CraftStatus.STOPPED)
                        return
                    time.sleep(0.1)

                step = self.config.steps[step_index % len(self.config.steps)]

                input_actions.apply_currency(step.currency_pos, target.pos)
                self.attempts += 1

                text = input_actions.copy_text_at(target.pos)
                self._report(CraftStatus.RUNNING, last_text=text, step_label=step.label)

                if self.config.rules.is_match(text):
                    self._report(CraftStatus.SUCCESS, last_text=text, step_label=step.label)
                    return

                step_index += 1

            self._report(CraftStatus.MAX_ATTEMPTS_REACHED)
        except Exception as e:
            # A bad regex or a pyautogui FAILSAFE trip should stop the loop
            # cleanly and report why - never crash the thread silently.
            self._report(CraftStatus.STOPPED, message=f"Dừng do lỗi/fail-safe: {e}")

    def _report(self, status: CraftStatus, last_text: str = "", step_label: str = "", message: str = "") -> None:
        self.on_progress(CraftProgress(
            status=status, attempts=self.attempts,
            last_text=last_text, step_label=step_label, message=message,
        ))
