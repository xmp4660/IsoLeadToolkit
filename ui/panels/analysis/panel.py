"""Analysis panel mixin composition."""

from .build import AnalysisPanelBuildMixin
from .diagnostics import AnalysisPanelDiagnosticsMixin
from .equations import AnalysisPanelEquationMixin
from .mixing import AnalysisPanelMixingMixin
from .selection import AnalysisPanelSelectionMixin


class AnalysisPanelMixin(
    AnalysisPanelBuildMixin,
    AnalysisPanelDiagnosticsMixin,
    AnalysisPanelSelectionMixin,
    AnalysisPanelEquationMixin,
    AnalysisPanelMixingMixin,
):
    """Analysis tab mixin composed from focused mixins."""
