"""Ternary plot helpers."""
from __future__ import annotations

import logging
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy.stats import gmean

from core import app_state, state_gateway

logger = logging.getLogger(__name__)
_FULL_TERNARY_LIMITS = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
_VALID_LIMIT_MODES = {'min', 'max', 'both'}
_TERNARY_LIMIT_EPSILON = 1e-9
_TERNARY_FACTORS_FILL_VALUE = 1e-3
_TERNARY_FACTORS_MIN_VALUE = 1e-6


def _data_state() -> Any:
    return getattr(app_state, 'data', app_state)


def _df_global() -> Any:
    return getattr(_data_state(), 'df_global', app_state.df_global)


def _active_subset_indices() -> Any:
    return getattr(_data_state(), 'active_subset_indices', app_state.active_subset_indices)


def _apply_ternary_stretch(
    t_vals: Iterable[float],
    l_vals: Iterable[float],
    r_vals: Iterable[float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Apply ternary stretch transform based on current mode."""
    if not getattr(app_state, 'ternary_stretch', False):
        return t_vals, l_vals, r_vals

    factors = getattr(app_state, 'ternary_factors', [1.0, 1.0, 1.0])
    if not factors or len(factors) != 3:
        factors = [1.0, 1.0, 1.0]

    t_vals = np.asarray(t_vals, dtype=float) * float(factors[0])
    l_vals = np.asarray(l_vals, dtype=float) * float(factors[1])
    r_vals = np.asarray(r_vals, dtype=float) * float(factors[2])

    mode = getattr(app_state, 'ternary_stretch_mode', 'power')
    power = float(getattr(app_state, 'ternary_stretch_power', 0.5))

    def _minmax(vals: np.ndarray) -> np.ndarray:
        vmin = np.nanmin(vals)
        vmax = np.nanmax(vals)
        if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax == vmin:
            return vals
        return (vals - vmin) / (vmax - vmin)

    if mode in ('minmax', 'hybrid'):
        t_vals = _minmax(t_vals)
        l_vals = _minmax(l_vals)
        r_vals = _minmax(r_vals)

    if mode in ('power', 'hybrid'):
        t_vals = np.power(np.maximum(t_vals, 0), power)
        l_vals = np.power(np.maximum(l_vals, 0), power)
        r_vals = np.power(np.maximum(r_vals, 0), power)

    return t_vals, l_vals, r_vals


def _coerce_nonnegative(values: Iterable[float]) -> np.ndarray:
    """Convert values to finite, non-negative float arrays."""
    arr = np.asarray(values, dtype=float)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    return np.maximum(arr, 0.0)





def resolve_ternary_limit_mode(mode: Any = None) -> str:
    """Resolve ternary limit mode from explicit value or app state fallback."""
    candidate = mode
    if candidate is None:
        candidate = getattr(app_state, 'ternary_limit_mode', None)

    token = str(candidate).strip().lower() if candidate is not None else ''
    if token in _VALID_LIMIT_MODES:
        return token

    anchor = str(getattr(app_state, 'ternary_limit_anchor', 'min')).strip().lower()
    if anchor in ('min', 'max'):
        return anchor
    return 'min'


def _sanitize_limit_value(value: Any, default: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = float(default)
    return min(1.0, max(0.0, v))


def _resolve_manual_limits() -> tuple[float, float, float, float, float, float]:
    manual = getattr(app_state, 'ternary_manual_limits', {}) or {}

    tmin = _sanitize_limit_value(manual.get('tmin', 0.0), 0.0)
    tmax = _sanitize_limit_value(manual.get('tmax', 1.0), 1.0)
    lmin = _sanitize_limit_value(manual.get('lmin', 0.0), 0.0)
    lmax = _sanitize_limit_value(manual.get('lmax', 1.0), 1.0)
    rmin = _sanitize_limit_value(manual.get('rmin', 0.0), 0.0)
    rmax = _sanitize_limit_value(manual.get('rmax', 1.0), 1.0)

    if tmin > tmax:
        tmin, tmax = tmax, tmin
    if lmin > lmax:
        lmin, lmax = lmax, lmin
    if rmin > rmax:
        rmin, rmax = rmax, rmin

    return tmin, tmax, lmin, lmax, rmin, rmax


def normalize_ternary_components(
    t_vals: Iterable[float],
    l_vals: Iterable[float],
    r_vals: Iterable[float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Normalize ternary components so each triplet sums to 1."""
    t_arr = _coerce_nonnegative(t_vals)
    l_arr = _coerce_nonnegative(l_vals)
    r_arr = _coerce_nonnegative(r_vals)

    sums = t_arr + l_arr + r_arr
    valid = np.isfinite(sums) & (sums > 0)
    safe_sums = np.where(valid, sums, 1.0)

    t_norm = t_arr / safe_sums
    l_norm = l_arr / safe_sums
    r_norm = r_arr / safe_sums

    if np.any(~valid):
        t_norm[~valid] = 1.0 / 3.0
        l_norm[~valid] = 1.0 / 3.0
        r_norm[~valid] = 1.0 / 3.0

    return t_norm, l_norm, r_norm


def prepare_ternary_components(
    t_vals: Iterable[float],
    l_vals: Iterable[float],
    r_vals: Iterable[float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Normalize ternary components by sum only (no stretch)."""
    return normalize_ternary_components(t_vals, l_vals, r_vals)





def infer_ternary_limits(
    t_vals: Iterable[float],
    l_vals: Iterable[float],
    r_vals: Iterable[float],
) -> tuple[float, float, float, float, float, float]:
    """Infer ternary data limits from component ranges."""
    t_arr, l_arr, r_arr = normalize_ternary_components(t_vals, l_vals, r_vals)
    if t_arr.size == 0 or l_arr.size == 0 or r_arr.size == 0:
        return _FULL_TERNARY_LIMITS

    tmin = float(np.nanmin(t_arr))
    tmax = float(np.nanmax(t_arr))
    lmin = float(np.nanmin(l_arr))
    lmax = float(np.nanmax(l_arr))
    rmin = float(np.nanmin(r_arr))
    rmax = float(np.nanmax(r_arr))

    return tmin, tmax, lmin, lmax, rmin, rmax











def configure_ternary_axis(
    ax: Any,
    t_vals: Iterable[float],
    l_vals: Iterable[float],
    r_vals: Iterable[float],
    labels: tuple[str, str, str] | list[str] | None = None,
    *,
    auto_zoom: bool = True,
) -> tuple[float, float, float, float, float, float]:
    """Configure mpltern axis labels and limits using mpltern API."""
    if labels and len(labels) == 3:
        try:
            ax.set_tlabel(str(labels[0]))
            ax.set_llabel(str(labels[1]))
            ax.set_rlabel(str(labels[2]))
        except Exception:
            logger.debug("Failed to set ternary axis labels", exc_info=True)

    mode = resolve_ternary_limit_mode(getattr(app_state, 'ternary_limit_mode', None))
    state_gateway.set_ternary_limit_mode(mode)

    tmin, tmax, lmin, lmax, rmin, rmax = _FULL_TERNARY_LIMITS
    
    try:
        if auto_zoom:
            use_manual = bool(getattr(app_state, 'ternary_manual_limits_enabled', False))
            if use_manual:
                tmin, tmax, lmin, lmax, rmin, rmax = _resolve_manual_limits()
            else:
                tmin, tmax, lmin, lmax, rmin, rmax = infer_ternary_limits(t_vals, l_vals, r_vals)

        # Apply via mpltern API based on mode
        if mode == 'max':
            ax.set_ternary_max(tmax, lmax, rmax)
        elif mode == 'min':
            ax.set_ternary_min(tmin, lmin, rmin)
        else:  # 'both' or default
            ax.set_ternary_lim(tmin, tmax, lmin, lmax, rmin, rmax)
    except Exception as e:
        logger.warning("Failed to configure ternary limits: %s", e)
        ax.set_ternary_lim(*_FULL_TERNARY_LIMITS)
        tmin, tmax, lmin, lmax, rmin, rmax = _FULL_TERNARY_LIMITS

    try:
        ax.set_aspect('equal', adjustable='box')
    except Exception:
        logger.debug("Failed to set equal aspect on ternary axis", exc_info=True)

    return tmin, tmax, lmin, lmax, rmin, rmax


def calculate_auto_ternary_factors() -> bool:
    """Calculate optimal scaling factors for the ternary plot using geometric means.

    This effectively centers the data in the ternary diagram (compositional centering).
    """
    try:
        if not hasattr(app_state, 'selected_ternary_cols') or len(app_state.selected_ternary_cols) != 3:
            logger.warning("Factors calc: invalid col selection")
            return False

        cols = app_state.selected_ternary_cols
        df_global = _df_global()
        if df_global is None:
            logger.warning("Factors calc: no source dataframe available")
            return False

        subset_indices = _active_subset_indices()
        if subset_indices is not None:
            df = df_global.iloc[subset_indices].copy()
        else:
            df = df_global.copy()

        data = df[cols].apply(pd.to_numeric, errors='coerce').fillna(_TERNARY_FACTORS_FILL_VALUE).values
        data = np.maximum(data, _TERNARY_FACTORS_MIN_VALUE)

        gmeans = gmean(data, axis=0)

        factors = 1.0 / gmeans
        min_f = np.min(factors)
        if min_f > 0:
            factors = factors / min_f

        factors_list = factors.tolist()
        state_gateway.set_ternary_factors(factors_list)
        logger.info("Auto-Calculated Factors: %s", factors_list)
        return True

    except Exception as e:
        logger.error("Auto factor calculation failed: %s", e)
        return False


