"""Mission-scenario loading — ``manuscript/config.yaml`` is the source of truth.

Every number that parameterises the CRAB KEY assessment (detector geometry,
source inventory, meteorology, facilities, probe points) is declared once, in
the ``mission:`` block of ``manuscript/config.yaml``, and read from there by
:mod:`dr_no.canonical`, :mod:`dr_no.figures.plots`, and
:mod:`dr_no.manuscript_variables`. Nothing re-declares a scenario constant in
Python, so a config edit moves the computation, the figures, and the manuscript
tokens together.

The loader is deliberately **strict**: a missing or wrongly typed key raises
rather than falling back to a built-in default. A silent default would let the
config drift away from the computation without any gate noticing — exactly the
failure this module exists to prevent.

One PyYAML trap is closed here explicitly: under the YAML 1.1 resolver PyYAML
ships, ``2.0e6`` parses as a *string* (the resolver requires a signed
exponent), so :func:`_as_float` rejects non-numeric scalars instead of letting
``float("2.0e6")`` quietly succeed on some values and not others.

Pure domain logic: standard library + PyYAML only, no ``bond_api``.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "PACKAGE_ROOT",
    "DecayProjectionSpec",
    "DetectorSpec",
    "DosePropeSpec",
    "FacilitySpec",
    "MissionScenario",
    "PlumeSpec",
    "ShieldingProbeSpec",
    "load_scenario",
]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

_CONTAINMENT_STATES = ("contained", "breached")


def _require(mapping: dict[str, Any], key: str, where: str) -> Any:
    """Fetch ``key`` from ``mapping`` or raise a located ``KeyError``."""
    if key not in mapping:
        raise KeyError(f"mission config is missing required key {where}.{key!r}")
    return mapping[key]


def _as_mapping(value: Any, where: str) -> dict[str, Any]:
    """Coerce ``value`` to a mapping or raise a located ``TypeError``."""
    if not isinstance(value, dict):
        raise TypeError(
            f"mission config section {where!r} must be a mapping, got {type(value).__name__}"
        )
    return value


def _as_float(value: Any, where: str) -> float:
    """Coerce ``value`` to a float, rejecting YAML strings and booleans.

    ``bool`` is excluded explicitly because it is a subclass of ``int`` and
    ``float(True) == 1.0`` would otherwise pass silently.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(
            f"mission config value {where!r} must be a YAML number, got "
            f"{type(value).__name__} ({value!r}) — write 2.0e+6 or 2000000.0, not 2.0e6"
        )
    return float(value)


