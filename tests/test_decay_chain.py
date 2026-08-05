"""Real-data tests for :mod:`dr_no.decay_chain` (Bateman radioactive decay)."""

from __future__ import annotations

import math

import pytest

from dr_no.decay_chain import (
    SECONDS_PER_DAY,
    SECONDS_PER_HOUR,
    DecayChain,
    Nuclide,
    activities_at_t,
    activity_fraction_remaining,
    activity_from_atoms,
    atoms_from_activity,
    chain_names,
    decay_chains,
    decay_constant,
    lookup_chain,
    populations_at_t,
    time_to_fraction,
    transient_equilibrium_ratio,
)


def test_decay_constant_one_second_half_life() -> None:
    assert decay_constant(1.0) == pytest.approx(math.log(2.0), rel=1e-9)


def test_decay_constant_invalid() -> None:
    with pytest.raises(ValueError):
        decay_constant(0.0)
    with pytest.raises(ValueError):
        decay_constant(-1.0)


def test_activity_from_atoms() -> None:
    lam = decay_constant(1.0)
    assert activity_from_atoms(100.0, lam) == pytest.approx(100.0 * lam, rel=1e-12)


def test_activity_from_atoms_validation() -> None:
    with pytest.raises(ValueError):
        activity_from_atoms(-1.0, 1.0)
    with pytest.raises(ValueError):
        activity_from_atoms(1.0, 0.0)


def test_atoms_from_activity_round_trip() -> None:
    lam = decay_constant(1.0)
    a = 1000.0
    assert activity_from_atoms(atoms_from_activity(a, lam), lam) == pytest.approx(a, rel=1e-9)


def test_atoms_from_activity_validation() -> None:
    with pytest.raises(ValueError):
        atoms_from_activity(-1.0, 1.0)
    with pytest.raises(ValueError):
        atoms_from_activity(1.0, -1.0)


def test_activity_fraction_remaining_half_lives() -> None:
    half = 10.0
    assert activity_fraction_remaining(half, 0.0) == pytest.approx(1.0)
    assert activity_fraction_remaining(half, half) == pytest.approx(0.5)
    assert activity_fraction_remaining(half, 2 * half) == pytest.approx(0.25)


def test_activity_fraction_remaining_validation() -> None:
    with pytest.raises(ValueError):
        activity_fraction_remaining(0.0, 1.0)
    with pytest.raises(ValueError):
        activity_fraction_remaining(1.0, -1.0)


def test_time_to_fraction_inverse() -> None:
    half = 10.0
    assert time_to_fraction(half, 0.5) == pytest.approx(half, rel=1e-9)
    assert time_to_fraction(half, 1.0) == pytest.approx(0.0, abs=1e-9)


def test_time_to_fraction_validation() -> None:
    with pytest.raises(ValueError):
        time_to_fraction(1.0, 0.0)
    with pytest.raises(ValueError):
        time_to_fraction(1.0, 1.5)


def test_nuclide_validation() -> None:
    with pytest.raises(ValueError):
        Nuclide("", 1.0)
    with pytest.raises(ValueError):
        Nuclide("X", 0.0)
    with pytest.raises(ValueError):
        Nuclide("X", -1.0)


def test_nuclide_decay_constant_property() -> None:
    n = Nuclide("X", 1.0)
    assert n.decay_constant == pytest.approx(math.log(2.0), rel=1e-9)


def test_decay_chain_validation() -> None:
    with pytest.raises(ValueError):
        DecayChain("", (Nuclide("A", 1.0), Nuclide("B", 2.0)))
    with pytest.raises(ValueError):
        DecayChain("c", (Nuclide("A", 1.0),))
    with pytest.raises(TypeError):
        DecayChain("c", (Nuclide("A", 1.0), "not a nuclide"))  # type: ignore[arg-type]


def test_decay_chains_table() -> None:
    chains = decay_chains()
    for name in (
        "Mo-99/Tc-99m",
        "I-131/Xe-131m",
        "Cs-137/Ba-137m",
        "Ra-226/Rn-222",
        "U-235/Th-231",
    ):
        assert name in chains
    assert len(chains) >= 5


