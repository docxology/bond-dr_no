# src/dr_no — CRAB KEY domain core

Pure, deterministic, standalone-importable domain logic. `mission.py` and
`cli.py` are the only modules that import `bond_api`; everything else must stay
importable without it, so a broken protocol dependency cannot take the
forensics down.

| Module | Responsibility |
| --- | --- |
| `scenario.py` | loads + strictly validates the `mission:` block of `manuscript/config.yaml` into frozen dataclasses — the scenario source of truth |
| `isotope_profiles.py` | real gamma-line library, detector synthesis, peak detection, ranked identification, activity inversion |
| `spectrum_processing.py` | least-squares energy calibration, net photopeak area with Poisson uncertainty, Currie MDA |
| `decay_chain.py` | Bateman decay chains over real half-lives; equilibrium and time projection |
| `shielding.py` | log-log interpolated mass attenuation, transmission, HVL/TVL, required thickness |
| `dose_assessment.py` | external (point-source, shielded), inhalation, combined, and integrated dose |
| `plume_model.py` | Gaussian plume dispersion (Pasquill–Gifford A–F), fields, crosswind max, isopleth extent |
| `island_assessment.py` | per-facility dose rate, threat bands, containment actions, island aggregation |
| `canonical.py` | the single metric pass — every reported number, computed once, for mission **and** tokens |
| `mission.py` | the frozen BOND-API `MissionProvider` adapter + `GADGETS` registration |
| `manuscript_variables.py` | `{{TOKEN}}` hydration and manuscript resolution |
| `figures/plots.py` | three deterministic figures, rendered from the same scenario as the metrics |
| `cli.py` / `util_render.py` | thin phase driver + deterministic render helpers |

## Rules

- Type hints and docstrings on everything public; ruff + mypy clean.
- No `infrastructure` imports anywhere.
- **No scenario constant in Python** — it belongs in `manuscript/config.yaml`.
- **No reported metric computed outside `canonical.py`** — `mission.py` and
  `manuscript_variables.py` both read `canonical_metrics()`.
- **No failure path that returns a plausible number.** Raise instead.

Architecture detail, including the frozen protocol surface:
[`../docs/architecture.md`](../docs/architecture.md).
