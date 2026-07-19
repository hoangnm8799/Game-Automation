"""
features/base_feature.py

Every feature (auto-craft, and whatever comes later) implements this so
the main menu can list and launch it without importing or knowing
anything about that feature's internals.
"""

from abc import ABC, abstractmethod
import tkinter as tk

from core.app_context import AppContext


class BaseFeature(ABC):
    """Contract every feature module must satisfy to show up in the menu."""

    key: str = "base_feature"           # short id - used for profile filenames etc.
    display_name: str = "Base Feature"  # shown as the menu button label
    description: str = ""               # one-line blurb under the label

    @abstractmethod
    def open(self, ctx: AppContext) -> tk.Toplevel:
        """Build and show the feature's window. Called each time the user
        opens it from the main menu. `ctx` carries the shared services
        (root window, hotkeys, position capture) every feature needs."""
        raise NotImplementedError
