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

## [TD-03] 编辑 skip/makeup 调整时，保存后类型被错误改写为 reschedule【高】

**文件**：`src/gui/config_dialog.py`

**问题描述**：

调整管理标签页的"编辑"按钮（第1084行）对所有 override 类型（skip / makeup / reschedule）一律打开 `RescheduleDialog`：

```python
# config_dialog.py:1084
dlg = RescheduleDialog(self.school_config, course, existing_override=ov, parent=self)
```

而 `RescheduleDialog.save()` 将 `type` 字段硬编码为 `"reschedule"`（第392行）：

```python
# config_dialog.py:392
self.result_override = Override(type="reschedule", ...)
```

**实际影响**：

用户编辑一条 `skip`（停课）或 `makeup`（补课）记录后，保存的 override 类型变为 `"reschedule"`，且被填入了原本不存在的 `new_date` / `new_period` 字段。调度引擎会将该记录按调课处理：
- 原本应被删除的课变成了"从原日期调到新日期"的调课
- `session_key` 重新编号逻辑也会按 reschedule 规则执行，产生错误结果

**建议修正**：

为 skip 和 makeup 各自创建独立的编辑对话框（或在 `RescheduleDialog` 中根据传入的 override 类型保留原始类型），确保保存时 `type` 字段与原始类型一致。

**影响**：高（数据破坏性——静默地将 skip/makeup 记录转换为语义不同的 reschedule）

**发现时机**：2026-03-04，外部代码评审

---

## [TD-04] 日期/时间解析无异常保护，配置格式错误时应用直接崩溃【高】

**文件**：`src/engine/override.py`、`src/engine/scheduler.py`、`src/main.py`

**问题描述**：

多处解析操作未包裹 try/except，配置文件中任何格式错误均会引发未捕获异常：

```python
# override.py:40 — skip 日期解析
skip_date = date.fromisoformat(ov.date)

# override.py:52 — makeup 日期解析
new_date = date.fromisoformat(ov.date)

# override.py:67 — reschedule 原始日期解析
orig_date = date.fromisoformat(ov.original_date)

# override.py:78 — reschedule 新日期解析
new_date = date.fromisoformat(ov.new_date)

# scheduler.py:94 — 自定义开始时间解析
h, m = map(int, sc.custom_start.split(":"))
```

此外，`main.py` 启动时的 try/except 块（第121–128行）仅覆盖配置文件的加载操作，而调用 `_build_all_scheduled()`（第131行）在该块**之外**：

```python
# main.py:121-131（简化）
try:
    school_config = load_school_config(...)   # 受保护
    teacher_config = load_teacher_config(...)  # 受保护
except Exception as e:
    ...
    return
all_scheduled = _build_all_scheduled(...)      # ← 未受保护，异常直接崩溃
```

**实际影响**：

配置文件中任何格式错误（如日期写成 `"2025/03/05"` 而非 `"2025-03-05"`，或 `custom_start` 写成 `"9:00"` 而非 `"09:00"`）均会导致应用在启动时抛出未捕获的 `ValueError`，程序直接退出，无任何提示给用户。

**建议修正**：

1. 将 `_build_all_scheduled()` 调用纳入现有的 try/except 块，或添加独立的异常处理
2. 在 `override.py` 和 `scheduler.py` 的解析点添加 try/except，记录日志并跳过格式错误的记录

**影响**：高（配置格式错误时静默崩溃，无用户可读的错误提示）

**发现时机**：2026-03-04，外部代码评审

---

## [TD-05] 临时码 TTL 过期后，显示窗口不自动清除——需等待下一次状态变化【中】

**文件**：`src/main.py`

**问题描述**：

临时码（temp code）的过期判断仅在 `_code_for()` 函数被调用时执行（第212–224行）。`_tick()` 在活跃课程未变化时提前返回（第243行），不会重新调用 `_code_for()`：

```python
# main.py:243（简化）
def _tick():
    active = compute_window(...)
    if active == _last_active[0]:
        return          # ← 提前返回，不更新显示
    ...
    win.update_class(active, _code_for(active))
```

**实际影响**：

若临时码在课程进行中过期，显示窗口不会自动切换回正式出席码。直到下一次状态变化（例如课程结束、用户触发刷新等），窗口才会更新。从用户感知角度看，临时码"粘住了"，TTL 设定失去实际意义。

**建议修正**：

在 `_tick()` 中加入临时码过期状态检测：即使 `active` 未变化，若临时码状态（有无/值）已改变，也应触发 UI 更新。

**影响**：中（临时码功能逻辑不完整；用户可能误以为临时码永久有效）

**发现时机**：2026-03-04，外部代码评审

---

## [TD-06] 启动时无条件调用 win.show()，非上课时段启动会导致窗口短暂闪现【中】

**文件**：`src/main.py`

**问题描述**：

应用启动序列末尾无条件调用 `win.show()`（第148行），随后定时器触发首次 `_tick()`（第255行）。若当前时间不在任何课程的展示窗口内，`_tick()` 会调用 `win.hide()`，但两者之间存在时间差：

```python
# main.py:148
win.show()   # ← 无条件显示

# main.py:255
QTimer.singleShot(0, _tick)   # ← 首次 tick，决定是否隐藏
```

**实际影响**：

在非上课时段启动应用时，用户会看到出勤码窗口短暂弹出后立刻消失，视觉体验不佳。在课程展示窗口内启动时不受影响。

**建议修正**：

在调用 `win.show()` 之前先执行一次 `compute_window()` 判断，或将首次 `_tick()` 改为同步调用，确保窗口状态在显示前已确定。

**影响**：中（非功能性缺陷；仅影响非上课时段启动时的视觉体验）

**发现时机**：2026-03-04，外部代码评审

---
