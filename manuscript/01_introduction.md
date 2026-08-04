# Introduction

## 1.1 The threat on Crab Key

Crab Key presents a compact, well-bounded radiological-assessment problem: a
small island, a limited number of facilities, a single prevailing wind, and a
concealed source of gamma-emitting material. The detection and attribution of
that material is the classic task of radiation forensics — measure the emitted
gamma spectrum, identify the isotopes present from their characteristic
emission lines, and use atmospheric transport to locate the plume and the
concentrations it deposits on the island.

## 1.2 Three models, one mission

The package is organised around three pure domain cores:

1. **Isotope identification** (`isotope_profiles`) — a deterministic
   gamma-spectroscopy engine. It starts from a library of real isotopes and
   their principal gamma lines, synthesizes a binned spectrum from a detector
   model (Gaussian photopeaks whose width grows with the square root of
   energy), detects the peaks, and matches them back against the library to
   produce a ranked identification.

2. **Plume dispersion** (`plume_model`) — the steady-state Gaussian plume with
   Pasquill–Gifford dispersion coefficients. Given a release rate, wind speed,
   and stability class, it returns airborne concentration as a function of
   downwind and crosswind position.

3. **Island assessment** (`island_assessment`) — the decision layer. It
   converts plume concentrations at each detected facility into an inhaled
   dose rate, maps that rate (together with containment status) onto a threat
   band, aggregates the island, and recommends containment actions.

All three are pure arithmetic over real physics: no simulation randomness, no
external calls, no wall-clock dependence.

## 1.3 Reader's guide

Section 2 derives the mathematics of each model. Section 3 reports results
from the deterministic CRAB KEY scenario. Section 5 documents the experimental
configuration and software environment (Python {{PYTHON_VERSION}}, numpy
{{NUMPY_VERSION}}). Tables and figures are generated from live code.
