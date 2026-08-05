# Dr. No — CRAB KEY · PROJECT BOND film package

**Film:** Dr. No (1962) · **Mission codename:** CRAB KEY · **Discipline:**
radiation / isotope forensics · **Version:** 0.3.0

A PROJECT BOND suite package. **Local-only** working tree: no remote, never
push. Scope is exactly this directory.

## The film, and what it maps onto

Dr. No's Crab Key is an island whose hidden facility runs on a nuclear reactor,
and the film turns on radiological detection: the Geiger counter, the
contamination scrub-down, the decontamination suits, ore samples that read hot
when they should not. The technical question the film poses is a real one —
*given a gamma measurement taken on an island, what is the material, where is it
going, and how dangerous is it?*

CRAB KEY implements that question as software. Not a stub with a film title on
it: a real gamma-spectroscopy engine over a real emission-line library, real
Bateman decay chains, real NIST-style attenuation data, the standard regulatory
Gaussian plume, and a decision layer that turns all of it into a containment
recommendation.

## What it does

A single deterministic chain, from a declared scenario to an actionable posture:

```
config.yaml ─► synthesize spectrum ─► detect peaks ─► identify isotopes
                                                            │
              calibrate energy · net peak area · Currie MDA ─┤
                                                            │
                        project decay forward (Bateman) ────┤
                                                            │
                    attenuate through a barrier (μ, HVL) ───┤
                                                            │
              disperse downwind (Gaussian plume, P-G A–F) ──┤
                                                            ▼
                         inhaled dose ─► threat band ─► containment action
```

## Modules

Every module in `src/dr_no/`, and what it computes:

| Module | What it computes |
| --- | --- |
| `scenario.py` | Loads and strictly validates the `mission:` block of `manuscript/config.yaml` into frozen dataclasses — the scenario source of truth. |
| `isotope_profiles.py` | Gamma-spectrum forensics: a 10-isotope emission-line library, detector spectrum synthesis (√E-broadened Gaussian photopeaks), peak detection, ranked isotope identification, and exact activity inversion. |
| `spectrum_processing.py` | Quantification: least-squares channel→energy calibration (gain, offset, residuals, R²), background-subtracted net photopeak area with Poisson uncertainty, and the Currie minimum detectable activity. |
| `decay_chain.py` | Time dependence: the Bateman solution over five real parent→daughter chains, activities and populations at *t*, transient-equilibrium ratios, and fraction-remaining / time-to-fraction. |
| `shielding.py` | Barriers: log-log interpolated mass attenuation over four materials, linear attenuation coefficient, transmission factor, half- and tenth-value layers, and required shield thickness. |
| `dose_assessment.py` | Dose accounting: external point-source dose (specific gamma constant, inverse square, optionally shielded), inhalation dose from airborne concentration, combined and time-integrated dose. |
| `plume_model.py` | Atmospheric transport: the steady-state Gaussian plume with ground reflection over Pasquill–Gifford classes A–F, concentration fields, the crosswind maximum, and the downwind isopleth extent. |
| `island_assessment.py` | The decision layer: per-facility dose rate from the plume, five-band threat scoring with breach escalation, island aggregation, and containment actions (none / shelter / evacuation). |
| `canonical.py` | The single metric pass — computes every reported number once, from one scenario, for both the mission provider and the manuscript. |
| `mission.py` | The frozen BOND-API `MissionProvider` adapter (slug `dr_no`) plus the `GADGETS` registry. |
| `manuscript_variables.py` | Hydrates every manuscript `{{TOKEN}}` and resolves the numbered sections into `output/manuscript/`. |
| `cli.py` | Thin mission-phase driver (`brief`/`recon`/`plan`/`execute`/`debrief`/`full`/`render`) with exit codes. |
| `util_render.py` | Deterministic, key-sorted text rendering of the protocol dataclasses. |
| `figures/plots.py` | Three deterministic figures — gamma spectrum, plume field, decay curves — rendered from the same scenario as the metrics. |

## Quick start

```bash
cd projects/working/bond/dr_no
uv sync --extra dev

# The gate
uv run pytest tests/ --cov=src --cov-fail-under=90

# Run the mission
uv run python scripts/run_mission.py full
uv run python scripts/run_mission.py brief      # or recon / plan / execute / debrief

# Regenerate figures and manuscript tokens
uv run python scripts/run_mission.py render
uv run python scripts/z_generate_manuscript_variables.py
```

## The MissionProvider surface

