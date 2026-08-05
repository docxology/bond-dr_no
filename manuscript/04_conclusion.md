# Conclusion

The CRAB KEY package converts a compact radiological question — what is on
Crab Key, where is it going, and how dangerous is it — into a set of
deterministic models that an agent can run, trust, and reproduce. Isotope
identification rests on a real emission-line library rather than guesswork;
spectrum quantification bounds what is actually measurable, refusing to report
a calibration it could not fit; radioactive-decay chains correct activities for
mission elapsing time; and shielding-and-dose models turn a source inventory
into an engineerable containment answer. Plume dispersion uses the standard
Gaussian model across the {{NUM_STABILITY_CLASSES}} Pasquill–Gifford stability
classes, and island assessment turns the resulting concentrations into an
actionable threat band — {{ISLAND_THREAT}} on the declared scenario — and a
per-facility containment posture.

Two structural properties matter more than any single model. First, the
scenario is declared once, in `manuscript/config.yaml`, and read from there by
the metrics, the figures, and the manuscript tokens alike; the loader raises on
a missing or mistyped key rather than substituting a default, and a test edits
the YAML and asserts the numbers move. A configuration this report describes but
does not actually drive would be worse than no configuration at all. Second,
every reported number flows through one `canonical_metrics()` call, so the
mission provider's results and this report's prose are the same computation
observed twice.

The package is exposed through the frozen BOND-API mission protocol, so the
orchestrator can discover it by slug (`dr_no`) and drive all five mission
phases (brief, recon, plan, execute, debrief) without knowing its internals.
Guarantees: ≥90% line-and-branch coverage on `src/`, zero mocks, deterministic
execution, and no leftover template lineage. The result is mission software
whose every number can be traced to the code that produced it, and whose code
can be traced to the configuration that parameterised it.
