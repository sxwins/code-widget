"""ConfigDialog — three-tab configuration dialog for teacher config."""
from __future__ import annotations

import copy
from pathlib import Path

import re

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
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
from engine.scheduler import ScheduledClass, resolve_course_schedule
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


class RescheduleDialog(QDialog):
    """Dialog for adding a reschedule (time adjustment) override."""

    def __init__(
        self,
        school_config: SchoolConfig,
        teacher_config: TeacherConfig,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.school_config = school_config
        self.teacher_config = teacher_config
        self.result_override: Override | None = None
        self._sessions: list[ScheduledClass] = []

        self.setWindowTitle("調整を追加")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self._form = QFormLayout()

        # Row 0: 授業
        self._course_combo = QComboBox()
        for c in self.teacher_config.courses:
            self._course_combo.addItem(c.name, userData=c.id)
        self._course_combo.currentIndexChanged.connect(self._on_course_changed)
        self._form.addRow("授業:", self._course_combo)

        # Row 1: 対象回
        self._session_combo = QComboBox()
        self._session_combo.currentIndexChanged.connect(self._on_session_changed)
        self._form.addRow("対象回:", self._session_combo)

        # Row 2: 元日時 (readonly)
        self._orig_label = QLabel()
        self._form.addRow("元日時:", self._orig_label)

        # Row 3: 新日付
        self._new_date_edit = QDateEdit()
        self._new_date_edit.setCalendarPopup(True)
        self._new_date_edit.setDisplayFormat("yyyy-MM-dd")
        self._form.addRow("新日付:", self._new_date_edit)

        # Row 4: 新時限
        self._period_combo = QComboBox()
        for p in range(1, 7):
            self._period_combo.addItem(f"{p}限", userData=p)
        self._period_combo.addItem("カスタム", userData=None)
        self._period_combo.currentIndexChanged.connect(self._on_period_changed)
        self._form.addRow("新時限:", self._period_combo)

        # Row 5: 時刻 (shown only when カスタム)
        self._time_edit = QLineEdit()
        self._time_edit.setPlaceholderText("HH:MM")
        self._form.addRow("時刻:", self._time_edit)
        self._form.setRowVisible(5, False)

        layout.addLayout(self._form)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        if self._course_combo.count() > 0:
            self._on_course_changed(0)

    def _on_course_changed(self, index: int) -> None:
        course_id = self._course_combo.itemData(index)
        course = next((c for c in self.teacher_config.courses if c.id == course_id), None)
        if course is None:
            self._sessions = []
            self._session_combo.clear()
            return
        try:
            sessions = resolve_course_schedule(course, self.school_config)
            self._sessions = sorted(sessions, key=lambda s: (s.date, s.period))
        except (ValueError, KeyError):
            self._sessions = []

        self._session_combo.blockSignals(True)
        self._session_combo.clear()
        for i, sc in enumerate(self._sessions):
            jp_wd = WEEKDAY_JP.get(sc.weekday, sc.weekday)
            self._session_combo.addItem(f"第{i + 1}回 ({sc.date} {jp_wd}{sc.period}限)")
        self._session_combo.blockSignals(False)

        if self._sessions:
            self._on_session_changed(0)

    def _on_session_changed(self, index: int) -> None:
        if index < 0 or index >= len(self._sessions):
            return
        sc = self._sessions[index]
        jp_wd = WEEKDAY_JP.get(sc.weekday, sc.weekday)
        self._orig_label.setText(f"{sc.date} {jp_wd}{sc.period}限")
        self._new_date_edit.setDate(QDate(sc.date.year, sc.date.month, sc.date.day))
        self._period_combo.setCurrentIndex(sc.period - 1)

    def _on_period_changed(self, index: int) -> None:
        is_custom = self._period_combo.itemData(index) is None
        self._form.setRowVisible(5, is_custom)

    def _on_accept(self) -> None:
        session_idx = self._session_combo.currentIndex()
        if session_idx < 0 or session_idx >= len(self._sessions):
            QMessageBox.warning(self, "エラー", "授業回を選択してください。")
            return

        sc = self._sessions[session_idx]
        original_date = str(sc.date)
        original_period = sc.period

        new_qdate = self._new_date_edit.date()
        new_date = f"{new_qdate.year():04d}-{new_qdate.month():02d}-{new_qdate.day():02d}"

        period_data = self._period_combo.currentData()
        is_custom = period_data is None

        if is_custom:
            custom_time = self._time_edit.text().strip()
            if not custom_time:
                QMessageBox.warning(self, "入力エラー", "時刻を入力してください。")
                return
            if not re.match(r"^\d{2}:\d{2}$", custom_time):
                QMessageBox.warning(self, "入力エラー", "時刻はHH:MM形式で入力してください。")
                return
            new_period = None
            new_start_time = custom_time
        else:
            new_period = period_data
            new_start_time = ""
            if new_date == original_date and new_period == original_period:
                QMessageBox.warning(self, "変更なし", "変更がありません。")
                return

        course_id = self._course_combo.currentData()
        self.result_override = Override(
            type="reschedule",
            course_id=course_id,
            original_date=original_date,
            original_period=original_period,
            new_date=new_date,
            new_period=new_period,
            new_start_time=new_start_time,
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

        self.courses_table = QTableWidget(0, 5)
        self.courses_table.setHorizontalHeaderLabels(["ID", "授業名", "年度", "種別", "スロット"])
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

        self.adj_table = QTableWidget(0, 4)
        self.adj_table.setHorizontalHeaderLabels(["授業名", "元日付", "新日付", "新時限"])
        hh = self.adj_table.horizontalHeader()
        for col in range(4):
            hh.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        self.adj_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.adj_table)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("調整を追加")
        btn_del = QPushButton("削除")
        btn_add.clicked.connect(self._on_add_adjustment)
        btn_del.clicked.connect(self._on_delete_override)
        btn_layout.addWidget(btn_add)
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
            ct = self.school_config.course_types.get(course.course_type)
            year = ct.semester_id.split("_")[-1] if ct else ""
            self.courses_table.setItem(row, 2, QTableWidgetItem(year))
            self.courses_table.setItem(row, 3, QTableWidgetItem(course.course_type))
            slots_str = ", ".join(_slot_label(s) for s in course.slots)
            self.courses_table.setItem(row, 4, QTableWidgetItem(slots_str))

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
        course_map = {c.id: c.name for c in self.teacher_config.courses}
        for ov in self.teacher_config.overrides:
            row = self.adj_table.rowCount()
            self.adj_table.insertRow(row)
            self.adj_table.setItem(row, 0, QTableWidgetItem(course_map.get(ov.course_id, ov.course_id)))
            orig = ov.original_date if ov.type == "reschedule" else ov.date
            self.adj_table.setItem(row, 1, QTableWidgetItem(orig))
            self.adj_table.setItem(row, 2, QTableWidgetItem(ov.new_date))
            if ov.new_start_time:
                period_str = ov.new_start_time
            elif ov.new_period is not None:
                period_str = str(ov.new_period)
            else:
                period_str = ""
            self.adj_table.setItem(row, 3, QTableWidgetItem(period_str))

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

    def _on_add_adjustment(self) -> None:
        dlg = RescheduleDialog(self.school_config, self.teacher_config, parent=self)
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
