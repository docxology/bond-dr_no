# Experimental Setup

## 5.1 Scenario configuration

All results derive from the deterministic CRAB KEY scenario declared in
`manuscript/config.yaml` (`mission:` block) and consumed by the provider core:

* **Detector**: 60 s live acquisition, full-energy peak efficiency 0.01,
  resolution anchor 2.0 keV FWHM at 1332.5 keV, energy grid 20–3000 keV.
* **Isotope library**: {{NUM_ISOTOPES}} isotopes / {{NUM_GAMMA_LINES}} lines.
* **Source mixture**: Cs-137 ($2.0\times10^6$ Bq) plus Co-60 ($8.0\times10^5$ Bq).
* **Plume**: release $4.0\times10^5$ Bq/s, wind 3 m/s, stability class D,
  release height 10 m; contamination action threshold 1000 Bq/m³.
* **Facilities**: two — a breached dock compound and a contained load-out cave.

## 5.2 Software environment

* Python {{PYTHON_VERSION}}; numpy {{NUMPY_VERSION}}.
* Pasquill–Gifford stability classes: {{STABILITY_CLASSES_CSV}}.
* Threat bands: LOW, MODERATE, HIGH, SEVERE, CRITICAL.
* Seed: 42 (fixed; randomness disabled by construction).

## 5.3 Determinism and reproducibility

No random draws are made anywhere in the computation path, so the mission
report is byte-identical across runs and machines. Wall-clock time is never
persisted into artifacts; the provenance block carries a fixed `wall_time_s` of
zero and a stable input hash. Version {{DRNO_VERSION}} of film {{DRNO_FILM}},
codename {{DRNO_CODENAME}}.
