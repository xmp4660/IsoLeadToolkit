"""Backward compatibility shim for merged plotting module."""
from .plotting import (
    get_embedding,
    plot_embedding,
    plot_umap,
    plot_2d_data,
    plot_3d_data,
)

__all__ = [
    'get_embedding',
    'plot_embedding',
    'plot_umap',
    'plot_2d_data',
    'plot_3d_data',
]
