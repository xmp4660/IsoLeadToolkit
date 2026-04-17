"""Tests for visualization.plotting.styling.overlays helpers."""

from __future__ import annotations

from core import app_state
from visualization.plotting.styling.overlays import (
    refresh_overlay_styles,
    refresh_overlay_visibility,
)


class _DummyArtist:
    def __init__(self) -> None:
        self.color = None
        self.linewidth = None
        self.linestyle = None
        self.alpha = None
        self.visible = True

    def set_color(self, value):
        self.color = value

    def set_linewidth(self, value):
        self.linewidth = value

    def set_linestyle(self, value):
        self.linestyle = value

    def set_alpha(self, value):
        self.alpha = value

    def set_visible(self, value):
        self.visible = bool(value)


class _DummyCanvas:
    def __init__(self) -> None:
        self.draw_calls = 0

    def draw_idle(self) -> None:
        self.draw_calls += 1


class _DummyFigure:
    def __init__(self) -> None:
        self.canvas = _DummyCanvas()


def test_refresh_overlay_styles_updates_artist_properties(monkeypatch) -> None:
    fig = _DummyFigure()
    artist = _DummyArtist()

    monkeypatch.setattr(app_state, "fig", fig, raising=False)
    monkeypatch.setattr(app_state, "ax", object(), raising=False)
    monkeypatch.setattr(
        app_state,
        "overlay_artists",
        {"model_curves": {"group_a": [artist]}},
        raising=False,
    )
    monkeypatch.setattr(
        app_state,
        "line_styles",
        {
            "model_curve": {
                "color": "#112233",
                "linewidth": 2.5,
                "linestyle": "--",
                "alpha": 0.4,
            }
        },
        raising=False,
    )

    refresh_overlay_styles()

    assert artist.color == "#112233"
    assert artist.linewidth == 2.5
    assert artist.linestyle == "--"
    assert artist.alpha == 0.4
    assert fig.canvas.draw_calls == 1


def test_refresh_overlay_visibility_applies_toggle_and_group_visibility(monkeypatch) -> None:
    fig = _DummyFigure()
    model_artist = _DummyArtist()
    group_artist = _DummyArtist()
    label_artist = _DummyArtist()

    monkeypatch.setattr(app_state, "fig", fig, raising=False)
    monkeypatch.setattr(app_state, "ax", object(), raising=False)
    monkeypatch.setattr(
        app_state,
        "overlay_artists",
        {
            "model_curve": [model_artist],
            "plumbotectonics_curve:grp": [group_artist],
        },
        raising=False,
    )
    monkeypatch.setattr(app_state, "show_model_curves", False, raising=False)
    monkeypatch.setattr(app_state, "show_plumbotectonics_curves", True, raising=False)
    monkeypatch.setattr(
        app_state,
        "plumbotectonics_group_visibility",
        {"plumbotectonics_curve:grp": False},
        raising=False,
    )
    monkeypatch.setattr(
        app_state,
        "overlay_curve_label_data",
        [{"text": label_artist, "style_key": "model_curve"}],
        raising=False,
    )
    monkeypatch.setattr(app_state, "paleoisochron_label_data", [], raising=False)
    monkeypatch.setattr(app_state, "plumbotectonics_label_data", [], raising=False)
    monkeypatch.setattr(app_state, "plumbotectonics_isoage_label_data", [], raising=False)

    refresh_overlay_visibility()

    assert model_artist.visible is False
    assert group_artist.visible is False
    assert label_artist.visible is False
    assert fig.canvas.draw_calls == 1
