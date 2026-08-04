# src/dr_no — CRAB KEY domain core

Pure, deterministic, standalone-importable domain logic. `mission.py` is the
only module that imports `bond_api`; the rest must stay importable without it.

| Module | Responsibility |
| --- | --- |
| `isotope_profiles.py` | real gamma-line library, detector synthesis, peak detection, identification |
| `plume_model.py` | Gaussian plume dispersion (Pasquill–Gifford A–F) |
| `island_assessment.py` | dose-rate, threat bands, containment, island aggregation |
| `mission.py` | BOND-API `MissionProvider` adapter + gadget registration |
| `manuscript_variables.py` | `{{TOKEN}}` hydration |
| `figures/plots.py` | deterministic figures |
| `cli.py` / `util_render.py` | thin phase driver + render helpers |

Type hints + docstrings required; ruff + mypy clean. No `infrastructure`
imports anywhere.
