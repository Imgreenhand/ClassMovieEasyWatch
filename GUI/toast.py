"""
【GUI】Toast 弹窗组件

轻量级消息提示，自动消失。由 GUI 层统一调用。
下层通过 error_reporter 回调将错误上报，由 GUI 层弹出 Toast。
"""

import logging
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QApplication


class Toast(QLabel):
    """浮动 Toast 提示（仅 warning 级别），显示后自动淡出消失"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFont(QFont("微软雅黑", 10))
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumWidth(220)
        self.setMaximumWidth(500)
        self.setWordWrap(True)
        self.setStyleSheet("""
            QLabel {
                background: #ffffff;
                color: #333333;
                border: 2px solid #FF9800;
                border-radius: 8px;
                padding: 10px 20px;
            }
        """)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)

        self._animation: QPropertyAnimation | None = None

    def show_message(self, text: str, duration_ms: int = 4000) -> None:
        """显示警告 Toast，文字自适应大小"""
        self.setText(text)
        self.adjustSize()
        self._position_at_bottom_center()
        self.show()
        self.raise_()
        self._timer.start(duration_ms)

    def _position_at_bottom_center(self) -> None:
        """将 Toast 放在主屏幕底部中央"""
        app = QApplication.instance()
        if app is None:
            return
        screen = app.primaryScreen()
        if screen is None:
            return
        geom = screen.availableGeometry()
        x = geom.center().x() - self.width() // 2
        y = geom.bottom() - self.height() - 40
        self.move(x, y)

    def _fade_out(self) -> None:
        """淡出动画后隐藏"""
        try:
            self._animation = QPropertyAnimation(self, b"windowOpacity")
            self._animation.setDuration(300)
            self._animation.setStartValue(1.0)
            self._animation.setEndValue(0.0)
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
