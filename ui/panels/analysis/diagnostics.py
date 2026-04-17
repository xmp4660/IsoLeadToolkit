"""Analysis diagnostics actions mixin."""

import logging

logger = logging.getLogger(__name__)


class AnalysisPanelDiagnosticsMixin:
    """Diagnostics tools for analysis panel."""

    def _on_show_correlation_heatmap(self):
        """Show correlation heatmap."""
        try:
            from visualization.plotting.analysis_qt import show_correlation_heatmap

            show_correlation_heatmap(self)
        except Exception as error:
            logger.error("Failed to show correlation heatmap: %s", error)

    def _on_show_axis_correlation(self):
        """Show embedding axis correlation."""
        try:
            from visualization.plotting.analysis_qt import show_embedding_correlation

            show_embedding_correlation(self)
        except Exception as error:
            logger.error("Failed to show axis correlation: %s", error)

    def _on_show_shepard_diagram(self):
        """Show Shepard diagram."""
        try:
            from visualization.plotting.analysis_qt import show_shepard_diagram

            show_shepard_diagram(self)
        except Exception as error:
            logger.error("Failed to show Shepard diagram: %s", error)