def test_chain_names_sorted() -> None:
    names = chain_names()
    assert names == tuple(sorted(names))


def test_lookup_chain_known_and_unknown() -> None:
    assert lookup_chain("I-131/Xe-131m").members[0].name == "I-131"
    with pytest.raises(KeyError):
        lookup_chain("no/such")


def test_mo99_i131_real_half_lives() -> None:
    mo = lookup_chain("Mo-99/Tc-99m")
    assert mo.members[0].half_life_s == pytest.approx(65.94 * SECONDS_PER_HOUR, rel=1e-3)
    i131 = lookup_chain("I-131/Xe-131m").members[0]
    assert i131.half_life_s == pytest.approx(8.02 * SECONDS_PER_DAY, rel=1e-3)


def test_populations_at_zero() -> None:
    chain = lookup_chain("Mo-99/Tc-99m")
    pops = populations_at_t(chain, 1000.0, 0.0)
    assert pops[0] == pytest.approx(1000.0)
    assert pops[1] == pytest.approx(0.0, abs=1e-6)


def test_parent_decays_exponentially() -> None:
    chain = lookup_chain("Mo-99/Tc-99m")
    parent_lambda = chain.members[0].decay_constant
    t = 10.0 * SECONDS_PER_HOUR
    pops = populations_at_t(chain, 1000.0, t)
    assert pops[0] == pytest.approx(1000.0 * math.exp(-parent_lambda * t), rel=1e-9)


def test_activities_at_t_zero() -> None:
    chain = lookup_chain("Mo-99/Tc-99m")
    acts = activities_at_t(chain, 1.0e6, 0.0)
    assert acts[0] == pytest.approx(1.0e6, rel=1e-9)
    assert acts[1] == pytest.approx(0.0, abs=1e-6)


def test_activities_at_t_positive() -> None:
    chain = lookup_chain("Mo-99/Tc-99m")
    acts = activities_at_t(chain, 1.0e9, 6.0 * SECONDS_PER_HOUR)
    assert acts[0] > 0
    assert acts[1] > 0


def test_populations_at_t_validation() -> None:
    chain = lookup_chain("Mo-99/Tc-99m")
    with pytest.raises(ValueError):
        populations_at_t(chain, -1.0, 1.0)
    with pytest.raises(ValueError):
        populations_at_t(chain, 1.0, -1.0)
    with pytest.raises(ValueError):
        activities_at_t(chain, -1.0, 1.0)


def test_transient_equilibrium_ratio_mo99() -> None:
    chain = lookup_chain("Mo-99/Tc-99m")
    ratio = transient_equilibrium_ratio(chain)
    # Daughter (Tc-99m, 6.0 h) decays faster than parent (Mo-99, 66 h).
    assert ratio > 1.0


def test_transient_equilibrium_ratio_ra226_secular_approx() -> None:
    chain = lookup_chain("Ra-226/Rn-222")
    ratio = transient_equilibrium_ratio(chain)
    # Radon-222 decays far faster than Ra-226: ratio approaches 1 (secular).
    assert ratio == pytest.approx(1.0, abs=1e-3)


def test_transient_equilibrium_ratio_requires_faster_daughter() -> None:
    # In I-131 → Xe-131m the daughter is longer lived; no equilibrium exists.
    chain = lookup_chain("I-131/Xe-131m")
    with pytest.raises(ValueError):
        transient_equilibrium_ratio(chain)


def test_transient_equilibrium_ratio_needs_two_members() -> None:
    chain = DecayChain("three", (Nuclide("A", 1.0), Nuclide("B", 2.0), Nuclide("C", 3.0)))
    with pytest.raises(ValueError):
        transient_equilibrium_ratio(chain)


def test_bateman_degenerate_lambdas_raises() -> None:
    chain = DecayChain("deg", (Nuclide("A", 10.0), Nuclide("B", 10.0)))
    with pytest.raises(ValueError):
        populations_at_t(chain, 100.0, 1.0)
