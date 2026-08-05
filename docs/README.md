# Docs — CRAB KEY (dr_no)

Agent-facing documentation for the Dr. No mission package: radiation and
isotope forensics, plume dispersion, and Crab Key island threat assessment.

## What is in here

| File | What it holds |
| --- | --- |
| [`agent_instructions.md`](agent_instructions.md) | Operational instructions: scope, read order, where code goes, the frozen-protocol rule, manuscript rules, and the full verification gate. **Read first.** |
| [`architecture.md`](architecture.md) | Module-by-module architecture of `src/`, the layer diagram, how the pieces compose, and how `mission.py` implements the frozen `bond_api` `MissionProvider`. |
| [`testing_philosophy.md`](testing_philosophy.md) | The no-mock / real-data / determinism doctrine as it applies here, plus what makes a test able to fail. |
| [`AGENTS.md`](AGENTS.md) | One-screen pointer for an agent landing in `docs/`. |
| [`_generated/COUNTS.md`](_generated/COUNTS.md) | Live test count and measured coverage. Regenerated from a real run — never hand-edited. |

## The package in one paragraph

CRAB KEY assesses a radiological threat on an island. It chains seven pure
domain models — gamma-spectrum isotope identification
(`isotope_profiles.py`), spectrum quantification and detection limits
(`spectrum_processing.py`), Bateman decay chains (`decay_chain.py`), photon
attenuation (`shielding.py`), dose accounting (`dose_assessment.py`), Gaussian
plume dispersion (`plume_model.py`), and threat/containment scoring
(`island_assessment.py`) — over a scenario declared in
`../manuscript/config.yaml` and loaded by `scenario.py`. `canonical.py` runs
that chain once and hands the same metrics to both the BOND-API mission
provider (`mission.py`) and the manuscript tokens
(`manuscript_variables.py`), so the software and the report cannot disagree.

## Two invariants worth knowing before you touch anything

**The config is the source of truth.** Every scenario number lives in the
`mission:` block of `../manuscript/config.yaml`. The loader raises rather than
defaulting on a missing or mistyped key, and `tests/test_canonical.py` edits the
YAML and asserts the metrics move. Do not reintroduce a Python-side constant.

**`mission.py`'s public surface is frozen.** `bond-cli`, the coordinator, and
the orchestrator consume `MissionProvider` (`brief`/`recon`/`plan`/`execute`/
`debrief`) and the `GADGETS` registry across packages. Deepen inside the
package, never by changing that shape.

## Elsewhere in the tree

- `../manuscript/` — the mission report (numbered sections, `config.yaml`,
  `references.bib`, `SYNTAX.md`).
- `../src/dr_no/` — the implementation.
- `../tests/` — the zero-mock suite.
- `../output/` — regenerable figures, resolved manuscript, and the token map.
  Disposable; never hand-edit to make a gate pass.
