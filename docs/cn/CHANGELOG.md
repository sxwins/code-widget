# docs/cn 变更记录

本文件记录中文文档集（`docs/cn/`）的所有新增与修订历史。

---

## [1.0.15] — 2026-03-04 JST · commit `pending`

### 更新：TECHNICAL_DEBT.md — 新增 TD-03 至 TD-06（外部代码评审结果）

根据外部代码评审，核实并记录了四项代码级问题：

- **[TD-03] 高**：`config_dialog.py` 编辑 skip/makeup override 时，`RescheduleDialog` 将 `type` 硬编码为 `"reschedule"`，导致保存后记录类型被静默改写（`config_dialog.py:392, 1084`）
- **[TD-04] 高**：`override.py` 四处 `date.fromisoformat()` 及 `scheduler.py` 的 `custom_start.split(":")` 均无 try/except；`main.py:131` 的 `_build_all_scheduled()` 调用在启动 try/except 块之外，配置格式错误时直接崩溃
- **[TD-05] 中**：`_tick()` 在活跃课程不变时提前返回（`main.py:243`），临时码过期后不触发 UI 更新，过期码持续显示直到下次状态变化
- **[TD-06] 中**：`main.py:148` 无条件 `win.show()`，首次 `_tick()` 之前窗口已可见，非上课时段启动时窗口短暂闪现

四条均已由源码核实（相关行号：`override.py:40,52,67,78`；`scheduler.py:94`；`main.py:131,148,212-224,243`；`config_dialog.py:392,1084`）。

---

## [1.0.14] — 2026-03-03 JST · commit `b81a817`

### 新增：09～12 标准测试文档四件套

新增四份符合软件工程标准的测试文档，并同步更新 README 索引：

- **`09_测试计划.md`**（Test Plan）：测试范围（纳入/排除）、资源分配、进度安排、风险评估表（4项风险）、退出准则。
- **`10_测试规格说明书.md`**（Test Specification）：测试环境规格、`uv sync --group dev` 搭建步骤、测试策略（引擎层/GUI层）、需求到测试点的完整映射矩阵（4张映射表）。
- **`11_测试用例.md`**（Test Cases）：全部38件测试用例的正式规格（TC-SCH/TC-OVR/TC-WIN/TC-TRAY/TC-CFG），含TC-ID、优先级、前置条件、输入、步骤、预期结果；P1共25件，P2共13件。
- **`12_测试报告.md`**（Test Report）：执行结果（38/38通过）、按文件/功能域/优先级三维汇总、缺陷汇总（0件）、覆盖分析（已覆盖/未覆盖区域）、遗留风险评估、发布建议。

---

## [1.0.13] — 2026-03-03 JST · commit `d729d8f`

### 补充：08_自动测试规格.md — 新增 §5 GUI 测试原理

新增独立章节，说明 `pytest-qt` 如何对 UI 进行测试：

- **§5.1**：`qtbot` 的两个核心职责（自动创建 QApplication、通过 `addWidget` 管理 widget 生命周期）。
- **§5.2**：测试"状态"而非"像素"的方法——直接读取 widget 属性（`text()`、`isVisible()`、`count()`、`findChildren()`）。
- **§5.3**：三个 GUI 测试文件的具体做法及代码示例。
- **§5.4**：覆盖边界表格——能发现与发现不了的问题，说明本项目未使用 `qtbot.mouseClick` 等操作模拟。

原 §5 / §6 / §7 依次后移为 §6 / §7 / §8，小节编号同步更新。

---

## [1.0.12] — 2026-03-03 JST · commit `2ac8e03`

### 补充：08_自动测试规格.md — 新增 §4 引擎层可测试性原理

新增独立章节，说明以 `compute_window` 为代表的引擎函数为何能在无 Qt 环境下直接测试：

- **§4.1**：函数签名与三个参数的数据来源追溯（`school_config.json` → `SchoolConfig`、`teacher_config.json` → `Settings`），说明参数全为内存数据对象，与 UI 无引用关系。
- **§4.2**：单向数据流示意（配置文件 → 内存模型 → 引擎函数 → UI 展示），引擎层不 import 任何 PySide6 模块。
- **§4.3**：引擎/GUI/main.py 三层的依赖关系表格，说明引擎层完全可测试、GUI 层需 pytest-qt、main.py 集成层未纳入自动化测试。

