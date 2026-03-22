"""BBPM CLI."""

from __future__ import annotations

from pathlib import Path

import typer

from .errors import BBPMError
from .fsutil import safe_rmtree
from .fetch import fetch_git, fetch_local, reset_all, resolve_local_path
from .load import prepare_runtime
from .manifest import empty_manifest, read_manifest, write_manifest
from .paths import DEFAULT_FOBLOX_GIT_URL, find_project_root, manifest_path
from bbscript.core.loader import load_bbs_document
from bbscript.core.runner import run_bbs_document

app = typer.Typer(help="BBScript Package Manager (bbpm).")


def _project_root(path: Path | None) -> Path:
    root = (path or Path.cwd()).resolve()
    if not root.is_dir():
        raise typer.BadParameter(f"Not a directory: {root}")
    return root


def _require_manifest(project_root: Path) -> None:
    if not manifest_path(project_root).is_file():
        raise typer.BadParameter(f"No .bbpm/bbpm.json in {project_root}. Run `bbpm init`.")


@app.command()
def init(
    path: Path = typer.Option(None, "--path", help="Project root (default: current directory)."),
    no_foblox: bool = typer.Option(False, "--no-foblox", help="Do not fetch the default Foblox package."),
    ref: str = typer.Option("main", "--ref", help="Git branch/tag for default Foblox fetch."),
) -> None:
    """Create `.bbpm/bbpm.json` and optionally fetch Foblox from GitHub."""
    project_root = _project_root(path)
    mp = manifest_path(project_root)
    if mp.is_file():
        typer.echo(f"Already initialized: {mp}", err=True)
        raise typer.Exit(code=1)
    project_root.joinpath(".bbpm").mkdir(parents=True, exist_ok=True)
    write_manifest(project_root, empty_manifest())
    typer.echo(f"Created {mp}")
    if not no_foblox:
        try:
            fetch_git(project_root, DEFAULT_FOBLOX_GIT_URL, ref=ref)
            typer.echo(f"Fetched Foblox from {DEFAULT_FOBLOX_GIT_URL} (ref={ref})")
        except BBPMError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(code=1) from e


@app.command()
def fetch(
    source: str = typer.Argument(..., help="Git URL or path to a local package directory."),
    path: Path = typer.Option(None, "--path", help="Project root (default: current directory)."),
    ref: str = typer.Option(None, "--ref", help="Git branch or tag (Git sources only)."),
) -> None:
    """Install a BBScript package from a Git URL or local folder into `.bbpm/packages/`."""
    project_root = _project_root(path)
    _require_manifest(project_root)
    try:
        if source.startswith("git@") or "://" in source:
            entry = fetch_git(project_root, source.strip(), ref=ref)
        else:
            src = resolve_local_path(project_root, source.strip())
            entry = fetch_local(project_root, src)
        typer.echo(f"Installed package `{entry.name}` -> .bbpm/{entry.path}")
    except BBPMError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from e


@app.command("reset")
def reset_cmd(
    path: Path = typer.Option(None, "--path", help="Project root (default: current directory)."),
) -> None:
    """Remove installed copies under `.bbpm/packages/` and re-fetch all packages from the manifest."""
    project_root = _project_root(path)
    _require_manifest(project_root)
    try:
        reset_all(project_root)
        typer.echo("Reset complete: all packages re-fetched.")
    except BBPMError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from e


@app.command()
def cleanup(
    package_name: str = typer.Argument(..., help="Package name as in the manifest."),
    path: Path = typer.Option(None, "--path", help="Project root (default: current directory)."),
) -> None:
    """Remove one package from the manifest and delete its files under `.bbpm/packages/`."""
    project_root = _project_root(path)
    _require_manifest(project_root)
    try:
        manifest = read_manifest(project_root)
        entry = next((p for p in manifest.packages if p.name == package_name), None)
        if entry is None:
            raise BBPMError(f"No package named `{package_name}` in the manifest.")
        manifest.packages = [p for p in manifest.packages if p.name != package_name]
        write_manifest(project_root, manifest)
        install = project_root / ".bbpm" / Path(*entry.path.split("/"))
        if install.exists():
            safe_rmtree(install)
        typer.echo(f"Removed package `{package_name}`.")
    except BBPMError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from e


@app.command("list")
def list_cmd(
    path: Path = typer.Option(None, "--path", help="Project root (default: current directory)."),
) -> None:
    """List packages registered in `.bbpm/bbpm.json`."""
    project_root = _project_root(path)
    _require_manifest(project_root)
    try:
        manifest = read_manifest(project_root)
        if not manifest.packages:
            typer.echo("(no packages)")
            return
        for p in manifest.packages:
            src = p.source
            st = src.get("type")
            if st == "git":
                typer.echo(f"- {p.name} (git {src.get('url')!r} ref={src.get('ref')!r})")
            elif st == "local":
                typer.echo(f"- {p.name} (local {src.get('path')!r})")
            else:
                typer.echo(f"- {p.name} ({st})")
    except BBPMError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from e


@app.command()
def run(
    bbs_path: Path = typer.Argument(..., help="Path to a .bbs file."),
    path: Path = typer.Option(
        None,
        "--path",
        help="BBScript project root containing .bbpm (default: discover from .bbs location).",
    ),
    execution_id: str = typer.Option(None, help="Optional execution id for events."),
    max_workers: int = typer.Option(8, help="Max parallel worker threads."),
) -> None:
    """Run a `.bbs` document with built-in blocks and installed BBPM packages."""
    bbs = bbs_path.resolve()
    if not bbs.is_file():
        typer.echo(f"File not found: {bbs}", err=True)
        raise typer.Exit(code=1)

    project_root: Path | None = None
    if path is not None:
        project_root = _project_root(path)
    else:
        project_root = find_project_root(bbs)

    try:
        prepare_runtime(project_root)
    except BBPMError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1) from e

    doc = load_bbs_document(bbs)
    result = run_bbs_document(doc, execution_id=execution_id, max_workers=max_workers)
    typer.echo(f"execution_status: {result.state.status.value}")
    if result.state.errors.get("__execution__"):
        typer.echo(f"error: {result.state.errors['__execution__']}")
    typer.echo("")
    typer.echo("final_context:")
    for k, v in result.context.items():
        if isinstance(v, str) and len(v) > 300:
            typer.echo(f"- {k}: {v[:300]}...")
        else:
            typer.echo(f"- {k}: {v}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
