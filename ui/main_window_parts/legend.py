"""Legend interaction and rendering mixin for main window."""

import logging
import os

from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QColor, QCursor
from PyQt5.QtWidgets import (
    QAction,
    QCheckBox,
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from core import app_state, state_gateway, translate
from ui.icons import apply_color_swatch, build_marker_icon
from visualization.line_styles import resolve_line_style
from visualization.plotting.legend_model import OVERLAY_TOGGLE_MAP, normalize_render_mode, overlay_legend_items

logger = logging.getLogger(__name__)
QT_DEBUG_MODE = os.environ.get("ISOTOPES_QT_DEBUG", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


class MainWindowLegendMixin:
    """Legend panel behavior for main window."""

    def _build_marker_icon(self, color, marker, size=14):
        return build_marker_icon(color, marker, size)

    def _ensure_marker_shape_map(self):
        if not hasattr(self, "_marker_shape_map"):
            self._marker_shape_map = {
                translate("Point (.)"): ".",
                translate("Pixel (,)"): ",",
                translate("Circle (o)"): "o",
                translate("Triangle Down (v)"): "v",
                translate("Triangle Up (^)"): "^",
                translate("Triangle Left (<)"): "<",
                translate("Triangle Right (>)"): ">",
                translate("Tri Down (1)"): "1",
                translate("Tri Up (2)"): "2",
                translate("Tri Left (3)"): "3",
                translate("Tri Right (4)"): "4",
                translate("Octagon (8)"): "8",
                translate("Square (s)"): "s",
                translate("Pentagon (p)"): "p",
                translate("Plus Filled (P)"): "P",
                translate("Star (*)"): "*",
                translate("Hexagon 1 (h)"): "h",
                translate("Hexagon 2 (H)"): "H",
                translate("Diamond (D)"): "D",
                translate("Plus (+)"): "+",
                translate("Cross (x)"): "x",
                translate("X (X)"): "X",
                translate("Thin Diamond (d)"): "d",
                translate("Vline (|)"): "|",
                translate("Hline (_)"): "_",
            }

    def _overlay_entries_for_legend(self):
        mode = normalize_render_mode(getattr(app_state, "render_mode", ""))
        return list(overlay_legend_items(render_mode=mode, include_disabled=True))

    def _is_plumbotectonics_group_style(self, style_key):
        return isinstance(style_key, str) and style_key.startswith("plumbotectonics_curve:")

    def _legend_order_key(self, entry_type, key):
        return f"{entry_type}:{key}"

    def _set_legend_item_meta(self, item, entry_type, key):
        if item is None:
            return
        item.setData(Qt.UserRole, {"type": entry_type, "key": key})

    def _overlay_artists_for_style(self, style_key, overlay_map=None):
        if overlay_map is None:
            overlay_map = getattr(app_state, "overlay_artists", {}) or {}
        artists = []

        def _extend_artists(value):
            if value is None:
                return
            if isinstance(value, dict):
                for nested in value.values():
                    _extend_artists(nested)
                return
            if isinstance(value, (list, tuple, set)):
                for artist in value:
                    if artist is not None:
                        artists.append(artist)
                return
            artists.append(value)

        _extend_artists(overlay_map.get(style_key))

        style_to_category = {
            "model_curve": "model_curves",
            "plumbotectonics_curve": "plumbotectonics_curves",
            "paleoisochron": "paleoisochrons",
            "model_age_line": "model_age_lines",
            "isochron": "isochrons",
            "growth_curve": "growth_curves",
        }
        category_key = style_to_category.get(style_key)
        if category_key:
            _extend_artists(overlay_map.get(category_key))

        if style_key == "isochron":
            _extend_artists(overlay_map.get("selected_isochron"))

        def _extend_text_artists(entries):
            for entry in entries or []:
                if not isinstance(entry, dict):
                    continue
                if entry.get("style_key") != style_key:
                    continue
                text_artist = entry.get("text")
                if text_artist is not None:
                    artists.append(text_artist)

        _extend_text_artists(getattr(app_state, "overlay_curve_label_data", []))
        if style_key == "paleoisochron":
            _extend_text_artists(getattr(app_state, "paleoisochron_label_data", []))
            _extend_text_artists(getattr(app_state, "plumbotectonics_isoage_label_data", []))
            _extend_text_artists(getattr(app_state, "plumbotectonics_label_data", []))

        if not artists:
            return []

        unique = []
        seen = set()
        for artist in artists:
            aid = id(artist)
            if aid in seen:
                continue
            seen.add(aid)
            unique.append(artist)
        return unique

    def _apply_legend_z_order(self):
        if not hasattr(self, "_legend_list") or self._legend_list is None:
            return
        ax = getattr(app_state, "ax", None)
        if ax is None:
            return

        order = []
        for i in range(self._legend_list.count()):
            item = self._legend_list.item(i)
            meta = item.data(Qt.UserRole)
            if not meta:
                continue
            entry_type = meta.get("type")
            entry_key = meta.get("key")
            if entry_type and entry_key is not None:
                order.append((entry_type, entry_key))

        if not order:
            return

        max_z = 2
        try:
            for artist in ax.get_children():
                try:
                    max_z = max(max_z, artist.get_zorder())
                except Exception:
                    continue
        except Exception:
            pass

        target_z = max_z + len(order)
        overlay_map = getattr(app_state, "overlay_artists", {}) or {}
        group_map = getattr(app_state, "group_to_scatter", {}) or {}

        for entry_type, entry_key in order:
            if entry_type == "group":
                artist = group_map.get(entry_key)
                if artist is not None:
                    try:
                        artist.set_zorder(target_z)
                    except Exception:
                        pass
            elif entry_type == "overlay":
                for artist in self._overlay_artists_for_style(entry_key, overlay_map=overlay_map):
                    try:
                        z_value = target_z + 0.25 if hasattr(artist, "get_text") else target_z
                        artist.set_zorder(z_value)
                    except Exception:
                        pass
            target_z -= 1

        state_gateway.set_attr(
            "legend_item_order",
            [
                self._legend_order_key(entry_type, entry_key)
                for entry_type, entry_key in order
            ],
        )

        if app_state.fig is not None and app_state.fig.canvas is not None:
            app_state.fig.canvas.draw_idle()

    def _on_legend_rows_moved(self, *args):
        QTimer.singleShot(0, self._rebuild_legend_after_reorder)

    def _rebuild_legend_after_reorder(self):
        self._apply_legend_z_order()
        title = getattr(app_state, "legend_last_title", None)
        handles = getattr(app_state, "legend_last_handles", None)
        labels = getattr(app_state, "legend_last_labels", None)
        if not title or handles is None or labels is None:
            return
        self._update_legend_panel(title, handles, labels)

    def _move_legend_item_to_top(self, entry_type, entry_key):
        if not hasattr(self, "_legend_list") or self._legend_list is None:
            return
        if QT_DEBUG_MODE:
            logger.debug("Move legend item to top: type=%s key=%s", entry_type, entry_key)
        order = []
        target = (entry_type, entry_key)
        for i in range(self._legend_list.count()):
            item = self._legend_list.item(i)
            meta = item.data(Qt.UserRole)
            if not meta:
                continue
            current_type = meta.get("type")
            current_key = meta.get("key")
            if current_type and current_key is not None:
                order.append((current_type, current_key))

        if not order:
            return
        if order[0] == target or target not in order:
            return

        new_order = [target] + [entry for entry in order if entry != target]
        state_gateway.set_attr(
            "legend_item_order",
            [
                self._legend_order_key(current_type, current_key)
                for current_type, current_key in new_order
            ],
        )

        title = getattr(app_state, "legend_last_title", None)
        handles = getattr(app_state, "legend_last_handles", None)
        labels = getattr(app_state, "legend_last_labels", None)
        if title and handles is not None and labels is not None:
            self._update_legend_panel(title, handles, labels)
        else:
            self._apply_legend_z_order()

    def _open_line_style_dialog(self, style_key, swatch):
        from ui.dialogs.line_style_dialog import open_line_style_dialog

        open_line_style_dialog(self, style_key, swatch=swatch, on_applied=self._refresh_plot)

    def _add_overlay_legend_item(self, label_key, style_key, default_color=None, fallback=None):
        item_widget = QWidget()
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(4, 2, 4, 2)
        item_layout.setSpacing(6)

        style = getattr(app_state, "line_styles", {}).get(style_key, {}) or {}
        swatch_color = style.get("color")
        if not swatch_color and fallback:
            resolved = resolve_line_style(app_state, style_key, fallback)
            swatch_color = resolved.get("color")
        if not swatch_color:
            swatch_color = default_color or "#e2e8f0"

        swatch = QPushButton()
        swatch.setFixedSize(22, 22)
        apply_color_swatch(swatch, swatch_color, marker="s", icon_size=16)
        swatch.setCursor(QCursor(Qt.PointingHandCursor))
        swatch.clicked.connect(lambda checked=False, k=style_key, btn=swatch: self._open_line_style_dialog(k, btn))
        item_layout.addWidget(swatch)

        checkbox = QCheckBox()
        checkbox.setChecked(self._overlay_checked_state(style_key))
        checkbox.stateChanged.connect(lambda state, k=style_key: self._on_overlay_checkbox_change(k, state))
        checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        checkbox.setFixedWidth(18)
        item_layout.addWidget(checkbox)

        label = QLabel(translate(label_key))
        item_layout.addWidget(label, 1)
        item_layout.addStretch()

        item_widget.setLayout(item_layout)

        item = QListWidgetItem()
        item.setSizeHint(item_widget.sizeHint())
        self._set_legend_item_meta(item, "overlay", style_key)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
        self._legend_list.addItem(item)
        self._legend_list.setItemWidget(item, item_widget)

    def _overlay_checked_state(self, style_key):
        if self._is_plumbotectonics_group_style(style_key):
            visibility = getattr(app_state, "plumbotectonics_group_visibility", {}) or {}
            return bool(getattr(app_state, "show_plumbotectonics_curves", True) and visibility.get(style_key, True))
        attr = OVERLAY_TOGGLE_MAP.get(style_key)
        if attr:
            return bool(getattr(app_state, attr, True))
        if style_key == "isochron":
            return bool(getattr(app_state, "show_isochrons", False) or getattr(app_state, "selected_isochron_data", None))
        return True

    def _on_overlay_checkbox_change(self, style_key, state):
        checked = state == Qt.Checked
        if self._is_plumbotectonics_group_style(style_key):
            if not hasattr(app_state, "plumbotectonics_group_visibility"):
                state_gateway.set_attr("plumbotectonics_group_visibility", {})
            visibility = getattr(app_state, "plumbotectonics_group_visibility", {}) or {}
            visibility[style_key] = checked
            state_gateway.set_attr("plumbotectonics_group_visibility", visibility)
            try:
                from visualization.plotting.style import refresh_overlay_visibility

                refresh_overlay_visibility()
            except Exception:
                self._refresh_plot()
            return
        if style_key == "isochron":
            if checked:
                state_gateway.set_show_isochrons(True)
                try:
                    selected = getattr(app_state, "selected_indices", set()) or set()
                    if app_state.render_mode == "PB_EVOL_76" and len(selected) >= 2:
                        from visualization.events import calculate_selected_isochron

                        calculate_selected_isochron()
                except Exception as err:
                    logger.warning("Failed to calculate selected isochron: %s", err)
            else:
                state_gateway.set_show_isochrons(False)
                state_gateway.set_selected_isochron_data(None)
                state_gateway.set_attr("isochron_results", {})

            self._sync_geochem_toggle_panels(style_key)
            self._refresh_plot()
            return
        attr = OVERLAY_TOGGLE_MAP.get(style_key)
        if attr:
            state_gateway.set_attr(attr, checked)

        if style_key == "isochron" and not checked:
            state_gateway.set_selected_isochron_data(None)
            state_gateway.set_attr("isochron_results", {})

        self._sync_geochem_toggle_panels(style_key)

        try:
            from visualization.plotting.style import refresh_overlay_visibility

            refresh_overlay_visibility()
        except Exception:
            self._refresh_plot()

    def _sync_geochem_toggle_panels(self, style_key):
        panel = getattr(app_state, "control_panel_ref", None)
        data_panel = getattr(panel, "data_panel", None) if panel is not None else None
        if data_panel is None:
            return
        try:
            if style_key == "model_curve":
                data_panel._sync_geochem_toggle_widgets(
                    app_state.show_model_curves,
                    getattr(data_panel, "modeling_show_model_check", None),
                    getattr(data_panel, "show_model_check", None),
                )
            elif style_key == "plumbotectonics_curve":
                data_panel._sync_geochem_toggle_widgets(
                    app_state.show_plumbotectonics_curves,
                    getattr(data_panel, "modeling_show_plumbotectonics_check", None),
                )
            elif style_key == "paleoisochron":
                data_panel._sync_geochem_toggle_widgets(
                    app_state.show_paleoisochrons,
                    getattr(data_panel, "modeling_show_paleoisochron_check", None),
                    getattr(data_panel, "show_paleoisochron_check", None),
                )
            elif style_key == "model_age_line":
                data_panel._sync_geochem_toggle_widgets(
                    app_state.show_model_age_lines,
                    getattr(data_panel, "modeling_show_model_age_check", None),
                    getattr(data_panel, "show_model_age_check", None),
                )
            elif style_key == "isochron":
                data_panel._sync_geochem_toggle_widgets(
                    app_state.show_isochrons,
                    getattr(data_panel, "modeling_show_isochron_check", None),
                    getattr(data_panel, "show_isochron_check", None),
                )
                if hasattr(data_panel, "_update_isochron_btn_text"):
                    data_panel._update_isochron_btn_text()
            elif style_key == "growth_curve":
                data_panel._sync_geochem_toggle_widgets(
                    app_state.show_growth_curves,
                    getattr(data_panel, "modeling_show_growth_curve_check", None),
                )
        except Exception:
            pass

    def _on_legend_item_double_clicked(self, item):
        meta = item.data(Qt.UserRole) if item is not None else None
        if not meta:
            return
        entry_type = meta.get("type")
        entry_key = meta.get("key")
        if entry_type == "group":
            self._bring_to_front(entry_key)
        elif entry_type == "overlay":
            self._bring_overlay_to_front(entry_key)

    def _bring_overlay_to_front(self, style_key):
        ax = getattr(app_state, "ax", None)
        if ax is None:
            return
        overlay_map = getattr(app_state, "overlay_artists", {}) or {}
        artists = self._overlay_artists_for_style(style_key, overlay_map=overlay_map)
        if not artists:
            return

        max_z = 2
        try:
            for artist in ax.get_children():
                try:
                    max_z = max(max_z, artist.get_zorder())
                except Exception:
                    continue
        except Exception:
            pass

        target_z = max_z + 1
        for artist in artists:
            try:
                z_value = target_z + 0.25 if hasattr(artist, "get_text") else target_z
                artist.set_zorder(z_value)
            except Exception:
                pass

        if app_state.fig is not None and app_state.fig.canvas is not None:
            app_state.fig.canvas.draw_idle()
        self._move_legend_item_to_top("overlay", style_key)

    def _update_marker_swatch(self, group, swatch):
        color = app_state.current_palette.get(group, "#cccccc")
        marker = app_state.group_marker_map.get(group, getattr(app_state, "plot_marker_shape", "o"))
        icon = self._build_marker_icon(color, marker, size=16)
        swatch.setIcon(icon)
        swatch.setIconSize(QSize(16, 16))
        swatch.setStyleSheet("border: 1px solid #111827; border-radius: 3px; background: transparent;")

    def _sync_legend_panel_ui(self, refresh=False):
        panel = getattr(app_state, "control_panel_ref", None)
        if panel is None or not hasattr(panel, "legend_checkboxes"):
            return
        try:
            if refresh and hasattr(panel, "_update_group_list"):
                panel._update_group_list()
            elif hasattr(panel, "sync_legend_ui"):
                panel.sync_legend_ui()
        except Exception:
            pass

    def _pick_color(self, group, swatch):
        current_color = app_state.current_palette.get(group, "#cccccc")
        color = QColorDialog.getColor(QColor(current_color), self, f"Color for {group}")
        if color.isValid():
            new_hex = color.name()
            app_state.current_palette[group] = new_hex
            self._update_marker_swatch(group, swatch)

            if hasattr(app_state, "group_to_scatter") and group in app_state.group_to_scatter:
                sc = app_state.group_to_scatter[group]
                try:
                    sc.set_color(new_hex)
                    sc.set_edgecolor("#1e293b")
                    if app_state.fig:
                        app_state.fig.canvas.draw_idle()
                except Exception as exc:
                    logger.warning("Failed to update color for %s: %s", group, exc)
            self._sync_legend_panel_ui(refresh=True)

    def _set_group_shape_value(self, group, marker_value, swatch):
        self._ensure_marker_shape_map()
        marker = marker_value or getattr(app_state, "plot_marker_shape", "o")
        app_state.group_marker_map[group] = marker
        self._update_marker_swatch(group, swatch)
        self._sync_legend_panel_ui(refresh=True)
        self._refresh_plot()

    def _show_color_shape_menu(self, group, swatch):
        self._ensure_marker_shape_map()
        menu = QMenu(self)

        color_action = QAction(translate("Color..."), self)
        color_action.triggered.connect(lambda checked=False, g=group, btn=swatch: self._pick_color(g, btn))
        menu.addAction(color_action)

        shape_menu = menu.addMenu(translate("Shape"))
        current_marker = app_state.group_marker_map.get(group, getattr(app_state, "plot_marker_shape", "o"))
        for label, value in self._marker_shape_map.items():
            icon = self._build_marker_icon("#94a3b8", value, size=14)
            action = QAction(icon, "", self)
            action.setCheckable(True)
            action.setChecked(value == current_marker)
            action.triggered.connect(
                lambda checked=False, g=group, v=value, btn=swatch: self._set_group_shape_value(g, v, btn)
            )
            shape_menu.addAction(action)

        menu.exec_(QCursor.pos())

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
            state_gateway.set_visible_groups(None)
        else:
            state_gateway.set_visible_groups(sorted(current_visible))

        self._sync_legend_panel_ui()
        self._refresh_plot()

    def _bring_to_front(self, group):
        if hasattr(app_state, "group_to_scatter") and group in app_state.group_to_scatter:
            sc = app_state.group_to_scatter[group]
            try:
                max_z = 2
                if hasattr(app_state, "scatter_collections"):
                    for c in app_state.scatter_collections:
                        max_z = max(max_z, c.get_zorder())

                sc.set_zorder(max_z + 1)
                if app_state.fig:
                    app_state.fig.canvas.draw_idle()
            except Exception as exc:
                logger.warning("Failed to bring %s to front: %s", group, exc)
        self._move_legend_item_to_top("group", group)

    def _update_legend_panel(self, title, handles, labels):
        try:
            if not hasattr(self, "_legend_list") or self._legend_list is None:
                return
            self._apply_legend_panel_layout()
            location_key = getattr(app_state, "legend_location", None)
            if location_key not in {"outside_left", "outside_right"}:
                return

            if self._legend_title_label is not None:
                self._legend_title_label.setText(str(title))

            self._legend_list.clear()

            has_groups = app_state.last_group_col and app_state.df_global is not None
            groups = []
            if has_groups:
                groups = list(app_state.df_global[app_state.last_group_col].unique())
            overlay_entries = self._overlay_entries_for_legend()

            entries = []
            if has_groups:
                max_items = 100
                groups_to_show = list(groups)[:max_items]
                if len(groups) > max_items:
                    logger.warning("Showing first %d groups only.", max_items)
                for group in groups_to_show:
                    entries.append({"type": "group", "key": group, "group": group})
            for overlay_entry in overlay_entries:
                entries.append(
                    {
                        "type": "overlay",
                        "key": overlay_entry["style_key"],
                        "label_key": overlay_entry["label_key"],
                        "default_color": overlay_entry.get("default_color"),
                        "fallback": overlay_entry.get("fallback"),
                    }
                )

            order_keys = getattr(app_state, "legend_item_order", []) or []
            order_index = {key: idx for idx, key in enumerate(order_keys)}
            entries.sort(key=lambda e: order_index.get(self._legend_order_key(e["type"], e["key"]), 10_000))

            if has_groups:
                self._ensure_marker_shape_map()
                visible = set(app_state.visible_groups) if app_state.visible_groups is not None else set(groups)

            for entry in entries:
                if entry["type"] == "group":
                    group = entry["group"]
                    item_widget = QWidget()
                    item_layout = QHBoxLayout()
                    item_layout.setContentsMargins(4, 2, 4, 2)
                    item_layout.setSpacing(6)

                    color_btn = QPushButton()
                    color_btn.setFixedSize(22, 22)
                    self._update_marker_swatch(group, color_btn)
                    color_btn.setCursor(QCursor(Qt.PointingHandCursor))
                    color_btn.clicked.connect(
                        lambda checked=False, g=group, btn=color_btn: self._show_color_shape_menu(g, btn)
                    )
                    item_layout.addWidget(color_btn)

                    checkbox = QCheckBox()
                    checkbox.setChecked(group in visible)
                    checkbox.stateChanged.connect(lambda state, g=group: self._on_group_checkbox_change(g, state))
                    checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                    checkbox.setFixedWidth(18)
                    item_layout.addWidget(checkbox)

                    label = QLabel(str(group))
                    item_layout.addWidget(label, 1)
                    item_layout.addStretch()

                    item_widget.setLayout(item_layout)

                    item = QListWidgetItem()
                    item.setSizeHint(item_widget.sizeHint())
                    self._set_legend_item_meta(item, "group", group)
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
                    self._legend_list.addItem(item)
                    self._legend_list.setItemWidget(item, item_widget)
                elif entry["type"] == "overlay":
                    self._add_overlay_legend_item(
                        entry["label_key"],
                        entry["key"],
                        default_color=entry.get("default_color"),
                        fallback=entry.get("fallback"),
                    )
            self._apply_legend_z_order()
        except Exception as exc:
            import traceback

            logger.error("Legend panel update failed: %s", exc)
            traceback.print_exc()
