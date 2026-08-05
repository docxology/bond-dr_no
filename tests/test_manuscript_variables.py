"""Manuscript-variable hydration tests for CRAB KEY (dr_no).

Includes the live ``{{TOKEN}}`` cross-reference gate: every token that appears
in a numbered ``manuscript/[0-9]*.md`` section must exist in the
``generate_variables()`` map, so the manuscript can never reference a token the
code does not produce.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from dr_no import manuscript_variables as mv

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def test_generate_variables_returns_expected_tokens() -> None:
    variables = mv.generate_variables()
    for key in (
        "DRNO_TITLE",
        "DRNO_SUBTITLE",
        "DRNO_VERSION",
        "DRNO_FILM",
        "DRNO_CODENAME",
        "NUM_ISOTOPES",
        "NUM_GAMMA_LINES",
        "NUM_DECAY_CHAINS",
        "DECAY_CHAIN_NAMES_CSV",
        "I131_HALF_LIFE_DAYS",
        "I131_FRACTION_7D_PCT",
        "CALIBRATION_R2",
        "CALIBRATION_GAIN",
        "MDA_CS137_BQ",
        "HVL_LEAD_662_CM",
        "TVL_CONCRETE_1332_CM",
        "TRANSMISSION_LEAD_5CM_662_PCT",
        "EXTERNAL_DOSE_100M_MSV_H",
        "GAMMA_CONSTANT_CO60",
        "NUM_STABILITY_CLASSES",
        "STABILITY_CLASSES_CSV",
        "NUMPY_VERSION",
        "PYTHON_VERSION",
        "GENERATION_TIMESTAMP",
    ):
        assert key in variables
        assert variables[key] != ""


def test_generate_variables_stability_classes() -> None:
    variables = mv.generate_variables()
    assert variables["NUM_STABILITY_CLASSES"] == "6"
    assert "A" in variables["STABILITY_CLASSES_CSV"]
    assert "F" in variables["STABILITY_CLASSES_CSV"]


def test_generate_variables_require_outputs_raises_on_empty_library(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mv, "library_names", lambda: ())
    with pytest.raises(ValueError, match="isotope library is empty"):
        mv.generate_variables()


def test_load_manuscript_config_missing_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        mv.load_manuscript_config(tmp_path / "nope.yaml")


def test_load_manuscript_config_not_mapping(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("- 1\n- 2\n", encoding="utf-8")
    with pytest.raises(TypeError):
        mv.load_manuscript_config(bad)


def test_generate_variables_paper_not_mapping(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("paper: [1, 2]\n", encoding="utf-8")
    with pytest.raises(TypeError):
        mv.generate_variables(config_path=cfg)


def test_resolve_manuscript_tree_substitutes_and_writes(tmp_path: Path) -> None:
    mdir = tmp_path / "manuscript"
    mdir.mkdir()
    (mdir / "00_abstract.md").write_text(
        "Hello {{DRNO_CODENAME}} / {{NUM_ISOTOPES}}", encoding="utf-8"
    )
    variables = {"DRNO_CODENAME": "CRAB KEY", "NUM_ISOTOPES": "10"}
    out_dir, files = mv.resolve_manuscript_tree(
        variables, manuscript_dir=mdir, output_dir=tmp_path / "out"
    )
    rendered = (out_dir / "00_abstract.md").read_text(encoding="utf-8")
    assert "CRAB KEY / 10" in rendered
    assert files == ["00_abstract.md"]


def test_resolve_manuscript_tree_strict_leftover_token_raises(tmp_path: Path) -> None:
    mdir = tmp_path / "manuscript"
    mdir.mkdir()
    (mdir / "00_abstract.md").write_text("Value {{UNKNOWN_TOKEN}}", encoding="utf-8")
    with pytest.raises(ValueError, match="UNKNOWN_TOKEN"):
        mv.resolve_manuscript_tree(
            {"DRNO_CODENAME": "x"}, manuscript_dir=mdir, output_dir=tmp_path / "out"
        )


def test_resolve_manuscript_tree_draft_allows_leftover(tmp_path: Path) -> None:
    mdir = tmp_path / "manuscript"
    mdir.mkdir()
    (mdir / "00_abstract.md").write_text("Value {{UNKNOWN_TOKEN}}", encoding="utf-8")
    out_dir, _ = mv.resolve_manuscript_tree(
        {"DRNO_CODENAME": "x"}, manuscript_dir=mdir, output_dir=tmp_path / "out", strict=False
    )
    assert "{{UNKNOWN_TOKEN}}" in (out_dir / "00_abstract.md").read_text(encoding="utf-8")


def test_import_version_missing_module() -> None:
    assert mv._import_version("no_such_module_xyz") == ""


def test_import_version_present_module() -> None:
    assert mv._import_version("numpy") != ""


def test_every_manuscript_token_is_generated() -> None:
    """Live cross-reference gate: all prose tokens resolve from generate_variables()."""
    variables = mv.generate_variables()
    tokens: set[str] = set()
    for source in sorted((PACKAGE_ROOT / "manuscript").glob("[0-9][0-9]_*.md")):
        tokens.update(TOKEN_RE.findall(source.read_text(encoding="utf-8")))
    missing = tokens - set(variables)
    assert not missing, f"manuscript tokens missing from generate_variables(): {sorted(missing)}"
    assert tokens, "no manuscript tokens found — the gate is not exercising anything"
