"""StateStore for managed AppState domains."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


class StateStore:
    """Manage selected AppState domains through action dispatch."""

    DEFAULT_EXPORT_IMAGE_OPTIONS = {
        "preset_key": "science_single",
        "image_ext": "png",
        "dpi": 400,
        "bbox_tight": True,
        "pad_inches": 0.02,
        "transparent": False,
        "point_size": None,
        "legend_size": None,
    }

    def __init__(self, state: Any) -> None:
        self._state = state
        self._snapshot: dict[str, Any] = {
            "render_mode": str(getattr(state, "render_mode", "UMAP")),
            "selected_indices": set(getattr(state, "selected_indices", set()) or set()),
            "available_groups": list(getattr(state, "available_groups", []) or []),
            "visible_groups": self._normalize_visible_groups(getattr(state, "visible_groups", None)),
            "selected_2d_cols": list(getattr(state, "selected_2d_cols", []) or []),
            "selected_3d_cols": list(getattr(state, "selected_3d_cols", []) or []),
            "selected_ternary_cols": list(getattr(state, "selected_ternary_cols", []) or []),
            "selected_2d_confirmed": bool(getattr(state, "selected_2d_confirmed", False)),
            "selected_3d_confirmed": bool(getattr(state, "selected_3d_confirmed", False)),
            "selected_ternary_confirmed": bool(getattr(state, "selected_ternary_confirmed", False)),
            "export_image_options": self._normalize_export_options(
                getattr(state, "export_image_options", None)
            ),
        }
        self._sync_state()

    def dispatch(self, action: dict[str, Any]) -> dict[str, Any]:
        """Dispatch an action and return a snapshot copy."""
        action_type = str(action.get("type", "")).upper().strip()

        if action_type == "SET_RENDER_MODE":
            render_mode = str(action.get("render_mode", "UMAP") or "UMAP")
            self._snapshot["render_mode"] = render_mode

        elif action_type == "SET_SELECTED_INDICES":
            indices = self._to_index_set(action.get("indices", []))
            self._snapshot["selected_indices"] = indices

        elif action_type == "ADD_SELECTED_INDICES":
            indices = self._to_index_set(action.get("indices", []))
            self._snapshot["selected_indices"].update(indices)

        elif action_type == "REMOVE_SELECTED_INDICES":
            indices = self._to_index_set(action.get("indices", []))
            for index in indices:
                self._snapshot["selected_indices"].discard(index)

        elif action_type == "CLEAR_SELECTED_INDICES":
            self._snapshot["selected_indices"].clear()

        elif action_type == "SET_SELECTED_2D_COLUMNS":
            self._snapshot["selected_2d_cols"] = list(action.get("columns") or [])
            self._snapshot["selected_2d_confirmed"] = bool(action.get("confirmed", False))

        elif action_type == "SET_SELECTED_3D_COLUMNS":
            self._snapshot["selected_3d_cols"] = list(action.get("columns") or [])
            self._snapshot["selected_3d_confirmed"] = bool(action.get("confirmed", False))

        elif action_type == "SET_SELECTED_TERNARY_COLUMNS":
            self._snapshot["selected_ternary_cols"] = list(action.get("columns") or [])
            self._snapshot["selected_ternary_confirmed"] = bool(action.get("confirmed", False))

        elif action_type == "RESET_COLUMN_SELECTION":
            self._snapshot["selected_2d_cols"] = []
            self._snapshot["selected_3d_cols"] = []
            self._snapshot["selected_ternary_cols"] = []
            self._snapshot["selected_2d_confirmed"] = False
            self._snapshot["selected_3d_confirmed"] = False
            self._snapshot["selected_ternary_confirmed"] = False
            self._snapshot["available_groups"] = []
            self._snapshot["visible_groups"] = None

        elif action_type == "SYNC_AVAILABLE_VISIBLE_GROUPS":
            groups = [str(group) for group in list(action.get("all_groups") or [])]
            self._snapshot["available_groups"] = groups
            visible_groups = self._snapshot["visible_groups"]
            if visible_groups:
                filtered = [group for group in visible_groups if group in groups]
                self._snapshot["visible_groups"] = filtered if filtered else None

        elif action_type == "SET_VISIBLE_GROUPS":
            self._snapshot["visible_groups"] = self._normalize_visible_groups(action.get("groups"))

        elif action_type == "SET_EXPORT_IMAGE_OPTIONS":
            merged = dict(self._snapshot["export_image_options"])
            payload = dict(action.get("options") or {})
            for key, value in payload.items():
                if value is not None:
                    merged[key] = value
            self._snapshot["export_image_options"] = self._normalize_export_options(merged)

        self._sync_state()
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        """Return shallow-copied tracked domains."""
        return {
            "render_mode": str(self._snapshot["render_mode"]),
            "selected_indices": set(self._snapshot["selected_indices"]),
            "available_groups": list(self._snapshot["available_groups"]),
            "visible_groups": self._normalize_visible_groups(self._snapshot["visible_groups"]),
            "selected_2d_cols": list(self._snapshot["selected_2d_cols"]),
            "selected_3d_cols": list(self._snapshot["selected_3d_cols"]),
            "selected_ternary_cols": list(self._snapshot["selected_ternary_cols"]),
            "selected_2d_confirmed": bool(self._snapshot["selected_2d_confirmed"]),
            "selected_3d_confirmed": bool(self._snapshot["selected_3d_confirmed"]),
            "selected_ternary_confirmed": bool(self._snapshot["selected_ternary_confirmed"]),
            "export_image_options": dict(self._snapshot["export_image_options"]),
        }

    def _sync_state(self) -> None:
        render_mode = str(self._snapshot["render_mode"])
        self._state.render_mode = render_mode
        if render_mode in ("UMAP", "tSNE", "PCA", "RobustPCA"):
            self._state.algorithm = render_mode

        self._state.selected_indices = set(self._snapshot["selected_indices"])
        self._state.available_groups = list(self._snapshot["available_groups"])
        self._state.visible_groups = self._normalize_visible_groups(self._snapshot["visible_groups"])
        self._state.selected_2d_cols = list(self._snapshot["selected_2d_cols"])
        self._state.selected_3d_cols = list(self._snapshot["selected_3d_cols"])
        self._state.selected_ternary_cols = list(self._snapshot["selected_ternary_cols"])
        self._state.selected_2d_confirmed = bool(self._snapshot["selected_2d_confirmed"])
        self._state.selected_3d_confirmed = bool(self._snapshot["selected_3d_confirmed"])
        self._state.selected_ternary_confirmed = bool(self._snapshot["selected_ternary_confirmed"])
        self._state.export_image_options = dict(self._snapshot["export_image_options"])

    @classmethod
    def _normalize_export_options(cls, options: Any) -> dict[str, Any]:
        merged = dict(cls.DEFAULT_EXPORT_IMAGE_OPTIONS)
        if isinstance(options, dict):
            merged.update(options)

        merged["preset_key"] = str(merged.get("preset_key") or "science_single")
        merged["image_ext"] = str(merged.get("image_ext") or "png").lower().strip(".")
        merged["dpi"] = max(72, int(merged.get("dpi", 400)))
        merged["bbox_tight"] = bool(merged.get("bbox_tight", True))
        merged["pad_inches"] = max(0.0, float(merged.get("pad_inches", 0.02)))
        merged["transparent"] = bool(merged.get("transparent", False))

        point_size = merged.get("point_size")
        legend_size = merged.get("legend_size")
        merged["point_size"] = int(point_size) if point_size is not None else None
        merged["legend_size"] = int(legend_size) if legend_size is not None else None
        return merged

    @staticmethod
    def _to_index_set(indices: Any) -> set[int]:
        if indices is None:
            return set()
        if isinstance(indices, set):
            return {int(v) for v in indices}
        if isinstance(indices, Iterable) and not isinstance(indices, (str, bytes)):
            return {int(v) for v in indices}
        return {int(indices)}

    @staticmethod
    def _normalize_visible_groups(groups: Any) -> list[str] | None:
        if groups is None:
            return None
        if isinstance(groups, Iterable) and not isinstance(groups, (str, bytes)):
            out = [str(group) for group in groups]
            return out if out else None
        return [str(groups)]
