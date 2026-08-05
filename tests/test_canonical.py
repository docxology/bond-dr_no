"""Tests for :mod:`dr_no.canonical` — the single-source-of-truth metrics."""

from __future__ import annotations

import json

from dr_no.canonical import (
    canonical_metrics,
    canonical_scenario,
    canonical_spectrum,
    detector_energy_grid,
)

_REQUIRED_KEYS = {
    "detected_peaks",
    "identified_isotopes",
    "top_isotope",
    "net_area_cs137",
    "calibration_gain_kev_per_ch",
    "calibration_r2",
    "mda_cs137_bq",
    "i131_fraction_7d",
    "hvl_lead_662_cm",
    "tvl_concrete_1332_cm",
    "transmission_lead_5cm_662",
    "external_dose_100m_msv_h",
    "peak_concentration_bq_m3",
    "island_threat",
    "downwind_extent_m",
    "num_facilities",
    "num_isotopes",
}


def test_metrics_keys_present() -> None:
    metrics = canonical_metrics()
    assert _REQUIRED_KEYS <= set(metrics)


def test_metrics_deterministic() -> None:
    assert canonical_metrics() == canonical_metrics()


def test_metrics_physical_sanity() -> None:
    m = canonical_metrics()
    assert m["detected_peaks"] >= 3
    assert "Cs-137" in m["identified_isotopes"]
    assert "Co-60" in m["identified_isotopes"]
    assert m["calibration_r2"] > 0.99
    assert m["mda_cs137_bq"] > 0
    assert 0 < m["i131_fraction_7d"] < 1
    assert m["hvl_lead_662_cm"] > 0
    assert 0 < m["transmission_lead_5cm_662"] <= 1
    assert m["external_dose_100m_msv_h"] > 0
    assert m["downwind_extent_m"] >= 0
    assert m["num_facilities"] == 2
    assert m["num_isotopes"] == 10


def test_scenario_json_safe() -> None:
    payload = canonical_scenario()
    # Round-trips through JSON: used as the provenance input hash.
    json.dumps(payload, sort_keys=True)
    assert set(payload) == {"spectrum", "detector", "plume", "facilities"}


def test_canonical_spectrum_shape() -> None:
    energies, counts = canonical_spectrum()
    assert energies.ndim == 1
    assert energies.size == counts.size == detector_energy_grid().size
    assert counts.min() >= 0


def test_detector_energy_grid() -> None:
    grid = detector_energy_grid()
    assert grid.size == 1200
    assert grid.min() >= 20.0
