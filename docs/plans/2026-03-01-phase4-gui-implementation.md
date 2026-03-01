# Phase 4 GUI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the four GUI files (main.py, tray.py, attendance_window.py, config_dialog.py) that form the complete desktop application for attendance code display.

**Architecture:** A 30-second QTimer in main.py polls `get_active_class()` and controls an always-on-top frameless `AttendanceWindow`. A `QSystemTrayIcon` provides manual override and access to a tabbed `ConfigDialog` for course/override management.

**Tech Stack:** Python 3.12, PySide6 6.10.2, UV package manager (`uv run` for all commands), pytest + pytest-qt for tests, existing engine: `engine.scheduler`, `engine.override`, `models.*`

---

## Pre-flight

Before starting, verify the engine layer is green:
```bash
uv run pytest -v
```
Expected: 22 passed.

Add `pytest-qt` for GUI testing:
```bash
uv add --dev pytest-qt
```

---

## Task 1: AttendanceWindow — floating code display

**Files:**
- Modify: `src/gui/attendance_window.py`
- Test: `tests/test_attendance_window.py`

### Step 1: Write the failing tests

Create `tests/test_attendance_window.py`:

```python
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
```

### Step 2: Run tests — verify they fail

```bash
uv run pytest tests/test_attendance_window.py -v
```
Expected: ImportError or AttributeError (class not yet implemented).

### Step 3: Implement `attendance_window.py`

```python
"""attendance_window.py — always-on-top floating attendance code window."""
from __future__ import annotations

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
)

from engine.scheduler import ScheduledClass


class AttendanceWindow(QWidget):
    """Small frameless always-on-top window for displaying attendance codes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos: QPoint | None = None
        self._setup_window_flags()
        self._build_ui()
        self.clear_class()  # start hidden

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_window_flags(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(360, 170)
        # White background
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("white"))
        self.setPalette(pal)
        self.setAutoFillBackground(True)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Top row: course name + session
        top = QHBoxLayout()
        self.label_course = QLabel("")
        font_course = QFont()
        font_course.setPointSize(11)
        font_course.setBold(True)
        self.label_course.setFont(font_course)

        self.label_session = QLabel("")
        font_session = QFont()
        font_session.setPointSize(10)
        self.label_session.setFont(font_session)
        self.label_session.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        top.addWidget(self.label_course, stretch=3)
        top.addWidget(self.label_session, stretch=1)
        layout.addLayout(top)

        # Code display: large QLineEdit
        self.code_edit = QLineEdit()
        font_code = QFont("Courier New", 72)
        font_code.setBold(True)
        self.code_edit.setFont(font_code)
        self.code_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_edit.setReadOnly(True)
        self.code_edit.setPlaceholderText("----")
        self.code_edit.setStyleSheet(
            "QLineEdit { border: 1px solid #ccc; border-radius: 4px; "
            "background: #f9f9f9; color: #1a1a1a; }"
            "QLineEdit:focus { border: 2px solid #0078d4; }"
        )
        self.code_edit.setMinimumHeight(90)
        layout.addWidget(self.code_edit)

        # Bottom row: buttons
        btn_row = QHBoxLayout()
        self.btn_edit = QPushButton("入力 / ペースト")
        self.btn_edit.setFixedHeight(28)
        self.btn_edit.clicked.connect(self._on_edit_clicked)

        self.btn_clear = QPushButton("クリア")
        self.btn_clear.setFixedHeight(28)
        self.btn_clear.clicked.connect(self._on_clear_clicked)

        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_clear)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_class(self, sc: ScheduledClass) -> None:
        """Update labels for the given scheduled class."""
        self.label_course.setText(sc.course_name)
        self.label_session.setText(f"第{sc.session_key}回")

    def clear_class(self) -> None:
        """Reset labels and code; hide the window."""
        self.label_course.setText("")
        self.label_session.setText("")
        self.code_edit.clear()
        self.hide()

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _on_edit_clicked(self) -> None:
        self.code_edit.setReadOnly(False)
        self.code_edit.setFocus()
        self.code_edit.selectAll()

    def _on_clear_clicked(self) -> None:
        self.code_edit.clear()
        self.code_edit.setReadOnly(True)

    # ------------------------------------------------------------------
    # Drag support (frameless window)
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
            # Signal position changed (connected in main.py)
            self.position_changed.emit(self.pos().x(), self.pos().y())

    # Qt signal — defined at class level (added in __init_subclass__ pattern below)
    from PySide6.QtCore import Signal
    position_changed = Signal(int, int)
```

