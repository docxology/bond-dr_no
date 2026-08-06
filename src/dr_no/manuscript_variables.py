"""Manuscript variable hydration for the CRAB KEY (Dr. No) mission report.

Every ``{{TOKEN}}`` in ``manuscript/[0-9]*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
live domain surface (isotope library, stability classes, threat bands). Metrics
are never hand-authored in prose — they flow through this module so the
manuscript cannot drift from the code.

Consuming orchestrator: ``scripts/z_generate_manuscript_variables.py`` (thin
wrapper). Live cross-reference gate: ``tests/test_manuscript_variables.py``.
"""

from __future__ import annotations

import math
import platform
import re
from pathlib import Path
from typing import Any

import yaml

from dr_no import CODENAME, FILM
from dr_no.canonical import canonical_metrics, scenario_fingerprint
from dr_no.decay_chain import chain_names, decay_chains, lookup_chain
from dr_no.dose_assessment import specific_gamma_constant
from dr_no.island_assessment import THREAT_LEVELS
from dr_no.isotope_profiles import isotope_library, library_names, total_gamma_lines
from dr_no.plume_model import STABILITY_CLASSES
from dr_no.scenario import DEFAULT_CONFIG_PATH, PACKAGE_ROOT, load_scenario
from dr_no.shielding import MATERIALS

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "PACKAGE_ROOT",
    "generate_variables",
    "load_manuscript_config",
    "resolve_manuscript_tree",
]

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def load_manuscript_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate ``manuscript/config.yaml`` (or an explicit path)."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"manuscript config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise TypeError(f"manuscript config must be a top-level mapping, got {type(data).__name__}")
    return data