原 §4 / §5 / §6 依次后移为 §5 / §6 / §7，小节编号同步更新。

---

## [1.0.11] — 2026-03-03 JST · commit `17f9fb0`

### 修正：08_自动测试规格.md（同事提交后核查修正）

经逐行比对 `test_scheduler.py`、`test_override.py`、`test_attendance_window.py`、`test_config_dialog.py`、`test_tray.py`，发现以下问题：

#### 1. §3.2 ConfigDialog：虚构了不存在的测试行为（重要）

- **问题**：文档声称"通过 `qtbot.mouseClick` 模拟标签页切换"和"验证保存按钮的状态流转（保存中→已保存）"。
- **证据**：`test_config_dialog.py` 中不存在任何 `qtbot.mouseClick` 调用，也无任何保存按钮相关测试。5件测试均为结构验证（tab数、列数、年度列值、按钮集合）。
- **修正**：修正为实际测试内容的准确描述，并注明不含操作模拟和保存流程测试。

#### 2. §3.2 AttendanceWindow：虚构了"外观应用"测试（重要）

- **问题**：文档写"验证窗口初始状态（隐藏）和外观应用"。
- **证据**：`test_attendance_window.py` 仅有3件测试（标签更新、出席码显示、初始隐藏），无外观相关测试。
- **修正**：删除"外观应用"。

#### 3. §4 执行时间误写（次要）

- **问题**：文档写"~0.83 秒"。
- **证据**：实测结果为 `38 passed in 2.33s`。
- **修正**：改为"~2.33 秒"。

#### 4. §6 详细测试用例清单大量缺失（重要）

- **问题**：三个小节均不完整——§6.1 只列8件（实为17件）、§6.2 只列5件（实为10件）、§6.3 只列5件（实为6件），§6.4 只列3件（实为5件）。共缺失16件测试描述。
- **修正**：补全所有缺失测试，使清单与 pytest 输出的38件完全一致。

#### 5. §6.4 按钮名称日中文字混用（次要）

- **问题**："调整を追加"、"编辑" 混用中文汉字；实际测试代码使用日文。
- **证据**：`test_config_dialog.py:67`：`{"調整を追加", "編集", "削除"}`。
- **修正**：统一为日文（"調整を追加"、"編集"、"削除"）。

---

## [1.0.10] — 2026-03-03 JST · commit `382d5e9`

### 修正：06_数据流图.md（自审后修正）

经逐行比对 `main.py`、`attendance_window.py`、`engine/scheduler.py`、`models/teacher_config.py`，文档整体准确，发现以下4处问题（§3 修复已在审查时同步提交，此处记录全部4处）：

#### 1. §3 节标题：_tick 触发条件遗漏"加载新配置文件时"（次要）

- **问题**：触发条件描述为"每30秒（以及启动时、配置保存时立即触发）"，遗漏第四个触发点。
- **证据**：`main.py` 中 `on_config_file_loaded()` 末尾调用 `_tick()`，与 `on_config_saved()` 的处理相同。
- **修正**：补充"加载新配置文件时"至两处触发条件说明。

#### 2. §4 示例 key 未零填充（次要）

- **问题**：代码示例中 key 写为 `"MATH101_3"`。
- **证据**：`scheduler.py:57` 使用 `f"{i+1:02d}"` 格式化 session_key，始终零填充为两位数。
- **修正**：改为 `"MATH101_03"`。

#### 3. §4 临时码清除流程缺少 None 守卫（次要）

- **问题**：`on_temp_code_cleared` 流程图中，`win.update_class(...)` 显示为无条件调用。
- **证据**：`main.py` 中 `on_temp_code_cleared` 仅在 `_last_active[0] is not None` 时才调用 `win.update_class()`，避免向窗口传入 None。
- **修正**：补充 `if _last_active[0] is not None:` 条件分支及注释。

#### 4. §8 外观配置项误含"透明度"（重要）

- **问题**：`appearance` 箭头说明写"（字体/颜色/透明度）"，将透明度列为可配置外观属性。
- **证据**：`Appearance` 类（`teacher_config.py:58-67`）仅含字体和颜色字段；透明度由 `attendance_window.py` 中 `WA_TranslucentBackground` 硬编码实现，不属于外观配置。
- **修正**：改为"（字体/颜色）"并加注说明透明度为硬编码非配置项。

---

## [1.0.9] — 2026-03-03 JST · commit `e535572`

