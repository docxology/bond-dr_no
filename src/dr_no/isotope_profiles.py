"""Gamma-spectrum isotope identification — the radiation-forensics core of CRAB KEY.

This module implements a deterministic gamma-ray spectroscopy engine:

* a library of real gamma-emitting isotopes with their principal emission lines
  (energy in keV, intensity as a fraction of decays) and half-lives;
* a detector model that synthesizes a binned gamma spectrum from a set of
  isotope activities: Gaussian photopeaks (resolution broadens with
  :math:`\\sqrt{E}`), plus a smooth background continuum;
* peak detection on the synthesized spectrum; and
* isotope identification by matching the detected peak energies against the
  library within an energy-dependent window, returning a ranked score.

It is pure domain logic — no bond-api, no infrastructure imports — so it is
importable standalone and serves as the fallback core if the BOND protocol path
ever fails.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field

import numpy as np

__all__ = [
    "DetectedPeak",
    "Identification",
    "IsotopeProfile",
    "detect_peaks",
    "estimate_activity",
    "identify_isotopes",
    "isotope_library",
    "library_names",
    "match_energy",
    "synthesize_spectrum",
    "total_gamma_lines",
]

# Real gamma emission lines: (energy_keV, intensity_fraction). Intensities are
# representative literature values (photons per decay). Only the principal lines
# per isotope are recorded — enough for unambiguous identification.
_GAMMA_LINES: dict[str, tuple[tuple[float, float], ...]] = {
    "Cs-137": ((661.66, 0.8510),),
    "Co-60": ((1173.24, 0.9985), (1332.50, 0.9998)),
    "I-131": ((80.19, 0.0262), (284.31, 0.0614), (364.49, 0.8160), (636.99, 0.0717)),
    "Na-22": ((511.00, 0.9060), (1274.54, 0.9994)),
    "Am-241": ((59.54, 0.3590),),
    "Ba-133": ((81.00, 0.3410), (302.85, 0.1830), (356.01, 0.6205)),
    "K-40": ((1460.82, 0.1067),),
    "Tl-208": ((583.19, 0.8450), (2614.53, 0.9980)),
    "U-235": ((143.76, 0.1096), (163.36, 0.0508), (185.72, 0.5720)),
    "Eu-152": ((121.78, 0.2837), (344.28, 0.2659), (778.90, 0.1297), (1408.01, 0.2085)),
}

# Representative half-lives in years (literature values).
_HALF_LIFE_Y: dict[str, float] = {
    "Cs-137": 30.08,
    "Co-60": 5.271,
    "I-131": 0.0221,  # 8.02 d
    "Na-22": 2.602,
    "Am-241": 432.2,
    "Ba-133": 10.51,
    "K-40": 1.248e9,
    "Tl-208": 1.9e-9,  # 3.053 min decay chain progeny
    "U-235": 7.038e8,
    "Eu-152": 13.54,
}


@dataclass(frozen=True)
class IsotopeProfile:
    """A gamma-emitting isotope: name, half-life, and its emission lines."""

    name: str
    half_life_y: float
    gamma_lines: tuple[tuple[float, float], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("isotope name must be a non-empty string")
        if self.half_life_y <= 0:
            raise ValueError(f"half-life must be positive, got {self.half_life_y}")
        for energy, intensity in self.gamma_lines:
            if energy <= 0:
                raise ValueError(f"gamma energy must be positive, got {energy}")
            if not 0 < intensity <= 1.0:
                raise ValueError(f"gamma intensity must be in (0, 1], got {intensity}")

    @property
    def discrete_energies(self) -> tuple[float, ...]:
        """The peak energies of this isotope's emission lines."""
        return tuple(energy for energy, _ in self.gamma_lines)

    def strongest_line(self) -> tuple[float, float]:
        """Return the (energy, intensity) of the most intense emission line."""
        if not self.gamma_lines:
            raise ValueError(f"isotope {self.name!r} has no gamma lines")
        return max(self.gamma_lines, key=lambda line: line[1])


def isotope_library() -> dict[str, IsotopeProfile]:
    """Return the immutable isotope library keyed by isotope name."""
    return {
        name: IsotopeProfile(name=name, half_life_y=_HALF_LIFE_Y[name], gamma_lines=lines)
        for name, lines in _GAMMA_LINES.items()
    }


def library_names() -> tuple[str, ...]:
    """Sorted names of every isotope in the library."""
    return tuple(sorted(isotope_library()))


