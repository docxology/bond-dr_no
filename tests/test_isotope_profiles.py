"""Real-data tests for :mod:`dr_no.isotope_profiles` (gamma-spectrum isotope ID).

All assertions use genuine computations over the real gamma-line library — no
mocks, no guessed peaks.
"""

from __future__ import annotations

import numpy as np
import pytest

from dr_no.isotope_profiles import (
    DetectedPeak,
    IsotopeProfile,
    detect_peaks,
    estimate_activity,
    identify_isotopes,
    isotope_library,
    library_names,
    match_energy,
    synthesize_spectrum,
    total_gamma_lines,
)


def test_library_contains_known_isotopes() -> None:
    lib = isotope_library()
    for name in ("Cs-137", "Co-60", "I-131", "Am-241", "K-40"):
        assert name in lib


def test_library_names_sorted_and_consistent() -> None:
    names = library_names()
    assert names == tuple(sorted(names))
    assert len(names) == len(isotope_library())


def test_total_gamma_lines_positive() -> None:
    assert total_gamma_lines() >= len(isotope_library())


def test_profile_half_life_and_lines() -> None:
    cl = isotope_library()["Cs-137"]
    assert cl.half_life_y == pytest.approx(30.08, rel=1e-3)
    assert cl.gamma_lines[0][0] == pytest.approx(661.66, rel=1e-3)


def test_profile_validation() -> None:
    with pytest.raises(ValueError):
        IsotopeProfile(name="", half_life_y=1.0, gamma_lines=(()))
    with pytest.raises(ValueError):
        IsotopeProfile(name="X", half_life_y=0.0, gamma_lines=(()))
    with pytest.raises(ValueError):
        IsotopeProfile(name="X", half_life_y=1.0, gamma_lines=((-1.0, 0.5),))
    with pytest.raises(ValueError):
        IsotopeProfile(name="X", half_life_y=1.0, gamma_lines=((100.0, 2.0),))


def test_strongest_line() -> None:
    co = isotope_library()["Co-60"]
    energy, intensity = co.strongest_line()
    assert energy == pytest.approx(1332.50, rel=1e-3)
    assert intensity == pytest.approx(0.9998, rel=1e-3)


def test_strongest_line_empty_raises() -> None:
    profile = IsotopeProfile(name="empty", half_life_y=1.0, gamma_lines=())
    with pytest.raises(ValueError):
        profile.strongest_line()


def test_discrete_energies() -> None:
    co = isotope_library()["Co-60"]
    assert co.discrete_energies == (1173.24, 1332.50)


def test_synthesize_spectrum_single_isotope() -> None:
    energies = np.linspace(20.0, 3000.0, 1500)
    _, counts = synthesize_spectrum({"Cs-137": 2.0e6}, energies=energies)
    idx = int(np.argmax(counts))
    # Cs-137's only line is at 661.66 keV.
    assert abs(energies[idx] - 661.66) < 10.0


def test_synthesize_spectrum_multi() -> None:
    energies = np.linspace(20.0, 3000.0, 3000)
    _, counts = synthesize_spectrum({"Cs-137": 2.0e6, "Co-60": 8.0e5}, energies=energies)
    top = np.argsort(counts)[-3:]
    peaks_e = sorted(float(energies[i]) for i in top)
    # Co-60 1173/1332 and Cs-137 661.7 should dominate.
    assert min(peaks_e) < 700.0


def test_synthesize_spectrum_unknown_isotope() -> None:
    with pytest.raises(KeyError):
        synthesize_spectrum({"Zz-999": 1.0}, energies=np.linspace(20.0, 3000.0, 10))


