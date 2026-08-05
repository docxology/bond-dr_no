# Experimental Setup

## 5.1 Scenario configuration

All results derive from the deterministic CRAB KEY scenario declared in the
`mission:` block of `manuscript/config.yaml`. That block is the sole source of
truth: `src/dr_no/scenario.py` loads and validates it, and
`src/dr_no/canonical.py` (metrics), `src/dr_no/figures/plots.py` (figures), and
`src/dr_no/manuscript_variables.py` (the tokens below) all read it. No scenario
constant is re-declared in Python, and the loader raises rather than defaulting
on a missing or mistyped key, so config and computation cannot drift apart
silently. `tests/test_canonical.py` pins the binding by editing the YAML and
asserting the metrics move.

* **Detector**: {{DETECTOR_ACQUISITION_S}} s live acquisition, full-energy peak
  efficiency {{DETECTOR_EFFICIENCY}}, resolution anchor
  {{DETECTOR_RESOLUTION_KEV}} keV FWHM at 1332.5 keV, energy grid
  {{DETECTOR_ENERGY_MIN_KEV}}–{{DETECTOR_ENERGY_MAX_KEV}} keV in
  {{DETECTOR_BINS}} bins.
* **Isotope library**: {{NUM_ISOTOPES}} isotopes / {{NUM_GAMMA_LINES}} lines,
  spanning {{LIBRARY_MIN_LINE_KEV}}–{{LIBRARY_MAX_LINE_KEV}} keV.
* **Source mixture**: {{SOURCE_MIXTURE_CSV}}.
* **Quantification**: energy calibration against the declared calibration
  lines; Currie MDA at the {{QUANTIFIED_LINE}} line ({{QUANTIFIED_LINE_KEV}} keV).
* **Decay chains**: {{NUM_DECAY_CHAINS}} Bateman chains
  ({{DECAY_CHAIN_NAMES_CSV}}); {{DECAY_CHAIN_PROJECTED}} projected
  {{DECAY_ELAPSED_DAYS}} days after release.
* **Shielding**: {{NUM_SHIELDING_MATERIALS}} mass-attenuation tables
  ({{SHIELDING_MATERIALS_CSV}}) over 0.1–2.0 MeV, interpolated log-log; the
  report's barrier is {{SHIELD_THICKNESS_CM}} cm of {{SHIELD_MATERIAL}} at
  {{SHIELD_ENERGY_KEV}} keV.
* **External dose probe**: {{DOSE_PROBE_ISOTOPE}} at
  {{DOSE_PROBE_DISTANCE_M}} m.
* **Plume**: release {{PLUME_SOURCE_Q_BQ_S}} Bq/s, wind
  {{PLUME_WIND_SPEED_M_S}} m/s, stability class {{PLUME_STABILITY_CLASS}},
  release height {{PLUME_RELEASE_HEIGHT_M}} m; contamination action threshold
  {{ACTION_CONCENTRATION_BQ_M3}} Bq/m³.
* **Facilities**: {{NUM_FACILITIES}} — {{FACILITY_NAMES_CSV}} (a breached dock
  compound and a contained load-out cave).

## 5.2 Software environment

* Python {{PYTHON_VERSION}}; numpy {{NUMPY_VERSION}}.
* Pasquill–Gifford stability classes ({{NUM_STABILITY_CLASSES}}):
  {{STABILITY_CLASSES_CSV}}.
* Threat bands ({{NUM_THREAT_BANDS}}): {{THREAT_BANDS_CSV}}.
* Declared mission seed: {{MISSION_SEED}}.

## 5.3 Determinism and reproducibility

No random draws are made anywhere in the computation path, so the mission
report is byte-identical across runs and machines. The declared seed
({{MISSION_SEED}}) is recorded in the provenance block for audit rather than
consumed by any generator — there is nothing stochastic for it to seed, and
saying so is more useful than implying a randomness that does not exist.

Wall-clock time is never persisted into artifacts: the provenance block carries
a fixed `wall_time_s` of zero and a stable input hash taken over the whole
declared scenario, so a scenario edit changes the hash and an unrelated rerun
does not. Version {{DRNO_VERSION}} of film {{DRNO_FILM}}, codename
{{DRNO_CODENAME}}.