### 修正：05_界面规格.md（自审后修正）

经逐行比对 `attendance_window.py`、`tray.py`、`config_dialog.py`、`main.py`，文档整体准确，发现以下4处问题：

#### 1. §5.1 列宽说明文误将列 0 纳入 ×1.2 组（重要）

- **问题**：说明文写"列 0（ID）和列 2、3…先按内容自动调整，再固定为自然宽度的 1.2 倍"。
- **证据**：`config_dialog.py:817`：`for col in (2, 3):` — 仅对列 2、3 执行 ×1.2；列 0 保持 `ResizeToContents` 不做额外缩放。
- **修正**：移除"列 0（ID）和"，并补充说明列 0 保持 ResizeToContents。

#### 2. §5.2 衝突検出的 custom_start 时间窗口写成"90分钟"（重要）

- **问题**：文档写"以 start → start + 90分钟 作为时间窗口"，但代码从 school_config 第一时限实际时长计算。
- **证据**：`config_dialog.py:1013-1017`：`duration = first.end - first.start`；2026 年度 period 1 = 8:50→10:30 = 100 分钟，90 是未读到 periods 时的回退值。
- **修正**：改为"以第一时限实际时长（当前 100 分钟；fallback 90 分钟）"。

#### 3. §8.2 声称 skip 不在調整表格显示，但代码无类型过滤（重要）

- **问题**：文档写"skip 类型的 override 不在此表格中显示"。
- **证据**：`config_dialog.py:904`：`for ov in self.teacher_config.overrides:` — 无类型过滤，skip 也进入表格（新日付/新時限列为空）。
- **修正**：改为说明所有类型均显示，skip 行的新日付和新時限列为空白。

#### 4. §2.2 和附录 A 的 code_font_family 默认值写成 "Courier New"（中等）

- **问题**：`Appearance.code_font_family` 默认值为 `"Arial"`；`attendance_window.__init__` 硬编码 Courier New，但 `win.apply_appearance()` 在 `win.show()` 之前被调用，用户看到的有效默认字体是 Arial。
- **证据**：`teacher_config.py:60`：`code_font_family: str = "Arial"`；`main.py:147`：`win.apply_appearance(app_settings.appearance)` 在 `win.show()` 之前。
- **修正**：附录 A 改为 "Arial"；§2.2 加注区分硬编码初始值与有效默认值。

---

## [1.0.8] — 2026-03-03 JST · commit `be68cdd`

### 修正：04_数据格式规格.md（自审后修正）

经逐行比对 `school_config.py`、`teacher_config.py`、`app_settings.py`、`main.py`、`scheduler.py`、`override.py` 及配置文件实例，发现以下4处问题：

#### 1. §3.2 course_type 表格：Q2 和 Q4 slots 数量错误（重要）

- **问题**：表格将 Q2 和 Q4 的 `slots 数量` 标为 `1`。
- **证据**：`school_config.json` 显示 Q2 和 Q4 均有 `"slots_per_week": 2`；`scheduler.py:57` 公式 `actual_num = week_idx * ct.slots_per_week + slot_idx + 1` 以 `slots_per_week=2` 为乘数——若 Q2/Q4 课程只有 1 个 slot，生成的 session_key 将为 01, 03, 05…（全奇数），属配置错误。
- **修正**：Q2 和 Q4 的 slots 数量改为 `2`。

#### 2. §3.2 说明文：Q2/Q4 错误描述为每周 1 课时（重要）

- **问题**："Q1 和 Q3 每周 2 课时…spring / autumn / Q2 / Q4 每周 1 课时，`slots` 含 1 个元素。"
- **修正**：改为"Q1/Q2/Q3/Q4 类型均为每周 2 课时，`slots` 必须含 2 个元素"，并补充配置错误时的后果说明。

#### 3. §3.3 reschedule：两者均缺省时的 fallback 行为未说明（次要）

- **问题**：`new_period` 和 `new_start_time` 标注为"二选一"，未说明两者均缺省时的行为。
- **证据**：`override.py:83`：`new_period = ov.new_period if ov.new_period is not None else ref.period`——两者均缺省时回退到被调课程的原时限，不报错。
- **修正**：在两字段说明中补充 fallback 行为说明。

#### 4. §3.6 `courses` 标为"必须"但代码使用 `.get()`（次要）

