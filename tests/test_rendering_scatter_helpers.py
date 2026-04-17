"""Tests for rendering common scatter helper."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from core import app_state
from visualization.plotting.rendering.common.scatter import _render_scatter_groups


def _snapshot_scatter_state() -> dict[str, object]:
    return {
        "fig": getattr(app_state, "fig", None),
        "ax": getattr(app_state, "ax", None),
        "scatter_collections": list(getattr(app_state, "scatter_collections", []) or []),
        "group_to_scatter": dict(getattr(app_state, "group_to_scatter", {}) or {}),
        "sample_index_map": dict(getattr(app_state, "sample_index_map", {}) or {}),
        "sample_coordinates": dict(getattr(app_state, "sample_coordinates", {}) or {}),
        "artist_to_sample": dict(getattr(app_state, "artist_to_sample", {}) or {}),
        "show_kde": getattr(app_state, "show_kde", False),
        "group_marker_map": dict(getattr(app_state, "group_marker_map", {}) or {}),
    }


def _restore_scatter_state(snapshot: dict[str, object]) -> None:
    setattr(app_state, "fig", snapshot.get("fig"))
    setattr(app_state, "ax", snapshot.get("ax"))
    setattr(app_state, "scatter_collections", list(snapshot.get("scatter_collections", []) or []))
    setattr(app_state, "group_to_scatter", dict(snapshot.get("group_to_scatter", {}) or {}))
    setattr(app_state, "sample_index_map", dict(snapshot.get("sample_index_map", {}) or {}))
    setattr(app_state, "sample_coordinates", dict(snapshot.get("sample_coordinates", {}) or {}))
    setattr(app_state, "artist_to_sample", dict(snapshot.get("artist_to_sample", {}) or {}))
    setattr(app_state, "show_kde", bool(snapshot.get("show_kde", False)))
    setattr(app_state, "group_marker_map", dict(snapshot.get("group_marker_map", {}) or {}))


def test_render_scatter_groups_2d_builds_point_mappings() -> None:
    snapshot = _snapshot_scatter_state()
    fig, ax = plt.subplots()
    try:
        setattr(app_state, "fig", fig)
        setattr(app_state, "ax", ax)
        setattr(app_state, "scatter_collections", [])
        setattr(app_state, "group_to_scatter", {})
        setattr(app_state, "sample_index_map", {})
        setattr(app_state, "sample_coordinates", {})
        setattr(app_state, "artist_to_sample", {})
        setattr(app_state, "show_kde", False)
        setattr(app_state, "group_marker_map", {})

        df_plot = pd.DataFrame(
            {
                "group": ["A", "A"],
                "_emb_x": [1.0, 2.0],
                "_emb_y": [3.0, 4.0],
            },
            index=[10, 11],
        )

        scatters = _render_scatter_groups(
            actual_algorithm="UMAP",
            df_plot=df_plot,
            group_col="group",
            unique_cats=["A"],
            size=30.0,
            palette={"A": "#ff0000"},
        )

        assert scatters is not None
        assert len(scatters) == 1
        assert len(getattr(app_state, "scatter_collections", [])) == 1
        assert "A" in getattr(app_state, "group_to_scatter", {})
        assert getattr(app_state, "sample_coordinates", {}).get(10) == (1.0, 3.0)
        assert getattr(app_state, "sample_coordinates", {}).get(11) == (2.0, 4.0)
        assert len(getattr(app_state, "artist_to_sample", {})) == 2
    finally:
        plt.close(fig)
        _restore_scatter_state(snapshot)
