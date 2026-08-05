"""CRAB KEY mission provider — the thin BOND-API adapter for the Dr. No film.

This is the only module that may import ``bond_api``. The pure domain core
(:mod:`dr_no.isotope_profiles`, :mod:`dr_no.plume_model`,
:mod:`dr_no.island_assessment`, :mod:`dr_no.decay_chain`,
:mod:`dr_no.spectrum_processing`, :mod:`dr_no.shielding`,
:mod:`dr_no.dose_assessment`, and the shared :mod:`dr_no.canonical` metric
source) stays protocol-free so it remains importable and testable standalone.

It implements the FROZEN :class:`bond_api.protocol.MissionProvider` contract
and registers a set of CRAB KEY gadgets with the
:class:`bond_api.registry.GadgetRegistry` at import time. Its public shape is
fixed: top-level ``MissionProvider`` and the module-level ``GADGETS`` mapping.
"""

from __future__ import annotations

from typing import Any, cast

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
from dr_no.canonical import canonical_metrics, canonical_scenario, scenario_fingerprint
from dr_no.decay_chain import decay_chains
from dr_no.dose_assessment import GAMMA_CONSTANT_MSV_M2_H_GBQ, INHALATION_DCF_SV_BQ
from dr_no.island_assessment import THREAT_LEVELS
from dr_no.isotope_profiles import isotope_library, library_names
from dr_no.plume_model import STABILITY_CLASSES
from dr_no.scenario import load_scenario
from dr_no.shielding import MATERIALS

__all__ = ["MissionProvider"]

_PACKAGE_VERSION = __version__


def _seed() -> int:
    """The mission seed of record, declared in ``manuscript/config.yaml``."""
    return load_scenario().seed


def _input_hash() -> str:
    """Stable fingerprint of the canonical scenario for provenance.

    Delegates to :func:`dr_no.canonical.scenario_fingerprint` so the provenance
    hash and the manuscript's ``SCENARIO_FINGERPRINT`` token are the same
    number by construction rather than by coincidence.
    """
    return scenario_fingerprint()


def _detector_payload() -> dict[str, float]:
    return cast("dict[str, float]", canonical_scenario()["detector"])


def _spectrum_payload() -> dict[str, float]:
    return cast("dict[str, float]", canonical_scenario()["spectrum"])


def _plume_payload() -> dict[str, float | str]:
    return cast("dict[str, float | str]", canonical_scenario()["plume"])


def _facilities() -> list[dict[str, object]]:
    return cast("list[dict[str, object]]", canonical_scenario()["facilities"])


class MissionProvider:
    """Deterministic CRAB KEY mission provider for the Dr. No film."""

    film = "dr_no"

    def brief(self) -> MissionBrief:
        """Declare the CRAB KEY mission: isotope forensics, dispersion, threat."""
        scenario = canonical_scenario()
        return MissionBrief(
            film=self.film,
            codename=load_scenario().codename,
            objectives=(
                "identify gamma-emitting isotopes from a measured spectrum",
                "quantify, time-project, and shield against the radiological source",
                "model radioactive plume dispersion under local meteorology",
                "assess island-wide radiological threat and containment actions",
            ),
            assets=(
                Asset(
                    kind="isotope-library",
                    name="canonical",
                    payload={"count": len(isotope_library())},
                ),
                Asset(kind="decay-chains", name="bateman", payload={"count": len(decay_chains())}),
                Asset(kind="detector", name="hpge", payload=scenario["detector"]),
                Asset(kind="meteorology", name="plume", payload=scenario["plume"]),
            ),
            constraints=(
                Constraint(
                    kind="determinism", detail="no random draws; fixed scenario, fixed seed"
                ),
                Constraint(kind="sources", detail="real gamma-line, dose, and attenuation data"),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the threat surface: library, chains, dispersion, shielding."""
        detector = _detector_payload()
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(
                    label="isotope-library", detail=f"{len(isotope_library())} isotopes catalogued"
                ),
                Finding(
                    label="decay-chains", detail=f"{len(decay_chains())} parent/daughter chains"
                ),
                Finding(
                    label="detector",
                    detail="HPGe synthesis resolved at "
                    f"{float(detector['resolution_at_1332'])} keV",
                ),
                Finding(label="stability-classes", detail=", ".join(STABILITY_CLASSES)),
                Finding(label="threat-bands", detail=", ".join(THREAT_LEVELS)),
                Finding(label="shielding-materials", detail=", ".join(MATERIALS)),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the full deterministic assessment pipeline."""
        return MissionPlan(
            steps=(
                Step(name="spectrum", action="synthesize_spectrum", params=_detector_payload()),
                Step(name="identify", action="identify_isotopes", params=_spectrum_payload()),
                Step(name="quantify", action="calibrate_and_mda", params={"line": "Cs-137"}),
                Step(name="decay", action="project_activity", params={"chain": "I-131/Xe-131m"}),
                Step(name="shield", action="assess_shielding", params={"material": "lead"}),
                Step(name="plume", action="model_dispersion", params=_plume_payload()),
                Step(
                    name="assess", action="assess_island", params={"facilities": len(_facilities())}
                ),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the full CRAB KEY pipeline deterministically and capture its results."""
        metrics: dict[str, Any] = canonical_metrics()
        metrics["steps_planned"] = len(plan.steps)
        metrics["facilities_assessed"] = int(metrics["num_facilities"])
        return MissionOutcome(
            success=True,
            results=metrics,
            provenance=Provenance(
                package_version=_PACKAGE_VERSION,
                seed=_seed(),
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
                "a calibrated spectrum and Currie MDA bound what is actually detectable",
                "transient-equilibrium decay changes activity on mission timescales",
                "shielding attenuates exponentially; a breached containment escalates threat",
            ),
        )


# Register CRAB KEY gadgets and provider with the BOND registries.
GADGETS: dict[str, object] = {
    "isotope_library": isotope_library,
    "stability_classes": STABILITY_CLASSES,
    "inhalation_dcf": INHALATION_DCF_SV_BQ,
    "threat_levels": THREAT_LEVELS,
    "library_names": library_names,
    "decay_chains": decay_chains,
    "shielding_materials": MATERIALS,
    "specific_gamma_constants": GAMMA_CONSTANT_MSV_M2_H_GBQ,
}

_PROVIDER = MissionProvider()
GADGET_REGISTRY = GadgetRegistry()
GADGET_REGISTRY.register(_PROVIDER.film, GADGETS)

MISSION_REGISTRY = MissionRegistry()
MISSION_REGISTRY.register(_PROVIDER)
