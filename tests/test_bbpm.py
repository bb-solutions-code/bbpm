"""BBPM integration tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FOBLOX = REPO_ROOT / "foblox"


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
    )

    subprocess.run(
        [sys.executable, "-m", "bbpm", "fetch", str(foblox_dir), "--path", str(project)],
        check=True,
        cwd=tmp_path,
    )

    subprocess.run(
        [sys.executable, "-m", "bbpm", "reset", "--path", str(project)],
        check=True,
        cwd=tmp_path,
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
        [sys.executable, "-m", "bbpm", "run", str(bbs), "--path", str(project)],
        check=True,
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert "completed" in proc.stdout
    assert "hello bbpm" in proc.stdout or "out1" in proc.stdout

    subprocess.run(
        [sys.executable, "-m", "bbpm", "cleanup", "foblox", "--path", str(project)],
        check=True,
        cwd=tmp_path,
    )

    manifest = json.loads((project / ".bbpm" / "bbpm.json").read_text(encoding="utf-8"))
    assert manifest["packages"] == []
