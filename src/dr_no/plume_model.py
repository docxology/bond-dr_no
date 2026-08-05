"""Gaussian plume dispersion model — advection and concentration of a radioactive release.

CRAB KEY's atmospheric-dispersion core models how an airborne contaminant
released at a point is blown downwind. It implements the classic steady-state
Gaussian plume with Pasquill–Gifford dispersion parameters:

.. math::

    C(x, y, z) = \\frac{Q}{2\\,\\pi\\,u\\,\\sigma_y\\,\\sigma_z}\\
        \\exp\\!\\left(-\\frac{y^2}{2\\sigma_y^2}\\right)\\
        \\left[\\exp\\!\\left(-\\frac{(z-H)^2}{2\\sigma_z^2}\\right)
        + \\exp\\!\\left(-\\frac{(z+H)^2}{2\\sigma_z^2}\\right)\\right]

where :math:`x` is downwind distance, :math:`y` crosswind, :math:`z` height
above ground, :math:`Q` the release rate (Bq/s), :math:`u` the wind speed,
:math:`H` the effective release height, and :math:`\\sigma_y, \\sigma_z` the
dispersion coefficients that grow with downwind distance according to the
Pasquill–Gifford stability class (A–F).

Pure domain logic (standard library + numpy only): importable standalone and
independent of the BOND protocol.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

__all__ = [
    "STABILITY_CLASSES",
    "PlumeResult",
    "StabilitySpec",
    "centerline_concentration",
    "find_ground_level_max",
    "gaussian_plume_concentration",
    "grid_concentration",
    "isopleth_extent",
    "sigma_y",
    "sigma_z",
]

# Pasquill-Gifford classes A-F (unstable -> stable).
STABILITY_CLASSES = ("A", "B", "C", "D", "E", "F")


@dataclass(frozen=True)
class StabilitySpec:
    """Pasquill–Gifford dispersion coefficients (Martin/Green, 1976 form).

    ``sigma_y = a_y * x^b_y`` and ``sigma_z = c_z * x^d_z + f_z`` where ``x`` is
    downwind distance in kilometres; the results are returned in metres.
    """

    class_label: str
    a_y: float
    b_y: float
    c_z: float
    d_z: float
    f_z: float

    def __post_init__(self) -> None:
        if self.class_label not in STABILITY_CLASSES:
            raise ValueError(
                f"stability spec class must be one of {STABILITY_CLASSES}, got {self.class_label!r}"
            )


#: Canonical Pasquill–Gifford coefficient table (x in km, sigma in m).
STABILITY_TABLE: dict[str, StabilitySpec] = {
    "A": StabilitySpec("A", 0.3658, 0.9031, 0.00024, 2.1250, 0.0),
    "B": StabilitySpec("B", 0.2751, 0.9031, 0.0550, 1.6674, 0.0),
    "C": StabilitySpec("C", 0.2089, 0.9031, 0.1130, 0.9169, 0.0),
    "D": StabilitySpec("D", 0.1474, 0.9031, 0.2227, 0.7255, 0.0),
    "E": StabilitySpec("E", 0.1046, 0.9031, 0.2118, 0.6784, 0.0),
    "F": StabilitySpec("F", 0.0708, 0.9031, 0.0864, 0.7400, 0.0),
}

_KM = 1000.0  # metres per km


def _spec(stability: str) -> StabilitySpec:
    try:
        return STABILITY_TABLE[stability]
    except KeyError:
        raise ValueError(
            f"unknown stability class {stability!r}; expected one of {STABILITY_CLASSES}"
        ) from None


def sigma_y(x_m: float, stability: str) -> float:
    """Horizontal dispersion coefficient (m) at downwind distance ``x_m`` (m)."""
    if x_m < 0:
        raise ValueError("downwind distance must be non-negative")
    spec = _spec(stability)
    x_km = x_m / _KM
    # Martin/Greene coefficients take x in km and yield sigma in km -> convert to m.
    return float(_KM * spec.a_y * (x_km**spec.b_y))


def sigma_z(x_m: float, stability: str) -> float:
    """Vertical dispersion coefficient (m) at downwind distance ``x_m`` (m)."""
    if x_m < 0:
        raise ValueError("downwind distance must be non-negative")
    spec = _spec(stability)
    x_km = x_m / _KM
    return float(_KM * (spec.c_z * (x_km**spec.d_z) + spec.f_z))


def _validate_source(Q: float, u: float, H: float) -> None:
    if Q <= 0:
        raise ValueError("release rate Q must be positive")
    if u <= 0:
        raise ValueError("wind speed must be positive")
    if H < 0:
        raise ValueError("effective release height must be non-negative")


def gaussian_plume_concentration(
    x_m: float,
    y_m: float,
    z_m: float,
    *,
    Q: float,
    u: float,
    stability: str,
    H: float = 0.0,
) -> float:
    """Ground- or elevated-receptor concentration (Bq/m^3) at a downwind point.

    ``x_m`` is downwind distance, ``y_m`` crosswind offset, ``z_m`` receptor
    height, ``Q`` release rate (Bq/s), ``u`` wind speed (m/s), ``H`` effective
    release height (m), and ``stability`` a Pasquill–Gifford class (A–F).

    The model includes the ground-reflection term so a raised plume
    (``H > 0``) deposits concentration at ground level (``z_m = 0``).
    """
    _validate_source(Q, u, H)
    if x_m <= 0:
        return 0.0
    sy = sigma_y(x_m, stability)
    sz = sigma_z(x_m, stability)
    y_term = math.exp(-(y_m * y_m) / (2.0 * sy * sy))
    z_plus = math.exp(-((z_m - H) ** 2) / (2.0 * sz * sz))
    z_minus = math.exp(-((z_m + H) ** 2) / (2.0 * sz * sz))
    return Q / (2.0 * math.pi * u * sy * sz) * y_term * (z_plus + z_minus)


def centerline_concentration(
    x_m: float,
    *,
    Q: float,
    u: float,
    stability: str,
    H: float = 0.0,
) -> float:
    """Ground-level concentration (Bq/m^3) on the plume centreline at ``x_m``.

    Equivalent to :func:`gaussian_plume_concentration` at ``y=0, z=0``.
    """
    return gaussian_plume_concentration(x_m, 0.0, 0.0, Q=Q, u=u, stability=stability, H=H)


def grid_concentration(
    x: Iterable[float],
    y: Iterable[float],
    z_m: float,
    *,
    Q: float,
    u: float,
    stability: str,
    H: float = 0.0,
) -> np.ndarray:
    """Concentration field (Bq/m^3) over a downwind/crosswind grid at height ``z_m``."""
    xa = np.asarray(list(x), dtype=float)
    ya = np.asarray(list(y), dtype=float)
    grid = np.empty((xa.size, ya.size), dtype=float)
    for i, xi in enumerate(xa):
        for j, yi in enumerate(ya):
            grid[i, j] = gaussian_plume_concentration(
                float(xi), float(yi), z_m, Q=Q, u=u, stability=stability, H=H
            )
    return grid


def find_ground_level_max(
    x_m: float,
    *,
    Q: float,
    u: float,
    stability: str,
    H: float = 0.0,
    n_crosswind: int = 101,
    crosswind_span_m: float = 200.0,
) -> PlumeResult:
    """Locate the maximum ground-level concentration on a crosswind transect.

    Scans ``y`` in ``[-span/2, span/2]`` at downwind distance ``x_m`` and
    returns the peak value and its crosswind offset.

    Returns:
        A :class:`PlumeResult` with ``max_concentration`` and ``y`` at the max.
    """
    _validate_source(Q, u, H)
    if n_crosswind < 2:
        raise ValueError("n_crosswind must be >= 2")
    half = crosswind_span_m / 2.0
    ys = np.linspace(-half, half, n_crosswind)
    values = [
        gaussian_plume_concentration(x_m, float(yv), 0.0, Q=Q, u=u, stability=stability, H=H)
        for yv in ys
    ]
    idx = int(np.argmax(values))
    return PlumeResult(max_concentration=float(values[idx]), y_at_max=float(ys[idx]), x=x_m)


@dataclass(frozen=True)
class PlumeResult:
    """Summary of a plume concentration profile at a given downwind distance."""

    max_concentration: float
    y_at_max: float
    x: float


def isopleth_extent(
    threshold: float,
    *,
    Q: float,
    u: float,
    stability: str,
    H: float = 0.0,
    max_km: float = 50.0,
    steps: int = 200,
    n_scan: int = 512,
) -> float:
    """Farthest downwind distance (m) whose centreline concentration is ``>= threshold``.

    The ground-level centreline profile of an **elevated** release is not
    monotonic: it is ~0 at the source (the plume is still aloft), rises to a
    maximum some way downwind as vertical spreading brings it to ground, then
    decays. A plain bisection seeded at the release point is therefore invalid —
    it assumes a monotone profile that only exists for a ground-level release
    (``H = 0``).

    This implementation does it in two deterministic stages:

    1. **Locate the ground-level maximum** with a log-spaced scan of ``n_scan``
       points over ``[1 m, max_km]``. If even the maximum is below ``threshold``
       the release never reaches it anywhere, and the extent is ``0.0``.
    2. **Bisect the decaying tail** from that maximum outward, where the profile
       *is* monotone, for the crossing point.

    Both failure modes this replaces produced a wrong number rather than an
    error: seeded at ``x = 1 m``, the old search returned ``1.0`` for a release
    that contaminated nothing, and ``0.0`` for an elevated release whose
    threshold sat between the near-field value and the true downwind peak —
    silently reporting "no contamination" over a contaminated area.

    Args:
        threshold: concentration (Bq/m³) defining the isopleth.
        Q: release rate (Bq/s).
        u: wind speed (m/s).
        stability: Pasquill-Gifford class (A-F).
        H: effective release height (m).
        max_km: outer bound of the search (km).
        steps: bisection iterations on the tail.
        n_scan: log-spaced samples used to locate the ground-level maximum.

    Returns:
        The farthest downwind distance (m) at or above ``threshold``, ``max_km``
        in metres if the threshold still holds at the outer bound, or ``0.0``
        if it is never met. Deterministic.
    """
    _validate_source(Q, u, H)
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    if steps < 2:
        raise ValueError("steps must be >= 2")
    if n_scan < 2:
        raise ValueError("n_scan must be >= 2")

    hi = max_km * _KM

    # Stage 1: find the ground-level maximum of the (unimodal) profile.
    scan = np.logspace(0.0, math.log10(hi), n_scan)  # 1 m .. max_km, log-spaced
    values = [centerline_concentration(float(x), Q=Q, u=u, stability=stability, H=H) for x in scan]
    peak_index = int(np.argmax(values))
    if values[peak_index] < threshold:
        return 0.0
    if centerline_concentration(hi, Q=Q, u=u, stability=stability, H=H) >= threshold:
        return hi

    # Stage 2: bisect the monotone decaying tail beyond the peak.
    lo = float(scan[peak_index])
    for _ in range(steps):
        mid = 0.5 * (lo + hi)
        if centerline_concentration(mid, Q=Q, u=u, stability=stability, H=H) >= threshold:
            lo = mid
        else:
            hi = mid
    return lo
