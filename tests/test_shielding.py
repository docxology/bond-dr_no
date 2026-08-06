"""Real-data tests for :mod:`dr_no.shielding` (gamma attenuation)."""

from __future__ import annotations

import math

import pytest

from dr_no.shielding import (
    MATERIAL_DENSITY_G_CM3,
    MATERIALS,
    half_value_layer,
    linear_attenuation_coefficient,
    mass_attenuation,
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
        linear_attenuation_coefficient(0.04, "lead")  # below the 0.05 floor
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


# --- Round-2 (2026-08-06): the attenuation table must cover every library line ---
# C1 in TODO.md: the table's ceiling was 2.0 MeV, so shielding could not be
# computed for Tl-208's 2614.53 keV line — the library's strongest high-energy
# emitter — without raising. The table now extends to 3.0 MeV; these tests pin
# that the ceiling brackets every gamma line in the isotope library and that
# mass_attenuation returns a finite, positive value for each.


def test_every_library_gamma_line_is_covered_by_the_attenuation_table() -> None:
    """No isotope line may fall off the end of the mass-attenuation table.

    Before the round-2 fix this raised for Tl-208 at 2614.53 keV
    (``ValueError: energy 2.61453 MeV is outside the table range [0.1, 2.0]``),
    silently denying a shielding answer for the library's strongest high-energy
    emitter. Iterating every line for every material makes that regression fail.
    """
    from dr_no.isotope_profiles import isotope_library, total_gamma_lines

    assert total_gamma_lines() >= 1
    line_mev_list: list[float] = []
    for profile in isotope_library().values():
        for energy_kev, _ in profile.gamma_lines:
            line_mev_list.append(energy_kev / 1000.0)
    assert line_mev_list  # non-empty library

    for material in MATERIALS:
        for energy_mev in line_mev_list:
            value = mass_attenuation(energy_mev, material)
            assert value > 0.0, f"non-positive mu/rho for {material} at {energy_mev} MeV"
            assert value < 1e6, f"implausibly large mu/rho: {value}"


def test_library_hottest_line_is_covered_and_finite() -> None:
    """Tl-208's 2614.53 keV line specifically: the C1 motivating case."""
    from dr_no.isotope_profiles import isotope_library

    tl = isotope_library()["Tl-208"]
    hot_mev = max(e for e, _ in tl.gamma_lines) / 1000.0
    assert hot_mev == pytest.approx(2.61453)
    for material in MATERIALS:
        value = mass_attenuation(hot_mev, material)
        assert 0.0 < value < 1.0, f"{material}: {value}"
