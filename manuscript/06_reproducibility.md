# Reproducibility

## 6.1 Verification gates

The package is verified before any mission is reported done. Gate definitions,
not gate results, are recorded here — the live measured numbers belong in
`docs/_generated/COUNTS.md`, which is regenerated from an actual run.

1. `uv run pytest tests/ --cov=src --cov-fail-under=90` — line **and** branch
   coverage on `src/`, floor 90%.
2. Zero mocks — every test exercises real computation on real data. No
   `MagicMock`, no `mocker.patch`, no `unittest.mock`.
3. `uv run ruff check src/ scripts/ tests/` and `uv run ruff format --check`
   — clean.
4. `uv run mypy src/ scripts/` — clean.
5. No leftover template-scaffold lineage strings outside documentation that
   explains the exemplar lineage.
6. Version identity: `pyproject.toml`, `dr_no.__version__`, and
   `manuscript/config.yaml` must declare the same version
   ({{DRNO_VERSION}}); `tests/test_version_identity.py` enforces it.
7. Token cross-reference: every placeholder appearing in a numbered manuscript
   section must be produced by `generate_variables()`, every generated token
   must be consumed by some section, and the results narrative may carry no
   bare metric numeral. `tests/test_manuscript_variables.py` enforces all
   three directions.
8. `git status` clean after the path-scoped commit.

## 6.2 Deterministic regeneration

```bash
uv run python scripts/run_mission.py full     # mission report
uv run python scripts/run_mission.py render   # all three figures
uv run python scripts/z_generate_manuscript_variables.py   # tokens + resolved sections
```

None of these consult wall-clock state or draw a random number, so repeated runs
are byte-identical. The one deliberate exception is
`{{GENERATION_TIMESTAMP}}`, which records when the token map was hydrated; it is
written to `output/`, never into a computed metric or the provenance hash.

## 6.3 Artifacts

* Scenario of record: `manuscript/config.yaml` (`mission:` block), loaded and
  validated by `src/dr_no/scenario.py`.
* Domain core: `src/dr_no/isotope_profiles.py`,
  `src/dr_no/spectrum_processing.py`, `src/dr_no/decay_chain.py`,
  `src/dr_no/shielding.py`, `src/dr_no/dose_assessment.py`,
  `src/dr_no/plume_model.py`, `src/dr_no/island_assessment.py`, and the shared
  metric source `src/dr_no/canonical.py`.
* Mission adapter: `src/dr_no/mission.py` (the only module importing
  `bond_api`, alongside the CLI driver `src/dr_no/cli.py`).
* Figures: `output/figures/gamma_spectrum.png`,
  `output/figures/plume_field.png`, `output/figures/decay_curves.png` — all
  rendered from the same declared scenario as the metrics.
* Manuscript variables: `output/data/manuscript_variables.json`; resolved
  sections: `output/manuscript/`.

Environment: Python {{PYTHON_VERSION}}, numpy {{NUMPY_VERSION}}, generated
{{GENERATION_TIMESTAMP}} (UTC).
