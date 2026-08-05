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

## 3.4 Quantitative forensics

Beyond identification, CRAB KEY's canonical run quantifies the source. The
energy calibration over the detected Cs-137 and Co-60 photopeaks achieves
$R^2=$ {{CALIBRATION_R2}} at a gain of {{CALIBRATION_GAIN}} keV/channel, and
the Currie detection limit puts the Cs-137 MDA at {{MDA_CS137_BQ}} Bq — an
honest floor on what the detector can claim. Time dependence matters: for the
I-131 component ($T_{1/2}=$ {{I131_HALF_LIFE_DAYS}} d) only
{{I131_FRACTION_7D_PCT}}% survives 7 days, as [@fig:decay] shows.

![I-131 → Xe-131m parent and daughter activity over 72 h.](../output/figures/decay_curves.png){#fig:decay}

Shielding engineering closes the assessment: the half-value layer of lead at
662 keV is {{HVL_LEAD_662_CM}} cm and 5 cm of lead transmits only
{{TRANSMISSION_LEAD_5CM_662_PCT}}% of the 662 keV flux, cutting the unshielded
Co-60 dose rate of {{EXTERNAL_DOSE_100M_MSV_H}} mSv/h at 100 m
($\Gamma_{Co60}=$ {{GAMMA_CONSTANT_CO60}} mSv·m²·h⁻¹·GBq⁻¹) accordingly.
