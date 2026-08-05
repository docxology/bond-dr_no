# CRAB KEY live counts

<!--
Regenerated from an actual verification run; do not hand-edit the numbers here.
Regenerate with:
  uv run pytest tests/ --cov=src --cov-fail-under=90
  uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
  uv run mypy src/ scripts/
Measured 2026-08-05 on Python 3.14.6 (darwin, arm64), package version 0.3.0.
-->

## Test suite

- **Tests collected:** 281
- **Tests passed:** 281
- **Tests failed / skipped:** 0 / 0
- **Coverage (`src/`, line + branch):** 99.01%
- **Gate:** `uv run pytest tests/ --cov=src --cov-fail-under=90` (≥90% required)

## Per-module coverage

| Module | Cover |
| --- | --- |
| `canonical.py` | 100.00% |
| `cli.py` | 100.00% |
| `decay_chain.py` | 98.82% |
| `dose_assessment.py` | 100.00% |
| `figures/plots.py` | 98.88% |
| `island_assessment.py` | 100.00% |
| `isotope_profiles.py` | 93.88% |
| `manuscript_variables.py` | 100.00% |
| `mission.py` | 100.00% |
| `plume_model.py` | 100.00% |
| `scenario.py` | 100.00% |
| `shielding.py` | 100.00% |
| `spectrum_processing.py` | 100.00% |
| `util_render.py` | 100.00% |
| **TOTAL** | **99.01%** |

16 Python modules under `src/dr_no/` (14 measured; `__init__.py` files are
omitted from coverage by `pyproject.toml`).

## Lint, types, and policy scans

- `uv run ruff check src/ scripts/ tests/` — clean (all checks passed).
- `uv run ruff format --check src/ scripts/ tests/` — clean (41 files formatted).
- `uv run mypy src/ scripts/` — clean (no issues in 18 source files).
- Lineage scan for the exemplar string — **zero** hits outside documentation.
- Mock-framework scan (`MagicMock`, `mocker.patch`, `unittest.mock`) — **zero**
  hits in `src/` or `tests/`.
- `infrastructure` imports in `src/` — zero.
- `bond_api` seam — `mission.py` and `cli.py` only; the twelve other modules
  import without it.