### Step 4: Run tests — verify they pass

```bash
uv run pytest tests/test_attendance_window.py -v
```
Expected: 3 passed.

### Step 5: Commit

```bash
git add src/gui/attendance_window.py tests/test_attendance_window.py
git commit -m "feat(gui): implement AttendanceWindow with drag and code display"
```

---

## Task 2: TrayIcon — system tray integration

**Files:**
- Modify: `src/gui/tray.py`
- Test: `tests/test_tray.py`

### Step 1: Write failing test

Create `tests/test_tray.py`:

```python
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
    assert "No active class" in tray.toolTip() or tray.toolTip() == ""
```

### Step 2: Run — verify fail

```bash
uv run pytest tests/test_tray.py -v
```
Expected: ImportError.

### Step 3: Implement `tray.py`

```python
"""tray.py — system tray icon and menu."""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon, QPixmap, QColor, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication

from engine.scheduler import ScheduledClass


def _make_default_icon(size: int = 32) -> QIcon:
    """Create a simple solid-blue square icon when no asset is available."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor("#0078d4"))
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    """System tray icon with context menu."""

    # Emitted when teacher requests config dialog
    open_config = Signal()
    # Emitted when teacher requests manual window toggle
    toggle_window = Signal()

    def __init__(self, attendance_window, parent=None):
        icon_path = "assets/icon.png"
        try:
            icon = QIcon(icon_path)
            if icon.isNull():
                raise ValueError
        except Exception:
            icon = _make_default_icon()

        super().__init__(icon, parent)
        self._attendance_window = attendance_window
        self._build_menu()
        self.activated.connect(self._on_activated)
        self.setToolTip("CodeWidget — No active class")

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self):
        menu = QMenu()

        self._action_toggle = QAction("ウィンドウを表示", menu)
        self._action_toggle.triggered.connect(self.toggle_window.emit)
        menu.addAction(self._action_toggle)

        self._action_settings = QAction("設定…", menu)
        self._action_settings.triggered.connect(self.open_config.emit)
        menu.addAction(self._action_settings)

        menu.addSeparator()

        action_exit = QAction("終了", menu)
        action_exit.triggered.connect(QApplication.instance().quit)
        menu.addAction(action_exit)

        self.setContextMenu(menu)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_status(self, sc: ScheduledClass | None) -> None:
        """Update tooltip and toggle-action label based on active class."""
        if sc is None:
            self.setToolTip("CodeWidget — No active class")
            self._action_toggle.setText("ウィンドウを表示")
        else:
            self.setToolTip(f"CodeWidget — {sc.course_name}  第{sc.session_key}回")
            self._action_toggle.setText("ウィンドウを隠す" if self._attendance_window.isVisible() else "ウィンドウを表示")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window.emit()
```

### Step 4: Run — verify pass

```bash
uv run pytest tests/test_tray.py -v
```
Expected: 2 passed.

### Step 5: Commit

```bash
git add src/gui/tray.py tests/test_tray.py
git commit -m "feat(gui): implement TrayIcon with menu and status update"
```

---

## Task 3: ConfigDialog — Courses tab

**Files:**
- Modify: `src/gui/config_dialog.py` (create skeleton + Courses tab)
- Test: `tests/test_config_dialog.py`

### Step 1: Write failing test for courses tab

Create `tests/test_config_dialog.py`:

```python
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
```

### Step 2: Run — verify fail

```bash
uv run pytest tests/test_config_dialog.py -v
```

### Step 3: Implement ConfigDialog skeleton + Courses tab

