"""Tests for visualization.plotting.geochem.overlay_common helpers."""

from __future__ import annotations

from core import app_state, state_gateway
from visualization.plotting.geochem import overlay_common


def test_format_label_text_supports_age_and_fallback() -> None:
    assert overlay_common._format_label_text("Age={age:.1f}", age=12.34) == "Age=12.3"
    assert overlay_common._format_label_text("Name={name}", name="A") == "Name=A"
    assert overlay_common._format_label_text("Missing={missing}") == "Missing={missing}"
    assert overlay_common._format_label_text(None) is None


def test_label_bbox_uses_defaults_and_custom_edge() -> None:
    assert overlay_common._label_bbox({"label_background": False}) is None

    bbox = overlay_common._label_bbox(
        {
            "label_background": True,
            "label_bg_color": "#ffeecc",
            "label_bg_alpha": 0.6,
        },
        edgecolor="#333333",
    )

    assert bbox == {
        "boxstyle": "round,pad=0.25",
        "facecolor": "#ffeecc",
        "edgecolor": "#333333",
        "alpha": 0.6,
    }


def test_resolve_label_options_ignores_empty_or_none_values() -> None:
    original_line_styles = dict(getattr(app_state, "line_styles", {}) or {})
    try:
        state_gateway.set_line_styles(
            {
                "model_curve": {
                    "label_background": True,
                    "label_bg_alpha": 0.7,
                    "label_bg_color": "",
                    "label_template": None,
                }
            }
        )

        resolved = overlay_common._resolve_label_options(
            "model_curve",
            {
                "label_background": False,
                "label_bg_alpha": 0.5,
                "label_bg_color": "#ffffff",
                "label_template": "Age={age}",
            },
        )

        assert resolved["label_background"] is True
        assert resolved["label_bg_alpha"] == 0.7
        assert resolved["label_bg_color"] == "#ffffff"
        assert resolved["label_template"] == "Age={age}"
    finally:
        state_gateway.set_line_styles(original_line_styles)