def generate_variables(
    *,
    config_path: str | Path | None = None,
    require_outputs: bool = True,
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), verify the isotope library is
            non-empty — the strict-mode gate that keeps metrics live.
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise TypeError("manuscript config 'paper' section must be a mapping")
    library = library_names()
    if require_outputs and not library:
        raise ValueError("isotope library is empty — dr_no failed to expose its isotopes")
    scenario = load_scenario(config_path)
    metrics = canonical_metrics(scenario)
    chains = decay_chains()
    detector = scenario.detector
    plume = scenario.plume
    shield = scenario.shielding_probe
    probe = scenario.external_dose_probe
    parent = lookup_chain(scenario.decay_projection.chain).members[0]
    return {
        # --- identity -------------------------------------------------------
        "DRNO_TITLE": str(paper.get("title", "")),
        "DRNO_SUBTITLE": str(paper.get("subtitle", "")),
        "DRNO_VERSION": str(paper.get("version", "")),
        "DRNO_FILM": FILM,
        "DRNO_CODENAME": CODENAME,
        "MISSION_SEED": str(scenario.seed),
        # --- library surface ------------------------------------------------
        "NUM_ISOTOPES": str(len(library)),
        "NUM_GAMMA_LINES": str(total_gamma_lines()),
        "NUM_DECAY_CHAINS": str(len(chains)),
        "DECAY_CHAIN_NAMES_CSV": ", ".join(chain_names()),
        "NUM_STABILITY_CLASSES": str(len(STABILITY_CLASSES)),
        "STABILITY_CLASSES_CSV": ", ".join(STABILITY_CLASSES),
        "NUM_SHIELDING_MATERIALS": str(len(MATERIALS)),
        "SHIELDING_MATERIALS_CSV": ", ".join(MATERIALS),
        "NUM_THREAT_BANDS": str(len(THREAT_LEVELS)),
        "THREAT_BANDS_CSV": ", ".join(THREAT_LEVELS),
        "THREAT_BAND_EDGES_SV_S_CSV": ", ".join(
            _sci(edge) for edge in scenario.threat.band_edges_sv_s
        ),
        "SHELTER_DOSE_RATE_SV_S": _sci(scenario.threat.shelter_dose_rate_sv_s),
        "LIBRARY_MIN_LINE_KEV": f"{_library_line_bounds()[0]:.2f}",
        "LIBRARY_MAX_LINE_KEV": f"{_library_line_bounds()[1]:.2f}",
        # --- declared scenario (mission: block of config.yaml) ---------------
        "DETECTOR_ACQUISITION_S": f"{detector.acquisition_time_s:g}",
        "DETECTOR_EFFICIENCY": f"{detector.detector_efficiency:g}",
        "DETECTOR_RESOLUTION_KEV": f"{detector.resolution_at_1332_keV:g}",
        "DETECTOR_ENERGY_MIN_KEV": f"{detector.energy_min_keV:g}",
        "DETECTOR_ENERGY_MAX_KEV": f"{detector.energy_max_keV:g}",
        "DETECTOR_BINS": str(detector.bins),
        "SOURCE_MIXTURE_CSV": ", ".join(
            f"{iso} ({_sci(act)} Bq)" for iso, act in sorted(scenario.source_activities_bq.items())
        ),
        "PLUME_SOURCE_Q_BQ_S": _sci(plume.source_Q_bq_s),
        "PLUME_WIND_SPEED_M_S": f"{plume.wind_speed_m_s:g}",
        "PLUME_STABILITY_CLASS": plume.stability,
        "PLUME_RELEASE_HEIGHT_M": f"{plume.release_height_m:g}",
        "ACTION_CONCENTRATION_BQ_M3": _sci(scenario.action_concentration_bq_m3),
        "NUM_FACILITIES": str(len(scenario.facilities)),
        "FACILITY_NAMES_CSV": ", ".join(f.name for f in scenario.facilities),
        "SHIELD_MATERIAL": shield.material,
        "SHIELD_THICKNESS_CM": f"{shield.thickness_cm:g}",
        "SHIELD_ENERGY_KEV": f"{shield.hvl_energy_MeV * 1000.0:g}",
        "TVL_MATERIAL": shield.tvl_material,
        "TVL_ENERGY_KEV": f"{shield.tvl_energy_MeV * 1000.0:g}",
        "DOSE_PROBE_ISOTOPE": probe.isotope,
        "DOSE_PROBE_DISTANCE_M": f"{probe.distance_m:g}",
        # --- computed metrics ------------------------------------------------
        "DETECTED_PEAKS": str(metrics["detected_peaks"]),
        "TOP_ISOTOPE": str(metrics["top_isotope"]),
        "QUANTIFIED_LINE": str(metrics["quantified_line"]),
        "QUANTIFIED_LINE_KEV": f"{float(metrics['quantified_line_energy_kev']):.2f}",
        "NET_AREA_QUANTIFIED": _sci(float(metrics["net_area_quantified"])),
        "DECAY_CHAIN_PROJECTED": str(metrics["decay_chain"]),
        "DECAY_ELAPSED_DAYS": f"{float(metrics['decay_elapsed_days']):g}",
        "PARENT_HALF_LIFE_DAYS": f"{parent.half_life_s / 86400.0:.2f}",
        "PARENT_FRACTION_REMAINING_PCT": (
            f"{float(metrics['parent_fraction_remaining']) * 100.0:.1f}"
        ),
        "CALIBRATION_R2": f"{float(metrics['calibration_r2']):.4f}",
        "CALIBRATION_GAIN": f"{float(metrics['calibration_gain_kev_per_ch']):.3f}",
        "MDA_BQ": f"{float(metrics['mda_bq']):.1f}",
        "HVL_CM": f"{float(metrics['hvl_cm']):.3f}",
        "TVL_CM": f"{float(metrics['tvl_cm']):.2f}",
        "TRANSMISSION_SHIELD_PCT": f"{float(metrics['transmission_shield']) * 100.0:.2f}",
        "EXTERNAL_DOSE_PROBE_MSV_H": _sci(float(metrics["external_dose_probe_msv_h"])),
        "GAMMA_CONSTANT_PROBE": f"{specific_gamma_constant(probe.isotope):.3f}",
        "PEAK_CONCENTRATION_BQ_M3": _sci(float(metrics["peak_concentration_bq_m3"])),
        "ISLAND_THREAT": str(metrics["island_threat"]),
        "DOWNWIND_EXTENT_M": f"{float(metrics['downwind_extent_m']):.0f}",
        "ACTION_THRESHOLD_VERDICT": _threshold_verdict(float(metrics["downwind_extent_m"])),
        "CONTAINMENT_ACTIONS_CSV": ", ".join(
            f"{name}: {action}"
            for name, action in sorted(dict(metrics["containment_actions"]).items())
        ),
        # --- environment ------------------------------------------------------
        # No wall clock here, by design. A ``datetime.now()`` stamp used to be
        # rendered into the prose and the token JSON, which silently falsified
        # the manuscript's byte-identical-regeneration claim: every rerun wrote
        # different bytes. The provenance question the stamp was reaching for
        # is *what was run*, and the scenario fingerprint answers that from a
        # committed source without reintroducing nondeterminism.
        "NUMPY_VERSION": _import_version("numpy"),
        "PYTHON_VERSION": platform.python_version(),
        "SCENARIO_FINGERPRINT": scenario_fingerprint(scenario),
    }


