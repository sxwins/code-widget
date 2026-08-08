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
File layout (teacher_config.json):
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
File layout (teacher_config.json):
  teacher_name, academic_year, courses[], overrides[], attendance_codes{},
  window_position{}, settings{}

Note: Appearance settings were previously stored here; they are now managed
by AppSettings and persisted in settings.json.
"""
```

**影响**：低（不影响运行时行为；仅为结构清晰度和可维护性问题）

**发现时机**：2026-03-03，文档审查 `docs/cn/02_架构设计.md` 过程中

---

## [TD-02] `period=0` 记录的排序键不含 `custom_start`，同天多条时顺序不确定

**文件**：`src/engine/override.py`

**背景**：

`override.py` 中共有三处排序调用，均以 `(sc.date, sc.period)` 作为排序键：

```python
# override.py:34  — apply_overrides 主排序
result.sort(key=lambda sc: (sc.date, sc.period))

# override.py:114 — _reassign_session_keys 组内排序
group.sort(key=lambda sc: (sc.date, sc.period))

# override.py:118 — _reassign_session_keys 最终全局排序
scheduled.sort(key=lambda sc: (sc.date, sc.period))
```

当 reschedule override 提供 `new_start_time` 时，`new_period` 被设为 0（见 `_apply_reschedule`）。若同一天存在多个此类记录，其排序键 `(date, 0)` 完全相同，实际顺序由 Python 稳定排序保持前一步的相对顺序，**而非按 `custom_start` 时间先后排列**。

**当前影响**：

- 对于表示窗口显示而言，影响极小——同天多次自定义时间调课是极罕见的场景。
- `session_key` 的最终赋值顺序可能与实际上课时间顺序不一致（例如下午课的编号早于上午课）。

**建议修正**：

将排序键改为三元组，`custom_start`（空字符串 `""` 在比较中排在非空值之前，可作为合理默认）：

```python
# 改进后的排序键
result.sort(key=lambda sc: (sc.date, sc.period, sc.custom_start))
```

三处排序调用均需同步修改。

**影响**：低（极罕见场景；不影响典型使用的正确性）

**发现时机**：2026-03-03，文档审查 `docs/cn/03_调度逻辑规格.md` 过程中

---
