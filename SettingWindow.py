"""设置修改窗口：顶部操作栏 + 左侧索引 + 右侧滚动内容。

窗口为无边框圆角卡片，内部三块区域：
* 顶部栏：品牌、配置档案选择、新建/保存/关闭；
* 侧边栏：三个设置分类，带矢量图标与选中态；
* 内容区：由 :class:`GUI.SettingMainScroll.SettingMainScroll` 按需构建页面。
"""

from __future__ import annotations

import json
import logging
import sys

from PySide6.QtCore import Qt, QPoint, QTimer, QSize
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QWidget, QApplication, QPushButton, QLabel,
    QComboBox, QScrollArea, QFrame, QVBoxLayout, QHBoxLayout,
    QMessageBox,
)

from GUI import theme
from GUI.SettingMainScroll import SettingMainScroll
from GUI.widgets import NavItem
from infrastructure.data_manager import ProfileStore
from infrastructure.path_utils import get_data_dir, resource_path
from infrastructure.version import APP_VERSION

SAVE_DIR = get_data_dir()

TOPBAR_H = 58
SIDEBAR_W = 168
NAV_ITEMS = [
    ("热键修改", "keyboard"),
    ("应用名称", "apps"),
    ("个性化设置", "personal"),
]


class SettingWindow(QWidget):
    """设置修改窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("用户设置")

        screen = QApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            self.resize(
                min(980, int(avail.width() * 0.9)),
                min(700, int(avail.height() * 0.88)),
            )
        else:
            self.resize(980, 700)
        self.setMinimumSize(830, 560)

        self._drag_pos: QPoint | None = None
        self._current_nav: str = ""

        self._setup_card()
        self._setup_topbar()
        self._setup_sidebar()
        self._setup_scroll_area()
        self._setup_message_overlay()

        self._refresh_profile_list()
        self._on_sidebar_click(self._nav_items["热键修改"])

    # ═══════════════════════════════════════════════════════
    # 圆角卡片
    # ═══════════════════════════════════════════════════════

    def _setup_card(self) -> None:
        margin = theme.CARD_MARGIN
        self._card = QFrame(self)
        self._card.setObjectName("card")
        self._card.setStyleSheet(theme.card_qss(theme.RADIUS_CARD))
        theme.add_shadow(self._card, blur=48, dy=10, alpha=46)
        self._card.setGeometry(
            margin, margin,
            self.width() - margin * 2, self.height() - margin * 2,
        )

    # ═══════════════════════════════════════════════════════
    # 顶栏
    # ═══════════════════════════════════════════════════════

    def _setup_topbar(self) -> None:
        """顶栏：品牌图标 + 标题 + 配置下拉 + 新建/保存/关闭"""
        self._topbar = QFrame(self._card)
        self._topbar.setObjectName("topbar")
        self._topbar.setStyleSheet(theme.topbar_qss(theme.RADIUS_CARD))
        self._topbar.setFixedHeight(TOPBAR_H)

        layout = QHBoxLayout(self._topbar)
        layout.setContentsMargins(18, 0, 14, 0)
        layout.setSpacing(10)

        # ── 品牌 + 标题 ──
        brand = QLabel()
        logo = QPixmap(resource_path("GUI/Art/Sign.svg"))
        if not logo.isNull():
            brand.setPixmap(logo.scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        brand.setFixedSize(26, 26)
        brand.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(brand)

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(1)

        title = QLabel("用户设置")
        title.setFont(QFont(theme.FONT_FAMILY, 11, QFont.Bold))
        title.setStyleSheet(f"color: {theme.TEXT}; background: transparent; border: none;")
        title_box.addWidget(title)

        subtitle = QLabel("修改后点击保存即可生效")
        subtitle.setFont(QFont(theme.FONT_FAMILY, 8))
        subtitle.setStyleSheet(
            f"color: {theme.TEXT_MUTED}; background: transparent; border: none;"
        )
        title_box.addWidget(subtitle)

        layout.addLayout(title_box)
        layout.addStretch()

        # ── 配置档案 ──
        profile_label = QLabel("配置档案")
        profile_label.setFont(QFont(theme.FONT_FAMILY, 9))
        profile_label.setStyleSheet(
            f"color: {theme.TEXT_SUB}; background: transparent; border: none;"
        )
        layout.addWidget(profile_label)

        self._profile_combo = QComboBox()
        self._profile_combo.setEditable(False)
        self._profile_combo.setFont(QFont(theme.FONT_FAMILY, 10))
        self._profile_combo.setFixedSize(168, 34)
        self._profile_combo.setCursor(Qt.PointingHandCursor)
        self._profile_combo.setStyleSheet(theme.combo_qss(height=32))
        self._profile_combo.currentTextChanged.connect(self._on_profile_changed)
        layout.addWidget(self._profile_combo)

        # ── 新建配置 ──
        self._btn_new = QPushButton("新建配置")
        self._btn_new.setIcon(theme.icon("add", 15, theme.PINK))
        self._btn_new.setIconSize(QSize(15, 15))
        self._btn_new.setFont(QFont(theme.FONT_FAMILY, 9))
        self._btn_new.setFixedHeight(34)
        self._btn_new.setCursor(Qt.PointingHandCursor)
        self._btn_new.setStyleSheet(theme.secondary_button_qss(height=32, font_size=9))
        self._btn_new.setToolTip("基于默认值新建一个配置档案")
        self._btn_new.clicked.connect(self._on_new_profile)
        layout.addWidget(self._btn_new)

        # ── 保存 ──
        self._btn_save = QPushButton("保存")
        self._btn_save.setIcon(theme.icon("save", 15, "#ffffff"))
        self._btn_save.setIconSize(QSize(15, 15))
        self._btn_save.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Bold))
        self._btn_save.setFixedHeight(34)
        self._btn_save.setMinimumWidth(88)
        self._btn_save.setCursor(Qt.PointingHandCursor)
        self._btn_save.setStyleSheet(theme.primary_button_qss(height=34, font_size=10))
        self._btn_save.clicked.connect(self._on_save)
        layout.addWidget(self._btn_save)

        # ── 关闭 ──
        self._btn_close = QPushButton()
        self._btn_close.setIcon(theme.icon("close", 16, theme.TEXT_SUB))
        self._btn_close.setIconSize(QSize(16, 16))
        self._btn_close.setFixedSize(32, 32)
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.setStyleSheet(theme.ghost_button_qss(32))
        self._btn_close.setToolTip("关闭")
        self._btn_close.clicked.connect(self.close)
        layout.addWidget(self._btn_close)

        self._bar_h = TOPBAR_H

    # ═══════════════════════════════════════════════════════
    # 侧边栏
    # ═══════════════════════════════════════════════════════

    def _setup_sidebar(self) -> None:
        """左侧索引侧边栏"""
        self._sidebar = QFrame(self._card)
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setStyleSheet(theme.sidebar_qss(theme.RADIUS_CARD))
        self._sidebar.setFixedWidth(SIDEBAR_W)

        layout = QVBoxLayout(self._sidebar)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(4)

        self._nav_items: dict[str, NavItem] = {}
        for text, icon_name in NAV_ITEMS:
            item = NavItem(text, text, icon_name, on_activated=self._on_sidebar_click)
            layout.addWidget(item)
            self._nav_items[text] = item

        layout.addStretch()

        version = QLabel(f"v{APP_VERSION}")
        version.setFont(QFont(theme.FONT_FAMILY, 8))
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet(
            f"color: {theme.TEXT_MUTED}; background: transparent; border: none;"
        )
        layout.addWidget(version)

        self._sidebar_items = [t for t, _ in NAV_ITEMS]

    # ═══════════════════════════════════════════════════════
    # 滚动区域
    # ═══════════════════════════════════════════════════════

    def _setup_scroll_area(self) -> None:
        """主内容滚动区域"""
        self._scroll = QScrollArea(self._card)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(theme.scroll_qss())
        self._scroll.viewport().setStyleSheet("background: transparent;")

        self._main_scroll = SettingMainScroll()
        self._scroll.setWidget(self._main_scroll)

    # ═══════════════════════════════════════════════════════
    # 内联消息叠加层
    # ═══════════════════════════════════════════════════════

    def _setup_message_overlay(self) -> None:
        """内容区上方的内联提示胶囊"""
        self._msg_frame = QFrame(self._card)
        self._msg_frame.setObjectName("inlineMsg")
        self._msg_frame.setStyleSheet(
            f"""
            QFrame#inlineMsg {{
                background: {theme.PINK_LIGHT};
                border: 1px solid {theme.PINK_EDGE};
                border-radius: 18px;
            }}
            """
        )
        theme.add_shadow(self._msg_frame, blur=18, dy=4, alpha=34)

        msg_layout = QHBoxLayout(self._msg_frame)
        msg_layout.setContentsMargins(16, 6, 18, 6)
        msg_layout.setSpacing(8)

        self._msg_icon = QLabel()
        self._msg_icon.setFixedSize(16, 16)
        self._msg_icon.setStyleSheet("background: transparent; border: none;")
        msg_layout.addWidget(self._msg_icon)

        self._msg_label = QLabel()
        self._msg_label.setFont(QFont(theme.FONT_FAMILY, 10, QFont.Bold))
        self._msg_label.setStyleSheet(
            f"color: {theme.PINK_DEEP}; background: transparent; border: none;"
        )
        msg_layout.addWidget(self._msg_label)

        self._msg_frame.hide()

        self._msg_timer = QTimer(self)
        self._msg_timer.setSingleShot(True)
        self._msg_timer.timeout.connect(self._hide_message)

    def _show_inline_message(
        self, text: str, duration_ms: int = 3000, icon_name: str = "check_circle"
    ) -> None:
        """在内容区上方显示内联消息，自动消失"""
        self._msg_label.setText(text)
        try:
            self._msg_icon.setPixmap(theme.icon_pixmap(icon_name, 16, theme.PINK_DEEP))
            self._msg_icon.show()
        except FileNotFoundError:
            self._msg_icon.hide()

        self._msg_frame.adjustSize()
        self._position_message()
        self._msg_frame.show()
        self._msg_frame.raise_()
        self._msg_timer.start(duration_ms)

    def _position_message(self) -> None:
        """让消息胶囊停在内容区右上角，避免遮挡页面标题"""
        x = self._card.width() - self._msg_frame.width() - 24
        y = TOPBAR_H + 12
        self._msg_frame.move(x, y)

    def _hide_message(self) -> None:
        """隐藏消息标签"""
        self._msg_frame.hide()

    # ═══════════════════════════════════════════════════════
    # 配置文件管理
    # ═══════════════════════════════════════════════════════

    def _on_profile_changed(self, text: str) -> None:
        """下拉栏切换配置档案时加载对应数据"""
        if text:
            self._main_scroll.load_profile(text)

    def _refresh_profile_list(self) -> None:
        """扫描 SaveData/*.json 刷新下拉栏"""
        old_text = self._profile_combo.currentText()
        self._profile_combo.blockSignals(True)
        self._profile_combo.clear()
        if not SAVE_DIR.exists():
            self._profile_combo.addItem("default")
            self._profile_combo.blockSignals(False)
            return

        for f in sorted(SAVE_DIR.glob("*.json")):
            if f.stem == "save":
                continue
            self._profile_combo.addItem(f.stem)

        if self._profile_combo.count() == 0:
            self._profile_combo.addItem("default")
        # 恢复之前的选中项
        if old_text and self._profile_combo.findText(old_text) >= 0:
            self._profile_combo.setCurrentText(old_text)
        self._profile_combo.blockSignals(False)
        self._main_scroll.load_profile(self._profile_combo.currentText())

    def _on_new_profile(self) -> None:
        """点击新建配置"""
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "新建配置", "请输入配置名称:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name == "save":
            return

        default_data = {
            "name": name,
            "hotkey_hide": "<ctrl>+<alt>+q",
            "hotkey_restore": "<ctrl>+<alt>+<f9>",
            "browser_names": "msedge.exe",
            "auto_pause": True,
            "hotspot_width": 220,
            "hotspot_height": 120,
            "hotspot_x": 1.0,
            "hotspot_y": 1.0,
            "pause_method": "appcommand",
            "highlight_seconds": 3,
        }
        try:
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            path = SAVE_DIR / f"{name}.json"
            path.write_text(
                json.dumps(default_data, indent=4, ensure_ascii=False), encoding="utf-8"
            )
            ProfileStore().reload()
        except OSError as e:
            logging.error("新建配置 %s 失败: %s", name, e)
            QMessageBox.warning(self, "创建失败", f"无法创建配置:\n{e}")
            return

        self._refresh_profile_list()
        idx = self._profile_combo.findText(name)
        if idx >= 0:
            self._profile_combo.setCurrentIndex(idx)
        self._show_inline_message(f"已创建配置 “{name}”", icon_name="add")

    def _on_save(self) -> None:
        """收集表单数据并通过 ProfileStore.update_profile 保存到磁盘"""
        name = self._profile_combo.currentText().strip()
        if not name or name == "save":
            return

        data = self._main_scroll.collect_data()
        store = ProfileStore()
        # 确保档案存在于内存中
        if store.get_profile(name) is None:
            store.reload()
        if store.get_profile(name) is None:
            QMessageBox.warning(self, "保存失败", f"配置档案 '{name}' 不存在")
            return

        try:
            ok = store.update_profile(
                name,
                hotkey_hide=data.get("hotkey_hide"),
                hotkey_restore=data.get("hotkey_restore"),
                browser_names=data.get("browser_names"),
                auto_pause=data.get("auto_pause"),
                hotspot_width=data.get("hotspot_width"),
                hotspot_height=data.get("hotspot_height"),
                hotspot_x=data.get("hotspot_x"),
                hotspot_y=data.get("hotspot_y"),
                pause_method=data.get("pause_method"),
                highlight_seconds=data.get("highlight_seconds"),
            )
            if not ok:
                QMessageBox.warning(self, "保存失败", f"配置档案 '{name}' 保存失败")
                return
        except Exception as e:
            logging.error("保存配置 %s 异常: %s", name, e)
            QMessageBox.critical(self, "保存异常", f"保存时发生错误:\n{e}")
            return

        self._show_inline_message(f"配置 “{name}” 已保存")
        self._refresh_profile_list()
        self._profile_combo.setCurrentText(name)

    # ═══════════════════════════════════════════════════════
    # 侧边栏点击
    # ═══════════════════════════════════════════════════════

    def _on_sidebar_click(self, clicked: NavItem) -> None:
        """侧边栏选中切换"""
        for item in self._nav_items.values():
            item.set_selected(item is clicked)
        for text, item in self._nav_items.items():
            if item is clicked:
                self._main_scroll.switch_page(text)
                self._scroll.verticalScrollBar().setValue(0)
                break

    # ═══════════════════════════════════════════════════════
    # 窗口事件
    # ═══════════════════════════════════════════════════════

    def resizeEvent(self, event):
        if not hasattr(self, "_card"):
            super().resizeEvent(event)
            return

        margin = theme.CARD_MARGIN
        card_w = self.width() - margin * 2
        card_h = self.height() - margin * 2

        self._card.setGeometry(margin, margin, card_w, card_h)
        self._topbar.setGeometry(0, 0, card_w, TOPBAR_H)
        self._sidebar.setGeometry(0, TOPBAR_H, SIDEBAR_W, card_h - TOPBAR_H)
        self._scroll.setGeometry(
            SIDEBAR_W, TOPBAR_H, card_w - SIDEBAR_W, card_h - TOPBAR_H
        )

        if self._msg_frame.isVisible():
            self._position_message()

        super().resizeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("ClassMovieEasyWatch")
    win = SettingWindow()
    win.show()
    app.exec()
