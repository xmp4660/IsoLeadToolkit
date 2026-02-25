# 开发规范 (统一)

本规范为 Isotopes Analyse 全项目统一标准，适用于 `ui/` 与 `visualization/` 等所有模块。原则参考并融合以下知名规范体系：
- PEP 8 (Python 代码风格)
- PEP 257 (Docstring 规范)
- Google Python Style Guide
- Black / Ruff (自动化格式化与静态检查思想)
- NumPy Docstring Standard
- Qt / PyQt 事件与线程模型约束
- Matplotlib 组合式绘图规范

目标：让代码在一致性、可维护性、可扩展性与可测试性上达到工程级标准。

---

**1. 命名与结构**
1. 模块文件使用 `snake_case.py`，类名使用 `PascalCase`，函数/方法使用 `snake_case`，私有方法使用 `_leading_underscore`。
2. 包对外 API 仅通过 `__init__.py` 导出，默认不暴露私有符号（以 `_` 开头）。
3. 单文件超过 800 行或职责超过 2 个必须拆分，按“数据准备 / 计算 / 渲染 / UI / 事件”分层。
4. 模块顶层禁止副作用（如绘图、读写文件、耗时计算），仅允许定义常量、函数、类。

**2. 文件头与导入顺序**
1. 文件第一行必须是模块 docstring，说明职责与关键依赖。
2. 导入顺序固定：标准库 → 第三方库 → 本项目模块。
3. `logger = logging.getLogger(__name__)` 必须在导入之后声明。
4. 统一入口：`from core import translate, app_state`，禁止混用 `core.state`/`core.localization` 直入。

**3. 格式化与静态检查**
1. 代码风格以 Black 兼容格式为目标，行宽建议 88-100。
2. 统一使用 Ruff 的规则集合进行静态检查，禁止手工绕过规则。
3. 任何禁用规则必须在注释中解释原因并限定范围。

**4. 日志规范**
1. 禁止手工拼接 `[INFO]` 前缀，使用 `logger.info/warning/error`。
2. 可恢复异常用 `logger.warning`，不可恢复用 `logger.error`。
3. 需要堆栈时使用 `logger.exception`。
4. 日志必须包含可检索上下文（算法名、列名、样本数、关键参数）。

**5. 国际化与用户可见文本**
1. 所有用户可见字符串必须使用 `translate("English text")`。
2. 翻译键统一使用英文原文，不允许中文 key。
3. 新增 UI 文本必须同时更新 `locales/zh.json` 与 `locales/en.json`。
4. visualization 中的提示/错误同样必须翻译。

**6. UI 与线程模型**
1. 所有 UI 更新必须在主线程执行。
2. >200ms 的计算必须移入 `QThread` 或后台线程，并提供进度提示。
3. UI 事件回调只负责采集参数与触发，不执行长计算。
4. 线程回调必须保证 UI 状态一致性，禁止部分更新。

**7. 可视化层规范**
1. 绘图入口统一通过 `visualization/plotting/api.py`。
2. 渲染函数不得直接修改 UI 控件，仅操作 `app_state` 与绘图对象。
3. 所有 Matplotlib 样式设置集中在 `plotting/style.py`。
4. 渲染流程必须可重入，异常时要回滚或保持一致状态。

**8. 数据处理与数值稳定性**
1. 数值列解析必须使用 `pd.to_numeric(..., errors='coerce')`。
2. 缺失值必须有明确策略并记录日志。
3. 列名推断规则集中管理，禁止多处复制。
4. 对外输入必须验证并给出清晰错误提示。

**9. API 边界与依赖管理**
1. 模块内 helper 使用 `_` 前缀且不导出。
2. 跨模块调用优先走公开 API，不直接访问内部状态。
3. 大型依赖（sklearn/umap/seaborn）必须懒加载。

**10. 类型注解与文档**
1. 新增或重构的核心函数必须补充类型注解。
2. 对外 API 必须有 docstring，描述输入/输出/异常。
3. 重要 UI 行为需同步更新 docs。

**11. 测试与回归**
1. 修复 bug 必须提供回归测试或最小复现步骤。
2. 算法逻辑优先单元测试，UI 逻辑优先集成测试或验收清单。
3. 关键重构需提供性能与行为一致性说明。

**12. 配置与演进**
1. 可配置项集中于 `core/config.py` 或用户配置文件。
2. 新配置必须提供默认值与文档说明。
3. 兼容性 shim 必须显式标注，并在 2 个版本内移除。
