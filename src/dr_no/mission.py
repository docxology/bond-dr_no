"""CRAB KEY mission provider — the thin BOND-API adapter for the Dr. No film.

This is the only module that may import ``bond_api``. The pure domain core
(:mod:`dr_no.isotope_profiles`, :mod:`dr_no.plume_model`,
:mod:`dr_no.island_assessment`) stays protocol-free so it remains importable
and testable standalone.

It implements the FROZEN :class:`bond_api.protocol.MissionProvider` contract
and registers a set of CRAB KEY gadgets with the
:class:`bond_api.registry.GadgetRegistry` at import time.
"""

from __future__ import annotations

import hashlib
import json
from typing import cast

import numpy as np
from bond_api.protocol import (  # type: ignore[import-untyped]
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry, MissionRegistry  # type: ignore[import-untyped]

from dr_no import __version__
from dr_no.island_assessment import (
    INHALATION_DCF_SV_BQ,
    THREAT_LEVELS,
    DetectedFacility,
    Meteorology,
    assess_island,
)
from dr_no.isotope_profiles import (
    detect_peaks,
    identify_isotopes,
    isotope_library,
    library_names,
    synthesize_spectrum,
)
from dr_no.plume_model import STABILITY_CLASSES, find_ground_level_max

__all__ = ["MissionProvider"]

_PACKAGE_VERSION = __version__
_SEED = 42

# Deterministic scenario used by the execute stage (typed so mypy can follow it).
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


def _scenario_payload() -> dict[str, object]:
    """The full scenario as a JSON-safe mapping (used for the provenance hash)."""
    return {
        "spectrum": _SPECTRUM,
        "detector": _DETECTOR,
        "plume": _PLUME,
        "facilities": _FACILITIES,
    }


def _input_hash() -> str:
    """Stable fingerprint of the scenario for provenance."""
    return hashlib.sha256(
        json.dumps(_scenario_payload(), sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]


def _detector_energies() -> np.ndarray:
    return np.linspace(20.0, 3000.0, 1200)


def _source_Q() -> float:
    return float(_PLUME["source_Q"])


def _wind_speed() -> float:
    return float(_PLUME["wind_speed_m_s"])


def _stability() -> str:
    return str(_PLUME["stability"])


def _release_height() -> float:
    return float(_PLUME["release_height_m"])


def _facility_isotopes(entry: dict[str, object]) -> dict[str, float]:
    return cast("dict[str, float]", entry["isotopes"])


class MissionProvider:
    """Deterministic CRAB KEY mission provider for the Dr. No film."""

    film = "dr_no"

    def brief(self) -> MissionBrief:
        """Declare the CRAB KEY mission: isotope forensics, plume, island risk."""
        return MissionBrief(
            film=self.film,
            codename="CRAB KEY",
            objectives=(
                "identify gamma-emitting isotopes from a measured spectrum",
                "model radioactive plume dispersion under local meteorology",
                "assess island-wide radiological threat and containment actions",
            ),
            assets=(
                Asset(
                    kind="isotope-library",
                    name="canonical",
                    payload={"count": len(isotope_library())},
                ),
                Asset(kind="detector", name="hpge", payload=_DETECTOR),
                Asset(kind="meteorology", name="plume", payload=_PLUME),
            ),
            constraints=(
                Constraint(
                    kind="determinism", detail="no random draws; fixed scenario, fixed seed"
                ),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the threat surface: library, dispersion model, island geometry."""
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(
                    label="isotope-library", detail=f"{len(isotope_library())} isotopes catalogued"
                ),
                Finding(
                    label="detector",
                    detail="HPGe synthesis resolved at "
                    f"{float(_DETECTOR['resolution_at_1332'])} keV",
                ),
                Finding(label="stability-classes", detail=", ".join(STABILITY_CLASSES)),
                Finding(label="threat-bands", detail=", ".join(THREAT_LEVELS)),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the four deterministic stages of a CRAB KEY assessment."""
        return MissionPlan(
            steps=(
                Step(name="spectrum", action="synthesize_spectrum", params=_SPECTRUM),
                Step(name="identify", action="identify_isotopes", params={"peaks": "detected"}),
                Step(name="plume", action="model_dispersion", params=_PLUME),
                Step(
                    name="assess", action="assess_island", params={"facilities": len(_FACILITIES)}
                ),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the CRAB KEY pipeline deterministically and capture its results."""
        energies = _detector_energies()
        spectrum = _SPECTRUM
        detector = _DETECTOR
        _, counts = synthesize_spectrum(
            spectrum,
            energies=energies,
            acquisition_time_s=float(detector["acquisition_time_s"]),
            detector_efficiency=float(detector["detector_efficiency"]),
            resolution_at_1332=float(detector["resolution_at_1332"]),
        )
        peaks = detect_peaks(energies, counts, background_level=50.0)
        identifications = identify_isotopes(peaks)

        max_plume = find_ground_level_max(
            500.0,
            Q=_source_Q(),
            u=_wind_speed(),
            stability=_stability(),
            H=_release_height(),
        )

        facilities = [
            DetectedFacility(
                name=str(f["name"]),
                x_m=float(cast("float", f["x_m"])),
                y_m=float(cast("float", f["y_m"])),
                isotope_activities=_facility_isotopes(f),
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

        results = {
            "detected_peaks": len(peaks),
            "identified_isotopes": [i.isotope for i in identifications],
            "top_isotope": identifications[0].isotope if identifications else None,
            "peak_concentration_bq_m3": max_plume.max_concentration,
            "island_threat": assessment.overall_level,
            "downwind_extent_m": assessment.downwind_contamination_m,
            "steps_planned": len(plan.steps),
            "facilities_assessed": len(facilities),
        }
        return MissionOutcome(
            success=True,
            results=results,
            provenance=Provenance(
                package_version=_PACKAGE_VERSION,
                seed=_SEED,
                input_hash=_input_hash(),
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarize the mission outcome and record CRAB KEY's standing lessons."""
        return Debrief(
            outcome=outcome,
            lessons=(
                "isotope identification must use a real gamma-line library, never guesswork",
                "dispersion and dose are computed with fixed physics, no randomness",
                "a breached containment escalates a facility's threat band",
            ),
        )


# Register CRAB KEY gadgets and provider with the BOND registries.
GADGETS: dict[str, object] = {
    "isotope_library": isotope_library,
    "stability_classes": STABILITY_CLASSES,
    "inhalation_dcf": INHALATION_DCF_SV_BQ,
    "threat_levels": THREAT_LEVELS,
    "library_names": library_names,
}

_PROVIDER = MissionProvider()
GADGET_REGISTRY = GadgetRegistry()
GADGET_REGISTRY.register(_PROVIDER.film, GADGETS)

MISSION_REGISTRY = MissionRegistry()
MISSION_REGISTRY.register(_PROVIDER)
