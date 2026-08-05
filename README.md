# Dr. No — CRAB KEY · PROJECT BOND film package

**Film:** Dr. No (1962) · **Mission codename:** CRAB KEY · **Discipline:**
radiation / isotope forensics

This is a PROJECT BOND suite package. It is a **local-only** working tree: no
remote, never push. Scope is exactly this directory.

## What it does

CRAB KEY is special-agent mission software that assesses a radiological threat
on an island like Crab Key. It chains deterministic, computation-first models:

1. **Gamma-spectrum isotope identification** — `src/dr_no/isotope_profiles.py`
   A real gamma-line library (10 isotopes, principal emission lines), a detector
   model that synthesizes a binned spectrum, peak detection, and ranked isotope
   identification.

2. **Spectrum quantification** — `src/dr_no/spectrum_processing.py`
   Least-squares energy calibration, background-subtracted net photopeak areas,
   and a Currie minimum-detectable-activity (MDA) formalism.

3. **Radioactive decay chains** — `src/dr_no/decay_chain.py`
   The Bateman solution over five real parent–daughter chains, with
   transient-equilibrium ratios and activity projection in time.

4. **Shielding & attenuation** — `src/dr_no/shielding.py`
   Exponential absorption over a real mass-attenuation table (lead, iron,
   concrete, water): transmission, half/tenth-value layers, required thickness.

5. **Dose assessment** — `src/dr_no/dose_assessment.py`
   External point-source dose (specific gamma-ray constant + inverse-square),
   inhalation from airborne concentration, and combined/integrated dose.

6. **Plume dispersion** — `src/dr_no/plume_model.py`
   The steady-state Gaussian plume with Pasquill–Gifford dispersion coefficients
   across all six stability classes (A–F), plus isopleth extent.

7. **Island threat assessment** — `src/dr_no/island_assessment.py`
   Converts plume concentration at each detected facility into a dose rate,
   maps it (with containment status) onto a threat band, aggregates the island,
   and recommends a containment action.

`src/dr_no/canonical.py` is the single-source-of-truth metric computation
consumed by **both** the mission provider's results and the manuscript tokens,
so the two can never disagree. The mission is exposed through the frozen
**BOND-API** protocol via `src/dr_no/mission.py` (`MissionProvider`, slug
`dr_no`), with gadgets registered on the `GadgetRegistry`.

## Quick start

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90

# Run the full mission and render figures
uv run python scripts/run_mission.py full
uv run python scripts/run_mission.py render

# Hydrate manuscript tokens
uv run python scripts/z_generate_manuscript_variables.py
```

## Layout

| Path | Role |
| --- | --- |
| `src/dr_no/isotope_profiles.py` | gamma-spectrum isotope identification core |
| `src/dr_no/spectrum_processing.py` | energy calibration, net area, MDA (Currie) |
| `src/dr_no/decay_chain.py` | Bateman radioactive decay chains |
| `src/dr_no/shielding.py` | gamma attenuation, HVL/TVL, required thickness |
| `src/dr_no/dose_assessment.py` | external/inhalation/combined/integrated dose |
| `src/dr_no/plume_model.py` | Gaussian plume dispersion core |
| `src/dr_no/island_assessment.py` | threat scoring / containment core |
| `src/dr_no/canonical.py` | single-source-of-truth canonical metrics |
| `src/dr_no/mission.py` | BOND-API `MissionProvider` adapter + gadget registry |
| `src/dr_no/manuscript_variables.py` | `{{TOKEN}}` hydration for the manuscript |
| `src/dr_no/figures/plots.py` | deterministic figure generators |
| `scripts/` | thin CLIs (`run_mission.py`, `z_generate_manuscript_variables.py`) |
| `tests/` | real-data, zero-mock test suite (≥90% coverage) |
| `manuscript/` | mission report + config |

## Guarantees

- ≥90% line-and-branch coverage on `src/` (see `docs/_generated/COUNTS.md`).
- Zero mocks — every test computes with real data.
- Deterministic: fixed scenario, fixed seed, no RNG, no wall-clock in artifacts.
- No leftover template-scaffold lineage in code or docs.
- Thin orchestrators in `scripts/`; business logic in `src/`.
