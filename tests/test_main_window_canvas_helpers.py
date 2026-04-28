"""Tests for main window canvas/setup helper compatibility surface."""

from __future__ import annotations

import inspect

import pytest

pytest.importorskip("PyQt5")

from ui.main_window_parts.canvas import MainWindowCanvasMixin
from ui.main_window_parts.setup import MainWindowSetupMixin


def test_main_window_canvas_mixin_no_legacy_set_control_panel() -> None:
    assert not hasattr(MainWindowCanvasMixin, "set_control_panel")


def test_setup_ui_no_legacy_panel_splitter_layer() -> None:
    source = inspect.getsource(MainWindowSetupMixin._setup_ui)

    assert "self.panel_container =" not in source
    assert "self.panel_layout =" not in source
    assert "self.main_splitter =" not in source
