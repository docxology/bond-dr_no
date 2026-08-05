# Dr. No: CRAB KEY — Special-Agent Mission Software

**Abstract.** Crab Key, a small island held by a shadow syndicate, shelters a
radiological threat that must be located, characterised, and contained. This
package, codename CRAB KEY, is the special-agent mission software that executes
that assessment. It couples several deterministic, computation-first models: a
gamma-spectrum isotope-identification engine built on a real emission-line
library ({{NUM_ISOTOPES}} isotopes, {{NUM_GAMMA_LINES}} principal lines); a
spectrum-quantification layer (energy calibration, net peak areas, Currie
detection limits); {{NUM_DECAY_CHAINS}} real Bateman parent–daughter decay
chains; an exponential shielding/attenuation model over real mass-attenuation
data; an external-and-inhalation dose-accounting core; a Gaussian-plume
atmospheric-dispersion model over the {{NUM_STABILITY_CLASSES}} Pasquill–Gifford
stability classes ({{STABILITY_CLASSES_CSV}}); and a Crab Key-style island
threat assessor that scores each detected facility from its isotope inventory,
containment status, and local meteorology, then recommends a containment
action. The mission is exposed through the BOND-API mission protocol (codename
{{DRNO_CODENAME}}, film {{DRNO_FILM}}, version {{DRNO_VERSION}}) and is fully
deterministic: fixed scenario, fixed seed, no randomness, no wall-clock
dependence in any persisted artifact.

All figures in this report are generated from the same code that produces the
underlying measurements, so the manuscript cannot drift from the software.
