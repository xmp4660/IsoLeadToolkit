"""Tests for ui.app_parts.plotting helper methods."""

from __future__ import annotations

import logging


def test_setup_control_panel_clears_runtime_reference_only(monkeypatch) -> None:
    import core.state as state_pkg
    from ui.app_parts import plotting as plotting_module

    calls: list[object | None] = []

    monkeypatch.setattr(
        plotting_module.state_gateway,
        "set_control_panel_ref",
        lambda panel: calls.append(panel),
    )

    class _DummyApp(plotting_module.Qt5AppPlottingMixin):
        def __init__(self) -> None:
            self.control_panel = object()

    app = _DummyApp()

    missing = object()
    before_value = getattr(state_pkg, "control_panel", missing)

    app._setup_control_panel()

    after_value = getattr(state_pkg, "control_panel", missing)
    assert app.control_panel is None
    assert calls == [None]
    assert after_value is before_value


def test_setup_control_panel_without_legacy_attribute(monkeypatch) -> None:
    from ui.app_parts import plotting as plotting_module

    calls: list[object | None] = []

    monkeypatch.setattr(
        plotting_module.state_gateway,
        "set_control_panel_ref",
        lambda panel: calls.append(panel),
    )

    class _DummyApp(plotting_module.Qt5AppPlottingMixin):
        pass

    app = _DummyApp()
    assert not hasattr(app, "control_panel")

    app._setup_control_panel()

    assert calls == [None]
    assert not hasattr(app, "control_panel")


def test_print_instructions_matches_menu_dialog_mode(caplog) -> None:
    from ui.app_parts.plotting import Qt5AppPlottingMixin

    class _DummyApp(Qt5AppPlottingMixin):
        pass

    app = _DummyApp()

    with caplog.at_level(logging.INFO):
        app._print_instructions()

    text = "\n".join(record.getMessage() for record in caplog.records)
    assert "top-menu dialogs" in text
    assert "Control Panel window" not in text
