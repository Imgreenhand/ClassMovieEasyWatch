import sys
import logging
from collections.abc import Callable
from PySide6.QtWidgets import QApplication
from GUI.FloatingButton import FloatingButton


class ButtonEvents:
    """基于任务栏窗口代理（Windows 任务栏按钮）的按钮事件封装。

    使用方式示例：
        be = ButtonEvents(on_hide=my_hide_cb, on_restore=my_restore_cb)
        be.start()
        # 在主应用的 QApplication 事件循环中继续运行
    """

    def __init__(self, on_hide: Callable[[], None] | None = None, on_restore: Callable[[], None] | None = None,
                 hotspot_width: int = 220, hotspot_height: int = 120,
                 hotspot_x: float = 1.0, hotspot_y: float = 1.0):
        self._on_hide = on_hide
        self._on_restore = on_restore
        self._button: FloatingButton | None = None
        self._self_created_app = False
        self._app = None
        self._hotspot_width = hotspot_width
        self._hotspot_height = hotspot_height
        self._hotspot_x = hotspot_x
        self._hotspot_y = hotspot_y

    @property
    def on_hide(self):
        return self._on_hide

    @on_hide.setter
    def on_hide(self, cb: Callable[[], None] | None):
        self._on_hide = cb

    @property
    def on_restore(self):
        return self._on_restore

    @on_restore.setter
    def on_restore(self, cb: Callable[[], None] | None):
        self._on_restore = cb

    def start(self):
        """
        创建并显示任务栏代理窗口（要求外部已有 QApplication 更好）。
        如果没有 QApplication，会在内部创建一个（但不会自动 exec()）。
        """
        app = QApplication.instance()
        if app is None:
            self._self_created_app = True
            self._app = QApplication([])
        else:
            self._self_created_app = False
            self._app = app

        # 创建代理窗口：它会在任务栏生成一个（透明）图标，点击该图标将触发回调
        self._button = FloatingButton(on_hide=self._handle_hide, on_restore=self._handle_restore,
                                       hotspot_width=self._hotspot_width, hotspot_height=self._hotspot_height,
                                       hotspot_x=self._hotspot_x, hotspot_y=self._hotspot_y)
        self._button.show()
        logging.info("[ButtonEvents] 任务栏代理窗口已显示")

    def stop(self):
        """关闭代理窗口并清理引用"""
        if self._button:
            try:
                self._button.close()
            finally:
                self._button = None
        logging.info("[ButtonEvents] 任务栏代理窗口已关闭")

        if self._self_created_app and self._app is not None:
            # 我们只创建了 QApplication 的引用，不强制退出
            self._app = None
            self._self_created_app = False

    def _handle_hide(self):
        if self._on_hide:
            try:
                self._on_hide()
            except Exception:
                pass

    def _handle_restore(self):
        if self._on_restore:
            try:
                self._on_restore()
            except Exception:
                pass