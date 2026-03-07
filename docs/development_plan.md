# 开发规划（进行中）

本文件仅保留尚未完成或正在推进的事项。历史已完成条目不再重复记录。

## 核查更新（2026-03-07）

本次按代码现状逐项核查后，更新如下：

- 仍未完成（保持原计划）：
    - AppState 分层的全量字段迁移与调用切换。
    - 类型注解全覆盖（P2）。
    - 数值稳定性统一收口。
    - 测试框架落地。
    - 配置外部化。
    - 插件系统（含 ML 管线插件化）。

## 执行策略调整（2026-03-07）

按当前决策，`ML 管线增强` 延后到插件功能开发完成后再推进。

- 当前阶段只推进：第一优先级 + 第二优先级。
- 延后事项：`1.2 ML 管线增强`（依赖插件接口与插件管理能力）。
- 进入条件：`插件开发计划` 至少完成 M2（内置插件迁移）。

---

## 全局改进计划

### 第一优先级：功能与性能

#### 1.2 ML 管线增强（延期）

**状态:** 延期，待插件功能完成后执行。

**延期原因:** ML 算法将转为插件化实现，当前直接改造主仓库会导致重复重构。

**重启条件:** 插件开发计划达到 M2（XGBoost/UMAP 等内置插件迁移完成）。

**后续实施要点（保留）:**

- 增加 train/valid/test 划分与固定随机种子报告。
- 增加交叉验证指标（macro-F1、balanced accuracy、AUC-ovr）。
- XGBoost 默认 `tree_method='hist'`，并在报告中标注训练耗时。
- 支持 per-label 阈值与阈值搜索结果导出。

### 第二优先级：代码质量

#### 2.1 类型注解补齐（部分完成）

**范围优先级:** `core/` > `data/` > `visualization/` > `ui/`

**要求:**

- 新增/重构公共函数必须含类型注解。
- 公共 API 使用 Google 风格 docstring（Args/Returns/Raises）。
- 剩余重点：`core/state.py`、`core/session.py`、`data/` 核心计算函数。

#### 2.2 AppState 分层拆分

**目标:** 将 `AppState` 按职责拆分为子状态对象，降低耦合。

**建议结构:**

```python
class AppState:
    data: DataState
    algorithm: AlgorithmState
    visual: VisualState
    geochem: GeochemState
    style: StyleState
    interaction: InteractionState
```

**实现状态:** 进行中（已新增分层兼容视图、可写属性与顶层别名；正在分批迁移调用方）

#### 2.3 数值稳定性统一（部分完成）

**目标:** 统一除零与无效值处理策略。

**实施要点:**

- 统一 `EPSILON` 常量来源，避免散落魔法数字。
- 在关键计算路径中使用 `np.errstate`。
- 所有外部输入统一 `pd.to_numeric(errors='coerce')`。
- 剩余重点：扩展到其余模块并补充相应回归验证。

### 当前阶段交付顺序（仅 P2）

1. P2-1：类型注解补齐（先 core/data）
2. P2-2：AppState 分层拆分
3. P2-3：数值稳定性统一收口

### 第三优先级：基础设施

#### 3.1 单元测试框架落地

**最小目标:** 建立可运行测试骨架并覆盖关键数值模块。

```text
tests/
├── test_geochemistry.py
├── test_cache.py
├── test_session.py
├── test_localization.py
├── test_endmember.py
├── test_mixing.py
└── test_provenance_ml.py
```

#### 3.2 配置外部化

支持用户配置文件 `~/.isotopes_analysis/config.json`，并与 `CONFIG` 合并。

```json
{
  "default_language": "zh",
  "figure_dpi": 150,
  "embedding_cache_size": 16,
  "xgboost_tree_method": "hist"
}
```

---

## 模块改进建议（进行中）

### data/ 模块

#### 高优先级

1. `provenance_ml.py` 增加交叉验证与测试集报告（延期，插件完成后执行）。
2. XGBoost 训练默认切换到 `tree_method='hist'`（延期，插件完成后执行）。

#### 中优先级

3. 列名规范化策略外置（导入配置或映射表）。
4. `GeochemistryEngine` 为后台线程场景增加并发保护。
5. `mixing.py` 增加误差传播能力（不确定度输入到权重区间）。

#### 低优先级

6. 清理 geochemistry 兼容别名函数（下个大版本）。
7. `endmember.py` 中阈值参数可配置化。

### visualization/ 模块

#### 高优先级

1. 补充渲染子函数级测试（覆盖散点/KDE/地球化学覆盖层/图例/标题路径）。
2. 继续增强 UI 进度展示与异常可视反馈（与后台任务联动）。

