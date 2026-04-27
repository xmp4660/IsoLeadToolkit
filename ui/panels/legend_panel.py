"""图例面板 - 颜色和形状设置"""
from __future__ import annotations

import logging

from .base_panel import BasePanel
from .legend import LegendPanelMixin

logger = logging.getLogger(__name__)


class LegendPanel(LegendPanelMixin, BasePanel):
    """图例标签页"""