`src/dr_no/mission.py` implements the **frozen** `bond_api.protocol.MissionProvider`
structurally (no inheritance; the runtime-checkable `isinstance` is asserted in
the tests). `bond-cli`, the coordinator, and the orchestrator consume this shape
across packages — **do not change it**:

```python
from dr_no.mission import MissionProvider, GADGETS, MISSION_REGISTRY

provider = MissionProvider()
provider.film                      # "dr_no"

brief    = provider.brief()        # MissionBrief: codename, objectives, assets, constraints
report   = provider.recon(ReconRequest(goal=...))   # ReconReport: findings
plan     = provider.plan(brief)    # MissionPlan: 7 ordered steps
outcome  = provider.execute(plan)  # MissionOutcome: results + Provenance
debrief  = provider.debrief(outcome)                # Debrief: outcome + lessons
```

`GADGETS` is a module-level dict of eight Q-branch entries (`isotope_library`,
`stability_classes`, `inhalation_dcf`, `threat_levels`, `library_names`,
`decay_chains`, `shielding_materials`, `specific_gamma_constants`), registered
on `GADGET_REGISTRY` at import time. Discovery via
`bond_api.discovery.load_provider("dr_no", search_paths=["src"])` works because
`mission.py` exists and `src/` is on `sys.path`.

`execute()` recomputes nothing: it returns `canonical_metrics()` plus two
plan-derived counts, so the mission outcome and the manuscript are the same
computation observed twice.

## The scenario is declared, not hardcoded

Every scenario number — detector geometry, source mixture, meteorology,
facilities, shielding and dose probes, thresholds — lives in the `mission:`
block of `manuscript/config.yaml`. `scenario.py` loads and validates it; the
metrics, the figures, and the manuscript tokens all read it. The loader **raises**
on a missing or mistyped key rather than substituting a default, and
`tests/test_canonical.py` edits the YAML on disk and asserts the metrics move.

## Layout

| Path | Role |
| --- | --- |
| `src/dr_no/` | the implementation (see the module table above) |
| `tests/` | real-data suite; no mock framework, substitutions gated by `tests/test_suite_hygiene.py` |
| `scripts/` | thin CLIs: `run_mission.py`, `z_generate_manuscript_variables.py` |
| `manuscript/` | the mission report, `config.yaml` (scenario of record), `references.bib` |
| `docs/` | architecture, agent instructions, testing doctrine, live counts |
| `output/` | regenerable figures, resolved manuscript, token map — disposable |

## Guarantees

- **Coverage**: line-and-branch on `src/`, gate `--cov-fail-under=90`. Measured
  figure and per-module breakdown: [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).
- **No mock framework, and four declared substitutions** — no `MagicMock`,
  `mocker.patch`, or `unittest.mock` anywhere; every test computes with real
  data. Stated exactly, because the previous wording ("zero mocks, verified by
  scan") was not exact: four `monkeypatch.setattr` calls do replace a
  module-level production attribute — three swap a callable for a trivial real
  one to reach an empty-library guard, one swaps a string constant. The scan
  that sentence pointed at grepped only for mock-framework *names* and was
  structurally blind to them. Both facts are now gated in-suite by
  [`tests/test_suite_hygiene.py`](tests/test_suite_hygiene.py), which reads the
  suite's own source: an undeclared substitution fails the build.
- **Deterministic** — fixed declared scenario, no RNG anywhere in `src/`, no
  wall-clock in any computed metric or in the provenance hash.
- **Typed and linted** — ruff and mypy clean on `src/`, `scripts/`, and `tests/`.
- **Thin orchestrators** — `scripts/` forward argv; logic lives in `src/`.
- **No hand-authored metrics** — every number in the manuscript arrives as a
  token, enforced in both directions plus a bare-numeral scan of the results
  narrative.
- **One version** — `pyproject.toml`, `dr_no.__version__`, and
  `manuscript/config.yaml` are gated to agree.
- **No template-scaffold lineage** in code or docs.

## Documentation

- [`docs/agent_instructions.md`](docs/agent_instructions.md) — start here to work in this package.
- [`docs/architecture.md`](docs/architecture.md) — module-by-module architecture and the frozen protocol.
- [`docs/testing_philosophy.md`](docs/testing_philosophy.md) — the no-mock / real-data / determinism doctrine.
- [`AGENTS.md`](AGENTS.md) — build, test, and verify instructions.
- [`TODO.md`](TODO.md) — remaining work and integration points.
