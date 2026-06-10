import sys
from collections.abc import Callable
from GUI.FloatingButton import FloatingButton
from PySide6.QtWidgets import QApplication

class ButtonEvents:
    """按钮按下时触发"""

    def __init__(self, on_hide=None, on_restore=None):
        self.on_hide = on_hide
        self.on_restore = on_restore
        self._button = None

    """# 回调属性

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
"""

    # 生命周期

    def start(self):
        """创建并显示浮动按钮（要求外部已经创建 QApplication 实例）"""
        # 确保 QApplication 存在，否则创建（但推荐外部创建）
        app = QApplication.instance()
        if app is None:
            # 如果外部没创建，自己创建（注意：这样只能单独使用按钮模式）
            self._self_created_app = True
            app = QApplication([])
        else:
            self._self_created_app = False

        self._button = FloatingButton(
            on_hide = self._handle_hide,
            on_restore = self._handle_restore
        )
        self._button.show()
        print("[ButtonEvents] 浮动按钮已显示")

    def stop(self):
        """关闭浮动按钮并清理"""
        if self._button:
            self._button.close()
            self._button = None
        # 如果自己创建了 QApplication，可以退出事件循环，但一般由外部控制
        print("[ButtonEvents] 浮动按钮已关闭")

    def _handle_hide(self):
        if self.on_hide:
            self.on_hide()

    def _handle_restore(self):
        if self.on_restore:
            self.on_restore()

