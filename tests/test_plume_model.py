"""Real-data tests for :mod:`dr_no.plume_model` (Gaussian plume dispersion)."""

from __future__ import annotations

import numpy as np
import pytest

from dr_no.plume_model import (
    STABILITY_CLASSES,
    StabilitySpec,
    centerline_concentration,
    find_ground_level_max,
    gaussian_plume_concentration,
    grid_concentration,
    isopleth_extent,
    sigma_y,
    sigma_z,
)


def test_stability_classes() -> None:
    assert STABILITY_CLASSES == ("A", "B", "C", "D", "E", "F")


def test_stability_spec_validation() -> None:
    with pytest.raises(ValueError):
        StabilitySpec("Q", 0.1, 0.9, 0.1, 1.0, 0.0)


def test_sigma_y_grows_with_distance() -> None:
    assert sigma_y(100.0, "D") < sigma_y(1000.0, "D")


def test_sigma_z_grows_with_distance() -> None:
    assert sigma_z(100.0, "D") < sigma_z(1000.0, "D")


def test_sigma_size_reasonable() -> None:
    # FWHM-scale sanity: sigma at 1000 m under D should be on the order of tens of metres.
    sy = sigma_y(1000.0, "D")
    assert 10.0 < sy < 500.0


def test_sigma_units_in_metres() -> None:
    # At 500 m the horizontal sigma should be tens of metres, not fractions of a metre.
    assert sigma_y(500.0, "D") > 10.0


# --- Published-value binding -------------------------------------------------
#
# Values read from the Pasquill-Gifford dispersion curves as reproduced in
# Turner, *Workbook of Atmospheric Dispersion Estimates* (turner1994workbook) —
# the curves that Martin (1976) fitted. Tolerance is 15%, which is roughly the
# precision a log-log graph read supports.
#
# What this pins and what it does not: it constrains the *implementation's*
# arithmetic, units, and coefficient transcription against externally published
# numbers. It does not independently re-validate Martin's fit against the
# underlying tracer experiments — the fit is taken as published.

_PG_SIGMA_Y_M: dict[str, dict[float, float]] = {
    #        x = 100 m,  x = 500 m,  x = 1000 m
    "A": {100.0: 27.0, 500.0: 115.0, 1000.0: 213.0},
    "B": {100.0: 20.0, 500.0: 84.0, 1000.0: 156.0},
    "C": {100.0: 13.0, 500.0: 56.0, 1000.0: 104.0},
    "D": {100.0: 8.5, 500.0: 36.0, 1000.0: 68.0},
    "E": {100.0: 6.5, 500.0: 27.0, 1000.0: 50.5},
    "F": {100.0: 4.3, 500.0: 18.0, 1000.0: 34.0},
}

_PG_SIGMA_Z_M: dict[str, dict[float, float]] = {
    "A": {100.0: 14.0, 500.0: 124.0, 1000.0: 450.0},
    "B": {100.0: 11.0, 500.0: 51.0, 1000.0: 110.0},
    "C": {100.0: 7.5, 500.0: 32.0, 1000.0: 61.0},
    "D": {100.0: 4.7, 500.0: 18.5, 1000.0: 31.5},
    "E": {100.0: 3.5, 500.0: 13.0, 1000.0: 21.5},
    "F": {100.0: 2.3, 500.0: 8.3, 1000.0: 14.0},
}


@pytest.mark.parametrize("stability", STABILITY_CLASSES)
def test_sigma_y_matches_published_pasquill_gifford(stability: str) -> None:
    for x_m, expected in _PG_SIGMA_Y_M[stability].items():
        assert sigma_y(x_m, stability) == pytest.approx(expected, rel=0.15), (
            f"sigma_y({x_m} m, {stability}) is {sigma_y(x_m, stability):.3g} m; "
            f"published Pasquill-Gifford value is {expected} m"
        )


@pytest.mark.parametrize("stability", STABILITY_CLASSES)
def test_sigma_z_matches_published_pasquill_gifford(stability: str) -> None:
    for x_m, expected in _PG_SIGMA_Z_M[stability].items():
        assert sigma_z(x_m, stability) == pytest.approx(expected, rel=0.15), (
            f"sigma_z({x_m} m, {stability}) is {sigma_z(x_m, stability):.3g} m; "
            f"published Pasquill-Gifford value is {expected} m"
        )


@pytest.mark.parametrize("x_m", [100.0, 500.0, 1000.0, 5000.0])
def test_sigma_ordering_is_unstable_to_stable(x_m: float) -> None:
    """A (most unstable) must disperse most and F (most stable) least, in both axes.

    The physical ordering of the classes, which a coefficient table can lose
    without any monotonicity-in-x test noticing.
    """
    ys = [sigma_y(x_m, c) for c in STABILITY_CLASSES]
    zs = [sigma_z(x_m, c) for c in STABILITY_CLASSES]
    assert ys == sorted(ys, reverse=True), f"sigma_y not ordered A>...>F at {x_m} m: {ys}"
    assert zs == sorted(zs, reverse=True), f"sigma_z not ordered A>...>F at {x_m} m: {zs}"


