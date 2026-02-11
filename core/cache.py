"""Embedding cache utilities."""
from __future__ import annotations

import json
from collections import OrderedDict
from typing import Any, Hashable, Iterable, Tuple


def _normalize_params(params: Any) -> str:
    try:
        return json.dumps(params, sort_keys=True, default=str)
    except Exception:
        return str(params)


def build_data_signature(app_state) -> Tuple[Any, ...]:
    df = getattr(app_state, 'df_global', None)
    shape = (len(df), len(df.columns)) if df is not None else (0, 0)
    file_path = getattr(app_state, 'file_path', '') or ''
    sheet_name = getattr(app_state, 'sheet_name', '') or ''
    data_cols = tuple(getattr(app_state, 'data_cols', []) or [])
    group_cols = tuple(getattr(app_state, 'group_cols', []) or [])
    data_version = getattr(app_state, 'data_version', 0)
    return (file_path, sheet_name, shape, data_cols, group_cols, data_version)


def build_embedding_cache_key(app_state, algorithm: str, params: Any, subset_key: Hashable) -> Tuple[Any, ...]:
    signature = build_data_signature(app_state)
    return (
        'embed',
        str(algorithm),
        _normalize_params(params),
        subset_key,
        signature,
    )


class EmbeddingCache:
    """Simple LRU cache for embeddings."""

    def __init__(self, max_entries: int = 8) -> None:
        self.max_entries = max_entries
        self._store: OrderedDict[Hashable, Any] = OrderedDict()

    def get(self, key: Hashable) -> Any:
        if key not in self._store:
            return None
        value = self._store.pop(key)
        self._store[key] = value
        return value

    def set(self, key: Hashable, value: Any) -> None:
        if key in self._store:
            self._store.pop(key)
        self._store[key] = value
        self._trim()

    def clear(self) -> None:
        self._store.clear()

    def _trim(self) -> None:
        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)

    def __len__(self) -> int:
        return len(self._store)

    def keys(self) -> Iterable[Hashable]:
        return list(self._store.keys())
