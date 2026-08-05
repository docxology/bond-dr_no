# Pandoc syntax reference — CRAB KEY manuscript

This file documents citation and cross-reference syntax for the manuscript. It
is a *reference*, not a rendered section: it legitimately illustrates `{{TOKEN}}`
placeholders, so the token cross-reference gate scans only numbered `NN_*.md`
sections.

## Cross-references

Figures are referenced with Pandoc-crossref labels:

* `{#fig:spectrum}` → `[@fig:spectrum]` (parenthetical) or `@fig:spectrum` (narrative).
* `{#fig:plume}` → `[@fig:plume]`.

## Tokens

Manuscript metrics use `{{TOKEN}}` placeholders resolved by
`scripts/z_generate_manuscript_variables.py` from
`src/dr_no/manuscript_variables.py` (source of truth). Core tokens:
`DRNO_TITLE`, `DRNO_SUBTITLE`, `DRNO_VERSION`, `DRNO_FILM`, `DRNO_CODENAME`,
`NUM_ISOTOPES`, `NUM_GAMMA_LINES`, `NUM_DECAY_CHAINS`, `DECAY_CHAIN_NAMES_CSV`,
`I131_HALF_LIFE_DAYS`, `I131_FRACTION_7D_PCT`, `CALIBRATION_R2`,
`CALIBRATION_GAIN`, `MDA_CS137_BQ`, `HVL_LEAD_662_CM`, `TVL_CONCRETE_1332_CM`,
`TRANSMISSION_LEAD_5CM_662_PCT`, `EXTERNAL_DOSE_100M_MSV_H`,
`GAMMA_CONSTANT_CO60`, `NUM_STABILITY_CLASSES`, `STABILITY_CLASSES_CSV`,
`NUMPY_VERSION`, `PYTHON_VERSION`, `GENERATION_TIMESTAMP`.

## Mathematics

`$...$` inline and `$$...$$` display math are used throughout the numbered
sections.
