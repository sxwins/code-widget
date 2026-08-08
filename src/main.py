"""main.py — CodeWidget application entry point."""
from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from engine.override import apply_overrides
from engine.scheduler import get_active_class, resolve_course_schedule, ScheduledClass
from gui.attendance_window import AttendanceWindow
from gui.config_dialog import ConfigDialog
from gui.icon import make_icon
from gui.tray import TrayIcon
from models.school_config import SchoolConfig, load_school_config
from models.app_settings import AppSettings, load_app_settings, save_app_settings
from models.teacher_config import (
    TeacherConfig,
    Settings,
    WindowPosition,
    load_teacher_config,
    save_teacher_config,
)
from utils.time_utils import now

def _resource(rel: str) -> Path:
    """Bundled read-only resource path (works in dev and PyInstaller onefile)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / rel  # type: ignore[attr-defined]
    return Path(__file__).parent.parent / rel


def _user_data_dir() -> Path:
    """Writable directory next to the EXE / .app bundle (or project root in dev).

    On macOS the frozen executable lives inside the .app bundle at
    ``CodeWidget.app/Contents/MacOS/CodeWidget``, so we walk up four levels to
    reach the folder that *contains* the .app, keeping config/ alongside the
    bundle the same way it sits alongside the Windows EXE.
    """
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable)
        if sys.platform == "darwin" and exe.parent.name == "MacOS":
            # .app/Contents/MacOS/CodeWidget → go up 4 levels → parent of .app
            return exe.parent.parent.parent.parent
        return exe.parent
    return Path(__file__).parent.parent


SCHOOL_CONFIG_PATH = _user_data_dir() / "config" / "school_config.json"
APP_SETTINGS_PATH  = _user_data_dir() / "config" / "settings.json"
DEFAULT_TEACHER_CONFIG = _user_data_dir() / "config" / "teacher_config.json"
TICK_MS = 30_000  # 30 seconds


def _ensure_school_config(school_path: Path) -> None:
    """On first run, copy bundled school config template next to the EXE.

    school_config.json is placed in the writable config/ directory so it can
    be replaced each academic year without rebuilding the EXE.
    """
    if school_path.exists():
        return
    school_path.parent.mkdir(parents=True, exist_ok=True)
    template = _resource("config/school_config.json")
    if template.exists():
        import shutil
        shutil.copy(template, school_path)


def _ensure_app_settings(path: Path) -> None:
    """On first run, copy bundled settings.json template next to the EXE."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    template = _resource("config/settings.json")
    if template.exists():
        import shutil
        shutil.copy(template, path)
    else:
        save_app_settings(AppSettings(), path)


def _ensure_user_config(teacher_path: Path) -> None:
    """On first run, copy bundled teacher config template next to the EXE."""
    if teacher_path.exists():
        return
    teacher_path.parent.mkdir(parents=True, exist_ok=True)
    template = _resource("config/teacher_config.json")
    if template.exists():
        import shutil
        shutil.copy(template, teacher_path)


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
    _ensure_school_config(SCHOOL_CONFIG_PATH)
    _ensure_app_settings(APP_SETTINGS_PATH)
    app_settings = load_app_settings(APP_SETTINGS_PATH)
    teacher_path = Path(app_settings.active_config) if app_settings.active_config else DEFAULT_TEACHER_CONFIG
    _ensure_user_config(teacher_path)
    try:
        school_config = load_school_config(SCHOOL_CONFIG_PATH)
        teacher_config = load_teacher_config(teacher_path)
        all_scheduled = _build_all_scheduled(teacher_config, school_config)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as exc:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "設定ファイルエラー",
                             f"設定ファイルの読み込みに失敗しました。\n\n{exc}")
        sys.exit(1)
    _last_active = [None]  # mutable list used as closure cell

    # Temporary codes: key -> (code, expiry_datetime); in-memory only, not persisted
    _temp_codes: dict = {}

    # Create widgets
    win = AttendanceWindow()
    tray = TrayIcon(attendance_window=win)
    tray.show()

    # Restore saved window position
    if teacher_config.window_position:
        win.move(teacher_config.window_position.x, teacher_config.window_position.y)

    # Apply saved appearance and show window on startup
    win.apply_appearance(app_settings.appearance)
    win.show()

    # Save position when dragged
    def on_position_changed(x: int, y: int):
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
                app_settings=app_settings,
                app_settings_path=APP_SETTINGS_PATH,
            )
            dlg.config_saved.connect(on_config_saved)
            dlg.config_file_loaded.connect(on_config_file_loaded)
            config_dialog_holder[0] = dlg
        config_dialog_holder[0].show()
        config_dialog_holder[0].raise_()

    def on_config_saved():
        nonlocal all_scheduled
        try:
            all_scheduled = _build_all_scheduled(teacher_config, school_config)
        except Exception:
            pass  # keep existing schedule; UI refresh still proceeds below
        win.apply_appearance(app_settings.appearance)
        _last_active[0] = None  # force _tick() to re-evaluate and push new code to window
        _tick()

    def on_config_file_loaded(new_path: str) -> None:
        """Handle a new teacher config file loaded from the Settings dialog.

        Updates settings.json so the path persists across restarts, then
        rebuilds the schedule and refreshes the UI exactly like on_config_saved.
        """
        nonlocal teacher_path, all_scheduled
        teacher_path = Path(new_path)
        app_settings.active_config = new_path
        save_app_settings(app_settings, APP_SETTINGS_PATH)
        all_scheduled = _build_all_scheduled(teacher_config, school_config)
        win.apply_appearance(app_settings.appearance)
        _last_active[0] = None
        _tick()

    tray.open_config.connect(open_config)
    win.open_settings.connect(open_config)

    def on_temp_code_entered(key: str, code: str) -> None:
        _temp_codes[key] = (code, now() + timedelta(minutes=30))

    def on_temp_code_cleared(key: str) -> None:
        _temp_codes.pop(key, None)
        if _last_active[0] is not None:
            win.update_class(_last_active[0], _code_for(_last_active[0]))

    win.code_entered.connect(on_temp_code_entered)
    win.code_cleared.connect(on_temp_code_cleared)

    def _code_for(sc: ScheduledClass) -> str:
        """Return the attendance code for a session.

        Priority: in-memory temp code (30-min TTL) > saved config code > empty string.
        Expired temp codes are pruned here on access.
        """
        key = f"{sc.course_id}_{sc.session_key}"
        if key in _temp_codes:
            temp_code, expiry = _temp_codes[key]
            if now() < expiry:
                return temp_code
            del _temp_codes[key]  # expired — fall through to config code
        return teacher_config.attendance_codes.get(key, "")

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

    # Timer tick — called every TICK_MS (30 s) and immediately on startup / config save.
    # Only acts when the active class changes to avoid redundant UI updates.
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
