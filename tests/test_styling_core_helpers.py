"""Tests for plotting styling core helper functions."""

from __future__ import annotations

import matplotlib.pyplot as plt

from core import app_state
from visualization.plotting.styling.core import _apply_axis_text_style, _enforce_plot_style


def _snapshot_style_state() -> dict[str, object]:
    keys = [
        "fig",
        "label_color",
        "label_weight",
        "label_pad",
        "title_color",
        "title_weight",
        "plot_style_grid",
        "grid_color",
        "grid_linewidth",
        "grid_alpha",
        "grid_linestyle",
        "minor_ticks",
        "minor_grid",
        "tick_direction",
        "tick_length",
        "tick_width",
        "tick_color",
        "minor_tick_length",
        "minor_tick_width",
        "axis_linewidth",
        "axis_line_color",
        "show_top_spine",
        "show_right_spine",
    ]
    return {key: getattr(app_state, key, None) for key in keys}


def _restore_style_state(snapshot: dict[str, object]) -> None:
    for key, value in snapshot.items():
        setattr(app_state, key, value)


def test_apply_axis_text_style_updates_axis_labels_and_title() -> None:
    snapshot = _snapshot_style_state()
    fig, ax = plt.subplots()
    try:
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title("Title")

        setattr(app_state, "label_color", "#112233")
        setattr(app_state, "label_weight", "bold")
        setattr(app_state, "label_pad", 9.0)
        setattr(app_state, "title_color", "#334455")
        setattr(app_state, "title_weight", "normal")

        _apply_axis_text_style(ax)

        assert ax.xaxis.label.get_color() == "#112233"
        assert ax.yaxis.label.get_color() == "#112233"
        assert ax.xaxis.label.get_fontweight() == "bold"
        assert ax.yaxis.label.get_fontweight() == "bold"
        assert ax.xaxis.labelpad == 9.0
        assert ax.yaxis.labelpad == 9.0
        assert ax.title.get_color() == "#334455"
        assert ax.title.get_fontweight() == "normal"
    finally:
        plt.close(fig)
        _restore_style_state(snapshot)


def test_enforce_plot_style_applies_spine_visibility_and_tick_direction() -> None:
    snapshot = _snapshot_style_state()
    fig, ax = plt.subplots()
    try:
        setattr(app_state, "fig", fig)
        setattr(app_state, "plot_style_grid", False)
        setattr(app_state, "minor_ticks", False)
        setattr(app_state, "minor_grid", False)
        setattr(app_state, "tick_direction", "in")
        setattr(app_state, "tick_length", 6.0)
        setattr(app_state, "tick_width", 1.1)
        setattr(app_state, "tick_color", "#222222")
        setattr(app_state, "minor_tick_length", 3.0)
        setattr(app_state, "minor_tick_width", 0.7)
        setattr(app_state, "axis_linewidth", 1.3)
        setattr(app_state, "axis_line_color", "#123456")
        setattr(app_state, "show_top_spine", False)
        setattr(app_state, "show_right_spine", True)

        _enforce_plot_style(ax)

        assert ax.spines["top"].get_visible() is False
        assert ax.spines["right"].get_visible() is True
        assert ax.spines["left"].get_linewidth() == 1.3
        assert ax.spines["left"].get_edgecolor() != (0.0, 0.0, 0.0, 0.0)
        assert fig.patch.get_facecolor() is not None
    finally:
        plt.close(fig)
        _restore_style_state(snapshot)
