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
