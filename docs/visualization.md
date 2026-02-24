# visualization/ 模块开发文档

## 模块概述

`visualization/` 是应用的渲染引擎，负责所有图形绑定、交互事件、样式管理。支持 8+ 种图类型。

**文件清单 (3,728 行)**

| 文件 | 行数 | 职责 |
|------|------|------|
| `__init__.py` | 89 | 模块入口，导出公共 API |
| `plotting.py` | 1,216 | 主渲染调度器 + 嵌入计算 |
| `plotting_embed.py` | 1,336 | 嵌入渲染 (从 plotting.py 拆出) |
| `events.py` | 1,057 | 交互事件 (hover, 选择, 图例点击) |
| `plotting_style.py` | 320 | 绘图样式 + 图例布局 |
| `style_manager.py` | 224 | 调色板 + 字体 + UI 主题 |
| `plotting_analysis_qt.py` | 261 | 诊断图 (scree, loadings, 相关性) |
| `plotting_kde.py` | 127 | KDE 叠加渲染 |
| `plotting_data.py` | 63 | 数据准备工具 (懒加载 ML 依赖) |
| `line_styles.py` | 22 | 线型解析工具 |

---

## 渲染管线

```
用户操作 (控制面板/菜单)
  ↓
on_slider_change() [events.py]
  ↓
判断 render_mode:
  ├─ UMAP/tSNE/PCA/RobustPCA/V1V2/PB_EVOL_76/86/PB_MU_AGE/PB_KAPPA_AGE/TERNARY
  │    → plot_embedding()
  ├─ 2D → plot_2d_data()
  └─ 3D → plot_3d_data()
  ↓
计算/获取嵌入:
  ├─ get_umap_embedding() → UMAP + LRU 缓存
  ├─ get_tsne_embedding() → t-SNE + perplexity 验证
  ├─ get_pca_embedding() → PCA + 方差追踪
  ├─ get_robust_pca_embedding() → MinCovDet / PCA 回退
  ├─ V1V2 → geochemistry.calculate_all_parameters()
  ├─ TERNARY → 原始数据 + 拉伸
  └─ PB_EVOL → 原始 Pb 比值
  ↓
构建调色板 + 准备数据:
  ├─ _build_group_palette() → 稳定颜色映射
  ├─ 按 visible_groups 过滤
  └─ 添加嵌入列到 DataFrame
  ↓
渲染散点:
  ├─ 按组循环: ax.scatter(color, marker, size, alpha)
  ├─ 存储索引映射 (artist_to_sample, sample_coordinates)
  └─ 存储 scatter_collections
  ↓
可选: KDE 叠加
  ├─ sns.kdeplot() (主图)
  └─ draw_marginal_kde() (上/右边际)
  ↓
可选: 地球化学叠加 (PB_EVOL_76/86)
  ├─ _draw_model_curves() → SK 模型曲线
  ├─ _draw_isochron_overlays() → York 回归线 + 年龄标签
  ├─ _draw_paleoisochrons() → 参考古等时线
  └─ _draw_model_age_lines() → 模式年龄构造线
  ↓
渲染图例:
  ├─ _legend_layout_config() → 位置/bbox
  ├─ _legend_columns_for_layout() → 自动列数
  ├─ _style_legend() → 样式
  └─ _notify_legend_panel() → 更新主窗口图例面板
  ↓
恢复选择叠加:
  ├─ refresh_selection_overlay() → 高亮选中点
  └─ draw_confidence_ellipse() → 95% 置信椭圆
  ↓
应用样式:
  ├─ _apply_current_style() → 全局 rcParams
  ├─ _enforce_plot_style() → 坐标轴级别
  └─ _apply_axis_text_style() → 标签/标题
  ↓
fig.canvas.draw_idle()
```

---

## 1. plotting.py — 主渲染调度器

### 职责
嵌入计算、主渲染函数、地球化学叠加、三元图支持。

### 嵌入计算函数

```python
def get_umap_embedding(params: dict) -> np.ndarray
    """计算 UMAP 嵌入，带 LRU 缓存"""
    # 懒加载 umap-learn
    # 缓存键: (algorithm, params, subset_key, data_signature)

def get_tsne_embedding(params: dict) -> np.ndarray
    """计算 t-SNE 嵌入"""
    # perplexity 自动调整: min(perplexity, n_samples/3 - 1)

def get_pca_embedding(params: dict) -> np.ndarray
    """计算 PCA 嵌入"""
    # 存储 explained_variance_ratio 到 app_state.last_pca_variance
    # 存储 components 到 app_state.last_pca_components

def get_robust_pca_embedding(params: dict) -> np.ndarray
    """计算 Robust PCA (MinCovDet)"""
    # support_fraction 参数
    # MinCovDet 失败时回退到标准 PCA

def get_embedding(algorithm: str, ...) -> np.ndarray
    """调度器: 根据 algorithm 调用对应函数"""
```

