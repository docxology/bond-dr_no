# manuscript/ — CRAB KEY mission report

Numbered sections (`00_abstract.md` … `99_references.md`) are the rendered
report; `SYNTAX.md`, `AGENTS.md`, `README.md`, `config.yaml`, `references.bib`,
and `preamble.md` are sidecars.

Token protocol: every numeric metric in the numbered sections uses a
`{{TOKEN}}` resolved by `scripts/z_generate_manuscript_variables.py` from
`src/dr_no/manuscript_variables.py` — never hand-author a number in prose. The
live cross-reference gate is `tests/test_manuscript_variables.py`. SYNTAX.md is
a reference and legitimately contains literal `{{VARIABLE}}` examples; the gate
scans only numbered sections.
