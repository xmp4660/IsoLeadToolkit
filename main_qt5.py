#!/usr/bin/env python3
"""
Isotopes Analyse - PyQt5 版本

基于 PyQt5 的同位素数据分析应用程序
"""

import sys
import os

# 确保项目根目录在路径中
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """主函数"""
    from ui.qt5_app import Qt5Application

    app = Qt5Application()
    return app.run()


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
