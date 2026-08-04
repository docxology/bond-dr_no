# CRAB KEY (dr_no) — TODO & integration register

Status: **phase-2 build complete** — pure domain core, BOND-API mission adapter,
thin CLIs, manuscript, figures, and a zero-mock ≥90% coverage test suite.

## Built (phase 2)

- `src/dr_no/isotope_profiles.py` — gamma-spectrum isotope identification:
  real 10-isotope emission-line library, detector spectrum synthesis, peak
  detection, energy-window matching, activity estimation.
- `src/dr_no/plume_model.py` — Gaussian plume dispersion: Pasquill–Gifford
  classes A–F, downwind/crosswind concentration, ground-level max, isopleth
  extent.
- `src/dr_no/island_assessment.py` — Crab Key threat assessment: inhaled
  dose-rate from plume concentration, five-band threat scoring, containment
  action recommendation, island aggregation.
- `src/dr_no/mission.py` — FROZEN `bond_api.MissionProvider` adapter + gadget
  registration.
- `src/dr_no/manuscript_variables.py` — `{{TOKEN}}` hydration.
- `src/dr_no/figures/plots.py` — gamma-spectrum and plume-field figures.
- `scripts/run_mission.py`, `scripts/z_generate_manuscript_variables.py`.
- Zero-mock tests, one per concept module + mission + manuscript + CLI +
  figures + scripts smoke.

## Integration points / declared

- **bond-utilities provenance**: `record_provenance_outcome` from
  `bond_utilities.mission_io` is NOT yet consumed. Acceptance: once
  bond-utilities ships its phase-1 mission_io, `mission.py` debrief/outcome
  should delegate persistence through it (replacing the local `_input_hash`
  provenance). Currently the Provenance block is built directly from the frozen
  bond-api types, which is protocol-complete.
- **bond-cli / bond-dashboard**: no dashboard or suite CLI binding yet. When a
  suite CLI lands, wire `scripts/run_mission.py` as the film's registered
  subcommand.
- **bond-orchestrator / discovery**: verified via `bond_api.discovery` in tests
  (`test_discovery_loads_provider_by_slug`); the orchestrator can already auto-
  discover `dr_no` on `sys.path`.

## Never

- Never push; this tree is local-only.
- Do not re-add template-scaffold lineage strings.
- Do not introduce mocks or non-determinism.
