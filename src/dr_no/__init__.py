"""CRAB KEY — Dr. No (1962) film-package mission software for PROJECT BOND.

Radiation / isotope forensics: gamma-spectrum isotope identification
(:mod:`dr_no.isotope_profiles`), spectrum quantification
(:mod:`dr_no.spectrum_processing`), radioactive decay chains
(:mod:`dr_no.decay_chain`), photon shielding (:mod:`dr_no.shielding`), dose
assessment (:mod:`dr_no.dose_assessment`), Gaussian plume dispersion
(:mod:`dr_no.plume_model`), and Crab Key-style island threat assessment
(:mod:`dr_no.island_assessment`). The BOND-API adapter and the shared metric
source live in :mod:`dr_no.mission` and :mod:`dr_no.canonical`.
"""

from dr_no.decay_chain import (
    DecayChain,
    Nuclide,
    activity_fraction_remaining,
    decay_chains,
    transient_equilibrium_ratio,
)
from dr_no.dose_assessment import (
    BREATHING_RATE_M3_S,
    GAMMA_CONSTANT_MSV_M2_H_GBQ,
    INHALATION_DCF_SV_BQ,
    combined_dose_rate,
    dose_rate_from_concentration,
    external_dose_rate,
    integrated_dose,
)
from dr_no.island_assessment import (
    THREAT_LEVELS,
    DetectedFacility,
    IslandAssessment,
    Meteorology,
    assess_island,
    containment_recommendation,
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
from dr_no.shielding import (
    MATERIALS,
    half_value_layer,
    required_shield_thickness,
    tenth_value_layer,
    transmission_factor,
)
from dr_no.spectrum_processing import (
    calibrate_energy,
    minimum_detectable_activity,
    net_peak_area,
)

__version__ = "0.3.0"
FILM = "Dr. No"
CODENAME = "CRAB KEY"

__all__ = [
    "BREATHING_RATE_M3_S",
    "CODENAME",
    "FILM",
    "GAMMA_CONSTANT_MSV_M2_H_GBQ",
    "INHALATION_DCF_SV_BQ",
    "MATERIALS",
    "STABILITY_CLASSES",
    "THREAT_LEVELS",
    "DecayChain",
    "DetectedFacility",
    "DetectedPeak",
    "Identification",
    "IslandAssessment",
    "IsotopeProfile",
    "Meteorology",
    "Nuclide",
    "__version__",
    "activity_fraction_remaining",
    "assess_island",
    "calibrate_energy",
    "combined_dose_rate",
    "containment_recommendation",
    "decay_chains",
    "detect_peaks",
    "dose_rate_from_concentration",
    "estimate_activity",
    "external_dose_rate",
    "facility_threat_level",
    "find_ground_level_max",
    "half_value_layer",
    "identify_isotopes",
    "integrated_dose",
    "isopleth_extent",
    "isotope_library",
    "library_names",
    "minimum_detectable_activity",
    "net_peak_area",
    "required_shield_thickness",
    "sigma_y",
    "sigma_z",
    "synthesize_spectrum",
    "tenth_value_layer",
    "transient_equilibrium_ratio",
    "transmission_factor",
]
