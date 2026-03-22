"""bbpm.json manifest read/write."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, TypedDict

from .errors import BBPMError
from .paths import MANIFEST_NAME, bbpm_dir, manifest_path, packages_dir


class GitSourceDict(TypedDict, total=False):
    type: Literal["git"]
    url: str
    ref: str | None


class LocalSourceDict(TypedDict, total=False):
    type: Literal["local"]
    path: str


PackageSourceDict = GitSourceDict | LocalSourceDict


class PackageEntryDict(TypedDict, total=False):
    name: str
    source: PackageSourceDict
    path: str


class ManifestDict(TypedDict, total=False):
    schema_version: int
    packages: list[PackageEntryDict]


@dataclass
class PackageEntry:
    name: str
    source: dict[str, Any]
    path: str  # relative to .bbpm/, e.g. packages/foblox

    def to_dict(self) -> PackageEntryDict:
        return {"name": self.name, "source": self.source, "path": self.path}  # type: ignore[typeddict-item]


@dataclass
class Manifest:
    schema_version: int = 1
    packages: list[PackageEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "packages": [p.to_dict() for p in self.packages],
        }


def _parse_package(raw: dict[str, Any]) -> PackageEntry:
    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        raise BBPMError("Each package entry must have a non-empty string `name`.")
    src = raw.get("source")
    if not isinstance(src, dict):
        raise BBPMError(f"Package `{name}`: `source` must be an object.")
    st = src.get("type")
    if st == "git":
        url = src.get("url")
        if not isinstance(url, str) or not url.strip():
            raise BBPMError(f"Package `{name}`: git source needs `url`.")
        ref = src.get("ref")
        if ref is not None and not isinstance(ref, str):
            raise BBPMError(f"Package `{name}`: `ref` must be a string or omitted.")
        source: dict[str, Any] = {"type": "git", "url": url.strip(), "ref": ref}
    elif st == "local":
        lp = src.get("path")
        if not isinstance(lp, str) or not lp.strip():
            raise BBPMError(f"Package `{name}`: local source needs `path`.")
        source = {"type": "local", "path": lp.strip()}
    else:
        raise BBPMError(f"Package `{name}`: unknown source type `{st!r}`.")
    rel = raw.get("path")
    if not isinstance(rel, str) or not rel.strip():
        raise BBPMError(f"Package `{name}`: `path` must be set (relative to .bbpm/).")
    if ".." in Path(rel).parts or Path(rel).is_absolute():
        raise BBPMError(f"Package `{name}`: invalid `path` {rel!r}.")
    return PackageEntry(name=name.strip(), source=source, path=rel.strip().replace("\\", "/"))


def read_manifest(project_root: Path) -> Manifest:
    mp = manifest_path(project_root)
    if not mp.is_file():
        raise BBPMError(f"Manifest not found: {mp}. Run `bbpm init` first.")
    try:
        raw = json.loads(mp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise BBPMError(f"Invalid JSON in {mp}: {e}") from e
    if not isinstance(raw, dict):
        raise BBPMError(f"{MANIFEST_NAME} must be a JSON object.")
    ver = raw.get("schema_version", 1)
    if ver != 1:
        raise BBPMError(f"Unsupported schema_version: {ver!r} (expected 1).")
    pkgs_raw = raw.get("packages", [])
    if not isinstance(pkgs_raw, list):
        raise BBPMError("`packages` must be an array.")
    packages = [_parse_package(p) for p in pkgs_raw if isinstance(p, dict)]
    return Manifest(schema_version=1, packages=packages)


def write_manifest(project_root: Path, manifest: Manifest) -> None:
    bdir = bbpm_dir(project_root)
    bdir.mkdir(parents=True, exist_ok=True)
    mp = manifest_path(project_root)
    mp.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")


def empty_manifest() -> Manifest:
    return Manifest(schema_version=1, packages=[])


def ensure_manifest_file(project_root: Path) -> None:
    """Create `.bbpm/bbpm.json` if missing."""
    mp = manifest_path(project_root)
    if mp.is_file():
        return
    bbpm_dir(project_root).mkdir(parents=True, exist_ok=True)
    write_manifest(project_root, empty_manifest())


def package_install_path(project_root: Path, entry: PackageEntry) -> Path:
    return bbpm_dir(project_root).joinpath(*entry.path.split("/"))