### 主渲染函数

```python
def plot_embedding(group_col, algorithm, umap_params=None, tsne_params=None,
                   pca_params=None, robust_pca_params=None, size=60) -> bool
```

**支持的 algorithm 值:**
| 值 | 图类型 |
|----|--------|
| `UMAP` | UMAP 降维散点图 |
| `tSNE` | t-SNE 降维散点图 |
| `PCA` | PCA 降维散点图 |
| `RobustPCA` | Robust PCA 降维散点图 |
| `V1V2` | V1-V2 判别图 |
| `TERNARY` | 三元图 |
| `PB_EVOL_76` | 206Pb/204Pb vs 207Pb/204Pb 演化图 |
| `PB_EVOL_86` | 206Pb/204Pb vs 208Pb/204Pb 演化图 |
| `PB_MU_AGE` | μ vs Age 图 |
| `PB_KAPPA_AGE` | κ vs Age 图 |

```python
def plot_2d_data(group_col, data_columns, size=60, show_kde=False) -> bool
    """原始 2D 散点图 (用户选择的两列)"""

def plot_3d_data(group_col, data_columns, size=60) -> bool
    """原始 3D 散点图 (用户选择的三列)"""
```

### 地球化学叠加函数

```python
def _draw_model_curves(ax, algorithm, params_list)
    """绘制 Stacey-Kramers 模型曲线 + 年龄标记点"""

def _draw_isochron_overlays(ax, algorithm)
    """绘制等时线回归线 + 年龄/MSWD 标签"""

def _draw_selected_isochron(ax)
    """高亮当前选中的等时线"""

def _draw_paleoisochrons(ax, algorithm, ages, params)
    """绘制参考古等时线 (0-3000 Ma)"""

def _draw_model_age_lines(ax, pb206, pb207, params)
    """绘制 206-207 模式年龄构造线"""

def _draw_model_age_lines_86(ax, pb206, pb207, pb208, params)
    """绘制 206-208 模式年龄构造线"""

def _draw_equation_overlays(ax)
    """绘制自定义方程/线叠加"""
```

### 三元图支持

```python
def _apply_ternary_stretch(t_vals, l_vals, r_vals)
    """应用拉伸模式 (power/minmax/hybrid)"""

def calculate_auto_ternary_factors()
    """基于几何均值的自动居中因子"""
```

### 工具函数

```python
def _ensure_axes(dimensions=2)
    """创建/切换 2D/3D 坐标轴"""

def _build_group_palette(unique_cats) -> dict
    """构建稳定的组→颜色映射"""
    # 保持已有颜色，仅为新组分配新颜色

def _get_subset_dataframe() -> tuple[DataFrame, str]
    """返回活动子集或完整数据"""

def _get_pb_columns(columns) -> tuple[str, str, str]
    """查找 Pb 同位素比值列 (206/204, 207/204, 208/204)"""

def _find_age_column(columns) -> str | None
    """查找年龄列 (用于 Mu/Kappa 图)"""
```

---

## 2. plotting_embed.py — 嵌入渲染

### 职责
从 plotting.py 拆出的嵌入渲染逻辑。

### 与 plotting.py 的关系
- 导入 plotting.py 的辅助函数
- 提供相同的公共 API (`plot_embedding`, `plot_2d_data`, `plot_3d_data`)
- **存在代码重复** — 两个文件有大量相似逻辑

### 注意
这两个文件存在循环导入风险，应合并或明确分工。

---

## 3. events.py — 交互事件

### 职责
处理所有用户交互: 悬停提示、点击选择、图例交互、选择工具。

### 事件处理器

```python
def on_hover(event)
    """鼠标悬停 → 显示样本信息提示"""
    # 查找最近散点 → 显示 tooltip_columns 信息
    # 显示选中状态标记

def on_click(event)
    """双击 → 选择/取消选择样本"""

def on_legend_click(event)
    """点击图例 → 切换组可见性"""
    # 将点击的组移到最前层 (zorder)

def on_slider_change(val=None)
    """参数变更 → 重新渲染"""
    # 调度到 plot_embedding / plot_2d_data / plot_3d_data
    # 保存会话参数
    # 刷新画布
```

### 选择工具

