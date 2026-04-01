"""Embedding computation helpers for ML-based algorithms."""
from __future__ import annotations

from .embedding.compute_ml import apply_precomputed_embedding, compute_ml_embedding

__all__ = [
    'apply_precomputed_embedding',
    'compute_ml_embedding',
]
