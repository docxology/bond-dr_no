# Dr. No — CRAB KEY · Agent Working Notes

Build, test, and verify instructions for this PROJECT BOND film package.
Behavioural rules live in [`docs/agent_instructions.md`](docs/agent_instructions.md);
the architecture contract in [`docs/architecture.md`](docs/architecture.md); the
testing doctrine in [`docs/testing_philosophy.md`](docs/testing_philosophy.md).
Read those before editing.

## Scope contract

- Work **only** inside this directory. Never touch a sibling BOND package, the
  `bond/` root, or the template repo.
- **Local-only**: no remote, never push. Own git repo, path-scoped commits
  (`git add -A` inside this repo only).

## Build

```bash
cd projects/working/bond/dr_no
uv sync --extra dev
```

`bond-api` is a path dependency (`[tool.uv.sources]` in `pyproject.toml`)
pointing at the sibling `bond-api` package. Runtime deps: numpy, matplotlib,
pyyaml, bond-api. Python ≥3.10; the pinned mypy target is 3.12 (numpy 2.x stubs
use PEP-695 syntax), and the local interpreter is 3.14.

## Test

```bash
# The gate — line + branch coverage on src/, floor 90%
uv run pytest tests/ --cov=src --cov-fail-under=90

# One file / one test
uv run pytest tests/test_canonical.py -v
uv run pytest tests/test_canonical.py::test_metrics_deterministic -v

# Without coverage (faster iteration)
uv run pytest tests/ -q --no-cov
```

Measured counts and per-module coverage: [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).
Regenerate that file from a run you actually performed — never edit its numbers
to match an expectation.

## Run

```bash
uv run python scripts/run_mission.py full      # brief -> recon -> plan -> execute -> debrief
uv run python scripts/run_mission.py brief     # or recon / plan / execute / debrief
uv run python scripts/run_mission.py render    # write the three figures
uv run python scripts/z_generate_manuscript_variables.py   # tokens + resolved sections
```

Exit codes: `0` success, `1` unknown phase via `run_phase`, `2` usage error or
an unregistered provider.

## Verify — the full gate

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
rg -n "MagicMock|mocker\.patch|unittest\.mock" src/ tests/ || echo "No mocks"
git status --short   # clean after commit
```

If anything you changed moves a number, regenerate the artifacts *and* update
`docs/_generated/COUNTS.md`:

```bash
uv run python scripts/run_mission.py render
uv run python scripts/z_generate_manuscript_variables.py
```

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/dr_no/scenario.py` | stdlib + PyYAML. Loads `manuscript/config.yaml`. No `bond_api`. |
| `isotope_profiles`, `spectrum_processing`, `decay_chain`, `shielding`, `dose_assessment`, `plume_model` | Pure domain: stdlib + numpy. No config I/O, no `bond_api`, no `infrastructure`. |
| `island_assessment.py` | Pure; may import `plume_model` + `dose_assessment`. No `bond_api`. |
| `canonical.py` | The single metric pass; imports `scenario` + the domain modules. No `bond_api`. |
| `manuscript_variables.py`, `figures/plots.py` | Consume `canonical` + `scenario`. No `bond_api`. |
| `mission.py`, `cli.py` | The **only** modules importing `bond_api`. |
| `scripts/` | Thin argv-forwarding wrappers. No business logic. |

The domain core must stay importable **without** bond-api, so a broken protocol
dependency can never take the forensics down.

## Protocol integration — frozen

`src/dr_no/mission.py` exports `MissionProvider` at module top level (slug
`dr_no`) implementing the frozen `bond_api.protocol.MissionProvider`:
`film`, `brief()`, `recon()`, `plan()`, `execute()`, `debrief()`. Gadgets are
registered on `bond_api.registry.GadgetRegistry` at import time via the
module-level `GADGETS` dict; the provider registers on `MissionRegistry`.

**Do not change that public shape** — `bond-cli`, the coordinator's reconcile
pass, and the orchestrator consume it across packages. Deepen inside the package
instead. `bond_api.discovery.load_provider("dr_no", search_paths=["src"])` is
exercised in `tests/test_mission.py` and must keep working.

## Two invariants that bite

- **Scenario numbers live in `manuscript/config.yaml`**, never as Python
  literals. Adding one means: config key → dataclass field + validation in
  `scenario.py` → consumption in `canonical.py` → a binding test that moves the
  value and asserts the metric moves.
- **Manuscript metrics are tokens**, never hand-authored prose numbers. Three
  tests enforce it: unresolved token, orphaned token, and a bare-numeral scan of
  the results narrative.

## Reporting

Report modules touched, measured coverage %, test count, and commit SHA — each
from output you actually read. If a gate could not be run, say so.
