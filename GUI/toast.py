"""Toast 弹窗组件：轻量级消息提示，自动淡出消失。

由 GUI 层统一调用；下层通过 error_reporter 回调把错误上报给 GUI 层，
再由 GUI 层弹出 Toast，避免业务层直接依赖界面。
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from GUI import theme

# 提示级别的强调色（琥珀色，用于与粉色主题区分）
ACCENT = "#f0a24a"
ACCENT_BG = "#fff5e9"
ACCENT_EDGE = "#f8dfc0"


class Toast(QWidget):
    """浮动提示：图标 + 文案，淡入后自动淡出"""

    MAX_TEXT_WIDTH = 420

    def __init__(self, parent: QWidget | None = None):
        super().__init__(
            parent,
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        self._card = QFrame()
        self._card.setObjectName("toastCard")
        self._card.setStyleSheet(
            f"""
            QFrame#toastCard {{
                background: {theme.BG};
                border: 1px solid {ACCENT_EDGE};
                border-radius: 10px;
            }}
            """
        )
        theme.add_shadow(self._card, blur=26, dy=6, alpha=52)
        outer.addWidget(self._card)

        layout = QHBoxLayout(self._card)
        layout.setContentsMargins(14, 11, 18, 11)
        layout.setSpacing(10)

        # 图标：浅色圆底 + 矢量图标
        self._icon = QLabel()
        self._icon.setFixedSize(22, 22)
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setStyleSheet(
            f"background: {ACCENT_BG}; border-radius: 11px;"
        )
        self._icon.setPixmap(theme.icon_pixmap("bolt", 13, ACCENT))
        layout.addWidget(self._icon, 0, Qt.AlignVCenter)

        self._label = QLabel()
        self._label.setFont(QFont(theme.FONT_FAMILY, 10))
        self._label.setWordWrap(True)
        self._label.setMaximumWidth(self.MAX_TEXT_WIDTH)
        self._label.setStyleSheet(
            f"color: {theme.TEXT}; background: transparent; border: none;"
        )
        layout.addWidget(self._label, 1)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)

        self._animation: QPropertyAnimation | None = None

    # ── 对外接口 ──

    def show_message(self, text: str, duration_ms: int = 4000) -> None:
        """显示一条提示，结束后自动消失"""
        self._label.setText(text)
        # 按文字实际宽度确定单行宽度，超出上限才换行
        metrics = self._label.fontMetrics()
        text_width = metrics.horizontalAdvance(text) + 6
        self._label.setFixedWidth(min(self.MAX_TEXT_WIDTH, max(120, text_width)))
        self.adjustSize()
        self._position_at_bottom_center()

        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self._fade_in()

        self._timer.start(duration_ms)

    # ── 内部 ──

    def _fade_in(self) -> None:
        self._animation = QPropertyAnimation(self, b"windowOpacity")
        self._animation.setDuration(180)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.start()

    def _position_at_bottom_center(self) -> None:
        """将 Toast 放在主屏幕底部中央"""
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geom = screen.availableGeometry()
        x = geom.center().x() - self.width() // 2
        y = geom.bottom() - self.height() - 48
        self.move(x, y)

    def _fade_out(self) -> None:
        """淡出动画后隐藏"""
        try:
            self._animation = QPropertyAnimation(self, b"windowOpacity")
            self._animation.setDuration(260)
            self._animation.setStartValue(self.windowOpacity())
            self._animation.setEndValue(0.0)
            self._animation.setEasingCurve(QEasingCurve.InCubic)
            self._animation.finished.connect(self.hide)
            self._animation.start()
        except Exception:
            self.hide()


class ToastManager:
    """全局 Toast 管理器单例（仅 warning 级别）"""

    _instance: "ToastManager | None" = None

    def __init__(self):
        self._toast: Toast | None = None

    @classmethod
    def get_instance(cls) -> "ToastManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def toast(self) -> Toast:
        if self._toast is None:
            self._toast = Toast()
        return self._toast

    def warning(self, text: str, duration_ms: int = 4000) -> None:
        """显示警告 Toast（自适应文字大小）"""
        try:
            self.toast.show_message(text, duration_ms)
        except Exception:
            logging.error("ToastManager: 显示 warning Toast 失败", exc_info=True)
