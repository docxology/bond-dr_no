# Scope and Related Work

## 7.1 Scope

CRAB KEY addresses the *assessment* half of a radiological incident: identify
the isotopes, quantify what is actually measurable, project activities forward,
engineer a barrier, model the airborne dispersion, and score the island. It is
deliberately scoped to deterministic, first-principles modelling over declared
inputs.

It does **not** perform Bayesian spectrum unfolding, full-spectrum least-squares
deconvolution of overlapping multiplets, isotopic age dating, detonation
physics, three-dimensional computational fluid dynamics, wet or dry deposition,
plume rise, or terrain-following flow — each of which is a substantial
discipline of its own and outside a single film package. Where the real world
calls for such machinery, the deterministic core here serves as a fast,
auditable first pass.

## 7.2 Related work

Gamma-ray isotope identification against a known library is a standard
spectroscopic procedure — peak search followed by energy-window matching
[@knoll2010radiation]. The detection-limit formalism is Currie's
[@currie1968limits], the decay-chain solution is Bateman's
[@bateman1910solution], and mass attenuation coefficients follow the NIST
tabulations [@hubbell1995tables; @nistxcom]. Atmospheric transport uses the
conventional short-range regulatory Gaussian plume with Pasquill–Gifford
dispersion parameters [@pasquill1961estimation; @gifford1961use], in the
power-law fitted form [@martin1976comment; @turner1994workbook]. Inhalation dose
coefficients follow the ICRP compendium [@icrp119compendium], and specific
gamma-ray constants follow the Smith and Stabin tabulation
[@smith2012exposure].

The island threat score is unusual only in its packaging: it fuses a transport
model with a dose-conversion step and a decision rule into one small,
deterministic, protocol-exposed mission. The contribution of this package is not
a new physical law but a *complete, reproducible, agent-runnable* chain from a
declared configuration through raw gamma measurements to a containment
recommendation.

## 7.3 Limitations

The dose coefficients, specific gamma-ray constants, mass-attenuation entries,
and dispersion coefficients are representative literature values held at a
coarse tabulation, interpolated log-log between table points. They are
order-of-magnitude faithful and fully auditable — every one is a named constant
in a named module, traceable to a cited source — but they are approximations,
not a licensed consequence-assessment dataset.

Three specific caveats bound the results. The detector model synthesizes
Gaussian photopeaks on a flat continuum with no Compton edge, no escape peaks,
no true-coincidence summing, and no pulse pile-up, so the identification problem
is easier than a real measurement. The Gaussian plume is a steady-state,
flat-terrain, constant-wind idealisation valid for short range and neutral-ish
conditions; it has no deposition term, so it does not conserve mass against the
ground. And the threat banding is a declared decision rule, not a regulatory
standard — the band edges are constants in `island_assessment.py`, chosen to be
legible rather than derived from any published intervention level.

The results are therefore directionally correct and fully traceable, and should
be read as a screening pass rather than as a substitute for a licensed
consequence assessment.
