"""Project and .bbpm layout helpers."""

from __future__ import annotations

from pathlib import Path


BBPM_DIR_NAME = ".bbpm"
MANIFEST_NAME = "bbpm.json"
PACKAGES_SUBDIR = "packages"
DEFAULT_FOBLOX_GIT_URL = "https://github.com/bb-solutions-code/foblox.git"


def bbpm_dir(project_root: Path) -> Path:
    return project_root / BBPM_DIR_NAME


def manifest_path(project_root: Path) -> Path:
    return bbpm_dir(project_root) / MANIFEST_NAME


def packages_dir(project_root: Path) -> Path:
    return bbpm_dir(project_root) / PACKAGES_SUBDIR


def find_project_root(start: Path) -> Path | None:
    """Walk upward from `start` (file or directory) for `.bbpm/bbpm.json`."""
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for p in [cur, *cur.parents]:
        if manifest_path(p).is_file():
            return p
    return None
