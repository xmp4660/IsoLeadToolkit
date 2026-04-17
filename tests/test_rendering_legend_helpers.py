"""Tests for rendering common legend helper functions."""

from __future__ import annotations

from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from visualization.plotting.rendering.common import legend as legend_helpers


def test_build_legend_proxies_uses_patch_when_any_handle_is_patch(monkeypatch) -> None:
    monkeypatch.setattr(
        legend_helpers,
        "group_legend_items",
        lambda all_groups: [
            {"marker": "o", "color": "#111111"},
            {"marker": "s", "color": "#222222"},
        ],
    )

    handles = [Patch(facecolor="#aaaaaa")]
    labels = ["A", "B"]

    proxies = legend_helpers._build_legend_proxies(handles, labels)

    assert len(proxies) == 2
    assert all(isinstance(item, Patch) for item in proxies)


def test_build_overlay_legend_entries_translates_and_applies_style(monkeypatch) -> None:
    monkeypatch.setattr(
        legend_helpers,
        "overlay_legend_items",
        lambda actual_algorithm: [
            {
                "style_key": "model_curve",
                "fallback": {},
                "default_color": "#333333",
                "label_key": "Model Curve",
            }
        ],
    )
    monkeypatch.setattr(
        legend_helpers,
        "resolve_line_style",
        lambda _state, _key, _fallback: {
            "color": "#ff0000",
            "linewidth": 2.0,
            "linestyle": "--",
            "alpha": 0.5,
        },
    )
    monkeypatch.setattr(legend_helpers, "translate", lambda text: f"T:{text}")

    entries = legend_helpers._build_overlay_legend_entries("PB_EVOL_76")

    assert len(entries) == 1
    handle, label = entries[0]
    assert isinstance(handle, Line2D)
    assert handle.get_color() == "#ff0000"
    assert handle.get_linewidth() == 2.0
    assert handle.get_linestyle() == "--"
    assert handle.get_alpha() == 0.5
    assert label == "T:Model Curve"
