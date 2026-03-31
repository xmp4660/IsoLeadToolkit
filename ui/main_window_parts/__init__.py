"""Main window mixins."""

from .canvas import MainWindowCanvasMixin
from .legend import MainWindowLegendMixin
from .lifecycle import MainWindowLifecycleMixin
from .setup import MainWindowSetupMixin

__all__ = [
    "MainWindowSetupMixin",
    "MainWindowLegendMixin",
    "MainWindowCanvasMixin",
    "MainWindowLifecycleMixin",
]
