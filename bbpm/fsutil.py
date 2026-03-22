"""Filesystem helpers (Windows-safe tree removal)."""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path


def safe_rmtree(path: Path) -> None:
    """Remove a directory tree; clear read-only bits on Windows."""

    def _onerror(func: object, p: str, _exc_info: object) -> None:
        os.chmod(p, stat.S_IWRITE)
        func(p)

    shutil.rmtree(path, onerror=_onerror)


def ignore_git(_dir: str, names: list[str]) -> list[str]:
    return [".git"] if ".git" in names else []
