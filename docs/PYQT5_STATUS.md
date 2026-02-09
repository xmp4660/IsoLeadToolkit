# PyQt5 迁移 - 使用说明

## 已完成的工作

### 核心文件
- ✅ `pyproject.toml` - 添加 PyQt5 依赖
- ✅ `main_qt5.py` - Qt5 版本主入口
- ✅ `ui/qt5_app.py` - Qt5 应用程序类
- ✅ `ui/qt5_main_window.py` - Qt5 主窗口
- ✅ `ui/qt5_control_panel.py` - Qt5 控制面板（基础版）
- ✅ `data/qt5_loader.py` - 使用 Qt5 对话框的数据加载器

### 对话框
- ✅ `ui/qt5_dialogs/file_dialog.py` - 文件选择对话框
- ✅ `ui/qt5_dialogs/sheet_dialog.py` - 工作表选择对话框
- ✅ `ui/qt5_dialogs/data_config.py` - 数据配置对话框
- ✅ `ui/qt5_dialogs/progress_dialog.py` - 进度对话框

## 安装依赖

```bash
# 安装 PyQt5
pip install pyqt5>=5.15.10 pyqt5-qt5>=5.15.11

# 或使用 uv（推荐）
uv pip install pyqt5>=5.15.10 pyqt5-qt5>=5.15.11
```

## 测试导入

```bash
python test_qt5_imports.py
```

## 运行应用

```bash
python main_qt5.py
```

## 当前状态

### 已实现功能
1. **基础架构**
   - Qt5 应用程序生命周期管理
   - 主窗口框架
   - Matplotlib 集成（Qt5Agg 后端）
   - 会话状态保存/恢复

2. **对话框**
   - 文件选择（支持 CSV/Excel）
   - 工作表选择
   - 数据列配置
   - 进度显示

3. **控制面板（基础版）**
   - 侧边导航
   - 算法选择（UMAP/t-SNE/PCA）
   - UMAP 参数调整（n_neighbors）
   - 点大小调整
   - 分节布局（Modeling/Display/Legend/Tools/Geochemistry）

### 待完善功能

1. **控制面板扩展**
   - [ ] 完整的 UMAP 参数（min_dist, metric, random_state）
   - [ ] t-SNE 参数（perplexity, learning_rate）
   - [ ] PCA 参数
   - [ ] 渲染模式切换（2D/3D/Ternary）
   - [ ] 样式配置
   - [ ] 图例管理
   - [ ] 地球化学参数

2. **其他对话框**
   - [ ] 2D 列选择对话框
   - [ ] 3D 列选择对话框
   - [ ] 三元图对话框
   - [ ] 图例编辑对话框

3. **功能完善**
   - [ ] 国际化翻译刷新
   - [ ] 工具栏图标
   - [ ] 快捷键支持
   - [ ] 主题切换

## 与 Tkinter 版本对比

| 特性 | Tkinter 版本 | PyQt5 版本 | 状态 |
|------|-------------|-----------|------|
| 文件加载 | ✅ | ✅ | 完成 |
| 数据配置 | ✅ | ✅ | 完成 |
| 基础绘图 | ✅ | ✅ | 完成 |
| 控制面板 | ✅ | ⚠️ | 部分完成 |
| 参数调整 | ✅ | ⚠️ | 部分完成 |
| 导出功能 | ✅ | ❌ | 待实现 |
| 选择工具 | ✅ | ❌ | 待实现 |
| 地球化学 | ✅ | ❌ | 待实现 |

## 架构说明

### 文件组织
```
ui/
├── qt5_app.py              # 应用程序入口
├── qt5_main_window.py      # 主窗口（包含 matplotlib 画布）
├── qt5_control_panel.py    # 控制面板
└── qt5_dialogs/            # 对话框模块
    ├── file_dialog.py      # 文件选择
    ├── sheet_dialog.py     # 工作表选择
    ├── data_config.py      # 数据配置
    └── progress_dialog.py  # 进度显示
```

### 关键设计

1. **Matplotlib 集成**
   - 使用 `FigureCanvasQTAgg` 嵌入 matplotlib 图形
   - 使用 `NavigationToolbar2QT` 提供工具栏
   - 后端设置为 `Qt5Agg`

2. **状态管理**
   - 继续使用 `core.state.app_state` 全局状态
   - 通过 `QSettings` 保存窗口状态
   - 通过 `save_session_params` 保存会话参数

3. **信号槽机制**
   - 使用 `pyqtSignal` 定义自定义信号
   - 使用 `connect()` 连接信号和槽
   - 使用 `QTimer` 实现防抖

4. **样式系统**
   - 使用 QSS（Qt Style Sheets）定义样式
   - 保持与 Tkinter 版本一致的配色方案

## 下一步工作

### 优先级 1（核心功能）
1. 完善控制面板的所有参数控制
2. 实现数据导出功能
3. 实现选择工具（矩形选择、椭圆选择）

### 优先级 2（增强功能）
1. 实现剩余对话框（2D/3D/Ternary/Legend）
2. 完善国际化支持
3. 添加工具栏图标

### 优先级 3（优化）
1. 性能优化
2. 错误处理增强
3. 用户体验改进

## 已知问题

1. 控制面板功能不完整（仅实现基础参数）
2. 国际化翻译刷新未完全实现
3. 部分对话框尚未迁移

## 贡献指南

如需继续开发，请参考：
- [docs/PYQT5_MIGRATION_PLAN.md](docs/PYQT5_MIGRATION_PLAN.md) - 完整迁移方案
- 原 Tkinter 版本代码作为参考

## 测试

```bash
# 测试导入
python test_qt5_imports.py

# 运行应用（需要数据文件）
python main_qt5.py
```

## 许可证

与主项目保持一致