#### 中优先级

3. 诊断图增加“另存为”导出能力。
4. `refresh_plot_style()` 支持增量更新，避免全量遍历散点集合。
5. `calculate_selected_isochron()` 扩展 206-208 模式。

#### 低优先级

6. 完善渲染异常回滚测试，确保失败时 canvas 状态一致。

---

## 插件开发计划（扩展版）

### 目标

- 将机器学习能力从主仓库解耦为插件，降低核心代码耦合。
- 支持第三方算法快速接入，保持 UI 与数据层兼容。
- 保证插件 API 稳定、可发现、可诊断、可回退。

### 设计原则

1. **稳定接口优先**：先定义最小可用 API，再扩展能力。
2. **弱依赖核心**：插件只依赖公开接口，不直接访问内部状态。
3. **可观测性**：插件加载、执行、失败必须有结构化日志。
4. **兼容演进**：通过 API 版本协商避免一次性破坏升级。

### V1 插件范围

- `MLClassifierPlugin`：监督分类（训练/预测/概率输出）。
- `EmbeddingPlugin`：降维嵌入（fit_transform/transform）。
- `FeatureEngineeringPlugin`：特征构造与清洗。

### 目录与发现机制

```text
plugins/
├── __init__.py
├── api.py                 # 抽象接口、类型定义、错误类型
├── manager.py             # 插件发现、加载、生命周期管理
├── registry.py            # 已加载插件注册表
├── builtins/
│   ├── xgboost_plugin.py
│   └── umap_plugin.py
└── third_party/
    └── ...
```

**发现策略（按优先顺序）:**

1. 内置目录 `plugins/builtins/`
2. 用户目录 `~/.isotopes_analysis/plugins/`
3. 可选 entry points（后续版本）

### 接口草案（V1）

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class PluginMeta:
    name: str
    version: str
    api_version: str
    plugin_type: str
    author: str = ""


class BasePlugin(Protocol):
    meta: PluginMeta

    def validate_environment(self) -> tuple[bool, str]:
        ...

    def get_default_params(self) -> dict[str, Any]:
        ...


class MLClassifierPlugin(BasePlugin, Protocol):
    def fit(self, x: Any, y: Any, **params: Any) -> dict[str, Any]:
        ...

    def predict(self, x: Any) -> Any:
        ...

    def predict_proba(self, x: Any) -> Any:
        ...
```

### 生命周期管理

1. `discover`：扫描插件并解析元数据。
2. `validate`：检查依赖、API 版本、运行环境。
3. `register`：写入注册表并暴露给 UI。
4. `execute`：统一调用并捕获异常。
5. `dispose`：释放资源并记录统计信息。

### 兼容性策略

- `api_version` 采用 `MAJOR.MINOR`。
- 主版本不匹配时拒绝加载并给出可读错误。
- 次版本不匹配时允许加载但记录 warning。
- 保留 `capabilities` 字段，支持按能力降级。

### 安全与隔离

- 默认与主进程同进程运行（V1）。
- 对插件异常做边界捕获，不允许异常穿透到 UI 事件循环。
- 严禁插件直接读写 `app_state` 内部字段；通过受控上下文对象访问。
- 对第三方插件开启“受限模式”标记（禁用敏感入口）。

### 开发者体验

- 提供 `plugins/examples/` 最小模板。
- 提供 `scripts/new_plugin.py` 脚手架命令。
- 提供插件自检命令：`uv run python -m plugins.manager --check`。
- 在 UI 中新增“插件管理”对话框（启用/禁用/诊断信息）。

### 里程碑

#### M1（接口冻结）

- 完成 `plugins/api.py` 与 `PluginMeta`。
- 实现 `PluginManager` 基础加载链路。

#### M2（内置插件迁移）

- 将当前 XGBoost 管线迁移为内置 `MLClassifierPlugin`。
- 将 UMAP/t-SNE 包装为 `EmbeddingPlugin`。

#### M3（UI 接入）

- 算法下拉框改为读取注册表。
- 新增插件状态与失败原因展示。

#### M4（第三方支持）

- 支持用户目录安装插件。
- 增加插件签名/来源标识字段。

#### M5（测试与文档）

- 增加插件加载、执行、回退、兼容性测试。
- 新增 `docs/plugins.md`（开发指南 + API 参考）。

### 验收标准

- 关闭/卸载某个插件不影响应用启动。
- 插件执行失败时 UI 不冻结，且有可检索日志。
- 至少 2 个内置插件完成迁移并通过回归验证。
- 插件接口升级时，旧插件可得到明确兼容性提示。

---

