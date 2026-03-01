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
```json
{
  "semester_name": "2026春季学期",
  "semester_start": "2026-04-06",
  "semester_end": "2026-07-25",
  "weekday_dates": {
    "Monday":    ["2026-04-06", "2026-04-13", ...],
    "Tuesday":   [...],
    "Wednesday": [...],
    "Thursday":  [...],
    "Friday":    [...]
  },
  "periods": {
    "1": {"start": "08:50", "end": "10:20"},
    "2": {"start": "10:30", "end": "12:00"},
    "3": {"start": "13:00", "end": "14:30"},
    "4": {"start": "14:40", "end": "16:10"},
    "5": {"start": "16:20", "end": "17:50"},
    "6": {"start": "18:30", "end": "20:00"},
    "7": {"start": "20:10", "end": "21:40"}
  }
}
```

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
| PySide6（非 PyQt6） | LGPL 授权更友好；Qt6 原生支持 always-on-top、系统托盘、跨平台 |
| JSON 配置文件 | 纯文本、可移植、无需数据库、可手动编辑 |
| 双文件配置 | school_config.json（全校/可共享）+ teacher_config.json（个人） |
| PyInstaller 打包 | 独立可执行，用户无需安装任何依赖 |
| 排课引擎纯 Python | 与 GUI 解耦，便于测试 |

## Project Structure（建议）
```
CodeWidget/
├── requirements.md          # 需求文档（已有）
├── task_plan.md             # 项目规划
├── findings.md              # 本文件
├── progress.md              # 进度日志
├── src/
│   ├── main.py              # 程序入口，初始化 QApplication + 系统托盘
│   ├── engine/
│   │   ├── scheduler.py     # 排课引擎：推导授课日、计算窗口期
│   │   └── override.py      # 调整规则应用（stop/makeup/reschedule）
│   ├── models/
│   │   ├── school_config.py # SchoolConfig 数据类 + JSON 读写
│   │   └── teacher_config.py# TeacherConfig + Override 数据类
│   ├── gui/
│   │   ├── tray.py          # 系统托盘
│   │   ├── attendance_window.py  # 出勤码展示小窗（置顶、可拖动）
│   │   └── config_dialog.py     # 配置界面（课程管理、预览、调整）
│   └── utils/
│       └── time_utils.py    # 时间工具函数
├── assets/
│   └── icon.png             # 托盘图标
├── config/
│   ├── school_config.json   # 全校通用配置（示例/模板）
│   └── teacher_config.json  # 教师个人配置
└── build/                   # PyInstaller 输出
```

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| （暂无） | — |

## Resources
- 需求文档：`requirements.md`（项目根目录）
- PySide6 文档：https://doc.qt.io/qtforpython-6/
- PyInstaller 文档：https://pyinstaller.org/

---
*Update this file after every 2 view/browser/search operations*
