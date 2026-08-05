"""Real-data tests for :mod:`dr_no.shielding` (gamma attenuation)."""

from __future__ import annotations

import math

import pytest

from dr_no.shielding import (
    MATERIAL_DENSITY_G_CM3,
    MATERIALS,
    half_value_layer,
    linear_attenuation_coefficient,
    required_shield_thickness,
    tenth_value_layer,
    transmission_factor,
)


def test_materials() -> None:
    assert "lead" in MATERIALS
    assert "iron" in MATERIALS
    assert "concrete" in MATERIALS
    assert "water" in MATERIALS


def test_densities() -> None:
    assert MATERIAL_DENSITY_G_CM3["lead"] == pytest.approx(11.34)
    assert MATERIAL_DENSITY_G_CM3["water"] == pytest.approx(1.0)


def test_linear_attenuation_lead_662() -> None:
    mu = linear_attenuation_coefficient(0.662, "lead")
    # mu/rho = 0.113 cm^2/g at 662 keV; rho_lead = 11.34 g/cm^3.
    assert mu == pytest.approx(0.113 * 11.34, rel=1e-6)


def test_linear_attenuation_at_table_point() -> None:
    # 1.0 MeV is an exact table row for iron.
    mu = linear_attenuation_coefficient(1.0, "iron")
    assert mu == pytest.approx(0.0599 * 7.87, rel=1e-6)


def test_linear_attenuation_interpolates_between_rows() -> None:
    mu_mid = linear_attenuation_coefficient(0.8, "lead")
    mu_lo = linear_attenuation_coefficient(0.662, "lead")
    mu_hi = linear_attenuation_coefficient(1.0, "lead")
    assert mu_lo > mu_mid > mu_hi  # attenuation falls as energy rises


def test_transmission_factor_zero_thickness() -> None:
    assert transmission_factor(0.662, 0.0, "lead") == pytest.approx(1.0)


def test_transmission_factor_monotonic() -> None:
    t1 = transmission_factor(0.662, 1.0, "lead")
    t2 = transmission_factor(0.662, 2.0, "lead")
    assert 0.0 < t2 < t1 < 1.0


def test_transmission_matches_exponential() -> None:
    mu = linear_attenuation_coefficient(0.662, "lead")
    assert transmission_factor(0.662, 3.0, "lead") == pytest.approx(math.exp(-mu * 3.0), rel=1e-9)


def test_half_value_layer_halves() -> None:
    hvl = half_value_layer(0.662, "lead")
    assert transmission_factor(0.662, hvl, "lead") == pytest.approx(0.5, rel=1e-9)
    # Literature: ~0.55 cm of lead at 662 keV.
    assert 0.4 < hvl < 0.7


def test_tenth_value_layer_relation() -> None:
    hvl = half_value_layer(0.662, "lead")
    tvl = tenth_value_layer(0.662, "lead")
    assert tvl == pytest.approx(hvl * math.log(10.0) / math.log(2.0), rel=1e-9)


def test_tenth_vs_half_value() -> None:
    hvl = half_value_layer(1.332, "concrete")
    tvl = tenth_value_layer(1.332, "concrete")
    assert tvl > hvl


def test_required_shield_thickness_zero_when_under_limit() -> None:
    assert required_shield_thickness(0.662, "lead", 1.0, 5.0) == pytest.approx(0.0)


def test_required_shield_thickness_positive() -> None:
    x = required_shield_thickness(0.662, "lead", 100.0, 1.0)
    assert x > 0
    # Verify it actually reduces transmission to 100:1.
    assert transmission_factor(0.662, x, "lead") == pytest.approx(0.01, rel=1e-6)


def test_required_shield_thickness_grows_with_dose() -> None:
    x_small = required_shield_thickness(0.662, "lead", 10.0, 1.0)
    x_large = required_shield_thickness(0.662, "lead", 100.0, 1.0)
    assert x_large > x_small


def test_required_shield_thickness_validation() -> None:
    with pytest.raises(ValueError):
        required_shield_thickness(0.662, "lead", -1.0, 1.0)
    with pytest.raises(ValueError):
        required_shield_thickness(0.662, "lead", 10.0, 0.0)
    with pytest.raises(ValueError):
        required_shield_thickness(0.662, "lead", 10.0, -1.0)


def test_error_branches() -> None:
    with pytest.raises(ValueError):
        linear_attenuation_coefficient(0.05, "lead")  # below table range
    with pytest.raises(ValueError):
        linear_attenuation_coefficient(5.0, "lead")  # above table range
    with pytest.raises(KeyError):
        linear_attenuation_coefficient(0.662, "unobtainium")
    with pytest.raises(KeyError):
        linear_attenuation_coefficient(0.662, "lead_")  # bad density lookup
    with pytest.raises(ValueError):
        transmission_factor(0.662, -1.0, "lead")


def test_linear_attenuation_unknown_material() -> None:
    with pytest.raises(KeyError):
        linear_attenuation_coefficient(0.662, "concrete_")
