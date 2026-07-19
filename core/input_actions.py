"""
core/input_actions.py

The only file that talks to pyautogui/pyperclip directly. Every feature
goes through the functions here instead of calling pyautogui itself, so
swapping the automation backend (e.g. pyautogui -> pydirectinput, for
games that ignore SetCursorPos-style clicks) means editing this one file.
"""

import time

import pyautogui
import pyperclip

from core.position import Position

# The click path is intentionally short, but the result check is strict:
# after Ctrl+C we wait until fresh clipboard text arrives instead of using a
# stale value or immediately assuming an empty result. This makes normal
# crafts much faster without skipping a rule check.
CLICK_DELAY = 0.04
COPY_READY_TIMEOUT = 1.0
COPY_RETRY_AFTER = 0.25
COPY_POLL_INTERVAL = 0.01

pyautogui.PAUSE = 0          # we manage our own delays explicitly below
pyautogui.FAILSAFE = True    # slam the mouse into a screen corner to abort


class ClipboardReadError(RuntimeError):
    """The game did not put fresh item text on the clipboard in time."""


def get_current_mouse_position() -> Position:
    x, y = pyautogui.position()
    return Position(x=x, y=y)


def right_click(pos: Position) -> None:
    pyautogui.moveTo(pos.x, pos.y)
    time.sleep(CLICK_DELAY)
    pyautogui.click(button="right")
    time.sleep(CLICK_DELAY)


def left_click(pos: Position) -> None:
    pyautogui.moveTo(pos.x, pos.y)
    time.sleep(CLICK_DELAY)
    pyautogui.click(button="left")
    time.sleep(CLICK_DELAY)


def apply_currency(currency_pos: Position, target_pos: Position) -> None:
    """One craft step: right-click the currency, then left-click the target."""
    right_click(currency_pos)
    left_click(target_pos)


def copy_text_at(pos: Position) -> str:
    """Return fresh copied text, never a stale value from a previous craft."""
    pyautogui.moveTo(pos.x, pos.y)
    time.sleep(CLICK_DELAY)
    pyperclip.copy("")  # clear first so a stale value can't cause a false match
    pyautogui.hotkey("ctrl", "c")
    deadline = time.monotonic() + COPY_READY_TIMEOUT
    retry_at = time.monotonic() + COPY_RETRY_AFTER
    while time.monotonic() < deadline:
        text = pyperclip.paste()
        if text:
            return text
        if time.monotonic() >= retry_at:
            pyautogui.hotkey("ctrl", "c")
            retry_at = deadline
        time.sleep(COPY_POLL_INTERVAL)
    raise ClipboardReadError(
        "Không đọc được text mới từ clipboard; craft đã dừng để tránh check sai."
    )
