"""
Data Loading and Processing
Handles Excel file loading and data validation
"""
from __future__ import annotations

import logging
import traceback

import pandas as pd

logger = logging.getLogger(__name__)


def read_data_frame(excel_file: str, sheet_name: str | None = None) -> pd.DataFrame:
    """Read data file into a cleaned DataFrame."""
    if sheet_name:
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=str, engine='calamine')
        except Exception:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=str)
    else:
        df = pd.read_csv(excel_file, dtype=str)

    df.columns = df.columns.astype(str).str.strip()

    for col in df.columns:
        numeric_col = pd.to_numeric(df[col], errors='coerce')
        non_null_count = numeric_col.notna().sum()
        total_count = len(numeric_col)

        if non_null_count > 0 and (non_null_count / total_count) > 0.5:
            df[col] = numeric_col
        else:
            df[col] = df[col].fillna("empty").astype(str)
            df[col] = df[col].replace(['nan', 'NaN', 'None'], 'empty')

    return df


def load_data(show_file_dialog: bool = True, show_config_dialog: bool = True) -> bool:
    """Compatibility wrapper delegated to application use case."""
    try:
        from application.use_cases import load_dataset

        return load_dataset(
            show_file_dialog=show_file_dialog,
            show_config_dialog=show_config_dialog,
        )
    except Exception as exc:
        logger.error("Data loading failed: %s", exc)
        traceback.print_exc()
        return False
