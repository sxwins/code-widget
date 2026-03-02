# CodeWidget

A desktop attendance-code display tool for university teachers.

## Overview

CodeWidget shows a floating overlay window on your desktop during class time,
displaying a randomized 4-digit attendance code that students enter into the
learning management system (LMS) to record their presence.

The overlay appears automatically at the start of each scheduled class and
disappears after class ends — no manual operation required during the lesson.

![CodeWidget overlay example](docs/time_slot.png)

## Features

- **Automatic schedule tracking** — reads your course timetable and shows the
  correct code at the right time, including makeup/rescheduled sessions
- **Per-session codes** — each class meeting has its own pre-assigned code;
  codes can be edited or bulk-generated at any time
- **Floating overlay** — compact, always-on-top window; position is remembered
  across restarts
- **Config dialog** — full GUI to manage courses, preview the semester schedule,
  add date adjustments, and customize appearance
- **Multiple teacher configs** — each teacher keeps a separate JSON file;
  switching is one click
- **Appearance customization** — font, colors, and window scale stored globally
  in `settings.json`, independent of teacher data

## Requirements

- Windows 10 / 11
  *(macOS is supported when built from source on a Mac)*
- No installer needed — single `.exe` file

## Getting Started

1. Download `CodeWidget.exe` from [Releases](../../releases)
2. Place it in any folder — a `config/` subdirectory is created automatically
   on first launch
3. Open the settings dialog (tray icon → **設定**) and configure your courses

## Configuration Files

| File | Purpose |
|------|---------|
| `config/settings.json` | Global appearance settings and active teacher config path |
| `config/teacher_config.json` | Default blank teacher template |
| `config/school_config.json` | School calendar: semester dates, holidays, period times |

All files are plain JSON and can be edited by hand or replaced each academic year.

## Building from Source

```bash
# Prerequisites: Python 3.12, uv
uv sync
uv run pytest          # run tests
uv run pyinstaller CodeWidget.spec --clean   # build EXE → dist/CodeWidget.exe
```

## License

[MIT](LICENSE)

> This software uses [PySide6](https://doc.qt.io/qtforpython/), licensed under
> [LGPL v3](https://www.gnu.org/licenses/lgpl-3.0.html).
