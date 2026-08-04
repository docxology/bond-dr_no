"""CRAB KEY manuscript-variable hydration — thin wrapper over ``dr_no.manuscript_variables``.

Writes the ``{{TOKEN}}`` → value map to ``output/data/manuscript_variables.json``
and renders resolved copies of the numbered manuscript sections to
``output/manuscript/``. Strict by default; pass ``--allow-draft`` to skip the
library-non-empty check.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dr_no.manuscript_variables import generate_variables, resolve_manuscript_tree


def main() -> int:
    allow_draft = "--allow-draft" in sys.argv
    variables = generate_variables(require_outputs=not allow_draft)
    data_dir = ROOT / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "manuscript_variables.json").write_text(
        json.dumps(variables, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    out_dir, files = resolve_manuscript_tree(variables, strict=not allow_draft)
    print(f"resolved {len(files)} manuscript sections -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
