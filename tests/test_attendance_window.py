"""Tests for AttendanceWindow (non-visual logic only)."""
import pytest
from datetime import date
from pytestqt.qtbot import QtBot  # provided by pytest-qt

from engine.scheduler import ScheduledClass


@pytest.fixture
def sc():
    return ScheduledClass(
        course_id="EEE1000411",
        course_name="初年次セミナーA",
        date=date(2026, 4, 16),
        weekday="Thursday",
        period=1,
        session_key="07",
        slot_index=0,
    )


def test_update_class_sets_labels(qtbot, sc):
    from gui.attendance_window import AttendanceWindow
    win = AttendanceWindow()
    qtbot.addWidget(win)
    win.update_class(sc)
    assert "初年次セミナーA" in win.label_course.text()
    assert "07" in win.label_session.text()


def test_clear_class_clears_code(qtbot, sc):
    from gui.attendance_window import AttendanceWindow
    win = AttendanceWindow()
    qtbot.addWidget(win)
    win.update_class(sc)
    win.code_edit.setText("1234")
    win.clear_class()
    assert win.code_edit.text() == ""


def test_initial_state_hidden(qtbot):
    from gui.attendance_window import AttendanceWindow
    win = AttendanceWindow()
    qtbot.addWidget(win)
    assert not win.isVisible()
