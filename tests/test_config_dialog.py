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
    assert dlg.courses_table.columnCount() == 5


def test_year_column(qtbot, school, teacher):
    from gui.config_dialog import ConfigDialog
    dlg = ConfigDialog(school_config=school, teacher_config=teacher)
    qtbot.addWidget(dlg)
    # Year column (index 2) should contain "2026" for all non-intensive courses
    for row in range(dlg.courses_table.rowCount()):
        year_item = dlg.courses_table.item(row, 2)
        assert year_item is not None
        assert year_item.text() == "2026"


def test_tab_count(qtbot, school, teacher):
    from gui.config_dialog import ConfigDialog
    dlg = ConfigDialog(school_config=school, teacher_config=teacher)
    qtbot.addWidget(dlg)
    assert dlg.tabs.count() == 3


def test_adj_tab_single_button(qtbot, school, teacher):
    from gui.config_dialog import ConfigDialog
    from PySide6.QtWidgets import QPushButton
    dlg = ConfigDialog(school_config=school, teacher_config=teacher)
    qtbot.addWidget(dlg)
    # Adj tab should have exactly 2 buttons: 調整を追加 and 削除
    buttons = dlg._tab_adj.findChildren(QPushButton)
    assert len(buttons) == 2
    labels = {btn.text() for btn in buttons}
    assert labels == {"調整を追加", "削除"}
