"""Build export DataFrame for selected samples."""

from __future__ import annotations

import logging
from typing import Iterable, Mapping, Sequence

import pandas as pd

logger = logging.getLogger(__name__)


def build_export_dataframe(
    *,
    selected_indices: Iterable[int],
    df_global: pd.DataFrame,
    algorithm: str | None,
    embedding: Sequence[Sequence[float]] | None,
    embedding_type: str | None,
    active_subset_indices: Iterable[int] | None,
    pca_component_indices: Sequence[int] | None,
    algorithm_params: Mapping[str, object] | None,
) -> pd.DataFrame:
    """Create export DataFrame and append embedding columns when available.

    Args:
        selected_indices: Selected row indices in the original dataset.
        df_global: Source dataset.
        algorithm: Current dimensionality-reduction algorithm.
        embedding: Last computed embedding values.
        embedding_type: Embedding display type.
        active_subset_indices: Dataset subset used when computing embedding.
        pca_component_indices: Selected PCA component indices.
        algorithm_params: Algorithm parameter map to be exported.

    Returns:
        DataFrame for exporting selected samples.
    """
    selected_list = list(selected_indices)
    selected_df = df_global.iloc[selected_list].copy()

    dr_algorithms = {"UMAP", "tSNE", "PCA", "RobustPCA"}
    if algorithm not in dr_algorithms or embedding is None or embedding_type is None:
        return selected_df

    if active_subset_indices is not None:
        data_indices = sorted(list(active_subset_indices))
    else:
        data_indices = list(range(len(df_global)))

    index_map = {orig: i for i, orig in enumerate(data_indices)}
    dim1: list[float | None] = []
    dim2: list[float | None] = []

    for idx in selected_list:
        mapped_idx = index_map.get(idx)
        if mapped_idx is None or mapped_idx >= len(embedding):
            dim1.append(None)
            dim2.append(None)
            continue

        row = embedding[mapped_idx]
        dim1.append(row[0] if len(row) > 0 else None)
        dim2.append(row[1] if len(row) > 1 else None)

    if embedding_type in ("PCA", "RobustPCA"):
        pca_idx = list(pca_component_indices or [0, 1])
        col1 = f"PC{pca_idx[0] + 1}"
        col2 = f"PC{pca_idx[1] + 1}" if len(pca_idx) > 1 else "PC2"
    else:
        col1 = f"{embedding_type} Dimension 1"
        col2 = f"{embedding_type} Dimension 2"

    selected_df[col1] = dim1
    selected_df[col2] = dim2

    for key, value in (algorithm_params or {}).items():
        selected_df[f"param_{key}"] = value

    return selected_df
