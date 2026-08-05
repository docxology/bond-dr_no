# Methodology

## 2.1 Gamma-spectrum isotope identification

A gamma-emitting isotope emits photons at discrete energies. For isotope $i$
with activity $A_i$ (Bq), acquisition time $t$, detector peak efficiency
$\varepsilon$, and emission intensity $I_{k}$ for line $k$ at energy $E_k$, the
integrated photopeak count is

$$ N_{i,k} = A_i \, t \, \varepsilon \, I_{k} .$$

The detector broadens each line into a Gaussian photopeak whose standard
deviation derives from an energy-proportional resolution model anchored at the
Co-60 calibration line,

$$ \mathrm{FWHM}(E) = \mathrm{FWHM}(1332.5) \sqrt{E/1332.5}, \qquad
   \sigma(E) = \mathrm{FWHM}(E)/2.3548 .$$

A flat background continuum is added. Peak detection finds local maxima whose
signal-to-noise ratio exceeds a floor; isotope identification matches each
detected peak energy against the library within a window of $2.5\sigma$ and
scores each candidate by the summed intensity of its matched lines scaled by
the square root of the matched-line fraction.

The library holds {{NUM_ISOTOPES}} real isotopes spanning {{NUM_GAMMA_LINES}}
principal lines, from {{LIBRARY_MIN_LINE_KEV}} keV (Am-241) to
{{LIBRARY_MAX_LINE_KEV}} keV (Tl-208): fission products (Cs-137, I-131),
activation products (Co-60, Na-22), naturally occurring material (K-40, U-235),
and calibration standards (Ba-133, Eu-152).

## 2.2 Gaussian plume dispersion

For a continuous release at rate $Q$ (Bq/s) into a wind of speed $u$ (m/s),
the steady-state airborne concentration at downwind distance $x$, crosswind
offset $y$, and height $z$ is

$$ C(x,y,z) = \frac{Q}{2\pi\, u\, \sigma_y\, \sigma_z}\,
   \exp\!\left(-\frac{y^2}{2\sigma_y^2}\right)\,
   \left[\exp\!\left(-\frac{(z-H)^2}{2\sigma_z^2}\right)
   + \exp\!\left(-\frac{(z+H)^2}{2\sigma_z^2}\right)\right],$$

where $H$ is the effective release height and the second vertical term models
ground reflection. The dispersion coefficients grow with downwind distance
according to the Pasquill–Gifford stability class (A–F):

$$ \sigma_y = a_y x^{b_y}, \qquad \sigma_z = c_z x^{d_z} + f_z,$$

with $x$ in kilometres and $\sigma$ in metres, using the coefficient set
published by D. O. Martin [@martin1976comment] for the classes
{{STABILITY_CLASSES_CSV}}. Two accuracy caveats belong here rather than in a
footnote. First, only Martin's near-field ($x \le 1$ km) $\sigma_z$ branch is
implemented, so vertical spread beyond 1 km is an extrapolation of that fit and
not the published far-field curve. Second, Martin's $f_z$ offsets are negative
for classes D, E and F, which drives $\sigma_z$ non-positive within roughly
17 m of the source; both coefficients are therefore floored at a small positive
value, and concentrations inside that near-source region are not modelled
quantitatively. `tests/test_plume_model.py` pins both coefficients against
published Pasquill–Gifford values at 100, 500 and 1000 m for every class, and
against the physical class ordering $\sigma(A) > \cdots > \sigma(F)$.

The downwind extent over which contamination exceeds an action threshold is
**not** found by a plain bisection: the ground-level centreline profile of an
elevated release is unimodal, not monotone, so a bisection seeded at the
release point assumes a monotonicity that does not exist. `isopleth_extent`
instead scans log-spaced samples to locate the ground-level maximum, returns
zero extent if even that maximum is below the threshold, and only then bisects
the monotone decaying tail beyond the peak.

## 2.3 Island threat assessment

At each detected facility the plume model yields a concentration, which is
converted to an inhaled effective dose rate (Sv/s) by weighting its isotope mix
against per-isotope inhalation dose coefficients and a breathing rate,

