"""icon.py — programmatic app icon generator."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QBrush, QColor, QFont, QFontMetrics, QIcon,
    QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
)


def make_icon(size: int = 32) -> QIcon:
    """Return a QIcon matching the reference design:
    iOS-style blue gradient rounded square with 3D-embossed white '出'.
    """
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # ------------------------------------------------------------------ #
    # Background: blue gradient (light top-left → dark bottom-right)      #
    # with a large corner radius like iOS app icons                        #
    # ------------------------------------------------------------------ #
    margin = max(1, size // 24)
    radius = max(6, size // 5)
    bx, by = margin, margin
    bw, bh = size - margin * 2, size - margin * 2

    bg = QLinearGradient(0, 0, size, size)
    bg.setColorAt(0.00, QColor("#5EC0FA"))   # light sky-blue
    bg.setColorAt(0.55, QColor("#2E81D4"))   # medium blue
    bg.setColorAt(1.00, QColor("#1155B0"))   # deep blue
    p.setBrush(QBrush(bg))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(bx, by, bw, bh, radius, radius)

    # Top-left highlight: subtle white sheen
    hl = QLinearGradient(0, 0, 0, size * 0.50)
    hl.setColorAt(0.0, QColor(255, 255, 255, 65))
    hl.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(QBrush(hl))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(bx, by, bw, bh, radius, radius)

    # Metallic silver border
    pen = QPen(QColor(200, 220, 255, 180))
    pen.setWidthF(max(0.8, size / 48))
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(bx, by, bw, bh, radius, radius)

    # ------------------------------------------------------------------ #
    # '出' character — drawn via QPainterPath so we can layer            #
    #   1. dark-blue drop shadow (offset down-right)                      #
    #   2. white fill with top-to-bottom gradient for 3D depth            #
    # ------------------------------------------------------------------ #
    font = QFont()
    font.setBold(True)
    # Prefer fonts with thick CJK strokes; Qt falls back gracefully
    font.setFamilies(["BIZ UDGothic", "Yu Gothic", "Meiryo", "MS Gothic",
                      "Noto Sans CJK JP", "Arial"])
    pt = max(6, int(size * 0.52))
    font.setPointSize(pt)

    fm = QFontMetrics(font)
    tb = fm.tightBoundingRect("出")
    x_off = (size - tb.width()) / 2.0 - tb.x()
    y_off = (size - tb.height()) / 2.0 - tb.y()

    char_path = QPainterPath()
    char_path.addText(x_off, y_off, font, "出")

    # Shadow layer (dark blue, translated down-right)
    shadow_offset = max(1, size // 18)
    p.fillPath(char_path.translated(shadow_offset, shadow_offset),
               QBrush(QColor(10, 40, 130, 150)))

    # Main character: white with slight blue tint at bottom for depth
    char_grad = QLinearGradient(0, y_off - tb.y(), 0, y_off - tb.y() + tb.height())
    char_grad.setColorAt(0.0, QColor(255, 255, 255, 255))   # pure white at top
    char_grad.setColorAt(1.0, QColor(215, 232, 255, 255))   # blue-white at bottom
    p.fillPath(char_path, QBrush(char_grad))

    p.end()
    return QIcon(pix)
