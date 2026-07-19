"""
core/updater.py

Self-update via GitHub Releases - no backend server needed, GitHub's own
API is the "server". Flow:

  1. check_for_update() hits GET /repos/{owner}/{repo}/releases/latest
     and compares the release tag against core.version.APP_VERSION.
  2. apply_update() downloads the new .exe (as a sibling file), writes a
     tiny .bat that waits for this process to exit, swaps the old exe for
     the new one, relaunches it, then deletes itself - then this process
     exits. A running .exe can't overwrite its own file while the OS has
     it open, hence the external helper script.

Repo is PUBLIC, so GITHUB_TOKEN below can stay empty - GitHub's API and
release-asset downloads work unauthenticated for public repos (limited to
60 requests/hour per IP, plenty for a manual "check update" button). Only
fill in a token if you ever switch the repo back to private.

Only works from the packaged .exe (apply_update needs sys.executable to
BE the exe) - from `python main.py` you can still call
check_for_update() to test the API call itself, but apply_update() will
raise.
"""

import json
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.version import APP_VERSION

# --- Fill these in for your repo --------------------------------------
GITHUB_OWNER = "YOUR_GITHUB_USERNAME"
GITHUB_REPO = "YOUR_REPO_NAME"
# Leave empty for a public repo (works unauthenticated). Only needed if
# the repo is private - then use a fine-grained PAT scoped to just this
# repo, "Contents: Read-only" permission, nothing else.
GITHUB_TOKEN = ""
# ------------------------------------------------------------------------

_API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
_TIMEOUT = 15


@dataclass
class UpdateInfo:
    version: str
    asset_download_url: str
    asset_name: str
    notes: str = ""


def _parse_version(v: str) -> tuple:
    v = v.strip().lstrip("vV")
    parts = []
    for p in v.split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


def _headers(accept: str) -> dict:
    h = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def check_for_update() -> Optional[UpdateInfo]:
    """Returns UpdateInfo if the latest GitHub release is newer than
    APP_VERSION, else None. Raises urllib.error.URLError / HTTPError on
    network problems - the caller decides how to show that."""
    req = urllib.request.Request(
        f"{_API_BASE}/releases/latest",
        headers=_headers("application/vnd.github+json"),
    )
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    latest_tag = data["tag_name"]
    if _parse_version(latest_tag) <= _parse_version(APP_VERSION):
        return None

    assets = data.get("assets", [])
    exe_asset = next((a for a in assets if a["name"].lower().endswith(".exe")), None)
    if exe_asset is None:
        raise RuntimeError(f"Release {latest_tag} không có file .exe đính kèm")

    return UpdateInfo(
        version=latest_tag.lstrip("vV"),
        asset_download_url=exe_asset["browser_download_url"],
        asset_name=exe_asset["name"],
        notes=(data.get("body") or "").strip(),
    )


def _download_asset(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers=_headers("application/octet-stream"))
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            f.write(chunk)


def apply_update(info: UpdateInfo) -> None:
    """Downloads the new exe next to the current one, spawns a detached
    helper that waits for this process to exit and swaps the files, then
    exits this process. Caller should warn the user the app is about to
    close BEFORE calling this."""
    if not getattr(sys, "frozen", False):
        raise RuntimeError("apply_update() chỉ chạy được từ bản .exe đã đóng gói, không chạy từ `python main.py`")

    current_exe = Path(sys.executable).resolve()
    new_exe = current_exe.with_name(f"_update_{info.asset_name}")
    _download_asset(info.asset_download_url, new_exe)

    bat_path = current_exe.with_name("_apply_update.bat")
    bat_path.write_text(
        "@echo off\r\n"
        "timeout /t 2 /nobreak > NUL\r\n"
        f'move /y "{new_exe}" "{current_exe}"\r\n'
        f'start "" "{current_exe}"\r\n'
        f'del "%~f0"\r\n',
        encoding="utf-8",
    )
    subprocess.Popen(
        ["cmd", "/c", str(bat_path)],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    sys.exit(0)
