"""Icons drawn in code (a mouse between two chevrons), so they stay crisp at any DPI.

Run `python -m hscroll.icons out.ico` to write the multi-size .ico used for the exe.
"""
import struct
import sys
import winreg
from pathlib import Path

from PyQt6.QtCore import QBuffer, QIODevice, QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QIcon, QIconEngine, QImage, QLinearGradient, QPainter, QPainterPath, QPen,
                         QPixmap)

_SIZES = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)
_ICO_SIZES = (16, 20, 24, 32, 40, 48, 64, 256)
_STROKE = 1.6  # in the 24x24 design grid


def _pen(color, width=_STROKE) -> QPen:
    return QPen(QBrush(color), width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)


def _body() -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(QRectF(7.5, 3.5, 9, 17), 4.5, 4.5)
    return path


def _chevrons() -> QPainterPath:
    path = QPainterPath(QPointF(5, 8.5))
    path.lineTo(2.5, 12)
    path.lineTo(5, 15.5)
    path.moveTo(19, 8.5)
    path.lineTo(21.5, 12)
    path.lineTo(19, 15.5)
    return path


def paint_glyph(p: QPainter, rect: QRectF, color: QColor, fill: QColor = None, wheel: QColor = None):
    """Paint the glyph into `rect`: outline in `color`, optional body fill and wheel color."""
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(rect.topLeft())
    p.scale(rect.width() / 24, rect.height() / 24)
    p.setPen(_pen(fill or color))
    p.setBrush(fill if fill is not None else Qt.BrushStyle.NoBrush)
    p.drawPath(_body())
    p.setPen(_pen(wheel or color))
    p.drawLine(QPointF(12, 7.2), QPointF(12, 9.6))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_pen(color))
    p.drawPath(_chevrons())
    p.restore()


def _paint_app(p: QPainter, size: int):
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(size / 24, size / 24)
    blue = QLinearGradient(0, 3.5, 0, 20.5)
    blue.setColorAt(0, QColor("#60CDFF"))
    blue.setColorAt(1, QColor("#0067C0"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(blue)
    p.drawPath(_body())
    p.setPen(_pen(QColor("white")))
    p.drawLine(QPointF(12, 7.2), QPointF(12, 9.6))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(_pen(QBrush(blue), 2.2))
    p.drawPath(_chevrons())


def _image(size: int, paint) -> QImage:
    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    paint(p, size)
    p.end()
    return img


def _icon(paint) -> QIcon:
    icon = QIcon()
    for size in _SIZES:
        icon.addPixmap(QPixmap.fromImage(_image(size, paint)))
    return icon


def app_icon() -> QIcon:
    return _icon(_paint_app)


class _ThemedGlyph(QIconEngine):
    """Paints the glyph in the current Fluent theme's text color, like FluentIcon does."""

    def paint(self, painter, rect, mode, state):
        from qfluentwidgets import isDarkTheme

        color = QColor(255, 255, 255, 230) if isDarkTheme() else QColor(0, 0, 0, 228)
        paint_glyph(painter, QRectF(rect), color)

    def clone(self):
        return _ThemedGlyph()


def glyph_icon() -> QIcon:
    return QIcon(_ThemedGlyph())


def light_taskbar() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            return winreg.QueryValueEx(key, "SystemUsesLightTheme")[0] == 1
    except OSError:
        return False


def tray_icon(state: str, accent: QColor) -> QIcon:
    """state: "on", "latched" (accent-filled) or "off" (dimmed). `accent` is the base accent color."""
    light = light_taskbar()
    fg = QColor(0, 0, 0) if light else QColor(255, 255, 255)
    if state == "off":
        fg.setAlphaF(0.45)
    if not light:  # brighter accent shade on a dark taskbar, as Windows does
        h, s, _, _ = accent.getHsvF()
        accent = QColor.fromHsvF(max(h, 0), s * 0.84, 1.0)

    def paint(p, size):
        rect = QRectF(0, 0, size, size)
        if state == "latched":
            paint_glyph(p, rect, accent, fill=accent, wheel=QColor("white"))
        else:
            paint_glyph(p, rect, fg)

    return _icon(paint)


def write_ico(path):
    """Write a multi-size .ico (PNG-compressed entries, Windows Vista+)."""
    images = [_image(size, _paint_app) for size in _ICO_SIZES]
    blobs = []
    for img in images:
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        img.save(buf, "PNG")
        blobs.append(bytes(buf.data()))
    data = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    for img, blob in zip(images, blobs):
        side = img.width() % 256  # 0 means 256
        data += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(blob), offset)
        offset += len(blob)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data + b"".join(blobs))


if __name__ == "__main__":
    from PyQt6.QtGui import QGuiApplication

    app = QGuiApplication(sys.argv)
    write_ico(sys.argv[1] if len(sys.argv) > 1 else "build/app.ico")
