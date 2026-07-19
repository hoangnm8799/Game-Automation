"""Secure self-update support using public GitHub Releases."""

import json
import os
import ssl
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import certifi

from core.version import APP_VERSION


GITHUB_OWNER = "hoangnm8799"
GITHUB_REPO = "Game-Automation"
GITHUB_TOKEN = ""

_API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
_TIMEOUT = 15


@dataclass
class UpdateInfo:
    version: str
    asset_download_url: str
    asset_name: str
    notes: str = ""


DownloadProgress = Callable[[int, Optional[int]], None]


def _ssl_context() -> ssl.SSLContext:
    """Use certifi's bundled CA list instead of relying on a user's Python CA store."""
    return ssl.create_default_context(cafile=certifi.where())


def _parse_version(value: str) -> tuple:
    parts = []
    for part in value.strip().lstrip("vV").split("."):
        digits = "".join(char for char in part if char.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


def _headers(accept: str) -> dict:
    headers = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def _open(request: urllib.request.Request, timeout: int):
    return urllib.request.urlopen(request, timeout=timeout, context=_ssl_context())


def check_for_update() -> Optional[UpdateInfo]:
    request = urllib.request.Request(
        f"{_API_BASE}/releases/latest", headers=_headers("application/vnd.github+json")
    )
    with _open(request, _TIMEOUT) as response:
        data = json.loads(response.read().decode("utf-8"))

    latest_tag = data["tag_name"]
    if _parse_version(latest_tag) <= _parse_version(APP_VERSION):
        return None

    exe_asset = next(
        (asset for asset in data.get("assets", []) if asset["name"].lower().endswith(".exe")),
        None,
    )
    if exe_asset is None:
        raise RuntimeError(f"Release {latest_tag} không có file .exe đính kèm.")

    return UpdateInfo(
        version=latest_tag.lstrip("vV"),
        asset_download_url=exe_asset["browser_download_url"],
        asset_name=exe_asset["name"],
        notes=(data.get("body") or "").strip(),
    )


def _download_asset(
    url: str, destination: Path, on_progress: Optional[DownloadProgress] = None
) -> None:
    request = urllib.request.Request(url, headers=_headers("application/octet-stream"))
    with _open(request, 120) as response, open(destination, "wb") as file:
        try:
            total_bytes = int(response.headers.get("Content-Length", ""))
        except ValueError:
            total_bytes = None
        if total_bytes is not None and total_bytes <= 0:
            total_bytes = None

        downloaded_bytes = 0
        while chunk := response.read(1024 * 256):
            file.write(chunk)
            downloaded_bytes += len(chunk)
            if on_progress is not None:
                on_progress(downloaded_bytes, total_bytes)


def download_update(
    info: UpdateInfo, on_progress: Optional[DownloadProgress] = None
) -> Path:
    if not getattr(sys, "frozen", False):
        raise RuntimeError("Tự cập nhật chỉ chạy được từ bản .exe đã đóng gói.")

    current_exe = Path(sys.executable).resolve()
    new_exe = current_exe.with_name(f"_update_{info.asset_name}")
    try:
        _download_asset(info.asset_download_url, new_exe, on_progress)
    except Exception:
        new_exe.unlink(missing_ok=True)
        raise
    return new_exe


def apply_update(info: UpdateInfo, downloaded_exe: Optional[Path] = None) -> None:
    """Swap the exe only after the PyInstaller process exits, then restart."""
    if not getattr(sys, "frozen", False):
        raise RuntimeError("Tự cập nhật chỉ chạy được từ bản .exe đã đóng gói.")

    current_exe = Path(sys.executable).resolve()
    new_exe = downloaded_exe or download_update(info)
    batch_file = current_exe.with_name("_apply_update.bat")
    batch_file.write_text(
        "@echo off\r\n"
        "setlocal EnableExtensions\r\n"
        f'set "UPDATE_PID={os.getpid()}"\r\n'
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
        ["cmd", "/c", str(batch_file)],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    sys.exit(0)
