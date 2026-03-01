"""Tests for ConfigDialog."""
import pytest
from pathlib import Path

SCHOOL  = Path(__file__).parent.parent / "config" / "school_config.json"
TEACHER = Path(__file__).parent.parent / "config" / "邵_teacher_config.json"


@pytest.fixture(scope="module")
def school():
    from models.school_config import load_school_config
    return load_school_config(SCHOOL)


@pytest.fixture(scope="module")
def teacher():
    from models.teacher_config import load_teacher_config
    return load_teacher_config(TEACHER)


def test_dialog_opens(qtbot, school, teacher):
    from gui.config_dialog import ConfigDialog
    dlg = ConfigDialog(school_config=school, teacher_config=teacher)
    qtbot.addWidget(dlg)
    assert dlg is not None


def test_courses_tab_row_count(qtbot, school, teacher):
    from gui.config_dialog import ConfigDialog
    dlg = ConfigDialog(school_config=school, teacher_config=teacher)
    qtbot.addWidget(dlg)
    # 邵_teacher_config has 14 non-intensive courses
    assert dlg.courses_table.rowCount() == 14


def test_tab_count(qtbot, school, teacher):
    from gui.config_dialog import ConfigDialog
    dlg = ConfigDialog(school_config=school, teacher_config=teacher)
    qtbot.addWidget(dlg)
    assert dlg.tabs.count() == 3
