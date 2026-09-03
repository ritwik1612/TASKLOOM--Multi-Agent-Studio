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
