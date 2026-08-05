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
        "MISSION_SEED",
        "NUM_ISOTOPES",
        "NUM_GAMMA_LINES",
        "NUM_DECAY_CHAINS",
        "DECAY_CHAIN_NAMES_CSV",
        "NUM_SHIELDING_MATERIALS",
        "SHIELDING_MATERIALS_CSV",
        "NUM_THREAT_BANDS",
        "THREAT_BANDS_CSV",
        "LIBRARY_MIN_LINE_KEV",
        "LIBRARY_MAX_LINE_KEV",
        "DETECTOR_ACQUISITION_S",
        "DETECTOR_BINS",
        "SOURCE_MIXTURE_CSV",
        "PLUME_SOURCE_Q_BQ_S",
        "PLUME_STABILITY_CLASS",
        "ACTION_CONCENTRATION_BQ_M3",
        "NUM_FACILITIES",
        "FACILITY_NAMES_CSV",
        "DETECTED_PEAKS",
        "TOP_ISOTOPE",
        "QUANTIFIED_LINE",
        "PARENT_HALF_LIFE_DAYS",
        "PARENT_FRACTION_REMAINING_PCT",
        "CALIBRATION_R2",
        "CALIBRATION_GAIN",
        "MDA_BQ",
        "HVL_CM",
        "TVL_CM",
        "TRANSMISSION_SHIELD_PCT",
        "EXTERNAL_DOSE_PROBE_MSV_H",
        "GAMMA_CONSTANT_PROBE",
        "PEAK_CONCENTRATION_BQ_M3",
        "ISLAND_THREAT",
        "DOWNWIND_EXTENT_M",
        "CONTAINMENT_ACTIONS_CSV",
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


def test_import_version_missing_module_raises() -> None:
    """A missing declared dependency is an error, not an empty version string.

    Returning "" here would put `numpy ` with no version into the
    reproducibility section and pass every gate.
    """
    with pytest.raises(ModuleNotFoundError):
        mv._import_version("no_such_module_xyz")


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


def test_every_generated_token_is_used_somewhere() -> None:
    """The reverse direction: no token is generated that no section consumes.

    Without this, a renamed token leaves its predecessor in the map forever and
    the forward gate above stays green while the manuscript quietly stops
    reporting it.
    """
    variables = mv.generate_variables()
    used: set[str] = set()
    for source in sorted((PACKAGE_ROOT / "manuscript").glob("[0-9][0-9]_*.md")):
        used.update(TOKEN_RE.findall(source.read_text(encoding="utf-8")))
    orphans = set(variables) - used
    assert not orphans, f"generated tokens no manuscript section uses: {sorted(orphans)}"


def test_results_prose_has_no_hand_authored_metrics() -> None:
    """No bare numeral may appear in the results narrative.

    Section 3 is where hand-authored numbers do the most damage, because they
    read as measurements. Every quantity there must arrive as a token. Numerals
    inside image paths, figure labels, section numbers, and inline maths are
    stripped before the check; anything left is prose.
    """
    text = (PACKAGE_ROOT / "manuscript" / "03_results.md").read_text(encoding="utf-8")
    stripped = TOKEN_RE.sub("<TOKEN>", text)
    stripped = re.sub(r"!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?", "", stripped)  # figures
    stripped = re.sub(r"\[@[^\]]*\]", "", stripped)  # crossrefs
    stripped = re.sub(r"`[^`]*`", "", stripped)  # inline code
    stripped = re.sub(r"\$[^$]*\$", "", stripped)  # inline maths
    stripped = re.sub(r"(?m)^#{1,6} .*$", "", stripped)  # headings (numbered)
    leftovers = re.findall(r"(?<![\w/.-])\d[\d.,]*", stripped)
    assert not leftovers, f"hand-authored numerals in results prose: {leftovers}"


