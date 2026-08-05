"""Crab Key-style island threat assessment — facility detection, risk scoring, containment.

The top of CRAB KEY's decision core. Given a set of detected facilities on an
island, each carrying a measured inventory of gamma-emitting isotopes, plus the
local meteorology and a presumed radiological source, this module:

* converts airborne contaminant concentrations into an inhaled dose rate using
  per-isotope inhalation dose coefficients (breathing-rate weighted) — the
  dose models live in :mod:`dr_no.dose_assessment` and are re-exported here;
* maps that dose rate — together with each facility's containment status and its
  isotope hazard — onto a five-level threat band;
* aggregates per-facility risks into an island-wide assessment; and
* recommends a contamination-containment action (none / shelter / evacuation)
  from the downwind extent of contamination above an action threshold.

Everything is deterministic: pure arithmetic over real dispersion and dose
models, no randomness, no I/O.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from dr_no.dose_assessment import (
    INHALATION_DCF_SV_BQ,
    dose_rate_from_concentration,
)
from dr_no.plume_model import gaussian_plume_concentration, isopleth_extent

__all__ = [
    "INHALATION_DCF_SV_BQ",
    "THREAT_LEVELS",
    "THREAT_RANK",
    "DetectedFacility",
    "IslandAssessment",
    "Meteorology",
    "assess_island",
    "containment_recommendation",
    "dose_rate_from_concentration",
    "facility_threat_level",
]

THREAT_LEVELS = ("LOW", "MODERATE", "HIGH", "SEVERE", "CRITICAL")
#: Rank used for ordering threat levels (higher = worse).
THREAT_RANK: dict[str, int] = {level: i for i, level in enumerate(THREAT_LEVELS)}

#: Threat-level dose-rate thresholds, Sv/s (effective dose rate).
_DOSE_THRESHOLDS_SV_S: tuple[float, ...] = (1.0e-11, 1.0e-9, 1.0e-7, 1.0e-5)

#: Dose-rate threshold (Sv/s) above which shelter-in-place is recommended.
SHELTER_THRESHOLD_SV_S = 1.0e-9

#: Contamination concentration threshold (Bq/m^3) used for exclusion/extent.
ACTION_CONCENTRATION_BQ_M3 = 1000.0


@dataclass(frozen=True)
class DetectedFacility:
    """A facility on the island with a detected radiological inventory."""

    name: str
    x_m: float  # downwind distance from the source reference (m)
    y_m: float  # crosswind offset from the plume centreline (m)
    isotope_activities: dict[str, float]  # isotope -> activity (Bq)
    containment: str  # "contained" | "breached"

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("facility name must be non-empty")
        if self.x_m < 0:
            raise ValueError("facility downwind distance must be non-negative")
        if self.containment not in ("contained", "breached"):
            raise ValueError("facility containment must be 'contained' or 'breached'")


@dataclass(frozen=True)
class Meteorology:
    """Local meteorological conditions governing plume dispersion."""

    wind_speed_m_s: float
    stability: str  # Pasquill-Gifford class A-F
    release_height_m: float = 0.0


def facility_threat_level(
    dose_rate_sv_s: float,
    *,
    containment: str = "contained",
) -> str:
    """Map a dose rate (Sv/s) onto a five-level threat band.

    A breached facility is escalated one band to reflect the loss of shielding
    and the elevated risk of secondary contamination.
    """
    if dose_rate_sv_s < 0:
        raise ValueError("dose rate must be non-negative")
    if containment not in ("contained", "breached"):
        raise ValueError("containment must be 'contained' or 'breached'")
    level = 0
    for threshold in _DOSE_THRESHOLDS_SV_S:
        if dose_rate_sv_s >= threshold:
            level += 1
        else:
            break
    if containment == "breached":
        level += 1
    return THREAT_LEVELS[min(level, len(THREAT_LEVELS) - 1)]


def containment_recommendation(
    dose_rate_sv_s: float,
    concentration_bq_m3: float,
    *,
    evacuation_dose_rate_sv_s: float = SHELTER_THRESHOLD_SV_S,
    action_concentration_bq_m3: float = ACTION_CONCENTRATION_BQ_M3,
) -> str:
    """Recommended contamination-containment action for a location.

    Returns ``"evacuation"`` when the dose rate reaches
    ``evacuation_dose_rate_sv_s``, ``"shelter"`` when the contamination
    concentration reaches ``action_concentration_bq_m3``, and ``"none"``
    otherwise.

    Both thresholds are parameters rather than baked-in constants: the mission
    scenario declares them in ``manuscript/config.yaml`` and they are threaded
    through :func:`assess_island`.
    """
    if dose_rate_sv_s < 0:
        raise ValueError("dose rate must be non-negative")
    if concentration_bq_m3 < 0:
        raise ValueError("concentration must be non-negative")
    if evacuation_dose_rate_sv_s <= 0:
        raise ValueError("evacuation dose-rate threshold must be positive")
    if action_concentration_bq_m3 <= 0:
        raise ValueError("action concentration threshold must be positive")
    if dose_rate_sv_s >= evacuation_dose_rate_sv_s:
        return "evacuation"
    if concentration_bq_m3 >= action_concentration_bq_m3:
        return "shelter"
    return "none"


@dataclass(frozen=True)
class IslandAssessment:
    """Aggregate island-wide radiological threat assessment."""

    overall_level: str  # the island posture = the single worst facility band
    facilities: dict[str, str]  # facility name -> threat level
    downwind_contamination_m: float  # isopleth extent of the action threshold
    containment_actions: dict[str, str]  # facility name -> recommended action

    @property
    def worst_threat(self) -> str:
        """Alias of :attr:`overall_level`.

        The island posture *is* the worst facility band — these were two stored
        fields that were always assigned the same value, which is two places for
        one fact to drift. It is now one field plus this read-only alias, kept
        because the name reads better at call sites that mean "the worst one".
        """
        return self.overall_level

    def maximum_rank(self) -> int:
        """Highest threat rank among facilities.

        Raises:
            ValueError: no facilities were assessed.
        """
        if not self.facilities:
            raise ValueError("no facilities were assessed; maximum rank is undefined")
        return max(THREAT_RANK[level] for level in self.facilities.values())


def _facility_dose_rate(
    facility: DetectedFacility,
    meteo: Meteorology,
    source_Q: float,
) -> tuple[float, float]:
    """Compute (dose_rate_Sv_s, concentration_Bq_m3) at a detected facility."""
    concentration = gaussian_plume_concentration(
        facility.x_m,
        facility.y_m,
        0.0,
        Q=source_Q,
        u=meteo.wind_speed_m_s,
        stability=meteo.stability,
        H=meteo.release_height_m,
    )
    total_activity = sum(facility.isotope_activities.values())
    if total_activity <= 0:
        return 0.0, concentration
    fractions = {iso: act / total_activity for iso, act in facility.isotope_activities.items()}
    rate = dose_rate_from_concentration(concentration, fractions)
    return rate, concentration


def assess_island(
    facilities: Iterable[DetectedFacility],
    meteo: Meteorology,
    *,
    source_Q: float,
    evacuation_dose_rate_sv_s: float = SHELTER_THRESHOLD_SV_S,
    action_concentration_bq_m3: float = ACTION_CONCENTRATION_BQ_M3,
) -> IslandAssessment:
    """Assess the radiological threat across an island of detected facilities.

    Each facility's concentration is evaluated with the plume model at its
    (downwind, crosswind) position; that concentration is converted to an
    inhaled dose rate via its isotope mix; and each facility is assigned a
    threat level and a containment-recommendation action. The island summary
    reports the worst threat and the downwind extent of contamination above the
    action threshold.

    Args:
        facilities: the detected facilities (source-referenced positions).
        meteo: local meteorology driving the plume.
        source_Q: presumed release rate (Bq/s) at the source reference.
        evacuation_dose_rate_sv_s: dose rate (Sv/s) at or above which a facility
            is told to evacuate rather than shelter. Threaded into every
            :func:`containment_recommendation` call.
        action_concentration_bq_m3: contamination concentration (Bq/m³) that
            defines both the shelter trigger and the downwind isopleth extent.

    Returns:
        An :class:`IslandAssessment` aggregating the per-facility results. With
        no facilities the island posture is the floor band, ``"LOW"``.
    """
    facilities_list = list(facilities)
    levels: dict[str, str] = {}
    actions: dict[str, str] = {}
    worst_rank: int = -1
    worst_level: str = THREAT_LEVELS[0]
    for facility in facilities_list:
        rate, concentration = _facility_dose_rate(facility, meteo, source_Q=source_Q)
        level = facility_threat_level(rate, containment=facility.containment)
        levels[facility.name] = level
        actions[facility.name] = containment_recommendation(
            rate,
            concentration,
            evacuation_dose_rate_sv_s=evacuation_dose_rate_sv_s,
            action_concentration_bq_m3=action_concentration_bq_m3,
        )
        rank = THREAT_RANK[level]
        if rank > worst_rank:
            worst_rank = rank
            worst_level = level

    extent = isopleth_extent(
        action_concentration_bq_m3,
        Q=source_Q,
        u=meteo.wind_speed_m_s,
        stability=meteo.stability,
        H=meteo.release_height_m,
    )
    return IslandAssessment(
        overall_level=worst_level,
        facilities=levels,
        downwind_contamination_m=extent,
        containment_actions=actions,
    )
