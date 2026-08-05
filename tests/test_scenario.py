"""Tests for :mod:`dr_no.scenario` — the config-backed mission scenario.

The loader is deliberately strict, so most of this file is negative controls:
each required key, each wrong type, each out-of-range value must raise. A
loader that silently defaulted would let ``manuscript/config.yaml`` drift away
from the computation with every gate still green.

Real YAML files on disk throughout — no mocks, no fake file objects.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from dr_no.scenario import (
    DEFAULT_CONFIG_PATH,
    DetectorSpec,
    FacilitySpec,
    MissionScenario,
    PlumeSpec,
    load_scenario,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _raw_config() -> dict:
    """The real ``manuscript/config.yaml``, parsed."""
    with DEFAULT_CONFIG_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def _write(tmp_path: Path, config: dict) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


# --- the shipped config -------------------------------------------------------


def test_default_config_loads() -> None:
    scenario = load_scenario()
    assert scenario.codename == "CRAB KEY"
    assert scenario.seed == 42
    assert scenario.detector.bins >= 2
    assert scenario.plume.stability in ("A", "B", "C", "D", "E", "F")
    assert len(scenario.facilities) == 2
    assert scenario.quantified_line in scenario.source_activities_bq


def test_load_scenario_is_cached_per_path() -> None:
    """Repeated loads of the same path return the identical cached object."""
    assert load_scenario() is load_scenario()


def test_payload_is_json_safe_and_complete() -> None:
    import json

    payload = load_scenario().as_payload()
    round_tripped = json.loads(json.dumps(payload, sort_keys=True))
    assert round_tripped == payload
    assert set(payload) >= {"spectrum", "detector", "plume", "facilities", "seed"}


def test_missing_config_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_scenario(tmp_path / "absent.yaml")


# --- required keys ------------------------------------------------------------


@pytest.mark.parametrize(
    "key",
    [
        "codename",
        "seed",
        "detector",
        "plume",
        "source_activities_bq",
        "calibration_lines_keV",
        "quantified_line",
        "facilities",
        "decay_projection",
        "shielding_probe",
        "external_dose_probe",
        "action_concentration_bq_m3",
    ],
)
def test_every_required_mission_key_is_enforced(tmp_path: Path, key: str) -> None:
    config = _raw_config()
    del config["mission"][key]
    with pytest.raises(KeyError, match=key):
        load_scenario(_write(tmp_path, config))


def test_missing_mission_block_raises(tmp_path: Path) -> None:
    config = _raw_config()
    del config["mission"]
    with pytest.raises(KeyError, match="mission"):
        load_scenario(_write(tmp_path, config))


@pytest.mark.parametrize("key", ["acquisition_time_s", "detector_efficiency", "bins"])
def test_required_detector_keys_are_enforced(tmp_path: Path, key: str) -> None:
    config = _raw_config()
    del config["mission"]["detector"][key]
    with pytest.raises(KeyError, match=key):
        load_scenario(_write(tmp_path, config))


# --- type guards --------------------------------------------------------------


def test_bare_exponent_float_is_rejected(tmp_path: Path) -> None:
    """PyYAML parses ``2.0e6`` as a string; the loader must not accept it.

    This is the trap the config comment warns about. ``float("2.0e6")`` would
    succeed, so a permissive loader would silently accept a value that YAML
    never treated as a number.
    """
    path = tmp_path / "config.yaml"
    text = DEFAULT_CONFIG_PATH.read_text(encoding="utf-8").replace(
        "source_Q_bq_s: 400000.0", "source_Q_bq_s: 4.0e5"
    )
    path.write_text(text, encoding="utf-8")
    with pytest.raises(TypeError, match="must be a YAML number"):
        load_scenario(path)


def test_boolean_is_not_accepted_as_a_number(tmp_path: Path) -> None:
    """``bool`` subclasses ``int``; ``float(True) == 1.0`` must not slip through."""
    config = _raw_config()
    config["mission"]["plume"]["wind_speed_m_s"] = True
    with pytest.raises(TypeError, match="must be a YAML number"):
        load_scenario(_write(tmp_path, config))


def test_float_where_int_expected_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["detector"]["bins"] = 1200.5
    with pytest.raises(TypeError, match="must be a YAML integer"):
        load_scenario(_write(tmp_path, config))


def test_empty_string_field_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["codename"] = "   "
    with pytest.raises(TypeError, match="non-empty string"):
        load_scenario(_write(tmp_path, config))


def test_non_mapping_section_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["detector"] = [1, 2, 3]
    with pytest.raises(TypeError, match="must be a mapping"):
        load_scenario(_write(tmp_path, config))


def test_facilities_must_be_a_list(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["facilities"] = {"name": "solo"}
    with pytest.raises(TypeError, match="facilities' must be a list"):
        load_scenario(_write(tmp_path, config))


def test_calibration_lines_must_be_a_list(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["calibration_lines_keV"] = 661.66
    with pytest.raises(TypeError, match="calibration_lines_keV' must be a list"):
        load_scenario(_write(tmp_path, config))


def test_top_level_config_must_be_a_mapping(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(TypeError, match="must be a mapping"):
        load_scenario(path)


def test_empty_isotope_mapping_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["source_activities_bq"] = {}
    with pytest.raises(ValueError, match="at least one isotope"):
        load_scenario(_write(tmp_path, config))


# --- range guards -------------------------------------------------------------


@pytest.mark.parametrize(
    ("section", "key", "bad_value", "message"),
    [
        ("detector", "acquisition_time_s", -1.0, "acquisition_time_s must be positive"),
        ("detector", "detector_efficiency", 1.5, "detector_efficiency must be in"),
        ("detector", "resolution_at_1332_keV", 0.0, "resolution_at_1332_keV must be positive"),
        ("detector", "bins", 1, "bins must be >= 2"),
        ("plume", "source_Q_bq_s", -5.0, "source_Q_bq_s must be positive"),
        ("plume", "wind_speed_m_s", 0.0, "wind_speed_m_s must be positive"),
        ("plume", "release_height_m", -2.0, "release_height_m must be non-negative"),
    ],
)
def test_out_of_range_values_are_rejected(
    tmp_path: Path, section: str, key: str, bad_value: object, message: str
) -> None:
    config = _raw_config()
    config["mission"][section][key] = bad_value
    with pytest.raises(ValueError, match=message):
        load_scenario(_write(tmp_path, config))


def test_inverted_energy_range_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["detector"]["energy_min_keV"] = 3000.0
    config["mission"]["detector"]["energy_max_keV"] = 20.0
    with pytest.raises(ValueError, match="0 < min < max"):
        load_scenario(_write(tmp_path, config))


def test_negative_action_concentration_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["action_concentration_bq_m3"] = -1.0
    with pytest.raises(ValueError, match="action_concentration_bq_m3 must be positive"):
        load_scenario(_write(tmp_path, config))


def test_empty_facility_list_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["facilities"] = []
    with pytest.raises(ValueError, match="at least one facility"):
        load_scenario(_write(tmp_path, config))


def test_single_calibration_line_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["calibration_lines_keV"] = [661.66]
    with pytest.raises(ValueError, match="at least two lines"):
        load_scenario(_write(tmp_path, config))


def test_quantified_line_must_be_in_the_source_mixture(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["quantified_line"] = "Am-241"
    with pytest.raises(ValueError, match="is not in"):
        load_scenario(_write(tmp_path, config))


def test_bad_containment_state_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["facilities"][0]["containment"] = "leaky"
    with pytest.raises(ValueError, match="containment must be one of"):
        load_scenario(_write(tmp_path, config))


def test_negative_facility_distance_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["facilities"][0]["x_m"] = -10.0
    with pytest.raises(ValueError, match="x_m must be non-negative"):
        load_scenario(_write(tmp_path, config))


def test_negative_elapsed_days_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["decay_projection"]["elapsed_days"] = -1.0
    with pytest.raises(ValueError, match="elapsed_days must be non-negative"):
        load_scenario(_write(tmp_path, config))


def test_negative_shield_thickness_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["shielding_probe"]["thickness_cm"] = -1.0
    with pytest.raises(ValueError, match="thickness_cm must be non-negative"):
        load_scenario(_write(tmp_path, config))


def test_zero_probe_distance_is_rejected(tmp_path: Path) -> None:
    config = _raw_config()
    config["mission"]["external_dose_probe"]["distance_m"] = 0.0
    with pytest.raises(ValueError, match="distance_m must be positive"):
        load_scenario(_write(tmp_path, config))


# --- dataclass construction ----------------------------------------------------


def test_specs_are_constructible_directly() -> None:
    detector = DetectorSpec(60.0, 0.01, 2.0, 20.0, 3000.0, 1200)
    plume = PlumeSpec(1.0e5, 2.0, "C", 5.0)
    facility = FacilitySpec("dock", 100.0, 0.0, "contained", {"Cs-137": 1.0})
    assert detector.as_payload()["bins"] == 1200.0
    assert plume.as_payload()["stability"] == "C"
    assert facility.as_payload()["isotopes"] == {"Cs-137": 1.0}


def test_scenario_from_config_rejects_non_mapping_root() -> None:
    with pytest.raises(TypeError, match="must be a mapping"):
        MissionScenario.from_config("not a mapping")
