# manuscript/ — the CRAB KEY mission report

Numbered markdown sections compose the report; the sidecars configure and
document it.

| File | Role |
| --- | --- |
| `00_abstract.md` … `07_scope_and_related_work.md`, `99_references.md` | the rendered report, in order |
| `config.yaml` | paper metadata **and** the `mission:` scenario of record |
| `references.bib` | the bibliography — verified sources only |
| `preamble.md` | pandoc title block |
| `SYNTAX.md` | citation, cross-reference, and token conventions |
| `AGENTS.md` | the token protocol and editing rules |

## config.yaml does two jobs

It carries the usual paper metadata (title, authors, keywords, version) **and**
the `mission:` block that declares the entire computational scenario — detector,
source mixture, meteorology, facilities, probes, thresholds.

That block is the source of truth for the software, not just for the report:
`src/dr_no/scenario.py` loads and validates it, and `canonical.py`,
`figures/plots.py`, and `manuscript_variables.py` all read it. Editing a value
there moves the computation, the figures, and this report together.

## Regenerating

```bash
uv run python scripts/z_generate_manuscript_variables.py
```

Writes `output/data/manuscript_variables.json` (the token map) and
`output/manuscript/` (sections with tokens resolved). Strict by default: any
unresolved token fails. Pass `--allow-draft` to skip strict resolution while
drafting.

Figures are regenerated separately with
`uv run python scripts/run_mission.py render`.

## The one rule

Never hand-author a number in a numbered section. See `AGENTS.md`.
