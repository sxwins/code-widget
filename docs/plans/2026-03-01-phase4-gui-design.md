# Phase 4 GUI Design — 出勤码展示工具

**Date:** 2026-03-01
**Status:** Approved

---

## Overview

Implement the GUI layer on top of the completed Phase 3 engine (scheduler + override). The engine is fully tested and decoupled; the GUI layer only calls:

- `resolve_course_schedule(course, school_config)` → list of ScheduledClass
- `apply_overrides(scheduled, overrides)` → list of ScheduledClass
- `get_active_class(now, all_scheduled, school_config, settings)` → ScheduledClass | None

---

## Architecture

### Timer / Polling (Approach A — QTimer)

A single `QTimer` fires every **30 seconds**. On each tick:
1. Call `get_active_class(now(), all_scheduled, school_config, settings)`
2. If result changed from last tick: show/hide `AttendanceWindow`, update displayed course info

Rationale: Simple, zero threading complexity, 30s latency is imperceptible in a ±10-min window context. No issues with suspend/resume or DST.

### State Rebuilt on Config Change

When teacher saves config (overrides, courses), `main.py` rebuilds `all_scheduled` from scratch and resets the timer cycle. No stale cache.

---

## Components

### 1. `src/main.py` — Entry Point

- Load `config/school_config.json`
- Load teacher config (path stored in `QSettings` key `"teacher_config_path"`; default `config/邵_teacher_config.json`)
- Build `all_scheduled`:
  ```python
  all_scheduled = []
  for course in teacher_config.courses:
      base = resolve_course_schedule(course, school_config)
      all_scheduled.extend(apply_overrides(base, teacher_config.overrides))
  ```
- Instantiate `AttendanceWindow`, `TrayIcon`
- Start `QTimer(interval=30_000)` → `on_tick()`
- `on_tick()`: call `get_active_class`, show/hide window, update info if class changed

### 2. `src/gui/attendance_window.py` — Floating Code Window

**Visual layout (approx 340×160 px, white background):**

```
+------------------------------------------+
| 初年次セミナーA          第7回            |
|                                          |
|              1 2 3 4                     |  ← 72pt bold
|                                          |
|         [Edit / Paste]   [Clear]         |
+------------------------------------------+
```

**Behavior:**
- `Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool`
- Always-on-top, no system chrome
- Code field: `QLineEdit` styled as large display; read-only by default; "Edit / Paste" button makes it editable, focus returns to read-only after Enter/blur
- 4-digit code shown in **72pt bold** monospace font
- Drag: `mousePressEvent` records offset; `mouseMoveEvent` moves window; `mouseReleaseEvent` saves position to teacher_config `window_position`
- `update_class(sc: ScheduledClass)`: set course name label, session key label, keep existing code
- `clear_class()`: hide window

### 3. `src/gui/tray.py` — System Tray

- `QSystemTrayIcon` with a default icon (generated solid-color pixmap as fallback if no assets/icon.png)
- Tooltip: active class name, or "No active class"
- Context menu:
  - "Show window" / "Hide window" (toggles `AttendanceWindow.show()/hide()`)
  - "Settings…" → opens `ConfigDialog`
  - ─────────────
  - "Exit"
- Double-click tray icon → toggle window visibility

### 4. `src/gui/config_dialog.py` — Configuration Dialog

`QDialog`, three tabs:

#### Tab 1: Courses
- `QTableWidget` (columns: ID, Name, Type, Slots)
- Buttons: **Add**, **Edit**, **Delete**
- Add/Edit opens `CourseEditDialog` (sub-dialog): fields for course name, course_type (dropdown: spring/autumn/Q1/Q2/Q3/Q4), and slots (weekday + period; 1 or 2 rows based on type)
- Intensive courses shown greyed out / not editable

#### Tab 2: Schedule Preview
- `QComboBox` to select course
- `QTableWidget` showing session 01–14: columns = Session, Date, Weekday, Period, Notes
- Overridden sessions shown with italic text and "(調整)" note

#### Tab 3: Adjustments (Overrides)
- `QTableWidget` listing all overrides: Type, Course, Original Date, New Date, Period
- Buttons: **Add Skip**, **Add Makeup**, **Add Reschedule**, **Delete**
- Each Add opens a small sub-dialog with the relevant fields
- On change: preview tab auto-refreshes

#### Footer
- **Save** button: calls `save_teacher_config(...)`, then signals `main.py` to rebuild `all_scheduled`
- **Cancel** button: discard changes

---

## Data Flow

```
school_config.json ──┐
                      ├─→ main.py ──→ all_scheduled ──→ QTimer tick
teacher_config.json ─┘                                    │
        ↑                                                  ↓
  ConfigDialog ──[Save]──→ save_teacher_config()    get_active_class()
                          + rebuild all_scheduled         │
                                                          ↓
                                               AttendanceWindow.update_class()
                                               or .hide()
```

---

## Decisions

| Decision | Rationale |
|----------|-----------|
| 30s QTimer polling | Simple, no threading, latency acceptable |
| FramelessWindowHint | Teacher can drag freely, unobtrusive on screen |
| 72pt code font | 4 digits, need to be readable from across room |
| No date in window | Removed per user request; course name + session sufficient |
| QSettings for config path | Cross-platform, persists between runs without extra files |
| Solid-color pixmap as tray icon fallback | No asset dependency at runtime |

---

## Out of Scope for Phase 4

- School config editor (school_config.json editing via GUI)
- Multiple teacher config file switching via GUI
- Undo/redo in config dialog
- Localization / i18n

---

## Files to Implement

| File | Lines est. |
|------|-----------|
| `src/main.py` | ~80 |
| `src/gui/tray.py` | ~60 |
| `src/gui/attendance_window.py` | ~120 |
| `src/gui/config_dialog.py` | ~300 |
