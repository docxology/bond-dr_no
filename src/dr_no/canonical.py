"""Canonical CRAB KEY scenario and metrics — the single source of truth.

Both the mission provider (``mission.py`` ``execute()``) and the manuscript
token hydrator (:mod:`dr_no.manuscript_variables`) consume
:func:`canonical_metrics`, so outcome ``results`` and manuscript ``{{TOKEN}}``s
can never disagree. The scenario constants previously resident in
``mission.py`` live here, typed, so the adapter stays a thin seam.

Pure domain logic: imports only the domain core, no bond_api.
"""

from __future__ import annotations

from typing import Any, cast

import numpy as np

from dr_no.decay_chain import activity_fraction_remaining, lookup_chain
from dr_no.dose_assessment import external_dose_rate, specific_gamma_constant
from dr_no.island_assessment import DetectedFacility, Meteorology, assess_island
from dr_no.isotope_profiles import (
    detect_peaks,
    identify_isotopes,
    isotope_library,
    synthesize_spectrum,
)
from dr_no.plume_model import find_ground_level_max
from dr_no.shielding import half_value_layer, tenth_value_layer, transmission_factor
from dr_no.spectrum_processing import calibrate_energy, minimum_detectable_activity, net_peak_area

__all__ = [
    "canonical_metrics",
    "canonical_scenario",
    "canonical_spectrum",
    "detector_energy_grid",
]

# Deterministic scenario (typed so mypy can follow it).
_SPECTRUM: dict[str, float] = {"Cs-137": 2.0e6, "Co-60": 8.0e5}
_DETECTOR: dict[str, float] = {
    "acquisition_time_s": 60.0,
    "detector_efficiency": 0.01,
    "resolution_at_1332": 2.0,
}
_PLUME: dict[str, float | str] = {
    "source_Q": 4.0e5,
    "wind_speed_m_s": 3.0,
    "stability": "D",
    "release_height_m": 10.0,
}
_FACILITIES: list[dict[str, object]] = [
    {
        "name": "north_dock",
        "x_m": 500.0,
        "y_m": 20.0,
        "isotopes": {"Cs-137": 2.0e6, "Co-60": 8.0e5},
        "containment": "breached",
    },
    {
        "name": "guano_cave",
        "x_m": 1500.0,
        "y_m": -40.0,
        "isotopes": {"I-131": 1.0e7},
        "containment": "contained",
    },
]

#: The two injected isotopes' principal line energies used for calibration.
_CALIBRATION_LINES: tuple[float, ...] = (661.66, 1173.24, 1332.50)
_I131_ELAPSED_DAYS = 7.0


def canonical_scenario() -> dict[str, object]:
    """The full scenario as a JSON-safe mapping (used for the provenance hash)."""
    return {
        "spectrum": _SPECTRUM,
        "detector": _DETECTOR,
        "plume": _PLUME,
        "facilities": _FACILITIES,
    }


def detector_energy_grid() -> np.ndarray:
    """The canonical detector energy grid (keV bin centres)."""
    return np.linspace(20.0, 3000.0, 1200)


def canonical_spectrum() -> tuple[np.ndarray, np.ndarray]:
    """Synthesize the canonical detector spectrum: ``(energies, counts)``."""
    energies = detector_energy_grid()
    _, counts = synthesize_spectrum(
        _SPECTRUM,
        energies=energies,
        acquisition_time_s=float(_DETECTOR["acquisition_time_s"]),
        detector_efficiency=float(_DETECTOR["detector_efficiency"]),
        resolution_at_1332=float(_DETECTOR["resolution_at_1332"]),
    )
    return energies, counts


def _source_Q() -> float:
    return float(_PLUME["source_Q"])


def _wind_speed() -> float:
    return float(_PLUME["wind_speed_m_s"])


def _stability() -> str:
    return str(_PLUME["stability"])


def _release_height() -> float:
    return float(_PLUME["release_height_m"])


