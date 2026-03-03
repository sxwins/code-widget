# Technical Debt

本文件记录在文档审查过程中发现的、建议在下一版本修正的代码级问题。
这些问题不影响当前功能的正确性，但存在代码与注释不一致的风险。

---

## [TD-01] `teacher_config.py` 模块 docstring 包含过时的 `appearance{}` 字段

**文件**：`src/models/teacher_config.py`，第 3-7 行（模块 docstring）

**问题**：

```python
"""
File layout (邵_teacher_config.json):
  teacher_name, academic_year, courses[], overrides[], attendance_codes{},
  appearance{}, window_position{}, settings{}
"""
```

docstring 中列出了 `appearance{}`，但实际上：

- `TeacherConfig` dataclass 没有 `appearance` 字段。
- `save_teacher_config()` 不向 `teacher_config.json` 写入 appearance。
- `load_teacher_config()` 不从 `teacher_config.json` 读取 appearance。
- `Appearance` 类虽定义于本文件，但由 `AppSettings`（`app_settings.py`）使用，appearance 数据保存于 `settings.json`。

该 docstring 应为历史残留（曾计划或测试时将 appearance 放在 teacher_config，后改为 settings）。

**建议修正**：

```python
"""
File layout (<姓>_teacher_config.json):
  teacher_name, academic_year, courses[], overrides[], attendance_codes{},
  window_position{}, settings{}

Note: Appearance settings are stored in settings.json (managed by AppSettings),
not in the teacher config file.
"""
```

**影响**：低（仅注释问题，不影响运行时行为）

**发现时机**：2026-03-03，文档审查 `docs/cn/02_架构设计.md` 过程中

---
