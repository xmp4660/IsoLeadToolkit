"""Embedding rendering subpackage."""

from .algorithm import compute_embedding, normalize_algorithm, resolve_embedding_params, resolve_target_dimensions
from .compute_geochem import compute_geochem_embedding, compute_v1v2_embedding
from .compute_ml import apply_precomputed_embedding, compute_ml_embedding
from .compute_ternary import compute_ternary_embedding
from .dataframe import prepare_plot_dataframe

__all__ = [
    'apply_precomputed_embedding',
    'compute_embedding',
    'compute_geochem_embedding',
    'compute_ml_embedding',
    'compute_ternary_embedding',
    'compute_v1v2_embedding',
    'normalize_algorithm',
    'prepare_plot_dataframe',
    'resolve_embedding_params',
    'resolve_target_dimensions',
]
