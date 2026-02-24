# 项目架构总览与改进计划

## 项目概况

**Isotopes Analyse** — 基于 PyQt5 的铅同位素地球化学数据分析与可视化桌面应用。

| 指标 | 数值 |
|------|------|
| Python 代码总量 | ~18,558 行 |
| 模块数 | 5 个主模块 |
| Python 文件数 | 47 个 |
| 对话框数 | 11 个 |
| 支持算法 | UMAP, t-SNE, PCA, RobustPCA, V1V2 |
| 图类型 | 8+ 种 |
| 语言支持 | 中文/英文 |

---

## 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                      main.py (入口)                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  core/   │  │     ui/      │  │  visualization/   │  │
│  │          │  │              │  │                   │  │
│  │ state    │←─│ app          │──│ plotting          │  │
│  │ config   │  │ main_window  │  │ plotting_embed    │  │
│  │ session  │  │ control_panel│  │ events            │  │
│  │ locale   │  │ dialogs/     │  │ plotting_style    │  │
│  │ cache    │  │  (11 个)     │  │ style_manager     │  │
│  └──────────┘  └──────────────┘  │ plotting_kde      │  │
│       ↑                          │ plotting_analysis  │  │
│       │        ┌──────────┐      │ plotting_data     │  │
│       └────────│  data/   │──────│ line_styles       │  │
│                │          │      └───────────────────┘  │
│                │ loader   │                             │
│                │ geochem  │      ┌───────────────────┐  │
│                │ endmember│      │     utils/        │  │
│                │ prov_ml  │      │ logger            │  │
│                │ mixing   │      └───────────────────┘  │
│                └──────────┘                             │
└─────────────────────────────────────────────────────────┘
```

### 数据流

```
Excel/CSV 文件
  → data/loader.py (加载 + 列映射)
  → core/state.py (app_state.df_global)
  → visualization/plotting.py (嵌入计算 + 渲染)
  → matplotlib Figure (app_state.fig / app_state.ax)
  → ui/main_window.py (画布显示)
  → visualization/events.py (交互)
  → core/session.py (会话保存)
```

### 设计模式

| 模式 | 应用位置 |
|------|----------|
| 单例 | AppState, GeochemistryEngine, StyleManager |
| 观察者 | 语言变更监听器 |
| 懒加载 | sklearn, umap-learn, seaborn, xgboost |
| LRU 缓存 | 嵌入计算缓存 |
| 调度器 | plot_embedding() 根据 algorithm 分发 |
| 回调 | control_panel → on_slider_change → 重绘 |

---

## 各模块文档索引

| 模块 | 文档路径 | 行数 |
|------|----------|------|
| core/ | [docs/core.md](core.md) | 905 |
| data/ | [docs/data.md](data.md) | 2,410 |
| ui/ | [docs/ui.md](ui.md) | 9,422 |
| visualization/ | [docs/visualization.md](visualization.md) | 3,728 |
| utils/ | [docs/utils.md](utils.md) | 108 |

---

## 改进计划

### 第一优先级: 代码结构

#### 1.1 拆分 control_panel.py (5,700 行) — ✅ 已完成

**现状:** 单个文件包含 6 个标签页的全部逻辑，100+ 方法。

**目标结构:**
```
ui/
├── control_panel.py          # 组装逻辑 + create_section_dialog()
├── panels/
│   ├── __init__.py
│   ├── data_panel.py         # 数据标签页
│   ├── display_panel.py      # 显示标签页
│   ├── analysis_panel.py     # 分析标签页
│   ├── export_panel.py       # 导出标签页
│   ├── legend_panel.py       # 图例标签页
│   └── geo_panel.py          # 地球化学标签页
```

**已完成内容:**
- 每个 `_build_xxx_section()` 拆分为独立面板类
- 相关 `_on_xxx_change()` 方法迁移到对应面板
- `control_panel.py` 仅保留组装与 `create_section_dialog()`
- `_on_style_change()` 下沉至 `BasePanel` (跨面板共享)

#### 1.2 合并 plotting.py + plotting_embed.py

**现状:** 两个文件有大量重复代码和循环导入风险。

**目标结构:**
```
visualization/
├── plotting_core.py      # 嵌入计算 + 工具函数
├── plotting_render.py    # 散点/图例/标题渲染
├── plotting_geo.py       # 地球化学叠加 (模型曲线, 等时线, 古等时线)
├── plotting_ternary.py   # 三元图逻辑
```

#### 1.3 拆分 geochemistry.py (1,369 行)

**目标结构:**
```
data/
├── geochemistry/
│   ├── __init__.py       # 导出公共 API
│   ├── engine.py         # GeochemistryEngine + 预设模型
│   ├── age.py            # 年龄计算
│   ├── delta.py          # Delta + V1V2
│   ├── source.py         # 源区参数反演
│   └── isochron.py       # 等时线工具
```

---

### 第二优先级: 功能改进

#### 2.1 后台计算 + 进度指示

**现状:** UMAP/t-SNE 在大数据集上阻塞 UI。

**方案:**
```python
class EmbeddingWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(np.ndarray)

    def run(self):
        # 在后台线程计算嵌入
        result = get_umap_embedding(self.params)
        self.finished.emit(result)
