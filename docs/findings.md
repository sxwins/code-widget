# Findings & Decisions — 出勤码展示工具

## Requirements（需求摘要）

### In Scope
- 基于学期课表推导每门课的授课日期（第1回～第N回）
- 教师以"周几+第几限 → 课程名"方式配置个人课程
- 上课前10分钟 ～ 上课后30分钟内，自动弹出置顶小窗
- 小窗：可拖动、始终置顶、醒目展示出勤码（教师手动输入/粘贴）
- 超出窗口期后自动隐藏/待机
- 支持停课 / 补课 / 调课（例外规则，优先级高于基础课表）
- 配置界面：课程管理、授课日预览、调整管理
- 打包为 Windows .exe + macOS .app（无需用户安装 Python）

### Out of Scope
- 不与学校系统对接、不自动获取出勤码
- 不处理学生端出勤登记
- 暂不支持集中讲义等特殊课型

## 数据模型（来自 requirements.md §5）

### SchoolConfig（全校通用，school_config.json）

6限制（docs/time_slot.png 確認済み）＋2セメスター構造（spring_2026 / autumn_2026）。
`weekday_dates` の各配列は index 0 = 第1回、index 13 = 第14回 に対応。

```json
{
  "periods": {
    "1": {"start": "08:50", "end": "10:30"},
    "2": {"start": "10:40", "end": "12:20"},
    "3": {"start": "13:10", "end": "14:50"},
    "4": {"start": "15:00", "end": "16:40"},
    "5": {"start": "16:50", "end": "18:30"},
    "6": {"start": "18:40", "end": "20:20"}
  },
  "semesters": [
    {
      "semester_id": "spring_2026",
      "semester_name": "2026春セメスター",
      "semester_start": "2026-04-15",
      "semester_end": "2026-07-28",
      "weekday_dates": {
        "Monday":    ["2026-04-20", "2026-04-27", ..., "2026-07-27"],
        "Tuesday":   ["2026-04-21", ..., "2026-07-28"],
        "Wednesday": ["2026-04-15", ..., "2026-07-22"],
        "Thursday":  ["2026-04-16", "2026-04-23", "2026-05-07", ..., "2026-07-23"],
        "Friday":    ["2026-04-17", "2026-04-24", "2026-05-08", ..., "2026-07-24"]
      }
    },
    {
      "semester_id": "autumn_2026",
      "semester_name": "2026秋セメスター",
      "semester_start": "2026-09-25",
      "semester_end": "2027-01-18",
      "weekday_dates": {
        "Monday":    ["2026-09-28", ..., "2027-01-04", "2027-01-18"],
        "Tuesday":   ["2026-09-29", ..., "2027-01-05", "2027-01-12"],
        "Wednesday": ["2026-09-30", ..., "2027-01-06", "2027-01-13"],
        "Thursday":  ["2026-10-01", ..., "2027-01-07", "2027-01-14"],
        "Friday":    ["2026-09-25", ..., "2027-01-08", "2027-01-15"]
      }
    }
  ]
}
```

**休講・跳過日メモ（spring_2026）：**
- 月 5/4（みどりの日）、火 5/5（こどもの日）、水 5/6（振替休日）、木 4/30・金 5/1（休）

**休講・跳過日メモ（autumn_2026）：**
- 月 11/2（学祭片付）、金 10/30（学祭準備）、火 12/22（SDGsフォーラム）
- 月～金 12/23～1/3前後（年末年始）、月 1/11（成人の日）

### TeacherConfig（个人配置，teacher_config.json）
```json
{
  "teacher_name": "田中先生",
  "courses": [
    {
      "id": "course_001",
      "name": "微积分A",
      "weekday": "Monday",
      "period": 2
    }
  ],
  "overrides": [
    {
      "type": "skip",
      "course_id": "course_001",
      "date": "2026-05-04"
    },
    {
      "type": "makeup",
      "course_id": "course_001",
      "date": "2026-05-09",
      "period": 3
    },
    {
      "type": "reschedule",
      "course_id": "course_001",
      "original_date": "2026-06-01",
      "original_period": 2,
      "new_date": "2026-06-03",
      "new_period": 4
    }
  ],
  "window_position": {"x": 100, "y": 100}
}
```

