"""Qt5 控制面板。

提供算法参数调整和可视化设置。
"""
import logging
from typing import Any, Callable

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QScrollArea, QComboBox, QGroupBox, QTabWidget,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from core import app_state, available_languages, state_gateway, translate
from ui.panels import (
    DataPanel, DisplayPanel, AnalysisPanel,
    ExportPanel, LegendPanel, GeoPanel,
)

logger = logging.getLogger(__name__)


class Qt5ControlPanel(QWidget):
    """Qt5 控制面板。

    .. deprecated::
        控制面板已禁用，改用菜单栏弹出对话框模式。
        参见 :func:`create_section_dialog`。
        此类保留仅供向后兼容，将在下个大版本移除。
    """

    parameter_changed = pyqtSignal(str, object)

    def __init__(self, callback=None, parent=None, build_ui=True):
        super().__init__(parent)
        self.callback = callback
        self._is_initialized = False
        self._is_rebuilding = False
        self._language_change_pending = False

        self.data_panel = None
        self.display_panel = None
        self.analysis_panel = None
        self.export_panel = None
        self.legend_panel = None
        self.geo_panel = None

        if build_ui:
            self._setup_ui()
            self._setup_styles()
            self._update_data_count_label()
            self.update_selection_controls()
            self._is_initialized = True
            try:
                app_state.register_language_listener(self._refresh_language)
            except Exception:
                pass

    def _setup_ui(self):
        """初始化控制面板 UI"""
        self.setWindowTitle(translate("Control Panel"))
        self.resize(560, 860)
        self.setMinimumSize(520, 740)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        title = QLabel(translate("Visualization Controls"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.data_count_label = QLabel("")
        header_layout.addWidget(self.data_count_label)

        lang_label = QLabel(f"{translate('Language')}:")
        header_layout.addWidget(lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.setFixedWidth(140)
        lang_map = dict(available_languages())
        for code, label in lang_map.items():
            self.lang_combo.addItem(label, code)
        current_lang = getattr(app_state, 'language', None)
        if current_lang:
            idx = self.lang_combo.findData(current_lang)
            if idx >= 0:
                self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_language_change)
        header_layout.addWidget(self.lang_combo)

        root_layout.addWidget(header)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        root_layout.addWidget(divider)

        status_group = QGroupBox(translate("Status"))
        status_layout = QHBoxLayout(status_group)
        status_layout.setContentsMargins(12, 8, 12, 8)
        status_layout.setSpacing(16)

        status_summary = QVBoxLayout()
        status_summary.setSpacing(6)

        self.status_data_label = QLabel("")
        self.status_render_label = QLabel("")
        self.status_algo_label = QLabel("")
        self.status_group_label = QLabel("")
        self.status_selected_label = QLabel("")

        for lbl in (
            self.status_data_label,
            self.status_render_label,
            self.status_algo_label,
            self.status_group_label,
            self.status_selected_label,
        ):
            lbl.setWordWrap(True)
            status_summary.addWidget(lbl)

        status_layout.addLayout(status_summary, 1)

        status_actions = QGroupBox(translate("Quick Actions"))
        actions_layout = QVBoxLayout()

        clear_btn = QPushButton(translate("Clear Selection"))
        clear_btn.setFixedWidth(170)
        clear_btn.clicked.connect(self._clear_selection_only)
        actions_layout.addWidget(clear_btn, 0, Qt.AlignHCenter)

        self.status_export_button = QPushButton(translate("Export Selected"))
        self.status_export_button.setFixedWidth(170)
        self.status_export_button.clicked.connect(self._on_export_clicked)
        actions_layout.addWidget(self.status_export_button, 0, Qt.AlignHCenter)

        refresh_btn = QPushButton(translate("Replot"))
        refresh_btn.setFixedWidth(170)
        refresh_btn.clicked.connect(self._on_change)
        actions_layout.addWidget(refresh_btn, 0, Qt.AlignHCenter)

        status_actions.setLayout(actions_layout)
        status_layout.addWidget(status_actions, 0)

        root_layout.addWidget(status_group)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(False)

        self.data_panel = DataPanel(self._on_change, self)
        self.display_panel = DisplayPanel(self._on_change, self)
        self.analysis_panel = AnalysisPanel(self._on_change, self)
        self.export_panel = ExportPanel(self._on_change, self)
        self.legend_panel = LegendPanel(self._on_change, self)
        self.geo_panel = GeoPanel(self._on_change, self)

        self.data_panel.legend_panel = self.legend_panel
        self.data_panel.geo_panel = self.geo_panel
        self.display_panel.legend_panel = self.legend_panel

        sections = [
            (translate("Data"), self.data_panel),
            (translate("Display"), self.display_panel),
            (translate("Analysis"), self.analysis_panel),
            (translate("Export"), self.export_panel),
            (translate("Legend"), self.legend_panel),
            (translate("Geochemistry"), self.geo_panel),
        ]

        for label, panel in sections:
            content = panel.build()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setWidget(content)
            self.tab_widget.addTab(scroll, label)

        root_layout.addWidget(self.tab_widget, 1)

        self._update_status_panel()

    def _setup_styles(self):
        """应用基础样式"""
        self.setStyleSheet(
            "QFrame { background: transparent; }"
            "QGroupBox { margin-top: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 6px; }"
            "QScrollArea { border: none; }"
            "QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 6px; }"
            "QTabBar::tab { padding: 6px 12px; margin-right: 2px; }"
            "QTabBar::tab:selected { background-color: #e2e8f0; }"
            "QPushButton { text-align: left; padding: 6px 10px; }"
        )

    def _on_language_change(self, _index):
        """语言切换"""
        code = self.lang_combo.currentData() if self.lang_combo else None
        if not code:
            return
        if self._is_rebuilding or self._language_change_pending:
            return
        if code == getattr(app_state, 'language', None):
            return

        self._language_change_pending = True
        try:
            from core import set_language
            set_language(code)
        finally:
            QTimer.singleShot(0, self._rebuild_ui)

    def _refresh_language(self):
        """刷新语言"""
        self._update_data_count_label()
        if not self._is_initialized or self._is_rebuilding:
            return
        if self._language_change_pending:
            return
        QTimer.singleShot(0, self._rebuild_ui)

    def _rebuild_ui(self):
        """重建 UI 以刷新翻译"""
        self._is_rebuilding = True
        try:
            layout = self.layout()
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()

            self._setup_ui()
            self._setup_styles()
            self._update_data_count_label()
        finally:
            self._is_rebuilding = False
            self._language_change_pending = False

    def _update_data_count_label(self):
        """更新数据计数标签"""
        if app_state.df_global is not None:
            count = len(app_state.df_global)
            text = translate("Loaded Data: {count} rows", count=count)
            self.data_count_label.setText(text)
        else:
            self.data_count_label.setText("")
        self._update_status_panel()

    def _update_status_panel(self):
        """刷新右侧状态面板"""
        if any(label is None for label in (
            getattr(self, 'status_data_label', None),
            getattr(self, 'status_render_label', None),
            getattr(self, 'status_algo_label', None),
            getattr(self, 'status_group_label', None),
            getattr(self, 'status_selected_label', None),
        )):
            return

        data_count = len(app_state.df_global) if app_state.df_global is not None else 0
        render_mode = getattr(app_state, 'render_mode', '')
        algorithm = getattr(app_state, 'algorithm', '')
        group_col = getattr(app_state, 'last_group_col', '')
        selected_count = len(getattr(app_state, 'selected_indices', []))

        self.status_data_label.setText(
            translate("Loaded Data: {count} rows", count=data_count)
        )
        self.status_render_label.setText(
            translate("Render Mode: {mode}").format(mode=render_mode)
        )
        self.status_algo_label.setText(
            translate("Algorithm: {mode}").format(mode=algorithm)
        )
        self.status_group_label.setText(
            translate("Group Column: {col}").format(col=group_col)
        )
        self.status_selected_label.setText(
            translate("Selected Samples: {count}").format(count=selected_count)
        )

    def update_selection_controls(self):
        """Refresh selection UI state across panels."""
        if self.analysis_panel is not None:
            try:
                self.analysis_panel.update_selection_controls()
            except Exception:
                pass
        if self.export_panel is not None:
            try:
                self.export_panel.update_selection_controls()
            except Exception:
                pass

        count = len(getattr(app_state, 'selected_indices', []))
        if getattr(self, 'status_export_button', None) is not None:
            self.status_export_button.setEnabled(count > 0)
        self._update_status_panel()

    def _on_change(self):
        """参数变化回调"""
        self._update_status_panel()
        if self.callback:
            self.callback()

    def _clear_selection_only(self):
        if self.export_panel is not None and hasattr(self.export_panel, '_clear_selection_only'):
            self.export_panel._clear_selection_only()
            return
        if app_state.selected_indices:
            app_state.selected_indices.clear()
        try:
            from visualization.events import refresh_selection_overlay
            refresh_selection_overlay()
        except Exception:
            pass
        self.update_selection_controls()

    def _on_export_clicked(self):
        if self.export_panel is not None and hasattr(self.export_panel, '_on_export_clicked'):
            self.export_panel._on_export_clicked()


def create_control_panel(callback: Callable[[], None] | None) -> Qt5ControlPanel:
    """创建控制面板工厂函数"""
    return Qt5ControlPanel(callback)


def create_section_dialog(
    section_key: str | None,
    callback: Callable[[], None] | None,
    parent: Any = None,
) -> Any | None:
    """Create a dialog that hosts a single control section."""
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QApplication, QScrollArea
    from core import set_language

    section_key = (section_key or '').lower()

    section_map = {
        'data': ("Data", DataPanel),
        'display': ("Display", DisplayPanel),
        'analysis': ("Analysis", AnalysisPanel),
        'export': ("Export", ExportPanel),
        'legend': ("Legend", LegendPanel),
        'geochemistry': ("Geochemistry", GeoPanel),
    }

    if section_key not in section_map:
        return None

    title_key, panel_cls = section_map[section_key]
    title = translate(title_key)

    dialog = QDialog(parent)
    dialog.setWindowTitle(title)

    root = QVBoxLayout(dialog)
    header = QHBoxLayout()
    title_label = QLabel(title)
    header.addWidget(title_label)
    header.addStretch()

    lang_label = QLabel(translate("Language"))
    header.addWidget(lang_label)

    lang_combo = QComboBox()
    lang_combo.setFixedWidth(140)
    lang_map = dict(available_languages())
    for code, label in lang_map.items():
        lang_combo.addItem(label, code)
    current_lang = getattr(app_state, 'language', None)
    if current_lang:
        idx = lang_combo.findData(current_lang)
        if idx >= 0:
            lang_combo.setCurrentIndex(idx)
    header.addWidget(lang_combo)
    root.addLayout(header)

    panel = panel_cls(callback, parent=dialog)
    panel.reset_state()

    content_widget = panel.build()
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setWidget(content_widget)
    root.addWidget(scroll, 1)

    def _apply_adaptive_size():
        dialog.adjustSize()
        hint = dialog.sizeHint()
        screen = dialog.screen() or QApplication.primaryScreen()
        if screen is None:
            dialog.resize(hint)
            return
        bounds = screen.availableGeometry()
        max_w = int(bounds.width() * 0.9)
        max_h = int(bounds.height() * 0.85)
        min_w = 420
        min_h = 280
        target_w = min(max(hint.width(), min_w), max_w)
        target_h = min(max(hint.height(), min_h), max_h)
        dialog.resize(target_w, target_h)

    def _rebuild_section():
        panel.reset_state()
        new_content = panel.build()
        scroll.takeWidget()
        scroll.setWidget(new_content)
        QTimer.singleShot(0, _apply_adaptive_size)

    def _try_lightweight_update():
        """尝试轻量级翻译更新，仅刷新带 translate_key 的控件文本。

        如果面板不支持（无 _update_translations），回退到完整重建。
        """
        content_widget = scroll.widget()
        if content_widget is not None and hasattr(panel, '_update_translations'):
            try:
                panel._update_translations(content_widget)
                return
            except Exception:
                logger.debug("Lightweight translation update failed, falling back to rebuild")
        _rebuild_section()

    def _refresh_titles():
        new_title = translate(title_key)
        dialog.setWindowTitle(new_title)
        title_label.setText(new_title)
        lang_label.setText(translate("Language"))

    def _on_language_change(_index):
        code = lang_combo.currentData()
        if not code:
            return
        set_language(code)
        QTimer.singleShot(0, _refresh_titles)
        QTimer.singleShot(0, _try_lightweight_update)

    lang_combo.currentIndexChanged.connect(_on_language_change)

    # 跟踪对话框关闭时的语言，用于检测是否需要重建
    _dialog_last_lang = [getattr(app_state, 'language', None)]

    def _on_show(_event):
        state_gateway.set_control_panel_ref(panel)
        try:
            panel.update_selection_controls()
        except Exception:
            pass
        # 重新注册语言监听器（关闭时已移除）
        listeners = getattr(app_state, 'language_listeners', [])
        if _on_language_refresh not in listeners:
            try:
                app_state.register_language_listener(_on_language_refresh)
            except Exception:
                pass
        # 如果关闭期间语言发生了变化，重建内容
        current_lang = getattr(app_state, 'language', None)
        if current_lang != _dialog_last_lang[0]:
            _dialog_last_lang[0] = current_lang
            # 同步语言下拉框
            idx = lang_combo.findData(current_lang)
            if idx >= 0 and lang_combo.currentIndex() != idx:
                lang_combo.blockSignals(True)
                lang_combo.setCurrentIndex(idx)
                lang_combo.blockSignals(False)
            QTimer.singleShot(0, _refresh_titles)
            QTimer.singleShot(0, _try_lightweight_update)
        QTimer.singleShot(0, _apply_adaptive_size)

    def _on_language_refresh():
        current_lang = getattr(app_state, 'language', None)
        _dialog_last_lang[0] = current_lang
        if current_lang:
            idx = lang_combo.findData(current_lang)
            if idx >= 0 and lang_combo.currentIndex() != idx:
                lang_combo.blockSignals(True)
                lang_combo.setCurrentIndex(idx)
                lang_combo.blockSignals(False)
        QTimer.singleShot(0, _refresh_titles)
        QTimer.singleShot(0, _try_lightweight_update)

    def _on_close(_event):
        if getattr(app_state, 'control_panel_ref', None) is panel:
            state_gateway.set_control_panel_ref(None)
        _dialog_last_lang[0] = getattr(app_state, 'language', None)
        listeners = getattr(app_state, 'language_listeners', [])
        if _on_language_refresh in listeners:
            listeners.remove(_on_language_refresh)

    dialog.showEvent = _on_show
    dialog.closeEvent = _on_close
    try:
        app_state.register_language_listener(_on_language_refresh)
    except Exception:
        pass

    return dialog
