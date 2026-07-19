"""
core/config_store.py

Generic JSON profile storage shared by every feature. Each feature owns
the shape of its own config dict; this module only knows how to save,
load, and list named profiles under configs/<feature_key>/<name>.json.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _app_root() -> Path:
    """Where to anchor configs/. Must NOT be sys._MEIPASS - that's a
    temp folder PyInstaller --onefile extracts to and deletes on exit, so
    anything written there is gone the moment the app closes."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


CONFIG_ROOT = _app_root() / "configs"


def _feature_dir(feature_key: str) -> Path:
    d = CONFIG_ROOT / feature_key
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_profile(feature_key: str, profile_name: str, data: Dict[str, Any]) -> Path:
    path = _feature_dir(feature_key) / f"{profile_name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def load_profile(feature_key: str, profile_name: str) -> Dict[str, Any]:
    path = _feature_dir(feature_key) / f"{profile_name}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_profiles(feature_key: str) -> List[str]:
    return sorted(p.stem for p in _feature_dir(feature_key).glob("*.json"))


def delete_profile(feature_key: str, profile_name: str) -> None:
    path = _feature_dir(feature_key) / f"{profile_name}.json"
    if path.exists():
        path.unlink()