def test_scenario_tokens_track_the_config(tmp_path: Path) -> None:
    """Editing the declared scenario moves the token values.

    Tokens that were computed once and frozen would satisfy every other test in
    this file while reporting a scenario the package no longer runs.
    """
    original = (PACKAGE_ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8")
    edited = tmp_path / "config.yaml"
    edited.write_text(
        original.replace("wind_speed_m_s: 3.0", "wind_speed_m_s: 9.0"), encoding="utf-8"
    )
    base = mv.generate_variables()
    moved = mv.generate_variables(config_path=edited)
    assert base["PLUME_WIND_SPEED_M_S"] == "3"
    assert moved["PLUME_WIND_SPEED_M_S"] == "9"
    # A faster wind dilutes the plume, so the reported concentration must drop.
    assert float(moved["PEAK_CONCENTRATION_BQ_M3"]) < float(base["PEAK_CONCENTRATION_BQ_M3"])


def test_library_line_bounds_are_the_real_extremes() -> None:
    from dr_no.isotope_profiles import isotope_library

    variables = mv.generate_variables()
    energies = [e for p in isotope_library().values() for e, _ in p.gamma_lines]
    assert float(variables["LIBRARY_MIN_LINE_KEV"]) == pytest.approx(min(energies))
    assert float(variables["LIBRARY_MAX_LINE_KEV"]) == pytest.approx(max(energies))


def test_library_line_bounds_raises_on_empty_library(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mv, "isotope_library", dict)
    with pytest.raises(ValueError, match="no gamma lines"):
        mv._library_line_bounds()


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.0, "0"),
        (1000.0, "1000"),  # regression: a bare rstrip("0") yielded "1"
        (1.0, "1"),
        (3.9868, "3.99"),
        (0.001, "0.001"),
        (400000.0, r"$4.00\times10^{5}$"),
        (2.0e6, r"$2.00\times10^{6}$"),
        (2.832e-8, r"$2.83\times10^{-8}$"),
    ],
)
def test_sci_formatting(value: float, expected: str) -> None:
    """Magnitudes render readably; decimal-range values never lose digits."""
    assert mv._sci(value) == expected


def test_sci_never_truncates_an_integral_magnitude() -> None:
    """Round-trip check across decades: the formatted value must reparse equal."""
    for exponent in range(-6, 9):
        value = 1.5 * (10.0**exponent)
        rendered = mv._sci(value)
        numeric = rendered.replace("$", "").replace(r"\times10^{", "e").replace("}", "")
        assert float(numeric) == pytest.approx(value, rel=1e-2), rendered


def test_threshold_verdict_reports_a_null_result_as_null() -> None:
    """A zero extent must read as "never reached", not as a very short strip.

    The prose used to presuppose an exceedance ("stays above the threshold out
    to X m"), so a zero X rendered as a measurement of a contaminated strip of
    zero length rather than as the absence of any exceedance.
    """
    assert mv._threshold_verdict(0.0) == "never reaches that level at any downwind distance"
    assert mv._threshold_verdict(-1.0) == "never reaches that level at any downwind distance"


def test_threshold_verdict_reports_an_exceedance_when_there_is_one() -> None:
    """The other branch: a positive extent must not read as a null result."""
    verdict = mv._threshold_verdict(318.0)
    assert "never" not in verdict
    assert verdict == "stays at or above it from the ground-level maximum outward"


def test_threshold_verdict_token_tracks_the_scenario(tmp_path: Path) -> None:
    """The token is derived from the computed extent, not frozen.

    Loosening the declared action threshold far enough must flip the rendered
    clause — a value pasted once and never recomputed would not move.
    """
    import yaml

    config = mv.load_manuscript_config()
    strict = mv.generate_variables()
    assert strict["ACTION_THRESHOLD_VERDICT"] == (
        "never reaches that level at any downwind distance"
    )

    config["mission"]["action_concentration_bq_m3"] = 1.0
    loosened_path = tmp_path / "config.yaml"
    loosened_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    loosened = mv.generate_variables(config_path=loosened_path)
    assert loosened["ACTION_THRESHOLD_VERDICT"] == (
        "stays at or above it from the ground-level maximum outward"
    )
    assert float(loosened["DOWNWIND_EXTENT_M"]) > 0.0