def canonical_metrics() -> dict[str, Any]:
    """Compute every deterministic CRAB KEY metric from the canonical scenario.

    Returns a flat mapping of named metrics consumed by ``mission.execute()``
    results and by ``manuscript_variables.generate_variables()`` tokens:

    * identification: detected peak count, ranked isotopes, top isotope,
      net photopeak area of the Cs-137 line;
    * quantification: energy-calibration gain and R², Currie MDA for Cs-137;
    * time dependence: I-131 activity fraction remaining after 7 days;
    * shielding: lead half-value layer at 662 keV, concrete tenth-value layer
      at 1332 keV, transmission through 5 cm of lead;
    * dose: unshielded Co-60 external dose rate at 100 m;
    * island: plume peak concentration, island threat level, downwind extent.
    """
    energies, counts = canonical_spectrum()
    peaks = detect_peaks(energies, counts, background_level=50.0)
    identifications = identify_isotopes(peaks)
    top_isotope = identifications[0].isotope if identifications else "none"

    # Energy calibration: match detected peaks to the injected lines.
    channels: list[float] = []
    line_energies: list[float] = []
    for peak in peaks:
        best_line = min(_CALIBRATION_LINES, key=lambda e: abs(peak.energy_keV - e))
        if abs(peak.energy_keV - best_line) <= 3.0:
            channel = float(np.argmin(np.abs(energies - peak.energy_keV)))
            channels.append(channel)
            line_energies.append(best_line)
    if len(channels) >= 2:
        calibration = calibrate_energy(np.array(channels), np.array(line_energies))
        calibration_gain = calibration.gain_kev_per_ch
        calibration_r2 = calibration.r_squared
    else:
        calibration_gain = 0.0
        calibration_r2 = 0.0

    # Net photopeak area and Currie MDA for the Cs-137 line.
    cs137_index = int(np.argmin(np.abs(energies - 661.66)))
    area = net_peak_area(energies, counts, cs137_index)
    tail = counts[energies > 2500.0]
    background = float(tail.mean()) if tail.size else 0.0
    mda = minimum_detectable_activity(
        background,
        acquisition_time_s=float(_DETECTOR["acquisition_time_s"]),
        detector_efficiency=float(_DETECTOR["detector_efficiency"]),
        gamma_intensity=0.8510,
    )

    # Decay: I-131 remaining after 7 days.
    i131_chain = lookup_chain("I-131/Xe-131m")
    i131_fraction = activity_fraction_remaining(
        i131_chain.members[0].half_life_s, _I131_ELAPSED_DAYS * 86400.0
    )

    # Shielding.
    hvl_lead = half_value_layer(0.662, "lead")
    tvl_concrete = tenth_value_layer(1.332, "concrete")
    transmission = transmission_factor(0.662, 5.0, "lead")

    # External dose at 100 m from the Co-60 component.
    dose_100m = external_dose_rate(8.0e5, specific_gamma_constant("Co-60"), 100.0)

    # Plume and island assessment.
    max_plume = find_ground_level_max(
        500.0, Q=_source_Q(), u=_wind_speed(), stability=_stability(), H=_release_height()
    )
    facilities = [
        DetectedFacility(
            name=str(f["name"]),
            x_m=float(cast("float", f["x_m"])),
            y_m=float(cast("float", f["y_m"])),
            isotope_activities=cast("dict[str, float]", f["isotopes"]),
            containment=str(f["containment"]),
        )
        for f in _FACILITIES
    ]
    meteo = Meteorology(
        wind_speed_m_s=_wind_speed(),
        stability=_stability(),
        release_height_m=_release_height(),
    )
    assessment = assess_island(facilities, meteo, source_Q=_source_Q())

    return {
        "detected_peaks": len(peaks),
        "identified_isotopes": [i.isotope for i in identifications],
        "top_isotope": top_isotope,
        "net_area_cs137": area.net_counts,
        "calibration_gain_kev_per_ch": calibration_gain,
        "calibration_r2": calibration_r2,
        "mda_cs137_bq": mda,
        "i131_fraction_7d": i131_fraction,
        "hvl_lead_662_cm": hvl_lead,
        "tvl_concrete_1332_cm": tvl_concrete,
        "transmission_lead_5cm_662": transmission,
        "external_dose_100m_msv_h": dose_100m,
        "peak_concentration_bq_m3": max_plume.max_concentration,
        "island_threat": assessment.overall_level,
        "downwind_extent_m": assessment.downwind_contamination_m,
        "num_facilities": len(facilities),
        "num_isotopes": len(isotope_library()),
    }
