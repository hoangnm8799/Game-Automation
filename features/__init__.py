"""
features/

Importing this package registers every feature (each submodule's
@register decorator runs on import). main.py imports this package once,
before building the menu.

Add a new feature: create features/<name>/ with a ui.py that defines a
BaseFeature subclass decorated with @register, then add one import line
below. Nothing else in the project needs to change.
"""

from features.auto_craft import ui as _auto_craft_ui  # noqa: F401
