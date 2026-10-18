"""通用界面组件：设置窗口与关于窗口共用的侧边栏导航项。"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from GUI import theme


class NavItem(QFrame):
    """侧边栏导航项：图标 + 文本，支持悬停与选中态。

    ``on_activated`` 在鼠标点击时回调，参数为该导航项自身，
    调用方可通过 :attr:`key` 或 :attr:`text` 判断具体是哪一项。
    """

    def __init__(
        self,
        key: str,
        text: str,
        icon_name: str,
        on_activated: Callable[["NavItem"], None] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.key = key
        self.text = text
        self.setObjectName("navItem")
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)

        self._icon_name = icon_name
        self._on_activated = on_activated
        self._selected = False
        self._hovered = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(10)

        self._icon = QLabel()
        self._icon.setFixedSize(16, 16)
        self._icon.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._icon)

        self.label = QLabel(text)
        self.label.setFont(QFont(theme.FONT_FAMILY, 10))
        self.label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.label)
        layout.addStretch()

        self._refresh_style()

    # ── 状态 ──

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._refresh_style()

    def is_selected(self) -> bool:
        return self._selected

    def _refresh_style(self) -> None:
        if self._selected:
            background, color = theme.PINK_LIGHT, theme.PINK
        elif self._hovered:
            background, color = "#fdf3f6", theme.PINK_DARK
        else:
            background, color = "transparent", theme.TEXT_SUB

        self.setStyleSheet(
            f"QFrame#navItem {{ background: {background}; border: none;"
            f" border-radius: {theme.RADIUS}px; }}"
        )
        self.label.setStyleSheet(
            f"color: {color}; background: transparent; border: none;"
            f" font: 10pt '{theme.FONT_FAMILY}';"
            + (" font-weight: bold;" if self._selected else "")
        )
        self._icon.setPixmap(theme.icon_pixmap(self._icon_name, 16, color))

    # ── 事件 ──

    def enterEvent(self, event):
        self._hovered = True
        if not self._selected:
            self._refresh_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        if not self._selected:
            self._refresh_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._on_activated:
            self._on_activated(self)
        super().mousePressEvent(event)
