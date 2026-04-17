"""数据面板 - 分组与投影设置"""

import logging

from .base_panel import BasePanel
from .data import (
    DataPanelBuildMixin,
    DataPanelGeochemMixin,
    DataPanelGroupingMixin,
    DataPanelProjectionMixin,
)

logger = logging.getLogger(__name__)


class DataPanel(
    DataPanelBuildMixin,
    DataPanelProjectionMixin,
    DataPanelGeochemMixin,
    DataPanelGroupingMixin,
    BasePanel,
):
    """数据标签页"""
