# manuscript/ — CRAB KEY mission report

Numbered sections (`00_abstract.md` … `99_references.md`) are the rendered
report; `config.yaml`, `references.bib`, `preamble.md`, `SYNTAX.md`,
`README.md`, and this file are sidecars.

## Token protocol

Every numeric metric in a numbered section is a double-brace placeholder
resolved by `scripts/z_generate_manuscript_variables.py` from
`src/dr_no/manuscript_variables.py`. **Never hand-author a number in prose.**

To add a quantitative claim:

1. compute it in `canonical_metrics()` (`src/dr_no/canonical.py`);
2. expose it as a token in `generate_variables()`;
3. reference the token in the section;
4. regenerate.

Three gates in `tests/test_manuscript_variables.py` enforce this:

- a token used in a section but not generated → fail;
- a token generated but used by no section → fail (catches renames that leave
  a stale entry behind while the forward gate stays green);
- a bare numeral in the prose of `03_results.md` → fail.

`SYNTAX.md` is a reference and legitimately contains literal placeholder
examples; the gates scan only numbered `NN_*.md` sections.

## config.yaml is the scenario of record

The `mission:` block is not documentation — it is the input the software
actually runs on, loaded and strictly validated by `src/dr_no/scenario.py`.
Change a value there and the metrics, figures, and tokens all move together;
`tests/test_canonical.py` pins that binding by editing the YAML and asserting
the numbers change.

Write floats in full (`2000000.0`) or with a signed exponent (`2.0e+6`).
PyYAML's YAML 1.1 resolver parses bare `2.0e6` as a **string**, and the loader
rejects it rather than coercing it silently.

## references.bib

Real, verifiable sources only. If you are not confident an entry is real,
**remove it** rather than ship it — two entries were removed on exactly those
grounds, and the header comment in `references.bib` records which and why.
Every `[@key]` in the prose must resolve to an entry there.
