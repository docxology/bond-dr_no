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


def test_line_intensity_raises_for_an_isotope_with_no_lines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A line-less isotope cannot be quantified; that must raise, not return 0.

    A zero intensity would divide into the Currie MDA and produce an infinite
    or absurd detection limit rather than an error. The library is extended with
    a real ``IsotopeProfile`` carrying no lines — a real object with real
    behaviour, not a stub.
    """
    import dr_no.canonical as canonical_module
    from dr_no.canonical import line_intensity

    extended = dict(isotope_library())
    extended["Nu-000"] = IsotopeProfile(name="Nu-000", half_life_y=1.0, gamma_lines=())
    monkeypatch.setattr(canonical_module, "isotope_library", lambda: extended)
    with pytest.raises(ValueError, match="no gamma lines to quantify"):
        line_intensity("Nu-000", 100.0)


def test_detect_peaks_reports_merged_doublet() -> None:
    """A genuine doublet inside ``min_separation_keV`` stays visible, not one line.

    C2 in TODO.md: before the round-2 fix, two photopeaks closer than 5 keV
    were collapsed to the stronger one and the weaker was discarded silently —
    a confidently wrong answer (one line) rather than an uncertain one. Now the
    surviving peak carries the absorbed member's energy in ``merged_energies``.
    """
    from dr_no.isotope_profiles import _gaussian

    energies = np.linspace(100.0, 200.0, 2001)
    counts = np.full_like(energies, 50.0)
    sigma = 0.5
    for centre, amp in ((150.0, 3000.0), (152.0, 2000.0)):  # 2 keV apart
        counts += amp * np.array([_gaussian(e, centre, sigma) for e in energies])

    peaks = detect_peaks(energies, counts, min_separation_keV=5.0, background_level=50.0)

    # Two local maxima within 5 keV collapse to one survivor.
    assert len(peaks) == 1
    peak = peaks[0]
    assert abs(peak.energy_keV - 150.0) < 0.5  # the stronger member survives
    # ...and the absorbed member is recorded, not erased.
    assert any(abs(e - 152.0) < 0.1 for e in peak.merged_energies)

    # An isolated peak reports no merge.
    solo = detect_peaks(energies, np.full_like(energies, 50.0), background_level=50.0)
    assert all(p.merged_energies == () for p in solo)


# --- V3 (round-2, 2026-08-06): reach the previously uncovered branches ---------


def test_fwhm_raises_on_non_positive_resolution() -> None:
    """The detector-resolution guard must not be silently skipped."""
    from dr_no.isotope_profiles import _fwhm_at

    assert _fwhm_at(1332.5, 2.0) > 0.0
    with pytest.raises(ValueError, match="must be positive"):
        _fwhm_at(1332.5, 0.0)
    with pytest.raises(ValueError, match="must be positive"):
        _fwhm_at(1332.5, -1.0)


def test_synthesize_spectrum_skips_zero_activity_isotope() -> None:
    """An isotope declared at 0 Bq contributes nothing but does not abort."""
    from dr_no.isotope_profiles import isotope_library

    energies = np.linspace(20.0, 3000.0, 2000)
    _, all_zeroed = synthesize_spectrum({"Cs-137": 0.0, "Co-60": 2.0e6}, energies=energies)
    _, co_only = synthesize_spectrum({"Co-60": 2.0e6}, energies=energies)
    assert "Cs-137" in isotope_library()
    assert np.array_equal(all_zeroed, co_only)


def test_detect_peaks_empty_spectrum_returns_empty() -> None:
    """A zero-length counts array yields no peaks, not an error or a phantom."""
    assert detect_peaks(np.array([]), np.array([])) == []


def test_detect_peaks_filters_subthreshold_local_maxima() -> None:
    """A local maximum whose SNR is below min_snr must be discarded."""
    energies = np.arange(0.0, 10.0, 1.0)
    counts = np.full_like(energies, 50.0)
    counts[5] = 100.0  # net 50, snr 1.0 < default min_snr 3.0
    assert detect_peaks(energies, counts, min_snr=3.0, background_level=50.0) == []
    # Raise the SNR floor above it and the same bump is a peak.
    bumped = detect_peaks(energies, counts, min_snr=0.5, background_level=50.0)
    assert len(bumped) == 1
    assert bumped[0].energy_keV == pytest.approx(5.0)


def test_detect_peaks_reports_merge_when_stronger_arrives_second() -> None:
    """Both merge orientations are visible (the trailing peak may be stronger)."""
    from dr_no.isotope_profiles import _gaussian

    energies = np.linspace(100.0, 200.0, 2001)
    counts = np.full_like(energies, 50.0)
    sigma = 0.5
    # Leading (150) weaker, trailing (152) stronger: survivor is 152.
    for centre, amp in ((150.0, 2000.0), (152.0, 3000.0)):
        counts += amp * np.array([_gaussian(e, centre, sigma) for e in energies])
    peaks = detect_peaks(energies, counts, min_separation_keV=5.0, background_level=50.0)
    assert len(peaks) == 1
    assert abs(peaks[0].energy_keV - 152.0) < 0.5
    assert any(abs(e - 150.0) < 0.1 for e in peaks[0].merged_energies)
