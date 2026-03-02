# Progress Log — 出勤码展示工具

## Session: 2026-03-01

### Phase 1: 需求分析与理解
- **Status:** complete
- **Started:** 2026-03-01
- Actions taken:
  - 读取并完整理解 requirements.md（共 263 行）
  - 提取项目背景、范围、数据模型、业务规则、技术要求
  - 确认技术栈：Python + PySide6 + PyInstaller，跨平台（Windows/macOS）
  - 建立 task_plan.md、findings.md、progress.md 三个规划文件
- Files created/modified:
  - `task_plan.md`（创建）
  - `findings.md`（创建，含完整数据模型设计与目录结构）
  - `progress.md`（本文件，创建）

### Phase 2: 架构设计
- **Status:** in_progress
- Actions taken:
  - 技术选型确认：PySide6（LGPL v3，学校内部使用合规）
  - 从 docs/time_slot.png 提取6限时间数据，写入 config/school_config.json
  - 从 docs/2026年度授業日程.pdf 提取春・秋両セメスター全授業日（各曜日14回分）
  - school_config.json schema 升级为双学期结构（semesters 数组）
  - 文档整理：planning files + 参考资料全部移入 docs/ 目录
  - requirements.md §5.1.2 更新：7限→6限，附实际时间
  - findings.md 更新：数据模型、目录结构、PySide6 选型理由、schema 样例
- Files created/modified:
  - `config/school_config.json`（重构：periods 实际值 + 两学期 weekday_dates 完整数据）
  - `docs/findings.md`（更新：数据模型、选型理由、目录结构）
  - `docs/requirements.md`（§5.1.2 修正：7限→6限）
  - `docs/task_plan.md`（决策表更新：PySide6 确认及理由）
  - 在 findings.md 中设计了 JSON 配置格式（SchoolConfig + TeacherConfig + Overrides）
  - 设计了建议的项目目录结构（src/engine, src/models, src/gui, src/utils）
  - 记录了技术决策（PySide6 LGPL、双文件配置、排课引擎与 GUI 解耦）
- Files created/modified:
  - `findings.md`（更新：数据模型、目录结构、技术决策）
- 待完成：
  - [ ] 与用户确认架构方向
  - [ ] 细化排课引擎接口设计
  - [ ] 确认 GUI 交互流程

## Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| （开发阶段尚未开始测试） | — | — | — | — |

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| — | （暂无） | — | — |

  - 从 docs/邵_教員時間割表.pdf 提取邵先生全课程（春6门+秋8门），生成 config/邵_teacher_config.json
  - 确认并文档化完整业务逻辑数据流（findings.md "業務ロジック"）
  - Phase 2 标记为 complete，Phase 3 开始

## Phase 3 完成（2026-03-01）

- 实现 src/models/school_config.py、teacher_config.py
- 实现 src/engine/scheduler.py（resolve_course_schedule, compute_window, get_active_class）
- 实现 src/engine/override.py（apply_overrides, _reassign_session_keys）
- 实现 src/utils/time_utils.py
- 测试：22 个测试全部通过

## Phase 4 完成（2026-03-01）

- 实现 src/gui/attendance_window.py（AttendanceWindow — 置顶浮窗，72pt 4位出勤码）
- 实现 src/gui/tray.py（TrayIcon — 系统托盘，菜单，状态提示）
- 实现 src/gui/config_dialog.py（ConfigDialog — 3标签页：课程/预览/调整）
- 实现 src/main.py（QApplication + 30s QTimer + 全部 widget 接线）
- 新增 docs/plans/2026-03-01-phase4-gui-design.md（设计文档）
- 新增 docs/plans/2026-03-01-phase4-gui-implementation.md（实现计划）
- 新增 CLAUDE.md（项目配置）
- 测试：31 个测试全部通过（22 engine + 3 attendance + 3 config + 3 tray）

## Phase 4+ 追加実装（2026-03-01〜03-02）

