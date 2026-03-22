"""Load block entrypoints from installed BBPM packages."""

from __future__ import annotations

import warnings
from pathlib import Path

from bbscript.package_load import load_package_blocks as _load_package_blocks
from bbscript.runtime import prepare_core
from bbscript.errors import PackageLoadError

from .errors import BBPMError
from .manifest import read_manifest, package_install_path
from .paths import packages_dir


def load_package_blocks(package_root: Path, *, package_name: str) -> None:
    """Add package root to sys.path and import each block entrypoint module."""
    try:
        _load_package_blocks(package_root, package_name=package_name)
    except PackageLoadError as e:
        raise BBPMError(str(e)) from e


def load_installed_packages(project_root: Path) -> None:
    """Load all packages registered in `.bbpm/bbpm.json`."""
    manifest = read_manifest(project_root)
    pdir = packages_dir(project_root)
    if not pdir.is_dir():
        return
    for entry in manifest.packages:
        install = package_install_path(project_root, entry)
        if not install.is_dir():
            warnings.warn(
                f"Package `{entry.name}` is listed but missing at {install}. Run `bbpm reset`.",
                UserWarning,
                stacklevel=2,
            )
            continue
        load_package_blocks(install, package_name=entry.name)


def prepare_runtime(project_root: Path | None) -> None:
    """Import built-in blocks, bundled foundation (if present), then project BBPM packages."""
    prepare_core()
    if project_root is not None:
        load_installed_packages(project_root)
