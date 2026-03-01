"""ConfigDialog — three-tab configuration dialog for teacher config."""
from __future__ import annotations

import copy
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from engine.override import apply_overrides
from engine.scheduler import resolve_course_schedule
from models.school_config import SchoolConfig
from models.teacher_config import (
    Course,
    Override,
    Slot,
    TeacherConfig,
    save_teacher_config,
)

WEEKDAY_JP = {
    "Monday": "月",
    "Tuesday": "火",
    "Wednesday": "水",
    "Thursday": "木",
    "Friday": "金",
}

_WEEKDAY_OPTIONS = [
    ("月曜", "Monday"),
    ("火曜", "Tuesday"),
    ("水曜", "Wednesday"),
    ("木曜", "Thursday"),
    ("金曜", "Friday"),
]

_Q_TYPES = {"Q1", "Q2", "Q3", "Q4"}


def _slot_label(slot: Slot) -> str:
    """Return a human-readable slot string, e.g. '木1限'."""
    jp = WEEKDAY_JP.get(slot.weekday, slot.weekday)
    return f"{jp}{slot.period}限"


class CourseEditDialog(QDialog):
    """Dialog for adding or editing a Course."""

    def __init__(
        self,
        school_config: SchoolConfig,
        course: Course | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.school_config = school_config
        self._course = course
        self.result_course: Course | None = None

        self.setWindowTitle("授業を追加" if course is None else "授業を編集")
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # ID
        self._id_edit = QLineEdit()
        if self._course:
            self._id_edit.setText(self._course.id)
        form.addRow("ID:", self._id_edit)

        # 授業名
        self._name_edit = QLineEdit()
        if self._course:
            self._name_edit.setText(self._course.name)
        form.addRow("授業名:", self._name_edit)

        # 種別
        self._type_combo = QComboBox()
        for ct in ["spring", "autumn", "Q1", "Q2", "Q3", "Q4"]:
            self._type_combo.addItem(ct)
        if self._course:
            idx = self._type_combo.findText(self._course.course_type)
            if idx >= 0:
                self._type_combo.setCurrentIndex(idx)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        form.addRow("種別:", self._type_combo)

        # Slots container
        self._slots_container = QWidget()
        slots_layout = QVBoxLayout(self._slots_container)
        slots_layout.setContentsMargins(0, 0, 0, 0)

        self._slot_rows: list[tuple[QComboBox, QComboBox]] = []
        for i in range(2):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            wd_combo = QComboBox()
            for label, data in _WEEKDAY_OPTIONS:
                wd_combo.addItem(label, userData=data)

            period_combo = QComboBox()
            for p in range(1, 7):
                period_combo.addItem(f"{p}限", userData=p)

            row_layout.addWidget(wd_combo)
            row_layout.addWidget(period_combo)
            slots_layout.addWidget(row_widget)
            self._slot_rows.append((wd_combo, period_combo))

            # Prefill from existing course slots
            if self._course and i < len(self._course.slots):
                slot = self._course.slots[i]
                wd_idx = next(
                    (j for j, (_, d) in enumerate(_WEEKDAY_OPTIONS) if d == slot.weekday),
                    0,
                )
                wd_combo.setCurrentIndex(wd_idx)
                period_combo.setCurrentIndex(slot.period - 1)

        form.addRow("スロット:", self._slots_container)
        layout.addLayout(form)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        # Set initial slot row visibility based on type
        self._update_slot_visibility(self._type_combo.currentText())

    def _on_type_changed(self, text: str) -> None:
        self._update_slot_visibility(text)

    def _update_slot_visibility(self, course_type: str) -> None:
        # Row 0 always visible; row 1 only for Q types
        # The second slot row widget is the parent of the second combo pair
        second_wd, _ = self._slot_rows[1]
        second_row_widget = second_wd.parent()
        if course_type in _Q_TYPES:
            second_row_widget.setVisible(True)
        else:
            second_row_widget.setVisible(False)

    def _on_accept(self) -> None:
        course_id = self._id_edit.text().strip()
        name = self._name_edit.text().strip()
        if not course_id or not name:
            QMessageBox.warning(self, "入力エラー", "IDと授業名は必須です。")
            return
        course_type = self._type_combo.currentText()

        slots: list[Slot] = []
        num_slots = 2 if course_type in _Q_TYPES else 1
        for i in range(num_slots):
            wd_combo, period_combo = self._slot_rows[i]
            weekday = wd_combo.currentData()
            period = period_combo.currentData()
            slots.append(Slot(weekday=weekday, period=period))

        self.result_course = Course(
            id=course_id,
            name=name,
            course_type=course_type,
            slots=slots,
        )
        self.accept()


class OverrideEditDialog(QDialog):
    """Dialog for adding a skip, makeup, or reschedule override."""

    def __init__(
        self,
        ov_type: str,
        courses: list[Course],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.ov_type = ov_type
        self.courses = courses
        self.result_override: Override | None = None

        titles = {"skip": "休講を追加", "makeup": "補講を追加", "reschedule": "調課を追加"}
        self.setWindowTitle(titles.get(ov_type, "調整を追加"))
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # 授業
        self._course_combo = QComboBox()
        for c in self.courses:
            self._course_combo.addItem(c.name, userData=c.id)
        form.addRow("授業:", self._course_combo)

        # Date fields
        self._date_edit: QLineEdit | None = None
        self._new_date_edit: QLineEdit | None = None
        self._period_combo: QComboBox | None = None

        if self.ov_type == "skip":
            self._date_edit = QLineEdit()
            self._date_edit.setPlaceholderText("YYYY-MM-DD")
            form.addRow("日付:", self._date_edit)

        elif self.ov_type == "makeup":
            self._new_date_edit = QLineEdit()
            self._new_date_edit.setPlaceholderText("YYYY-MM-DD")
            form.addRow("新日付:", self._new_date_edit)

            self._period_combo = QComboBox()
            for p in range(1, 7):
                self._period_combo.addItem(f"{p}限", userData=p)
            form.addRow("時限:", self._period_combo)

        elif self.ov_type == "reschedule":
            self._date_edit = QLineEdit()
            self._date_edit.setPlaceholderText("YYYY-MM-DD")
            form.addRow("元日付:", self._date_edit)

            self._new_date_edit = QLineEdit()
            self._new_date_edit.setPlaceholderText("YYYY-MM-DD")
            form.addRow("新日付:", self._new_date_edit)

            self._period_combo = QComboBox()
            for p in range(1, 7):
                self._period_combo.addItem(f"{p}限", userData=p)
            form.addRow("時限:", self._period_combo)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_accept(self) -> None:
        course_id = self._course_combo.currentData()
        date_str = self._date_edit.text().strip() if self._date_edit else ""
        new_date_str = self._new_date_edit.text().strip() if self._new_date_edit else ""
        period = self._period_combo.currentData() if self._period_combo else None

        if self.ov_type == "skip":
            self.result_override = Override(
                type="skip",
                course_id=course_id,
                date=date_str,
            )
        elif self.ov_type == "makeup":
            self.result_override = Override(
                type="makeup",
                course_id=course_id,
                date=self._new_date_edit.text().strip(),
                period=period,
            )
        elif self.ov_type == "reschedule":
            self.result_override = Override(
                type="reschedule",
                course_id=course_id,
                original_date=date_str,
                new_date=new_date_str,
                new_period=period,
            )

        self.accept()


class ConfigDialog(QDialog):
    """Three-tab configuration dialog."""

    config_saved = Signal()

    def __init__(
        self,
        school_config: SchoolConfig,
        teacher_config: TeacherConfig,
        save_path: Path | str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.school_config = school_config
        self._orig_teacher = teacher_config
        self.teacher_config = copy.deepcopy(teacher_config)
        self.save_path = save_path

        self.setWindowTitle("CodeWidget 設定")
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.setMinimumSize(700, 500)
        main_layout = QVBoxLayout(self)

        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: 授業
        self._tab_courses = QWidget()
        self.tabs.addTab(self._tab_courses, "授業")
        self._build_courses_tab()

        # Tab 2: 日程プレビュー
        self._tab_preview = QWidget()
        self.tabs.addTab(self._tab_preview, "日程プレビュー")
        self._build_preview_tab()

        # Tab 3: 調整
        self._tab_adj = QWidget()
        self.tabs.addTab(self._tab_adj, "調整")
        self._build_adj_tab()

        # Footer buttons
        footer = QHBoxLayout()
        btn_save = QPushButton("保存")
        btn_cancel = QPushButton("キャンセル")
        btn_save.clicked.connect(self._on_save)
        btn_cancel.clicked.connect(self.reject)
        footer.addStretch()
        footer.addWidget(btn_save)
        footer.addWidget(btn_cancel)
        main_layout.addLayout(footer)

        # Connect tab change signal
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Initial population
        self._populate_courses_table()
        self._populate_preview_combo()
        self._populate_adj_table()

    def _build_courses_tab(self) -> None:
        layout = QVBoxLayout(self._tab_courses)

        self.courses_table = QTableWidget(0, 4)
        self.courses_table.setHorizontalHeaderLabels(["ID", "授業名", "種別", "スロット"])
        self.courses_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.courses_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.courses_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.courses_table)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("追加")
        btn_edit = QPushButton("編集")
        btn_del = QPushButton("削除")
        btn_add.clicked.connect(self._on_add_course)
        btn_edit.clicked.connect(self._on_edit_course)
        btn_del.clicked.connect(self._on_delete_course)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _build_preview_tab(self) -> None:
        layout = QVBoxLayout(self._tab_preview)

        self.preview_combo = QComboBox()
        self.preview_combo.currentIndexChanged.connect(self._refresh_preview)
        layout.addWidget(self.preview_combo)

        self.preview_table = QTableWidget(0, 4)
        self.preview_table.setHorizontalHeaderLabels(["回", "日付", "曜日", "限"])
        hh = self.preview_table.horizontalHeader()
        for col in range(4):
            hh.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.preview_table)

    def _build_adj_tab(self) -> None:
        layout = QVBoxLayout(self._tab_adj)

        self.adj_table = QTableWidget(0, 5)
        self.adj_table.setHorizontalHeaderLabels(["種別", "授業ID", "元日付", "新日付", "限"])
        hh = self.adj_table.horizontalHeader()
        for col in range(5):
            hh.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        self.adj_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.adj_table)

        btn_layout = QHBoxLayout()
        btn_skip = QPushButton("休講を追加")
        btn_makeup = QPushButton("補講を追加")
        btn_reschedule = QPushButton("調課を追加")
        btn_del = QPushButton("削除")
        btn_skip.clicked.connect(lambda: self._on_add_override("skip"))
        btn_makeup.clicked.connect(lambda: self._on_add_override("makeup"))
        btn_reschedule.clicked.connect(lambda: self._on_add_override("reschedule"))
        btn_del.clicked.connect(self._on_delete_override)
        btn_layout.addWidget(btn_skip)
        btn_layout.addWidget(btn_makeup)
        btn_layout.addWidget(btn_reschedule)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Population helpers
    # ------------------------------------------------------------------

    def _populate_courses_table(self) -> None:
        self.courses_table.setRowCount(0)
        for course in self.teacher_config.courses:
            row = self.courses_table.rowCount()
            self.courses_table.insertRow(row)
            self.courses_table.setItem(row, 0, QTableWidgetItem(course.id))
            self.courses_table.setItem(row, 1, QTableWidgetItem(course.name))
            self.courses_table.setItem(row, 2, QTableWidgetItem(course.course_type))
            slots_str = ", ".join(_slot_label(s) for s in course.slots)
            self.courses_table.setItem(row, 3, QTableWidgetItem(slots_str))

    def _populate_preview_combo(self) -> None:
        self.preview_combo.blockSignals(True)
        self.preview_combo.clear()
        for course in self.teacher_config.courses:
            self.preview_combo.addItem(course.name, userData=course.id)
        self.preview_combo.blockSignals(False)
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        self.preview_table.setRowCount(0)
        course_id = self.preview_combo.currentData()
        if course_id is None:
            return
        course = next((c for c in self.teacher_config.courses if c.id == course_id), None)
        if course is None:
            return

        try:
            base = resolve_course_schedule(course, self.school_config)
            course_overrides = [ov for ov in self.teacher_config.overrides if ov.course_id == course_id]
            scheduled_sorted = sorted(apply_overrides(base, course_overrides), key=lambda sc: sc.date)
        except ValueError:
            self.preview_table.setRowCount(0)
            return

        for sc in scheduled_sorted:
            row = self.preview_table.rowCount()
            self.preview_table.insertRow(row)
            self.preview_table.setItem(row, 0, QTableWidgetItem(sc.session_key))
            self.preview_table.setItem(row, 1, QTableWidgetItem(str(sc.date)))
            jp_wd = WEEKDAY_JP.get(sc.weekday, sc.weekday)
            self.preview_table.setItem(row, 2, QTableWidgetItem(jp_wd))
            self.preview_table.setItem(row, 3, QTableWidgetItem(str(sc.period)))

    def _populate_adj_table(self) -> None:
        self.adj_table.setRowCount(0)
        for ov in self.teacher_config.overrides:
            row = self.adj_table.rowCount()
            self.adj_table.insertRow(row)
            self.adj_table.setItem(row, 0, QTableWidgetItem(ov.type))
            self.adj_table.setItem(row, 1, QTableWidgetItem(ov.course_id))
            orig = ov.original_date if ov.type == "reschedule" else ov.date
            self.adj_table.setItem(row, 2, QTableWidgetItem(orig))
            self.adj_table.setItem(row, 3, QTableWidgetItem(ov.new_date))
            period_str = str(ov.new_period) if ov.type == "reschedule" else (
                str(ov.period) if ov.period is not None else ""
            )
            self.adj_table.setItem(row, 4, QTableWidgetItem(period_str))

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_tab_changed(self, index: int) -> None:
        if index == 1:  # 日程プレビュー
            self._refresh_preview()
        elif index == 2:  # 調整
            self._populate_adj_table()

    def _on_add_course(self) -> None:
        dlg = CourseEditDialog(self.school_config, course=None, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result_course is not None:
            self.teacher_config.courses.append(dlg.result_course)
            self._populate_courses_table()

    def _on_edit_course(self) -> None:
        row = self.courses_table.currentRow()
        if row < 0 or row >= len(self.teacher_config.courses):
            return
        course = self.teacher_config.courses[row]
        dlg = CourseEditDialog(self.school_config, course=course, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result_course is not None:
            self.teacher_config.courses[row] = dlg.result_course
            self._populate_courses_table()

    def _on_delete_course(self) -> None:
        row = self.courses_table.currentRow()
        if row < 0 or row >= len(self.teacher_config.courses):
            return
        course = self.teacher_config.courses[row]
        answer = QMessageBox.question(
            self,
            "削除確認",
            f"「{course.name}」を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.teacher_config.courses.pop(row)
            self._populate_courses_table()

    def _on_add_override(self, ov_type: str) -> None:
        dlg = OverrideEditDialog(ov_type, self.teacher_config.courses, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result_override is not None:
            self.teacher_config.overrides.append(dlg.result_override)
            self._populate_adj_table()
            self._refresh_preview()

    def _on_delete_override(self) -> None:
        row = self.adj_table.currentRow()
        if row < 0 or row >= len(self.teacher_config.overrides):
            return
        self.teacher_config.overrides.pop(row)
        self._populate_adj_table()
        self._refresh_preview()

    def _on_save(self) -> None:
        if self.save_path is not None:
            save_teacher_config(self.teacher_config, self.save_path)
        self._orig_teacher.__dict__.update(self.teacher_config.__dict__)
        self.config_saved.emit()
        self.accept()
