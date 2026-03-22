"""Git helpers for cloning package sources."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .errors import BBPMError


def git_available() -> bool:
    return shutil.which("git") is not None


def git_clone(url: str, dest: Path, ref: str | None = None) -> None:
    if not git_available():
        raise BBPMError(
            "`git` was not found on PATH. Install Git or use a local folder with `bbpm fetch <path>`."
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd: list[str] = ["git", "clone", "--depth", "1"]
    if ref:
        cmd.extend(["--branch", ref])
    cmd.extend([url, str(dest)])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        # Retry without shallow clone (some refs need full history)
        cmd2: list[str] = ["git", "clone"]
        if ref:
            cmd2.extend(["--branch", ref])
        cmd2.extend([url, str(dest)])
        proc2 = subprocess.run(cmd2, capture_output=True, text=True)
        if proc2.returncode != 0:
            err2 = (proc2.stderr or proc2.stdout or "").strip()
            raise BBPMError(f"git clone failed:\n{err}\n---\n{err2}")
    if not dest.is_dir():
        raise BBPMError(f"git clone did not create directory: {dest}")
