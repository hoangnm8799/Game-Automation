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
import os
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from core.version import APP_VERSION

# --- Fill these in for your repo --------------------------------------
GITHUB_OWNER = "YOUR_GITHUB_USERNAME"
GITHUB_REPO = "YOUR_REPO_NAME"
# Leave empty for a public repo (works unauthenticated). Only needed if
# the repo is private - then use a fine-grained PAT scoped to just this
# repo, "Contents: Read-only" permission, nothing else.
GITHUB_TOKEN = ""
# ------------------------------------------------------------------------

GITHUB_OWNER = "hoangnm8799"
GITHUB_REPO = "Game-Automation"

_API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
_TIMEOUT = 15


@dataclass
class UpdateInfo:
    version: str
    asset_download_url: str
    asset_name: str
    notes: str = ""


DownloadProgress = Callable[[int, Optional[int]], None]


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


def _download_asset(
    url: str, dest: Path, on_progress: Optional[DownloadProgress] = None
) -> None:
    req = urllib.request.Request(url, headers=_headers("application/octet-stream"))
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        try:
            total_bytes = int(resp.headers.get("Content-Length", ""))
        except ValueError:
            total_bytes = None
        if total_bytes is not None and total_bytes <= 0:
            total_bytes = None

        downloaded_bytes = 0
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            f.write(chunk)
            downloaded_bytes += len(chunk)
            if on_progress is not None:
                on_progress(downloaded_bytes, total_bytes)


def download_update(
    info: UpdateInfo, on_progress: Optional[DownloadProgress] = None
) -> Path:
    """Download a release next to the running exe without restarting it."""
    if not getattr(sys, "frozen", False):
        raise RuntimeError(
            "Tự cập nhật chỉ chạy được từ bản .exe đã đóng gói, "
            "không chạy từ `python main.py`."
        )

    current_exe = Path(sys.executable).resolve()
    new_exe = current_exe.with_name(f"_update_{info.asset_name}")
    try:
        _download_asset(info.asset_download_url, new_exe, on_progress)
    except Exception:
        new_exe.unlink(missing_ok=True)
        raise
    return new_exe


def apply_update(info: UpdateInfo, downloaded_exe: Optional[Path] = None) -> None:
    """Downloads the new exe next to the current one, spawns a detached
    helper that waits for this process to exit and swaps the files, then
    exits this process. Caller should warn the user the app is about to
    close BEFORE calling this."""
    if not getattr(sys, "frozen", False):
        raise RuntimeError("apply_update() chỉ chạy được từ bản .exe đã đóng gói, không chạy từ `python main.py`")

    current_exe = Path(sys.executable).resolve()
    new_exe = downloaded_exe or download_update(info)

    bat_path = current_exe.with_name("_apply_update.bat")
    # A fixed delay is unreliable: PyInstaller still has to tear down its
    # bootloader and remove its temporary _MEI directory after sys.exit().
    # Wait for this exact process instead, then retry the move in case the
    # bootloader holds the executable for a moment longer.
    current_pid = os.getpid()
    bat_path.write_text(
        "@echo off\r\n"
        "setlocal EnableExtensions\r\n"
        f'set "UPDATE_PID={current_pid}"\r\n'
        f'set "NEW_EXE={new_exe}"\r\n'
        f'set "CURRENT_EXE={current_exe}"\r\n'
        ":wait_for_exit\r\n"
        'tasklist /FI "PID eq %UPDATE_PID%" /NH | findstr /C:"%UPDATE_PID%" > NUL\r\n'
        "if not errorlevel 1 (\r\n"
        "  timeout /t 1 /nobreak > NUL\r\n"
        "  goto wait_for_exit\r\n"
        ")\r\n"
        ":replace_file\r\n"
        'move /y "%NEW_EXE%" "%CURRENT_EXE%" > NUL\r\n'
        "if errorlevel 1 (\r\n"
        "  timeout /t 1 /nobreak > NUL\r\n"
        "  goto replace_file\r\n"
        ")\r\n"
        'start "" "%CURRENT_EXE%"\r\n'
        'del "%~f0"\r\n',
        encoding="utf-8",
    )
    subprocess.Popen(
        ["cmd", "/c", str(bat_path)],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    sys.exit(0)
