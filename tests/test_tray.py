"""Tests for TrayIcon (signal/menu wiring)."""
import pytest


def test_tray_creates_without_error(qtbot, qapp):
    from gui.tray import TrayIcon
    from gui.attendance_window import AttendanceWindow
    win = AttendanceWindow()
    qtbot.addWidget(win)
    tray = TrayIcon(attendance_window=win, parent=None)
    assert tray is not None


def test_tray_tooltip_no_class(qtbot, qapp):
    from gui.tray import TrayIcon
    from gui.attendance_window import AttendanceWindow
    win = AttendanceWindow()
    qtbot.addWidget(win)
    tray = TrayIcon(attendance_window=win)
    tray.update_status(None)
    assert "No active class" in tray.toolTip()


def test_tray_tooltip_active_class(qtbot, qapp):
    from datetime import date
    from gui.tray import TrayIcon
    from gui.attendance_window import AttendanceWindow
    from engine.scheduler import ScheduledClass
    win = AttendanceWindow()
    qtbot.addWidget(win)
    tray = TrayIcon(attendance_window=win)
    sc = ScheduledClass(
        course_id="EEE1000411",
        course_name="初年次セミナーA",
        date=date(2026, 4, 16),
        weekday="Thursday",
        period=1,
        session_key="07",
        slot_index=0,
    )
    tray.update_status(sc)
    assert "初年次セミナーA" in tray.toolTip()
    assert "07" in tray.toolTip()