- **问题**：`courses` 在总表中标为"必须"，但 `teacher_config.py:87` 使用 `data.get("courses", [])` → 缺省时为 `[]`，应为"可选"；且"必须"与默认值 `[]` 自相矛盾。
- **修正**：改为"可选"。

---

## [1.0.7] — 2026-03-03 JST · commit `a1de819`

### 修正：03_调度逻辑规格.md + TECHNICAL_DEBT.md（外部审查 2B 修正）

针对外部审查员 2B（`period=0` 记录的排序局限）评估结果：**接受**，并作如下文档修正。

#### 问题确认

`override.py` 中所有三处 `sort(key=lambda sc: (sc.date, sc.period))` 均不含 `custom_start` 字段。当同一日期存在多个 `period=0` 的记录（同天多次使用 `new_start_time` 调课）时，排序键完全相同，实际顺序为 Python 稳定排序保留前一步的相对顺序，不保证按 `custom_start` 时间排列。

#### 修正：03_调度逻辑规格.md §4.5（已于 [1.0.6] 提交中更新）

- 在 Override 后处理步骤 1（`result.sort`）说明中加注已知局限。

#### 修正：03_调度逻辑规格.md §5.3（本次新增）

- 在 `_reassign_session_keys` 组内排序说明后加注相同局限（引用 TECHNICAL_DEBT.md TD-02）。

#### 新增：TECHNICAL_DEBT.md TD-02

- 记录三处排序调用均未含 `custom_start` 的代码级问题，提供建议修正方案（排序键改为三元组 `(date, period, custom_start)`）。

---

## [1.0.6] — 2026-03-03 JST · commit `13ddaf1`

### 修正：03_调度逻辑规格.md（自审后修正）

经逐行比对 `engine/scheduler.py`、`engine/override.py`、`models/school_config.py`、`models/teacher_config.py` 及 `config/school_config.json`，文档整体准确，发现以下2处措辞问题，均在 §2.4 Override 字段说明：

#### 1. Override `period` 字段分组不准确

- **问题**：`period` 字段被归入 "skip 和 makeup 使用" 分组，但 `_apply_skip` 函数仅读取 `course_id` 和 `date`，完全不使用 `period`。该字段仅属于 makeup。
- **修正**：将分组拆分为 "skip / makeup 共用"（仅 `date`）和 "makeup 专用"（`period`），并在 `period` 描述中加注 skip 不使用此字段。

#### 2. `new_start_time` 描述措辞自相矛盾

- **问题**："与 new_period 互斥，优先级更高" 逻辑矛盾——"互斥"意味着不能共存，但"优先级更高"意味着可以共存。代码实际行为（`_apply_reschedule`）是：允许两者同时存在，`new_start_time` 优先（`new_period` 被忽略，`period` 固定设为 0）。
- **修正**：改为"与 new_period 二选一，如同时提供则本字段优先（new_period 被忽略，period 固定设为 0）"。

---

## [1.0.5] — 2026-03-03 JST · commit `d18659e`

### 修正：02_架构设计.md + TECHNICAL_DEBT.md（1A 重新评估）

#### 背景

上一轮对审查员 1A（"TeacherConfig 遗漏 appearance 字段"）的处理过于简单——仅核查了 `TeacherConfig` dataclass 不含该字段，而忽略了 `Appearance` 类本身定义于 `teacher_config.py` 这一架构信号。

用户指出：`Appearance` 定义在 `teacher_config.py` 是历史设计痕迹（外观参数曾属于教师配置，后迁移至 `settings.json`），迁移时代码未完整清理。这一信息对重写团队有重要参考价值。

#### 修正：02_架构设计.md §3.2（Appearance 节后新增设计背景说明）

- 补充说明 `Appearance` 定义位置与实际使用位置不一致的历史原因：外观参数原属教师配置，后迁移为全局配置，类定义留在原文件未移动。
- 提示重写团队：建议将 `Appearance` 定义移至 `app_settings.py` 或独立模块，使定义位置与逻辑归属一致。

#### 修正：TECHNICAL_DEBT.md TD-01（扩充）

- 将原有的"module docstring 过时"条目扩充为完整的设计迁移遗留说明，涵盖：Appearance 类定义位置问题、跨模块 import 方向颠倒、module docstring 残留三个方面。

---

## [1.0.4] — 2026-03-03 JST · commit `9ee07d1`

### 修正：02_架构设计.md（第二轮外部审查后修正）

以下为对外部审查员反馈的处理结果：