def _threshold_verdict(downwind_extent_m: float) -> str:
    """Prose for whether the centreline ever reaches the declared action threshold.

    The manuscript sentence used to presuppose an exceedance ("stays above the
    threshold out to X m"), which reads as a measurement even when the isopleth
    is empty and X is zero. Deriving the clause from the computed extent means
    the null result is reported as a null result rather than as a very short
    contaminated strip.
    """
    if downwind_extent_m <= 0.0:
        return "never reaches that level at any downwind distance"
    return "stays at or above it from the ground-level maximum outward"


def _sci(value: float, *, digits: int = 2) -> str:
    """Format a value as inline LaTeX scientific notation, e.g. ``$4.0\\times10^{5}$``.

    Python's ``:.3g`` renders 400000.0 as ``4e+05``, which reads as a code
    literal rather than a quantity. Values already comfortable in decimal
    (``1e-3`` to ``1e5``) are returned plain, so only genuinely large or small
    magnitudes pick up the exponent form.
    """
    if value == 0.0:
        return "0"
    exponent = math.floor(math.log10(abs(value)))
    if -3 <= exponent < 5:
        plain = f"{value:.{max(digits - exponent, 0)}f}"
        # Strip trailing zeros only in the fractional part: a bare rstrip("0")
        # turns "1000" into "1" (and "1,000" into "1,").
        return plain.rstrip("0").rstrip(".") if "." in plain else plain
    mantissa = value / (10.0**exponent)
    return f"${mantissa:.{digits}f}\\times10^{{{exponent}}}$"


def _library_line_bounds() -> tuple[float, float]:
    """Lowest and highest gamma-line energies (keV) across the whole library."""
    energies = [
        energy for profile in isotope_library().values() for energy, _ in profile.gamma_lines
    ]
    if not energies:
        raise ValueError("isotope library exposes no gamma lines")
    return min(energies), max(energies)


def _import_version(module: str) -> str:
    """Report an installed dependency's ``__version__``.

    Deliberately does **not** swallow ``ImportError``. This is only ever called
    for declared runtime dependencies; returning ``""`` for a missing one would
    put an empty version string into the reproducibility section of the
    manuscript and pass every gate.

    Raises:
        ModuleNotFoundError: the module is not importable.
        AttributeError: the module exposes no ``__version__``.
    """
    import importlib

    imported = importlib.import_module(module)
    version = getattr(imported, "__version__", None)
    if version is None:
        raise AttributeError(f"module {module!r} exposes no __version__ to report")
    return str(version)


def resolve_manuscript_tree(
    variables: dict[str, str],
    *,
    manuscript_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict: bool = True,
) -> tuple[Path, list[str]]:
    """Copy each ``NN_*.md`` manuscript section to ``output/manuscript/``, substituting tokens.

    Only numbered section files are copied (not sidecars such as ``SYNTAX.md``).
    In strict mode any leftover ``{{TOKEN}}`` fails resolution so the manuscript
    can never render with raw braces.

    Returns the output directory and the sorted list of resolved file names.
    """
    manuscript_dir = (
        Path(manuscript_dir) if manuscript_dir is not None else PACKAGE_ROOT / "manuscript"
    )
    output_dir = (
        Path(output_dir) if output_dir is not None else PACKAGE_ROOT / "output" / "manuscript"
    )
    resolved: list[str] = []
    for source in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace("{{" + token + "}}", value)
        unresolved = sorted(set(_TOKEN_RE.findall(text)))
        if unresolved and strict:
            raise ValueError(f"unresolved manuscript tokens in {source.name}: {unresolved}")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / source.name).write_text(text, encoding="utf-8")
        resolved.append(source.name)
    return output_dir, resolved
