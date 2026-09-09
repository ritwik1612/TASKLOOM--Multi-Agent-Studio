"""Paths that work both from source and from a PyInstaller bundle."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_root() -> Path:
    """Return the directory containing bundled assets or source assets."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def resource_path(*parts: str | Path) -> Path:
    return resource_root().joinpath(*parts)


def application_data_dir() -> Path:
    """Return a user-writable location for caches and local application state."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    path = base / "Taskloom"
    path.mkdir(parents=True, exist_ok=True)
    return path


def downloads_dir() -> Path:
    """Return the current user's Windows Downloads known folder."""
    override = os.environ.get("TASKLOOM_DOWNLOADS_DIR")
    if override:
        path = Path(override).expanduser()
    elif sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            ) as key:
                raw_path, _ = winreg.QueryValueEx(
                    key, "{374DE290-123F-4565-9164-39C4925E467B}"
                )
            path = Path(os.path.expandvars(raw_path))
        except (OSError, ImportError):
            path = Path.home() / "Downloads"
    else:
        path = Path.home() / "Downloads"

    path.mkdir(parents=True, exist_ok=True)
    return path


def save_to_downloads(data: str | bytes, filename: str) -> Path:
    """Save a download without overwriting an existing file and return its path."""
    safe_name = Path(filename).name
    if safe_name in {"", ".", ".."}:
        raise ValueError("A valid download filename is required.")

    payload = data.encode("utf-8") if isinstance(data, str) else bytes(data)
    folder = downloads_dir()
    original = Path(safe_name)

    for index in range(1000):
        suffix = "" if index == 0 else f" ({index})"
        candidate = folder / f"{original.stem}{suffix}{original.suffix}"
        try:
            with candidate.open("xb") as stream:
                stream.write(payload)
            return candidate
        except FileExistsError:
            continue

    raise FileExistsError(f"Could not create a unique file for {safe_name}.")
