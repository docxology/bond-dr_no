# Results

Every number in this section arrives as a placeholder resolved from
`src/dr_no/manuscript_variables.py` against the scenario declared in
`manuscript/config.yaml`. Nothing here is typed by hand;
`tests/test_manuscript_variables.py` fails the build on any bare numeral in
this section's prose.

## 3.1 Isotope identification

The deterministic CRAB KEY scenario synthesizes the gamma spectrum that the
declared source mixture — {{SOURCE_MIXTURE_CSV}} — would produce on the
package's HPGe detector model over a {{DETECTOR_ACQUISITION_S}} s live
acquisition, then runs the identification pipeline end to end.
[@fig:spectrum] shows the synthesized spectrum with every detected photopeak
marked and the top-scoring identification annotated.

![Synthesized gamma spectrum with detected peaks and top identification.](../output/figures/gamma_spectrum.png){#fig:spectrum}

The pipeline resolves {{DETECTED_PEAKS}} photopeaks on the
{{DETECTOR_BINS}}-bin grid spanning
{{DETECTOR_ENERGY_MIN_KEV}}–{{DETECTOR_ENERGY_MAX_KEV}} keV, and ranks
{{TOP_ISOTOPE}} first. Because the identification engine uses a real
emission-line library and the round-trip from synthesis to detection is exact,
both injected isotopes are recovered among the top identifications — a live,
reproducible demonstration that the model identifies what was placed in front
of it.

The figure is rendered from the *same* energy grid, source mixture, and
detector settings that produce the metrics above, so the picture and the
numbers cannot describe different spectra.

## 3.2 Plume dispersion

The same scenario runs the Gaussian-plume model for a release of
{{PLUME_SOURCE_Q_BQ_S}} Bq/s under Pasquill–Gifford class
{{PLUME_STABILITY_CLASS}}, a {{PLUME_WIND_SPEED_M_S}} m/s wind, and a
{{PLUME_RELEASE_HEIGHT_M}} m effective release height. [@fig:plume] shows the
ground-level concentration field: the plume is advected downwind and spreads
crosswind, decaying away from the source in the far field.

![Gaussian-plume ground-level concentration field (Bq/m^3).](../output/figures/plume_field.png){#fig:plume}

Because the release is elevated, the ground-level centreline profile is **not**
monotonic: it is effectively zero at the stack, where the plume is still aloft,
rises to a maximum once vertical spreading brings it to ground, and only then
decays. At the nearest facility's downwind distance the maximum ground-level
concentration on a crosswind transect is {{PEAK_CONCENTRATION_BQ_M3}} Bq/m³.
Measured against the declared action threshold of
{{ACTION_CONCENTRATION_BQ_M3}} Bq/m³, the centreline profile
{{ACTION_THRESHOLD_VERDICT}}, so the reported downwind extent is
{{DOWNWIND_EXTENT_M}} m. That clause is itself computed from the extent rather
than typed, so a scenario whose plume *does* breach the threshold reports the
exceedance and one whose plume does not reports the null result — neither is
presupposed by the prose.

That extent is computed in two stages — locate the ground-level maximum by
scan, then bisect only the monotone decaying tail beyond it — precisely because
the profile is unimodal. A single bisection seeded at the release point assumes
a monotonicity that an elevated release does not have, and returns a confidently
wrong distance rather than an error.

These plume figures moved materially at the phase-6 review. An earlier revision
of `sigma_y`/`sigma_z` converted the downwind distance into kilometres and then
multiplied the whole power law back up by the same factor. That does not cancel
for a power law, and it left every dispersion coefficient wrong by an amount
that differed per stability class and per axis — with the vertical coefficients
so badly scaled that the Pasquill–Gifford class ordering came out reversed.
Correcting it moves the peak concentration, the downwind extent, and the island
posture reported below. The values above are the corrected ones; the defect is
pinned by `tests/test_defect_regressions.py` and by the published-value gate
described in the methodology.

## 3.3 Island assessment

Each of the {{NUM_FACILITIES}} scenario facilities ({{FACILITY_NAMES_CSV}}) is
evaluated at its (downwind, crosswind) position: the plume concentration there
is converted to an inhaled dose rate, mapped to a threat band, and assigned a
containment action. The island posture is **{{ISLAND_THREAT}}**, with
per-facility actions {{CONTAINMENT_ACTIONS_CSV}}. The assessment is fully
deterministic; repeating the mission returns a byte-identical report.

## 3.4 Quantitative forensics

Beyond identification, CRAB KEY's canonical run quantifies the source. The
energy calibration over the declared calibration lines achieves
$R^2=$ {{CALIBRATION_R2}} at a gain of {{CALIBRATION_GAIN}} keV/channel; the net
{{QUANTIFIED_LINE}} photopeak area at {{QUANTIFIED_LINE_KEV}} keV is
{{NET_AREA_QUANTIFIED}} counts; and the Currie detection limit puts the
{{QUANTIFIED_LINE}} MDA at {{MDA_BQ}} Bq — an honest floor on what the detector
can claim.

Time dependence matters: for the {{DECAY_CHAIN_PROJECTED}} chain
($T_{1/2}=$ {{PARENT_HALF_LIFE_DAYS}} d) only
{{PARENT_FRACTION_REMAINING_PCT}}% of the parent activity survives
{{DECAY_ELAPSED_DAYS}} days, as [@fig:decay] shows.

![Parent and daughter activity over 72 h for the projected decay chain.](../output/figures/decay_curves.png){#fig:decay}

Shielding engineering closes the assessment: the half-value layer of
{{SHIELD_MATERIAL}} at {{SHIELD_ENERGY_KEV}} keV is {{HVL_CM}} cm, and
{{SHIELD_THICKNESS_CM}} cm of {{SHIELD_MATERIAL}} transmits only
{{TRANSMISSION_SHIELD_PCT}}% of that flux, cutting the unshielded
{{DOSE_PROBE_ISOTOPE}} dose rate of {{EXTERNAL_DOSE_PROBE_MSV_H}} mSv/h at
{{DOSE_PROBE_DISTANCE_M}} m ($\Gamma=$ {{GAMMA_CONSTANT_PROBE}}
mSv·m²·h⁻¹·GBq⁻¹) accordingly.
