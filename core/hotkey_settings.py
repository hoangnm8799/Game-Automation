"""Persistent, user-configurable global hotkeys."""

import re
from typing import Callable, Dict, List, Mapping

from core import config_store
from core.hotkeys import HotkeyManager


DEFAULT_HOTKEYS = {
    "start": "<f6>",
    "stop": "<f7>",
    "pause": "<f10>",
    "capture": "<space>",
}

_MODIFIERS = {"ctrl", "alt", "shift", "cmd", "win"}
_SPECIAL_KEYS = {
    "space", "enter", "tab", "esc", "insert", "delete", "home", "end",
    "pageup", "pagedown", "up", "down", "left", "right",
}


def normalize_hotkey(value: str) -> str:
    """Turn friendly input such as ``Ctrl+F8`` into pynput syntax."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Hotkey không được để trống.")

    aliases = {"control": "ctrl", "windows": "win", "escape": "esc"}
    parts = [part.strip().lower().strip("<>") for part in value.split("+")]
    if any(not part for part in parts):
        raise ValueError("Định dạng hotkey không hợp lệ.")

    normalized = []
    for part in parts:
        part = aliases.get(part, part)
        if part in _MODIFIERS or part in _SPECIAL_KEYS or re.fullmatch(r"f([1-9]|1[0-9]|2[0-4])", part):
            normalized.append(f"<{part}>")
        elif re.fullmatch(r"[a-z0-9]", part):
            normalized.append(part)
        else:
            raise ValueError(f"Không nhận diện được phím '{part}'.")

    if normalized[-1].strip("<>") in _MODIFIERS:
        raise ValueError("Hotkey phải có phím chính, ví dụ Ctrl+F8.")

    hotkey = "+".join(normalized)
    try:
        HotkeyManager.validate(hotkey)
    except (ValueError, KeyError) as error:
        raise ValueError(f"Hotkey '{value}' không hợp lệ.") from error
    return hotkey


class HotkeySettings:
    """Stores bindings and tells active app components when they change."""

    _FEATURE_KEY = "app"
    _PROFILE_NAME = "hotkeys"

    def __init__(self):
        self._listeners: List[Callable[[Dict[str, str]], None]] = []
        self._values = self._load()

    def _load(self) -> Dict[str, str]:
        try:
            saved = config_store.load_profile(self._FEATURE_KEY, self._PROFILE_NAME)
        except (FileNotFoundError, OSError, ValueError):
            return dict(DEFAULT_HOTKEYS)

        try:
            return self._validate(saved)
        except ValueError:
            return dict(DEFAULT_HOTKEYS)

    @staticmethod
    def _validate(values: Mapping[str, object]) -> Dict[str, str]:
        normalized = {
            name: normalize_hotkey(str(values.get(name, default)))
            for name, default in DEFAULT_HOTKEYS.items()
        }
        if len(set(normalized.values())) != len(normalized):
            raise ValueError("Mỗi chức năng phải dùng một hotkey khác nhau.")
        return normalized

    def get(self, name: str) -> str:
        return self._values[name]

    def values(self) -> Dict[str, str]:
        return dict(self._values)

    def update(self, values: Mapping[str, object]) -> None:
        new_values = self._validate(values)
        config_store.save_profile(self._FEATURE_KEY, self._PROFILE_NAME, new_values)
        self._values = new_values
        for listener in list(self._listeners):
            listener(self.values())

    def subscribe(self, listener: Callable[[Dict[str, str]], None]) -> None:
        self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[Dict[str, str]], None]) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)
