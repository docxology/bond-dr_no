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


#: The slug this CLI drives. The provider registers itself under this name at
#: ``dr_no.mission`` import time; a lookup miss means the frozen registration
#: contract is broken, which is an error, not something to work around.
SLUG = "dr_no"


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: ``run_mission.py <phase>``.

    Exit codes: ``0`` success, ``1`` unknown phase reached via
    :func:`run_phase`, ``2`` usage error or an unregistered provider.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        provider = MISSION_REGISTRY.lookup(SLUG)
    except KeyError:
        _print(f"CRAB KEY provider {SLUG!r} not registered")
        return 2

    phase = argv[0] if argv else "full"
    if phase not in _PHASES:
        _print(f"usage: run_mission.py <{'|'.join(_PHASES)}>")
        return 2
    return run_phase(phase, provider)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
