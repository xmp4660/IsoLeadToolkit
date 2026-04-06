"""Shared isochron helpers."""
import logging
import numpy as np
import pandas as pd

from core import app_state

logger = logging.getLogger(__name__)


def resolve_isochron_errors(
    df: pd.DataFrame,
    size: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Resolve sX, sY, rXY arrays from app_state settings."""
    mode = getattr(app_state, 'isochron_error_mode', 'fixed')

    if mode == 'columns':
        sx_col = getattr(app_state, 'isochron_sx_col', '')
        sy_col = getattr(app_state, 'isochron_sy_col', '')
        rxy_col = getattr(app_state, 'isochron_rxy_col', '')

        if sx_col in df.columns and sy_col in df.columns:
            sx = pd.to_numeric(df[sx_col], errors='coerce').to_numpy(dtype=float)
            sy = pd.to_numeric(df[sy_col], errors='coerce').to_numpy(dtype=float)
            if rxy_col and rxy_col in df.columns:
                rxy = pd.to_numeric(df[rxy_col], errors='coerce').to_numpy(dtype=float)
            else:
                rxy = np.zeros_like(sx, dtype=float)
            return sx, sy, rxy

        logger.warning("Isochron error columns not found; using fixed values.")

    sx_val = float(getattr(app_state, 'isochron_sx_value', 0.001))
    sy_val = float(getattr(app_state, 'isochron_sy_value', 0.001))
    rxy_val = float(getattr(app_state, 'isochron_rxy_value', 0.0))
    sx = np.full(size, sx_val, dtype=float)
    sy = np.full(size, sy_val, dtype=float)
    rxy = np.full(size, rxy_val, dtype=float)
    return sx, sy, rxy

