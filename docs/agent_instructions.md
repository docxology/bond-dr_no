# Agent instructions — CRAB KEY (dr_no)

Read this first. These rules are mandatory before any edit to this package.

## Scope

Work only inside `projects/working/bond/dr_no/`. Never touch sibling packages,
the `bond/` root, or the template repo. Local-only: no remote, never push.
Path-scoped commits inside this repo only.

## Protocol

1. Before changing `src/` or `scripts/`, read `architecture.md`.
2. Before writing or editing pytest files, read `testing_philosophy.md`.
3. Before editing the manuscript, read `../manuscript/AGENTS.md` for the
   `{{TOKEN}}` protocol: numeric metrics come from
   `scripts/z_generate_manuscript_variables.py`, never hand-authored in prose.

## Guardrails

- No mock framework (MagicMock, mocker.patch, unittest.mock). Real data +
  computation only.
- Deterministic: fixed seeds, no untracked randomness, no wall-clock in
  persisted artifacts.
- `scripts/` are thin orchestrators; business logic lives in `src/`.
- No template-scaffold lineage strings in this tree (zero legacy).
- Type hints + docstrings everywhere; ruff + mypy clean on `src/` and `scripts/`.

## Verification gate

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
git status --short
```
