---
name: dr-no
description: PROJECT BOND film package — Dr. No (1962), codename CRAB KEY. Deterministic radiation/isotope forensics; drive mission, gates, figures.
version: 0.2.0
author: docxology
license: MIT
tags: [bond, film, radiation-forensics, isotope-identification, plume-dispersion, thin-orchestrator]
---

# dr-no — CRAB KEY

Project-scoped skill for the PROJECT BOND film package in this repo
(`bond-dr_no`, upstream <https://github.com/docxology/bond-dr_no>; film "Dr. No",
1962, mission codename CRAB KEY). Load this when working inside the package.

## When to Use

- Running the mission (`brief` / `recon` / `plan` / `execute` / `debrief` /
  `full` / `render`), editing `src/`, regenerating figures, or hydrating the
  manuscript.
- Implementing or verifying the BOND-API `MissionProvider` adapter and register
  integration.
- Validating the guardrails (thin-orchestrator, no-mocks, ≥90% coverage,
  determinism, zero lineage, path-scoped commits).

## Quick Reference (from the package root)

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/run_mission.py full        # five-stage mission
uv run python scripts/run_mission.py render      # gamma spectrum + plume figures
uv run python scripts/z_generate_manuscript_variables.py   # hydrate {{TOKEN}}s
```

## Domain core

- `src/dr_no/isotope_profiles.py` — gamma-spectrum isotope identification
  (real 10-isotope library, detector synthesis, peak detection, identification).
- `src/dr_no/spectrum_processing.py` — energy calibration, net photopeak area,
  Currie MDA.
- `src/dr_no/decay_chain.py` — Bateman decay chains over five real parent↔
  daughter pairs; transient equilibrium; fraction-remaining.
- `src/dr_no/shielding.py` — exponential attenuation (real mass-attenuation
  tables: lead/iron/concrete/water), HVL/TVL, required thickness.
- `src/dr_no/dose_assessment.py` — external (Γ + inverse-square), inhalation,
  combined, integrated dose.
- `src/dr_no/plume_model.py` — Gaussian plume dispersion (Pasquill–Gifford A–F).
- `src/dr_no/island_assessment.py` — dose-rate, threat bands, containment,
  island aggregation.
- `src/dr_no/canonical.py` — **single-source-of-truth** scenario + metrics;
  consumed by BOTH `mission.execute()` results and manuscript `{{TOKEN}}`s.
- `src/dr_no/mission.py` — the ONLY module importing `bond_api`; exposes
  `MissionProvider` (slug `dr_no`) and registers 8 gadgets.

## Pitfalls

- `mission.py` is the protocol seam. Domain modules must stay importable
  WITHOUT bond-api; never add `bond_api` imports to the pure core.
- Pasquill–Gifford sigma coefficients are kilometre-based — `sigma_y`/`sigma_z`
  convert to metres (`*1000`). Revert that and elevated releases produce ~0
  ground concentration.
- No mock framework, no RNG, no wall-clock in artifacts; fixed seed 42.
  Four declared `monkeypatch.setattr` substitutions are inventoried and gated
  in `tests/test_suite_hygiene.py`.
- Path-scoped commits in this repo only; upstream is
  `https://github.com/docxology/bond-dr_no` (default branch `main`).
- `output/` is git-ignored (regenerable); z_generate + render keep it current.
- Manuscript `{{TOKEN}}`s resolve from `src/dr_no/manuscript_variables.py`;
  the cross-ref gate scans `manuscript/[0-9]*.md` only (not SYNTAX.md).

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md) · README:
  [`README.md`](../../../README.md) · TODO: [`TODO.md`](../../../TODO.md)
- BOND suite skill: `bond-suite-package-development`; frozen protocol:
  `references/bond-api-phase1.md` there.
