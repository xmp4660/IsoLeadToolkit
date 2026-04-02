"""Tests for StateStore-backed gateway mutations."""

from __future__ import annotations

from typing import Any

from core import app_state, state_gateway


def _snapshot_state() -> dict[str, Any]:
    return {
        "render_mode": getattr(app_state, "render_mode", "UMAP"),
        "algorithm": getattr(app_state, "algorithm", "UMAP"),
        "selected_indices": set(getattr(app_state, "selected_indices", set()) or set()),
        "selection_mode": bool(getattr(app_state, "selection_mode", False)),
        "available_groups": list(getattr(app_state, "available_groups", []) or []),
        "visible_groups": list(getattr(app_state, "visible_groups", []) or []) if getattr(app_state, "visible_groups", None) else None,
        "selected_2d_cols": list(getattr(app_state, "selected_2d_cols", []) or []),
        "selected_3d_cols": list(getattr(app_state, "selected_3d_cols", []) or []),
        "selected_ternary_cols": list(getattr(app_state, "selected_ternary_cols", []) or []),
        "selected_2d_confirmed": bool(getattr(app_state, "selected_2d_confirmed", False)),
        "selected_3d_confirmed": bool(getattr(app_state, "selected_3d_confirmed", False)),
        "selected_ternary_confirmed": bool(getattr(app_state, "selected_ternary_confirmed", False)),
        "export_image_options": dict(getattr(app_state, "export_image_options", {}) or {}),
    }


def _restore_state(snapshot: dict[str, Any]) -> None:
    state_gateway.set_attrs(
        {
            "algorithm": snapshot["algorithm"],
            "selection_mode": snapshot["selection_mode"],
        }
    )
    state_gateway.set_render_mode(str(snapshot["render_mode"]))
    state_gateway.set_selected_indices(snapshot["selected_indices"])
    state_gateway.set_selected_2d_columns(snapshot["selected_2d_cols"], confirmed=snapshot["selected_2d_confirmed"])
    state_gateway.set_selected_3d_columns(snapshot["selected_3d_cols"], confirmed=snapshot["selected_3d_confirmed"])
    state_gateway.set_selected_ternary_columns(snapshot["selected_ternary_cols"], confirmed=snapshot["selected_ternary_confirmed"])
    state_gateway.sync_available_and_visible_groups(snapshot["available_groups"])
    state_gateway.set_visible_groups(snapshot["visible_groups"])
    state_gateway.set_export_image_options(**snapshot["export_image_options"])


def test_state_store_set_render_mode_syncs_algorithm() -> None:
    snapshot = _snapshot_state()
    try:
        state_gateway.set_render_mode("PCA")

        assert app_state.render_mode == "PCA"
        assert app_state.algorithm == "PCA"
        store_snapshot = app_state.state_store.snapshot()
        assert store_snapshot["render_mode"] == "PCA"
    finally:
        _restore_state(snapshot)


def test_state_store_selected_indices_mutations() -> None:
    snapshot = _snapshot_state()
    try:
        state_gateway.set_selected_indices({1, 2})
        state_gateway.add_selected_indices([2, 3])
        state_gateway.remove_selected_indices([1])

        assert app_state.selected_indices == {2, 3}
        assert app_state.state_store.snapshot()["selected_indices"] == {2, 3}

        state_gateway.clear_selected_indices()
        assert app_state.selected_indices == set()
    finally:
        _restore_state(snapshot)


def test_state_store_export_image_options_roundtrip() -> None:
    snapshot = _snapshot_state()
    try:
        state_gateway.set_export_image_options(
            preset_key="ieee_single",
            image_ext="SVG",
            dpi=50,
            bbox_tight=False,
            pad_inches=-1.0,
            transparent=True,
            point_size=12,
            legend_size=7,
        )
        options = state_gateway.get_export_image_options()

        assert options["preset_key"] == "ieee_single"
        assert options["image_ext"] == "svg"
        assert options["dpi"] == 72
        assert options["bbox_tight"] is False
        assert options["pad_inches"] == 0.0
        assert options["transparent"] is True
        assert options["point_size"] == 12
        assert options["legend_size"] == 7
        assert dict(app_state.export_image_options) == options
    finally:
        _restore_state(snapshot)


def test_state_store_column_selection_domains() -> None:
    snapshot = _snapshot_state()
    try:
        state_gateway.set_selected_2d_columns(["x", "y"], confirmed=True)
        state_gateway.set_selected_3d_columns(["x", "y", "z"], confirmed=True)
        state_gateway.set_selected_ternary_columns(["a", "b", "c"], confirmed=False)

        store_snapshot = app_state.state_store.snapshot()
        assert store_snapshot["selected_2d_cols"] == ["x", "y"]
        assert store_snapshot["selected_3d_cols"] == ["x", "y", "z"]
        assert store_snapshot["selected_ternary_cols"] == ["a", "b", "c"]
        assert store_snapshot["selected_2d_confirmed"] is True
        assert store_snapshot["selected_3d_confirmed"] is True
        assert store_snapshot["selected_ternary_confirmed"] is False

        state_gateway.reset_column_selection()
        assert app_state.selected_2d_cols == []
        assert app_state.selected_3d_cols == []
        assert app_state.selected_ternary_cols == []
        assert app_state.selected_2d_confirmed is False
        assert app_state.selected_3d_confirmed is False
        assert app_state.selected_ternary_confirmed is False
    finally:
        _restore_state(snapshot)


def test_state_store_available_visible_groups_sync() -> None:
    snapshot = _snapshot_state()
    try:
        state_gateway.sync_available_and_visible_groups(["A", "B", "C"])
        state_gateway.set_visible_groups(["A", "C"])
        assert app_state.visible_groups == ["A", "C"]

        state_gateway.sync_available_and_visible_groups(["B", "C"])
        assert app_state.available_groups == ["B", "C"]
        assert app_state.visible_groups == ["C"]

        state_gateway.set_visible_groups(None)
        assert app_state.visible_groups is None
    finally:
        _restore_state(snapshot)
