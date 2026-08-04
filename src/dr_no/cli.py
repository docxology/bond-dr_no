"""CRAB KEY command-line interface — thin mission-phase driver.

Business logic lives in the domain core and :mod:`dr_no.mission`; this module
only wires the five BOND-API phases (brief / recon / plan / execute / debrief)
to ``stdout`` and returns process exit codes (0 on success, 1 on failure).
``scripts/run_mission.py`` is a thin argv-forwarding wrapper over
:func:`main`.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

from dr_no.mission import MISSION_REGISTRY, MissionProvider
from dr_no.util_render import render_mission_output

__all__ = ["main", "run_phase"]

_PHASES = ("brief", "recon", "plan", "execute", "debrief", "full", "render")


def _print(text: str) -> None:
    print(text)


def run_phase(phase: str, provider: MissionProvider) -> int:
    """Execute one mission phase and print its deterministic result."""
    if phase == "brief":
        _print(render_mission_output(provider.brief()))
    elif phase == "recon":
        from bond_api.protocol import ReconRequest  # type: ignore[import-untyped]

        report = provider.recon(ReconRequest(goal="CRAB KEY radiological threat assessment"))
        _print(render_mission_output(report))
    elif phase == "plan":
        _print(render_mission_output(provider.plan(provider.brief())))
    elif phase == "execute":
        outcome = provider.execute(provider.plan(provider.brief()))
        _print(render_mission_output(outcome))
    elif phase == "debrief" or phase == "full":
        from bond_api.protocol import (  # type: ignore[import-untyped]
            ReconRequest,
            run_mission,
        )

        debrief = run_mission(
            provider, ReconRequest(goal="CRAB KEY radiological threat assessment")
        )
        _print(render_mission_output(debrief))
    elif phase == "render":
        from dr_no.figures.plots import render_all

        paths = render_all()
        for path in paths:
            _print(f"wrote {path}")
    else:
        _print(f"unknown phase {phase!r}; expected one of {_PHASES}")
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: ``run_mission.py <phase>`` with an optional explicit slug."""
    argv = list(sys.argv[1:] if argv is None else argv)
    provider: MissionProvider | None = None
    for name in ("dr_no",):
        try:
            provider = MISSION_REGISTRY.lookup(name)
            break
        except KeyError:
            continue
    if provider is None:
        _print("CRAB KEY provider not registered")
        return 2

    phase = argv[0] if argv else "full"
    if phase not in _PHASES:
        # Maintain a tolerant argv shape: an unknown first token is treated as
        # the phase anyway when it is one of the phases; otherwise error.
        _print(f"usage: run_mission.py <{'|'.join(_PHASES)}>")
        return 2
    return run_phase(phase, provider)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
