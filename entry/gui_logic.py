"""
【Entry Layer】GUILogic

提供向外界展示的 PySide6 窗口对象。
运行时的异常通过 Toast 弹窗统一展示，下层通过 error_reporter 回调上报错误。
"""

import sys
import logging
from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget, QMessageBox,
)
from PySide6.QtGui import QIcon, QCursor,QAction
from PySide6.QtCore import QTimer, QEventLoop

from GUI.toast import ToastManager
from GUI.StartWindow import StartWindow
from GUI.AboutWindow import AboutWindow
from GUI.FloatingButton import FloatingButton
from SettingWindow import SettingWindow
from infrastructure.path_utils import (
    resource_path,
    get_trigger_mode,
    set_trigger_mode,
    get_current_profile_name,
    set_current_profile_name,
)
from infrastructure.data_manager import ProfileStore


class GUILogic:
    """
    GUI 逻辑层。

    职责：
    - 管理所有 PySide6 窗口（托盘图标、开始窗口、设置窗口、关于窗口）
    - 统一的 Toast 错误提示
    - 接收下层的 error_reporter 回调
    """

    def __init__(
        self,
        on_start: Callable[[str, str], None],
        on_stop: Callable[[], None],
    ):
        """
        on_start(trigger_mode, profile_name): 用户点击"开始监听"时的回调
        on_stop(): 用户点击"结束监听"时的回调
        """
        self._on_start = on_start
        self._on_stop = on_stop

        self._app: QApplication | None = None
        self._tray_icon: QSystemTrayIcon | None = None
        self._tray_menu: QMenu | None = None

        self._start_action: QAction | None = None
        self._stop_action: QAction | None = None

        self._profile_store = ProfileStore()
        self._toast = ToastManager.get_instance()

        # 子窗口引用（防止被 GC）
        self._start_win: StartWindow | None = None
        self._settings_win: SettingWindow | None = None
        self._about_win: AboutWindow | None = None

    # ── 初始化 ──────────────────────────────────────────────

    def initialize(self) -> QApplication:
        """创建 QApplication 和系统托盘图标"""
        self._app = QApplication(sys.argv)
        self._app.setQuitOnLastWindowClosed(False)
        return self._app

    def setup_tray(self) -> bool:
        """设置系统托盘，返回是否成功"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logging.error("GUILogic: 系统托盘不可用")
            return False

        self._tray_icon = QSystemTrayIcon()
        self._tray_icon.setIcon(QIcon(resource_path("GUI/Art/Sign.svg")))
        self._tray_icon.setToolTip("ClassMovieEasyWatch")

        # 隐藏的父 widget，用于 QMenu
        self.hidden_widget = QWidget()
        self.hidden_widget.hide()
        self._tray_menu = QMenu(self.hidden_widget)

        # 菜单项
        self._start_action = QAction("开始监听", self._tray_menu)
        self._start_action.triggered.connect(self._handle_start)

        self._stop_action = QAction("结束监听", self._tray_menu)
        self._stop_action.triggered.connect(self._handle_stop)

        set_action = QAction("用户设置", self._tray_menu)
        set_action.triggered.connect(self._show_settings)

        about_action = QAction("关于我们", self._tray_menu)
        about_action.triggered.connect(self._show_about)

        quit_action = QAction("退出程序", self._tray_menu)
        quit_action.triggered.connect(self._app.quit)

        self._tray_menu.addAction(set_action)
        self._tray_menu.addSeparator()
        self._tray_menu.addAction(about_action)
        self._tray_menu.addSeparator()
        self._tray_menu.addAction(self._start_action)
        self._tray_menu.addAction(self._stop_action)
        self._tray_menu.addSeparator()
        self._tray_menu.addAction(quit_action)

        self._tray_icon.setContextMenu(self._tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()

        return True

    # ── 错误上报 ──────────────────────────────────────────

    def report_error(self, message: str) -> None:
        """下层调用此方法将错误上报到 GUI 层，弹出 QMessageBox"""
        logging.error("GUILogic: 收到错误上报: %s", message)
        try:
            QMessageBox.critical(None, "错误", message)
        except Exception:
            logging.error("GUILogic: QMessageBox 弹出失败", exc_info=True)

    def report_warning(self, message: str) -> None:
        """下层调用此方法将警告上报到 GUI 层，弹出 Toast"""
        logging.warning("GUILogic: 收到警告上报: %s", message)
        self._toast.warning(message)

    # ── 开始窗口 ────────────────────────────────────────────

    def show_start_window(self) -> tuple[str, str]:
        """
        显示开始窗口，阻塞等待用户选择。

        返回 (trigger_mode, profile_name)
        """
        result: dict = {"way": "hotkey", "profile": "default"}

        loop = QEventLoop()

        def _on_start() -> None:
            result["way"] = get_trigger_mode()
            result["profile"] = get_current_profile_name()
            loop.quit()

        self._start_win = StartWindow(on_start=_on_start)
        self._start_win.show()
        loop.exec()

        return result["way"], result["profile"]

    # ── 事件处理 ────────────────────────────────────────────

    def _handle_start(self) -> None:
        """托盘菜单：开始监听"""
        try:
            way, profile = self.show_start_window()
            self._on_start(way, profile)
        except Exception:
            logging.error("GUILogic: 开始监听失败", exc_info=True)
            QMessageBox.critical(None, "错误", "启动监听失败，请检查配置")

    def _handle_stop(self) -> None:
        """托盘菜单：结束监听"""
        try:
            self._on_stop()
        except Exception:
            logging.error("GUILogic: 结束监听失败", exc_info=True)

    def _show_settings(self) -> None:
        """打开设置窗口"""
        try:
            self._settings_win = SettingWindow()
            self._settings_win.show()
        except Exception:
            logging.error("GUILogic: 打开设置窗口失败", exc_info=True)
            QMessageBox.critical(None, "错误", "无法打开设置窗口")

    def _show_about(self) -> None:
        """打开关于窗口"""
        try:
            self._about_win = AboutWindow()
            self._about_win.show()
        except Exception:
            logging.error("GUILogic: 打开关于窗口失败", exc_info=True)
            QMessageBox.critical(None, "错误", "无法打开关于窗口")

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """系统托盘图标被点击时的兜底处理"""
        logging.debug("GUILogic: 托盘激活 reason=%s", reason)
        QTimer.singleShot(0, self._popup_tray_menu) # 不是

    def _popup_tray_menu(self) -> None:
        """弹出托盘菜单"""
        if self._tray_menu is None:
            logging.error("GUILogic: _tray_menu is None")
            return
        pos = QCursor.pos()
        try:
            self._tray_menu.popup(pos)
        except Exception:
            try:
                self._tray_menu.exec(pos)
            except Exception as e:
                logging.error("GUILogic: 弹出菜单失败: %s", e)

    # ── 属性 ────────────────────────────────────────────────

    @property
    def app(self) -> QApplication | None:
        return self._app
