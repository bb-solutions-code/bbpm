"""BBPM integration tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FOBLOX = REPO_ROOT / "foblox"


def _subprocess_env() -> dict[str, str]:
    """Prefer in-tree bbscript/bbpm (e.g. bbscript.__main__) over older site-packages installs."""
    env = os.environ.copy()
    prefix = str(REPO_ROOT)
    env["PYTHONPATH"] = prefix + os.pathsep + env.get("PYTHONPATH", "")
    return env


@pytest.fixture
def foblox_dir() -> Path:
    assert FOBLOX.is_dir(), f"Expected foblox at {FOBLOX}"
    return FOBLOX


def test_fetch_local_reset_cleanup_run(tmp_path: Path, foblox_dir: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()

    subprocess.run(
        [sys.executable, "-m", "bbpm", "init", "--no-foblox", "--path", str(project)],
        check=True,
        cwd=tmp_path,
        env=_subprocess_env(),
    )

    subprocess.run(
        [sys.executable, "-m", "bbpm", "fetch", str(foblox_dir), "--path", str(project)],
        check=True,
        cwd=tmp_path,
        env=_subprocess_env(),
    )

    subprocess.run(
        [sys.executable, "-m", "bbpm", "reset", "--path", str(project)],
        check=True,
        cwd=tmp_path,
        env=_subprocess_env(),
    )

    bbs = project / "hello.bbs"
    bbs.write_text(
        json.dumps(
            {
                "version": "2.0",
                "kind": "bbscript",
                "blocks": [
                    {
                        "id": "s1",
                        "block": "say",
                        "args": {"input": "hello bbpm"},
                        "output": "out1",
                    }
                ],
                "links": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, "-m", "bbscript", "run", str(bbs), "--path", str(project)],
        check=True,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=_subprocess_env(),
    )
    assert "completed" in proc.stdout
    assert "hello bbpm" in proc.stdout or "out1" in proc.stdout

    subprocess.run(
        [sys.executable, "-m", "bbpm", "cleanup", "foblox", "--path", str(project)],
        check=True,
        cwd=tmp_path,
        env=_subprocess_env(),
    )

    manifest = json.loads((project / ".bbpm" / "bbpm.json").read_text(encoding="utf-8"))
    assert manifest["packages"] == []


def test_bundled_packages_env_runs_without_bbpm_init(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, foblox_dir: Path
) -> None:
    """BBSCRIPT_BUNDLED_PACKAGES loads Foblox without a project .bbpm manifest."""
    monkeypatch.setenv("BBSCRIPT_BUNDLED_PACKAGES", str(foblox_dir))

    bbs = tmp_path / "hello.bbs"
    bbs.write_text(
        json.dumps(
            {
                "version": "2.0",
                "kind": "bbscript",
                "blocks": [
                    {
                        "id": "s1",
                        "block": "say",
                        "args": {"input": "bundled env"},
                        "output": "out1",
                    }
                ],
                "links": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, "-m", "bbscript", "run", str(bbs)],
        check=True,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=_subprocess_env(),
    )
    assert "completed" in proc.stdout
    assert "bundled env" in proc.stdout or "out1" in proc.stdout
