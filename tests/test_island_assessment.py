"""Real-data tests for :mod:`dr_no.island_assessment` (Crab Key threat scoring)."""

from __future__ import annotations

import pytest

from dr_no.island_assessment import (
    INHALATION_DCF_SV_BQ,
    THREAT_LEVELS,
    THREAT_RANK,
    DetectedFacility,
    IslandAssessment,
    Meteorology,
    assess_island,
    containment_recommendation,
    dose_rate_from_concentration,
    facility_threat_level,
)


def test_threat_level_ordering() -> None:
    assert THREAT_LEVELS == ("LOW", "MODERATE", "HIGH", "SEVERE", "CRITICAL")
    assert THREAT_RANK["CRITICAL"] > THREAT_RANK["LOW"]


def test_dcf_contains_key_isotopes() -> None:
    for iso in ("Cs-137", "I-131", "Co-60", "Am-241"):
        assert iso in INHALATION_DCF_SV_BQ


def test_dose_rate_zero_concentration() -> None:
    assert dose_rate_from_concentration(0.0, {"Cs-137": 1.0}) == 0.0


def test_dose_rate_scales_with_concentration() -> None:
    r1 = dose_rate_from_concentration(100.0, {"Cs-137": 1.0})
    r2 = dose_rate_from_concentration(200.0, {"Cs-137": 1.0})
    assert r2 == pytest.approx(2.0 * r1, rel=1e-9)


def test_dose_rate_fraction_weighting() -> None:
    mixed = dose_rate_from_concentration(100.0, {"Cs-137": 0.5, "Co-60": 0.5})
    pure_cs = dose_rate_from_concentration(100.0, {"Cs-137": 1.0})
    # Co-60's DCF (1.0e-8) exceeds Cs-137's (4.6e-9), so a half/half mix lies
    # strictly between the two pure extremes.
    assert pure_cs < mixed
    assert mixed >= 0.5 * pure_cs


def test_dose_rate_validation() -> None:
    with pytest.raises(ValueError):
        dose_rate_from_concentration(-1.0, {"Cs-137": 1.0})
    with pytest.raises(ValueError):
        dose_rate_from_concentration(
            1.0,
            {},
        )
    with pytest.raises(ValueError):
        dose_rate_from_concentration(1.0, {"Cs-137": 1.0}, breathing_rate_m3_s=0.0)


def test_facility_threat_level_bands() -> None:
    assert facility_threat_level(1e-12, containment="contained") == "LOW"
    assert facility_threat_level(1.0, containment="contained") == "CRITICAL"


def test_facility_threat_level_breach_escalates() -> None:
    base = THREAT_LEVELS.index(facility_threat_level(1e-10, containment="contained"))
    breached = THREAT_LEVELS.index(facility_threat_level(1e-10, containment="breached"))
    assert breached == base + 1


def test_facility_threat_level_capped() -> None:
    assert facility_threat_level(1e12, containment="breached") == "CRITICAL"


def test_facility_threat_level_validation() -> None:
    with pytest.raises(ValueError):
        facility_threat_level(-1.0)
    with pytest.raises(ValueError):
        facility_threat_level(1.0, containment="other")


def test_containment_recommendation() -> None:
    assert containment_recommendation(1e-12, 1.0) == "none"
    assert containment_recommendation(1e-12, 5000.0) == "shelter"
    assert containment_recommendation(1e-8, 5000.0) == "evacuation"


def test_containment_recommendation_validation() -> None:
    with pytest.raises(ValueError):
        containment_recommendation(-1.0, 1.0)
    with pytest.raises(ValueError):
        containment_recommendation(1.0, -1.0)


def test_detected_facility_validation() -> None:
    with pytest.raises(ValueError):
        DetectedFacility("", 100.0, 0.0, {"Cs-137": 1.0}, "contained")
    with pytest.raises(ValueError):
        DetectedFacility("f", -1.0, 0.0, {"Cs-137": 1.0}, "contained")
    with pytest.raises(ValueError):
        DetectedFacility("f", 100.0, 0.0, {"Cs-137": 1.0}, "unknown")


def test_assess_island_return_shape_and_levels() -> None:
    meteo = Meteorology(wind_speed_m_s=3.0, stability="D")
    facilities = [
        DetectedFacility("dock", 500.0, 20.0, {"Cs-137": 2.0e6, "Co-60": 8.0e5}, "breached"),
        DetectedFacility("cave", 1500.0, -40.0, {"I-131": 1.0e7}, "contained"),
    ]
    assessment = assess_island(facilities, meteo, source_Q=4.0e5)
    assert isinstance(assessment, IslandAssessment)
    assert set(assessment.facilities) == {"dock", "cave"}
    assert assessment.overall_level in THREAT_LEVELS
    assert assessment.worst_threat in THREAT_LEVELS
    assert assessment.downwind_contamination_m >= 0
    assert set(assessment.containment_actions) == {"dock", "cave"}
    assert assessment.maximum_rank() >= 0


def test_assess_island_empty() -> None:
    meteo = Meteorology(wind_speed_m_s=3.0, stability="D")
    assessment = assess_island([], meteo, source_Q=4.0e5)
    assert assessment.facilities == {}
    assert assessment.overall_level == "LOW"


def test_assess_island_zero_activity_facility() -> None:
    meteo = Meteorology(wind_speed_m_s=3.0, stability="D")
    facilities = [DetectedFacility("quiet", 800.0, 0.0, {}, "contained")]
    assessment = assess_island(facilities, meteo, source_Q=4.0e5)
    assert assessment.facilities["quiet"] in THREAT_LEVELS


def test_facility_threat_level_validates_threshold_values() -> None:
    """Config-threshold tuples are validated, not trusted."""
    with pytest.raises(ValueError, match="dose thresholds must be positive"):
        facility_threat_level(1e-10, dose_thresholds=(1e-11, 1e-9, -1e-7, 1e-5))
    with pytest.raises(ValueError, match="dose thresholds must be strictly ascending"):
        facility_threat_level(1e-10, dose_thresholds=(1e-5, 1e-9, 1e-7, 1e-11))
