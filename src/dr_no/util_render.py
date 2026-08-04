"""Deterministic render helpers for CRAB KEY CLI output.

Kept separate from :mod:`dr_no.cli` so the phase driver stays purely
structural. Renders each BOND-API protocol dataclass as a stable, key-sorted
text block for terminal display.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

__all__ = ["render_mission_output"]


def _render_value(value: Any, indent: str = "") -> list[str]:
    if is_dataclass(value):
        lines = []
        for f in fields(value):
            sub = _render_value(getattr(value, f.name), indent + "  ")
            lines.append(f"{indent}{f.name}:")
            lines.extend(sub if len(sub) == 1 else [indent + "  " + l for l in sub])
        return lines
    if isinstance(value, dict):
        return [f"{indent}{k}: {v}" for k, v in sorted(value.items())]
    if isinstance(value, (list, tuple)):
        return [f"{indent}- {v}" for v in value]
    return [f"{indent}{value}"]


def render_mission_output(obj: Any) -> str:
    """Render a protocol dataclass as a stable, deterministic text block."""
    lines = _render_value(obj)
    return "\n".join(lines)
