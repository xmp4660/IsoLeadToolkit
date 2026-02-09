"""
Qt5 进度对话框
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel,
                              QProgressBar, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.localization import translate


class Qt5ProgressDialog(QDialog):
    """Qt5 进度对话框"""

    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 150)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 消息标签
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("font-size: 12px; color: #1a202c;")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 不确定模式
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #e2e8f0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.show()

    def update_message(self, message):
        """更新消息"""
        self.message_label.setText(message)

    def set_progress(self, value, maximum=100):
        """设置进度"""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)


class ProgressDialog:
    """进度对话框包装器（兼容 Tkinter 版本）"""

    def __init__(self, title, message):
        self.dialog = Qt5ProgressDialog(title, message)

    def update_message(self, message):
        """更新消息"""
        self.dialog.update_message(message)

    def set_progress(self, value, maximum=100):
        """设置进度"""
        self.dialog.set_progress(value, maximum)

    def close(self):
        """关闭对话框"""
        self.dialog.close()
