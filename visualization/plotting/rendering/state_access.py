"""Shared state access helpers for rendering modules."""
from __future__ import annotations

from .common.state_access import _active_subset_indices, _data_cols, _data_state, _df_global

__all__ = [
    '_active_subset_indices',
    '_data_cols',
    '_data_state',
    '_df_global',
]
