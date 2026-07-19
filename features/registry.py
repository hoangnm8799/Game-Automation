"""
features/registry.py

Central place features register themselves so main_menu.py never has to
import feature classes by name. Adding a feature later = one new package
under features/ + one @register decorator - nothing here, and nothing in
ui/main_menu.py, has to change.
"""

from typing import List, Type

from features.base_feature import BaseFeature

_REGISTRY: List[Type[BaseFeature]] = []


def register(feature_cls: Type[BaseFeature]) -> Type[BaseFeature]:
    """Class decorator: put @register above a BaseFeature subclass to add
    it to the menu."""
    _REGISTRY.append(feature_cls)
    return feature_cls


def all_features() -> List[Type[BaseFeature]]:
    return list(_REGISTRY)
