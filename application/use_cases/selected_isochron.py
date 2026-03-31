"""Application use case for selected-point Pb-Pb isochron calculation."""

from __future__ import annotations

from typing import Any, Callable, Sequence

import numpy as np
import pandas as pd


class SelectedIsochronUseCase:
    """Calculate selected-point isochron result payload."""

    def execute(
        self,
        *,
        df: pd.DataFrame | None,
        selected_indices: Sequence[int],
        render_mode: str,
        resolve_errors: Callable[[pd.DataFrame, int], tuple[np.ndarray, np.ndarray, np.ndarray]],
        york_regression: Callable[..., dict[str, Any]],
        calculate_age: Callable[[float, float, dict[str, Any]], tuple[float, float | None]],
        get_engine_parameters: Callable[[], dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Return isochron payload or None when calculation is not possible."""
        if not selected_indices or len(selected_indices) < 2:
            return None

        if render_mode != "PB_EVOL_76":
            return None

        x_col = "206Pb/204Pb"
        y_col = "207Pb/204Pb"
        if df is None or x_col not in df.columns or y_col not in df.columns:
            return None

        selected_list = list(selected_indices)
        df_selected = df.iloc[selected_list]

        x_data = pd.to_numeric(df_selected[x_col], errors="coerce").values
        y_data = pd.to_numeric(df_selected[y_col], errors="coerce").values
        sx_data, sy_data, rxy_data = resolve_errors(df_selected, len(x_data))

        valid = ~np.isnan(x_data) & ~np.isnan(y_data)
        valid = valid & np.isfinite(sx_data) & np.isfinite(sy_data) & np.isfinite(rxy_data)
        valid = valid & (sx_data > 0) & (sy_data > 0) & (np.abs(rxy_data) <= 1)

        x_data = x_data[valid]
        y_data = y_data[valid]
        sx_data = sx_data[valid]
        sy_data = sy_data[valid]
        rxy_data = rxy_data[valid]

        if len(x_data) < 2:
            return None

        fit = york_regression(x_data, sx_data, y_data, sy_data, rxy_data)
        slope = fit["b"]
        intercept = fit["a"]
        slope_err = fit["sb"]
        intercept_err = fit["sa"]
        mswd = fit["mswd"]
        p_value = fit["p_value"]

        y_pred = slope * x_data + intercept
        ss_res = np.sum((y_data - y_pred) ** 2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        params = get_engine_parameters()
        age_ma, age_err = calculate_age(slope, slope_err, params)

        x_min, x_max = np.min(x_data), np.max(x_data)
        span = x_max - x_min
        x_range = [x_min - span * 0.1, x_max + span * 0.1]
        y_range = [slope * x_range[0] + intercept, slope * x_range[1] + intercept]

        return {
            "slope": slope,
            "intercept": intercept,
            "slope_err": slope_err,
            "intercept_err": intercept_err,
            "age": age_ma,
            "age_err": age_err,
            "r_squared": r_squared,
            "mswd": mswd,
            "p_value": p_value,
            "n_points": len(x_data),
            "mode": "ISOCHRON1",
            "x_range": x_range,
            "y_range": y_range,
            "x_col": x_col,
            "y_col": y_col,
        }