Phase 4 完成後に追加した機能（38 tests passing）:
- 出席コードキー変更: `{course_id}_{date}` → `{course_id}_{session_key}`
- 外観タブ（コードフォント・色・背景・ボーダー + 科目名フォント設定）
- 保存後ダイアログを閉じない（QTimer フィードバック）
- 调整タブ: 行選択 + 追加/編集/削除ボタン（courses タブと同パターン）
- プレビューで `{n}限` 表示
- Q1 課 session_key バグ修正: `_reassign_session_keys` でマルチスロットコースを course_id でグループ化
- アイコン: 実際の PNG ファイル使用 (src/assets/icon.png)
- 丸角ウィンドウ（WA_TranslucentBackground + 丸角矩形描画）
- 一時コード機能（右クリック入力→30分有効、_temp_codes, code_entered/code_cleared シグナル）
- 衝突検出ボタン（時間窓オーバーラップ判定）
- 調整ダイアログ: 元日時行削除、開始時刻ラベル

## Phase 5 完成（2026-03-02）

- uv add --dev pyinstaller pillow
- 創建 CodeWidget.spec（onefile/windowed，含 icon + configs）
- icon.png → icon.ico（Pillow, 16/32/48/256px）
- main.py: _resource()/_user_data_dir() frozen-mode path helpers
- main.py: _ensure_user_config() 首次运行自动复制模板
- icon.py: frozen mode 使用 sys._MEIPASS
- EXE 构建成功：dist/CodeWidget.exe (45MB)
- 验证：EXE 启动正常，dist/config/ 自动生成，15 courses + 3 overrides

## Phase 6 验收（2026-03-02）

### 7 条验收标准核查
| AC | 描述 | 状态 |
|----|------|------|
| AC1 | 周几第几限→课程名配置+保存 | ✓ ConfigDialog 课程 tab |
| AC2 | 按学期识别授课日，标识第几回+预览 | ✓ scheduler + 预览 tab |
| AC3 | 开课前10分→开课后30分自动显示置顶窗 | ✓ pre_class=10, post_class=30 |
| AC4 | 可拖动、始终置顶、面积小 | ✓ WindowStaysOnTopHint + mouseMoveEvent |
| AC5 | 粘贴出勤码，醒目展示 | ✓ 72pt 显示 + 临时码 |
| AC6 | 超窗口期后自动隐藏 | ✓ _tick() active=None → hide() |
| AC7 | 预览授课日，停课/补课/调课 CRUD，保存后生效 | ✓ 调整 tab |
- 38 tests passing

## Phase 6 完成：打包前整理（2026-03-02）

### 代码整理内容
- **docstrings 追加** (config_dialog.py): `_build_*` 全 5 件、`CourseEditDialog._build_ui/_on_accept`、`RescheduleDialog._build_ui/_prefill/_on_*`、`_populate_*`、`_refresh_preview`、`_on_check_conflicts`、`_on_save` 等 20+ メソッド
- **docstrings 追加** (school_config.py): `get_semester`、`load_school_config`
- **docstrings 追加** (teacher_config.py): `load_teacher_config`、`save_teacher_config`、`_strip_none`
- **死代码削除** (teacher_config.py): `Settings.standby_on_no_class` — load/save にはあるが `_tick()` で一切参照されていなかった
- **死枝削除** (main.py): `on_position_changed` の `window_position is None` 分岐 — `WindowPosition` は常に `default_factory` で生成されるため到達不能

### 変更後テスト
- 38 tests passing ✓

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Phase 7: 打包与发布 |
| Where am I going? | PyInstaller でパッケージング → 配布 |
| What's the goal? | 开发出勤码展示工具：置顶小窗、按课表自动提示、支持调整、打包为独立 exe |
| What have I learned? | 見 findings.md；完整実装済み、38 tests passing |
| What have I done? | Phase 1-6 完成 + 7 AC 全部验证通过 + 打包前代码整理 |

---
*Update after completing each phase or encountering errors*
