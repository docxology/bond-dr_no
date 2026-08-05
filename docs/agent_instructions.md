# Agent instructions — CRAB KEY (dr_no)

Concrete operational instructions for working inside this package. Read this
first; it is mandatory before any edit.

## 1. Scope

Work only inside `projects/working/bond/dr_no/`. Never touch a sibling BOND
package, the `bond/` root, or the template repo. This tree is **local-only**:
there is no remote and nothing is ever pushed. Commit inside this repo only,
with path-scoped commits.

## 2. Read order before editing

| Before you edit… | Read |
| --- | --- |
| anything in `src/` or `scripts/` | `architecture.md` |
| anything in `tests/` | `testing_philosophy.md` |
| anything in `manuscript/` | `../manuscript/AGENTS.md` and §5 below |
| `src/dr_no/mission.py` | `architecture.md` §3 — **frozen surface** |

## 3. Where things go

- **Business logic lives in `src/`.** `scripts/` are argv-forwarding wrappers
  that bootstrap `src/` onto `sys.path` and call into it. If you find yourself
  writing an `if` in `scripts/`, it belongs in `src/`.
- **Scenario numbers live in `manuscript/config.yaml`**, in the `mission:`
  block — never as a Python literal. `src/dr_no/scenario.py` loads them.
  Adding a scenario parameter means: add the key to the config, add the field
  and its validation to the matching dataclass, consume it in `canonical.py`,
  and add a binding test that moves it and asserts the metric moves.
- **New metrics go through `canonical.py`.** Never compute a reported number in
  `mission.py` or `manuscript_variables.py`; both must read
  `canonical_metrics()`. That is what keeps the mission outcome and the
  manuscript in agreement.

## 4. Do not break the protocol

`src/dr_no/mission.py` implements the **frozen** `bond_api` `MissionProvider`.
`bond-cli`, the coordinator, and the orchestrator consume it across packages.
Do not change the public shape of:

- the top-level `MissionProvider` class or its `film = "dr_no"` slug;
- `brief()`, `recon()`, `plan()`, `execute()`, `debrief()` — names, arity, or
  return types;
- the module-level `GADGETS` dict, `GADGET_REGISTRY`, or `MISSION_REGISTRY`.

Deepen **inside** the package instead: new domain modules, richer metrics in
`canonical.py`, more scenario parameters. Discovery must keep working —
`bond_api.discovery.load_provider("dr_no", ...)` is exercised by the tests.

## 5. Manuscript rules

Every numeric metric in a numbered section is a `{{TOKEN}}` resolved by
`scripts/z_generate_manuscript_variables.py` from
`src/dr_no/manuscript_variables.py`. **Never hand-author a number in prose.**

Adding a quantitative claim means: add the metric to `canonical_metrics()`, add
the token to `generate_variables()`, reference the token in the section, and
regenerate. Three gates will hold you to it — unresolved token, orphaned token,
and bare numeral in the results narrative.

`references.bib` must contain only sources you can actually verify. If you are
not confident a reference is real, **remove it** rather than ship it. Two were
removed on exactly those grounds; the header comment in `references.bib` records
which and why.

## 6. Guardrails

- No mock framework (`MagicMock`, `mocker.patch`, `unittest.mock`). Real data
  and real computation only.
- Deterministic: fixed scenario, no untracked randomness, no wall-clock in
  persisted artifacts.
- Type hints and docstrings on everything public; ruff and mypy clean on `src/`,
  `scripts/`, and `tests/`.
- No template-scaffold lineage strings in this tree.
- **Never let a failure path return a plausible number.** Raise instead. A zero
  calibration gain, an empty version string, or a 1 m contamination extent all
  render as if they were measurements. Every one of those was a real defect
  here.

## 7. Verification gate — run all of it before declaring done

```bash
cd projects/working/bond/dr_no

uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
git status --short   # clean after commit
```

If you changed anything that moves a number, also regenerate the artifacts:

```bash
uv run python scripts/run_mission.py render
uv run python scripts/z_generate_manuscript_variables.py
```

Then update `docs/_generated/COUNTS.md` from the run you actually just did —
never by editing the numbers to match what you expected.

## 8. Reporting

Report modules touched, the measured coverage percentage, the test count, and
the commit SHA. Report numbers you observed in output you read. If you could
not run a gate, say so plainly rather than omitting it.
