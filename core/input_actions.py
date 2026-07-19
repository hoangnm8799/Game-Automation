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

# Small pause after each simulated action so the OS/game has time to
# register it before the next one fires. Bump these up if clicks/copies
# feel unreliable in your game, lower them once you've confirmed it's stable.
CLICK_DELAY = 0.08
COPY_DELAY = 0.1

pyautogui.PAUSE = 0          # we manage our own delays explicitly below
pyautogui.FAILSAFE = True    # slam the mouse into a screen corner to abort


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
    """Hover a position and Ctrl+C it, returning whatever landed on the clipboard."""
    pyautogui.moveTo(pos.x, pos.y)
    time.sleep(COPY_DELAY)
    pyperclip.copy("")  # clear first so a stale value can't cause a false match
    pyautogui.hotkey("ctrl", "c")
    time.sleep(COPY_DELAY)
    return pyperclip.paste()
