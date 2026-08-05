"""Gamma-ray attenuation and shielding — exponential absorption over real data.

CRAB KEY's barrier-engineering core. Photon attenuation through a material
follows the exponential law

.. math::

    I(x) = I_0\\, e^{-\\mu x}, \\qquad \\mu = (\\mu/\\rho)\\,\\rho

with the linear attenuation coefficient :math:`\\mu` built from a real
mass-attenuation table :math:`\\mu/\\rho` (cm²/g) and material density
:math:`\\rho` (g/cm³). The table holds representative NIST-XCOM-style values
for lead, iron, concrete, and water across the 0.1–2.0 MeV range, interpolated
log-log in energy.

Derived quantities: transmission factors, half-value and tenth-value layers,
and the shield thickness required to bring an unshielded dose rate down to a
limit. All deterministic.
"""

from __future__ import annotations

import math

__all__ = [
    "MASS_ATTENUATION_CM2_G",
    "MATERIALS",
    "MATERIAL_DENSITY_G_CM3",
    "half_value_layer",
    "linear_attenuation_coefficient",
    "required_shield_thickness",
    "tenth_value_layer",
    "transmission_factor",
]

#: Representative mass attenuation coefficients mu/rho (cm²/g) by material and
#: photon energy (MeV) — NIST XCOM-style values.
MASS_ATTENUATION_CM2_G: dict[str, dict[float, float]] = {
    "lead": {0.1: 5.55, 0.5: 0.163, 0.662: 0.113, 1.0: 0.071, 1.25: 0.057, 2.0: 0.0457},
    "iron": {0.1: 0.372, 0.5: 0.0841, 0.662: 0.0775, 1.0: 0.0599, 1.25: 0.0528, 2.0: 0.0424},
    "concrete": {0.1: 0.1706, 0.5: 0.0872, 0.662: 0.0786, 1.0: 0.0635, 1.25: 0.0574, 2.0: 0.0453},
    "water": {0.1: 0.1706, 0.5: 0.0967, 0.662: 0.0859, 1.0: 0.0706, 1.25: 0.0628, 2.0: 0.0493},
}

#: Material densities (g/cm³).
MATERIAL_DENSITY_G_CM3: dict[str, float] = {
    "lead": 11.34,
    "iron": 7.87,
    "concrete": 2.35,
    "water": 1.0,
}

MATERIALS: tuple[str, ...] = ("lead", "iron", "concrete", "water")

#: Energy bounds of the attenuation table (MeV).
_MIN_ENERGY_MEV = 0.1
_MAX_ENERGY_MEV = 2.0


def _mass_attenuation(energy_mev: float, material: str) -> float:
    """Log-log interpolated mass attenuation coefficient (cm²/g)."""
    if not _MIN_ENERGY_MEV <= energy_mev <= _MAX_ENERGY_MEV:
        raise ValueError(
            f"energy {energy_mev} MeV is outside the table range [{_MIN_ENERGY_MEV}, {_MAX_ENERGY_MEV}]"
        )
    table = MASS_ATTENUATION_CM2_G.get(material)
    assert table is not None, f"material {material!r} must be present in the table"
    energies = sorted(table)
    if energy_mev in table:
        return float(table[energy_mev])
    # Log-log linear interpolation between the bracketing table points.
    e_lo = energies[0]
    e_hi = energies[-1]
    for i in range(len(energies) - 1):
        if energies[i] <= energy_mev <= energies[i + 1]:
            e_lo, e_hi = energies[i], energies[i + 1]
            break
    mu_lo = table[e_lo]
    mu_hi = table[e_hi]
    t = (math.log(energy_mev) - math.log(e_lo)) / (math.log(e_hi) - math.log(e_lo))
    return float(math.exp(math.log(mu_lo) + t * (math.log(mu_hi) - math.log(mu_lo))))


def linear_attenuation_coefficient(energy_mev: float, material: str) -> float:
    """Linear attenuation coefficient mu (cm⁻¹) = (mu/rho) * rho."""
    density = MATERIAL_DENSITY_G_CM3.get(material)
    if density is None:
        raise KeyError(f"unknown shielding material {material!r}; expected one of {MATERIALS}")
    return _mass_attenuation(energy_mev, material) * density


def transmission_factor(energy_mev: float, thickness_cm: float, material: str) -> float:
    """Fraction of photons surviving a barrier: ``exp(-mu * x)``."""
    if thickness_cm < 0:
        raise ValueError("thickness must be non-negative")
    mu = linear_attenuation_coefficient(energy_mev, material)
    return float(math.exp(-mu * thickness_cm))


def half_value_layer(energy_mev: float, material: str) -> float:
    """Half-value layer (cm): thickness halving the transmitted intensity."""
    mu = linear_attenuation_coefficient(energy_mev, material)
    return float(math.log(2.0) / mu)


def tenth_value_layer(energy_mev: float, material: str) -> float:
    """Tenth-value layer (cm): thickness reducing intensity to one tenth."""
    mu = linear_attenuation_coefficient(energy_mev, material)
    return float(math.log(10.0) / mu)


def required_shield_thickness(
    energy_mev: float,
    material: str,
    unshielded_dose_rate_m_sv_h: float,
    dose_limit_m_sv_h: float,
) -> float:
    """Barrier thickness (cm) reducing an unshielded dose rate to the limit.

    ``x = (1/mu) * ln(unshielded / limit)``; returns 0 when the unshielded
    rate already meets the limit.
    """
    if unshielded_dose_rate_m_sv_h < 0:
        raise ValueError("unshielded dose rate must be non-negative")
    if dose_limit_m_sv_h <= 0:
        raise ValueError("dose limit must be positive")
    if unshielded_dose_rate_m_sv_h <= dose_limit_m_sv_h:
        return 0.0
    mu = linear_attenuation_coefficient(energy_mev, material)
    return float(math.log(unshielded_dose_rate_m_sv_h / dose_limit_m_sv_h) / mu)
