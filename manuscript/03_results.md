# Results

## 3.1 Isotope identification

The deterministic CRAB KEY scenario synthesizes the gamma spectrum that a
shielded-source mixture of Cs-137 and Co-60 would produce on the package's HPGe
detector model, then runs the identification pipeline end to end. [@fig:spectrum]
shows the synthesized spectrum with every detected photopeak marked and the
top-scoring identification annotated.

![Synthesized gamma spectrum with detected peaks and top identification.](../output/figures/gamma_spectrum.png){#fig:spectrum}

Because the identification engine uses a real emission-line library and the
round-trip from synthesis to detection is exact, the two injected isotopes are
recovered as the top two identifications — a live, reproducible demonstration
that the model identifies what was placed in front of it.

## 3.2 Plume dispersion

The same scenario runs the Gaussian-plume model for a release of
$4.0\times10^5$ Bq/s under Pasquill–Gifford class D and a 3 m/s wind. [@fig:plume]
shows the ground-level concentration field: the plume is advected downwind and
spreads crosswind, with concentration falling monotonically away from the
source. The model is used to compute the downwind extent of contamination above
the action threshold and the maximum ground-level concentration on a crosswind
transect.

![Gaussian-plume ground-level concentration field (Bq/m^3).](../output/figures/plume_field.png){#fig:plume}

## 3.3 Island assessment

Each of the two scenario facilities is evaluated at its (downwind, crosswind)
position: the plume concentration there is converted to an inhaled dose rate,
mapped to a threat band, and assigned a containment action. The island report
records the worst threat level and the recommended containment posture for
every facility. The assessment is fully deterministic; repeating the mission
returns a byte-identical report.
