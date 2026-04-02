"""Compatibility checks for legacy state_gateway.set_attr routing."""

from __future__ import annotations

from core import app_state, state_gateway


def test_group_and_data_columns_set_attr_compatibility() -> None:
    original_group_cols = list(getattr(app_state, "group_cols", []) or [])
    original_data_cols = list(getattr(app_state, "data_cols", []) or [])

    try:
        state_gateway.set_group_data_columns(["G0"], ["A", "B", "C"])

        state_gateway.set_attr("group_cols", ["G1", "G2"])
        assert app_state.group_cols == ["G1", "G2"]
        assert app_state.data_cols == ["A", "B", "C"]

        state_gateway.set_attr("data_cols", ["X", "Y"])
        assert app_state.group_cols == ["G1", "G2"]
        assert app_state.data_cols == ["X", "Y"]

        store_snapshot = app_state.state_store.snapshot()
        assert store_snapshot["group_cols"] == ["G1", "G2"]
        assert store_snapshot["data_cols"] == ["X", "Y"]
    finally:
        state_gateway.set_group_data_columns(original_group_cols, original_data_cols)


def test_tooltip_set_attr_compatibility() -> None:
    original_show_tooltip = bool(getattr(app_state, "show_tooltip", False))

    try:
        state_gateway.set_attr("show_tooltip", True)
        assert app_state.show_tooltip is True
        assert app_state.state_store.snapshot()["show_tooltip"] is True

        state_gateway.set_attr("show_tooltip", False)
        assert app_state.show_tooltip is False
        assert app_state.state_store.snapshot()["show_tooltip"] is False
    finally:
        state_gateway.set_show_tooltip(original_show_tooltip)


def test_export_image_options_set_attr_compatibility() -> None:
    original_options = dict(getattr(app_state, "export_image_options", {}) or {})

    try:
        state_gateway.set_attr(
            "export_image_options",
            {
                "preset_key": "ieee_single",
                "image_ext": "SVG",
                "dpi": 50,
                "bbox_tight": False,
                "pad_inches": -1.0,
                "transparent": True,
                "point_size": 13,
                "legend_size": 8,
            },
        )

        options = state_gateway.get_export_image_options()
        assert options["preset_key"] == "ieee_single"
        assert options["image_ext"] == "svg"
        assert options["dpi"] == 72
        assert options["bbox_tight"] is False
        assert options["pad_inches"] == 0.0
        assert options["transparent"] is True
        assert options["point_size"] == 13
        assert options["legend_size"] == 8
    finally:
        state_gateway.set_export_image_options(**original_options)
