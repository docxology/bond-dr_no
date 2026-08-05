# Testing philosophy — CRAB KEY (dr_no)

Zero-mock, real-data, deterministic testing.

## Principles

- **No mocks.** No MagicMock, mocker.patch, or unittest.mock. Every test calls
  the real computation path with real arguments. Where a branch needs a
  controlled input (e.g. an empty library to exercise a guard), we pass that
  value directly or use `pytest.MonkeyPatch` on a module attribute — never a
  fake object with stubbed behaviour.
- **Deterministic.** Fixed seeds and fixed scenarios; no untracked RNG, no
  wall-clock assertions except interval-bracketed fallbacks.
- **Known-vector checks.** Identity round-trips (synthesize → detect →
  identify recovers the injected isotope) and exact inverse relations
  (`estimate_activity` inverts the synthesis model).
- **Error branches.** Every public validation guard has a matching
  `pytest.raises` test so the error paths are covered, not just the happy path.

## Coverage gate

`uv run pytest tests/ --cov=src --cov-fail-under=90` — line **and** branch
(`branch = true`) coverage on `src/`, exceeding 90% (live number in
`docs/_generated/COUNTS.md`).

## Test layout

| File | Covers |
| --- | --- |
| `test_isotope_profiles.py` | isotope library, synthesis, peak detection, identification |
| `test_spectrum_processing.py` | energy calibration, net area, Currie MDA |
| `test_decay_chain.py` | Bateman decay chains, equilibrium, time projection |
| `test_shielding.py` | attenuation, transmission, HVL/TVL, required thickness |
| `test_dose_assessment.py` | external/inhalation/combined/integrated dose |
| `test_plume_model.py` | dispersion coefficients, concentration, isopleth |
| `test_island_assessment.py` | dose rate, threat bands, containment, aggregation |
| `test_canonical.py` | single-source-of-truth canonical metrics |
| `test_mission.py` | BOND-API provider: protocol, flow, registers, discovery |
| `test_manuscript_variables.py` | token hydration + live `{{TOKEN}}` cross-reference gate |
| `test_cli.py` | in-process CLI phase driver coverage |
| `test_figures.py` | figure generators write real PNGs |
| `test_scripts_smoke.py` | thin scripts exit cleanly and write artifacts |
