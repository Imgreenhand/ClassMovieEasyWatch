from collections.abc import Callable
from pynput import keyboard


class InputsEvents:
    """全局热键监听器，支持从配置档案动态设置热键"""

    def __init__(self,
                 hotkey_hide: str = "<ctrl>+<alt>+q",
                 hotkey_restore: str = "<ctrl>+<alt>+<f9>",
                 on_hide: Callable[[], None] | None = None,
                 on_restore: Callable[[], None] | None = None):
        """
        hotkey_hide:    隐藏热键字符串
        hotkey_restore: 还原热键字符串
        on_hide:        隐藏回调
        on_restore:     还原回调
        """
        self._on_hide = on_hide
        self._on_restore = on_restore
        self._hotkey_hide = hotkey_hide
        self._hotkey_restore = hotkey_restore
        self._listener: keyboard.GlobalHotKeys | None = None
        self._started = False

    # ── 热键属性（支持从 Profile 动态传入）──────────────────────

    @property
    def hotkey_hide(self) -> str:
        return self._hotkey_hide

    @hotkey_hide.setter
    def hotkey_hide(self, value: str):
        self._hotkey_hide = value

    @property
    def hotkey_restore(self) -> str:
        return self._hotkey_restore

    @hotkey_restore.setter
    def hotkey_restore(self, value: str):
        self._hotkey_restore = value

    # ── 回调属性 ──────────────────────────────────────────────

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

    # ── 生命周期 ──────────────────────────────────────────────

    def start(self):
        """启动全局热键监听"""
        self._listener = keyboard.GlobalHotKeys({
            self._hotkey_hide:    self._handle_hide,
            self._hotkey_restore: self._handle_restore,
        })
        self._listener.start()
        self._started = True
        print(f"[InputEvents] 全局热键已注册：{self._hotkey_hide} / {self._hotkey_restore}")

    def stop(self):
        """停止全局热键监听"""
        if self._listener:
            self._listener.stop()
        self._started = False
        print("[InputEvents] 监听已停止")

    # ── 内部处理 ──────────────────────────────────────────────

    def _handle_hide(self):
        if self._on_hide:
            self._on_hide()

    def _handle_restore(self):
        if self._on_restore:
            self._on_restore()

