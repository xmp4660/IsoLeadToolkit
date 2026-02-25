"""标记图标渲染工具。

提供统一的 matplotlib 标记形状到 QIcon 的渲染。
"""
from __future__ import annotations

import logging
import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF

logger = logging.getLogger(__name__)

# 填充型标记集合
_FILLED_MARKERS = {'o', 's', '^', 'v', 'D', 'P', '*'}


def build_marker_icon(color: str, marker: str, size: int = 16) -> QIcon:
    """渲染标记图标。

    Args:
        color: 填充颜色 (hex 字符串)。
        marker: matplotlib 标记符号。
        size: 图标像素尺寸。

    Returns:
        渲染后的 QIcon。
    """
    try:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(QColor('#111827'))
        pen.setWidthF(1.0)
        painter.setPen(pen)

        brush = QBrush(QColor(color))
        painter.setBrush(brush if marker in _FILLED_MARKERS else Qt.NoBrush)

        cx = size / 2.0
        cy = size / 2.0
        r = size * 0.35

        _draw_marker_shape(painter, marker, cx, cy, r)

        painter.end()
        return QIcon(pixmap)
    except Exception:
        logger.debug("Marker icon fallback for marker=%s", marker)
        fallback = QPixmap(size, size)
        fallback.fill(QColor(color))
        return QIcon(fallback)


def _draw_marker_shape(
    painter: QPainter, marker: str, cx: float, cy: float, r: float
) -> None:
    """绘制标记形状到 painter。"""
    if marker == 'o':
        painter.drawEllipse(QPointF(cx, cy), r, r)
    elif marker == 's':
        painter.drawRect(QRectF(cx - r, cy - r, r * 2, r * 2))
    elif marker == '^':
        points = [QPointF(cx, cy - r), QPointF(cx - r, cy + r), QPointF(cx + r, cy + r)]
        painter.drawPolygon(QPolygonF(points))
    elif marker == 'v':
        points = [QPointF(cx - r, cy - r), QPointF(cx + r, cy - r), QPointF(cx, cy + r)]
        painter.drawPolygon(QPolygonF(points))
    elif marker == 'D':
        points = [QPointF(cx, cy - r), QPointF(cx + r, cy), QPointF(cx, cy + r), QPointF(cx - r, cy)]
        painter.drawPolygon(QPolygonF(points))
    elif marker == 'P':
        points = []
        for i in range(5):
            angle = (math.pi / 2.0) + (i * 2.0 * math.pi / 5.0)
            points.append(QPointF(cx + r * math.cos(angle), cy - r * math.sin(angle)))
        painter.drawPolygon(QPolygonF(points))
    elif marker == '*':
        points = []
        outer = r
        inner = r * 0.5
        for i in range(10):
            angle = (math.pi / 2.0) + (i * math.pi / 5.0)
            radius = outer if i % 2 == 0 else inner
            points.append(QPointF(cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
        painter.drawPolygon(QPolygonF(points))
    elif marker in {'+', 'x', 'X'}:
        if marker == '+':
            painter.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))
            painter.drawLine(QPointF(cx, cy - r), QPointF(cx, cy + r))
        else:
            painter.drawLine(QPointF(cx - r, cy - r), QPointF(cx + r, cy + r))
            painter.drawLine(QPointF(cx - r, cy + r), QPointF(cx + r, cy - r))
    else:
        painter.drawEllipse(QPointF(cx, cy), r, r)
