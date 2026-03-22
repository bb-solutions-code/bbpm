"""Load block entrypoints from installed BBPM packages."""

from __future__ import annotations

import importlib
import json
import re
import sys
import warnings
from pathlib import Path

from bbscript.core.registry import BLOCK_REGISTRY

from .bbpackage import read_root_manifest
from .errors import BBPMError
from .manifest import read_manifest, package_install_path
from .paths import packages_dir


def _warn_bbscript_dep(package_name: str, spec: str) -> None:
    warnings.warn(
        f"Package `{package_name}` declares bbscript dependency {spec!r}; "
        f"ensure it matches the installed bbscript.",
        UserWarning,
        stacklevel=2,
    )


def _semver_satisfied(installed: str, constraint: str) -> bool:
    """Very loose check for `>=0.2.0` style."""
    m = re.search(r">=\s*([\d.]+)", constraint)
    if not m:
        return True
    try:
        req = tuple(int(x) for x in m.group(1).split("."))
        cur = tuple(int(x) for x in installed.split(".")[:3])
        return cur >= req[: len(cur)]
    except ValueError:
        return True


def load_package_blocks(package_root: Path, *, package_name: str) -> None:
    """Add package root to sys.path and import each block entrypoint module."""
    root = package_root.resolve()
    data = read_root_manifest(root)
    deps = data.get("dependencies") or {}
    if isinstance(deps, dict):
        bb = deps.get("bbscript")
        if isinstance(bb, str):
            try:
                from importlib.metadata import version

                ver = version("bbscript")
                if not _semver_satisfied(str(ver), bb):
                    _warn_bbscript_dep(package_name, bb)
            except Exception:
                _warn_bbscript_dep(package_name, bb)

    blocks = data.get("blocks")
    if not isinstance(blocks, list):
        raise BBPMError(f"Package `{package_name}`: root manifest has no `blocks` array.")

    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    for rel in blocks:
        if not isinstance(rel, str) or not rel.strip():
            continue
        block_manifest_path = root.joinpath(*rel.split("/"))
        if not block_manifest_path.is_file():
            raise BBPMError(f"Package `{package_name}`: missing block file {rel}")
        try:
            bm = json.loads(block_manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise BBPMError(f"Invalid JSON in {block_manifest_path}: {e}") from e
        entrypoint = bm.get("entrypoint")
        if not isinstance(entrypoint, str) or not entrypoint.strip():
            raise BBPMError(f"{block_manifest_path}: missing `entrypoint`.")
        block_id = bm.get("block_id")
        if isinstance(block_id, str) and block_id in BLOCK_REGISTRY:
            warnings.warn(
                f"Block `{block_id}` is already registered; loading from {package_name} may override.",
                UserWarning,
                stacklevel=2,
            )

        block_dir = block_manifest_path.parent
        stem = Path(entrypoint).stem
        mod_name = f"{block_dir.name}.{stem}"
        importlib.import_module(mod_name)


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
    """Import built-in blocks, then optional BBPM packages."""
    import bbscript.blocks  # noqa: F401

    if project_root is not None:
        load_installed_packages(project_root)
