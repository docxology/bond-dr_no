"""Tests for the CRAB KEY BOND-API mission provider (:mod:`dr_no.mission`).

Exercises the frozen protocol contract, the full five-stage flow, the
registered registries/gadgets, and slug-based discovery via ``bond_api``. No
mocks — the provider and registries are real, deterministic implementations.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from bond_api.protocol import (
    Debrief,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    MissionProvider,
    Provenance,
    ReconReport,
    ReconRequest,
    run_mission,
)

from dr_no.mission import (
    GADGET_REGISTRY,
    GADGETS,
    MISSION_REGISTRY,
    _detector_energies,
    _input_hash,
)
from dr_no.mission import (
    MissionProvider as DrNoProvider,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


@pytest.fixture()
def provider() -> DrNoProvider:
    return DrNoProvider()


def test_provider_satisfies_protocol(provider: DrNoProvider) -> None:
    assert isinstance(provider, MissionProvider)
    assert provider.film == "dr_no"


def test_brief(provider: DrNoProvider) -> None:
    brief = provider.brief()
    assert isinstance(brief, MissionBrief)
    assert brief.film == "dr_no"
    assert brief.codename == "CRAB KEY"
    assert len(brief.objectives) == 3
    assert len(brief.assets) == 3


def test_recon(provider: DrNoProvider) -> None:
    report = provider.recon(ReconRequest(goal="assess the island"))
    assert isinstance(report, ReconReport)
    assert any(f.label == "goal" for f in report.findings)
    assert len(report.findings) >= 3


def test_plan(provider: DrNoProvider) -> None:
    plan = provider.plan(provider.brief())
    assert isinstance(plan, MissionPlan)
    names = [step.name for step in plan.steps]
    assert names == ["spectrum", "identify", "plume", "assess"]


def test_execute(provider: DrNoProvider) -> None:
    outcome = provider.execute(provider.plan(provider.brief()))
    assert isinstance(outcome, MissionOutcome)
    assert outcome.success is True
    assert isinstance(outcome.provenance, Provenance)
    assert outcome.provenance.seed == 42
    assert outcome.provenance.input_hash == _input_hash()
    results = outcome.results
    assert results["top_isotope"] in ("Cs-137", "Co-60")
    assert results["island_threat"] in ("LOW", "MODERATE", "HIGH", "SEVERE", "CRITICAL")
    assert results["downwind_extent_m"] >= 0
    assert results["steps_planned"] == 4
    assert "Cs-137" in results["identified_isotopes"]
    assert "Co-60" in results["identified_isotopes"]


def test_execute_deterministic(provider: DrNoProvider) -> None:
    plan = provider.plan(provider.brief())
    r1 = provider.execute(plan).results
    r2 = provider.execute(plan).results
    assert r1 == r2


def test_debrief(provider: DrNoProvider) -> None:
    outcome = provider.execute(provider.plan(provider.brief()))
    debrief = provider.debrief(outcome)
    assert isinstance(debrief, Debrief)
    assert len(debrief.lessons) >= 1
    assert debrief.outcome is outcome


def test_full_mission_flow(provider: DrNoProvider) -> None:
    debrief = run_mission(provider, ReconRequest(goal="rate the island"))
    assert debrief.outcome.success is True
    assert "top_isotope" in debrief.outcome.results


def test_detector_energies_shape() -> None:
    energies = _detector_energies()
    assert energies.size == 1200
    assert energies.min() >= 20.0


def test_input_hash_is_stable() -> None:
    assert isinstance(_input_hash(), str)
    assert len(_input_hash()) == 16
    assert _input_hash() == _input_hash()


def test_provider_registered(provider: DrNoProvider) -> None:
    assert "dr_no" in MISSION_REGISTRY
    assert MISSION_REGISTRY.lookup("dr_no").film == "dr_no"


def test_gadgets_registered() -> None:
    for gadget in (
        "isotope_library",
        "stability_classes",
        "inhalation_dcf",
        "threat_levels",
        "library_names",
    ):
        assert GADGET_REGISTRY.contains("dr_no", gadget)
    assert callable(GADGETS["isotope_library"])


def test_provider_accessible_from_registry(provider: DrNoProvider) -> None:
    provider_from_registry = MISSION_REGISTRY.providers()[0]
    assert isinstance(provider_from_registry, MissionProvider)


def test_discovery_loads_provider_by_slug() -> None:
    from bond_api.discovery import load_provider

    sys.path.insert(0, str(SRC))
    try:
        discovered = load_provider("dr_no", search_paths=[str(SRC)])
    finally:
        sys.path.remove(str(SRC))
    assert discovered.film == "dr_no"
    assert discovered.brief().codename == "CRAB KEY"
