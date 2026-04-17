"""Tests for rendering KDE helper style resolution."""

from __future__ import annotations

from core import app_state
from visualization.plotting.rendering import kde as kde_helpers


def _snapshot_kde_state() -> dict[str, object]:
    return {
        "kde_style": dict(getattr(app_state, "kde_style", {}) or {}),
        "marginal_kde_style": dict(getattr(app_state, "marginal_kde_style", {}) or {}),
    }


def _restore_kde_state(snapshot: dict[str, object]) -> None:
    setattr(app_state, "kde_style", dict(snapshot.get("kde_style", {}) or {}))
    setattr(app_state, "marginal_kde_style", dict(snapshot.get("marginal_kde_style", {}) or {}))


def test_resolve_kde_style_builds_fallback_from_legacy_kde_style(monkeypatch) -> None:
    snapshot = _snapshot_kde_state()
    try:
        monkeypatch.setattr(kde_helpers, "ensure_line_style", lambda _state, _key, fallback: fallback)
        setattr(
            app_state,
            "kde_style",
            {"linewidth": 2.5, "alpha": 0.8, "fill": False, "levels": 7},
        )

        style = kde_helpers._resolve_kde_style("kde")

        assert style["linewidth"] == 2.5
        assert style["alpha"] == 0.8
        assert style["fill"] is False
        assert style["levels"] == 7
        assert style["linestyle"] == "-"
    finally:
        _restore_kde_state(snapshot)


def test_resolve_kde_style_builds_marginal_defaults(monkeypatch) -> None:
    snapshot = _snapshot_kde_state()
    try:
        monkeypatch.setattr(kde_helpers, "ensure_line_style", lambda _state, _key, fallback: fallback)
        setattr(app_state, "marginal_kde_style", {"linewidth": 1.2, "alpha": 0.15, "fill": True})

        style = kde_helpers._resolve_kde_style("marginal")

        assert style["linewidth"] == 1.2
        assert style["alpha"] == 0.15
        assert style["fill"] is True
        assert "levels" not in style
    finally:
        _restore_kde_state(snapshot)
