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

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Phase 2: 架构设计（in_progress） |
| Where am I going? | Phase 3: 核心逻辑实现 → Phase 4: GUI → Phase 5: 打包 → Phase 6: 测试 |
| What's the goal? | 开发出勤码展示工具：置顶小窗、按课表自动提示、支持调整、打包为独立 exe/app |
| What have I learned? | 见 findings.md：数据模型设计、业务规则、技术栈、目录结构 |
| What have I done? | 读完需求文档，建立规划文件，完成数据模型与目录结构设计 |

---
*Update after completing each phase or encountering errors*
