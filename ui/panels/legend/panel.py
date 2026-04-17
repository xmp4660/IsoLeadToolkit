"""Legend panel mixin composition."""

from .actions import LegendActionsMixin
from .build import LegendBuildMixin
from .editors import LegendEditorsMixin


class LegendPanelMixin(LegendBuildMixin, LegendEditorsMixin, LegendActionsMixin):
    """图例标签页"""

