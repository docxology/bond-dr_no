"""Subprocess smoke tests for the thin CRAB KEY CLI scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def test_run_mission_full_exits_zero() -> None:
    proc = _run_script("run_mission.py", "full")
    assert proc.returncode == 0, proc.stderr
    assert "lessons" in proc.stdout


def test_run_mission_brief_exits_zero() -> None:
    proc = _run_script("run_mission.py", "brief")
    assert proc.returncode == 0, proc.stderr
    assert "CRAB KEY" in proc.stdout


def test_run_mission_unknown_exits_two() -> None:
    proc = _run_script("run_mission.py", "bogus")
    assert proc.returncode == 2


def test_z_generate_manuscript_variables_writes_json() -> None:
    proc = _run_script("z_generate_manuscript_variables.py")
    assert proc.returncode == 0, proc.stderr
    path = ROOT / "output" / "data" / "manuscript_variables.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["DRNO_CODENAME"] == "CRAB KEY"
    assert "NUM_ISOTOPES" in data
    # Resolved manuscript copy must exist and contain no raw tokens.
    resolved = ROOT / "output" / "manuscript" / "00_abstract.md"
    assert resolved.is_file()
    assert "{{" not in resolved.read_text(encoding="utf-8")


def test_scripts_write_under_gitignored_output() -> None:
    # Ensures exploratory runs leave the git tree clean: output/ is ignored.
    assert "output" in (ROOT / ".gitignore").read_text(encoding="utf-8")
