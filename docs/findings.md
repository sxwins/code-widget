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
        "Monday": {"01": "2026-04-20", "02": "2026-04-27", ..., "14": "2026-07-27"},
        "Tuesday": {"01": "2026-04-21", ..., "14": "2026-07-28"},
        "Wednesday": {"01": "2026-04-15", ..., "14": "2026-07-22"},
        "Thursday": {"01": "2026-04-16", "02": "2026-04-23", "03": "2026-05-07", ..., "14": "2026-07-23"},
        "Friday": {"01": "2026-04-17", "02": "2026-04-24", "03": "2026-05-08", ..., "14": "2026-07-24"}
      }
    },
    {
      "semester_id": "autumn_2026",
      "semester_name": "2026秋セメスター",
      "semester_start": "2026-09-25",
      "semester_end": "2027-01-18",
      "weekday_dates": {
        "Monday": {"01": "2026-09-28", ..., "13": "2027-01-04", "14": "2027-01-18"},
        "Tuesday": {"01": "2026-09-29", ..., "13": "2027-01-05", "14": "2027-01-12"},
        "Wednesday": {"01": "2026-09-30", ..., "13": "2027-01-06", "14": "2027-01-13"},
        "Thursday": {"01": "2026-10-01", ..., "13": "2027-01-07", "14": "2027-01-14"},
        "Friday": {"01": "2026-09-25", ..., "13": "2027-01-08", "14": "2027-01-15"}
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

### 课程类型（course_types，定义于 school_config.json）

| 类型 | 学期 | 使用回次 | 每周次数 | 槽位数 |
|------|------|----------|----------|--------|
| spring | spring_2026 | 01–14 | 1 | 1（单曜日×单限） |
| autumn | autumn_2026 | 01–14 | 1 | 1（单曜日×单限） |
| Q1 | spring_2026 | 01–07 | 2 | 2（两曜日×各1限） |
| Q2 | spring_2026 | 08–14 | 2 | 2（两曜日×各1限） |
| Q3 | autumn_2026 | 01–07 | 2 | 2（两曜日×各1限） |
| Q4 | autumn_2026 | 08–14 | 2 | 2（两曜日×各1限） |

全类型均为14次授课（春/秋：14周×1次；Q：7周×2次）。

### TeacherConfig（个人配置，teacher_config.json）
```json
{
  "teacher_name": "田中先生",
  "courses": [
    {
      "id": "course_001",
      "name": "微積分A",
      "course_type": "spring",
      "slots": [
        {"weekday": "Wednesday", "period": 3}
      ]
    },
    {
      "id": "course_002",
      "name": "線形代数B",
      "course_type": "Q1",
      "slots": [
        {"weekday": "Wednesday", "period": 2},
        {"weekday": "Friday",    "period": 3}
      ]
    }
  ],
  "overrides": [
    {
      "type": "skip",
      "course_id": "course_001",
      "date": "2026-05-13"
    },
    {
      "type": "makeup",
      "course_id": "course_001",
      "date": "2026-05-20",
      "period": 3
    },
    {
      "type": "reschedule",
      "course_id": "course_001",
      "original_date": "2026-06-03",
      "original_period": 3,
      "new_date": "2026-06-05",
      "new_period": 4
    }
  ],
  "window_position": {"x": 100, "y": 100},
  "settings": {
    "pre_class_minutes": 10,
    "post_class_minutes": 30,
    "standby_on_no_class": true
  }
}
```

## 業務ロジック（確定済み）

データ準備フェーズ完了。以下のロジックで「今日・今の時刻に出席コードを表示すべきか」を判定する。

---

### ステップ1：授業日付の解決

```
course.course_type
  → course_types[course_type]
      .semester_id   → semesters[semester_id].weekday_dates
      .session_keys  → 使用する回次キー（"01"〜"14" または "01"〜"07" 等）

course.slots[].weekday
  → weekday_dates[weekday]
      [session_key]  → 授業日付（YYYY-MM-DD）
```

**Q 系 course（Q1〜Q4）の場合：**
- 2つの slot（例：水曜2限・金曜3限）が同一 session_key を共有する
- session "01" = 第1週の水曜授業 + 第1週の金曜授業、というペアになる

| course_type | semester_id | session_keys | 週あたり回数 |
|------------|-------------|-------------|------------|
| spring | spring_2026 | 01〜14 | 1 |
| autumn | autumn_2026 | 01〜14 | 1 |
| Q1 | spring_2026 | 01〜07 | 2 |
| Q2 | spring_2026 | 08〜14 | 2 |
| Q3 | autumn_2026 | 01〜07 | 2 |
| Q4 | autumn_2026 | 08〜14 | 2 |

---

### ステップ2：授業時刻の解決

```
slot.period
  → periods[period].start  → 授業開始時刻（HH:MM）
```

| 限 | 開始 | 終了 |
|----|------|------|
| 1 | 08:50 | 10:30 |
| 2 | 10:40 | 12:20 |
| 3 | 13:10 | 14:50 |
| 4 | 15:00 | 16:40 |
| 5 | 16:50 | 18:30 |
| 6 | 18:40 | 20:20 |

---

### ステップ3：表示ウィンドウの判定

```
window_start = 授業開始時刻 − pre_class_minutes（デフォルト10分）
window_end   = 授業開始時刻 + post_class_minutes（デフォルト30分）

if window_start ≤ 現在時刻 ≤ window_end:
    → 出席コード表示ウィンドウを表示
```

---

### ステップ4：Override の適用（基礎課表より優先）

| タイプ | 動作 |
|--------|------|
| `skip` | 指定日付の授業をキャンセル（ウィンドウ非表示） |
| `makeup` | 新しい授業日付・限を追加（その日もウィンドウ表示対象） |
| `reschedule` | 元日付を skip + 新日付を makeup の組み合わせ |

Override 適用後に授業日付リストを再構築し、回次を実際の授業発生順で採番しなおす。

---

### ステップ5：複数課程が同時に命中した場合

優先順位：「window_start が現在時刻に最も近い課程」を表示。同点の場合は period 番号の小さい方を優先。

---

### ステップ6：非ウィンドウ期の動作

`standby_on_no_class: true` の場合 → 待機状態（システムトレイに格納）
教員が手動でウィンドウを開くことも可能。

---

### データフロー全体図

```
school_config.json                  teacher_config.json
├── periods[1〜6]         ←──────── courses[].slots[].period
└── semesters[]                      courses[].course_type
    └── weekday_dates     ←──────── courses[].slots[].weekday
        [weekday][回次]               + course_types[].session_keys
              ↓                               ↓
         授業日付 ──── Override適用 ────→ 確定授業日リスト
              ↓
         periods[period].start
              ↓
    window_start / window_end
              ↓
    現在時刻と比較 → 表示 / 待機
```

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
│   ├── school_config.json      # 全校通用配置（含实际6限时间 + 春秋两学期授课日）
│   ├── teacher_config.json     # 教师个人配置模板
│   └── teacher_A_config.json  # 担当教員実際設定（2026年度）
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
