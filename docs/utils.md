# utils/ 模块开发文档

## 模块概述

`utils/` 提供日志和通用工具函数。当前较轻量。

**文件清单 (108 行)**

| 文件 | 行数 | 职责 |
|------|------|------|
| `__init__.py` | 9 | 模块入口 |
| `logger.py` | 95 | 旋转文件日志 + stdout/stderr 重定向 |
| `line_styles.py` | 4 | 线型常量 (已迁移到 visualization/) |

---

## 1. logger.py — 日志系统

### 职责
配置旋转文件日志，重定向 stdout/stderr 到日志文件。

### LoggerWriter 类

```python
class LoggerWriter:
    """同时写入日志文件和原始控制台流的自定义 writer"""

    def __init__(self, logger, level, original_stream)
    def write(self, buf)   # 写入控制台 + 缓冲写入日志
    def flush(self)
```

- 按行缓冲: 遇到 `\n` 时将完整行写入 logger
- 保留原始控制台输出 (通过 `original_stream`)
- stdout → INFO 级别, stderr → ERROR 级别

### setup_logging 函数

```python
def setup_logging(log_filename='isotopes_analyse.log',
                  max_bytes=50*1024*1024,    # 50MB
                  backup_count=1)
```

**配置内容:**
1. `RotatingFileHandler` — 50MB 旋转，保留 1 个备份
2. 格式: `%(asctime)s - %(message)s`
3. 静默 matplotlib 日志 (`WARNING` 级别)
4. 静默 numba 日志 (`WARNING` 级别)
5. 重定向 `sys.stdout` → LoggerWriter(INFO)
6. 重定向 `sys.stderr` → LoggerWriter(ERROR)

### 日志文件位置
- 开发环境: `项目根目录/isotopes_analyse.log`
- 打包环境: 可执行文件同目录

### 已知限制
- `LoggerWriter` 无 `fileno()` 方法，导致 `faulthandler` 无法启用 (main.py 中有 warning)
- 日志格式不含模块名/行号，调试时定位困难

---

## 2. line_styles.py — 线型常量

```python
# 仅 4 行，定义基础线型常量
# 实际线型逻辑已迁移到 visualization/line_styles.py
```

此文件可考虑移除。

---

## 依赖关系

```
logger.py (无内部依赖)
  ↑
main.py (启动时调用 setup_logging())
```

---

## 改进建议

### 中优先级

1. **日志格式增强** — 添加模块名和行号:
   ```python
   formatter = logging.Formatter('%(asctime)s [%(name)s:%(lineno)d] %(message)s')
   ```

2. **LoggerWriter 添加 fileno()** — 返回原始流的 fileno，使 faulthandler 可用:
   ```python
   def fileno(self):
       return self.original_stream.fileno()
   ```

3. **移除 utils/line_styles.py** — 功能已迁移到 visualization/line_styles.py，此文件仅 4 行且无引用。

### 低优先级

4. **结构化日志** — 当前使用字符串前缀 `[INFO]`, `[WARN]`, `[ERROR]`。应直接使用 logging 级别:
   ```python
   logger.info("Message")      # 而非 logger.info("[INFO] Message")
   logger.warning("Message")   # 而非 logger.info("[WARN] Message")
   ```

5. **日志级别可配置** — 当前硬编码 DEBUG 级别，应支持通过环境变量或配置文件调整。
