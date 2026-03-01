# Task Plan: 出勤码展示工具（CodeWidget）

## Goal
开发一个轻量级桌面工具，帮助教师在上课前后自动弹出置顶小窗展示出勤码，支持按学期课表智能提示、手动输入码、以及停课/补课/调课调整，打包为 Windows/macOS 独立可执行文件。

## Current Phase
Phase 6: 测试与验收

## Phases

### Phase 1: 需求分析与理解
- [x] 阅读并理解 requirements.md
- [x] 明确项目范围（In Scope / Out of Scope）
- [x] 识别核心数据模型（SchoolConfig / TeacherConfig / Overrides / RuntimeState）
- [x] 确认技术栈（Python + PyQt6/PySide6，跨平台，打包为独立 exe/app）
- **Status:** complete

### Phase 2: 架构设计
- [x] 确定项目目录结构
- [x] 设计数据模型（JSON 配置格式：school_config + teacher_config）
- [x] 定义6种课程类型（spring/autumn/Q1〜Q4）及其 session_keys 映射规则
- [x] 确认完整业务逻辑数据流（见 findings.md "業務ロジック"）
- [x] 填充实际配置数据（6限时间表、春秋两学期14回授课日、邵先生课程配置）
- [x] 记录所有决策到 findings.md
- **Status:** complete

### Phase 3: 核心逻辑实现
- [x] 数据模型类（SchoolConfig、TeacherConfig、Course、Override）
- [x] JSON 配置文件读写（load/save school_config + teacher_config）
- [x] 排课引擎：course_type + slot → 授课日期列表（含 Q 系双槽位）
- [x] Override 应用：skip / makeup / reschedule 叠加到基础日期列表
- [x] 显示窗口判定：当前时间 vs window_start/window_end
- [x] 多课冲突消解：选优先显示课程
- **Status:** complete

### Phase 4: GUI 实现
- [x] 系统托盘 + 主程序生命周期管理
- [x] 出勤码展示小窗（置顶、可拖动、醒目大字）
- [x] 配置界面（课程录入、学期配置导入）
- [x] 授课日预览（第1回～第14回日期表）
- [x] 调整管理界面（停课/补课/调课 CRUD）
- **Status:** complete

### Phase 5: 打包与分发
- [x] Windows：PyInstaller 打包为独立 .exe（onefile + windowed）
- [x] 在 pyproject.toml 添加 PyInstaller 为 dev 依赖
- [x] 创建 CodeWidget.spec（含 config/ assets/ 数据文件）
- [x] 测试打包后运行（EXE 可独立启动，config/ 同目录自动生成）
- **Status:** complete

### Phase 6: 测试与验收
- [ ] 验证全部 7 条验收标准（requirements.md §12）
- [ ] 边界测试（跨日期、窗口边界、多课冲突）
- [ ] 文档整理
- **Status:** pending

## Key Questions
1. GUI 框架：PyQt6 还是 PySide6？（授权差异：PyQt6 GPL / PySide6 LGPL）
2. 配置文件：JSON 格式，分 school_config.json / teacher_config.json 两个文件？
3. 系统托盘行为：点击托盘图标打开配置界面还是展示当前状态？
4. 多课冲突时的优先级规则是否需要用户可配置？
5. 窗口位置记忆用 JSON 还是 QSettings？

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Python + **PySide6**（确认） | 官方 Qt 绑定；LGPL v3 在学校内部使用场景完全合规免费；工具链完整；长期维护有保障 |
| 不选 PyQt6 | GPL v3 免费版不允许闭源分发；商业版需付费；PySide6 技术上无明显劣势 |
| JSON 配置文件 | 纯文本、可移植、可手动编辑，无需数据库 |
| 两层配置文件 | school_config.json（全校通用）+ teacher_config.json（个人课程+调整） |
| PyInstaller 打包 | 生成独立可执行文件，用户无需安装 Python |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| （暂无） | — | — |

## Notes
- 需求文档：requirements.md（已读完）
- 技术栈确认：Python + PySide6 + PyInstaller
- 更新 Phase 状态：pending → in_progress → complete
- 每次重大决策前重读本文件