## 业务规则（来自 requirements.md §6）

| 规则 | 说明 |
|------|------|
| 显示窗口 | 课程开始前10分钟 ～ 课程开始后30分钟 |
| 多课冲突 | 优先"窗口开始时间更接近当前时间"的课程（或课时序号更小） |
| 非窗口期 | 待机/隐藏（可配置），允许手动打开 |
| 停课优先 | 调整规则优先级高于基础课表推导 |
| 回次计算 | 按"实际授课发生顺序"（应用调整后）重新编号 |

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **PySide6**（不用 PyQt6） | 见下方详细说明 ↓ |
| JSON 配置文件 | 纯文本、可移植、无需数据库、可手动编辑 |
| 双文件配置 | school_config.json（全校/可共享）+ teacher_config.json（个人） |
| PyInstaller 打包 | 独立可执行，用户无需安装任何依赖 |
| 排课引擎纯 Python | 与 GUI 解耦，便于测试 |

### GUI 框架选型：PySide6（已确认）

**结论：** 选用 PySide6（社区版，LGPL v3），不购买商业许可证。

#### 授权分析
| 框架 | 免费版授权 | 闭源商业分发 |
|------|-----------|------------|
| PyQt6 | GPL v3 | 不允许（须购买 Riverbank 商业许可） |
| PySide6 | **LGPL v3** | **允许**（满足 LGPL 条件即可） |

本项目为学校内部部署（教师端工具，不对外销售、不向第三方分发），属于"内部使用"场景。
**LGPL v3 的分发条款在内部使用时不被触发**，因此社区版完全合规，无需付费。

#### 选择 PySide6 的技术理由
1. **官方维护**：由 Qt Company 直接维护，是 Qt for Python 的官方绑定，长期支持有保障
2. **工具链完整**：附带 `pyside6-deploy`、`pyside6-uic`、`pyside6-rcc` 等官方工具，打包流程更规范
3. **文档质量**：与 Qt 官方文档深度集成，API 参考更完整
4. **API 兼容**：与 PyQt6 约 90% 兼容，未来迁移成本低
5. **社区增长**：官方背书后社区活跃度持续提升，学习资料丰富

#### 未来注意事项
- 若将来需要向校外分发打包版本（.exe/.app），需确保 Qt DLL 以独立文件形式存在（不完全合并进单一 exe），以满足 LGPL 的"可替换库"要求；或届时购买 Qt 商业许可证。
- 通过 `pip install pyside6` 安装的社区版用于内部使用完全合规。

## Project Structure（确定）
```
CodeWidget/
├── docs/
│   ├── requirements.md      # 需求文档
│   ├── task_plan.md         # 项目规划
│   ├── findings.md          # 本文件（设计决策）
│   ├── progress.md          # 进度日志
│   └── time_slot.png        # 时限表原始图片
├── src/
│   ├── main.py              # 程序入口，初始化 QApplication + 系统托盘
│   ├── engine/
│   │   ├── scheduler.py     # 排课引擎：推导授课日、计算窗口期
│   │   └── override.py      # 调整规则应用（skip/makeup/reschedule）
│   ├── models/
│   │   ├── school_config.py # SchoolConfig 数据类 + JSON 读写
│   │   └── teacher_config.py# TeacherConfig + Override 数据类
│   ├── gui/
│   │   ├── tray.py          # 系统托盘
│   │   ├── attendance_window.py  # 出勤码展示小窗（置顶、可拖动）
│   │   └── config_dialog.py     # 配置界面（课程管理、预览、调整）
│   └── utils/
│       └── time_utils.py    # 时间工具函数
├── assets/                  # 图标等资源
├── config/
│   ├── school_config.json   # 全校通用配置（含实际6限时间）
│   └── teacher_config.json  # 教师个人配置模板
├── tests/                   # 单元测试
├── requirements.txt         # Python 依赖
└── build/                   # PyInstaller 输出（gitignored）
```

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| （暂无） | — |

## Resources
- 需求文档：`docs/requirements.md`
- 时限表原图：`docs/time_slot.png`
- PySide6 文档：https://doc.qt.io/qtforpython-6/
- PyInstaller 文档：https://pyinstaller.org/

---
*Update this file after every 2 view/browser/search operations*
