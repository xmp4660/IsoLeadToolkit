"""Legend panel mixin composition."""
from __future__ import annotations

from .actions import LegendActionsMixin
from .build import LegendBuildMixin
from .editors import LegendEditorsMixin


class LegendPanelMixin(LegendBuildMixin, LegendEditorsMixin, LegendActionsMixin):
    """图例标签页"""