def _as_int(value: Any, where: str) -> int:
    """Coerce ``value`` to an int, rejecting floats, strings, and booleans."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"mission config value {where!r} must be a YAML integer, got {value!r}")
    return int(value)


def _as_str(value: Any, where: str) -> str:
    """Coerce ``value`` to a non-empty string or raise."""
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"mission config value {where!r} must be a non-empty string, got {value!r}")
    return value


def _as_activities(value: Any, where: str) -> dict[str, float]:
    """Coerce an ``isotope -> activity`` mapping, validating every entry."""
    mapping = _as_mapping(value, where)
    if not mapping:
        raise ValueError(f"mission config section {where!r} must declare at least one isotope")
    return {
        _as_str(name, f"{where}.key"): _as_float(act, f"{where}.{name}")
        for name, act in mapping.items()
    }


@dataclass(frozen=True)
class DetectorSpec:
    """Detector acquisition geometry and the energy grid it bins onto."""

    acquisition_time_s: float
    detector_efficiency: float
    resolution_at_1332_keV: float
    energy_min_keV: float
    energy_max_keV: float
    bins: int

    def __post_init__(self) -> None:
        if self.acquisition_time_s <= 0:
            raise ValueError("detector.acquisition_time_s must be positive")
        if not 0.0 < self.detector_efficiency <= 1.0:
            raise ValueError("detector.detector_efficiency must be in (0, 1]")
        if self.resolution_at_1332_keV <= 0:
            raise ValueError("detector.resolution_at_1332_keV must be positive")
        if self.energy_min_keV <= 0 or self.energy_max_keV <= self.energy_min_keV:
            raise ValueError("detector energy range must satisfy 0 < min < max")
        if self.bins < 2:
            raise ValueError("detector.bins must be >= 2")

    @classmethod
    def from_config(cls, raw: Any) -> DetectorSpec:
        """Build a detector spec from the ``mission.detector`` config section."""
        section = _as_mapping(raw, "mission.detector")
        where = "mission.detector"
        return cls(
            acquisition_time_s=_as_float(_require(section, "acquisition_time_s", where), where),
            detector_efficiency=_as_float(_require(section, "detector_efficiency", where), where),
            resolution_at_1332_keV=_as_float(
                _require(section, "resolution_at_1332_keV", where), where
            ),
            energy_min_keV=_as_float(_require(section, "energy_min_keV", where), where),
            energy_max_keV=_as_float(_require(section, "energy_max_keV", where), where),
            bins=_as_int(_require(section, "bins", where), where),
        )

    def as_payload(self) -> dict[str, float]:
        """JSON-safe mapping used for mission assets and the provenance hash."""
        return {
            "acquisition_time_s": self.acquisition_time_s,
            "detector_efficiency": self.detector_efficiency,
            "resolution_at_1332": self.resolution_at_1332_keV,
            "energy_min_keV": self.energy_min_keV,
            "energy_max_keV": self.energy_max_keV,
            "bins": float(self.bins),
        }


@dataclass(frozen=True)
class PlumeSpec:
    """Release rate and meteorology driving the Gaussian plume."""

    source_Q_bq_s: float
    wind_speed_m_s: float
    stability: str
    release_height_m: float

    def __post_init__(self) -> None:
        if self.source_Q_bq_s <= 0:
            raise ValueError("plume.source_Q_bq_s must be positive")
        if self.wind_speed_m_s <= 0:
            raise ValueError("plume.wind_speed_m_s must be positive")
        if self.release_height_m < 0:
            raise ValueError("plume.release_height_m must be non-negative")

    @classmethod
    def from_config(cls, raw: Any) -> PlumeSpec:
        """Build a plume spec from the ``mission.plume`` config section."""
        section = _as_mapping(raw, "mission.plume")
        where = "mission.plume"
        return cls(
            source_Q_bq_s=_as_float(_require(section, "source_Q_bq_s", where), where),
            wind_speed_m_s=_as_float(_require(section, "wind_speed_m_s", where), where),
            stability=_as_str(_require(section, "stability", where), where),
            release_height_m=_as_float(_require(section, "release_height_m", where), where),
        )

    def as_payload(self) -> dict[str, float | str]:
        """JSON-safe mapping used for mission assets and the provenance hash."""
        return {
            "source_Q": self.source_Q_bq_s,
            "wind_speed_m_s": self.wind_speed_m_s,
            "stability": self.stability,
            "release_height_m": self.release_height_m,
        }


@dataclass(frozen=True)
class FacilitySpec:
    """A facility declared on the island, with its detected isotope inventory."""

    name: str
    x_m: float
    y_m: float
    containment: str
    isotopes: dict[str, float]

    def __post_init__(self) -> None:
        if self.containment not in _CONTAINMENT_STATES:
            raise ValueError(f"facility containment must be one of {_CONTAINMENT_STATES}")
        if self.x_m < 0:
            raise ValueError("facility x_m must be non-negative")

    @classmethod
    def from_config(cls, raw: Any, index: int) -> FacilitySpec:
        """Build one facility spec from an entry of ``mission.facilities``."""
        where = f"mission.facilities[{index}]"
        section = _as_mapping(raw, where)
        return cls(
            name=_as_str(_require(section, "name", where), where),
            x_m=_as_float(_require(section, "x_m", where), where),
            y_m=_as_float(_require(section, "y_m", where), where),
            containment=_as_str(_require(section, "containment", where), where),
            isotopes=_as_activities(_require(section, "isotopes", where), f"{where}.isotopes"),
        )

    def as_payload(self) -> dict[str, object]:
        """JSON-safe mapping used for the provenance hash."""
        return {
            "name": self.name,
            "x_m": self.x_m,
            "y_m": self.y_m,
            "containment": self.containment,
            "isotopes": dict(self.isotopes),
        }


@dataclass(frozen=True)
class DecayProjectionSpec:
    """Which decay chain to project, and how far forward."""

    chain: str
    elapsed_days: float

    def __post_init__(self) -> None:
        if self.elapsed_days < 0:
            raise ValueError("decay_projection.elapsed_days must be non-negative")

    @classmethod
    def from_config(cls, raw: Any) -> DecayProjectionSpec:
        """Build a decay-projection spec from ``mission.decay_projection``."""
        where = "mission.decay_projection"
        section = _as_mapping(raw, where)
        return cls(
            chain=_as_str(_require(section, "chain", where), where),
            elapsed_days=_as_float(_require(section, "elapsed_days", where), where),
        )


@dataclass(frozen=True)
class ShieldingProbeSpec:
    """The shielding barrier the report quotes: material, thickness, energies."""

    material: str
    thickness_cm: float
    hvl_energy_MeV: float
    tvl_material: str
    tvl_energy_MeV: float

    def __post_init__(self) -> None:
        if self.thickness_cm < 0:
            raise ValueError("shielding_probe.thickness_cm must be non-negative")

    @classmethod
    def from_config(cls, raw: Any) -> ShieldingProbeSpec:
        """Build a shielding-probe spec from ``mission.shielding_probe``."""
        where = "mission.shielding_probe"
        section = _as_mapping(raw, where)
        return cls(
            material=_as_str(_require(section, "material", where), where),
            thickness_cm=_as_float(_require(section, "thickness_cm", where), where),
            hvl_energy_MeV=_as_float(_require(section, "hvl_energy_MeV", where), where),
            tvl_material=_as_str(_require(section, "tvl_material", where), where),
            tvl_energy_MeV=_as_float(_require(section, "tvl_energy_MeV", where), where),
        )


@dataclass(frozen=True)
class DosePropeSpec:
    """The external-dose probe the report quotes: which isotope, at what range."""

    isotope: str
    distance_m: float

    def __post_init__(self) -> None:
        if self.distance_m <= 0:
            raise ValueError("external_dose_probe.distance_m must be positive")

    @classmethod
    def from_config(cls, raw: Any) -> DosePropeSpec:
        """Build an external-dose probe spec from ``mission.external_dose_probe``."""
        where = "mission.external_dose_probe"
        section = _as_mapping(raw, where)
        return cls(
            isotope=_as_str(_require(section, "isotope", where), where),
            distance_m=_as_float(_require(section, "distance_m", where), where),
        )


@dataclass(frozen=True)
class MissionScenario:
    """The complete deterministic CRAB KEY scenario, loaded from config."""

    codename: str
    seed: int
    detector: DetectorSpec
    plume: PlumeSpec
    source_activities_bq: dict[str, float]
    calibration_lines_keV: tuple[float, ...]
    facilities: tuple[FacilitySpec, ...]
    decay_projection: DecayProjectionSpec
    shielding_probe: ShieldingProbeSpec
    external_dose_probe: DosePropeSpec
    action_concentration_bq_m3: float
    quantified_line: str

    def __post_init__(self) -> None:
        if self.action_concentration_bq_m3 <= 0:
            raise ValueError("mission.action_concentration_bq_m3 must be positive")
        if not self.facilities:
            raise ValueError("mission.facilities must declare at least one facility")
        if len(self.calibration_lines_keV) < 2:
            raise ValueError("mission.calibration_lines_keV needs at least two lines")
        if self.quantified_line not in self.source_activities_bq:
            raise ValueError(
                f"mission.quantified_line {self.quantified_line!r} is not in "
                f"mission.source_activities_bq {sorted(self.source_activities_bq)}"
            )

    @classmethod
    def from_config(cls, raw: Any) -> MissionScenario:
        """Build the whole scenario from a parsed ``manuscript/config.yaml``."""
        config = _as_mapping(raw, "config")
        section = _as_mapping(_require(config, "mission", "config"), "mission")
        where = "mission"
        facilities_raw = _require(section, "facilities", where)
        if not isinstance(facilities_raw, list):
            raise TypeError("mission config section 'mission.facilities' must be a list")
        lines_raw = _require(section, "calibration_lines_keV", where)
        if not isinstance(lines_raw, list):
            raise TypeError("mission config section 'mission.calibration_lines_keV' must be a list")
        return cls(
            codename=_as_str(_require(section, "codename", where), where),
            seed=_as_int(_require(section, "seed", where), where),
            detector=DetectorSpec.from_config(_require(section, "detector", where)),
            plume=PlumeSpec.from_config(_require(section, "plume", where)),
            source_activities_bq=_as_activities(
                _require(section, "source_activities_bq", where), "mission.source_activities_bq"
            ),
            calibration_lines_keV=tuple(
                _as_float(line, f"mission.calibration_lines_keV[{i}]")
                for i, line in enumerate(lines_raw)
            ),
            facilities=tuple(
                FacilitySpec.from_config(entry, i) for i, entry in enumerate(facilities_raw)
            ),
            decay_projection=DecayProjectionSpec.from_config(
                _require(section, "decay_projection", where)
            ),
            shielding_probe=ShieldingProbeSpec.from_config(
                _require(section, "shielding_probe", where)
            ),
            external_dose_probe=DosePropeSpec.from_config(
                _require(section, "external_dose_probe", where)
            ),
            action_concentration_bq_m3=_as_float(
                _require(section, "action_concentration_bq_m3", where), where
            ),
            quantified_line=_as_str(_require(section, "quantified_line", where), where),
        )

    def as_payload(self) -> dict[str, object]:
        """JSON-safe mapping of the whole scenario (the provenance hash input)."""
        return {
            "spectrum": dict(self.source_activities_bq),
            "detector": self.detector.as_payload(),
            "plume": self.plume.as_payload(),
            "facilities": [facility.as_payload() for facility in self.facilities],
            "action_concentration_bq_m3": self.action_concentration_bq_m3,
            "decay_projection": {
                "chain": self.decay_projection.chain,
                "elapsed_days": self.decay_projection.elapsed_days,
            },
            "seed": self.seed,
        }


@lru_cache(maxsize=8)
def _load_scenario_cached(path: Path) -> MissionScenario:
    if not path.is_file():
        raise FileNotFoundError(f"mission config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    return MissionScenario.from_config(raw)


def load_scenario(config_path: str | Path | None = None) -> MissionScenario:
    """Load the CRAB KEY scenario from ``manuscript/config.yaml`` (or an override).

    Results are cached per resolved path: the canonical scenario is read once
    per process, so repeated ``canonical_metrics()`` calls stay cheap and
    byte-identical.

    Args:
        config_path: Override for the default ``manuscript/config.yaml``.

    Returns:
        The validated :class:`MissionScenario`.

    Raises:
        FileNotFoundError: the config file does not exist.
        KeyError: a required ``mission:`` key is absent.
        TypeError: a value has the wrong YAML type.
        ValueError: a value is present and well-typed but out of range.
    """
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    return _load_scenario_cached(path.resolve())
