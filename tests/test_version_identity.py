"""The package version must be declared identically in all three places.

``pyproject.toml``, ``dr_no.__version__``, and ``manuscript/config.yaml`` each
carry a version, and each is consumed by something different: the build, the
mission provenance block, and the manuscript title page. Before this gate
existed they had already drifted — pyproject and config said ``0.1.0`` while
``__version__`` said ``0.2.0``, so a mission outcome and the report describing
it claimed different software versions.
"""

from __future__ import annotations

import re
from pathlib import Path

import tomllib
import yaml

import dr_no

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def _pyproject_version() -> str:
    with (PACKAGE_ROOT / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def _config_version() -> str:
    with (PACKAGE_ROOT / "manuscript" / "config.yaml").open("r", encoding="utf-8") as handle:
        return str(yaml.safe_load(handle)["paper"]["version"])


def test_all_three_declarations_agree() -> None:
    assert _pyproject_version() == dr_no.__version__ == _config_version()


def test_version_is_semver() -> None:
    assert _SEMVER.match(dr_no.__version__), f"not semver: {dr_no.__version__!r}"


def test_provenance_reports_the_declared_version() -> None:
    """The mission's provenance block carries the same version, not a copy."""
    from dr_no.mission import MissionProvider

    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    assert outcome.provenance.package_version == _pyproject_version()
