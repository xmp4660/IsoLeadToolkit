"""
Qt5 数据配置对话框
"""
import pandas as pd
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QFrame,
                              QListWidget, QListWidgetItem,
                              QWidget, QSizePolicy, QMessageBox,
                              QGroupBox, QLineEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.localization import translate


class Qt5DataConfigDialog(QDialog):
    """Qt5 数据配置对话框"""

    def __init__(self, df, default_group_cols=None, default_data_cols=None, parent=None):
        super().__init__(parent)
        self.df = df
        self.result = None

        self.all_columns = list(df.columns)
        self.selected_group_cols = set(default_group_cols or [])
        self.selected_data_cols = set(default_data_cols or [])

        self._setup_ui()

    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle(translate("Configure Data Columns"))
        self.resize(980, 700)
        self.setMinimumSize(900, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        header = QFrame()
        header.setStyleSheet("background-color: #edf2f7;")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel(translate("Select Columns"))
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)

        layout.addWidget(header)

        # 内容
        content = QFrame()
        content.setStyleSheet("background-color: #edf2f7;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # 分组列选择
        self._build_column_section(
            content_layout,
            translate("Grouping Columns"),
            translate("Pick one or more categorical columns to color and organize the scatter plot."),
            'group'
        )

        # 数据列选择
        self._build_column_section(
            content_layout,
            translate("Data Columns"),
            translate("Choose numeric measurements that feed into UMAP or t-SNE embeddings."),
            'data'
        )

        layout.addWidget(content, 1)

        # 底部
        footer = QFrame()
        footer.setStyleSheet("background-color: #edf2f7;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 10, 20, 10)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        footer_layout.addWidget(spacer)

        cancel_btn = QPushButton(translate("Cancel"))
        cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_btn)

        apply_btn = QPushButton(translate("Apply"))
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 8px 24px;
                border-radius: 4px;
            }
        """)
        apply_btn.clicked.connect(self._ok_clicked)
        footer_layout.addWidget(apply_btn)

        layout.addWidget(footer)

    def _build_column_section(self, parent, title, description, selection_type):
        """构建列选择区域"""
        card = QFrame()
        card.setStyleSheet("background-color: white; border-radius: 8px;")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)

        header = QLabel(title)
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        card_layout.addWidget(header)

        desc = QLabel(description)
        desc.setStyleSheet("font-size: 11px; color: #4a5568;")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        # 工具栏
        toolbar = QHBoxLayout()

        select_all_btn = QPushButton(translate("Select all"))
        select_all_btn.clicked.connect(lambda: self._select_all(selection_type))
        toolbar.addWidget(select_all_btn)

        clear_btn = QPushButton(translate("Clear"))
        clear_btn.clicked.connect(lambda: self._clear_selection(selection_type))
        toolbar.addWidget(clear_btn)

        toolbar.addStretch()
        card_layout.addLayout(toolbar)

        # 列列表
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.MultiSelection)
        list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #2563eb;
                color: white;
            }
        """)

        # 填充列
        for col in self.all_columns:
            is_numeric = pd.api.types.is_numeric_dtype(self.df[col])

            if selection_type == 'data' and not is_numeric:
                continue

            dtype_label = translate("numeric") if is_numeric else translate("text")
            display_text = translate("{column} ({dtype})").format(
                column=col,
                dtype=dtype_label
            )

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, col)

            if selection_type == 'group':
                item.setSelected(col in self.selected_group_cols)
            else:
                item.setSelected(col in self.selected_data_cols)

            list_widget.addItem(item)

        # 连接选择变化事件
        list_widget.itemSelectionChanged.connect(
            lambda: self._on_selection_changed(list_widget, selection_type)
        )

        card_layout.addWidget(list_widget, 1)

        # 保存引用
        if selection_type == 'group':
            self.group_list = list_widget
        else:
            self.data_list = list_widget

        parent.addWidget(card, 1)

    def _on_selection_changed(self, list_widget, selection_type):
        """选择变化处理"""
        selected_cols = set()
        for item in list_widget.selectedItems():
            col = item.data(Qt.UserRole)
            selected_cols.add(col)

        if selection_type == 'group':
            self.selected_group_cols = selected_cols
        else:
            self.selected_data_cols = selected_cols

    def _select_all(self, selection_type):
        """全选"""
        list_widget = self.group_list if selection_type == 'group' else self.data_list
        list_widget.selectAll()

    def _clear_selection(self, selection_type):
        """清除选择"""
        list_widget = self.group_list if selection_type == 'group' else self.data_list
        list_widget.clearSelection()

    def _ok_clicked(self):
        """确定"""
        # 验证选择
        if not self.selected_group_cols:
            QMessageBox.warning(
                self,
                translate("Validation Error"),
                translate("Please select at least one grouping column.")
            )
            return

        if not self.selected_data_cols:
            QMessageBox.warning(
                self,
                translate("Validation Error"),
                translate("Please select at least one data column.")
            )
            return

        # 检查数据列是否为数值型
        for col in self.selected_data_cols:
            if not pd.api.types.is_numeric_dtype(self.df[col]):
                QMessageBox.warning(
                    self,
                    translate("Validation Error"),
                    translate("Data column '{column}' is not numeric. Please select only numeric columns for data.").format(column=col)
                )
                return

        self.result = {
            'group_cols': list(self.selected_group_cols),
            'data_cols': list(self.selected_data_cols)
        }
        self.accept()


def get_data_configuration(df, default_group_cols=None, default_data_cols=None):
    """获取数据配置"""
    dialog = Qt5DataConfigDialog(df, default_group_cols, default_data_cols)
    if dialog.exec_() == Qt5DataConfigDialog.Accepted:
        return dialog.result
    return None
