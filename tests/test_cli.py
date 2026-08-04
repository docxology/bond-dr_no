"""In-process tests for the CRAB KEY CLI (:mod:`dr_no.cli`).

Cli coverage must be exercised in-process (not only via subprocess) so the
lines count toward the coverage gate.
"""

from __future__ import annotations

import pytest

from dr_no import cli


def _run(capsys: pytest.CaptureFixture[str], *phases: str) -> int:
    code = cli.main(list(phases))
    capsys.readouterr()  # drain
    return code


def test_brief(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["brief"]) == 0
    out = capsys.readouterr().out
    assert "CRAB KEY" in out


def test_recon(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["recon"]) == 0
    out = capsys.readouterr().out
    assert "isotope-library" in out or "goal" in out


def test_plan(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["plan"]) == 0
    assert "assess" in capsys.readouterr().out


def test_execute(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["execute"]) == 0
    out = capsys.readouterr().out
    assert "top_isotope" in out


def test_debrief(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["debrief"]) == 0
    out = capsys.readouterr().out
    assert "lessons" in out


def test_full_default(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main([]) == 0  # default phase = full
    out = capsys.readouterr().out
    assert "lessons" in out


def test_render_writes_figures(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["render"]) == 0
    out = capsys.readouterr().out
    assert "gamma_spectrum" in out
    assert "plume_field" in out


def test_unknown_phase(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["bogus"]) == 2
    assert "usage" in capsys.readouterr().out.lower()


def test_run_phase_unknown() -> None:
    from dr_no.mission import MissionProvider

    assert cli.run_phase("nope", MissionProvider()) == 1