```python
"""config_dialog.py — tabbed configuration dialog."""
from __future__ import annotations

import copy

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox,
    QComboBox, QLabel, QLineEdit, QFormLayout,
    QDialogButtonBox, QAbstractItemView,
)

from models.school_config import SchoolConfig
from models.teacher_config import (
    TeacherConfig, Course, Slot, Override, save_teacher_config,
)
from engine.scheduler import resolve_course_schedule, ScheduledClass
from engine.override import apply_overrides

COURSE_TYPES = ["spring", "autumn", "Q1", "Q2", "Q3", "Q4"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
WEEKDAY_JP = {"Monday":"月","Tuesday":"火","Wednesday":"水","Thursday":"木","Friday":"金"}


class ConfigDialog(QDialog):
    """Three-tab configuration dialog: Courses | Preview | Adjustments."""

    config_saved = Signal()  # emitted after successful save

    def __init__(self, school_config: SchoolConfig, teacher_config: TeacherConfig,
                 save_path=None, parent=None):
        super().__init__(parent)
        self.school_config = school_config
        # Work on a deep copy so Cancel truly discards changes
        self._orig_teacher = teacher_config
        self.teacher_config = copy.deepcopy(teacher_config)
        self.save_path = save_path
        self.setWindowTitle("CodeWidget 設定")
        self.setMinimumSize(700, 500)
        self._build_ui()
        self._populate_courses()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_courses_tab(), "授業")
        self.tabs.addTab(self._build_preview_tab(), "日程プレビュー")
        self.tabs.addTab(self._build_adjustments_tab(), "調整")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        # Save / Cancel
        btn_box = QHBoxLayout()
        self.btn_save = QPushButton("保存")
        self.btn_save.clicked.connect(self._on_save)
        btn_cancel = QPushButton("キャンセル")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addStretch()
        btn_box.addWidget(self.btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def _build_courses_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)

        self.courses_table = QTableWidget(0, 4)
        self.courses_table.setHorizontalHeaderLabels(["ID", "授業名", "種別", "スロット"])
        self.courses_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.courses_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.courses_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        v.addWidget(self.courses_table)

        btns = QHBoxLayout()
        btn_add  = QPushButton("追加")
        btn_edit = QPushButton("編集")
        btn_del  = QPushButton("削除")
        btn_add.clicked.connect(self._on_course_add)
        btn_edit.clicked.connect(self._on_course_edit)
        btn_del.clicked.connect(self._on_course_delete)
        btns.addWidget(btn_add)
        btns.addWidget(btn_edit)
        btns.addWidget(btn_del)
        btns.addStretch()
        v.addLayout(btns)
        return w

    def _build_preview_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)

        self.preview_combo = QComboBox()
        self.preview_combo.currentIndexChanged.connect(self._refresh_preview)
        v.addWidget(self.preview_combo)

        self.preview_table = QTableWidget(0, 4)
        self.preview_table.setHorizontalHeaderLabels(["回", "日付", "曜日", "限"])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.preview_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        v.addWidget(self.preview_table)
        return w

    def _build_adjustments_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)

        self.adj_table = QTableWidget(0, 5)
        self.adj_table.setHorizontalHeaderLabels(["種別", "授業ID", "元日付", "新日付", "限"])
        self.adj_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.adj_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        v.addWidget(self.adj_table)

        btns = QHBoxLayout()
        btn_skip    = QPushButton("休講を追加")
        btn_makeup  = QPushButton("補講を追加")
        btn_resch   = QPushButton("調課を追加")
        btn_del     = QPushButton("削除")
        btn_skip.clicked.connect(lambda: self._on_adj_add("skip"))
        btn_makeup.clicked.connect(lambda: self._on_adj_add("makeup"))
        btn_resch.clicked.connect(lambda: self._on_adj_add("reschedule"))
        btn_del.clicked.connect(self._on_adj_delete)
        btns.addWidget(btn_skip)
        btns.addWidget(btn_makeup)
        btns.addWidget(btn_resch)
        btns.addWidget(btn_del)
        btns.addStretch()
        v.addLayout(btns)
        return w

    # ------------------------------------------------------------------
    # Population helpers
    # ------------------------------------------------------------------

    def _populate_courses(self):
        self.courses_table.setRowCount(0)
        for course in self.teacher_config.courses:
            row = self.courses_table.rowCount()
            self.courses_table.insertRow(row)
            slots_str = ", ".join(
                f"{WEEKDAY_JP.get(s.weekday, s.weekday)}{s.period}限"
                for s in course.slots
            )
            self.courses_table.setItem(row, 0, QTableWidgetItem(course.id))
            self.courses_table.setItem(row, 1, QTableWidgetItem(course.name))
            self.courses_table.setItem(row, 2, QTableWidgetItem(course.course_type))
            self.courses_table.setItem(row, 3, QTableWidgetItem(slots_str))
        # Sync preview combo
        self.preview_combo.blockSignals(True)
        self.preview_combo.clear()
        for course in self.teacher_config.courses:
            self.preview_combo.addItem(course.name, userData=course.id)
        self.preview_combo.blockSignals(False)
        self._refresh_preview()
        self._populate_adjustments()

    def _populate_adjustments(self):
        self.adj_table.setRowCount(0)
        for ov in self.teacher_config.overrides:
            row = self.adj_table.rowCount()
            self.adj_table.insertRow(row)
            self.adj_table.setItem(row, 0, QTableWidgetItem(ov.type))
            self.adj_table.setItem(row, 1, QTableWidgetItem(ov.course_id))
            self.adj_table.setItem(row, 2, QTableWidgetItem(ov.original_date or ov.date or ""))
            self.adj_table.setItem(row, 3, QTableWidgetItem(ov.new_date or ""))
            period_str = str(ov.new_period or ov.period or "")
            self.adj_table.setItem(row, 4, QTableWidgetItem(period_str))

    def _refresh_preview(self):
        course_id = self.preview_combo.currentData()
        if not course_id:
            return
        course = next((c for c in self.teacher_config.courses if c.id == course_id), None)
        if course is None:
            return
        base = resolve_course_schedule(course, self.school_config)
        course_overrides = [ov for ov in self.teacher_config.overrides if ov.course_id == course_id]
        scheduled = sorted(apply_overrides(base, course_overrides), key=lambda s: s.date)

        self.preview_table.setRowCount(0)
        for sc in scheduled:
            row = self.preview_table.rowCount()
            self.preview_table.insertRow(row)
            self.preview_table.setItem(row, 0, QTableWidgetItem(sc.session_key))
            self.preview_table.setItem(row, 1, QTableWidgetItem(str(sc.date)))
            self.preview_table.setItem(row, 2, QTableWidgetItem(WEEKDAY_JP.get(sc.weekday, sc.weekday)))
            self.preview_table.setItem(row, 3, QTableWidgetItem(str(sc.period)))

    # ------------------------------------------------------------------
    # Course CRUD
    # ------------------------------------------------------------------

    def _on_course_add(self):
        dlg = CourseEditDialog(school_config=self.school_config, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.teacher_config.courses.append(dlg.result_course)
            self._populate_courses()

    def _on_course_edit(self):
        row = self.courses_table.currentRow()
        if row < 0:
            return
        course = self.teacher_config.courses[row]
        dlg = CourseEditDialog(school_config=self.school_config, course=course, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.teacher_config.courses[row] = dlg.result_course
            self._populate_courses()

    def _on_course_delete(self):
        row = self.courses_table.currentRow()
        if row < 0:
            return
        course = self.teacher_config.courses[row]
        reply = QMessageBox.question(self, "削除確認",
            f"「{course.name}」を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self.teacher_config.courses[row]
            self._populate_courses()

    # ------------------------------------------------------------------
    # Override CRUD
    # ------------------------------------------------------------------

    def _on_adj_add(self, ov_type: str):
        dlg = OverrideEditDialog(
            ov_type=ov_type,
            courses=self.teacher_config.courses,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.teacher_config.overrides.append(dlg.result_override)
            self._populate_adjustments()
            self._refresh_preview()

    def _on_adj_delete(self):
        row = self.adj_table.currentRow()
        if row < 0:
            return
        del self.teacher_config.overrides[row]
        self._populate_adjustments()
        self._refresh_preview()

    # ------------------------------------------------------------------
    # Tab change
    # ------------------------------------------------------------------

    def _on_tab_changed(self, index: int):
        if index == 1:
            self._refresh_preview()
        elif index == 2:
            self._populate_adjustments()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _on_save(self):
        if self.save_path:
            save_teacher_config(self.teacher_config, self.save_path)
        self._orig_teacher.__dict__.update(self.teacher_config.__dict__)
        self.config_saved.emit()
        self.accept()


# ---------------------------------------------------------------------------
# Sub-dialogs
# ---------------------------------------------------------------------------

class CourseEditDialog(QDialog):
    """Add or edit a single course."""

    def __init__(self, school_config: SchoolConfig, course: Course | None = None, parent=None):
        super().__init__(parent)
        self.school_config = school_config
        self._original = course
        self.result_course: Course | None = None
        self.setWindowTitle("授業を追加" if course is None else "授業を編集")
        self._build_ui(course)

    def _build_ui(self, course: Course | None):
        layout = QFormLayout(self)

        self.edit_id   = QLineEdit(course.id   if course else "")
        self.edit_name = QLineEdit(course.name if course else "")

        self.combo_type = QComboBox()
        for ct in COURSE_TYPES:
            self.combo_type.addItem(ct)
        if course:
            idx = self.combo_type.findText(course.course_type)
            if idx >= 0:
                self.combo_type.setCurrentIndex(idx)

        layout.addRow("ID:", self.edit_id)
        layout.addRow("授業名:", self.edit_name)
        layout.addRow("種別:", self.combo_type)

        # Slot rows (up to 2)
        self._slot_rows: list[tuple[QComboBox, QComboBox]] = []
        self.slots_container = QWidget()
        self.slots_layout = QVBoxLayout(self.slots_container)
        self.slots_layout.setContentsMargins(0, 0, 0, 0)

        slots = course.slots if course else [Slot(weekday="Monday", period=1)]
        for slot in slots:
            self._add_slot_row(slot)

        layout.addRow("スロット:", self.slots_container)

        self.combo_type.currentTextChanged.connect(self._on_type_changed)
        self._on_type_changed(self.combo_type.currentText())

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _add_slot_row(self, slot: Slot | None = None):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        combo_wd = QComboBox()
        for wd in WEEKDAYS:
            combo_wd.addItem(f"{WEEKDAY_JP[wd]}曜", userData=wd)
        if slot:
            idx = combo_wd.findData(slot.weekday)
            if idx >= 0:
                combo_wd.setCurrentIndex(idx)

        combo_period = QComboBox()
        for p in range(1, 7):
            combo_period.addItem(f"{p}限", userData=p)
        if slot:
            combo_period.setCurrentIndex(slot.period - 1)

        row_layout.addWidget(combo_wd)
        row_layout.addWidget(combo_period)
        self.slots_layout.addWidget(row_widget)
        self._slot_rows.append((combo_wd, combo_period))

    def _on_type_changed(self, ct: str):
        needed = 2 if ct in ("Q1", "Q2", "Q3", "Q4") else 1
        while len(self._slot_rows) < needed:
            self._add_slot_row()
        # Hide/show second row
        if len(self._slot_rows) >= 2:
            widget = self.slots_layout.itemAt(1).widget()
            widget.setVisible(needed == 2)

    def _on_accept(self):
        ct = self.combo_type.currentText()
        needed = 2 if ct in ("Q1", "Q2", "Q3", "Q4") else 1
        slots = []
        for i, (wd_combo, p_combo) in enumerate(self._slot_rows[:needed]):
            slots.append(Slot(weekday=wd_combo.currentData(), period=p_combo.currentData()))
        self.result_course = Course(
            id=self.edit_id.text().strip(),
            name=self.edit_name.text().strip(),
            course_type=ct,
            slots=slots,
        )
        self.accept()


class OverrideEditDialog(QDialog):
    """Add a single override (skip / makeup / reschedule)."""

    def __init__(self, ov_type: str, courses: list[Course], parent=None):
        super().__init__(parent)
        self.ov_type = ov_type
        self.courses = courses
        self.result_override: Override | None = None
        titles = {"skip": "休講を追加", "makeup": "補講を追加", "reschedule": "調課を追加"}
        self.setWindowTitle(titles.get(ov_type, "調整を追加"))
        self._build_ui()

    def _build_ui(self):
        layout = QFormLayout(self)

        self.combo_course = QComboBox()
        for c in self.courses:
            self.combo_course.addItem(c.name, userData=c.id)
        layout.addRow("授業:", self.combo_course)

        if self.ov_type in ("skip", "makeup", "reschedule"):
            self.edit_orig_date = QLineEdit()
            self.edit_orig_date.setPlaceholderText("YYYY-MM-DD")
            label = "日付:" if self.ov_type == "skip" else "元日付:"
            layout.addRow(label, self.edit_orig_date)

        if self.ov_type in ("makeup", "reschedule"):
            self.edit_new_date = QLineEdit()
            self.edit_new_date.setPlaceholderText("YYYY-MM-DD")
            layout.addRow("新日付:", self.edit_new_date)

            self.combo_period = QComboBox()
            for p in range(1, 7):
                self.combo_period.addItem(f"{p}限", userData=p)
            layout.addRow("時限:", self.combo_period)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _on_accept(self):
        course_id = self.combo_course.currentData()
        if self.ov_type == "skip":
            self.result_override = Override(
                type="skip",
                course_id=course_id,
                date=self.edit_orig_date.text().strip(),
            )
        elif self.ov_type == "makeup":
            self.result_override = Override(
                type="makeup",
                course_id=course_id,
                date=self.edit_new_date.text().strip(),
                period=self.combo_period.currentData(),
            )
        elif self.ov_type == "reschedule":
            self.result_override = Override(
                type="reschedule",
                course_id=course_id,
                original_date=self.edit_orig_date.text().strip(),
                new_date=self.edit_new_date.text().strip(),
                new_period=self.combo_period.currentData(),
            )
        self.accept()
```

