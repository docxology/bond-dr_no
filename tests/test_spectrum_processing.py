"""Real-data tests for :mod:`dr_no.spectrum_processing` (calibration, net area, MDA)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from dr_no.spectrum_processing import (
    EnergyCalibration,
    PeakArea,
    calibrate_energy,
    minimum_detectable_activity,
    net_peak_area,
)


def test_calibrate_energy_exact_linear() -> None:
    channels = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    energies = np.array([10.0, 12.0, 14.0, 16.0, 18.0])
    cal = calibrate_energy(channels, energies)
    assert cal.gain_kev_per_ch == pytest.approx(2.0, rel=1e-9)
    assert cal.offset_kev == pytest.approx(10.0, rel=1e-9)
    assert cal.r_squared == pytest.approx(1.0)
    assert all(abs(r) < 1e-9 for r in cal.residuals_kev)


def test_calibrate_energy_dataclass() -> None:
    cal = EnergyCalibration(1.0, 0.0, (0.0,), 1.0)
    assert cal.gain_kev_per_ch == 1.0


def test_calibrate_energy_imperfect_fit() -> None:
    channels = np.array([0.0, 1.0, 2.0, 3.0])
    energies = np.array([0.0, 2.1, 3.9, 6.2])
    cal = calibrate_energy(channels, energies)
    assert cal.r_squared > 0.9
    assert cal.gain_kev_per_ch > 0


def test_calibrate_energy_validation() -> None:
    with pytest.raises(ValueError):
        calibrate_energy(np.array([[1.0, 2.0]]), np.array([1.0, 2.0]))
    with pytest.raises(ValueError):
        calibrate_energy(np.array([1.0, 2.0]), np.array([1.0]))
    with pytest.raises(ValueError):
        calibrate_energy(np.array([1.0]), np.array([1.0]))
    # Degenerate (constant) channels: denominator is zero.
    with pytest.raises(ValueError):
        calibrate_energy(np.array([1.0, 1.0, 1.0]), np.array([1.0, 2.0, 3.0]))


def test_net_peak_area_knowledge_vector() -> None:
    energies = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    counts = np.array([10.0, 10.0, 100.0, 10.0, 10.0])
    area = net_peak_area(energies, counts, peak_index=2, half_width=2)
    assert area.gross_counts == pytest.approx(140.0)
    assert area.background_counts == pytest.approx(50.0)
    assert area.net_counts == pytest.approx(90.0)
    assert area.net_uncertainty == pytest.approx(math.sqrt(190.0), rel=1e-6)


def test_net_peak_area_dataclass() -> None:
    area = PeakArea(1.0, 0.0, 1.0, 1.0)
    assert area.net_counts == 1.0


def test_net_peak_area_flat_background_net_zero() -> None:
    energies = np.linspace(0, 10, 10)
    counts = np.full(10, 5.0)
    area = net_peak_area(energies, counts, peak_index=5, half_width=2)
    assert area.net_counts == pytest.approx(0.0, abs=1e-9)


def test_net_peak_area_validation() -> None:
    energies = np.linspace(0, 10, 5)
    counts = np.full(5, 1.0)
    with pytest.raises(ValueError):
        net_peak_area(np.array([1.0, 2.0]), counts, peak_index=1)
    with pytest.raises(ValueError):
        net_peak_area(energies, np.array([[1.0]]), peak_index=1)
    with pytest.raises(ValueError):
        net_peak_area(energies, counts, peak_index=99)
    with pytest.raises(ValueError):
        net_peak_area(energies, counts, peak_index=1, half_width=0)
    with pytest.raises(TypeError):
        net_peak_area(energies, counts, peak_index="x")  # type: ignore[arg-type]
    # A single-channel spectrum cannot span a two-channel region.
    with pytest.raises(ValueError):
        net_peak_area(np.array([1.0]), np.array([5.0]), peak_index=0, half_width=1)


def test_mda_known_vector() -> None:
    mda = minimum_detectable_activity(
        100.0, acquisition_time_s=60.0, detector_efficiency=0.01, gamma_intensity=0.8510
    )
    ld = 2.71 + 4.65 * math.sqrt(100.0)
    expected = ld / (60.0 * 0.01 * 0.8510)
    assert mda == pytest.approx(expected, rel=1e-9)


def test_mda_increases_with_background() -> None:
    m1 = minimum_detectable_activity(
        10.0, acquisition_time_s=60.0, detector_efficiency=0.01, gamma_intensity=0.5
    )
    m2 = minimum_detectable_activity(
        100.0, acquisition_time_s=60.0, detector_efficiency=0.01, gamma_intensity=0.5
    )
    assert m2 > m1


def test_mda_validation() -> None:
    with pytest.raises(ValueError):
        minimum_detectable_activity(
            -1.0, acquisition_time_s=60.0, detector_efficiency=0.01, gamma_intensity=0.5
        )
    with pytest.raises(ValueError):
        minimum_detectable_activity(
            10.0, acquisition_time_s=0.0, detector_efficiency=0.01, gamma_intensity=0.5
        )
    with pytest.raises(ValueError):
        minimum_detectable_activity(
            10.0, acquisition_time_s=60.0, detector_efficiency=0.0, gamma_intensity=0.5
        )
    with pytest.raises(ValueError):
        minimum_detectable_activity(
            10.0, acquisition_time_s=60.0, detector_efficiency=2.0, gamma_intensity=0.5
        )
    with pytest.raises(ValueError):
        minimum_detectable_activity(
            10.0, acquisition_time_s=60.0, detector_efficiency=0.01, gamma_intensity=0.0
        )
    with pytest.raises(ValueError):
        minimum_detectable_activity(
            10.0, acquisition_time_s=60.0, detector_efficiency=0.01, gamma_intensity=2.0
        )
