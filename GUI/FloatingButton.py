"""鼠标热区触发：用系统鼠标钩子在屏幕指定区域切换隐藏/还原。

界面部分只负责在两处「画」：
* 热区位置的高亮浮层（启动后短暂显示，提示用户点哪里）；
* 高亮使用矢量绘制，不依赖位图素材。
"""

from __future__ import annotations

from collections.abc import Callable

from pynput import mouse
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF,
)
from PySide6.QtGui import (
    QColor, QFont, QGuiApplication, QPainter, QPainterPath, QPen,
)
from PySide6.QtWidgets import QApplication, QWidget

from GUI import theme

HINT_TEXT = "点击此处隐藏 / 还原"


class _HotspotOverlay(QWidget):
    """半透明浮层：在屏幕上标出可点击区域"""

    def __init__(self, width: int, height: int, x: float, y: float):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._hotspot_x = x
        self._hotspot_y = y
        self._highlighting = False
        self._anim_in: QPropertyAnimation | None = None
        self._anim_out: QPropertyAnimation | None = None

        self.resize(width, height)
        self._update_position()

    def _update_position(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geom = screen.availableGeometry()
        range_x = geom.width() - self.width()
        range_y = geom.height() - self.height()
        pos_x = geom.x() + int(range_x * self._hotspot_x)
        pos_y = geom.y() + int(range_y * self._hotspot_y)
        self.move(pos_x, pos_y)

    def highlight(self, seconds: int) -> None:
        """淡入显示 n 秒后自动淡出，0 秒则不高亮"""
        if seconds <= 0:
            return
        self._highlighting = True
        self.update()

        self.setWindowOpacity(0.0)
        self._anim_in = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim_in.setDuration(220)
        self._anim_in.setStartValue(0.0)
        self._anim_in.setEndValue(1.0)
        self._anim_in.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_in.start()

        fade_delay = max(400, seconds * 1000 - 400)
        QTimer.singleShot(fade_delay, self._start_fade_out)

    def _start_fade_out(self) -> None:
        if not self._highlighting:
            return
        self._anim_out = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim_out.setDuration(400)
        self._anim_out.setStartValue(self.windowOpacity())
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.InCubic)
        self._anim_out.finished.connect(self._clear_highlight)
        self._anim_out.start()

    def _clear_highlight(self) -> None:
        self._highlighting = False
        self.update()

    def paintEvent(self, event) -> None:
        if not self._highlighting:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)

        # 热区：粉色半透明圆角块
        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)
        painter.fillPath(path, QColor(251, 114, 153, 52))
        painter.setPen(QPen(QColor(251, 114, 153, 235), 2))
        painter.drawPath(path)

        # 四角定位点
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(251, 114, 153, 235))
        for cx, cy in [
            (rect.left() + 2, rect.top() + 2),
            (rect.right() - 2, rect.top() + 2),
            (rect.left() + 2, rect.bottom() - 2),
            (rect.right() - 2, rect.bottom() - 2),
        ]:
            painter.drawEllipse(QRectF(cx - 3, cy - 3, 6, 6))

        # 中心提示胶囊
        font = QFont(theme.FONT_FAMILY, 10, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_w = metrics.horizontalAdvance(HINT_TEXT)
        pill_w = text_w + 34
        pill_h = 32
        pill = QRectF(
            rect.center().x() - pill_w / 2,
            rect.center().y() - pill_h / 2,
            pill_w,
            pill_h,
        )
        pill_path = QPainterPath()
        pill_path.addRoundedRect(pill, pill_h / 2, pill_h / 2)
        painter.fillPath(pill_path, QColor(255, 255, 255, 238))
        painter.setPen(QPen(QColor(251, 114, 153, 200), 1))
        painter.drawPath(pill_path)

        painter.setPen(QColor(theme.PINK_DEEP))
        painter.drawText(pill, Qt.AlignCenter, HINT_TEXT)


class FloatingButton:
    """使用系统鼠标钩子，在屏幕指定区域触发隐藏/恢复切换。"""

    def __init__(self, on_hide: Callable[[], None] | None = None,
                 on_restore: Callable[[], None] | None = None,
                 hotspot_width: int = 220, hotspot_height: int = 120,
                 hotspot_x: float = 1.0, hotspot_y: float = 1.0,
                 highlight_seconds: int = 3):
        self._on_hide = on_hide
        self._on_restore = on_restore
        self._is_hidden_logic = False
        self._listener = None
        self._overlay = None
        self._hotspot_width = hotspot_width
        self._hotspot_height = hotspot_height
        self._hotspot_x = hotspot_x
        self._hotspot_y = hotspot_y
        self._highlight_seconds = highlight_seconds

    def show(self) -> None:
        if self._listener is None:
            self._listener = mouse.Listener(on_click=self._on_click)
            self._listener.start()

        if self._overlay is None:
            self._overlay = _HotspotOverlay(self._hotspot_width, self._hotspot_height,
                                            self._hotspot_x, self._hotspot_y)
            self._overlay.show()
            self._overlay.raise_()
            self._overlay.activateWindow()
            self._overlay.repaint()

            app = QApplication.instance()
            if app is not None:
                QTimer.singleShot(0, self._overlay.repaint)

            if self._highlight_seconds > 0:
                QTimer.singleShot(200, lambda: self._overlay.highlight(self._highlight_seconds))

    def close(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

        if self._overlay is not None:
            self._overlay.close()
            self._overlay = None

    def _on_click(self, x: int, y: int, button, pressed: bool):
        if not pressed or button != mouse.Button.left:
            return True

        if self._is_hotspot(x, y):
            self._toggle_logic()

        return True

    def _is_hotspot(self, x: int, y: int) -> bool:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        ptr = wintypes.POINT(x, y)
        monitor = user32.MonitorFromPoint(ptr, 2)  # MONITOR_DEFAULTTONEAREST = 2

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", wintypes.DWORD),
            ]

        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        user32.GetMonitorInfoW(monitor, ctypes.byref(info))
        work_rect = info.rcWork
        work_w = work_rect.right - work_rect.left
        work_h = work_rect.bottom - work_rect.top
        range_x = work_w - self._hotspot_width
        range_y = work_h - self._hotspot_height
        hotspot_left = work_rect.left + int(range_x * self._hotspot_x)
        hotspot_top = work_rect.top + int(range_y * self._hotspot_y)

        in_horizontal_range = x >= hotspot_left and x <= hotspot_left + self._hotspot_width
        in_vertical_range = y >= hotspot_top and y <= hotspot_top + self._hotspot_height
        return in_horizontal_range and in_vertical_range

    def _toggle_logic(self) -> None:
        if self._is_hidden_logic:
            if self._on_restore:
                try:
                    ok = self._on_restore()
                except Exception:
                    ok = False
                if ok is not False:
                    self._is_hidden_logic = False
        else:
            if self._on_hide:
                try:
                    ok = self._on_hide()
                except Exception:
                    ok = False
                if ok is not False:
                    self._is_hidden_logic = True
