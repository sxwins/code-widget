# attendance_window.py — 出勤码展示小窗
# 特性：始终置顶、可拖动、醒目大字体显示出勤码、支持手动输入/粘贴

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from engine.scheduler import ScheduledClass


class AttendanceWindow(QWidget):
    """Floating widget that displays attendance code for a scheduled class."""

    position_changed = Signal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        flags = (
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        super().__init__(parent, flags)

        self.setFixedSize(360, 170)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("white"))
        self.setPalette(pal)
        self.setAutoFillBackground(True)

        # Drag state
        self._drag_active = False
        self._drag_offset_x = 0
        self._drag_offset_y = 0

        # --- Top row: course label + session label ---
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

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.label_course, stretch=1)
        top_layout.addWidget(self.label_session)

        # --- Center: code display ---
        self.code_edit = QLineEdit()
        font_code = QFont("Courier New", 72)
        font_code.setBold(True)
        self.code_edit.setFont(font_code)
        self.code_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_edit.setReadOnly(True)
        self.code_edit.setPlaceholderText("----")
        self.code_edit.setFrame(False)
        self.code_edit.editingFinished.connect(self._on_editing_finished)

        # --- Bottom: buttons ---
        self.btn_edit = QPushButton("入力 / ペースト")
        self.btn_clear = QPushButton("クリア")

        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_clear.clicked.connect(self._on_clear_btn)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_clear)

        # --- Main layout ---
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.code_edit)
        main_layout.addLayout(btn_layout)

        # Start hidden
        self.hide()

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _on_edit(self) -> None:
        self.code_edit.setReadOnly(False)
        self.code_edit.setFocus()
        self.code_edit.selectAll()

    def _on_editing_finished(self) -> None:
        self.code_edit.setReadOnly(True)

    def _on_clear_btn(self) -> None:
        self.code_edit.clear()
        self.code_edit.setReadOnly(True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_class(self, sc: ScheduledClass) -> None:
        """Populate course name and session key labels. Caller is responsible for show()."""
        self.label_course.setText(sc.course_name)
        self.label_session.setText(f"第{sc.session_key}回")

    def clear_class(self) -> None:
        """Clear all displayed data and hide the window."""
        self.label_course.setText("")
        self.label_session.setText("")
        self.code_edit.clear()
        self.code_edit.setReadOnly(True)
        self.hide()

    # ------------------------------------------------------------------
    # Drag support
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_offset_x = event.globalPosition().toPoint().x() - self.x()
            self._drag_offset_y = event.globalPosition().toPoint().y() - self.y()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_active:
            new_x = event.globalPosition().toPoint().x() - self._drag_offset_x
            new_y = event.globalPosition().toPoint().y() - self._drag_offset_y
            self.move(new_x, new_y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_active:
            self._drag_active = False
            self.position_changed.emit(self.x(), self.y())
        super().mouseReleaseEvent(event)
