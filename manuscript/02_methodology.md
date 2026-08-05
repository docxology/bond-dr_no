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
principal lines, from the 59.5 keV line of Am-241 to the 2.6 MeV line of
Tl-208, plus fission products (Cs-137, I-131), activation products (Co-60,
Na-22), and naturally occurring material (K-40, U-235).

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

with the Martin/Greene coefficient set ({{STABILITY_CLASSES_CSV}}). The
downwind extent over which contamination exceeds an action threshold is found
by binary search along the centreline.

## 2.3 Island threat assessment

At each detected facility the plume model yields a concentration, which is
converted to an inhaled effective dose rate (Sv/s) by weighting its isotope mix
against per-isotope inhalation dose coefficients and a breathing rate,

$$ \dot{D} = C \sum_{k} f_k\, \mathrm{DCF}_k \, \dot{V}.$$

The dose rate is mapped onto a five-band threat scale (LOW, MODERATE, HIGH,
SEVERE, CRITICAL); a facility whose containment is breached is escalated one
band. The island report records the worst threat and, for each facility, a
containment action (none / shelter / evacuation).

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
equilibrium. For the canonical iodine-131 release,
$T_{1/2} = $ {{I131_HALF_LIFE_DAYS}} d, so after 7 days the I-131 activity is
{{I131_FRACTION_7D_PCT}}% of its initial value — a decision-relevant
correction for any follow-up mission.

## 2.5 Spectrum calibration and detection limits

Beyond identifying peaks, the package quantifies them. A least-squares linear
calibration maps detector channel to energy, returning the calibration gain
({{CALIBRATION_GAIN}} keV/channel here) and the coefficient of determination
$R^2$ ({{CALIBRATION_R2}} for the canonical fit). Net photopeak areas are
computed with a linearly interpolated background and a Poisson-propagated
uncertainty. The minimum detectable activity follows Currie's formalism,

$$ L_D = 2.71 + 4.65\sqrt{B}, \qquad \mathrm{MDA} = \frac{L_D}{t\,\varepsilon\,I},$$

which bounds what a measurement can actually claim to have seen — for the
canonical detector the MDA at the Cs-137 line is {{MDA_CS137_BQ}} Bq.

## 2.6 Shielding, attenuation, and external dose

Exponential absorption governs every barrier: $I(x) = I_0 e^{-\mu x}$ with
$\mu = (\mu/\rho)\,\rho$ from a real mass-attenuation table (lead, iron,
concrete, water). The half-value layer of lead at the 662 keV Cs-137 line is
{{HVL_LEAD_662_CM}} cm, and the tenth-value layer of concrete at the 1332 keV
Co-60 line is {{TVL_CONCRETE_1332_CM}} cm. A {{TRANSMISSION_LEAD_5CM_662_PCT}}%
transmission fraction survives 5 cm of lead at 662 keV. External dose follows
the point-source inverse-square law with the specific gamma-ray constant
($\Gamma_{Co60} = $ {{GAMMA_CONSTANT_CO60}} mSv·m²·h⁻¹·GBq⁻¹), giving an
unshielded Co-60 dose rate of {{EXTERNAL_DOSE_100M_MSV_H}} mSv/h at 100 m.
