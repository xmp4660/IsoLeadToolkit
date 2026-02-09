"""
Qt5 工作表选择对话框
"""
import pandas as pd
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QFrame,
                              QListWidget, QListWidgetItem,
                              QWidget, QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.localization import translate


class Qt5SheetDialog(QDialog):
    """Qt5 工作表选择对话框"""

    def __init__(self, file_path, default_sheet=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.result = None
        self.default_sheet = default_sheet
        self.sheets = []

        # 加载工作表
        try:
            self.sheets = list(pd.ExcelFile(file_path).sheet_names)
        except Exception as e:
            print(f"[ERROR] Could not load sheets: {e}", flush=True)
            QMessageBox.critical(self, translate("Error"),
                               translate("Failed to load Excel file: {error}").format(error=str(e)))
            return

        self._setup_ui()

    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle(translate("Select Sheet"))
        self.resize(620, 460)
        self.setMinimumSize(560, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        header = QFrame()
        header.setStyleSheet("background-color: #edf2f7;")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel(translate("Choose a Sheet"))
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a202c;")
        header_layout.addWidget(title)

        layout.addWidget(header)

        # 内容
        content = QFrame()
        content.setStyleSheet("background-color: #edf2f7;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)

        subtitle = QLabel(translate(
            "Select the worksheet that contains the measurements you want to analyze."
        ))
        subtitle.setStyleSheet("color: #4a5568; font-size: 12px;")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        # 工作表列表
        self.sheet_list = QListWidget()
        self.sheet_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #2563eb;
                color: white;
            }
        """)

        for sheet in self.sheets:
            item = QListWidgetItem(sheet)
            self.sheet_list.addItem(item)
            if sheet == self.default_sheet:
                item.setSelected(True)

        if self.sheet_list.count() > 0 and not self.default_sheet:
            self.sheet_list.item(0).setSelected(True)

        self.sheet_list.itemDoubleClicked.connect(self._ok_clicked)

        content_layout.addWidget(self.sheet_list, 1)

        layout.addWidget(content, 1)

        # 底部按钮
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

        continue_btn = QPushButton(translate("Continue"))
        continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 8px 24px;
                border-radius: 4px;
            }
        """)
        continue_btn.clicked.connect(self._ok_clicked)
        footer_layout.addWidget(continue_btn)

        layout.addWidget(footer)

    def _ok_clicked(self):
        """确定按钮点击"""
        selected_items = self.sheet_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, translate("Warning"),
                               translate("Please select a sheet."))
            return

        self.result = selected_items[0].text()
        self.accept()


def get_sheet_selection(file_path, default_sheet=None):
    """获取工作表选择"""
    dialog = Qt5SheetDialog(file_path, default_sheet)
    if dialog.exec_() == Qt5SheetDialog.Accepted:
        return dialog.result
    return None
