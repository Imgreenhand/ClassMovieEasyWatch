import sys
import json
import logging
from pathlib import Path
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QPixmap, QIcon
from PySide6.QtWidgets import (
    QWidget, QApplication, QPushButton, QLabel,
    QComboBox, QScrollArea, QFrame, QVBoxLayout,
    QSystemTrayIcon, QMessageBox,
)
from GUI.SettingMainScroll import SettingMainScroll
from SaveData.DataManager import DataManager

SAVE_DIR = Path("SaveData")

# ── 通用按钮样式：粉色边框白底 ──
BTN_STYLE = """
    QPushButton {
        background: #ffffff;
        border: 1px solid #fb7299;
        border-radius: 4px;
        color: #fb7299;
        padding: 4px 14px;
    }
    QPushButton:hover {
        background: #fff0f4;
    }
    QPushButton:pressed {
        background: #ffe0ea;
    }
"""

# ── 关闭按钮样式：粉色边框白底 ──
CLOSE_BTN_STYLE = """
    QPushButton {
        background: #ffffff;
        border: 1px solid #fb7299;
        border-radius: 4px;
        color: #fb7299;
        font-weight: bold;
        padding: 2px 8px;
    }
    QPushButton:hover {
        background: #fb7299;
        color: #ffffff;
    }
"""


class SidebarItem(QFrame):
    """侧边栏索引项，高亮表示选中"""

    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setCursor(Qt.PointingHandCursor)

        self.label = QLabel(text, self)
        self.label.setFont(QFont("微软雅黑", 11))
        self.label.setStyleSheet("color: #666; background: transparent; padding-left: 16px;")
        self.label.setFixedHeight(38)

        self._selected = False

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        if selected:
            self.setStyleSheet("background: #fff0f4; border-left: 3px solid #fb7299;")
            self.label.setStyleSheet("color: #fb7299; background: transparent; padding-left: 13px;")
        else:
            self.setStyleSheet("background: transparent; border-left: 3px solid transparent;")
            self.label.setStyleSheet("color: #666; background: transparent; padding-left: 16px;")

    def mousePressEvent(self, event):
        self.parent().parent()._on_sidebar_click(self)