#### 1A — 驳回：TeacherConfig 中不存在 `appearance` 字段

审查员认为应将 `appearance: Appearance` 加入 `TeacherConfig` 代码片段。经代码核查，**审查员有误**：

- `TeacherConfig` dataclass（`teacher_config.py:71-78`）确实无 `appearance` 字段。
- `Appearance` 类定义于同文件，但由 `AppSettings` 使用，保存于 `settings.json`，与 `teacher_config.json` 无关。
- 文档现行描述正确，无需修改。

> **发现副作用**：`teacher_config.py` 模块 docstring（第3行）中列有 `appearance{}`，但代码实际不存储它——这是一处代码注释陈旧（stale docstring）。已记录于项目根目录新增的 `TECHNICAL_DEBT.md`（TD-01）。

#### 1B — 已完成：`AppSettings` 中 `Appearance` 来源注明

审查员建议在 §3.3 中明确指出 `Appearance` 复用自 `teacher_config.py`。核查后，文档已有此注释（`# 复用 teacher_config.py 中的 Appearance 数据类`），无需额外修改。

#### 2A — 修正：§1 窗口期参数说明（已实施）

- **问题**：§1 架构概述将窗口期描述为固定的"上课前 10 分钟至上课开始后 30 分钟"，未体现其可配置性（与 §3.2 中 `Settings` 的定义及 `01_业务需求.md` 不一致）。
- **修正**：改为"默认课前 10 分钟至课后 30 分钟，可通过 `Settings.pre_class_minutes` / `post_class_minutes` 配置"。

#### 2B — 修正：§4 补充 `intensive` 类型不参与排课（已实施）

- **问题**：§4 课程类型体系开头写"所有课程均恰好产生 14 次授课记录"，但 `scheduler.py:35-36` 对 `intensive` 类型直接 `return []`，不生成任何记录。
- **修正**：将"所有课程"限定为"排课引擎支持的6种类型"，并补充注明 `intensive` 不参与自动排课。

---

## [1.0.3] — 2026-03-03 JST · commit `0fb313b`

### 修正：02_架构设计.md（自审后修正）

以下4处修正均以代码为基准：

#### 1. 修正架构概述：轮询频率（§1）

- **问题**：原文档"应用每分钟检查一次"与代码不符。`main.py` 中 `TICK_MS = 30_000`（30,000毫秒），即每30秒轮询一次。
- **修正**：改为"每 30 秒检查一次"。

#### 2. 修正架构概述：配置文件数量（§1）

- **问题**：原文档"双文件 JSON 配置"仅提及 `school_config.json` 与 `teacher_config.json`，忽略了 `settings.json`（存储当前激活的教师配置路径及外观参数）。实际为三文件架构（§6 已正确列出三个文件，但概述描述不一致）。
- **修正**：将"双文件 JSON 配置"改为"三文件 JSON 配置"，并在描述中补充 `settings.json` 的用途。

#### 3. 补充目录结构：`gui/icon.py`（§2）

- **问题**：目录树中 `src/gui/` 下缺少 `icon.py`，但该文件实际存在，负责加载 `assets/icon.png` 并在文件缺失时程序化绘制回退图标。
- **修正**：在目录树 `gui/` 下补充 `icon.py` 条目及说明。

#### 4. 澄清课程类型表"使用回次"列含义（§4）

- **问题**："使用回次"一列对 Q 系课程的含义存在歧义。Q1 显示"01–07"，但这是 `CourseType.session_keys`（日期查找键），而非最终 `ScheduledClass.session_key`——Q系课程实际生成14条记录，`session_key` 始终为 "01"–"14"，易被误读为只有7次课。
- **修正**：在课程类型表下方新增注意说明，阐明"使用回次"是日期查找键范围，Q 系课程的实际 `session_key` 从 "01" 重新递增至 "14"。

---

## [1.0.2] — 2026-03-03 JST · commit `69c6e41`

### 修正：01_业务需求.md（第二轮代码审查后修正）

以下5处修正均以代码为基准：

#### 1. 修正出勤码管理的双向性描述（§2.1，§3.2 场景5）

