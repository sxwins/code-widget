# Technical Debt

本文件记录在文档审查过程中发现的、建议在下一版本修正的代码级问题。
这些问题不影响当前功能的正确性，但存在代码与注释不一致的风险。

---

## [TD-01] `Appearance` 类的定义位置与使用位置不一致（设计迁移遗留）

**文件**：`src/models/teacher_config.py`

**背景**：

外观参数（`Appearance`）最初作为教师个人配置的一部分，定义并存储于 `teacher_config.py` / `teacher_config.json`。后来迁移为全局设置，改为保存于 `settings.json`（由 `AppSettings` 管理），但迁移时未完成以下清理工作：

**遗留问题一：`Appearance` 类定义位置**

`Appearance` 类（第58-67行）仍定义于 `teacher_config.py`，而非其实际使用者 `app_settings.py`。`app_settings.py` 通过跨模块 import 引用：

```python
from models.teacher_config import Appearance  # app_settings.py:14
```

当前 `TeacherConfig` 自身不含 `appearance` 字段，`Appearance` 类与 `teacher_config.py` 在逻辑上已无关联。

**遗留问题二：模块 docstring 未更新**

`teacher_config.py` 第3-8行的模块 docstring 仍列出 `appearance{}`：

```python
"""
File layout (邵_teacher_config.json):
  teacher_name, academic_year, courses[], overrides[], attendance_codes{},
  appearance{}, window_position{}, settings{}   ← 过时，此字段已不存在
"""
```

但 `save_teacher_config()` 和 `load_teacher_config()` 均不处理 appearance 字段。

**建议修正**：

1. 将 `Appearance` 类移至 `src/models/app_settings.py`（或新建 `src/models/appearance.py`），消除跨模块依赖方向颠倒的问题。
2. 更新 `teacher_config.py` 模块 docstring，移除 `appearance{}` 行，并加注说明 appearance 已迁至 `settings.json`。

```python
# 修正后的 docstring 示例
"""
File layout (<姓>_teacher_config.json):
  teacher_name, academic_year, courses[], overrides[], attendance_codes{},
  window_position{}, settings{}

Note: Appearance settings were previously stored here; they are now managed
by AppSettings and persisted in settings.json.
"""
```

**影响**：低（不影响运行时行为；仅为结构清晰度和可维护性问题）

**发现时机**：2026-03-03，文档审查 `docs/cn/02_架构设计.md` 过程中

---
