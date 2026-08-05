"""Real-data tests for :mod:`dr_no.dose_assessment` (external/inhalation/combined dose)."""

from __future__ import annotations

import pytest

from dr_no.dose_assessment import (
    BREATHING_RATE_M3_S,
    GAMMA_CONSTANT_MSV_M2_H_GBQ,
    INHALATION_DCF_SV_BQ,
    combined_dose_rate,
    dose_rate_from_concentration,
    external_dose_rate,
    integrated_dose,
    shielded_external_dose_rate,
    specific_gamma_constant,
)


def test_tables_contain_key_isotopes() -> None:
    for iso in ("Cs-137", "Co-60", "I-131", "Am-241"):
        assert iso in INHALATION_DCF_SV_BQ
        assert iso in GAMMA_CONSTANT_MSV_M2_H_GBQ


def test_specific_gamma_constant_co60() -> None:
    assert specific_gamma_constant("Co-60") == pytest.approx(0.354, rel=1e-9)


def test_specific_gamma_constant_unknown() -> None:
    with pytest.raises(KeyError):
        specific_gamma_constant("Zz-999")


def test_breathing_rate_positive() -> None:
    assert BREATHING_RATE_M3_S > 0


def test_external_dose_rate_one_gbq_metre() -> None:
    # 1 GBq Co-60 at 1 m: D = 0.354 * 1 / 1^2 = 0.354 mSv/h.
    assert external_dose_rate(1.0e9, 0.354, 1.0) == pytest.approx(0.354, rel=1e-9)


def test_external_dose_rate_inverse_square() -> None:
    d1 = external_dose_rate(1.0e9, 0.354, 1.0)
    d2 = external_dose_rate(1.0e9, 0.354, 2.0)
    assert d2 == pytest.approx(d1 / 4.0, rel=1e-9)


def test_external_dose_rate_validation() -> None:
    with pytest.raises(ValueError):
        external_dose_rate(-1.0, 0.354, 1.0)
    with pytest.raises(ValueError):
        external_dose_rate(1.0e9, -0.1, 1.0)
    with pytest.raises(ValueError):
        external_dose_rate(1.0e9, 0.354, 0.0)
    with pytest.raises(ValueError):
        external_dose_rate(1.0e9, 0.354, -5.0)


def test_shielded_external_dose_rate_full_transmission() -> None:
    shielded = shielded_external_dose_rate(1.0e9, 0.354, 1.0, transmission_factor=1.0)
    assert shielded == pytest.approx(0.354, rel=1e-9)


def test_shielded_external_dose_rate_halves() -> None:
    shielded = shielded_external_dose_rate(1.0e9, 0.354, 1.0, transmission_factor=0.5)
    assert shielded == pytest.approx(0.354 * 0.5, rel=1e-9)


def test_shielded_external_dose_rate_validation() -> None:
    with pytest.raises(ValueError):
        shielded_external_dose_rate(1.0e9, 0.354, 1.0, transmission_factor=-0.1)
    with pytest.raises(ValueError):
        shielded_external_dose_rate(1.0e9, 0.354, 1.0, transmission_factor=1.5)


def test_dose_rate_from_concentration_zero() -> None:
    assert dose_rate_from_concentration(0.0, {"Cs-137": 1.0}) == 0.0


def test_dose_rate_from_concentration_scales() -> None:
    r1 = dose_rate_from_concentration(10.0, {"Cs-137": 1.0})
    r2 = dose_rate_from_concentration(20.0, {"Cs-137": 1.0})
    assert r2 == pytest.approx(2.0 * r1, rel=1e-9)


def test_dose_rate_from_concentration_validation() -> None:
    with pytest.raises(ValueError):
        dose_rate_from_concentration(-1.0, {"Cs-137": 1.0})
    with pytest.raises(ValueError):
        dose_rate_from_concentration(1.0, {})
    with pytest.raises(ValueError):
        dose_rate_from_concentration(1.0, {"Cs-137": 1.0}, breathing_rate_m3_s=0.0)
    with pytest.raises(ValueError):
        dose_rate_from_concentration(1.0, {"Cs-137": 0.0})  # zero total fraction


def test_combined_dose_rate_sums() -> None:
    assert combined_dose_rate(2.0, 3.0) == pytest.approx(5.0)


def test_combined_dose_rate_validation() -> None:
    with pytest.raises(ValueError):
        combined_dose_rate(-1.0, 1.0)
    with pytest.raises(ValueError):
        combined_dose_rate(1.0, -1.0)


def test_integrated_dose() -> None:
    # 1e-9 Sv/s for 3600 s = 3.6e-6 Sv.
    assert integrated_dose(1.0e-9, 3600.0) == pytest.approx(3.6e-6, rel=1e-9)


def test_integrated_dose_validation() -> None:
    with pytest.raises(ValueError):
        integrated_dose(-1.0, 1.0)
    with pytest.raises(ValueError):
        integrated_dose(1.0, -1.0)
