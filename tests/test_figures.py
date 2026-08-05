"""Tests for CRAB KEY figure generators (:mod:`dr_no.figures.plots`)."""

from __future__ import annotations

from pathlib import Path

from dr_no.figures.plots import (
    FIGURES_DIR,
    plot_decay_curves,
    plot_gamma_spectrum,
    plot_plume_field,
    render_all,
)


def test_plot_gamma_spectrum(tmp_path: Path) -> None:
    out = plot_gamma_spectrum(output_path=tmp_path / "spec.png")
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_plume_field(tmp_path: Path) -> None:
    out = plot_plume_field(output_path=tmp_path / "plume.png")
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_decay_curves(tmp_path: Path) -> None:
    out = plot_decay_curves(output_path=tmp_path / "decay.png")
    assert out.exists()
    assert out.stat().st_size > 0


def test_render_all(tmp_path: Path) -> None:
    paths = render_all()
    assert len(paths) == 3
    for path in paths:
        assert path.suffix == ".png"


def test_figures_dir_is_configured() -> None:
    assert FIGURES_DIR.name == "figures"
