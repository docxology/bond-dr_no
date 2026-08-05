# Dr. No — CRAB KEY · Agent Working Notes

This is a PROJECT BOND film package. Before modifying anything, follow the
behavioural rules in `docs/agent_instructions.md`, the architecture contract in
`docs/architecture.md`, and the testing philosophy in `docs/testing_philosophy.md`.

## Scope contract

- Work **only** inside this directory. Never touch a sibling BOND package, the
  `bond/` root, or the template repo.
- **Local-only**: no remote, never push. Own git repo with path-scoped commits
  (`git add -A` inside this repo only).

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/dr_no/isotope_profiles.py`, `plume_model.py`, `island_assessment.py`, `spectrum_processing.py`, `decay_chain.py`, `shielding.py`, `dose_assessment.py`, `canonical.py` | Pure domain: no `bond_api`, no `infrastructure` imports. |
| `src/dr_no/mission.py` | The mission adapter (imports `bond_api`); thin adapter over the domain core and `canonical` metrics. |
| `src/dr_no/cli.py` | Thin phase driver; imports `bond_api` only to run the mission flow. |
| `src/dr_no/manuscript_variables.py` | Token hydration from `manuscript/config.yaml` + the live `canonical_metrics()` surface. |
| `scripts/` | Thin CLI wrappers; business logic stays in `src/`. |

The domain core must remain importable **without** bond-api (fallback if the
path dependency ever fails) — mission.py is the thin adapter.

## Protocol integration

- `src/dr_no/mission.py` exports `MissionProvider` at module top level (slug
  `dr_no`), implementing the frozen `bond_api.protocol.MissionProvider` surface:
  `film`, `brief()`, `recon()`, `plan()`, `execute()`, `debrief()`.
- Gadgets are registered with `bond_api.registry.GadgetRegistry` at import time.
- Discovery finds the package because `src/dr_no/mission.py` exists and `src/`
  is on `sys.path` in tests/CLI.

## Verification (run before declaring done)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
git status --short   # clean after commit
```

Report: modules + concepts, coverage %, commit SHA.
