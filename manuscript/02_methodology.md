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
