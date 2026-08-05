# Pandoc syntax reference — CRAB KEY manuscript

This file documents citation, cross-reference, and token syntax for the
manuscript. It is a *reference*, not a rendered section: it legitimately
illustrates placeholder syntax, so the token cross-reference gate scans only
numbered `NN_*.md` sections.

## Cross-references

Figures carry pandoc-crossref labels:

* `{#fig:spectrum}` → `[@fig:spectrum]` (parenthetical) or `@fig:spectrum` (narrative)
* `{#fig:plume}` → `[@fig:plume]`
* `{#fig:decay}` → `[@fig:decay]`

## Citations

Citation keys resolve against `references.bib`:
`[@knoll2010radiation]`, `[@currie1968limits; @bateman1910solution]`.

Every key must exist in `references.bib`, and every entry there must be a real,
verifiable source. If you cannot confirm a reference is real, remove it rather
than ship it.

## Tokens

Numeric metrics use double-brace placeholders resolved by
`scripts/z_generate_manuscript_variables.py` from
`src/dr_no/manuscript_variables.py`. **Never hand-author a number in a numbered
section.** 63 tokens are currently defined, in five groups.

### Identity

`DRNO_TITLE`, `DRNO_SUBTITLE`, `DRNO_VERSION`, `DRNO_FILM`, `DRNO_CODENAME`,
`MISSION_SEED`

### Library surface (what the code exposes)

`NUM_ISOTOPES`, `NUM_GAMMA_LINES`, `LIBRARY_MIN_LINE_KEV`,
`LIBRARY_MAX_LINE_KEV`, `NUM_DECAY_CHAINS`, `DECAY_CHAIN_NAMES_CSV`,
`NUM_STABILITY_CLASSES`, `STABILITY_CLASSES_CSV`, `NUM_SHIELDING_MATERIALS`,
`SHIELDING_MATERIALS_CSV`, `NUM_THREAT_BANDS`, `THREAT_BANDS_CSV`

### Declared scenario (from the `mission:` block of `config.yaml`)

`DETECTOR_ACQUISITION_S`, `DETECTOR_EFFICIENCY`, `DETECTOR_RESOLUTION_KEV`,
`DETECTOR_ENERGY_MIN_KEV`, `DETECTOR_ENERGY_MAX_KEV`, `DETECTOR_BINS`,
`SOURCE_MIXTURE_CSV`, `PLUME_SOURCE_Q_BQ_S`, `PLUME_WIND_SPEED_M_S`,
`PLUME_STABILITY_CLASS`, `PLUME_RELEASE_HEIGHT_M`, `ACTION_CONCENTRATION_BQ_M3`,
`NUM_FACILITIES`, `FACILITY_NAMES_CSV`, `SHIELD_MATERIAL`,
`SHIELD_THICKNESS_CM`, `SHIELD_ENERGY_KEV`, `TVL_MATERIAL`, `TVL_ENERGY_KEV`,
`DOSE_PROBE_ISOTOPE`, `DOSE_PROBE_DISTANCE_M`

### Computed metrics (from `canonical_metrics()`)

`DETECTED_PEAKS`, `TOP_ISOTOPE`, `QUANTIFIED_LINE`, `QUANTIFIED_LINE_KEV`,
`NET_AREA_QUANTIFIED`, `CALIBRATION_R2`, `CALIBRATION_GAIN`, `MDA_BQ`,
`DECAY_CHAIN_PROJECTED`, `DECAY_ELAPSED_DAYS`, `PARENT_HALF_LIFE_DAYS`,
`PARENT_FRACTION_REMAINING_PCT`, `HVL_CM`, `TVL_CM`, `TRANSMISSION_SHIELD_PCT`,
`EXTERNAL_DOSE_PROBE_MSV_H`, `GAMMA_CONSTANT_PROBE`,
`PEAK_CONCENTRATION_BQ_M3`, `ISLAND_THREAT`, `DOWNWIND_EXTENT_M`,
`CONTAINMENT_ACTIONS_CSV`

### Environment

`PYTHON_VERSION`, `NUMPY_VERSION`, `GENERATION_TIMESTAMP`

## Adding a metric

1. Compute it in `canonical_metrics()` (`src/dr_no/canonical.py`) — never in
   `mission.py` or `manuscript_variables.py`.
2. Add the token to `generate_variables()`.
3. Reference the token in a numbered section.
4. Regenerate: `uv run python scripts/z_generate_manuscript_variables.py`.

Three gates in `tests/test_manuscript_variables.py` will hold you to it: a token
used but not generated fails, a token generated but unused fails, and a bare
numeral in the results narrative fails.

Large and small magnitudes are formatted as inline LaTeX by the `_sci()` helper
(e.g. `$4.00\times10^{5}$`), so tokens can be dropped straight into prose.

## Mathematics

`$...$` inline and `$$...$$` display math are used throughout the numbered
sections.