@pytest.mark.parametrize("stability", STABILITY_CLASSES)
def test_sigma_is_strictly_positive_including_near_source(stability: str) -> None:
    """Martin's negative f_z offsets go non-positive inside ~17 m; the floor holds.

    A non-positive sigma would put a negative concentration into the report
    rather than raising.
    """
    for x_m in (0.0, 1.0, 5.0, 10.0, 20.0, 100.0, 50_000.0):
        assert sigma_y(x_m, stability) > 0.0
        assert sigma_z(x_m, stability) > 0.0


def test_sigma_negative_distance() -> None:
    with pytest.raises(ValueError):
        sigma_y(-1.0, "D")
    with pytest.raises(ValueError):
        sigma_z(-1.0, "D")


def test_sigma_unknown_stability() -> None:
    with pytest.raises(ValueError):
        sigma_y(100.0, "Z")
    with pytest.raises(ValueError):
        sigma_z(100.0, "Z")


def test_centerline_concentration_positive() -> None:
    c = centerline_concentration(500.0, Q=4.0e5, u=3.0, stability="D")
    assert c > 0


def test_concentration_decreases_downwind() -> None:
    c_near = gaussian_plume_concentration(200.0, 0.0, 0.0, Q=4.0e5, u=3.0, stability="D")
    c_far = gaussian_plume_concentration(2000.0, 0.0, 0.0, Q=4.0e5, u=3.0, stability="D")
    assert c_near > c_far


def test_concentration_crosswind_decay() -> None:
    c_center = gaussian_plume_concentration(500.0, 0.0, 0.0, Q=4.0e5, u=3.0, stability="D")
    c_off = gaussian_plume_concentration(500.0, 300.0, 0.0, Q=4.0e5, u=3.0, stability="D")
    assert c_center > c_off


def test_release_at_x_zero_is_zero() -> None:
    assert gaussian_plume_concentration(0.0, 0.0, 0.0, Q=1e6, u=3.0, stability="D") == 0.0


def test_higher_wind_dilutes() -> None:
    c_slow = centerline_concentration(500.0, Q=4.0e5, u=1.0, stability="D")
    c_fast = centerline_concentration(500.0, Q=4.0e5, u=6.0, stability="D")
    assert c_slow > c_fast


def test_source_validation() -> None:
    with pytest.raises(ValueError):
        gaussian_plume_concentration(500.0, 0.0, 0.0, Q=0.0, u=3.0, stability="D")
    with pytest.raises(ValueError):
        gaussian_plume_concentration(500.0, 0.0, 0.0, Q=1e6, u=0.0, stability="D")
    with pytest.raises(ValueError):
        gaussian_plume_concentration(500.0, 0.0, 0.0, Q=1e6, u=3.0, stability="D", H=-1.0)


def test_grid_concentration_shape() -> None:
    x = np.linspace(50.0, 2000.0, 10)
    y = np.linspace(-200.0, 200.0, 8)
    grid = grid_concentration(x, y, 0.0, Q=4.0e5, u=3.0, stability="D")
    assert grid.shape == (10, 8)
    assert np.all(grid >= 0)


def test_find_ground_level_max_centerline() -> None:
    result = find_ground_level_max(500.0, Q=4.0e5, u=3.0, stability="D")
    assert result.max_concentration > 0
    # Symmetric plume peaks on the centreline.
    assert result.y_at_max == pytest.approx(0.0, abs=20.0)


def test_find_ground_level_max_validation() -> None:
    with pytest.raises(ValueError):
        find_ground_level_max(500.0, Q=0.0, u=3.0, stability="D")
    with pytest.raises(ValueError):
        find_ground_level_max(500.0, Q=1e6, u=3.0, stability="D", n_crosswind=1)


def test_isopleth_extent_threshold_met() -> None:
    # A very low threshold is exceeded at large distance.
    extent = isopleth_extent(1e-9, Q=4.0e5, u=3.0, stability="D")
    assert extent > 0


def test_isopleth_extent_unreachable() -> None:
    # A huge threshold is not reached beyond the source -> returns small/1m.
    extent = isopleth_extent(1e12, Q=4.0e5, u=3.0, stability="D")
    assert extent <= 1.0


def test_isopleth_validation() -> None:
    with pytest.raises(ValueError):
        isopleth_extent(0.0, Q=1e6, u=3.0, stability="D")
    with pytest.raises(ValueError):
        isopleth_extent(1.0, Q=0.0, u=3.0, stability="D")
    with pytest.raises(ValueError):
        isopleth_extent(1.0, Q=1e6, u=3.0, stability="D", steps=1)
