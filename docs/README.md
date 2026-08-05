# Docs — CRAB KEY (dr_no)

Agent-facing documentation hub for the Dr. No mission package.

- `agent_instructions.md` — operational constraints and the read-first protocol.
- `architecture.md` — modular boundaries (pure domain + canonical vs. BOND-API
  adapter).
- `testing_philosophy.md` — zero-mock, real-data, deterministic testing.
- `_generated/COUNTS.md` — live test count and achieved coverage.

Domain modules in `../src/dr_no/`: `isotope_profiles.py` (isotope
identification), `spectrum_processing.py` (calibration / MDA),
`decay_chain.py` (Bateman chains), `shielding.py` (attenuation),
`dose_assessment.py` (dose), `plume_model.py` (dispersion),
`island_assessment.py` (threat), and `canonical.py` (shared metrics).

The manuscript itself lives in `../manuscript/`; figures and data are
regenerable under `../output/` (git-ignored).
