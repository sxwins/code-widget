# tray.py — system tray integration
from __future__ import annotations

import os

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from engine.scheduler import ScheduledClass


class TrayIcon(QSystemTrayIcon):
    """System tray icon with context menu for CodeWidget."""

    open_config = Signal()
    toggle_window = Signal()

    def __init__(self, attendance_window, parent=None) -> None:
        super().__init__(parent)

        self._attendance_window = attendance_window

        # --- Icon: try assets/icon.png, fall back to a coloured square ---
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "assets", "icon.png"
        )
        icon = QIcon(icon_path)
        if icon.isNull():
            pix = QPixmap(32, 32)
            pix.fill(QColor("#0078d4"))
            icon = QIcon(pix)
        self.setIcon(icon)

        # --- Context menu ---
        menu = QMenu()

        self._action_toggle = menu.addAction("ウィンドウを表示")
        self._action_toggle.triggered.connect(self.toggle_window)

        self._action_settings = menu.addAction("設定…")
        self._action_settings.triggered.connect(self.open_config)

        menu.addSeparator()

        action_quit = menu.addAction("終了")
        action_quit.triggered.connect(QApplication.instance().quit)

        self.setContextMenu(menu)

        # --- Initial tooltip ---
        self.setToolTip("CodeWidget — No active class")

        # --- Single-click activates toggle ---
        self.activated.connect(self._on_activated)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window.emit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_status(self, sc: ScheduledClass | None) -> None:
        """Update tooltip and toggle-action label based on current class."""
        if sc is None:
            self.setToolTip("CodeWidget — No active class")
            self._action_toggle.setText("ウィンドウを表示")
        else:
            self.setToolTip(f"CodeWidget — {sc.course_name}  第{sc.session_key}回")
            if self._attendance_window.isVisible():
                self._action_toggle.setText("ウィンドウを隠す")
            else:
                self._action_toggle.setText("ウィンドウを表示")
