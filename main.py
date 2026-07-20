import sys
import shutil
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget
from PySide6.QtGui import QIcon, QAction, QCursor
from PySide6.QtCore import QTimer
import StartMain
import SettingWindow
from GUI.AboutWindow import AboutWindow
from SaveData.FindSave import get_data_dir

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon("./GUI/Art/Sign.svg"))
        self.setToolTip("ClassMovieEasyWatch")

        self._hidden_widget = QWidget()
        self._hidden_widget.hide()
        self.tray_menu = QMenu(self._hidden_widget)

        self._hider = None
        self._events = None

        # 为 QAction 指定 parent，并把它们保存为实例属性以保留引用
        self.set_action = QAction("用户设置", self.tray_menu)
        self.set_action.triggered.connect(self.set_main)
        self.about_action = QAction("关于我们", self.tray_menu)
        self.about_action.triggered.connect(self.show_about)
        self.start_action = QAction("开始监听", self.tray_menu)
        self.start_action.triggered.connect(self.start_main)
        self.stop_action = QAction("结束监听", self.tray_menu)
        self.stop_action.triggered.connect(self.stop_main)
        self.quit_action = QAction("退出程序", self.tray_menu)
        self.quit_action.triggered.connect(QApplication.instance().quit)
        self.tray_menu.addAction(self.set_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.about_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.start_action)
        self.tray_menu.addAction(self.stop_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.quit_action)

        # 标准用法：设置 context menu
        self.setContextMenu(self.tray_menu)

        # 兜底：activated 信号，用于在某些 Windows 环境下 setContextMenu 失效
        self.activated.connect(self._on_activated)

        # 如果你希望一开始就可见（通常 show() 就足够）
        self.show()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        # 打印 reason 有助于排查（在不同平台上右键/左键可能映射不同）
        logging.debug("Tray activated, reason = %s", reason)
        # 延迟到下一事件循环弹出，避免在信号回调中直接弹出失效
        QTimer.singleShot(0, lambda: self._popup_menu())

    def _popup_menu(self):
        pos = QCursor.pos()
        # 首先尝试非阻塞的 popup（更现代）
        try:
            self.tray_menu.popup(pos)
        except Exception:
            # 如果 popup 失效，作为兜底尝试阻塞式的 exec（某些平台更可靠）
            try:
                self.tray_menu.exec(pos)
            except Exception as e:
                logging.error("弹出菜单失败：%s", e)

    def set_main(self):
        self._settings_win = SettingWindow.SettingWindow()
        self._settings_win.show()

    def show_about(self):
        self._about_win = AboutWindow()
        self._about_win.show()

    def start_main(self):
        self._hider, self._events = StartMain.main()

    def stop_main(self):
        """结束监听，如有隐藏窗口先还原"""
        if self._events is None:
            return
        if self._hider is not None:
            self._hider.restore()
        self._events.stop()
        self._events = None
        self._hider = None


def _ensure_data_dir() -> None:
    """首次运行时将项目内 default.json 和 save.json 复制到用户数据目录"""
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    template_dir = Path(__file__).parent / "SaveData"
    for name in ("default.json", "save.json"):
        src = template_dir / name
        dst = data_dir / name
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
            logging.info("已复制模板文件: %s", name)


if __name__ == "__main__":
    _ensure_data_dir()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        logging.error("系统托盘不可用")
        sys.exit(1)
    else:
        tray_icon = TrayIcon()
        sys.exit(app.exec())