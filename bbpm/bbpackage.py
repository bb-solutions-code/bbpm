"""Discover and parse root `.bbpackage` manifests (delegates to bbscript, BBPMError for CLI)."""

from __future__ import annotations

from pathlib import Path

from bbscript import bbpackage as _bp
from bbscript.errors import PackageLoadError

from .errors import BBPMError


def _wrap(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except PackageLoadError as e:
        raise BBPMError(str(e)) from e


def find_root_bbpackage_file(package_root: Path) -> Path:
    return _wrap(_bp.find_root_bbpackage_file, package_root)


def read_root_manifest(package_root: Path) -> dict:
    return _wrap(_bp.read_root_manifest, package_root)


def read_package_name(package_root: Path) -> str:
    return _wrap(_bp.read_package_name, package_root)
