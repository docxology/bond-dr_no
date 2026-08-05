"""Tests for :mod:`dr_no.canonical` — the single-source-of-truth metrics.

Beyond shape and sanity, this module pins the *binding* between
``manuscript/config.yaml`` and the computed metrics: a scenario edit must move
the numbers. A metrics layer that ignored its config would pass every shape
assertion while silently reporting a scenario nobody declared — which is
exactly the defect this package carried before the scenario loader existed.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from dr_no.canonical import (
    _calibration_from_peaks,
    canonical_metrics,
    canonical_scenario,
    canonical_spectrum,
    detector_energy_grid,
    line_intensity,
)
from dr_no.isotope_profiles import DetectedPeak
from dr_no.scenario import load_scenario

PACKAGE_ROOT = Path(__file__).resolve().parents[1]

_REQUIRED_KEYS = {
    "detected_peaks",
    "identified_isotopes",
    "top_isotope",
    "quantified_line",
    "quantified_line_energy_kev",
    "net_area_quantified",
    "net_area_uncertainty",
    "calibration_gain_kev_per_ch",
    "calibration_r2",
    "mda_bq",
    "decay_chain",
    "decay_elapsed_days",
    "parent_fraction_remaining",
    "hvl_cm",
    "tvl_cm",
    "transmission_shield",
    "external_dose_probe_msv_h",
    "peak_concentration_bq_m3",
    "island_threat",
    "downwind_extent_m",
    "containment_actions",
    "num_facilities",
    "num_isotopes",
}


def test_metrics_keys_present() -> None:
    assert _REQUIRED_KEYS <= set(canonical_metrics())


def test_metrics_deterministic() -> None:
    assert canonical_metrics() == canonical_metrics()


def test_metrics_physical_sanity() -> None:
    m = canonical_metrics()
    assert m["detected_peaks"] >= 3
    assert "Cs-137" in m["identified_isotopes"]
    assert "Co-60" in m["identified_isotopes"]
    assert m["calibration_r2"] > 0.99
    assert m["mda_bq"] > 0
    assert 0 < m["parent_fraction_remaining"] < 1
    assert m["hvl_cm"] > 0
    assert m["tvl_cm"] > m["hvl_cm"]  # a tenth-value layer is thicker than a half
    assert 0 < m["transmission_shield"] <= 1
    assert m["external_dose_probe_msv_h"] > 0
    assert m["downwind_extent_m"] >= 0
    assert m["num_facilities"] == 2
    assert m["num_isotopes"] == 10
    assert set(m["containment_actions"]) == {"north_dock", "guano_cave"}


def test_scenario_json_safe() -> None:
    payload = canonical_scenario()
    # Round-trips through JSON: used as the provenance input hash.
    json.dumps(payload, sort_keys=True)
    assert {"spectrum", "detector", "plume", "facilities"} <= set(payload)


def test_canonical_spectrum_shape() -> None:
    energies, counts = canonical_spectrum()
    assert energies.ndim == 1
    assert energies.size == counts.size == detector_energy_grid().size
    assert counts.min() >= 0
    assert np.all(np.isfinite(counts))


def test_detector_energy_grid_matches_declared_config() -> None:
    scenario = load_scenario()
    grid = detector_energy_grid()
    assert grid.size == scenario.detector.bins
    assert grid.min() == pytest.approx(scenario.detector.energy_min_keV)
    assert grid.max() == pytest.approx(scenario.detector.energy_max_keV)


# --- config -> metrics binding ------------------------------------------------


def test_declared_release_rate_drives_plume_concentration() -> None:
    """Doubling the declared source term doubles the modelled concentration.

    The Gaussian plume is linear in Q, so this is an exact relation — a metrics
    layer reading a stale hardcoded Q would return the identical number twice.
    """
    scenario = load_scenario()
    doubled = replace(
        scenario, plume=replace(scenario.plume, source_Q_bq_s=scenario.plume.source_Q_bq_s * 2.0)
    )
    base = canonical_metrics(scenario)["peak_concentration_bq_m3"]
    scaled = canonical_metrics(doubled)["peak_concentration_bq_m3"]
    assert scaled == pytest.approx(2.0 * base, rel=1e-12)


def test_declared_shield_thickness_drives_transmission() -> None:
    """A thicker declared barrier transmits strictly less."""
    scenario = load_scenario()
    thicker = replace(
        scenario,
        shielding_probe=replace(
            scenario.shielding_probe, thickness_cm=scenario.shielding_probe.thickness_cm * 2.0
        ),
    )
    assert (
        canonical_metrics(thicker)["transmission_shield"]
        < canonical_metrics(scenario)["transmission_shield"]
    )


def test_declared_elapsed_time_drives_decay_projection() -> None:
    """Projecting further forward leaves strictly less parent activity."""
    scenario = load_scenario()
    later = replace(
        scenario,
        decay_projection=replace(
            scenario.decay_projection,
            elapsed_days=scenario.decay_projection.elapsed_days * 3.0,
        ),
    )
    assert (
        canonical_metrics(later)["parent_fraction_remaining"]
        < canonical_metrics(scenario)["parent_fraction_remaining"]
    )


def test_declared_detector_bins_drive_the_grid() -> None:
    scenario = load_scenario()
    coarse = replace(scenario, detector=replace(scenario.detector, bins=301))
    assert detector_energy_grid(coarse).size == 301
    assert canonical_spectrum(coarse)[1].size == 301


def test_declared_action_concentration_drives_downwind_extent() -> None:
    """A stricter action threshold pushes the contaminated isopleth further out."""
    scenario = load_scenario()
    stricter = replace(
        scenario, action_concentration_bq_m3=scenario.action_concentration_bq_m3 / 10.0
    )
    assert (
        canonical_metrics(stricter)["downwind_extent_m"]
        > canonical_metrics(scenario)["downwind_extent_m"]
    )


def test_config_file_edit_reaches_the_metrics(tmp_path: Path) -> None:
    """End-to-end: editing the YAML on disk changes the computed metric.

    The in-memory ``replace`` tests above would still pass if the file loader
    were bypassed entirely, so this one goes through a real file.
    """
    original = (PACKAGE_ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8")
    assert "wind_speed_m_s: 3.0" in original, "config no longer declares the wind speed as expected"
    edited = tmp_path / "config.yaml"
    edited.write_text(
        original.replace("wind_speed_m_s: 3.0", "wind_speed_m_s: 6.0"), encoding="utf-8"
    )
    faster_wind = load_scenario(edited)
    assert faster_wind.plume.wind_speed_m_s == 6.0
    # Concentration is inversely proportional to wind speed: doubling u halves C.
    base = canonical_metrics()["peak_concentration_bq_m3"]
    assert canonical_metrics(faster_wind)["peak_concentration_bq_m3"] == pytest.approx(
        base / 2.0, rel=1e-12
    )


# --- guards -------------------------------------------------------------------


def test_calibration_raises_when_no_peaks_match() -> None:
    """No usable calibration is an error, not a silent gain of 0.000.

    Peaks matching no declared line must raise rather than emit zeros that would
    render as a plausible-looking calibration in the manuscript.
    """
    energies = detector_energy_grid()
    stray = [DetectedPeak(energy_keV=42.0, net_counts=100.0, snr=9.0)]
    with pytest.raises(ValueError, match="needs >= 2 detected peaks"):
        _calibration_from_peaks(stray, energies, (661.66, 1173.24))


def test_calibration_raises_when_only_one_peak_matches() -> None:
    energies = detector_energy_grid()
    single = [DetectedPeak(energy_keV=661.66, net_counts=100.0, snr=9.0)]
    with pytest.raises(ValueError, match="matched 1"):
        _calibration_from_peaks(single, energies, (661.66, 1173.24))


def test_line_intensity_picks_the_nearest_line() -> None:
    # Co-60's two lines are 1173.24 and 1332.50 keV with distinct intensities.
    assert line_intensity("Co-60", 1173.0) == pytest.approx(0.9985)
    assert line_intensity("Co-60", 1332.0) == pytest.approx(0.9998)


def test_line_intensity_unknown_isotope_raises() -> None:
    with pytest.raises(KeyError):
        line_intensity("Xx-999", 100.0)


def test_metrics_quantified_line_matches_declaration() -> None:
    scenario = load_scenario()
    metrics = canonical_metrics(scenario)
    assert metrics["quantified_line"] == scenario.quantified_line
    assert metrics["quantified_line_energy_kev"] in scenario.calibration_lines_keV
