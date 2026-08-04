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

import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from dr_no import CODENAME, FILM
from dr_no.isotope_profiles import library_names, total_gamma_lines
from dr_no.plume_model import STABILITY_CLASSES

__all__ = ["generate_variables", "load_manuscript_config", "resolve_manuscript_tree"]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

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
    return {
        "DRNO_TITLE": str(paper.get("title", "")),
        "DRNO_SUBTITLE": str(paper.get("subtitle", "")),
        "DRNO_VERSION": str(paper.get("version", "")),
        "DRNO_FILM": FILM,
        "DRNO_CODENAME": CODENAME,
        "NUM_ISOTOPES": str(len(library)),
        "NUM_GAMMA_LINES": str(total_gamma_lines()),
        "NUM_STABILITY_CLASSES": str(len(STABILITY_CLASSES)),
        "STABILITY_CLASSES_CSV": ", ".join(STABILITY_CLASSES),
        "NUMPY_VERSION": _import_version("numpy"),
        "PYTHON_VERSION": platform.python_version(),
        "GENERATION_TIMESTAMP": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def _import_version(module: str) -> str:
    import importlib

    try:
        return str(getattr(importlib.import_module(module), "__version__", ""))
    except ImportError:
        return ""


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
