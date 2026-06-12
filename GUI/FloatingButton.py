import sys
from collections.abc import Callable
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QGuiApplication, QPainter, QColor, QBrush, QFont
from PySide6.QtWidgets import QWidget, QApplication, QPushButton

class FloatingButton(QWidget):
    def __init__(self, on_hide: Callable, on_restore: Callable = None):
        super().__init__()

        # === 1. 窗口属性设置 ===
        # 设置窗口为无边框、工具窗口（不显示在任务栏）、始终置顶
        self.setWindowFlags(
            Qt.FramelessWindowHint |      # 无边框[reference:2]
            Qt.Tool |                     # 不在任务栏显示
            Qt.WindowStaysOnTopHint       # 窗口始终置顶
        )
        # 设置窗口背景透明[reference:3]
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 设置初始窗口大小（宽120，高40）
        self.resize(40, 40)

        self._on_hide = on_hide
        self._on_restore = on_restore
        self._is_hidden = False 

        # === 2. 创建内部按钮 ===
        self.button = QPushButton("隐藏", self)   # 初始文字“隐藏”
        self.button.setGeometry(0, 0, 40, 40)
        self.button.clicked.connect(self._toggle)   # 点击触发切换


        # 设置按钮样式（圆角、背景色、字体等）
        self.button.setStyleSheet("""
            QPushButton {
                background-color: rgba(50, 150, 250, 200);
                color: white;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(80, 180, 255, 230);
            }
            QPushButton:pressed {
                background-color: rgba(30, 100, 200, 210);
            }
        """)

        # === 3. 窗口定位 ===
        # 获取主屏幕的可用几何区域（排除任务栏等）[reference:4]
        screen_geo = QGuiApplication.primaryScreen().availableGeometry()
        # 计算窗口的x坐标：【屏幕宽度 - 窗口宽度】/ 2
        x = (screen_geo.width() - self.width()) // 2
        # 计算窗口的y坐标：【屏幕高度 - 窗口高度】
        y = screen_geo.height() - self.height()
        # 移动窗口到计算出的位置
        self.move(x, y)

    def _toggle(self):
        """点击按钮时切换隐藏/恢复"""
        if not self._is_hidden:
            # 当前未隐藏 → 执行隐藏
            if self._on_hide:
                self._on_hide()
            self._is_hidden = True
            self.button.setText("恢复")
        else:
            # 当前已隐藏 → 执行恢复
            if self._on_restore:
                self._on_restore()
            self._is_hidden = False
            self.button.setText("隐藏")

    def paintEvent(self, event):
        """重绘事件，用于绘制窗口的自定义背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿
        # 设置画笔为透明，不绘制边框
        painter.setPen(Qt.NoPen)
        # 填充窗口背景（可选，如果你的按钮完全覆盖了窗口，可以不填充）
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))  # 完全透明
        super().paintEvent(event)