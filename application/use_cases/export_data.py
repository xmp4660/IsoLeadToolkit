"""Application use cases for tabular data export."""

from __future__ import annotations

import logging
from pathlib import Path
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


def export_dataframe_to_file(
    *,
    dataframe: pd.DataFrame,
    file_path: str,
    preferred_format: str | None = None,
) -> str:
    """Export DataFrame to CSV or Excel and return the normalized target path."""
    target = Path(file_path)
    normalized_preferred = str(preferred_format or "").strip().lower().lstrip(".")
    suffix = target.suffix.lower().lstrip(".")

    if suffix in {"xlsx", "xls"}:
        dataframe.to_excel(str(target), index=False)
        return str(target)

    if suffix == "csv":
        dataframe.to_csv(str(target), index=False)
        return str(target)

    if normalized_preferred in {"xlsx", "xls"}:
        target = target.with_suffix(".xlsx") if target.suffix else Path(f"{file_path}.xlsx")
        dataframe.to_excel(str(target), index=False)
        return str(target)

    target = target.with_suffix(".csv") if target.suffix else Path(f"{file_path}.csv")
    dataframe.to_csv(str(target), index=False)
    return str(target)


def export_selected_data_to_file(
    *,
    selected_indices: Iterable[int],
    df_global: pd.DataFrame,
    algorithm: str | None,
    embedding: Sequence[Sequence[float]] | None,
    embedding_type: str | None,
    active_subset_indices: Iterable[int] | None,
    pca_component_indices: Sequence[int] | None,
    algorithm_params: Mapping[str, object] | None,
    file_path: str,
    preferred_format: str | None = None,
) -> str:
    """Build and export selected data to target file."""
    export_df = build_export_dataframe(
        selected_indices=selected_indices,
        df_global=df_global,
        algorithm=algorithm,
        embedding=embedding,
        embedding_type=embedding_type,
        active_subset_indices=active_subset_indices,
        pca_component_indices=pca_component_indices,
        algorithm_params=algorithm_params,
    )
    return export_dataframe_to_file(
        dataframe=export_df,
        file_path=file_path,
        preferred_format=preferred_format,
    )


def append_selected_data_to_excel(
    *,
    selected_indices: Iterable[int],
    df_global: pd.DataFrame,
    algorithm: str | None,
    embedding: Sequence[Sequence[float]] | None,
    embedding_type: str | None,
    active_subset_indices: Iterable[int] | None,
    pca_component_indices: Sequence[int] | None,
    algorithm_params: Mapping[str, object] | None,
    file_path: str,
    sheet_name: str,
) -> str:
    """Append selected data to an Excel sheet and return normalized path."""
    export_df = build_export_dataframe(
        selected_indices=selected_indices,
        df_global=df_global,
        algorithm=algorithm,
        embedding=embedding,
        embedding_type=embedding_type,
        active_subset_indices=active_subset_indices,
        pca_component_indices=pca_component_indices,
        algorithm_params=algorithm_params,
    )

    target = Path(file_path)
    if target.suffix.lower().lstrip(".") not in {"xlsx", "xls"}:
        target = target.with_suffix(".xlsx") if target.suffix else Path(f"{file_path}.xlsx")

    # Ensures openpyxl is available and surfaces a clear dependency error to UI layer.
    import openpyxl  # noqa: F401

    if target.exists():
        with pd.ExcelWriter(str(target), engine="openpyxl", mode="a", if_sheet_exists="new") as writer:
            export_df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        export_df.to_excel(str(target), sheet_name=sheet_name, index=False)

    return str(target)
