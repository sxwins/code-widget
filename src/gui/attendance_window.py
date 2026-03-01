# attendance_window.py — 出勤码展示小窗
# 特性：始終置顶、可拖动、醒目大字体显示出勤码、右键菜单（入力/クリア/設定/隠す/終了）

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from engine.scheduler import ScheduledClass
from gui.icon import make_icon
from models.teacher_config import Appearance


class AttendanceWindow(QWidget):
    """Floating widget that displays attendance code for a scheduled class."""

    position_changed = Signal(int, int)
    open_settings = Signal()
    code_entered = Signal(str, str)  # (code_key, code_value)

    def __init__(self, parent: QWidget | None = None) -> None:
        flags = (
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        super().__init__(parent, flags)

        self.setFixedSize(300, 125)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("white"))
        self.setPalette(pal)
        self.setAutoFillBackground(True)

        self._border_color = "#90CAF9"

        # Drag state
        self._drag_active = False
        self._drag_offset_x = 0
        self._drag_offset_y = 0

        # Current scheduled class (used when emitting code_entered)
        self._current_sc = None

        # --- Top row: small icon + course label + session label ---
        self._icon_label = QLabel()
        pix: QPixmap = make_icon(16).pixmap(16, 16)
        self._icon_label.setPixmap(pix)
        self._icon_label.setFixedSize(18, 18)

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
        top_layout.addWidget(self._icon_label)
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
        self.code_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.code_edit.editingFinished.connect(self._on_editing_finished)

        # --- Main layout ---
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.code_edit)

        # Start hidden
        self.hide()

    # ------------------------------------------------------------------
    # Border
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        p = QPainter(self)
        p.setPen(QPen(QColor(self._border_color), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(1, 1, self.width() - 2, self.height() - 2)
        p.end()

    # ------------------------------------------------------------------
    # Context menu (right-click)
    # ------------------------------------------------------------------

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        action_input = menu.addAction("入力")
        action_clear = menu.addAction("クリア")
        menu.addSeparator()
        action_settings = menu.addAction("設定")
        action_hide = menu.addAction("隠す")
        menu.addSeparator()
        action_quit = menu.addAction("終了")
        action = menu.exec(event.globalPos())
        if action == action_input:
            self._on_edit()
        elif action == action_clear:
            self._on_clear_btn()
        elif action == action_settings:
            self.open_settings.emit()
        elif action == action_hide:
            self.hide()
        elif action == action_quit:
            QApplication.instance().quit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_edit(self) -> None:
        self.code_edit.setReadOnly(False)
        self.code_edit.setFocus()
        self.code_edit.selectAll()

    def _on_editing_finished(self) -> None:
        self.code_edit.setReadOnly(True)
        if self._current_sc is not None:
            key = f"{self._current_sc.course_id}_{self._current_sc.session_key}"
            self.code_entered.emit(key, self.code_edit.text())

    def _on_clear_btn(self) -> None:
        self.code_edit.clear()
        self.code_edit.setReadOnly(True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_appearance(self, appearance: Appearance) -> None:
        """Apply font, color, background, and border from Appearance settings."""
        font = QFont(appearance.code_font_family, appearance.code_font_size)
        font.setBold(True)
        self.code_edit.setFont(font)
        self.code_edit.setStyleSheet(
            f"color: {appearance.code_color}; background-color: transparent; border: none;"
        )
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(appearance.code_bg_color))
        self.setPalette(pal)
        self._border_color = appearance.border_color
        if appearance.course_font_family:
            course_font = QFont(appearance.course_font_family, appearance.course_font_size)
            course_font.setBold(True)
            self.label_course.setFont(course_font)
        self.update()

    def update_class(self, sc: ScheduledClass, code: str = "") -> None:
        """Populate course name, session key, and attendance code."""
        self._current_sc = sc
        self.label_course.setText(sc.course_name)
        self.label_session.setText(f"第{sc.session_key}回")
        self.code_edit.setText(code)
        self.code_edit.setReadOnly(True)

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