### Step 4: Run tests — verify pass

```bash
uv run pytest tests/test_config_dialog.py -v
```
Expected: 3 passed.

### Step 5: Commit

```bash
git add src/gui/config_dialog.py tests/test_config_dialog.py
git commit -m "feat(gui): implement ConfigDialog with courses/preview/adjustments tabs"
```

---

## Task 4: main.py — application entry point

**Files:**
- Modify: `src/main.py`
- No separate unit test (integration covered by smoke test below)

### Step 1: Write `main.py`

```python
"""main.py — CodeWidget application entry point."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QSettings, Qt
from PySide6.QtWidgets import QApplication

from models.school_config import load_school_config
from models.teacher_config import load_teacher_config, save_teacher_config
from engine.scheduler import resolve_course_schedule, get_active_class
from engine.override import apply_overrides
from gui.attendance_window import AttendanceWindow
from gui.tray import TrayIcon
from gui.config_dialog import ConfigDialog
from utils.time_utils import now

SCHOOL_CONFIG_PATH = Path(__file__).parent.parent / "config" / "school_config.json"
DEFAULT_TEACHER_CONFIG = Path(__file__).parent.parent / "config" / "邵_teacher_config.json"
TICK_MS = 30_000  # 30 seconds


def _build_all_scheduled(teacher_config, school_config):
    """Resolve + apply overrides for all courses."""
    all_sc = []
    for course in teacher_config.courses:
        base = resolve_course_schedule(course, school_config)
        course_overrides = [ov for ov in teacher_config.overrides if ov.course_id == course.id]
        all_sc.extend(apply_overrides(base, course_overrides))
    return all_sc


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # stay alive when attendance window hides
    app.setApplicationName("CodeWidget")
    app.setOrganizationName("CodeWidget")

    # ------------------------------------------------------------------
    # Load configs
    # ------------------------------------------------------------------
    settings = QSettings()
    teacher_path = Path(
        settings.value("teacher_config_path", str(DEFAULT_TEACHER_CONFIG))
    )

    school_config  = load_school_config(SCHOOL_CONFIG_PATH)
    teacher_config = load_teacher_config(teacher_path)

    all_scheduled = _build_all_scheduled(teacher_config, school_config)
    _last_active: list[object] = [None]  # mutable container for closure

    # ------------------------------------------------------------------
    # Widgets
    # ------------------------------------------------------------------
    win  = AttendanceWindow()
    tray = TrayIcon(attendance_window=win)
    tray.show()

    # Restore saved window position
    if teacher_config.window_position:
        win.move(teacher_config.window_position.x, teacher_config.window_position.y)

    # Save position when dragged
    def on_position_changed(x: int, y: int):
        if teacher_config.window_position is None:
            from models.teacher_config import WindowPosition
            teacher_config.window_position = WindowPosition(x=x, y=y)
        else:
            teacher_config.window_position.x = x
            teacher_config.window_position.y = y
        save_teacher_config(teacher_config, teacher_path)

    win.position_changed.connect(on_position_changed)

    # ------------------------------------------------------------------
    # Config dialog
    # ------------------------------------------------------------------
    config_dialog: list[ConfigDialog | None] = [None]

    def open_config():
        if config_dialog[0] is None or not config_dialog[0].isVisible():
            dlg = ConfigDialog(
                school_config=school_config,
                teacher_config=teacher_config,
                save_path=teacher_path,
            )
            dlg.config_saved.connect(on_config_saved)
            config_dialog[0] = dlg
        config_dialog[0].show()
        config_dialog[0].raise_()

    def on_config_saved():
        nonlocal all_scheduled
        all_scheduled = _build_all_scheduled(teacher_config, school_config)
        _tick()  # immediate re-check after save

    tray.open_config.connect(open_config)

    # ------------------------------------------------------------------
    # Toggle window
    # ------------------------------------------------------------------
    def toggle_window():
        if win.isVisible():
            win.hide()
        else:
            active = _last_active[0]
            if active is not None:
                win.update_class(active)
            win.show()
        tray.update_status(_last_active[0])

    tray.toggle_window.connect(toggle_window)

    # ------------------------------------------------------------------
    # Timer tick
    # ------------------------------------------------------------------
    def _tick():
        from models.teacher_config import Settings as AppSettings
        tc_settings = teacher_config.settings if teacher_config.settings else AppSettings()
        active = get_active_class(now(), all_scheduled, school_config, tc_settings)

        if active != _last_active[0]:
            _last_active[0] = active
            if active is not None:
                win.update_class(active)
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
```

