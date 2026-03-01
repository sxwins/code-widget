"""icon.py — programmatic app icon generator."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap


def make_icon(size: int = 32) -> QIcon:
    """Return a QIcon drawn programmatically: blue rounded square with '出' in white."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Blue rounded background
    p.setBrush(QColor("#0078d4"))
    p.setPen(Qt.PenStyle.NoPen)
    radius = max(3, size // 8)
    p.drawRoundedRect(1, 1, size - 2, size - 2, radius, radius)

    # White "出" character centred
    p.setPen(QColor("white"))
    f = QFont()
    f.setBold(True)
    f.setPointSize(max(6, size // 2))
    p.setFont(f)
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "出")

    p.end()
    return QIcon(pix)
