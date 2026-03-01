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
