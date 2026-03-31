"""Unified data import dialog mixin composition."""

from .build import DataImportBuildMixin
from .submit import DataImportSubmitMixin
from .workflow import DataImportWorkflowMixin


class Qt5DataImportDialogMixin(
    DataImportBuildMixin,
    DataImportWorkflowMixin,
    DataImportSubmitMixin,
):
    """Unified dialog mixin for data import and configuration."""
