"""
工具提示配置对话框
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QListWidget, QListWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt

from core import app_state, translate


def get_tooltip_configuration(parent=None):
    """
    打开工具提示配置对话框

    Args:
        parent: 父窗口

    Returns:
        list: 选中的列名列表，如果取消则返回 None
    """
    dialog = TooltipConfigDialog(parent)
    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_selected_columns()
    return None


class TooltipConfigDialog(QDialog):
    """工具提示配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate("Configure Tooltip"))
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        self._setup_ui()
        self._load_current_selection()

    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 说明文本
        info_label = QLabel(translate("Select columns to display:"))
        layout.addWidget(info_label)

        # 列列表
        self.column_list = QListWidget()
        self.column_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.column_list, 1)

        # 填充列列表
        if app_state.df_global is not None:
            for col in app_state.df_global.columns:
                item = QListWidgetItem(col)
                self.column_list.addItem(item)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        select_all_btn = QPushButton(translate("Select all"))
        select_all_btn.clicked.connect(self._select_all)
        button_layout.addWidget(select_all_btn)

        clear_btn = QPushButton(translate("Clear"))
        clear_btn.clicked.connect(self._clear_selection)
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        ok_btn = QPushButton(translate("OK"))
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton(translate("Cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _load_current_selection(self):
        """加载当前选择"""
        current_cols = getattr(app_state, 'tooltip_columns', [])
        if not current_cols and app_state.df_global is not None:
            # 默认选择前几列
            current_cols = list(app_state.df_global.columns[:5])

        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            if item.text() in current_cols:
                item.setSelected(True)

    def _select_all(self):
        """全选"""
        for i in range(self.column_list.count()):
            self.column_list.item(i).setSelected(True)

    def _clear_selection(self):
        """清除选择"""
        self.column_list.clearSelection()

    def get_selected_columns(self):
        """获取选中的列"""
        selected = []
        for item in self.column_list.selectedItems():
            selected.append(item.text())
        return selected
