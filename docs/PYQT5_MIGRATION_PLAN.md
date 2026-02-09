# PyQt5 迁移方案

> 版本：1.0
> 更新日期：2025-02-09
> 项目：Isotopes Analyse

---

## 目录

1. [项目现状分析](#1-项目现状分析)
2. [迁移策略对比](#2-迁移策略对比)
3. [详细实施计划](#3-详细实施计划)
4. [Tkinter 到 PyQt5 API 对照表](#4-tkinter-到-pyqt5-api-对照表)
5. [关键迁移注意事项](#5-关键迁移注意事项)
6. [工作量评估](#6-工作量评估)
7. [风险和缓解措施](#7-风险和缓解措施)
8. [迁移检查清单](#8-迁移检查清单)

---

## 1. 项目现状分析

### 1.1 当前技术栈

| 类别 | 技术选型 |
|------|----------|
| GUI 框架 | Tkinter（Python 标准库） |
| Python 版本 | >= 3.13 |
| 可视化 | Matplotlib + Seaborn + mpltern + python-ternary |
| 数据处理 | pandas + openpyxl + xlsxwriter |
| 机器学习 | scikit-learn + umap-learn |
| 国际化 | 自定义多语言框架（中/英） |
| 构建工具 | PyInstaller |

### 1.2 GUI 文件清单

```
ui/
├── __init__.py
├── dialogs/                    # 对话框模块
│   ├── __init__.py
│   ├── file_dialog.py          # 文件选择对话框
│   ├── sheet_dialog.py         # 工作表选择对话框
│   ├── data_config.py          # 数据配置对话框
│   ├── two_d_dialog.py        # 2D 列选择对话框
│   ├── three_d_dialog.py       # 3D 列选择对话框
│   ├── ternary_dialog.py       # 三元图对话框
│   ├── legend_dialog.py        # 图例对话框
│   └── progress_dialog.py      # 进度对话框
└── panel/                       # 控制面板模块
    ├── __init__.py
    ├── control_panel.py        # ControlPanel 主类
    ├── mixins/                 # Mixin 混合类
    │   ├── __init__.py
    │   ├── utils.py            # 工具方法
    │   ├── handlers.py         # 事件处理
    │   ├── dialogs.py           # 对话框
    │   └── export.py           # 导出功能
    └── tabs/                   # 标签页
        ├── __init__.py
        ├── settings_tab.py     # 设置标签
        ├── algorithm_tab.py    # 算法标签
        ├── tools_tab.py        # 工具标签
        ├── style_tab.py        # 样式标签
        ├── legend_tab.py       # 图例标签
        └── geochemistry_tab.py # 地球化学标签
```

### 1.3 核心入口文件

| 文件 | 职责 |
|------|------|
| `main.py` | 应用入口 |
| `core/app.py` | Application 类（应用生命周期管理） |
| `core/state.py` | 应用状态管理 |
| `data/loader.py` | 数据加载 |

### 1.4 当前架构特点

- **Mixin 模式**：控制面板通过多继承组合功能
- **国际化支持**：`_register_translation()` + `refresh_language()` 机制
- **会话管理**：`save_session_params()` / `load_session_params()`
- **样式系统**：ttk.Style 集中配置

---

## 2. 迁移策略对比

### 2.1 可选策略

| 策略 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A. 渐进式迁移** | 逐步将 Tkinter 替换为 PyQt5 | 风险低，可逐步验证 | 两套代码需同步维护 |
| **B. 全新重写** | 用 PyQt5 完全重写 UI 层 | 代码干净，充分利用 Qt 特性 | 工作量大，需全面测试 |
| **C. 抽象层适配** | 创建 UI 抽象层隔离框架差异 | 核心逻辑复用，换肤容易 | 增加抽象层复杂度 |

### 2.2 推荐策略

**推荐方案：B - 全新重写**

理由：
1. 当前 Tkinter 代码量适中，重写可控
2. 可充分利用 PyQt5 的现代特性
3. 避免维护两套代码的技术债
4. Qt 生态更丰富，后续扩展方便

---

## 3. 详细实施计划

### 3.1 阶段 1：依赖配置

#### 文件：`pyproject.toml`

**新增依赖：**

```toml
[project]
dependencies = [
    # 现有依赖...
    "pyqt5 >= 5.15.10",
    "pyqt5-qt5 >= 5.15.11",
    "PyQtWebEngine >= 5.15.6",  # 可选：如需嵌入浏览器
]
```

**修改说明：**
- 删除 Tkinter 相关注释（Tkinter 是标准库，无需依赖）
- 保留 matplotlib 后端配置修改

---

### 3.2 阶段 2：核心架构

#### 3.2.1 matplotlib 后端切换

**文件：`core/app.py`**

```python
# 修改前
try:
    matplotlib.use('TkAgg')
except Exception:
    matplotlib.use('Agg')

# 修改后
try:
    matplotlib.use('Qt5Agg')
except Exception:
    matplotlib.use('Agg')
```

**说明：**
- `Qt5Agg` 后端与 PyQt5 完全兼容
- DPI 感知由 Qt 自动处理，可简化 `_enable_high_dpi_awareness()` 函数

---

#### 3.2.2 Qt5 主窗口基类

**新建文件：`ui/qt5_main_window.py`**

```python
"""
Qt5 主窗口基类
提供标准的应用程序窗口框架
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QDockWidget, QToolBar,
                              QStatusBar, QMenuBar)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QAction, QFont

# 默认图标尺寸
DEFAULT_TOOLBAR_ICON_SIZE = QSize(24, 24)


class Qt5MainWindow(QMainWindow):
    """Qt5 主窗口基类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        self._restore_state()

    def _setup_ui(self):
        """设置 UI 基本属性"""
        self.setWindowTitle("Isotopes Analyse")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)

        # 中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 中央内容区域
        self.central_area = QWidget()
        self.main_layout.addWidget(self.central_area)

        # 浮动dock区域
        self.dock_widgets = []

    def _setup_menubar(self):
        """设置菜单栏"""
        self.menubar = self.menuBar()

    def _setup_toolbar(self):
        """设置工具栏"""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(DEFAULT_TOOLBAR_ICON_SIZE)
        self.addToolBar(self.toolbar)

    def _setup_statusbar(self):
        """设置状态栏"""
        self.statusBar().showMessage("Ready")

    def _restore_state(self):
        """恢复窗口状态"""
        # TODO: 从配置恢复窗口位置、大小、停靠状态

    def save_state(self):
        """保存窗口状态"""
        settings = QSettings("IsotopesAnalyse", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())

    def closeEvent(self, event):
        """关闭事件处理"""
        self.save_state()
        event.accept()

    def add_dock_widget(self, area, widget, title, allowed_areas=Qt.AllDockWidgetAreas):
        """添加停靠窗口"""
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setAllowedAreas(allowed_areas)
        self.addDockWidget(area, dock)
        self.dock_widgets.append(dock)
        return dock
```

---

#### 3.2.3 Qt5 应用程序类

**新建文件：`ui/qt5_app.py`**

```python
"""
Qt5 应用程序类
管理应用初始化、生命周期和资源清理
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QSettings, QTranslator, QLocale
from PyQt5.QtGui import QFont, QIcon

from core import CONFIG, app_state, load_session_params, save_session_params
from core.localization import set_language, available_languages
from ui.qt5_main_window import Qt5MainWindow


class Qt5Application:
    """Qt5 应用程序类"""

    def __init__(self):
        self.app = None
        self.main_window = None
        self.translator = None

    def _configure_fonts(self):
        """配置字体"""
        default_font = QFont("Microsoft YaHei UI", 9)
        QApplication.setFont(default_font)

    def _setup_translator(self, language):
        """设置翻译"""
        if self.translator:
            QApplication.removeTranslator(self.translator)

        self.translator = QTranslator()
        translations_dir = "locales"

        if self.translator.load(QLocale(language), "qt", "_", translations_dir):
            QApplication.installTranslator(self.translator)

    def _load_session(self):
        """加载会话参数"""
        session_data = load_session_params()

        if session_data:
            requested_language = session_data.get('language')
        else:
            requested_language = app_state.language or CONFIG.get('default_language')

        if not set_language(requested_language):
            requested_language = CONFIG.get('default_language', 'en')
            set_language(requested_language)

        return session_data

    def _restore_session_state(self, session_data):
        """恢复会话状态"""
        if not session_data:
            app_state.algorithm = 'UMAP'
            app_state.render_mode = 'UMAP'
            return

        # 算法参数
        app_state.algorithm = session_data.get('algorithm', 'UMAP')
        app_state.umap_params.update(session_data.get('umap_params', {}))
        app_state.tsne_params.update(session_data.get('tsne_params', {}))
        app_state.point_size = session_data.get('point_size', app_state.point_size)

        # 渲染模式
        render_mode = session_data.get('render_mode') or session_data.get('plot_mode', 'UMAP')
        app_state.render_mode = render_mode
        app_state.selected_2d_cols = session_data.get('selected_2d_cols', [])
        app_state.selected_3d_cols = session_data.get('selected_3d_cols', [])

        # UI 主题
        app_state.ui_theme = session_data.get('ui_theme', 'Modern Light')

    def run(self):
        """运行应用程序"""
        # 高 DPI 设置
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

        # 创建应用
        self.app = QApplication(sys.argv)
        self._configure_fonts()

        # 加载会话
        session_data = self._load_session()

        # 恢复会话状态
        self._restore_session_state(session_data)

        # 数据加载
        from data.loader import load_data
        if not load_data(show_file_dialog=True, show_config_dialog=True):
            print("[ERROR] Failed to load data. Exiting.")
            return False

        # 创建主窗口
        self.main_window = Qt5MainWindow()

        # 显示窗口
        self.main_window.show()

        # 事件循环
        result = self.app.exec_()

        # 保存会话
        save_session_params(
            algorithm=app_state.algorithm,
            # ... 其他参数
        )

        return result == 0
```

---

### 3.3 阶段 3：Qt5 控制面板

#### 3.3.1 整体架构

**新建文件：`ui/qt5_control_panel.py`**

```
ControlPanel
├── _setup_ui()           # 初始化 UI
├── _setup_styles()       # 样式配置
├── _setup_signals()       # 信号槽连接
├── _create_navigation()   # 侧边导航
├── _create_content()      # 内容区域
├── _create_footer()        # 底部按钮
└── 各个 Section 的内容构建方法
```

---

#### 3.3.2 基础控制面板类

```python
"""
Qt5 控制面板
提供算法参数调整和可视化设置
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QStackedWidget, QPushButton, QLabel,
                              QFrame, QScrollArea, QToolButton,
                              QComboBox, QCheckBox, QRadioButton,
                              QSlider, QProgressBar, QGroupBox,
                              QLineEdit, QSpinBox, QDoubleSpinBox,
                              QTabWidget, QGridLayout, QListWidget,
                              QListWidgetItem)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

from core import translate, app_state
from core.localization import available_languages


class Qt5ControlPanel(QWidget):
    """Qt5 控制面板"""

    # 信号定义
    parameter_changed = pyqtSignal(str, object)

    def __init__(self, callback=None, parent=None):
        super().__init__(parent)
        self.callback = callback
        self._translations = {}

        # 初始化变量
        self.sliders = {}
        self.labels = {}
        self.radio_vars = {}
        self.check_vars = {}
        self._slider_steps = {}
        self._slider_delay_ms = 350
        self._slider_timers = {}

        # 样式常量
        self.primary_bg = "#edf2f7"
        self.card_bg = "#ffffff"

        self._setup_ui()
        self._setup_styles()
        self._setup_signals()
        self._refresh_language()

    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle(translate("Control Panel"))
        self.setMinimumWidth(520)
        self.resize(560, 860)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 标题栏
        self._create_header(layout)

        # 主内容区（侧边导航 + 内容）
        content_wrap = QHBoxLayout()
        content_wrap.setSpacing(10)

        # 侧边导航
        self.nav_frame = QFrame()
        self.nav_frame.setFixedWidth(120)
        self.nav_layout = QVBoxLayout(self.nav_frame)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(2)

        self.section_buttons = {}
        self._create_navigation()

        # 内容区域
        self.content_stack = QStackedWidget()
        self._create_content()

        content_wrap.addWidget(self.nav_frame)
        content_wrap.addWidget(self.content_stack, 1)

        layout.addLayout(content_wrap, 1)

        # 底部按钮
        self._create_footer(layout)

    def _create_header(self, layout):
        """创建标题栏"""
        header = QHBoxLayout()

        title = QLabel(translate("Visualization Controls"))
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)

        self.data_count_label = QLabel()
        header.addWidget(self.data_count_label, alignment=Qt.AlignRight)

        layout.addLayout(header)

    def _create_navigation(self):
        """创建侧边导航"""
        sections = [
            ("Modeling", self._build_modeling_section),
            ("Display", self._build_display_section),
            ("Legend", self._build_legend_section),
            ("Tools", self._build_tools_section),
            ("Geochemistry", self._build_geo_section),
        ]

        for name, builder in sections:
            btn = QPushButton(translate(name))
            btn.setCheckable(True)
            btn.setChecked(len(self.section_buttons) == 0)
            btn.clicked.connect(lambda checked, n=name, b=btn: self._show_section(n, b))
            self.nav_layout.addWidget(btn)
            self.section_buttons[name] = btn

        self.nav_layout.addStretch()

    def _create_content(self):
        """创建内容区域"""
        sections = [
            ("Modeling", self._build_modeling_section),
            ("Display", self._build_display_section),
            ("Legend", self._build_legend_section),
            ("Tools", self._build_tools_section),
            ("Geochemistry", self._build_geo_section),
        ]

        for name, builder in sections:
            widget = QWidget()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)

            content = builder()
            scroll.setWidget(content)

            self.content_stack.addWidget(scroll)

    def _show_section(self, name, button):
        """显示指定部分"""
        for n, btn in self.section_buttons.items():
            btn.setChecked(n == name)
        index = list(self.section_buttons.keys()).index(name)
        self.content_stack.setCurrentIndex(index)

    def _create_footer(self, layout):
        """创建底部按钮"""
        footer = QHBoxLayout()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        footer.addWidget(spacer)

        close_btn = QPushButton(translate("Close Panel"))
        close_btn.clicked.connect(self.hide)
        footer.addWidget(close_btn)

        layout.addLayout(footer)

    def _setup_styles(self):
        """设置样式"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.primary_bg};
            }}
            QPushButton {{
                background-color: white;
                border: 1px solid #cbd5e0;
                border-radius: 4px;
                padding: 8px 12px;
                min-width: 80px;
            }}
            QPushButton:checked {{
                background-color: #2563eb;
                color: white;
                border-color: #2563eb;
            }}
            QPushButton:hover {{
                background-color: #f7fafc;
            }}
            QPushButton:checked:hover {{
                background-color: #1d4ed8;
            }}
            QGroupBox {{
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

    def _setup_signals(self):
        """设置信号槽"""
        app_state.register_language_listener(self._refresh_language)

    def _refresh_language(self):
        """刷新语言"""
        current_lang = app_state.language
        for key, widget in self._translations.items():
            text = translate(key, language=current_lang)
            if isinstance(widget, QLabel):
                widget.setText(text)
            elif isinstance(widget, QPushButton):
                widget.setText(text)
            elif hasattr(widget, 'setTitle'):
                widget.setTitle(text)

    def _on_change(self):
        """参数变化回调"""
        if self.callback:
            self.callback()

    def _schedule_slider_callback(self, key):
        """计划滑块回调（防抖）"""
        if key in self._slider_timers:
            self._slider_timers[key].stop()

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._apply_slider_change(key))
        timer.start(self._slider_delay_ms)
        self._slider_timers[key] = timer

    def _apply_slider_change(self, key):
        """应用滑块变化"""
        if key in self._slider_timers:
            self._slider_timers[key].stop()
            del self._slider_timers[key]
        self._on_change()

    # ========== 内容构建方法（待实现）==========

    def _build_modeling_section(self):
        """构建建模部分"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # 实现 Settings 和 Algorithm 内容
        return widget

    def _build_display_section(self):
        """构建显示部分"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # 实现 Style 内容
        return widget

    def _build_legend_section(self):
        """构建图例部分"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        return widget

    def _build_tools_section(self):
        """构建工具部分"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        return widget

    def _build_geo_section(self):
        """构建地球化学部分"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        return widget


def create_control_panel(callback):
    """创建控制面板工厂函数"""
    return Qt5ControlPanel(callback)
```

---

### 3.4 阶段 4：对话框迁移

#### 3.4.1 Qt5 文件选择对话框

**新建文件：`ui/qt5_dialogs/file_dialog.py`**

```python
"""
Qt5 文件选择对话框
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QFrame,
                              QComboBox, QFileDialog, QListWidget,
                              QListWidgetItem, QMessageBox, QLineEdit)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon

from core.localization import translate, available_languages, set_language


class Qt5FileDialog(QDialog):
    """Qt5 文件选择对话框"""

    def __init__(self, default_file=None, parent=None):
        super().__init__(parent)
        self.result = None
        self.selected_file = None
        self.default_file = default_file

        self._language_labels = dict(available_languages())
        self._translations = {}

        self._setup_ui()
        self._setup_signals()
        self._refresh_language()

        if default_file:
            self.selected_file = default_file
            self._update_file_display(default_file)

    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle(translate("Select Data File"))
        self.resize(820, 520)
        self.setMinimumSize(760, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题栏（包含语言选择）
        header = QFrame()
        header.setStyleSheet("background-color: #edf2f7;")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel(translate("Select Data File"))
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a202c;")
        header_layout.addWidget(title)

        # 语言选择
        lang_label = QLabel("Language:")
        header_layout.addWidget(lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.setFixedWidth(150)
        header_layout.addWidget(self.lang_combo)

        layout.addWidget(header)

        # 内容区域
        content = QFrame()
        content.setStyleSheet("background-color: #edf2f7;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)

        subtitle = QLabel(translate(
            "Choose a CSV or Excel file (.csv, .xlsx, .xls) that contains "
            "the isotope dataset you want to explore."
        ))
        subtitle.setStyleSheet("color: #4a5568; font-size: 12px;")
        subtitle.setWordWrap(True)
        content_layout.addWidget(subtitle)

        # 文件选择卡片
        card = QFrame()
        card.setStyleSheet("background-color: white; border-radius: 8px;")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)

        card_header = QLabel(translate("Current selection"))
        card_layout.addWidget(card_header)

        self.file_label = QLabel(translate("No file selected"))
        self.file_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.file_label.setWordWrap(True)
        card_layout.addWidget(self.file_label)

        tip_label = QLabel(translate(
            "Tip: For Excel workbooks, you can pick the sheet in the next step."
        ))
        card_layout.addWidget(tip_label)

        # 按钮行
        btn_row = QHBoxLayout()

        browse_btn = QPushButton(translate("Browse..."))
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        btn_row.addWidget(browse_btn)

        clear_btn = QPushButton(translate("Clear Selection"))
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2563eb;
                border: 1px solid #2563eb;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()
        card_layout.addLayout(btn_row)

        content_layout.addWidget(card)

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

        layout.addWidget(content)
        layout.addWidget(footer)

    def _setup_signals(self):
        """设置信号槽"""
        self.lang_combo.currentIndexChanged.connect(self._on_language_change)

    def _refresh_language(self):
        """刷新语言"""
        current_lang = app_state.language or 'en'

        # 更新语言下拉框
        self.lang_combo.clear()
        for code, name in self._language_labels.items():
            self.lang_combo.addItem(f"{code} - {name}", code)

        # 设置当前语言
        index = self.lang_combo.findData(current_lang)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)

        # 刷新其他翻译
        # ...

    def _on_language_change(self, index):
        """语言变化处理"""
        code = self.lang_combo.currentData()
        if set_language(code):
            app_state.language = code
            self._refresh_language()

    def _update_file_display(self, file_path):
        """更新文件显示"""
        import os
        display_path = os.path.basename(file_path)
        directory = os.path.dirname(file_path)
        self.file_label.setText(f"{display_path}\n{directory}")
        self.file_label.setStyleSheet("color: #1a202c; font-size: 12px; font-weight: bold;")

    def _browse_file(self):
        """浏览文件"""
        file_types = [
            translate("Excel files"): "*.xlsx *.xls",
            translate("CSV files"): "*.csv",
            translate("All files"): "*.*"
        ]

        filters = [f"{name} ({ext})" for name, ext in file_types.items()]

        file_path, selected_filter = QFileDialog.getOpenFileName(
            self,
            translate("Select Data File"),
            self.selected_file or "",
            ";;".join(filters)
        )

        if file_path:
            self.selected_file = file_path
            self._update_file_display(file_path)

    def _ok_clicked(self):
        """确定按钮点击"""
        if not self.selected_file:
            QMessageBox.warning(self, translate("Warning"),
                               translate("Please select a file."))
            return

        self.result = {'file': self.selected_file}
        self.accept()


def get_file_sheet_selection(default_file=None):
    """获取文件和工作表选择"""
    dialog = Qt5FileDialog(default_file)
    if dialog.exec_() == Qt5FileDialog.Accepted:
        return dialog.result
    return None
```

---

#### 3.4.2 其他对话框迁移模板

**新建文件模板：`ui/qt5_dialogs/data_config.py`**

```python
"""
Qt5 数据配置对话框
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QFrame,
                              QScrollArea, QGridLayout, QCheckBox,
                              QGroupBox, QLineEdit, QListWidget,
                              QListWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import pandas as pd


class Qt5DataConfigDialog(QDialog):
    """Qt5 数据配置对话框"""

    def __init__(self, df, default_group_cols=None, default_data_cols=None):
        super().__init__()
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
            translate("Pick one or more categorical columns to color and organize."),
            'group'
        )

        # 数据列选择
        self._build_column_section(
            content_layout,
            translate("Data Columns"),
            translate("Choose numeric measurements for UMAP or t-SNE embeddings."),
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
        toolbar.addWidget(select_all_btn)

        clear_btn = QPushButton(translate("Clear"))
        toolbar.addWidget(clear_btn)

        recommend_btn = QPushButton(translate("Recommend"))
        toolbar.addWidget(recommend_btn)

        toolbar.addStretch()
        card_layout.addLayout(toolbar)

        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel(translate("Search"))
        search_layout.addWidget(search_label)

        search_edit = QLineEdit()
        search_layout.addWidget(search_edit)
        card_layout.addLayout(search_layout)

        # 列列表
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.MultiSelection)
        card_layout.addWidget(list_widget, 1)

        # 填充列
        for col in self.all_columns:
            is_numeric = pd.api.types.is_numeric_dtype(self.df[col])

            if selection_type == 'data' and not is_numeric:
                continue

            dtype_label = translate("numeric") if is_numeric else translate("text")
            display_text = f"{col} ({dtype_label})"

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, col)

            if selection_type == 'group':
                item.setSelected(col in self.selected_group_cols)
            else:
                item.setSelected(col in self.selected_data_cols)

            list_widget.addItem(item)

        parent.addWidget(card, 1)

    def _ok_clicked(self):
        """确定"""
        # 验证选择
        # ...

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
```

---

### 3.5 阶段 5：主入口文件

**新建文件：`main_qt5.py`**

```python
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
```

---

## 4. Tkinter 到 PyQt5 API 对照表

### 4.1 顶层窗口

| Tkinter | PyQt5 | 说明 |
|---------|-------|------|
| `tk.Tk()` | `QMainWindow` | 主窗口 |
| `tk.Toplevel()` | `QDialog` / `QMainWindow` | 弹出窗口 |
| `root.title(text)` | `setWindowTitle(text)` | 设置标题 |
| `root.geometry(wxh)` | `resize(width, height)` | 设置大小 |
| `root.mainloop()` | `app.exec_()` | 事件循环 |
| `root.destroy()` | `close()` | 关闭窗口 |
| `root.withdraw()` | `hide()` | 隐藏窗口 |
| `root.deiconify()` | `show()` | 显示窗口 |

### 4.2 容器组件

| Tkinter | PyQt5 | 说明 |
|---------|-------|------|
| `ttk.Frame` | `QFrame` | 通用容器 |
| `ttk.LabelFrame` | `QGroupBox` | 带标题的分组框 |
| `ttk.Notebook` | `QTabWidget` | 选项卡控件 |

### 4.3 布局管理

```python
# Tkinter - pack
widget.pack(fill=X, expand=True, padx=10, pady=5)

# Tkinter - grid
widget.grid(row=0, column=0, columnspan=2, sticky=EW)

# PyQt5 - QVBoxLayout
layout = QVBoxLayout()
layout.addWidget(widget)
layout.addStretch()
layout.setContentsMargins(10, 10, 10, 10)
layout.setSpacing(5)

# PyQt5 - QHBoxLayout
layout = QHBoxLayout()
layout.addWidget(widget)
layout.addStretch()

# PyQt5 - QGridLayout
layout = QGridLayout()
layout.addWidget(widget, 0, 0, 1, 2)
layout.setColumnStretch(0, 1)
```

### 4.4 标签和按钮

| Tkinter | PyQt5 | 说明 |
|---------|-------|------|
| `ttk.Label` | `QLabel` | 文本显示 |
| `ttk.Button` | `QPushButton` | 按钮 |
| `ttk.Button(..., image=photo)` | `QPushButton(icon=QIcon(...))` | 图标按钮 |
| `command=callback` | `clicked.connect(callback)` | 点击事件 |
| `widget.config(text=...)` | `setText(...)` | 设置文本 |

### 4.5 输入控件

| Tkinter | PyQt5 | 说明 |
|---------|-------|------|
| `ttk.Entry` | `QLineEdit` | 单行输入 |
| `ttk.Combobox` | `QComboBox` | 下拉选择 |
| `ttk.Spinbox` | `QSpinBox` / `QDoubleSpinBox` | 数值输入 |
| `ttk.Checkbutton` | `QCheckBox` | 复选框 |
| `ttk.Radiobutton` | `QRadioButton` | 单选按钮 |
| `ttk.Scale` | `QSlider` | 滑块 |
| `textvariable=var` | `textChanged.connect()` | 文本变化信号 |

### 4.6 列表和表格

| Tkinter | PyQt5 | 说明 |
|---------|-------|------|
| `tk.Listbox` | `QListWidget` | 列表 |
| `tk.Treeview` | `QTreeWidget` | 树形视图 |
| `ttk.Treeview` | `QTableWidget` | 表格 |

### 4.7 滚动条

```python
# Tkinter
scrollbar = ttk.Scrollbar(parent, orient=VERTICAL, command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

# PyQt5
scrollbar = QScrollBar(Qt.Vertical, parent)
scrollbar.valueChanged.connect(canvas.setYScroll)
```

### 4.8 进度指示

| Tkinter | PyQt5 | 说明 |
|---------|-------|------|
| `ttk.Progressbar` | `QProgressBar` | 进度条 |
| `ttk.Progressbar(..., mode='determinate')` | `QProgressBar()` | 确定模式 |

### 4.9 文件对话框

```python
# Tkinter
from tkinter import filedialog
file_path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])

# PyQt5
from PyQt5.QtWidgets import QFileDialog
file_path, _ = QFileDialog.getOpenFileName(
    self, "Title", "", "Excel (*.xlsx);;All Files (*)"
)
```

### 4.10 消息框

```python
# Tkinter
from tkinter import messagebox
messagebox.showinfo("Title", "Message")
messagebox.showwarning("Title", "Message")
messagebox.showerror("Title", "Message")
messagebox.askyesno("Title", "Message?")

# PyQt5
from PyQt5.QtWidgets import QMessageBox
QMessageBox.information(self, "Title", "Message")
QMessageBox.warning(self, "Title", "Message")
QMessageBox.critical(self, "Title", "Message")
QMessageBox.question(self, "Title", "Message?") == QMessageBox.Yes
```

### 4.11 样式

```python
# Tkinter
style = ttk.Style()
style.configure('Accent.TButton', background="#2563eb")

# PyQt5 - QSS (Qt Style Sheets)
stylesheet = """
QPushButton {
    background-color: #2563eb;
    color: white;
    border-radius: 4px;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
"""
widget.setStyleSheet(stylesheet)
```

### 4.12 定时器

```python
# Tkinter
self.root.after(1000, callback)

# PyQt5
QTimer.singleShot(1000, callback)
# 或
timer = QTimer()
timer.timeout.connect(callback)
timer.start(1000)  # 重复执行
```

### 4.13 变量绑定

```python
# Tkinter BooleanVar
var = tk.BooleanVar(value=True)
checkbox.configure(variable=var)
value = var.get()
var.set(False)

# PyQt5
checkbox = QCheckBox()
checkbox.setChecked(True)
value = checkbox.isChecked()
checkbox.toggled.connect(handler)  # 信号

# Tkinter StringVar
var = tk.StringVar(value="text")
entry.configure(textvariable=var)
value = var.get()
var.set("new text")

# PyQt5
lineedit = QLineEdit()
lineedit.setText("text")
value = lineedit.text()
lineedit.textChanged.connect(handler)
```

### 4.14 国际化

```python
# Tkinter - 自定义注册
def _register_translation(self, widget, key, attr='text'):
    self._translations.append({'widget': widget, 'key': key, 'attr': attr})

def _refresh_language(self):
    for item in self._translations:
        text = translate(item['key'])
        item['widget'].configure(text=text)

# PyQt5 - 内置支持
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel()

    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.label.setText(self.tr("Hello"))
```

---

## 5. 关键迁移注意事项

### 5.1 国际化处理

PyQt5 提供内置的国际化支持，使用 `QApplication.translate()` 和 `tr()` 方法：

```python
# 方法1: 使用 tr() 方法（推荐用于类内部）
class MyWidget(QWidget):
    def __init__(self):
        self.label = QLabel(self.tr("Hello World"))

# 方法2: 使用全局 translate() 函数
from core.localization import translate
text = translate("Control Panel")

# 方法3: 使用 QApplication.translate()（用于外部函数）
from PyQt5.QtWidgets import QApplication
text = QApplication.translate("MyContext", "Cancel")
```

### 5.2 布局嵌套

PyQt5 强烈推荐使用布局嵌套，而非单一布局：

```python
# 不推荐：复杂网格
grid = QGridLayout()
for i in range(10):
    for j in range(10):
        grid.addWidget(QPushButton(f"Button {i}-{j}"), i, j)

# 推荐：分组布局
main_layout = QVBoxLayout()

# 顶部区域
top_layout = QHBoxLayout()
top_layout.addWidget(widget1)
top_layout.addWidget(widget2)
top_frame = QFrame()
top_frame.setLayout(top_layout)
main_layout.addWidget(top_frame)

# 底部区域
bottom_layout = QHBoxLayout()
bottom_layout.addWidget(widget3)
bottom_layout.addWidget(widget4)
bottom_frame = QFrame()
bottom_frame.setLayout(bottom_layout)
main_layout.addWidget(bottom_frame)

self.setLayout(main_layout)
```

### 5.3 信号槽连接

```python
# 基本连接
button.clicked.connect(self.on_click)

# 带参数
button.clicked.connect(lambda checked=False, id=item_id: self.handle_item(id))

# 断开连接
button.clicked.disconnect(self.on_click)

# 自定义信号
from PyQt5.QtCore import pyqtSignal
class MyWidget(QWidget):
    value_changed = pyqtSignal(int, str)  # 信号定义

    def __init__(self):
        self.value_changed.connect(self.on_change)

    def on_change(self, value, name):
        print(f"{name}: {value}")
```

### 5.4 DPI 感知配置

```python
# main.py 或入口文件
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
```

### 5.5 窗口状态保存

```python
from PyQt5.QtCore import QSettings

class MainWindow(QMainWindow):
    def closeEvent(self, event):
        settings = QSettings("Company", "AppName")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())
        event.accept()

    def restoreState(self):
        settings = QSettings("Company", "AppName")
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.contains("state"):
            self.restoreState(settings.value("state"))
```

---

## 6. 工作量评估

### 6.1 按阶段统计

| 阶段 | 文件数 | 预估工作量 |
|------|--------|------------|
| 1. 依赖配置 | 1 | 0.5 天 |
| 2. 核心架构 | 3 | 2-3 天 |
| 3. 控制面板 | 1 | 5-7 天 |
| 4. 对话框 (8个) | 8 | 8-12 天 |
| 5. Mixins 迁移 | 4 | 3-4 天 |
| 6. Tabs 迁移 | 6 | 4-6 天 |
| 7. 入口文件 | 1 | 0.5 天 |
| **合计** | **24** | **23-33 天** |

### 6.2 按文件详细估算

| 文件 | 复杂度 | 预估行数 |
|------|--------|----------|
| `ui/qt5_app.py` | 中 | 150 |
| `ui/qt5_main_window.py` | 中 | 200 |
| `ui/qt5_control_panel.py` | 高 | 400 |
| `ui/qt5_dialogs/file_dialog.py` | 中 | 200 |
| `ui/qt5_dialogs/data_config.py` | 高 | 250 |
| `ui/qt5_dialogs/sheet_dialog.py` | 低 | 100 |
| `ui/qt5_dialogs/two_d_dialog.py` | 中 | 150 |
| `ui/qt5_dialogs/three_d_dialog.py` | 中 | 150 |
| `ui/qt5_dialogs/ternary_dialog.py` | 中 | 150 |
| `ui/qt5_dialogs/legend_dialog.py` | 中 | 150 |
| `ui/qt5_dialogs/progress_dialog.py` | 低 | 80 |
| `main_qt5.py` | 低 | 30 |

---

## 7. 风险和缓解措施

### 7.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| API 差异导致迁移遗漏 | 中 | 创建迁移检查清单逐项验证 |
| 样式不一致 | 低 | 定义统一的 QSS 样式表 |
| 事件处理逻辑差异 | 中 | 编写单元测试覆盖核心功能 |
| 国际化失效 | 低 | 迁移后全语言覆盖测试 |

### 7.2 项目风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 工作量超出预期 | 高 | 分阶段实施，每阶段评审 |
| 新 Bug 引入 | 中 | 保留 Tkinter 版本作为备选 |
| 性能下降 | 低 | Qt5 通常比 Tkinter 更高效 |
| 第三方依赖问题 | 中 | 使用 requirements.txt 锁定版本 |

### 7.3 质量保证

1. **功能测试**
   - 迁移后运行所有现有测试
   - 手动测试核心功能流程

2. **UI 测试**
   - 检查所有对话框布局
   - 验证样式一致性
   - 测试不同分辨率

3. **国际化测试**
   - 中英文切换测试
   - 验证所有标签翻译

---

## 8. 迁移检查清单

### 8.1 准备阶段

- [ ] 创建迁移分支 `feature/pyqt5-migration`
- [ ] 备份当前 Tkinter 代码
- [ ] 添加 PyQt5 依赖
- [ ] 设置 CI/CD 流水线

### 8.2 核心架构

- [ ] `core/app.py` 后端切换为 Qt5Agg
- [ ] 创建 `ui/qt5_app.py`
- [ ] 创建 `ui/qt5_main_window.py`
- [ ] 验证 matplotlib 集成

### 8.3 控制面板

- [ ] 创建 `Qt5ControlPanel` 类
- [ ] 迁移侧边导航
- [ ] 迁移 Modeling 部分（Settings + Algorithm）
- [ ] 迁移 Display 部分（Style）
- [ ] 迁移 Legend 部分
- [ ] 迁移 Tools 部分
- [ ] 迁移 Geochemistry 部分
- [ ] 实现滑块防抖机制
- [ ] 实现国际化刷新

### 8.4 对话框

- [ ] 迁移 `Qt5FileDialog`
- [ ] 迁移 `Qt5SheetDialog`
- [ ] 迁移 `Qt5DataConfigDialog`
- [ ] 迁移 `Qt5TwoDDialog`
- [ ] 迁移 `Qt5ThreeDDialog`
- [ ] 迁移 `Qt5TernaryDialog`
- [ ] 迁移 `Qt5LegendDialog`
- [ ] 迁移 `Qt5ProgressDialog`

### 8.5 测试验证

- [ ] 功能测试：文件加载流程
- [ ] 功能测试：数据配置流程
- [ ] 功能测试：绘图渲染
- [ ] 功能测试：参数调整
- [ ] 功能测试：数据导出
- [ ] UI 测试：窗口布局
- [ ] UI 测试：样式一致性
- [ ] 国际化测试：英文界面
- [ ] 国际化测试：中文界面
- [ ] 性能测试：内存使用
- [ ] 性能测试：启动时间

### 8.6 部署准备

- [ ] 更新 PyInstaller 配置
- [ ] 更新 README
- [ ] 更新依赖说明
- [ ] 创建迁移完成报告

---

## 附录 A：样式表示例

```css
/* global.qss - 全局样式 */

/* 基础部件 */
QWidget {
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 9pt;
    background-color: #edf2f7;
    color: #1a202c;
}

/* 主窗口 */
QMainWindow {
    background-color: #edf2f7;
}

/* 按钮 */
QPushButton {
    background-color: white;
    border: 1px solid #cbd5e0;
    border-radius: 4px;
    padding: 6px 12px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #f7fafc;
    border-color: #a0aec0;
}

QPushButton:pressed {
    background-color: #edf2f7;
}

QPushButton#AccentButton {
    background-color: #2563eb;
    color: white;
    border: none;
}

QPushButton#AccentButton:hover {
    background-color: #1d4ed8;
}

/* 分组框 */
QGroupBox {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

/* 输入框 */
QLineEdit, QTextEdit {
    border: 1px solid #cbd5e0;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: white;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #2563eb;
}

/* 下拉框 */
QComboBox {
    border: 1px solid #cbd5e0;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: white;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

/* 复选框 */
QCheckBox {
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #cbd5e0;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #2563eb;
}

/* 滑块 */
QSlider::groove:horizontal {
    height: 6px;
    background: #e2e8f0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #2563eb;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

/* 进度条 */
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

/* 滚动条 */
QScrollBar:vertical {
    width: 12px;
    background: #f7fafc;
}

QScrollBar::handle:vertical {
    min-height: 30px;
    background: #cbd5e0;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background: #a0aec0;
}

/* 选项卡 */
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    border-radius: 4px;
}

QTabBar::tab {
    padding: 8px 16px;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    background-color: #f7fafc;
}

QTabBar::tab:selected {
    background-color: white;
    font-weight: bold;
}
```

---

## 附录 B：快速参考

### 创建项目结构

```
ui/
├── __init__.py
├── qt5_app.py              # 应用程序入口
├── qt5_main_window.py      # 主窗口
├── qt5_control_panel.py    # 控制面板
└── qt5_dialogs/
    ├── __init__.py
    ├── file_dialog.py      # 文件选择
    ├── sheet_dialog.py     # 工作表选择
    ├── data_config.py      # 数据配置
    ├── two_d_dialog.py    # 2D 设置
    ├── three_d_dialog.py   # 3D 设置
    ├── ternary_dialog.py   # 三元图设置
    ├── legend_dialog.py    # 图例设置
    └── progress_dialog.py  # 进度条
```

### 常用导入

```python
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit,
    QComboBox, QCheckBox, QRadioButton,
    QSlider, QProgressBar,
    QGroupBox, QFrame,
    QTabWidget, QStackedWidget,
    QScrollArea, QSplitter,
    QListWidget, QTreeWidget, QTableWidget,
    QAction, QMenu, QMenuBar, QToolBar,
    QStatusBar, QDockWidget,
    QFileDialog, QMessageBox, QDialog,
    QInputDialog, QColorDialog, QFontDialog
)

from PyQt5.QtCore import (
    Qt, QSize, QTimer, QPoint,
    pyqtSignal, pyqtSlot, QMetaObject,
    QSettings, QTranslator, QLocale
)

from PyQt5.QtGui import (
    QIcon, QFont, QColor, QPalette,
    QPixmap, QImage, QPainter,
    QAction, QKeySequence
)
```

---

> 文档版本历史
> - v1.0 (2025-02-09): 初始版本，完整迁移方案
