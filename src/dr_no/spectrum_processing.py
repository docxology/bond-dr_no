"""Gamma-spectrum processing — energy calibration, net peak areas, MDA (Currie).

CRAB KEY's quantification core, sitting between peak *detection*
(:mod:`dr_no.isotope_profiles`) and isotope *identification*. It implements
three standard spectroscopic procedures:

* **Energy calibration** — a least-squares linear fit of channel → energy from
  a set of calibration peaks, returning gain, offset, residuals, and R²;
* **Net peak area** — gross counts in a peak region minus a linearly
  interpolated background, with a Poisson-propagated uncertainty;
* **Minimum detectable activity** — the Currie detection-limit formalism
  (L_D = 2.71 + 4.65√B) converted into an MDA in Bq for a given detector
  efficiency, emission intensity, and acquisition time.

Pure deterministic arithmetic over real spectra; standard library + numpy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = [
    "EnergyCalibration",
    "PeakArea",
    "calibrate_energy",
    "minimum_detectable_activity",
    "net_peak_area",
]


@dataclass(frozen=True)
class EnergyCalibration:
    """Linear channel→energy calibration: ``E = gain * channel + offset``."""

    gain_kev_per_ch: float
    offset_kev: float
    residuals_kev: tuple[float, ...]
    r_squared: float


@dataclass(frozen=True)
class PeakArea:
    """Net photopeak area with background subtraction and uncertainty."""

    gross_counts: float
    background_counts: float
    net_counts: float
    net_uncertainty: float


def calibrate_energy(channels: np.ndarray, energies_kev: np.ndarray) -> EnergyCalibration:
    """Least-squares linear energy calibration from (channel, energy) pairs.

    Args:
        channels: calibration peak channel positions.
        energies_kev: known energies (keV) of those peaks.

    Returns:
        The fitted gain/offset, per-point residuals, and the coefficient of
        determination R².
    """
    if channels.ndim != 1 or energies_kev.ndim != 1:
        raise ValueError("channels and energies must be 1-D arrays")
    if channels.size != energies_kev.size:
        raise ValueError("channels and energies must have equal length")
    if channels.size < 2:
        raise ValueError("at least two calibration points are required")

    n = float(channels.size)
    sum_x = float(np.sum(channels))
    sum_y = float(np.sum(energies_kev))
    sum_xy = float(np.sum(channels * energies_kev))
    sum_xx = float(np.sum(channels * channels))
    denominator = n * sum_xx - sum_x * sum_x
    if denominator == 0.0:
        raise ValueError("calibration channels are degenerate (constant channel values)")

    gain = (n * sum_xy - sum_x * sum_y) / denominator
    offset = (sum_y - gain * sum_x) / n
    residuals = tuple(
        float(e - (gain * c + offset)) for c, e in zip(channels, energies_kev, strict=True)
    )

    mean_y = sum_y / n
    ss_res = float(np.sum((energies_kev - (gain * channels + offset)) ** 2))
    ss_tot = float(np.sum((energies_kev - mean_y) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return EnergyCalibration(
        gain_kev_per_ch=gain,
        offset_kev=offset,
        residuals_kev=residuals,
        r_squared=r_squared,
    )


def net_peak_area(
    energies: np.ndarray,
    counts: np.ndarray,
    peak_index: int,
    *,
    half_width: int = 3,
) -> PeakArea:
    """Net photopeak area with a linearly interpolated background.

    The region is ``[peak_index - half_width, peak_index + half_width]``. The
    background under the region is the average of the two boundary channels
    scaled by the region width (the standard trapezoid rule for a flat-plus-
    linear continuum). The net uncertainty follows Poisson propagation:
    ``sqrt(gross + background)``.

    Args:
        energies: energy bin centres (keV); used only for validation.
        counts: counts per bin.
        peak_index: index of the peak centroid channel.
        half_width: channels either side of the centroid to include.

    Returns:
        Gross, background, net counts, and the net-count uncertainty.
    """
    if energies.ndim != 1 or counts.ndim != 1 or energies.size != counts.size:
        raise ValueError("energies and counts must be matching 1-D arrays")
    if not isinstance(peak_index, (int, np.integer)):
        raise TypeError("peak_index must be an integer")
    peak_index = int(peak_index)
    if half_width < 1:
        raise ValueError("half_width must be >= 1")
    if not 0 <= peak_index < counts.size:
        raise ValueError(f"peak_index {peak_index} is outside the spectrum")

    lo = max(0, peak_index - half_width)
    hi = min(counts.size - 1, peak_index + half_width)
    region_width = hi - lo + 1
    if lo == hi:
        raise ValueError("peak region must span at least two channels")

    gross = float(np.sum(counts[lo : hi + 1]))
    left = float(counts[lo])
    right = float(counts[hi])
    background = float(0.5 * region_width * (left + right))
    net = gross - background
    uncertainty = math.sqrt(max(gross + background, 0.0))
    return PeakArea(
        gross_counts=gross,
        background_counts=background,
        net_counts=net,
        net_uncertainty=uncertainty,
    )


def minimum_detectable_activity(
    background_counts: float,
    *,
    acquisition_time_s: float,
    detector_efficiency: float,
    gamma_intensity: float,
) -> float:
    """Minimum detectable activity (Bq) via the Currie detection limit.

    The decision level uses Currie's form ``L_D = 2.71 + 4.65 * sqrt(B)``
    (1% false-negative rate at the 95% confidence decision level), and the MDA
    converts that count limit to activity: ``MDA = L_D / (t * efficiency * I)``.

    Args:
        background_counts: counts in the peak region from background alone, B.
        acquisition_time_s: live acquisition time (s).
        detector_efficiency: full-energy peak efficiency at the line energy.
        gamma_intensity: emission intensity (photons per decay) of the line.

    Returns:
        The minimum detectable activity in Bq.
    """
    if background_counts < 0:
        raise ValueError("background counts must be non-negative")
    if acquisition_time_s <= 0:
        raise ValueError("acquisition time must be positive")
    if detector_efficiency <= 0 or detector_efficiency > 1.0:
        raise ValueError("detector efficiency must be in (0, 1]")
    if gamma_intensity <= 0 or gamma_intensity > 1.0:
        raise ValueError("gamma intensity must be in (0, 1]")
    detection_limit = 2.71 + 4.65 * math.sqrt(background_counts)
    return float(detection_limit / (acquisition_time_s * detector_efficiency * gamma_intensity))