```python
def toggle_selection_mode(tool_type: str)
    """启用/禁用选择工具"""
    # tool_type: 'export' (框选), 'lasso' (套索), 'isochron' (等时线)
    # 创建 RectangleSelector 或 LassoSelector

def sync_selection_tools()
    """确保选择器匹配当前坐标轴"""

def refresh_selection_overlay()
    """更新选择高亮散点 + 置信椭圆"""
    # 红色高亮选中点
    # 可选 95% 置信椭圆

def calculate_selected_isochron()
    """对选中点计算等时线年龄"""
    # York 回归 → 年龄 + MSWD + R²
    # 存储到 app_state.selected_isochron_data
```

### 选择回调

```python
def _handle_rectangle_select(eclick, erelease)
    """框选回调 → 选中矩形内的点"""

def _handle_lasso_select(vertices)
    """套索回调 → 选中多边形内的点"""
```

### 置信椭圆

```python
def draw_confidence_ellipse(x, y, ax, confidence=0.95, facecolor='none',
                            edgecolor='red', linewidth=1.5, linestyle='--',
                            zorder=10, **kwargs) -> Ellipse
    """绘制基于卡方分布的 95% 置信椭圆"""
    # 协方差矩阵 → 特征值分解 → 椭圆参数
```

### 样本索引解析

```python
def _resolve_sample_index(event) -> int | None
    """从 matplotlib 事件解析样本索引"""
    # 1. 尝试 artist_to_sample 映射
    # 2. 回退到 sample_coordinates 最近邻搜索
```

---

## 4. plotting_style.py — 绘图样式

### 职责
管理 matplotlib rcParams、坐标轴样式、图例布局。

### 全局样式

```python
def _apply_current_style()
    """从 app_state 应用全局 matplotlib 样式"""
    # 设置 rcParams: DPI, 背景色, 网格, 刻度, 坐标轴, 标签
```

### 坐标轴样式

```python
def _enforce_plot_style(ax)
    """在特定坐标轴上强制样式"""
    # 网格 (主/次)
    # 刻度 (方向/长度/宽度/颜色)
    # 次刻度
    # 脊柱 (线宽/颜色/可见性)

def _apply_axis_text_style(ax)
    """应用标签/标题样式"""
    # 颜色, 粗细, 间距
```

### 图例布局

```python
def _legend_layout_config(ax, show_marginal_kde=False)
    """解析图例位置 → (loc, bbox, mode, borderaxespad)"""

def _legend_columns_for_layout(labels, ax, location_key) -> int | None
    """自动计算图例列数"""

def _style_legend(legend, show_marginal_kde=False)
    """应用图例样式 (框架, 透明度, 颜色)"""
```

### 样式刷新

```python
def refresh_plot_style()
    """不重新计算嵌入，仅刷新样式"""
    # 1. _apply_current_style() → rcParams
    # 2. 遍历所有 axes → _enforce_plot_style() + _apply_axis_text_style()
    # 3. 更新 scatter_collections (大小, 透明度, 边框)
    # 4. 刷新选择叠加
    # 5. fig.canvas.draw_idle()
```

---

## 5. style_manager.py — 样式管理器

### 职责
调色板定义、字体管理、UI 主题。

### StyleManager 类

```python
class StyleManager:
    def get_available_fonts(self) -> list[str]
        """获取系统可用字体 (带缓存)"""

    def get_palette_names(self) -> list[str]
        """获取调色板名列表"""

    def get_ui_theme_names(self) -> list[str]
        """获取 UI 主题名列表"""

    def get_ui_theme(self, name: str) -> dict
        """获取 UI 主题配置"""

    def apply_style(self, show_grid, color_scheme, primary_font, cjk_font, font_sizes)
        """应用全局 matplotlib 样式"""
```

### 调色板

| 名称 | 说明 |
|------|------|
| `vibrant` | 鲜艳色 (默认) |
| `bright` | 明亮色 |
| `high-vis` | 高对比度 |
| `light` | 浅色 |
| `muted` | 柔和色 |
| `retro` | 复古色 |
| `std-colors` | 标准色 |
| `dark_background` | 深色背景 |

### UI 主题

| 名称 | 背景 | 前景 | 风格 |
|------|------|------|------|
| Modern Light | 白色 | 深灰 | 默认 |
| Modern Dark | 深色 | 浅色 | dark_background |
| Scientific Blue | 蓝白 | 深蓝 | seaborn-v0_8-whitegrid |
| Retro Lab | 米色 | 棕色 | ggplot |

### 字体缓存
- 缓存路径: `~/.isotopes_analysis/font_cache.json`
- 存储字体名 → 路径映射
- 避免每次启动重新扫描系统字体

---

