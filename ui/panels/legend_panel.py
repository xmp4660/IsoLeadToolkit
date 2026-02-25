"""图例面板 - 分组可见性、颜色、形状、图例位置管理"""
import logging

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QGridLayout, QListWidget, QListWidgetItem,
    QComboBox, QCheckBox, QSpinBox, QToolButton,
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QColor, QCursor

from core import translate, app_state
from utils.icons import build_marker_icon
from .base_panel import BasePanel

logger = logging.getLogger(__name__)


class LegendPanel(BasePanel):
    """图例标签页"""

    def reset_state(self):
        super().reset_state()
        self.group_list = None
        self.legend_checkboxes = {}
        self.legend_position_buttons = {}
        self.legend_position_group = None
        self.legend_columns_spin = None

    def build(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        refresh_btn = QPushButton(translate("Refresh Legend"))
        refresh_btn.setProperty('translate_key', 'Refresh Legend')
        refresh_btn.clicked.connect(self._update_group_list)
        layout.addWidget(refresh_btn)

        group_visibility_group = QGroupBox(translate("Group Visibility"))
        group_visibility_group.setProperty('translate_key', 'Group Visibility')
        group_layout = QVBoxLayout()

        self.group_list = QListWidget()
        self.group_list.setMaximumHeight(200)
        self.group_list.itemChanged.connect(self._on_group_visibility_change)
        group_layout.addWidget(self.group_list)

        btn_layout = QHBoxLayout()
        show_all_btn = QPushButton(translate("Show All"))
        show_all_btn.setProperty('translate_key', 'Show All')
        show_all_btn.clicked.connect(self._show_all_groups)
        btn_layout.addWidget(show_all_btn)

        hide_all_btn = QPushButton(translate("Hide All"))
        hide_all_btn.setProperty('translate_key', 'Hide All')
        hide_all_btn.clicked.connect(self._hide_all_groups)
        btn_layout.addWidget(hide_all_btn)

        group_layout.addLayout(btn_layout)
        group_visibility_group.setLayout(group_layout)
        layout.addWidget(group_visibility_group)

        position_group = QGroupBox(translate("Legend Position"))
        position_group.setProperty('translate_key', 'Legend Position')
        position_layout = QVBoxLayout()

        position_grid = QGridLayout()
        position_grid.setHorizontalSpacing(6)
        position_grid.setVerticalSpacing(6)

        outer_grid = QGridLayout()
        outer_grid.setHorizontalSpacing(6)
        outer_grid.setVerticalSpacing(6)

        self.legend_position_buttons = {}
        from PyQt5.QtWidgets import QButtonGroup
        self.legend_position_group = QButtonGroup(self)
        self.legend_position_group.setExclusive(True)

        grid_positions = [
            (0, 0, 'upper left', 'NW'),
            (0, 1, 'upper center', 'N'),
            (0, 2, 'upper right', 'NE'),
            (1, 0, 'center left', 'W'),
            (1, 1, 'center', 'C'),
            (1, 2, 'center right', 'E'),
            (2, 0, 'lower left', 'SW'),
            (2, 1, 'lower center', 'S'),
            (2, 2, 'lower right', 'SE'),
        ]

        for row, col, value, label in grid_positions:
            btn = QToolButton()
            btn.setText(label)
            btn.setCheckable(True)
            btn.setFixedSize(40, 32)
            btn.clicked.connect(lambda checked=False, loc=value: self._on_legend_position_change(loc))
            self.legend_position_group.addButton(btn)
            self.legend_position_buttons[value] = btn
            position_grid.addWidget(btn, row, col)

        for key, text, row, col, align in [
            ('outside_top', 'OUT T', 0, 1, Qt.AlignHCenter),
            ('outside_left', 'OUT L', 1, 0, Qt.AlignHCenter),
            ('outside_right', 'OUT R', 1, 2, Qt.AlignHCenter),
            ('outside_bottom', 'OUT B', 2, 1, Qt.AlignHCenter),
        ]:
            btn = QToolButton()
            btn.setText(text)
            btn.setCheckable(True)
            btn.setFixedSize(56, 32)
            btn.clicked.connect(lambda checked=False, loc=key: self._on_legend_position_change(loc))
            self.legend_position_group.addButton(btn)
            self.legend_position_buttons[key] = btn

        outer_grid.addWidget(self.legend_position_buttons['outside_top'], 0, 1, Qt.AlignHCenter)
        outer_grid.addWidget(self.legend_position_buttons['outside_left'], 1, 0, Qt.AlignHCenter)
        outer_grid.addLayout(position_grid, 1, 1)
        outer_grid.addWidget(self.legend_position_buttons['outside_right'], 1, 2, Qt.AlignHCenter)
        outer_grid.addWidget(self.legend_position_buttons['outside_bottom'], 2, 1, Qt.AlignHCenter)

        position_layout.addLayout(outer_grid)

        initial_location = getattr(app_state, 'legend_location', '') or getattr(app_state, 'legend_position', 'outside_left')
        for old, new in [('outside right', 'outside_right'), ('outside left', 'outside_left'),
                         ('outside top', 'outside_top'), ('outside bottom', 'outside_bottom')]:
            if initial_location == old:
                initial_location = new
        if initial_location not in self.legend_position_buttons:
            initial_location = 'outside_left'
        self._set_legend_position_button(initial_location)

        position_group.setLayout(position_layout)
        layout.addWidget(position_group)

        columns_group = QGroupBox(translate("Legend Columns"))
        columns_group.setProperty('translate_key', 'Legend Columns')
        columns_layout = QVBoxLayout()

        self.legend_columns_spin = QSpinBox()
        self.legend_columns_spin.setRange(1, 5)
        self.legend_columns_spin.setValue(app_state.legend_columns)
        self.legend_columns_spin.valueChanged.connect(self._on_legend_columns_change)
        columns_layout.addWidget(self.legend_columns_spin)

        columns_group.setLayout(columns_layout)
        layout.addWidget(columns_group)

        self._update_group_list()

        layout.addStretch()
        return widget

    # ------ 标记图标 ------

    def _ensure_marker_shape_map(self):
        if not hasattr(self, '_marker_shape_map'):
            self._marker_shape_map = {
                translate("Circle (o)"): 'o',
                translate("Square (s)"): 's',
                translate("Triangle Up (^)"): '^',
                translate("Triangle Down (v)"): 'v',
                translate("Diamond (D)"): 'D',
                translate("Pentagon (P)"): 'P',
                translate("Star (*)"): '*',
                translate("Plus (+)"): '+',
                translate("Cross (x)"): 'x',
                translate("X (X)"): 'X',
            }

    def _marker_label_for_value(self, marker_value):
        self._ensure_marker_shape_map()
        for label, value in self._marker_shape_map.items():
            if value == marker_value:
                return label
        return next(iter(self._marker_shape_map.keys()))

    def _build_marker_icon(self, color, marker, size=16):
        return build_marker_icon(color, marker, size)

    def _update_marker_swatch(self, group, swatch):
        color = app_state.current_palette.get(group, '#cccccc')
        marker = app_state.group_marker_map.get(group, getattr(app_state, 'plot_marker_shape', 'o'))
        icon = self._build_marker_icon(color, marker)
        swatch.setIcon(icon)
        swatch.setIconSize(QSize(16, 16))
        swatch.setStyleSheet("border: 1px solid #111827; border-radius: 3px; background: transparent;")

    # ------ 位置 ------

    def _set_legend_position_button(self, location):
        buttons = getattr(self, 'legend_position_buttons', {})
        if not buttons:
            return
        if location == 'outside right':
            location = 'outside_right'
        target = buttons.get(location)
        for value, btn in buttons.items():
            btn.blockSignals(True)
            btn.setChecked(btn is target)
            btn.blockSignals(False)

    # ------ 颜色/形状 ------

    def _pick_color(self, group, swatch):
        from PyQt5.QtWidgets import QColorDialog

        current_color = app_state.current_palette.get(group, '#cccccc')
        color = QColorDialog.getColor(QColor(current_color), self, f"Color for {group}")

        if color.isValid():
            new_hex = color.name()
            app_state.current_palette[group] = new_hex
            self._update_marker_swatch(group, swatch)

            if hasattr(app_state, 'group_to_scatter') and group in app_state.group_to_scatter:
                sc = app_state.group_to_scatter[group]
                try:
                    sc.set_color(new_hex)
                    sc.set_edgecolor("#1e293b")
                    if app_state.fig:
                        app_state.fig.canvas.draw_idle()
                except Exception as e:
                    logger.warning("Failed to update color for %s: %s", group, e)

    def _apply_marker_shape(self, group, shape_combo, swatch):
        self._ensure_marker_shape_map()
        label = shape_combo.currentText()
        marker = self._marker_shape_map.get(label, getattr(app_state, 'plot_marker_shape', 'o'))
        app_state.group_marker_map[group] = marker
        self._update_marker_swatch(group, swatch)
        self._on_change()

    # ------ 分组列表 ------

    def _update_group_list(self):
        if not hasattr(self, 'group_list') or self.group_list is None:
            return
        self.group_list.clear()
        self.legend_checkboxes = {}

        if not app_state.last_group_col or app_state.df_global is None:
            return

        groups = app_state.df_global[app_state.last_group_col].unique()
        self._ensure_marker_shape_map()
        visible = set(app_state.visible_groups) if app_state.visible_groups is not None else set(groups)

        max_items = 100
        groups_to_show = list(groups)[:max_items]

        if len(groups) > max_items:
            logger.warning("Showing first %d groups only.", max_items)

        for group in groups_to_show:
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(5, 2, 5, 2)
            item_layout.setSpacing(10)

            color = app_state.current_palette.get(group, '#cccccc')
            color_btn = QPushButton()
            color_btn.setFixedSize(24, 24)
            self._update_marker_swatch(group, color_btn)
            color_btn.setCursor(QCursor(Qt.PointingHandCursor))
            color_btn.clicked.connect(lambda checked=False, g=group, btn=color_btn: self._pick_color(g, btn))
            item_layout.addWidget(color_btn)

            checkbox = QCheckBox(str(group))
            is_visible = group in visible
            checkbox.setChecked(is_visible)
            checkbox.stateChanged.connect(lambda state, g=group: self._on_group_checkbox_change(g, state))
            item_layout.addWidget(checkbox, 1)
            self.legend_checkboxes[group] = checkbox

            shape_combo = QComboBox()
            shape_combo.setFixedWidth(120)
            for label in self._marker_shape_map.keys():
                shape_combo.addItem(label)
            current_marker = app_state.group_marker_map.get(group, getattr(app_state, 'plot_marker_shape', 'o'))
            current_label = self._marker_label_for_value(current_marker)
            shape_combo.setCurrentText(current_label)
            shape_combo.currentTextChanged.connect(lambda text, g=group, combo=shape_combo, btn=color_btn: self._apply_marker_shape(g, combo, btn))
            item_layout.addWidget(shape_combo)

            top_btn = QPushButton(translate("Top"))
            top_btn.setFixedWidth(50)
            top_btn.clicked.connect(lambda checked=False, g=group: self._bring_to_front(g))
            item_layout.addWidget(top_btn)

            item_widget.setLayout(item_layout)

            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            self.group_list.addItem(item)
            self.group_list.setItemWidget(item, item_widget)

    def _on_group_checkbox_change(self, group, state):
        if not app_state.last_group_col or app_state.df_global is None:
            return

        groups = list(app_state.available_groups or app_state.df_global[app_state.last_group_col].unique())
        if app_state.visible_groups is None:
            current_visible = set(groups)
        else:
            current_visible = set(app_state.visible_groups)

        if state == Qt.Checked:
            current_visible.add(group)
        else:
            current_visible.discard(group)

        if len(current_visible) == len(groups):
            app_state.visible_groups = None
        else:
            app_state.visible_groups = sorted(current_visible)

        self._on_change()

    def _on_group_visibility_change(self, item):
        group_name = item.text()
        is_checked = item.checkState() == Qt.Checked
        state = Qt.Checked if is_checked else Qt.Unchecked
        self._on_group_checkbox_change(group_name, state)

    def _show_all_groups(self):
        was_empty = app_state.visible_groups == []
        app_state.visible_groups = None
        self._update_group_list()
        self._on_change()
        if was_empty:
            QTimer.singleShot(0, self._autoscale_current_axes)

    def _hide_all_groups(self):
        if app_state.last_group_col and app_state.df_global is not None:
            app_state.visible_groups = []
            self._update_group_list()
            self._on_change()

    def _autoscale_current_axes(self):
        ax = getattr(app_state, 'ax', None)
        if ax is None:
            return
        try:
            ax.autoscale(enable=True, axis='both')
            ax.relim()
            ax.autoscale_view()
            if app_state.fig is not None and app_state.fig.canvas is not None:
                app_state.fig.canvas.draw_idle()
        except Exception:
            pass

    def sync_legend_ui(self):
        if not hasattr(self, 'legend_checkboxes'):
            return
        if app_state.last_group_col and app_state.df_global is not None:
            groups = list(app_state.available_groups or app_state.df_global[app_state.last_group_col].unique())
        else:
            groups = []

        if app_state.visible_groups is None:
            visible = set(groups)
        else:
            visible = set(app_state.visible_groups)

        for group, checkbox in self.legend_checkboxes.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(group in visible)
            checkbox.blockSignals(False)

    def _bring_to_front(self, group):
        if hasattr(app_state, 'group_to_scatter') and group in app_state.group_to_scatter:
            sc = app_state.group_to_scatter[group]
            try:
                max_z = 2
                if hasattr(app_state, 'scatter_collections'):
                    for c in app_state.scatter_collections:
                        max_z = max(max_z, c.get_zorder())

                sc.set_zorder(max_z + 1)
                if app_state.fig:
                    app_state.fig.canvas.draw_idle()
            except Exception as e:
                logger.warning("Failed to bring %s to front: %s", group, e)

    def _on_legend_position_change(self, position):
        if position == 'outside right':
            position = 'outside_right'
        app_state.legend_position = position
        app_state.legend_location = position
        self._set_legend_position_button(position)
        self._on_change()

    def _on_legend_columns_change(self, columns):
        app_state.legend_columns = columns
        self._on_change()
