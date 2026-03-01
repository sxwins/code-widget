"""icon.py — programmatic app icon generator."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap,
)


def make_icon(size: int = 32) -> QIcon:
    """Return a QIcon: blue gradient rounded square with white '出' character."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    margin = max(1, size // 32)
    radius = max(4, size // 6)
    x, y = margin, margin
    w, h = size - margin * 2, size - margin * 2

    # --- Background gradient: light blue (top-left) → dark blue (bottom-right) ---
    bg = QLinearGradient(0, 0, size, size)
    bg.setColorAt(0.0, QColor("#4DAAEE"))
    bg.setColorAt(1.0, QColor("#1565C0"))
    p.setBrush(bg)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(x, y, w, h, radius, radius)

    # --- Top-highlight: faint white glow at the top for depth ---
    hl = QLinearGradient(0, 0, 0, size * 0.55)
    hl.setColorAt(0.0, QColor(255, 255, 255, 55))
    hl.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(hl)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(x, y, w, h, radius, radius)

    # --- Metallic border ---
    pen = QPen(QColor(210, 225, 255, 190))
    pen.setWidthF(max(0.8, size / 40))
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(x, y, w, h, radius, radius)

    # --- White "出" character ---
    p.setPen(QColor("white"))
    f = QFont()
    f.setBold(True)
    f.setPointSize(max(6, int(size * 0.52)))
    p.setFont(f)
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "出")

    p.end()
    return QIcon(pix)