def test_synthesize_spectrum_validation() -> None:
    energies = np.linspace(20.0, 3000.0, 10)
    with pytest.raises(ValueError):
        synthesize_spectrum({"Cs-137": 1.0}, energies=np.empty((2, 2)))
    with pytest.raises(ValueError):
        synthesize_spectrum({"Cs-137": 1.0}, energies=np.array([]))
    with pytest.raises(ValueError):
        synthesize_spectrum({"Cs-137": 1.0}, energies=energies, acquisition_time_s=0.0)
    with pytest.raises(ValueError):
        synthesize_spectrum({"Cs-137": 1.0}, energies=energies, detector_efficiency=0.0)
    with pytest.raises(ValueError):
        synthesize_spectrum({"Cs-137": 1.0}, energies=energies, background_level=-1.0)
    with pytest.raises(ValueError):
        synthesize_spectrum({"Cs-137": -1.0}, energies=energies)


def test_detect_peaks_finds_real_lines() -> None:
    energies = np.linspace(20.0, 3000.0, 3000)
    _, counts = synthesize_spectrum({"Cs-137": 2.0e6, "Co-60": 8.0e5}, energies=energies)
    peaks = detect_peaks(energies, counts)
    peak_energies = sorted(p.energy_keV for p in peaks)
    assert any(abs(e - 661.66) < 10 for e in peak_energies)
    assert any(abs(e - 1173.24) < 10 for e in peak_energies)
    assert any(abs(e - 1332.50) < 10 for e in peak_energies)


def test_detect_peaks_no_signal() -> None:
    energies = np.linspace(20.0, 3000.0, 100)
    counts = np.full_like(energies, 50.0)
    assert detect_peaks(energies, counts, min_snr=3.0, background_level=50.0) == []


def test_detect_peaks_validation() -> None:
    with pytest.raises(ValueError):
        detect_peaks(np.array([1.0, 2.0]), np.array([1.0]))
    with pytest.raises(ValueError):
        detect_peaks(np.array([[1.0]]), np.array([[1.0]]))


def test_match_energy_window() -> None:
    assert match_energy(661.66, 661.66)
    assert match_energy(663.0, 661.66)  # within ~2.5 sigma
    assert not match_energy(900.0, 661.66)


def test_identify_isotopes_pure_cs() -> None:
    energies = np.linspace(20.0, 3000.0, 2000)
    _, counts = synthesize_spectrum({"Cs-137": 2.0e6}, energies=energies)
    peaks = detect_peaks(energies, counts)
    ident = identify_isotopes(peaks)
    assert ident[0].isotope == "Cs-137"


def test_identify_isotopes_mixture() -> None:
    energies = np.linspace(20.0, 3000.0, 3000)
    _, counts = synthesize_spectrum({"Cs-137": 2.0e6, "Co-60": 8.0e5}, energies=energies)
    peaks = detect_peaks(energies, counts)
    ident = identify_isotopes(peaks)
    top_isotopes = {i.isotope for i in ident[:2]}
    assert "Cs-137" in top_isotopes and "Co-60" in top_isotopes


def test_identify_isotopes_no_matches() -> None:
    ident = identify_isotopes([DetectedPeak(energy_keV=9999.0, net_counts=1.0, snr=1.0)])
    assert ident == []


def test_estimate_activity_round_trip() -> None:
    activity = estimate_activity(
        net_counts=1.0e5,
        gamma_intensity=0.8510,
        acquisition_time_s=60.0,
        detector_efficiency=0.01,
    )
    assert activity == pytest.approx(1.0e5 / (60.0 * 0.01 * 0.8510), rel=1e-9)


def test_estimate_activity_validation() -> None:
    with pytest.raises(ValueError):
        estimate_activity(
            -1.0, gamma_intensity=0.5, acquisition_time_s=60.0, detector_efficiency=0.01
        )
    with pytest.raises(ValueError):
        estimate_activity(
            1.0, gamma_intensity=2.0, acquisition_time_s=60.0, detector_efficiency=0.01
        )
    with pytest.raises(ValueError):
        estimate_activity(
            1.0, gamma_intensity=0.5, acquisition_time_s=0.0, detector_efficiency=0.01
        )
    with pytest.raises(ValueError):
        estimate_activity(
            1.0, gamma_intensity=0.5, acquisition_time_s=60.0, detector_efficiency=0.0
        )
