"""Fetch BBScript packages from Git or local directories."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .bbpackage import read_package_name
from .errors import BBPMError
from .fsutil import ignore_git, safe_rmtree
from .git import git_clone
from .manifest import Manifest, PackageEntry, read_manifest, write_manifest
from .paths import packages_dir


def _install_rel_path(name: str) -> str:
    return f"packages/{name}"


def normalize_local_path_for_manifest(project_root: Path, src: Path) -> str:
    src = src.resolve()
    proj = project_root.resolve()
    try:
        return str(src.relative_to(proj)).replace("\\", "/")
    except ValueError:
        return str(src)


def resolve_local_path(project_root: Path, path_str: str) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p.resolve()
    return (project_root / p).resolve()


def _package_names(manifest: Manifest) -> set[str]:
    return {p.name for p in manifest.packages}


def fetch_git(
    project_root: Path,
    url: str,
    *,
    ref: str | None = None,
) -> PackageEntry:
    """Clone URL into `.bbpm/packages/<name>/` and append manifest entry."""
    manifest = read_manifest(project_root)
    dest_root = packages_dir(project_root)
    dest_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="bbpm-git-") as tmp:
        clone_dir = Path(tmp) / "src"
        git_clone(url, clone_dir, ref)
        name = read_package_name(clone_dir)
        if name in _package_names(manifest):
            raise BBPMError(
                f"Package `{name}` is already in the manifest. Use `bbpm cleanup {name}` first or re-init."
            )
        final = dest_root / name
        if final.exists():
            safe_rmtree(final)
        shutil.move(str(clone_dir), str(final))

    entry = PackageEntry(
        name=name,
        source={"type": "git", "url": url.strip(), "ref": ref},
        path=_install_rel_path(name),
    )
    manifest.packages = [p for p in manifest.packages if p.name != name]
    manifest.packages.append(entry)
    write_manifest(project_root, manifest)
    return entry


def fetch_local(
    project_root: Path,
    src: Path,
) -> PackageEntry:
    """Copy a local package tree into `.bbpm/packages/<name>/`."""
    src = src.resolve()
    if not src.is_dir():
        raise BBPMError(f"Local path is not a directory: {src}")
    manifest = read_manifest(project_root)
    name = read_package_name(src)
    if name in _package_names(manifest):
        raise BBPMError(
            f"Package `{name}` is already in the manifest. Use `bbpm cleanup {name}` first."
        )

    dest_root = packages_dir(project_root)
    dest_root.mkdir(parents=True, exist_ok=True)
    final = dest_root / name
    if final.exists():
        safe_rmtree(final)
    shutil.copytree(src, final, ignore=ignore_git)

    path_for_manifest = normalize_local_path_for_manifest(project_root, src)
    entry = PackageEntry(
        name=name,
        source={"type": "local", "path": path_for_manifest},
        path=_install_rel_path(name),
    )
    manifest.packages = [p for p in manifest.packages if p.name != name]
    manifest.packages.append(entry)
    write_manifest(project_root, manifest)
    return entry


def refetch_entry(project_root: Path, entry: PackageEntry) -> None:
    """Re-download or re-copy a single manifest entry into `entry.path`."""
    dest = project_root / ".bbpm" / Path(*entry.path.split("/"))
    if dest.exists():
        safe_rmtree(dest)
    st = entry.source.get("type")
    if st == "git":
        url = entry.source.get("url")
        ref = entry.source.get("ref")
        if not isinstance(url, str):
            raise BBPMError(f"Package `{entry.name}`: invalid git source.")
        git_clone(url, dest, ref if isinstance(ref, str) else None)
    elif st == "local":
        lp = entry.source.get("path")
        if not isinstance(lp, str):
            raise BBPMError(f"Package `{entry.name}`: invalid local source.")
        src = resolve_local_path(project_root, lp)
        if not src.is_dir():
            raise BBPMError(f"Package `{entry.name}`: local path not found: {src}")
        shutil.copytree(src, dest)
    else:
        raise BBPMError(f"Package `{entry.name}`: unknown source type {st!r}.")


def reset_all(project_root: Path) -> None:
    """Clear `.bbpm/packages` and re-fetch every package from the manifest."""
    manifest = read_manifest(project_root)
    pdir = packages_dir(project_root)
    if pdir.exists():
        safe_rmtree(pdir)
    pdir.mkdir(parents=True, exist_ok=True)
    for entry in list(manifest.packages):
        refetch_entry(project_root, entry)
