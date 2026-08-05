"""Regression tests for defects found and fixed during the phase-5 review.

Each test here corresponds to a specific bug that shipped in an earlier
revision. They are grouped together deliberately: this file is the record of
what was actually wrong, so a future refactor that reintroduces any of these
fails with a message naming the original defect rather than a generic
assertion.

Real computation throughout, no mocks.
"""

from __future__ import annotations

import math

import pytest

from dr_no.island_assessment import (
    DetectedFacility,
    IslandAssessment,
    Meteorology,
    assess_island,
    containment_recommendation,
)
from dr_no.manuscript_variables import _import_version
from dr_no.plume_model import centerline_concentration, isopleth_extent
from dr_no.shielding import (
    MASS_ATTENUATION_CM2_G,
    MATERIAL_DENSITY_G_CM3,
    MATERIALS,
    mass_attenuation,
)

_PLUME = {"Q": 4.0e5, "u": 3.0, "stability": "D"}


# --- DEFECT: isopleth_extent bisected a non-monotonic profile ------------------


def test_isopleth_extent_is_exact_at_the_reported_distance() -> None:
    """The returned distance must actually sit on the threshold isopleth.

    The old single-bisection implementation, seeded at x = 1 m, returned 1.0 m
    for the canonical elevated release whose true 1000 Bq/m3 extent is ~10.9 m —
    a wrong headline number, silently.
    """
    threshold = 1000.0
    extent = isopleth_extent(threshold, H=10.0, **_PLUME)
    assert extent > 1.0, "regression: bisection collapsed onto its lower bracket"
    assert centerline_concentration(extent, H=10.0, **_PLUME) == pytest.approx(threshold, rel=1e-6)


def test_isopleth_extent_handles_the_elevated_release_peak() -> None:
    """An elevated release is ~0 at the stack and peaks downwind.

    Any threshold between the near-field value and the true peak must still
    yield a real extent. A near-field bracket check alone would report 0.0 here
    — "no contamination" over a contaminated area.
    """
    near_field = centerline_concentration(1.0, H=10.0, **_PLUME)
    extent = isopleth_extent(100.0, H=10.0, **_PLUME)
    assert near_field < 100.0, "test premise: near field must be below the threshold"
    assert extent > 0.0
    assert centerline_concentration(extent, H=10.0, **_PLUME) == pytest.approx(100.0, rel=1e-6)


def test_isopleth_extent_returns_zero_when_never_reached() -> None:
    """A threshold above the global maximum yields zero extent, not 1 m."""
    huge = 1.0e30
    assert isopleth_extent(huge, H=10.0, **_PLUME) == 0.0


def test_isopleth_extent_is_monotone_in_threshold() -> None:
    """A stricter threshold always reaches at least as far."""
    extents = [isopleth_extent(t, H=10.0, **_PLUME) for t in (1000.0, 100.0, 10.0, 1.0)]
    assert extents == sorted(extents), f"extent not monotone in threshold: {extents}"


def test_isopleth_extent_saturates_at_the_outer_bound() -> None:
    """A threshold met even at max_km returns max_km, not a bisected interior."""
    assert isopleth_extent(1.0e-12, H=10.0, max_km=5.0, **_PLUME) == pytest.approx(5000.0)


def test_isopleth_extent_rejects_bad_scan_size() -> None:
    with pytest.raises(ValueError, match="n_scan must be >= 2"):
        isopleth_extent(1.0, H=10.0, n_scan=1, **_PLUME)


def test_isopleth_extent_rejects_bad_steps() -> None:
    with pytest.raises(ValueError, match="steps must be >= 2"):
        isopleth_extent(1.0, H=10.0, steps=1, **_PLUME)


def test_isopleth_extent_rejects_nonpositive_threshold() -> None:
    with pytest.raises(ValueError, match="threshold must be positive"):
        isopleth_extent(0.0, H=10.0, **_PLUME)


# --- DEFECT: assess_island's warn_dose_rate_sv_s was accepted and ignored ------


def _facility(name: str = "dock", containment: str = "contained") -> DetectedFacility:
    return DetectedFacility(
        name=name,
        x_m=200.0,
        y_m=0.0,
        isotope_activities={"Am-241": 1.0e12},  # highly radiotoxic by inhalation
        containment=containment,
    )


def test_evacuation_threshold_parameter_is_actually_consumed() -> None:
    """Threading the threshold must change the recommendation.

    The old signature accepted ``warn_dose_rate_sv_s`` and never referenced it:
    a caller could pass any value and get identical output.
    """
    meteo = Meteorology(wind_speed_m_s=1.0, stability="F", release_height_m=0.0)
    lenient = assess_island([_facility()], meteo, source_Q=1.0e12, evacuation_dose_rate_sv_s=1.0e30)
    strict = assess_island([_facility()], meteo, source_Q=1.0e12, evacuation_dose_rate_sv_s=1.0e-30)
    assert strict.containment_actions["dock"] == "evacuation"
    assert lenient.containment_actions["dock"] != "evacuation"


