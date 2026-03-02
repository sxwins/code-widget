"""icon.py — app icon loader."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap


def _icon_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets" / "icon.png"  # type: ignore[attr-defined]
    return Path(__file__).parent.parent / "assets" / "icon.png"


_ICON_PATH = _icon_path()


def make_icon(size: int = 32) -> QIcon:
    """Return the app icon scaled to *size* × *size* px."""
    if _ICON_PATH.exists():
        pix = QPixmap(str(_ICON_PATH))
        if not pix.isNull():
            icon = QIcon(pix.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
            if sys.platform == "darwin":
                icon.setIsMask(True)  # macOS menu bar: treat as template image
            return icon
    return _draw_fallback(size)


def _draw_fallback(size: int) -> QIcon:
    from PySide6.QtGui import (
        QBrush, QColor, QFont, QFontMetrics,
        QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
    )
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    margin = max(1, size // 24)
    radius = max(6, size // 5)
    bx, by = margin, margin
    bw, bh = size - margin * 2, size - margin * 2

    bg = QLinearGradient(0, 0, size, size)
    bg.setColorAt(0.00, QColor("#5EC0FA"))
    bg.setColorAt(0.55, QColor("#2E81D4"))
    bg.setColorAt(1.00, QColor("#1155B0"))
    p.setBrush(QBrush(bg))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(bx, by, bw, bh, radius, radius)

    hl = QLinearGradient(0, 0, 0, size * 0.50)
    hl.setColorAt(0.0, QColor(255, 255, 255, 65))
    hl.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(QBrush(hl))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(bx, by, bw, bh, radius, radius)

    pen = QPen(QColor(200, 220, 255, 180))
    pen.setWidthF(max(0.8, size / 48))
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(bx, by, bw, bh, radius, radius)

    font = QFont()
    font.setBold(True)
    font.setFamilies(["BIZ UDGothic", "Yu Gothic", "Meiryo", "MS Gothic"])
    font.setPointSize(max(6, int(size * 0.52)))
    fm = QFontMetrics(font)
    tb = fm.tightBoundingRect("出")
    x_off = (size - tb.width()) / 2.0 - tb.x()
    y_off = (size - tb.height()) / 2.0 - tb.y()
    char_path = QPainterPath()
    char_path.addText(x_off, y_off, font, "出")
    shadow_offset = max(1, size // 18)
    p.fillPath(char_path.translated(shadow_offset, shadow_offset),
               QBrush(QColor(10, 40, 130, 150)))
    char_grad = QLinearGradient(0, y_off - tb.y(), 0, y_off - tb.y() + tb.height())
    char_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
    char_grad.setColorAt(1.0, QColor(215, 232, 255, 255))
    p.fillPath(char_path, QBrush(char_grad))
    p.end()
    return QIcon(pix)
