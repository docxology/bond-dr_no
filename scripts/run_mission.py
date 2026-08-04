"""CRAB KEY mission CLI — thin argv-forwarding wrapper over ``dr_no.cli``.

Run: ``uv run python scripts/run_mission.py <brief|recon|plan|execute|debrief|full|render>``

Business logic lives in ``src/``; this script only bootstraps ``src/`` onto
``sys.path`` and forwards to :func:`dr_no.cli.main`.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dr_no.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