- **问题一（§2.1）**：原文档"手动录入"功能描述仅提到"来源为既有系统"，未提及本工具自带的随机码生成功能，导致与既有系统的关系描述不完整。
- **修正**：将 §2.1 功能类别"手动录入"更名为"出勤码管理"，说明码既可来自既有系统（教师手动获取后粘贴），也可由工具直接生成（随机4位数字，再由教师手动录入既有系统）；明确工具仅负责展示，不自动对接。
- **问题二（§3.2 场景5）**：场景5描述未区分临时码与持久码的行为差异，缺少临时码的30分钟TTL说明。
- **修正**：场景5补充"临时码行为"（30分钟TTL、仅存内存、优先级最高、适用临时情况）和"持久码"（通过配置界面保存，跨会话有效）的详细说明，并将TTL数字从错误的"40分钟"更正为正确的"30分钟"（`timedelta(minutes=30)`，见 `main.py:202`）。

#### 2. 新增出勤码数据结构说明（§4.2.3）

- **问题**：§4.2 教师个人配置部分未说明出勤码字典的存储结构，而出勤码是 `teacher_config.json` 的核心字段之一，键格式为 `{course_id}_{session_key}`。
- **修正**：在 §4.2.2（例外调整记录）之后新增 **§4.2.3 出勤码（Attendance Codes）**，说明键格式、值格式、持久化行为，以及临时码（内存中、不写入此字典）与持久码的区别。

#### 3. 新增调整类型实际使用说明（§5.6）

- **问题**：§5.6 对三种调整类型（停课/补课/调课）的描述给人三者均等使用的印象，但实际配置文件（如 `邵_teacher_config.json`）中所有调整记录均为 `reschedule` 类型，UI 也仅提供调课的添加入口。
- **修正**：在 §5.6.4 之后新增"当前实践说明"注释框，说明调课是当前唯一使用的调整类型，停课/补课需直接编辑 JSON（无 UI 入口）。

#### 4. 修正配置界面基本配置区描述（§7.2）

- **问题一**：原文档"配置保存按钮，支持另存为新文件"描述有误——保存按钮位于对话框底部的 `QDialogButtonBox`（非基本配置区），且不存在"另存为新文件"功能。
- **问题二**：原文档未提及冲突检测按钮（`btn_conflict`），而该按钮位于授業标签页（即基本配置区），是课程配置的重要操作入口。
- **修正**：移除"配置保存按钮，支持另存为新文件"；改为"提供冲突检测按钮（衝突検出），检测当前课程配置是否存在时间冲突"。

---

## [1.0.1] — 2026-03-03 18:34 JST · commit `efb48de`

### 修正：01_业务需求.md（代码审查后修正）

以下6处修正均以代码为基准，确保文档与现行实现一致：

#### 1. 新增 course_id 字段说明（§4.2.1）

- **问题**：原文档课程字段表中缺少 `course_id`，而该字段是系统的核心唯一标识符——所有 Override 通过 `course_id` 关联课程，出勤码以 `{course_id}_{session_key}` 为键存储。
- **修正**：在4.2.1课程字段表顶部新增"课程唯一ID"行，注明其用途、格式及唯一性要求。

#### 2. 修正冲突处理规则（§5.3）

- **问题**：文档规则3"按课程名称字典序"为杜撰内容，`get_active_class` 的排序键仅为 `(abs(now - window_start), period)`，不含任何字典序比较。此外，规则1描述"更晚"不精确。
- **修正**：
  - 删除规则3（字典序）。
  - 将规则1改为"显示窗口开始时间与当前时刻绝对差值最小"，与代码实现一致。

#### 3. 新增随机码生成功能（§6.3，F-DW-06）

- **问题**：原文档完全未提及 `ConfigDialog` 预览标签页中的"コード生成"按钮功能。实际实现为：为当前所选课程的全部回次生成4位随机数字码（`random.randint(0, 9999):04d`）。
- **修正**：在§6.3功能需求表中新增 F-DW-06 条目。

#### 4. 修正展示窗口显示内容（§7.1，F-RT-04）

- **问题**：原文档要求展示窗口显示"课程名、今天是第几回、**当前日期**"，F-RT-04 亦列出"星期、时限、日期"。但 `AttendanceWindow.update_class` 实际只设置课程名（`label_course`）和第几回（`label_session`，格式"第X回"），不显示日期、星期或时限。
- **修正**：
  - §7.1 布局要求改为"课程名、今天是第几回（当前实现不显示日期）"。
  - F-RT-04 更新为反映实际显示字段。

#### 5. 窗口时长注明可配置（§5.2，AC-03）

