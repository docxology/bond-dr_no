"""Radioactive decay chains — Bateman equations over real nuclide half-lives.

CRAB KEY's time-dependence core. Given a chain of nuclides A → B → C → … with
known half-lives, the Bateman solution describes how atom counts and activities
evolve in time:

.. math::

    N_k(t) = N_0 \\sum_{j=1}^{k}
        \\left[\\frac{\\prod_{i \\neq j}^{k} \\lambda_i}
        {\\prod_{i \\neq j}^{k}(\\lambda_i - \\lambda_j)}\\right]
        e^{-\\lambda_j t}

The module ships a small table of real decay chains (parent → daughter) with
their literature half-lives, plus the standard derived quantities: decay
constants, activity↔atom conversions, transient-equilibrium ratios, and
fraction-remaining/time-to-fraction helpers for a single nuclide.

Pure domain logic: deterministic, standard library only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "DecayChain",
    "Nuclide",
    "activities_at_t",
    "activity_fraction_remaining",
    "activity_from_atoms",
    "atoms_from_activity",
    "chain_names",
    "decay_chains",
    "decay_constant",
    "lookup_chain",
    "populations_at_t",
    "time_to_fraction",
    "transient_equilibrium_ratio",
]

# Time-unit conversions (seconds).
SECONDS_PER_MINUTE = 60.0
SECONDS_PER_HOUR = 3600.0
SECONDS_PER_DAY = 86400.0
SECONDS_PER_YEAR = 365.25 * SECONDS_PER_DAY


def decay_constant(half_life_s: float) -> float:
    """The decay constant (s⁻¹) for a half-life in seconds: ``lambda = ln2 / T``."""
    if half_life_s <= 0:
        raise ValueError("half-life must be positive")
    return float(math.log(2.0) / half_life_s)


def activity_from_atoms(atom_count: float, lambda_: float) -> float:
    """Activity (Bq) from an atom count and decay constant: ``A = lambda * N``."""
    if atom_count < 0:
        raise ValueError("atom count must be non-negative")
    if lambda_ <= 0:
        raise ValueError("decay constant must be positive")
    return lambda_ * atom_count


def atoms_from_activity(activity_bq: float, lambda_: float) -> float:
    """Atom count from an activity (Bq) and decay constant: ``N = A / lambda``."""
    if activity_bq < 0:
        raise ValueError("activity must be non-negative")
    if lambda_ <= 0:
        raise ValueError("decay constant must be positive")
    return float(activity_bq / lambda_)


def activity_fraction_remaining(half_life_s: float, elapsed_s: float) -> float:
    """Fraction of activity remaining after ``elapsed_s``: ``2^(-t/T)``."""
    if half_life_s <= 0:
        raise ValueError("half-life must be positive")
    if elapsed_s < 0:
        raise ValueError("elapsed time must be non-negative")
    return float(2.0 ** (-elapsed_s / half_life_s))


def time_to_fraction(half_life_s: float, fraction: float) -> float:
    """Time (s) after which the remaining fraction of a nuclide equals ``fraction``."""
    if half_life_s <= 0:
        raise ValueError("half-life must be positive")
    if not 0.0 < fraction <= 1.0:
        raise ValueError("fraction must be in (0, 1]")
    return float(-half_life_s * math.log(fraction) / math.log(2.0))


@dataclass(frozen=True)
class Nuclide:
    """A nuclide in a decay chain: name and half-life (seconds)."""

    name: str
    half_life_s: float

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("nuclide name must be non-empty")
        if self.half_life_s <= 0:
            raise ValueError("half-life must be positive")

    @property
    def decay_constant(self) -> float:
        """This nuclide's decay constant (s⁻¹)."""
        return decay_constant(self.half_life_s)


@dataclass(frozen=True)
class DecayChain:
    """A linear decay chain: ordered member nuclides (parent first)."""

    name: str
    members: tuple[Nuclide, ...]

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("chain name must be non-empty")
        if len(self.members) < 2:
            raise ValueError("a decay chain needs at least two members")
        for member in self.members:
            if not isinstance(member, Nuclide):
                raise TypeError("chain members must be Nuclide instances")


#: Real decay chains (parent → daughter) with literature half-lives.
_DECAY_CHAINS: dict[str, DecayChain] = {
    "Mo-99/Tc-99m": DecayChain(
        "Mo-99/Tc-99m",
        (Nuclide("Mo-99", 65.94 * SECONDS_PER_HOUR), Nuclide("Tc-99m", 6.006 * SECONDS_PER_HOUR)),
    ),
    "Cs-137/Ba-137m": DecayChain(
        "Cs-137/Ba-137m",
        (
            Nuclide("Cs-137", 30.08 * SECONDS_PER_YEAR),
            Nuclide("Ba-137m", 2.552 * SECONDS_PER_MINUTE),
        ),
    ),
    "Ra-226/Rn-222": DecayChain(
        "Ra-226/Rn-222",
        (Nuclide("Ra-226", 1600.0 * SECONDS_PER_YEAR), Nuclide("Rn-222", 3.8235 * SECONDS_PER_DAY)),
    ),
    "I-131/Xe-131m": DecayChain(
        "I-131/Xe-131m",
        (Nuclide("I-131", 8.02 * SECONDS_PER_DAY), Nuclide("Xe-131m", 11.84 * SECONDS_PER_DAY)),
    ),
    "U-235/Th-231": DecayChain(
        "U-235/Th-231",
        (Nuclide("U-235", 7.038e8 * SECONDS_PER_YEAR), Nuclide("Th-231", 25.52 * SECONDS_PER_HOUR)),
    ),
}