def total_gamma_lines() -> int:
    """Total number of emission lines across the whole library."""
    return sum(len(lines) for lines in _GAMMA_LINES.values())


@dataclass(frozen=True)
class DetectedPeak:
    """A peak located on a measured spectrum."""

    energy_keV: float
    net_counts: float
    snr: float


@dataclass(frozen=True)
class Identification:
    """A scored isotope identification produced by matching detected peaks."""

    isotope: str
    score: float
    matched_peaks: tuple[float, ...]
    unmatched_peaks: tuple[float, ...]


def _fwhm_at(energy_keV: float, resolution_at_1332: float) -> float:
    """Detector FWHM (keV) at a given energy.

    Uses the empirical HPGe energy-proportional model
    ``FWHM(E) = FWHM(1332) * sqrt(E / 1332.5)``, so resolution broadens with
    :math:`\\sqrt{E}` and is anchored at the Co-60 calibration line.
    """
    if resolution_at_1332 <= 0:
        raise ValueError("detector resolution (FWHM at 1332 keV) must be positive")
    return resolution_at_1332 * math.sqrt(energy_keV / 1332.5)


def _gaussian(energy: float, centre: float, sigma: float) -> float:
    return (1.0 / (sigma * math.sqrt(2.0 * math.pi))) * math.exp(
        -((energy - centre) ** 2) / (2.0 * sigma * sigma)
    )


