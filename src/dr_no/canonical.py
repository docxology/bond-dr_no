"""Canonical CRAB KEY scenario and metrics — the single source of truth.

Both the mission provider (``mission.py`` ``execute()``) and the manuscript
token hydrator (:mod:`dr_no.manuscript_variables`) consume
:func:`canonical_metrics`, so outcome ``results`` and manuscript ``{{TOKEN}}``s
can never disagree.

The scenario itself is *not* declared here — it is read from the ``mission:``
block of ``manuscript/config.yaml`` through :mod:`dr_no.scenario`. This module
is the computation over that scenario, never a second copy of it.

Pure domain logic: imports only the domain core, no bond_api.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from dr_no.decay_chain import activity_fraction_remaining, lookup_chain
from dr_no.dose_assessment import external_dose_rate, specific_gamma_constant
from dr_no.island_assessment import DetectedFacility, Meteorology, assess_island
from dr_no.isotope_profiles import (
    DetectedPeak,
    detect_peaks,
    identify_isotopes,
    isotope_library,
    synthesize_spectrum,
)
from dr_no.plume_model import find_ground_level_max
from dr_no.scenario import MissionScenario, load_scenario
from dr_no.shielding import half_value_layer, tenth_value_layer, transmission_factor
from dr_no.spectrum_processing import calibrate_energy, minimum_detectable_activity, net_peak_area

__all__ = [
    "BACKGROUND_LEVEL",
    "canonical_metrics",
    "canonical_scenario",
    "canonical_spectrum",
    "detector_energy_grid",
    "line_intensity",
]

#: Background continuum (counts/bin) used for synthesis and the SNR floor.
BACKGROUND_LEVEL = 50.0

#: Tolerance (keV) for pairing a detected peak with a declared calibration line.
_CALIBRATION_MATCH_KEV = 3.0

#: Energy (keV) above which spectrum bins are treated as background-only when
#: estimating B for the Currie detection limit.
_BACKGROUND_WINDOW_MIN_KEV = 2500.0


def canonical_scenario(scenario: MissionScenario | None = None) -> dict[str, object]:
    """The full scenario as a JSON-safe mapping (used for the provenance hash)."""
    return (scenario if scenario is not None else load_scenario()).as_payload()


def detector_energy_grid(scenario: MissionScenario | None = None) -> np.ndarray:
    """The canonical detector energy grid (keV bin centres), sized from config."""
    detector = (scenario if scenario is not None else load_scenario()).detector
    return np.linspace(detector.energy_min_keV, detector.energy_max_keV, detector.bins)


def canonical_spectrum(scenario: MissionScenario | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Synthesize the canonical detector spectrum: ``(energies, counts)``."""
    spec = scenario if scenario is not None else load_scenario()
    energies = detector_energy_grid(spec)
    _, counts = synthesize_spectrum(
        spec.source_activities_bq,
        energies=energies,
        acquisition_time_s=spec.detector.acquisition_time_s,
        detector_efficiency=spec.detector.detector_efficiency,
        resolution_at_1332=spec.detector.resolution_at_1332_keV,
        background_level=BACKGROUND_LEVEL,
    )
    return energies, counts


def line_intensity(isotope: str, energy_keV: float) -> float:
    """Emission intensity (photons/decay) of an isotope's line nearest ``energy_keV``.

    Used so the Currie MDA is computed against the declared quantified line's
    real branching ratio, rather than a literal pasted into the code.

    Raises:
        KeyError: the isotope is not in the library.
        ValueError: the isotope has no emission lines.
    """
    profile = isotope_library()[isotope]
    if not profile.gamma_lines:
        raise ValueError(f"isotope {isotope!r} has no gamma lines to quantify")
    nearest = min(profile.gamma_lines, key=lambda line: abs(line[0] - energy_keV))
    return float(nearest[1])


def _calibration_from_peaks(
    peaks: list[DetectedPeak],
    energies: np.ndarray,
    calibration_lines_keV: tuple[float, ...],
) -> tuple[float, float]:
    """Fit channel→energy from detected peaks paired to declared calibration lines.

    Returns ``(gain_keV_per_channel, r_squared)``.

    Raises:
        ValueError: fewer than two detected peaks matched a declared line. That
            is a genuine failure of the detection stage, not a degraded result —
            returning zeros here would put a plausible-looking ``0.000`` gain and
            an ``R² = 0.0000`` straight into the manuscript with nothing to
            flag it.
    """
    channels: list[float] = []
    line_energies: list[float] = []
    for peak in peaks:
        best_line = min(calibration_lines_keV, key=lambda e: abs(peak.energy_keV - e))
        if abs(peak.energy_keV - best_line) <= _CALIBRATION_MATCH_KEV:
            channels.append(float(np.argmin(np.abs(energies - peak.energy_keV))))
            line_energies.append(best_line)
    if len(channels) < 2:
        raise ValueError(
            "energy calibration needs >= 2 detected peaks within "
            f"{_CALIBRATION_MATCH_KEV} keV of a declared calibration line "
            f"{calibration_lines_keV}; matched {len(channels)}"
        )
    calibration = calibrate_energy(np.array(channels), np.array(line_energies))
    return calibration.gain_kev_per_ch, calibration.r_squared