- **问题**：原文档将"课前10分钟/课后30分钟"描述为固定值，但 `TeacherConfig.Settings` 中 `pre_class_minutes` 和 `post_class_minutes` 均可配置，存储于 `teacher_config.json` 的 `settings` 字段。
- **修正**：
  - §5.2 公式中将硬编码数值替换为参数名，并添加可配置说明。
  - AC-03 改为"默认 N=10/M=30，可配置"。

#### 6. 修正调整功能的 UI 范围说明（F-CA-03）

- **问题**：原文档暗示停课/补课/调课均可通过 UI 操作添加。实际上 `_on_add_adjustment` 仅调用 `RescheduleDialog`，只能创建 `reschedule` 类型的 Override；Skip 和 Makeup 类型无 UI 添加入口，需直接编辑 JSON。
- **修正**：F-CA-03 改为"UI 支持添加调课（Reschedule）；停课和补课可直接编辑 JSON 录入"。

---

## [1.0.0] — 2026-03-03 18:34 JST · commit `b131b53`

### 新增：中文文档集初始版本

为支持别语言重写，新建 `docs/cn/` 目录，创建以下8个文档：

#### README.md
- 文档集索引：列出全部7份文档的简介、推荐阅读顺序及参考资源路径。

#### 01_业务需求.md
- 基于 `docs/requirements.md` 整理的中文业务需求说明书。
- 涵盖：背景与问题、功能范围（In/Out Scope）、7个核心使用场景、三层数据模型（SchoolConfig / TeacherConfig / 运行时状态）、6条核心业务规则、功能需求表（F-CM/F-RT/F-DW/F-CA）、界面需求、技术要求、7条验收标准。

#### 02_架构设计.md
- 基于 `docs/findings.md` 整理的架构设计文档。
- 涵盖：架构概述、项目目录结构（含逐文件说明）、所有数据类定义（SchoolConfig / TeacherConfig / AppSettings / ScheduledClass）、6种课程类型体系、技术选型理由（PySide6 vs PyQt6 授权分析）、三个配置文件的关系说明。

#### 03_调度逻辑规格.md（743行）
- 排课引擎的完整算法规格，可供重写团队无需阅读源码即可实现。
- 涵盖：ScheduledClass 数据结构、单槽/双槽课程的日期解析算法（含 Q 课程 `actual_num` 公式推导）、三种 Override（Skip/Makeup/Reschedule）的详细应用逻辑、`_reassign_session_keys` 分组与编号规则、`compute_window` 与 `get_active_class` 算法、完整带真实日期数据的工作示例。

#### 04_数据格式规格.md
- 三个 JSON 配置文件的完整字段说明，含必填/可选标注。
- 涵盖：`school_config.json`（periods/course_types/semesters 全字段）、`teacher_config.json`（courses/overrides/attendance_codes/window_position/settings 全字段及 Override 三类型字段差异）、`settings.json`（active_config + 8个 appearance 字段）、开发模式与打包后的文件位置、首次运行初始化行为。

#### 05_界面规格.md（927行）
- UI 完整规格，含 ASCII 线框图。
- 涵盖：AttendanceWindow（窗口标志、基础尺寸、布局、右键菜单6项、出勤码输入流程、3级码优先级、4个信号）；TrayIcon（菜单3项、动态文本规则、ToolTip格式、单击行为）；ConfigDialog 5个标签页（授業/日程プレビュー/調整/外観/About）完整规格；CourseEditDialog 与 RescheduleDialog 子对话框；保存逻辑；窗口状态转换图。

#### 06_数据流图.md
- 从程序启动到出勤码显示的完整数据流，含 ASCII 流程图。
- 涵盖：`main()` 9步启动流程、`_tick()` 30秒定时器循环、`_code_for()` 三级码优先级、配置保存与加载新配置文件的信号传播链、`_resource()`/`_user_data_dir()` 文件路径解析（含 macOS .app 4层向上查找）、数据依赖关系图、完整时序图。

#### 07_平台差异说明.md
- macOS 与 Windows 平台差异的技术说明。
- 涵盖：`Qt.WindowType.Tool` 标志的平台差异及原因（macOS 失焦隐藏问题）、可写配置目录的路径计算差异（Windows：exe同级；macOS：.app外4级向上）、`LSUIElement` 配置（当前版本已启用）、构建与图标格式差异（.ico/.icns）、系统托盘位置差异、差异汇总对照表。
