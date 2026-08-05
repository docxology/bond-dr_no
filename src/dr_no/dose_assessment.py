"""Dose assessment models — external point-source, inhalation, combined, integrated.

CRAB KEY's dose-accounting core. It consolidates the dose models used across
the island assessment:

* **External exposure** — a point-source photon dose rate via the specific
  gamma-ray constant :math:`\\Gamma` (mSv·m²·h⁻¹·GBq⁻¹) and the inverse-square
  law, optionally attenuated by a shielding transmission factor;
* **Inhalation** — the airborne-concentration dose rate from per-isotope
  inhalation dose coefficients (previously resident in
  :mod:`dr_no.island_assessment`, re-exported there for compatibility);
* **Combined and integrated dose** — additive external + inhalation rates and
  the time integral of a constant dose rate.

All pure arithmetic: deterministic, no randomness, no I/O.
"""

from __future__ import annotations

__all__ = [
    "BREATHING_RATE_M3_S",
    "GAMMA_CONSTANT_MSV_M2_H_GBQ",
    "INHALATION_DCF_SV_BQ",
    "combined_dose_rate",
    "dose_rate_from_concentration",
    "external_dose_rate",
    "integrated_dose",
    "shielded_external_dose_rate",
    "specific_gamma_constant",
]

#: Inhalation committed effective dose coefficients, Sv/Bq (representative
#: public values). Higher is more radiotoxic by inhalation.
INHALATION_DCF_SV_BQ: dict[str, float] = {
    "Cs-137": 4.6e-9,
    "I-131": 7.4e-9,
    "Co-60": 1.0e-8,
    "Na-22": 2.0e-9,
    "Am-241": 9.6e-6,
    "Ba-133": 7.4e-10,
    "K-40": 3.0e-9,
    "Tl-208": 8.2e-9,
    "U-235": 5.6e-6,
    "Eu-152": 2.0e-9,
}

#: Specific gamma-ray constants, mSv·m²·h⁻¹·GBq⁻¹ (representative handbook
#: values). A point source of activity A (GBq) at distance d (m) delivers a
#: dose rate of Gamma * A / d² (mSv/h) before shielding.
GAMMA_CONSTANT_MSV_M2_H_GBQ: dict[str, float] = {
    "Cs-137": 0.078,
    "Co-60": 0.354,
    "Na-22": 0.233,
    "I-131": 0.022,
    "Am-241": 0.0037,
    "Ba-133": 0.043,
    "K-40": 0.0011,
    "Tl-208": 0.70,
    "U-235": 0.0015,
    "Eu-152": 0.122,
}

#: Default adult breathing rate, m^3/s (~1.2 m^3/h at light activity).
BREATHING_RATE_M3_S = 1.2 / 3600.0


def specific_gamma_constant(isotope: str) -> float:
    """The specific gamma-ray constant of ``isotope`` (mSv·m²·h⁻¹·GBq⁻¹)."""
    try:
        return GAMMA_CONSTANT_MSV_M2_H_GBQ[isotope]
    except KeyError:
        raise KeyError(f"no specific gamma constant for isotope {isotope!r}") from None


def dose_rate_from_concentration(
    concentration_bq_m3: float,
    isotope_fractions: dict[str, float],
    *,
    breathing_rate_m3_s: float = BREATHING_RATE_M3_S,
) -> float:
    """Inhaled effective dose rate (Sv/s) from an airborne concentration.

    ``concentration_bq_m3`` is the total airborne activity concentration;
    ``isotope_fractions`` maps isotope name -> fraction of that total it
    represents. The dose rate is the sum over isotopes of
    ``conc * fraction * DCF * breathing_rate``.

    Args:
        concentration_bq_m3: total contaminant concentration (Bq/m^3).
        isotope_fractions: isotope -> fraction of the total (must sum to ~1).
        breathing_rate_m3_s: breathing rate (m^3/s) for the exposed person.

    Returns:
        Effective dose rate in Sv/s (non-negative).
    """
    if concentration_bq_m3 < 0:
        raise ValueError("concentration must be non-negative")
    if breathing_rate_m3_s <= 0:
        raise ValueError("breathing rate must be positive")
    total_frac = sum(isotope_fractions.values())
    if not isotope_fractions or total_frac <= 0:
        raise ValueError("isotope_fractions must be non-empty with positive total")
    rate = 0.0
    for isotope, fraction in isotope_fractions.items():
        dcf = INHALATION_DCF_SV_BQ[isotope]
        rate += concentration_bq_m3 * (fraction / total_frac) * dcf
    return rate * breathing_rate_m3_s


def external_dose_rate(
    activity_bq: float,
    gamma_constant: float,
    distance_m: float,
) -> float:
    """Unshielded point-source photon dose rate (mSv/h).

    ``D = Gamma * A / d²`` with activity in GBq, distance in m, and Gamma in
    mSv·m²·h⁻¹·GBq⁻¹.
    """
    if activity_bq < 0:
        raise ValueError("activity must be non-negative")
    if gamma_constant < 0:
        raise ValueError("gamma constant must be non-negative")
    if distance_m <= 0:
        raise ValueError("distance must be positive")
    activity_gbq = activity_bq / 1.0e9
    return float(gamma_constant * activity_gbq / (distance_m * distance_m))


def shielded_external_dose_rate(
    activity_bq: float,
    gamma_constant: float,
    distance_m: float,
    transmission_factor: float,
) -> float:
    """External dose rate (mSv/h) attenuated by a shielding transmission factor.

    ``transmission_factor`` is the fraction of photons that survive the
    barrier (see :mod:`dr_no.shielding`).
    """
    if not 0.0 <= transmission_factor <= 1.0:
        raise ValueError("transmission factor must be in [0, 1]")
    return external_dose_rate(activity_bq, gamma_constant, distance_m) * transmission_factor


def combined_dose_rate(external_sv_s: float, inhaled_sv_s: float) -> float:
    """Total effective dose rate (Sv/s) from external and inhalation pathways."""
    if external_sv_s < 0:
        raise ValueError("external dose rate must be non-negative")
    if inhaled_sv_s < 0:
        raise ValueError("inhaled dose rate must be non-negative")
    return external_sv_s + inhaled_sv_s


def integrated_dose(dose_rate_sv_s: float, duration_s: float) -> float:
    """Integrated effective dose (Sv) for a constant dose rate over ``duration_s``."""
    if dose_rate_sv_s < 0:
        raise ValueError("dose rate must be non-negative")
    if duration_s < 0:
        raise ValueError("duration must be non-negative")
    return dose_rate_sv_s * duration_s