### Step 2: Smoke test — launch the app

```bash
uv run python src/main.py
```

Expected: App starts, tray icon appears in system tray, no errors in console. Since today is 2026-03-01 (before semester start), no attendance window should appear. Right-click tray → "設定…" should open the config dialog.

### Step 3: Verify always-on-top behavior

Manually: open "設定…", switch to "日程プレビュー" tab, verify 14 sessions listed for 初年次セミナーA (dates starting 2026-04-16).

### Step 4: Commit

```bash
git add src/main.py
git commit -m "feat(gui): implement main.py with QTimer loop and tray/window wiring"
```

---

## Task 5: Run full test suite

```bash
uv run pytest -v
```

Expected: All previous 22 tests + new GUI tests pass (≥27 total).

Commit if all green:
```bash
git commit --allow-empty -m "test: all tests passing after Phase 4 implementation"
```

---

## Task 6: Update planning docs

Update `docs/task_plan.md` — mark Phase 3 items complete, Phase 4 complete:
- Phase 3 checkbox items: all [x]
- Phase 4 status: `complete`

Update `docs/progress.md` with Phase 4 summary.

```bash
git add docs/task_plan.md docs/progress.md
git commit -m "docs: mark Phase 3 and Phase 4 complete"
```

---

## Known Limitations / Phase 5 Notes

- Tray icon uses a generated blue square; real icon goes in `assets/icon.png`
- `QSettings` persists teacher config path but not window title/version
- Config dialog does not validate date format (YYYY-MM-DD) — user must type correctly
- School config is not editable via GUI (out of scope for Phase 4)
