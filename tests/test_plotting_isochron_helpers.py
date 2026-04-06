"""Tests for visualization.plotting.isochron helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from core import app_state, state_gateway
from visualization.plotting.isochron import resolve_isochron_errors


def _snapshot_isochron_error_state() -> dict[str, object]:
    return {
        "mode": getattr(app_state, "isochron_error_mode", "fixed"),
        "sx_col": getattr(app_state, "isochron_sx_col", ""),
        "sy_col": getattr(app_state, "isochron_sy_col", ""),
        "rxy_col": getattr(app_state, "isochron_rxy_col", ""),
        "sx_value": getattr(app_state, "isochron_sx_value", 0.001),
        "sy_value": getattr(app_state, "isochron_sy_value", 0.001),
        "rxy_value": getattr(app_state, "isochron_rxy_value", 0.0),
    }


def _restore_isochron_error_state(snapshot: dict[str, object]) -> None:
    mode = str(snapshot.get("mode") or "fixed")
    if mode == "columns":
        state_gateway.set_isochron_error_columns(
            str(snapshot.get("sx_col") or ""),
            str(snapshot.get("sy_col") or ""),
            str(snapshot.get("rxy_col") or ""),
        )
        return
    state_gateway.set_isochron_error_fixed(
        float(snapshot.get("sx_value") or 0.001),
        float(snapshot.get("sy_value") or 0.001),
        float(snapshot.get("rxy_value") or 0.0),
    )


def test_resolve_isochron_errors_uses_columns_when_available() -> None:
    snapshot = _snapshot_isochron_error_state()
    try:
        state_gateway.set_isochron_error_columns("sx", "sy", "rxy")
        df = pd.DataFrame({"sx": [0.1, 0.2], "sy": [0.3, 0.4], "rxy": [0.5, 0.6]})

        sx, sy, rxy = resolve_isochron_errors(df, size=2)

        np.testing.assert_allclose(sx, np.array([0.1, 0.2], dtype=float), rtol=0.0, atol=1e-12)
        np.testing.assert_allclose(sy, np.array([0.3, 0.4], dtype=float), rtol=0.0, atol=1e-12)
        np.testing.assert_allclose(rxy, np.array([0.5, 0.6], dtype=float), rtol=0.0, atol=1e-12)
    finally:
        _restore_isochron_error_state(snapshot)


def test_resolve_isochron_errors_falls_back_to_fixed_when_columns_missing() -> None:
    snapshot = _snapshot_isochron_error_state()
    try:
        state_gateway.set_isochron_error_fixed(0.011, 0.022, 0.033)
        state_gateway.set_isochron_error_columns("missing_sx", "missing_sy", "missing_rxy")
        df = pd.DataFrame({"x": [1, 2, 3]})

        sx, sy, rxy = resolve_isochron_errors(df, size=3)

        np.testing.assert_allclose(sx, np.array([0.011, 0.011, 0.011], dtype=float), rtol=0.0, atol=1e-12)
        np.testing.assert_allclose(sy, np.array([0.022, 0.022, 0.022], dtype=float), rtol=0.0, atol=1e-12)
        np.testing.assert_allclose(rxy, np.array([0.033, 0.033, 0.033], dtype=float), rtol=0.0, atol=1e-12)
    finally:
        _restore_isochron_error_state(snapshot)