def _quantified_line_energy(scenario: MissionScenario) -> float:
    """The declared calibration line closest to the quantified isotope's strongest line."""
    strongest = isotope_library()[scenario.quantified_line].strongest_line()[0]
    return min(scenario.calibration_lines_keV, key=lambda e: abs(e - strongest))


def canonical_metrics(scenario: MissionScenario | None = None) -> dict[str, Any]:
    """Compute every deterministic CRAB KEY metric from the canonical scenario.

    Returns a flat mapping of named metrics consumed by ``mission.execute()``
    results and by ``manuscript_variables.generate_variables()`` tokens:

    * identification: detected peak count, ranked isotopes, top isotope;
    * quantification: net photopeak area of the declared quantified line, the
      energy-calibration gain and R², and the Currie MDA;
    * time dependence: parent activity fraction remaining after the declared
      elapsed time on the declared decay chain;
    * shielding: half-value layer, tenth-value layer, and the transmission of
      the declared barrier;
    * dose: unshielded external dose rate at the declared probe distance;
    * island: plume peak concentration, threat level, downwind extent, and the
      per-facility containment actions.

    Args:
        scenario: An explicit scenario; defaults to the one declared in
            ``manuscript/config.yaml``.
    """
    spec = scenario if scenario is not None else load_scenario()
    energies, counts = canonical_spectrum(spec)
    peaks = detect_peaks(energies, counts, background_level=BACKGROUND_LEVEL)
    identifications = identify_isotopes(peaks)
    top_isotope = identifications[0].isotope if identifications else "none"

    calibration_gain, calibration_r2 = _calibration_from_peaks(
        peaks, energies, spec.calibration_lines_keV
    )

    # Net photopeak area and Currie MDA for the declared quantified line.
    quantified = spec.quantified_line
    quantified_energy = _quantified_line_energy(spec)
    peak_index = int(np.argmin(np.abs(energies - quantified_energy)))
    area = net_peak_area(energies, counts, peak_index)
    tail = counts[energies > _BACKGROUND_WINDOW_MIN_KEV]
    background = float(tail.mean()) if tail.size else BACKGROUND_LEVEL
    mda = minimum_detectable_activity(
        background,
        acquisition_time_s=spec.detector.acquisition_time_s,
        detector_efficiency=spec.detector.detector_efficiency,
        gamma_intensity=line_intensity(quantified, quantified_energy),
    )

    # Decay: the declared chain's parent, projected forward.
    projection = spec.decay_projection
    chain = lookup_chain(projection.chain)
    parent_fraction = activity_fraction_remaining(
        chain.members[0].half_life_s, projection.elapsed_days * 86400.0
    )

    # Shielding.
    shield = spec.shielding_probe
    hvl = half_value_layer(shield.hvl_energy_MeV, shield.material)
    tvl = tenth_value_layer(shield.tvl_energy_MeV, shield.tvl_material)
    transmission = transmission_factor(shield.hvl_energy_MeV, shield.thickness_cm, shield.material)

    # External dose at the probe distance from the declared isotope's inventory.
    probe = spec.external_dose_probe
    dose_at_probe = external_dose_rate(
        spec.source_activities_bq[probe.isotope],
        specific_gamma_constant(probe.isotope),
        probe.distance_m,
    )

    # Plume and island assessment.
    facilities = [
        DetectedFacility(
            name=facility.name,
            x_m=facility.x_m,
            y_m=facility.y_m,
            isotope_activities=dict(facility.isotopes),
            containment=facility.containment,
        )
        for facility in spec.facilities
    ]
    meteo = Meteorology(
        wind_speed_m_s=spec.plume.wind_speed_m_s,
        stability=spec.plume.stability,
        release_height_m=spec.plume.release_height_m,
    )
    max_plume = find_ground_level_max(
        facilities[0].x_m,
        Q=spec.plume.source_Q_bq_s,
        u=spec.plume.wind_speed_m_s,
        stability=spec.plume.stability,
        H=spec.plume.release_height_m,
    )
    assessment = assess_island(
        facilities,
        meteo,
        source_Q=spec.plume.source_Q_bq_s,
        action_concentration_bq_m3=spec.action_concentration_bq_m3,
    )

    return {
        "detected_peaks": len(peaks),
        "identified_isotopes": [i.isotope for i in identifications],
        "top_isotope": top_isotope,
        "quantified_line": quantified,
        "quantified_line_energy_kev": quantified_energy,
        "net_area_quantified": area.net_counts,
        "net_area_uncertainty": area.net_uncertainty,
        "calibration_gain_kev_per_ch": calibration_gain,
        "calibration_r2": calibration_r2,
        "mda_bq": mda,
        "decay_chain": projection.chain,
        "decay_elapsed_days": projection.elapsed_days,
        "parent_fraction_remaining": parent_fraction,
        "hvl_cm": hvl,
        "tvl_cm": tvl,
        "transmission_shield": transmission,
        "external_dose_probe_msv_h": dose_at_probe,
        "peak_concentration_bq_m3": max_plume.max_concentration,
        "island_threat": assessment.overall_level,
        "downwind_extent_m": assessment.downwind_contamination_m,
        "containment_actions": dict(assessment.containment_actions),
        "num_facilities": len(facilities),
        "num_isotopes": len(isotope_library()),
    }
