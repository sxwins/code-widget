"""main.py — CodeWidget application entry point."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication

from engine.override import apply_overrides
from engine.scheduler import get_active_class, resolve_course_schedule, ScheduledClass
from gui.attendance_window import AttendanceWindow
from gui.config_dialog import ConfigDialog
from gui.icon import make_icon
from gui.tray import TrayIcon
from models.school_config import SchoolConfig, load_school_config
from models.teacher_config import (
    TeacherConfig,
    Settings,
    WindowPosition,
    load_teacher_config,
    save_teacher_config,
)
from utils.time_utils import now

SCHOOL_CONFIG_PATH = Path(__file__).parent.parent / "config" / "school_config.json"
DEFAULT_TEACHER_CONFIG = Path(__file__).parent.parent / "config" / "邵_teacher_config.json"
TICK_MS = 30_000  # 30 seconds


def _build_all_scheduled(teacher_config: TeacherConfig, school_config: SchoolConfig) -> list[ScheduledClass]:
    """Resolve and apply overrides for all courses in the teacher config."""
    all_sc = []
    for course in teacher_config.courses:
        base = resolve_course_schedule(course, school_config)
        course_overrides = [ov for ov in teacher_config.overrides if ov.course_id == course.id]
        all_sc.extend(apply_overrides(base, course_overrides))
    return all_sc


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("CodeWidget")
    app.setOrganizationName("CodeWidget")
    app.setWindowIcon(make_icon())

    # Load configs
    settings = QSettings()
    teacher_path = Path(settings.value("teacher_config_path", str(DEFAULT_TEACHER_CONFIG)))
    try:
        school_config = load_school_config(SCHOOL_CONFIG_PATH)
        teacher_config = load_teacher_config(teacher_path)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "設定ファイルエラー",
                             f"設定ファイルの読み込みに失敗しました。\n\n{exc}")
        sys.exit(1)

    # Build schedule
    all_scheduled = _build_all_scheduled(teacher_config, school_config)
    _last_active = [None]  # mutable list used as closure cell

    # Create widgets
    win = AttendanceWindow()
    tray = TrayIcon(attendance_window=win)
    tray.show()

    # Restore saved window position
    if teacher_config.window_position:
        win.move(teacher_config.window_position.x, teacher_config.window_position.y)

    # Apply saved appearance and show window on startup
    win.apply_appearance(teacher_config.appearance)
    win.show()

    # Save position when dragged
    def on_position_changed(x: int, y: int):
        if teacher_config.window_position is None:
            teacher_config.window_position = WindowPosition(x=x, y=y)
        else:
            teacher_config.window_position.x = x
            teacher_config.window_position.y = y
        save_teacher_config(teacher_config, teacher_path)

    win.position_changed.connect(on_position_changed)

    # Config dialog
    config_dialog_holder = [None]  # holds the ConfigDialog instance

    def open_config():
        if config_dialog_holder[0] is None or not config_dialog_holder[0].isVisible():
            dlg = ConfigDialog(
                school_config=school_config,
                teacher_config=teacher_config,
                save_path=teacher_path,
            )
            dlg.config_saved.connect(on_config_saved)
            config_dialog_holder[0] = dlg
        config_dialog_holder[0].show()
        config_dialog_holder[0].raise_()

    def on_config_saved():
        nonlocal all_scheduled
        all_scheduled = _build_all_scheduled(teacher_config, school_config)
        win.apply_appearance(teacher_config.appearance)
        _last_active[0] = None  # force _tick() to re-evaluate and push new code to window
        _tick()

    tray.open_config.connect(open_config)
    win.open_settings.connect(open_config)

    def _code_for(sc: ScheduledClass) -> str:
        return teacher_config.attendance_codes.get(f"{sc.course_id}_{sc.session_key}", "")

    # Toggle window
    def toggle_window():
        if win.isVisible():
            win.hide()
        else:
            if _last_active[0] is not None:
                win.update_class(_last_active[0], _code_for(_last_active[0]))
            win.show()
        tray.update_status(_last_active[0])

    tray.toggle_window.connect(toggle_window)

    # Timer tick
    def _tick():
        tc_settings = teacher_config.settings if teacher_config.settings else Settings()
        active = get_active_class(now(), all_scheduled, school_config, tc_settings)
        if active != _last_active[0]:
            _last_active[0] = active
            if active is not None:
                win.update_class(active, _code_for(active))
                win.show()
            else:
                win.hide()
            tray.update_status(active)

    timer = QTimer()
    timer.timeout.connect(_tick)
    timer.start(TICK_MS)
    _tick()  # run immediately on startup

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
