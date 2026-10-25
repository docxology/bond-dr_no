# References

Bibliography of record: `manuscript/references.bib`. Every entry below is a
real, checkable source for a model implemented in `src/dr_no/`. Two entries
present in an earlier revision were removed rather than shipped unverified —
see the header comment in `references.bib` for which and why.

## Gamma spectroscopy

**[knoll2010radiation]** G. F. Knoll, *Radiation Detection and Measurement*,
4th ed., John Wiley & Sons, 2010. — Detector resolution models, photopeak
analysis, and net-area background subtraction (`isotope_profiles.py`,
`spectrum_processing.py`).

**[currie1968limits]** L. A. Currie, "Limits for Qualitative Detection and
Quantitative Determination: Application to Radiochemistry," *Analytical
Chemistry* 40(3):586–593, 1968. doi:10.1021/ac60259a007 — The detection-limit
formalism in `minimum_detectable_activity()`.

**[ensdf]** National Nuclear Data Center, *ENSDF: Evaluated Nuclear Structure
Data File*, Brookhaven National Laboratory. — Gamma-ray energies, emission
intensities, and half-lives behind the isotope library and decay-chain table.

## Radioactive decay

**[bateman1910solution]** H. Bateman, "The Solution of a System of Differential
Equations Occurring in the Theory of Radioactive Transformations,"
*Proceedings of the Cambridge Philosophical Society* 15:423–427, 1910. — The
chain solution in `decay_chain.py`.

## Attenuation and shielding

**[hubbell1995tables]** J. H. Hubbell and S. M. Seltzer, *Tables of X-Ray Mass
Attenuation Coefficients and Mass Energy-Absorption Coefficients from 1 keV to
20 MeV*, NISTIR 5632, National Institute of Standards and Technology, 1995. —
Source of `MASS_ATTENUATION_CM2_G`.

**[nistxcom]** M. J. Berger, J. H. Hubbell, S. M. Seltzer, et al., *XCOM: Photon
Cross Sections Database*, NIST Standard Reference Database 8 (XGAM). — Photon
cross sections cross-checking the shielding tables.

## Dose assessment

**[icrp119compendium]** International Commission on Radiological Protection,
*Compendium of Dose Coefficients based on ICRP Publication 60*, ICRP
Publication 119, Annals of the ICRP 41 (Suppl.), 2012. — Committed effective
dose coefficients behind `INHALATION_DCF_SV_BQ`.

**[icrp72]** International Commission on Radiological Protection,
*Age-dependent Doses to Members of the Public from Intake of Radionuclides:
Part 5*, ICRP Publication 72, Annals of the ICRP 26(1), 1996.

**[smith2012exposure]** D. S. Smith and M. G. Stabin, "Exposure Rate Constants
and Lead Shielding Values for over 1,100 Radionuclides," *Health Physics*
102(3):271–291, 2012. — Specific gamma-ray constants behind
`GAMMA_CONSTANT_MSV_M2_H_GBQ`.

## Atmospheric dispersion

**[pasquill1961estimation]** F. Pasquill, "The Estimation of the Dispersion of
Windborne Material," *The Meteorological Magazine* 90(1063):33–49, 1961. —
Origin of the A–F stability classification.

**[gifford1961use]** F. A. Gifford, "Use of Routine Meteorological Observations
for Estimating Atmospheric Dispersion," *Nuclear Safety* 2(4):47–51, 1961. —
The dispersion curves paired with Pasquill's classes.

**[martin1976comment]** D. O. Martin, "Comment on 'The Change of Concentration
Standard Deviations with Distance'," *Journal of the Air Pollution Control
Association* 26(2):145–147, 1976. — The source of the power-law coefficients in
`plume_model.STABILITY_TABLE`, taken verbatim ($x$ in km, $\sigma$ in m); only
the near-field $x \le 1$ km $\sigma_z$ branch is implemented.

**[turner1994workbook]** D. B. Turner, *Workbook of Atmospheric Dispersion
Estimates: An Introduction to Dispersion Modeling*, 2nd ed., Lewis
Publishers/CRC Press, 1994. — Standard treatment of the Gaussian plume with
ground reflection.

## Suite context

The BOND suite documentation and the frozen `bond-api` mission protocol are
internal to the PROJECT BOND working tree and carry no external citation.
