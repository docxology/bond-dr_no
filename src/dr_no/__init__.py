"""CRAB KEY — Dr. No (1962) film-package mission software for PROJECT BOND.

Radiation / isotope forensics: gamma-spectrum isotope identification
(:mod:`dr_no.isotope_profiles`), Gaussian plume dispersion
(:mod:`dr_no.plume_model`), and Crab Key-style island threat assessment
(:mod:`dr_no.island_assessment`). The BOND-API adapter lives in
:mod:`dr_no.mission`.
"""

from dr_no.island_assessment import (
    BREATHING_RATE_M3_S,
    INHALATION_DCF_SV_BQ,
    THREAT_LEVELS,
    DetectedFacility,
    IslandAssessment,
    Meteorology,
    assess_island,
    containment_recommendation,
    dose_rate_from_concentration,
    facility_threat_level,
)
from dr_no.isotope_profiles import (
    DetectedPeak,
    Identification,
    IsotopeProfile,
    detect_peaks,
    estimate_activity,
    identify_isotopes,
    isotope_library,
    library_names,
    synthesize_spectrum,
)
from dr_no.plume_model import (
    STABILITY_CLASSES,
    find_ground_level_max,
    isopleth_extent,
    sigma_y,
    sigma_z,
)

__version__ = "0.1.0"
FILM = "Dr. No"
CODENAME = "CRAB KEY"

__all__ = [
    "BREATHING_RATE_M3_S",
    "CODENAME",
    "FILM",
    "INHALATION_DCF_SV_BQ",
    "STABILITY_CLASSES",
    "THREAT_LEVELS",
    "DetectedFacility",
    "DetectedPeak",
    "Identification",
    "IslandAssessment",
    "IsotopeProfile",
    "Meteorology",
    "__version__",
    "assess_island",
    "containment_recommendation",
    "detect_peaks",
    "dose_rate_from_concentration",
    "estimate_activity",
    "facility_threat_level",
    "find_ground_level_max",
    "identify_isotopes",
    "isopleth_extent",
    "isotope_library",
    "library_names",
    "sigma_y",
    "sigma_z",
    "synthesize_spectrum",
]