class SettingWindow(QWidget):
    """设置修改窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: #ffffff;")
        self.resize(900, 600)
        self.setMinimumSize(700, 450)

        self._drag_pos: QPoint | None = None
        self._current_nav: str = ""

        self._setup_topbar()
        self._setup_sidebar()
        self._setup_scroll_area()

        self._refresh_profile_list()

    # ═══════════════════════════════════════════════════════
    # 顶栏
    # ═══════════════════════════════════════════════════════

    def _setup_topbar(self) -> None:
        """顶栏：图标 + 当前配置下拉 + 新建配置 | 叉号"""
        bar_h = 44
        self._topbar = QFrame(self)
        self._topbar.setFixedHeight(bar_h)
        self._topbar.setStyleSheet("background: #ffffff; border-bottom: 1px solid #eee;")

        # 图标
        icon_label = QLabel(self._topbar)
        icon_pix = QPixmap("GUI/Art/Sign.svg")
        if not icon_pix.isNull():
            icon_label.setPixmap(icon_pix.scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.move(12, (bar_h - 22) // 2)

        # 当前配置下拉
        self._profile_combo = QComboBox(self._topbar)
        self._profile_combo.setEditable(False)
        self._profile_combo.setFont(QFont("微软雅黑", 10))
        self._profile_combo.setFixedWidth(140)
        self._profile_combo.setStyleSheet("""
            QComboBox {
                background: #ffffff; color: #333; border: 1px solid #ddd;
                border-radius: 4px; padding: 3px 8px;
            }
            QComboBox:hover { border-color: #fb7299; }
            QComboBox QAbstractItemView {
                background: #ffffff; color: #333; selection-background-color: #fff0f4;
                outline: none;
            }
        """)
        self._profile_combo.move(42, (bar_h - 28) // 2)
        self._profile_combo.currentTextChanged.connect(self._on_profile_changed)

        # 新建配置按钮
        self._btn_new = QPushButton("新建配置", self._topbar)
        self._btn_new.setFont(QFont("微软雅黑", 9))
        self._btn_new.setFixedHeight(26)
        self._btn_new.setStyleSheet(BTN_STYLE)
        self._btn_new.adjustSize()
        self._btn_new.move(188, (bar_h - 26) // 2)
        self._btn_new.clicked.connect(self._on_new_profile)

        # 保存按钮
        self._btn_save = QPushButton("保存", self._topbar)
        self._btn_save.setFont(QFont("微软雅黑", 10, QFont.Bold))
        self._btn_save.setFixedHeight(26)
        self._btn_save.setStyleSheet(BTN_STYLE)
        self._btn_save.adjustSize()
        self._btn_save.clicked.connect(self._on_save)

        # 叉号关闭按钮
        self._btn_close = QPushButton("X", self._topbar)
        self._btn_close.setFont(QFont("微软雅黑", 11, QFont.Bold))
        self._btn_close.setFixedSize(30, 26)
        self._btn_close.setStyleSheet(CLOSE_BTN_STYLE)
        self._btn_close.clicked.connect(self.close)

        self._bar_h = bar_h

    # ═══════════════════════════════════════════════════════
    # 侧边栏
    # ═══════════════════════════════════════════════════════

    def _setup_sidebar(self) -> None:
        """左侧索引侧边栏"""
        self._sidebar = QFrame(self)
        self._sidebar.setStyleSheet("background: #fafafa; border-right: 1px solid #eee;")
        self._sidebar.setFixedWidth(150)

        self._nav_items: dict[str, SidebarItem] = {}
        items = ["热键修改", "应用名称", "个性化设置"]
        y = 12
        for text in items:
            item = SidebarItem(text, self._sidebar)
            item.setFixedWidth(150)
            item.move(0, y)
            self._nav_items[text] = item
            y += 42

        self._sidebar_items = items

    # ═══════════════════════════════════════════════════════
    # 滚动区域
    # ═══════════════════════════════════════════════════════

    def _setup_scroll_area(self) -> None:
        """主内容滚动区域"""
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet("background: #ffffff; border: none;")

        self._main_scroll = SettingMainScroll()
        self._scroll.setWidget(self._main_scroll)

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
        }
        try:
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            path = SAVE_DIR / f"{name}.json"
            path.write_text(json.dumps(default_data, indent=4, ensure_ascii=False), encoding="utf-8")
            DataManager().load()
        except OSError as e:
            logging.error(f"新建配置 {name} 失败: {e}")
            QMessageBox.warning(self, "创建失败", f"无法创建配置:\n{e}")
            return

        self._refresh_profile_list()
        idx = self._profile_combo.findText(name)
        if idx >= 0:
            self._profile_combo.setCurrentIndex(idx)

    def _on_save(self) -> None:
        """保存当前配置，调用 DataManager.change 并发送系统通知"""
        name = self._profile_combo.currentText().strip()
        if not name or name == "save":
            return

        try:
            ok = DataManager().save(name)
            if not ok:
                QMessageBox.warning(self, "保存失败", f"配置档案 '{name}' 保存失败")
                return
        except Exception as e:
            logging.error(f"保存配置 {name} 异常: {e}")
            QMessageBox.critical(self, "保存异常", f"保存时发生错误:\n{e}")
            return

        self._show_saved_notification(name)
        self._refresh_profile_list()
        self._profile_combo.setCurrentText(name)

    def _show_saved_notification(self, name: str) -> None:
        """发送系统通知：配置已保存"""
        tray = QSystemTrayIcon(self)
        icon = QIcon("GUI/Art/Sign.svg")
        if icon.isNull():
            icon = self.style().standardIcon(self.style().SP_MessageBoxInformation)
        tray.setIcon(icon)
        tray.show()
        tray.showMessage(
            "ClassMovieEasyWatch",
            f"配置 '{name}' 已保存",
            QSystemTrayIcon.Information,
            2000,
        )

    # ═══════════════════════════════════════════════════════
    # 侧边栏点击
    # ═══════════════════════════════════════════════════════

    def _on_sidebar_click(self, clicked: SidebarItem) -> None:
        """侧边栏选中切换"""
        for item in self._nav_items.values():
            item.set_selected(item is clicked)
        for text, item in self._nav_items.items():
            if item is clicked:
                self._main_scroll.switch_page(text)
                break

    # ═══════════════════════════════════════════════════════
    # 窗口事件
    # ═══════════════════════════════════════════════════════

    def resizeEvent(self, event):
        bar_h = self._bar_h
        sidebar_w = self._sidebar.width()

        self._topbar.setGeometry(0, 0, self.width(), bar_h)
        self._btn_close.move(self.width() - 40, (bar_h - 26) // 2)
        self._btn_save.move(self.width() - 110, (bar_h - 26) // 2)

        self._sidebar.setGeometry(0, bar_h, sidebar_w, self.height() - bar_h)
        self._scroll.setGeometry(sidebar_w, bar_h,
                                 self.width() - sidebar_w, self.height() - bar_h)

        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

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