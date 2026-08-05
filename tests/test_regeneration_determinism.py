"""Regeneration determinism — the gate that binds the byte-identical claim.

The manuscript (§6.2), `README.md`, and `docs/testing_philosophy.md` all state
that regenerating CRAB KEY's artifacts reproduces them byte for byte. That
claim was false for a long time and no test noticed: `generate_variables()`
hydrated a `GENERATION_TIMESTAMP` from `datetime.now()` straight into
`output/data/manuscript_variables.json` and into the resolved
`output/manuscript/06_reproducibility.md`, so every rerun wrote different
bytes.

It survived because the only assertion touching the token was a shape check:
`test_generate_variables_returns_expected_tokens` asserted the key was present
and its value non-empty. An ISO-8601 wall-clock string passes both, forever. A
frozen-clock test would have been no better — pinning `now` proves the
formatter is a function of its input; it cannot see that the input is a clock.

The only test that can fail on this class of breach is one that runs the real
generator twice, on the real clock, and diffs the bytes actually written. That
is what this module does — no injection, no freezing, a deliberate sleep
between the runs so any clock-derived value would differ.

Scope: every persisted artifact the byte-identical claim covers — the token
map, the resolved manuscript sections, and the mission report.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"

#: Gap between the two regeneration runs. Long enough that any second-resolution
#: clock value (the exact granularity the removed `GENERATION_TIMESTAMP` used)
#: is guaranteed to differ between them.
_INTER_RUN_DELAY_S = 1.2


def _run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def _digest_tree(root: Path, patterns: tuple[str, ...]) -> dict[str, str]:
    """SHA-256 per file, keyed by path relative to ``root``.

    Hashes bytes, not decoded text, so an encoding or line-ending change counts
    as drift too.
    """
    digests: dict[str, str] = {}
    for pattern in patterns:
        for path in sorted(root.rglob(pattern)):
            if path.is_file():
                digests[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def _regenerate_and_digest() -> dict[str, str]:
    proc = _run_script("z_generate_manuscript_variables.py")
    assert proc.returncode == 0, proc.stderr
    digests = _digest_tree(OUTPUT, ("*.json", "*.md"))
    # A vacuous comparison of two empty dicts would pass forever. Assert the
    # generator actually persisted the artifacts the claim is about.
    assert "data/manuscript_variables.json" in digests, digests
    assert "manuscript/06_reproducibility.md" in digests, digests
    assert len(digests) >= 10, f"regeneration wrote only {len(digests)} artifacts: {digests}"
    return digests


def test_manuscript_regeneration_is_byte_identical_across_runs() -> None:
    """Two real regenerations, a real second apart, must write identical bytes."""
    first = _regenerate_and_digest()
    time.sleep(_INTER_RUN_DELAY_S)
    second = _regenerate_and_digest()

    assert first.keys() == second.keys(), (
        f"regeneration produced a different artifact set: {sorted(set(first) ^ set(second))}"
    )
    drifted = sorted(name for name in first if first[name] != second[name])
    assert drifted == [], f"artifacts changed between identical regenerations: {drifted}"


def test_mission_report_is_byte_identical_across_runs() -> None:
    """The rendered mission report carries no run-varying bytes either."""
    first = _run_script("run_mission.py", "full")
    assert first.returncode == 0, first.stderr
    time.sleep(_INTER_RUN_DELAY_S)
    second = _run_script("run_mission.py", "full")
    assert second.returncode == 0, second.stderr
    assert first.stdout, "mission report was empty — comparison would be vacuous"
    assert first.stdout == second.stdout


def test_no_persisted_artifact_contains_a_current_wall_clock_date() -> None:
    """Belt and braces: today's date must not appear anywhere under ``output/``.

    The byte-comparison above is the primary gate. This one names the failure
    mode explicitly, so a reintroduced timestamp reports *why* rather than only
    that two hashes differ.
    """
    _regenerate_and_digest()
    today = time.strftime("%Y-%m-%d", time.gmtime())
    offenders = [
        str(path.relative_to(ROOT))
        for pattern in ("*.json", "*.md")
        for path in sorted(OUTPUT.rglob(pattern))
        if path.is_file() and today in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"wall-clock date {today} persisted into: {offenders}"