## 6. plotting_kde.py — KDE 渲染

### 职责
KDE 等高线叠加和边际 KDE 分布。

```python
def lazy_import_seaborn()
    """懒加载 seaborn"""

def clear_marginal_axes()
    """清除边际 KDE 坐标轴"""

def draw_marginal_kde(ax, df_plot, group_col, palette, unique_cats, x_col, y_col)
    """绘制上/右边际 KDE"""
    # 使用 make_axes_locatable 创建附加坐标轴
    # 可配置大小 (5-40%)
    # 大数据集采样 (max_points)
```

---

## 7. plotting_analysis_qt.py — 诊断图

### 职责
Qt 对话框中的诊断分析图。

```python
def show_scree_plot(parent_window)
    """PCA 方差解释图 (碎石图)"""

def show_pca_loadings(parent_window)
    """PCA 成分载荷热图"""

def show_embedding_correlation(parent_window)
    """特征-嵌入相关性"""

def show_shepard_diagram(parent_window)
    """距离保持图 (Shepard diagram)"""
    # 采样上限 1000 点

def show_correlation_heatmap(parent_window)
    """特征相关性矩阵热图"""
```

---

## 8. plotting_data.py — 数据准备

### 职责
ML 算法的数据提取和懒加载。

```python
def _lazy_import_ml()
    """懒加载 sklearn 模块 (TSNE, PCA, MinCovDet, StandardScaler, SimpleImputer)"""

def _get_analysis_data() -> tuple[np.ndarray, np.ndarray]
    """提取数值数据子集用于分析"""
    # 返回活动子集或完整数据
    # 转换为 float，NaN 用 0 填充
    # 返回 (X, indices)
```

---

## 9. line_styles.py — 线型解析

```python
def resolve_line_style(app_state, style_key: str, fallback: dict) -> dict
    """合并 app_state 线型覆盖与回退默认值"""
    # 检查 app_state.line_styles[style_key]
    # 非 None 值覆盖 fallback
```

---

## 依赖关系

```
style_manager.py (无内部依赖)
  ↓
plotting_style.py ← style_manager, app_state
  ↓
plotting_data.py ← app_state, sklearn (懒加载)
  ↓
plotting_kde.py ← seaborn (懒加载), app_state
  ↓
line_styles.py ← app_state
  ↓
plotting.py ← plotting_style, plotting_data, plotting_kde, line_styles, geochemistry
  ↓
plotting_embed.py ← plotting.py (存在循环导入风险!)
  ↓
events.py ← plotting.py, plotting_embed.py, app_state
  ↓
plotting_analysis_qt.py ← plotting_data, PyQt5
  ↓
__init__.py ← 导出所有公共 API
```

---

## 改进建议

### 高优先级

1. **合并 plotting.py 和 plotting_embed.py** — 两个文件有大量重复代码和循环导入风险。应合并为一个文件，或明确拆分为:
   - `plotting_core.py` — 嵌入计算 + 工具函数
   - `plotting_render.py` — 渲染逻辑
   - `plotting_geo.py` — 地球化学叠加

2. **plot_embedding() 过长 (~757 行)** — 应拆分为子函数:
   - `_render_scatter_groups()` — 散点渲染
   - `_render_kde_overlay()` — KDE 叠加
   - `_render_geo_overlays()` — 地球化学叠加
   - `_render_legend()` — 图例
   - `_render_title_labels()` — 标题和标签

3. **_resolve_isochron_errors() 重复** — 在 plotting.py 和 events.py 中各有一份，应提取到共享工具模块。

4. **events.py 中硬编码中文字符串** — `"状态: 已选中"`, `"单击导出已移除"` 等应使用 `translate()`。

### 中优先级

5. **无进度指示** — UMAP/t-SNE 在大数据集 (10k+) 上可能耗时数分钟，UI 冻结。应添加进度条或后台线程。

6. **图例 bbox 偏移硬编码** — `1.08`, `1.32`, `-0.28` 等魔法数字应移到 CONFIG 或 app_state。

7. **诊断图无导出功能** — scree plot, loadings 等无法保存为图片。应添加 "另存为" 按钮。

8. **scatter_collections 全量迭代** — `refresh_plot_style()` 遍历所有散点集合，即使只有一个变更。

### 低优先级

9. **类型注解缺失** — 大部分函数无类型注解。

10. **单元测试缺失** — 复杂的渲染逻辑无测试覆盖，重构风险高。

11. **KDE 采样硬编码** — `max_points=5000` 应可配置。

12. **等时线工具仅支持 206-207** — 应扩展 `calculate_selected_isochron()` 支持 206-208 模式。
