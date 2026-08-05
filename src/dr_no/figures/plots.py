"""CRAB KEY figure generators (matplotlib, headless).

Deterministic visualizations of the two lead concepts:

* :func:`plot_gamma_spectrum` — a synthesized gamma spectrum with detected
  peaks marked and the top isotope identification annotated (isotope forensics);
* :func:`plot_plume_field` — a downwind/crosswind Gaussian-plume concentration
  field (dispersion modelling).

All writers target ``output/figures/`` under the package root. Pure domain
visualization; no infrastructure imports.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from dr_no.canonical import BACKGROUND_LEVEL, canonical_spectrum
from dr_no.decay_chain import activities_at_t, lookup_chain
from dr_no.isotope_profiles import detect_peaks, identify_isotopes
from dr_no.plume_model import grid_concentration
from dr_no.scenario import MissionScenario, load_scenario

__all__ = ["plot_decay_curves", "plot_gamma_spectrum", "plot_plume_field", "render_all"]

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
FIGURES_DIR = PACKAGE_ROOT / "output" / "figures"


def _figure_path(name: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return FIGURES_DIR / name


def plot_gamma_spectrum(
    *,
    scenario: MissionScenario | None = None,
    output_path: str | Path | None = None,
) -> Path:
    """Render a synthesized gamma spectrum with detected peaks and top isotope.

    Renders **the canonical spectrum** — the same energy grid, source mixture,
    and detector settings that :func:`dr_no.canonical.canonical_metrics` scores.
    Previously this figure re-declared its own 1500-bin grid and its own source
    mixture, so the published figure was not a picture of the published numbers.

    Args:
        scenario: An explicit scenario; defaults to ``manuscript/config.yaml``.
        output_path: destination PNG path (default ``output/figures/gamma_spectrum.png``).
    """
    spec = scenario if scenario is not None else load_scenario()
    path = Path(output_path) if output_path is not None else _figure_path("gamma_spectrum.png")
    energies, counts = canonical_spectrum(spec)
    peaks = detect_peaks(energies, counts, background_level=BACKGROUND_LEVEL)
    identifications = identify_isotopes(peaks)
    top = identifications[0].isotope if identifications else "unknown"

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(energies, counts, lw=0.8, color="#1e3a8a", label="synthesized spectrum")
    for peak in peaks:
        ax.axvline(peak.energy_keV, color="#dc2626", lw=0.6, alpha=0.7)
    # Proxy handle for the legend: drawing a real axvline at E=0 purely to earn a
    # legend entry would put a spurious data mark on the plot.
    ax.plot(
        [],
        [],
        color="#dc2626",
        lw=0.6,
        alpha=0.7,
        label=f"detected peaks (n={len(peaks)})",
    )
    ax.set_xlabel("Energy (keV)")
    ax.set_ylabel("Counts")
    ax.set_title(f"CRAB KEY gamma spectrum — top identification: {top}")
    ax.legend(fontsize=8)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_plume_field(
    *,
    scenario: MissionScenario | None = None,
    output_path: str | Path | None = None,
) -> Path:
    """Render a Gaussian-plume ground-level concentration field.

    Uses the scenario's release rate, wind speed, stability class **and release
    height**. The release height was previously omitted here while the metrics
    used 10 m, so the figure showed a different plume from the one assessed.

    Args:
        scenario: An explicit scenario; defaults to ``manuscript/config.yaml``.
        output_path: destination PNG path (default ``output/figures/plume_field.png``).
    """
    spec = scenario if scenario is not None else load_scenario()
    plume = spec.plume
    path = Path(output_path) if output_path is not None else _figure_path("plume_field.png")
    x = np.linspace(10.0, 5000.0, 120)
    y = np.linspace(-600.0, 600.0, 120)
    field = grid_concentration(
        x,
        y,
        0.0,
        Q=plume.source_Q_bq_s,
        u=plume.wind_speed_m_s,
        stability=plume.stability,
        H=plume.release_height_m,
    )

    fig, ax = plt.subplots(figsize=(7, 4.5))
    im = ax.pcolormesh(x, y, field.T, shading="auto", cmap="inferno", norm="log")
    ax.set_xlabel("Downwind distance (m)")
    ax.set_ylabel("Crosswind offset (m)")
    ax.set_title(
        f"CRAB KEY plume dispersion — stability {plume.stability}, "
        f"u={plume.wind_speed_m_s:g} m/s, H={plume.release_height_m:g} m"
    )
    fig.colorbar(im, ax=ax, label="Concentration (Bq/m$^3$)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_decay_curves(
    *,
    chain_name: str | None = None,
    hours: float = 72.0,
    initial_activity_bq: float = 1.0e10,
    output_path: str | Path | None = None,
) -> Path:
    """Render parent and daughter activity curves for a two-member decay chain.

    Args:
        chain_name: a two-member chain from ``decay_chain.decay_chains()``.
            Defaults to the scenario's declared ``decay_projection.chain``.
        hours: horizontal span of the plot.
        initial_activity_bq: the parent's initial activity (Bq).
        output_path: destination PNG path (default ``output/figures/decay_curves.png``).
    """
    if chain_name is None:
        chain_name = load_scenario().decay_projection.chain
    path = Path(output_path) if output_path is not None else _figure_path("decay_curves.png")
    chain = lookup_chain(chain_name)
    hours_arr = np.linspace(0.0, hours, 200)
    parent_name = chain.members[0].name
    daughter_name = chain.members[1].name
    parent_act: list[float] = []
    daughter_act: list[float] = []
    for h in hours_arr:
        acts = activities_at_t(chain, initial_activity_bq, h * 3600.0)
        parent_act.append(acts[0])
        daughter_act.append(acts[1])

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(hours_arr, parent_act, color="#1e3a8a", label=parent_name)
    ax.plot(hours_arr, daughter_act, color="#dc2626", label=daughter_name)
    ax.set_xlabel("Elapsed time (h)")
    ax.set_ylabel("Activity (Bq)")
    ax.set_title(f"CRAB KEY decay chain — {chain_name}")
    ax.legend()
    ax.set_yscale("log")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def render_all() -> list[Path]:
    """Render every CRAB KEY figure; returns the written paths."""
    return [plot_gamma_spectrum(), plot_plume_field(), plot_decay_curves()]