```

#### 2.2 ML 管线增强

- 添加交叉验证 (cross_val_score)
- XGBoost tree_method 改为 `'hist'`
- 支持 per-label 阈值
- 添加训练/测试集划分报告

#### 2.3 语言切换优化

**现状:** `_rebuild_ui()` 销毁并重建所有控件。

**方案:** 改为遍历控件树，仅更新文本:
```python
def _update_translations(self):
    for group_box in self.findChildren(QGroupBox):
        key = group_box.property('translate_key')
        if key:
            group_box.setTitle(translate(key))
```

---

### 第三优先级: 代码质量

#### 3.1 消除重复代码

| 重复项 | 位置 | 处理 |
|--------|------|------|
| `_resolve_isochron_errors()` | plotting.py + events.py | 提取到 data/geochemistry/ |
| `_build_marker_icon()` | main_window.py + control_panel.py | 提取到 utils/icons.py |
| 图例布局逻辑 | plotting.py + plotting_style.py | 统一到 plotting_style.py |

#### 3.2 国际化完善

- events.py 中硬编码中文字符串改用 `translate()`
- 统一 geochemistry.py 中的中英文注释

#### 3.3 类型注解

为核心模块添加类型注解:
```python
# 优先级: core/ > data/ > visualization/ > ui/
def calculate_single_stage_age(
    Pb206_204_S: np.ndarray,
    Pb207_204_S: np.ndarray,
    params: dict | None = None,
    initial_age: float | None = None
) -> np.ndarray: ...
```

#### 3.4 AppState 拆分

```python
class AppState:
    def __init__(self):
        self.data = DataState()           # df_global, data_cols, group_cols
        self.algorithm = AlgorithmState() # algorithm, params, cache
        self.visual = VisualState()       # fig, ax, scatter_collections
        self.geochem = GeochemState()     # model, line_styles, paleoisochrons
        self.style = StyleState()         # colors, fonts, grid, ticks
        self.interaction = InteractionState()  # selection, tooltip
```

---

### 第四优先级: 基础设施

#### 4.1 单元测试

```
tests/
├── test_geochemistry.py    # 年龄计算、Delta、V1V2
├── test_cache.py           # 嵌入缓存
├── test_session.py         # 会话持久化
├── test_localization.py    # 翻译系统
├── test_endmember.py       # 端元识别
├── test_mixing.py          # 混合模型
├── test_provenance_ml.py   # ML 管线
```

#### 4.2 配置外部化

支持用户配置文件 `~/.isotopes_analysis/config.json`:
```json
{
  "default_language": "zh",
  "figure_dpi": 150,
  "embedding_cache_size": 16,
  "xgboost_tree_method": "hist"
}
```

#### 4.3 日志改进

- 添加模块名和行号到日志格式
- LoggerWriter 添加 `fileno()` 支持 faulthandler
- 统一日志级别使用 (移除字符串前缀 `[INFO]`)

---

## 已知 Bug 与技术债

| 问题 | 位置 | 状态 |
|------|------|------|
| `_on_style_change` 初始化期间崩溃 | control_panel.py:3665 | ✅ 已修复 (添加 `_is_initialized` 守卫) |
| `create_section_dialog` 未初始化属性 | control_panel.py:5614 | ✅ 已修复 (添加 `_reset_ui_state()`) |
| numba 日志过长 | utils/logger.py | ✅ 已修复 (设置 WARNING 级别) |
| `_reset_ui_state` 重复赋值 | control_panel.py:285-296 | 待修复 |
| 全局 widget 引用 (slider_n 等) | state.py:332-344 | 待清理 |
| 循环导入风险 | plotting.py ↔ plotting_embed.py | 待重构 |
| 控制面板禁用但代码保留 | app.py:322 | 待清理 |

---

## 开发约定

### 文件命名
- 模块文件: `snake_case.py`
- 类名: `PascalCase`
- 函数/方法: `snake_case`
- 私有方法: `_leading_underscore`

### 导入顺序
1. 标准库
2. 第三方库
3. 本项目模块

### 日志约定
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Message")       # 信息
logger.warning("Message")    # 警告
logger.error("Message")      # 错误
logger.debug("Message")      # 调试
logger.exception("Message")  # 错误 + 堆栈
```

### 翻译约定
- 所有用户可见字符串使用 `translate("key")`
- 翻译键使用英文原文
- 新增翻译需同时更新 `locales/zh.json` 和 `locales/en.json`