$$ \dot{D} = C \sum_{k} f_k\, \mathrm{DCF}_k \, \dot{V}.$$

The dose rate is mapped onto a {{NUM_THREAT_BANDS}}-band threat scale
({{THREAT_BANDS_CSV}}); a facility whose containment is breached is escalated
one band. The island report records the worst threat and, for each facility, a
containment action (none / shelter / evacuation). Shelter is triggered at the
declared action concentration of {{ACTION_CONCENTRATION_BQ_M3}} Bq/m³.

## 2.4 Radioactive decay chains

A radiological source is not static: a parent nuclide decays into a daughter
with its own half-life, so activities change on mission timescales. CRAB KEY
models this with the Bateman solution over {{NUM_DECAY_CHAINS}} real
parent–daughter chains ({{DECAY_CHAIN_NAMES_CSV}}):

$$ N_k(t) = N_0 \sum_{j=1}^{k}
   \frac{\prod_{i=1}^{k-1}\lambda_i}{\prod_{i\neq j}^{k}(\lambda_i - \lambda_j)}
   e^{-\lambda_j t}, \qquad A = \lambda N ,$$

where $\lambda = \ln 2 / T_{1/2}$. The parent activity falls
exponentially, and a faster-decaying daughter may approach transient
equilibrium. For the declared {{DECAY_CHAIN_PROJECTED}} release,
$T_{1/2} = $ {{PARENT_HALF_LIFE_DAYS}} d, so after {{DECAY_ELAPSED_DAYS}} days
the parent activity is {{PARENT_FRACTION_REMAINING_PCT}}% of its initial value
— a decision-relevant correction for any follow-up mission.

## 2.5 Spectrum calibration and detection limits

Beyond identifying peaks, the package quantifies them. A least-squares linear
calibration maps detector channel to energy over the declared calibration lines,
returning the calibration gain ({{CALIBRATION_GAIN}} keV/channel here) and the
coefficient of determination $R^2$ ({{CALIBRATION_R2}} for the canonical fit).
A fit with fewer than two matched lines raises rather than reporting a zero
gain. Net photopeak areas are
computed with a linearly interpolated background and a Poisson-propagated
uncertainty. The minimum detectable activity follows Currie's formalism,

$$ L_D = 2.71 + 4.65\sqrt{B}, \qquad \mathrm{MDA} = \frac{L_D}{t\,\varepsilon\,I},$$

which bounds what a measurement can actually claim to have seen — for the
canonical detector the MDA at the {{QUANTIFIED_LINE}} line
({{QUANTIFIED_LINE_KEV}} keV) is {{MDA_BQ}} Bq.

## 2.6 Shielding, attenuation, and external dose

Exponential absorption governs every barrier: $I(x) = I_0 e^{-\mu x}$ with
$\mu = (\mu/\rho)\,\rho$ from a real mass-attenuation table
({{SHIELDING_MATERIALS_CSV}}), interpolated log-log in energy. The half-value
layer of {{SHIELD_MATERIAL}} at {{SHIELD_ENERGY_KEV}} keV is {{HVL_CM}} cm, and
the tenth-value layer of {{TVL_MATERIAL}} at {{TVL_ENERGY_KEV}} keV is
{{TVL_CM}} cm. A {{TRANSMISSION_SHIELD_PCT}}% transmission fraction survives
{{SHIELD_THICKNESS_CM}} cm of {{SHIELD_MATERIAL}} at {{SHIELD_ENERGY_KEV}} keV.
External dose follows the point-source inverse-square law with the specific
gamma-ray constant ($\Gamma = $ {{GAMMA_CONSTANT_PROBE}} mSv·m²·h⁻¹·GBq⁻¹ for
{{DOSE_PROBE_ISOTOPE}}), giving an unshielded dose rate of
{{EXTERNAL_DOSE_PROBE_MSV_H}} mSv/h at {{DOSE_PROBE_DISTANCE_M}} m.
