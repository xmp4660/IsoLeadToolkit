"""Application use case for tooltip text composition."""

from __future__ import annotations

from typing import Any, Iterable

import pandas as pd


class TooltipContentUseCase:
    """Compose user-facing tooltip text for hovered samples."""

    def build_text(
        self,
        *,
        row: Any,
        df_columns: Iterable[str],
        sample_idx: Any,
        tooltip_columns: list[str] | None,
        selected: bool,
        selected_status_label: str,
    ) -> str:
        """Create tooltip lines from configured columns with safe fallbacks."""
        lines: list[str] = []
        columns = list(df_columns)

        cols_to_show = tooltip_columns
        if cols_to_show is None:
            cols_to_show = ["Lab No.", "Discovery site", "Period"]

        if not cols_to_show:
            lines.append(f"ID: {sample_idx}")
        else:
            found_any = False
            for col in cols_to_show:
                if col not in columns:
                    continue
                val = row[col]
                val_str = str(val) if pd.notna(val) else "N/A"
                lines.append(f"{col}: {val_str}")
                found_any = True

            if not found_any:
                lines.append(f"ID: {sample_idx}")

        text = "\n".join(lines)
        if selected:
            text += "\n" + selected_status_label
        return text
