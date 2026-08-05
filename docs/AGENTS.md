# docs/ — agent-facing documentation for CRAB KEY (dr_no)

## Read order

1. [`agent_instructions.md`](agent_instructions.md) — scope, guardrails, and the
   verification gate. Mandatory before any edit.
2. [`architecture.md`](architecture.md) — before touching `src/` or `scripts/`.
3. [`testing_philosophy.md`](testing_philosophy.md) — before touching `tests/`.
4. [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — before touching the
   manuscript.

## The four rules that bite most often

- **Never hardcode a scenario number in Python.** It goes in the `mission:`
  block of `../manuscript/config.yaml`; `src/dr_no/scenario.py` loads it.
- **Never hand-author a metric in manuscript prose.** Add it to
  `canonical_metrics()`, expose it as a token, reference the token. Three tests
  enforce this.
- **Never change the public shape of `src/dr_no/mission.py`.** It is the frozen
  BOND-API surface other packages consume.
- **Never let a failure path return a plausible number.** Raise. A zero
  calibration gain and a 1 m contamination extent were both real defects that
  rendered as if they were measurements.

## Live numbers

Test count and measured coverage live in
[`_generated/COUNTS.md`](_generated/COUNTS.md), regenerated from a real run.
Never hardcode them in prose, and never edit that file to match an expectation
instead of an observation.
