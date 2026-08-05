# Reproducibility

## 6.1 Verification gates

The package is verified before any mission is reported done:

1. `uv run pytest tests/ --cov=src --cov-fail-under=90` — ≥90% line-and-branch
   coverage on `src/`.
2. Zero mocks — every test exercises real computation.
3. `uv run ruff check` + `uv run ruff format` and `uv run mypy src/ scripts/`
   — clean.
4. No leftover template-scaffold lineage (lineage string count is zero
   outside documentation that explains the exemplar lineage).
5. `git status` clean after the path-scoped commit.

## 6.2 Deterministic regeneration

Running `scripts/run_mission.py full` reproduces the mission report; running
`scripts/run_mission.py render` regenerates both figures; and running
`scripts/z_generate_manuscript_variables.py` regenerates the token map and
resolved manuscript. None of these touch wall-clock state, so the tree is
reproducible byte-for-byte.

## 6.3 Artifacts

* Domain core: `src/dr_no/isotope_profiles.py`, `src/dr_no/spectrum_processing.py`,
  `src/dr_no/decay_chain.py`, `src/dr_no/shielding.py`,
  `src/dr_no/dose_assessment.py`, `src/dr_no/plume_model.py`,
  `src/dr_no/island_assessment.py`, and the shared metric source
  `src/dr_no/canonical.py`.
* Mission adapter: `src/dr_no/mission.py`.
* Figures: `output/figures/gamma_spectrum.png`,
  `output/figures/plume_field.png`, `output/figures/decay_curves.png`.
* Manuscript variables: `output/data/manuscript_variables.json`.

Environment: Python {{PYTHON_VERSION}}, numpy {{NUMPY_VERSION}}, generated
{{GENERATION_TIMESTAMP}} (UTC).