def synthesize_spectrum(
    activities: dict[str, float],
    *,
    energies: Iterable[float],
    acquisition_time_s: float = 60.0,
    detector_efficiency: float = 0.01,
    resolution_at_1332: float = 2.0,
    background_level: float = 50.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Synthesize a binned gamma spectrum from isotope activities.

    Each emission line contributes a Gaussian photopeak whose integrated count
    is ``N = Activity * t * efficiency * intensity``, placed on the energy grid;
    a constant background continuum is added. Deterministic: no RNG.

    Args:
        activities: isotope name -> activity (Bq).
        energies: the energy bin centres (keV), an ordered Iterable.
        acquisition_time_s: live acquisition time (s).
        detector_efficiency: full-energy peak efficiency at answer energy.
        resolution_at_1332: detector FWHM (keV) at 1332.5 keV.
        background_level: constant background counts per bin.

    Returns:
        ``(energies, counts)`` as 1-D ``ndarray``s.
    """
    energy_arr = np.asarray(energies, dtype=float)
    if energy_arr.ndim != 1 or energy_arr.size == 0:
        raise ValueError("energies must be a non-empty 1-D array")
    if acquisition_time_s <= 0:
        raise ValueError("acquisition time must be positive")
    if detector_efficiency <= 0 or detector_efficiency > 1.0:
        raise ValueError("detector efficiency must be in (0, 1]")
    if background_level < 0:
        raise ValueError("background level must be non-negative")

    library = isotope_library()
    counts = np.full_like(energy_arr, background_level, dtype=float)
    for name, activity in activities.items():
        if activity < 0:
            raise ValueError(f"activity for {name!r} must be non-negative")
        if activity == 0.0:
            continue
        profile = library.get(name)
        if profile is None:
            raise KeyError(f"unknown isotope {name!r}; not in library")
        for line_energy, intensity in profile.gamma_lines:
            peak_area = activity * acquisition_time_s * detector_efficiency * intensity
            sigma = _fwhm_at(line_energy, resolution_at_1332) / 2.3548  # FWHM -> sigma
            counts = counts + peak_area * np.array(
                [_gaussian(e, line_energy, sigma) for e in energy_arr]
            )
    return energy_arr, counts


def detect_peaks(
    energies: np.ndarray,
    counts: np.ndarray,
    *,
    min_snr: float = 3.0,
    min_separation_keV: float = 5.0,
    background_level: float = 50.0,
) -> list[DetectedPeak]:
    """Locate photopeaks on a binned spectrum.

    A channel is a candidate peak when it is a local maximum (strictly higher
    than its neighbours) and its signal-to-noise ratio (net count divided by a
    robust background floor) exceeds ``min_snr``. Peaks closer than
    ``min_separation_keV`` are collapsed to the higher-count candidate to avoid
    double-counting one physical peak.

    Args:
        energies: energy bin centres (keV).
        counts: counts per bin.
        min_snr: minimum SNR for a channel to count as a peak.
        min_separation_keV: minimum energy gap between resolved peaks.
        background_level: background counts per bin used for the SNR floor.

    Returns:
        Detected peaks sorted by descending net count.
    """
    if energies.ndim != 1 or counts.ndim != 1 or energies.size != counts.size:
        raise ValueError("energies and counts must be matching 1-D arrays")
    if counts.size == 0:
        return []

    candidates: list[DetectedPeak] = []
    for i in range(1, counts.size - 1):
        if counts[i] > counts[i - 1] and counts[i] > counts[i + 1]:
            net = counts[i] - background_level
            snr = net / background_level if background_level > 0 else float(net)
            if snr >= min_snr:
                candidates.append(
                    DetectedPeak(
                        energy_keV=float(energies[i]), net_counts=float(net), snr=float(snr)
                    )
                )

    # Collapse near-duplicate peaks; keep the strongest in each cluster.
    candidates.sort(key=lambda p: p.energy_keV)
    merged: list[DetectedPeak] = []
    for peak in candidates:
        if merged and peak.energy_keV - merged[-1].energy_keV < min_separation_keV:
            if peak.net_counts > merged[-1].net_counts:
                merged[-1] = peak
        else:
            merged.append(peak)

    merged.sort(key=lambda p: p.net_counts, reverse=True)
    return merged


def match_energy(detected_keV: float, line_keV: float, resolution_at_1332: float = 2.0) -> bool:
    """True when a detected energy matches a library line within the detector window.

    The matching window is ``2.5 * sigma`` where sigma comes from the same
    energy-proportional resolution model used for peak synthesis — so a broad
    high-energy peak tolerates a wider window than a sharp low-energy peak.
    """
    sigma = _fwhm_at(line_keV, resolution_at_1332) / 2.3548
    return abs(detected_keV - line_keV) <= 2.5 * sigma


def identify_isotopes(
    peaks: Iterable[DetectedPeak],
    *,
    library: dict[str, IsotopeProfile] | None = None,
    resolution_at_1332: float = 2.0,
) -> list[Identification]:
    """Match detected peaks against the library and rank candidate isotopes.

    For each isotope, every detected peak that falls within the matching window
    of one of the isotope's lines counts as a *matched* peak. The score rewards
    the number of matched lines and their intensities, scaled by the fraction of
    the isotope's strongest lines that were observed:

    ``score = sum(matched_intensities) * sqrt(matched / total_lines)``

    Args:
        peaks: detected peaks (usually from :func:`detect_peaks`).
        library: isotope library (defaults to the canonical one).
        resolution_at_1332: detector resolution for the matching window.

    Returns:
        Candidate identifications sorted by descending score.
    """
    lib = library if library is not None else isotope_library()
    peak_list = list(peaks)
    results: list[Identification] = []
    for name, profile in lib.items():
        matched: list[float] = []
        unmatched: list[float] = []
        for peak in peak_list:
            line = next(
                (
                    line
                    for line in profile.gamma_lines
                    if match_energy(peak.energy_keV, line[0], resolution_at_1332)
                ),
                None,
            )
            if line is not None:
                matched.append(peak.energy_keV)
            else:
                unmatched.append(peak.energy_keV)
        if not matched:
            continue
        matched_intensity = sum(
            line[1]
            for line in profile.gamma_lines
            if any(match_energy(peak.energy_keV, line[0], resolution_at_1332) for peak in peak_list)
        )
        frac = math.sqrt(len(matched) / max(len(profile.gamma_lines), 1))
        score = matched_intensity * frac
        results.append(
            Identification(
                isotope=name,
                score=float(score),
                matched_peaks=tuple(matched),
                unmatched_peaks=tuple(unmatched),
            )
        )
    results.sort(key=lambda ident: ident.score, reverse=True)
    return results


def estimate_activity(
    net_counts: float,
    *,
    gamma_intensity: float,
    acquisition_time_s: float,
    detector_efficiency: float,
) -> float:
    """Back out an isotope's activity (Bq) from its measured photopeak area.

    ``A = N / (t * efficiency * intensity)`` — the inverse of the synthesis
    model, so a synthesized peak recovers the input activity exactly.
    """
    if net_counts < 0:
        raise ValueError("net counts must be non-negative")
    if gamma_intensity <= 0 or gamma_intensity > 1.0:
        raise ValueError("gamma intensity must be in (0, 1]")
    if acquisition_time_s <= 0:
        raise ValueError("acquisition time must be positive")
    if detector_efficiency <= 0 or detector_efficiency > 1.0:
        raise ValueError("detector efficiency must be in (0, 1]")
    return net_counts / (acquisition_time_s * detector_efficiency * gamma_intensity)