def decay_chains() -> dict[str, DecayChain]:
    """The immutable decay-chain table keyed by chain name."""
    return dict(_DECAY_CHAINS)


def chain_names() -> tuple[str, ...]:
    """Sorted names of every decay chain in the table."""
    return tuple(sorted(_DECAY_CHAINS))


def lookup_chain(name: str) -> DecayChain:
    """Look up a decay chain by name or raise ``KeyError``."""
    try:
        return _DECAY_CHAINS[name]
    except KeyError:
        raise KeyError(f"unknown decay chain {name!r}; available: {chain_names()}") from None


def _bateman_coefficients(lambdas: tuple[float, ...]) -> list[list[float]]:
    """Bateman coefficients ``C[k][j]`` for an n-member chain of distinct lambdas.

    ``N_k(t) = N0 * sum_j C[k][j] * exp(-lambda_j * t)`` with

    .. math::

        C[k][j] = \\frac{\\prod_{i=1}^{k-1} \\lambda_i}
        {\\prod_{i=1, i\\neq j}^{k}(\\lambda_i - \\lambda_j)}

    This makes ``N_k(0) = 0`` for every daughter (k > 1), as physically required
    when only the parent carries initial atoms.
    """
    n = len(lambdas)
    coefficients: list[list[float]] = []
    for k in range(1, n + 1):  # k = member index (1-based)
        numerator = math.prod(lambdas[: k - 1])  # empty product = 1 for k == 1
        row: list[float] = []
        for j in range(1, k + 1):
            denominator = 1.0
            for i in range(1, k + 1):
                if i == j:
                    continue
                denominator *= lambdas[i - 1] - lambdas[j - 1]
            if denominator == 0.0:
                raise ValueError("Bateman solution requires distinct decay constants")
            row.append(numerator / denominator)
        coefficients.append(row)
    return coefficients


def populations_at_t(
    chain: DecayChain,
    initial_parent_atoms: float,
    elapsed_s: float,
) -> tuple[float, ...]:
    """Atom counts of every member at ``elapsed_s`` (Bateman solution).

    Args:
        chain: the decay chain.
        initial_parent_atoms: N0 — initial parent atom count (daughters start at 0).
        elapsed_s: elapsed time in seconds.

    Returns:
        Atom count per member, parent first.
    """
    if initial_parent_atoms < 0:
        raise ValueError("initial parent atoms must be non-negative")
    if elapsed_s < 0:
        raise ValueError("elapsed time must be non-negative")
    lambdas = tuple(member.decay_constant for member in chain.members)
    coefficients = _bateman_coefficients(lambdas)
    populations: list[float] = []
    for k in range(len(chain.members)):
        total = 0.0
        for j in range(k + 1):
            total += coefficients[k][j] * math.exp(-lambdas[j] * elapsed_s)
        populations.append(initial_parent_atoms * total)
    return tuple(populations)


def activities_at_t(
    chain: DecayChain,
    initial_parent_activity_bq: float,
    elapsed_s: float,
) -> tuple[float, ...]:
    """Activities (Bq) of every member at ``elapsed_s`` given an initial parent activity.

    Converts the initial activity to parent atoms, integrates the chain, then
    multiplies each population by its decay constant.
    """
    if initial_parent_activity_bq < 0:
        raise ValueError("initial parent activity must be non-negative")
    parent_lambda = chain.members[0].decay_constant
    initial_atoms = atoms_from_activity(initial_parent_activity_bq, parent_lambda)
    populations = populations_at_t(chain, initial_atoms, elapsed_s)
    return tuple(
        activity_from_atoms(populations[i], chain.members[i].decay_constant)
        for i in range(len(chain.members))
    )


def transient_equilibrium_ratio(chain: DecayChain) -> float:
    """The transient-equilibrium daughter/parent activity ratio.

    For a two-member chain with ``lambda_daughter > lambda_parent`` the ratio
    converges to ``lambda_d / (lambda_d - lambda_p)``.
    """
    if len(chain.members) != 2:
        raise ValueError("transient equilibrium ratio is defined for two-member chains")
    parent_lambda = chain.members[0].decay_constant
    daughter_lambda = chain.members[1].decay_constant
    if daughter_lambda <= parent_lambda:
        raise ValueError(
            "transient equilibrium requires the daughter to decay faster than the parent"
        )
    return float(daughter_lambda / (daughter_lambda - parent_lambda))
