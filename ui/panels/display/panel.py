"""Display panel mixin composition."""

from .build import DisplayBuildMixin
from .helpers import DisplayControlHelperMixin
from .themes import DisplayThemeMixin


class DisplayPanelMixin(DisplayBuildMixin, DisplayThemeMixin, DisplayControlHelperMixin):
    """显示标签页"""