def test_action_concentration_parameter_is_actually_consumed() -> None:
    """The action-concentration threshold must move both action and extent."""
    meteo = Meteorology(wind_speed_m_s=3.0, stability="D", release_height_m=0.0)
    loose = assess_island([_facility()], meteo, source_Q=4.0e5, action_concentration_bq_m3=1.0e30)
    tight = assess_island([_facility()], meteo, source_Q=4.0e5, action_concentration_bq_m3=1.0e-6)
    assert tight.downwind_contamination_m > loose.downwind_contamination_m


def test_containment_recommendation_rejects_nonpositive_thresholds() -> None:
    with pytest.raises(ValueError, match="evacuation dose-rate threshold must be positive"):
        containment_recommendation(1.0, 1.0, evacuation_dose_rate_sv_s=0.0)
    with pytest.raises(ValueError, match="action concentration threshold must be positive"):
        containment_recommendation(0.0, 1.0, action_concentration_bq_m3=0.0)


# --- DEFECT: overall_level and worst_threat were two fields, one fact ---------


def test_worst_threat_is_an_alias_not_a_second_field() -> None:
    """They can no longer disagree, because there is only one stored value."""
    meteo = Meteorology(wind_speed_m_s=3.0, stability="D", release_height_m=10.0)
    assessment = assess_island([_facility(containment="breached")], meteo, source_Q=4.0e5)
    assert assessment.worst_threat == assessment.overall_level
    assert "worst_threat" not in assessment.__dict__


def test_maximum_rank_raises_on_an_empty_island() -> None:
    """An undefined maximum is an error, not a silently wrong rank."""
    empty = IslandAssessment(
        overall_level="LOW", facilities={}, downwind_contamination_m=0.0, containment_actions={}
    )
    with pytest.raises(ValueError, match="no facilities were assessed"):
        empty.maximum_rank()


def test_empty_island_reports_the_floor_band() -> None:
    meteo = Meteorology(wind_speed_m_s=3.0, stability="D", release_height_m=0.0)
    assessment = assess_island([], meteo, source_Q=4.0e5)
    assert assessment.overall_level == "LOW"
    assert assessment.facilities == {}


# --- DEFECT: shielding used an assert that could never fire -------------------


def test_material_tables_cover_exactly_the_declared_materials() -> None:
    """The invariant the old ``assert table is not None`` gestured at.

    That assert was unreachable (the caller validated the material first) *and*
    would have been stripped under ``python -O``. The real invariant is that the
    density table and the attenuation table declare the same material set.
    """
    assert set(MASS_ATTENUATION_CM2_G) == set(MATERIAL_DENSITY_G_CM3) == set(MATERIALS)


def test_mass_attenuation_raises_on_unknown_material() -> None:
    with pytest.raises(KeyError, match="no mass-attenuation table"):
        mass_attenuation(0.662, "unobtainium")


def test_mass_attenuation_raises_outside_the_table_range() -> None:
    with pytest.raises(ValueError, match="outside the table range"):
        mass_attenuation(10.0, "lead")


def test_mass_attenuation_interpolates_between_bracketing_points() -> None:
    """Log-log interpolation must land between the bracketing table values."""
    lo, hi = MASS_ATTENUATION_CM2_G["lead"][0.5], MASS_ATTENUATION_CM2_G["lead"][0.662]
    mid = mass_attenuation(0.6, "lead")
    assert hi < mid < lo  # mu/rho decreases with energy in this range


def test_mass_attenuation_returns_exact_table_values() -> None:
    for energy, expected in MASS_ATTENUATION_CM2_G["iron"].items():
        assert mass_attenuation(energy, "iron") == pytest.approx(expected)


def test_mass_attenuation_is_log_log_linear() -> None:
    """Verify the stated interpolation scheme rather than merely its bounds."""
    e_lo, e_hi = 0.5, 0.662
    mu_lo = MASS_ATTENUATION_CM2_G["water"][e_lo]
    mu_hi = MASS_ATTENUATION_CM2_G["water"][e_hi]
    e_mid = math.exp(0.5 * (math.log(e_lo) + math.log(e_hi)))
    expected = math.exp(0.5 * (math.log(mu_lo) + math.log(mu_hi)))
    assert mass_attenuation(e_mid, "water") == pytest.approx(expected)


# --- DEFECT: _import_version swallowed ImportError ----------------------------


def test_import_version_raises_when_module_lacks_version() -> None:
    """A module with no ``__version__`` is an error, not an empty string."""
    with pytest.raises(AttributeError, match="exposes no __version__"):
        _import_version("pathlib")  # stdlib pathlib exposes no __version__
