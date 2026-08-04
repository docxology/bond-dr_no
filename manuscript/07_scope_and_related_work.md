# Scope and Related Work

## 7.1 Scope

CRAB KEY addresses the *assessment* half of a radiological incident: identify
the isotopes, model the airborne dispersion, and score the island. It is
deliberately scoped to deterministic, first-principles modelling. It does *not*
perform Bayesian spectrum unfolding, isotopic age dating, full detonation
physics, or three-dimensional computational fluid dynamics — each of which is a
substantial discipline of its own and outside a single film package. Where the
real world calls for such machinery, the deterministic core here serves as a
fast, auditable first pass.

## 7.2 Related work

Gamma-ray isotope identification with a known library is a standard
spectroscopic procedure (peak search followed by energy-window matching), and
the Gaussian plume model with Pasquill–Gifford dispersion parameters is the
conventional regulatory Gaussian model for short-range atmospheric dispersion.
The island threat score is unusual only in its packaging: it fuses a
transport model with a dose-conversion step and a decision rule into one small,
deterministic, protocol-exposed mission. The contribution of this package is
not a new physical law but a *complete, reproducible, agent-runnable* chain
from raw gamma measurements to a containment recommendation.

## 7.3 Limitations

Representative dose coefficients and dispersion coefficients are constants
with real, cited-order-of-magnitude values; they are approximations and are
kept out of the manuscript's token prose by construction. The results are
therefore directionally correct and fully auditable rather than a substitute
for a licensed consequence assessment.
