from collections.abc import Callable
from pynput import keyboard
from PySide6.QtCore import QObject, Signal
import logging


class _Invoker(QObject):
    """跨线程调用桥接器：在 pynput 线程 emit 信号，Qt 自动排队到主线程执行"""
    invoke = Signal()


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
        self._pending: Callable[[], None] | None = None
        # 笔记：_Invoker 必须在此线程（主线程）创建，信号才能正确跨线程排队
        self._invoker = _Invoker()
        self._invoker.invoke.connect(self._on_invoke)

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

    def _on_invoke(self) -> None:
        """信号槽回调：在主线程执行暂存的函数"""
        if self._pending is not None:
            self._pending()
            self._pending = None

    def _safe_call_in_mainthread(self, func: Callable[[], None]) -> None:
        """把 func 调度到 Qt 主线程执行（线程安全）"""
        self._pending = func
        # 笔记：跨线程 emit 时 Qt 自动使用 QueuedConnection，将调用排队到主线程
        self._invoker.invoke.emit()

    def _handle_hide(self):
        """pynput 回调线程 -> 安全地把实际逻辑发到主线程执行"""
        if self._on_hide:
            try:
                self._safe_call_in_mainthread(self._on_hide)
            except Exception:
                logging.exception("_handle_hide 发生异常")

    def _handle_restore(self):
        """pynput 回调线程 -> 安全地把实际逻辑发到主线程执行"""
        if self._on_restore:
            try:
                self._safe_call_in_mainthread(self._on_restore)
            except Exception:
                logging.exception("_handle_restore 发生异常")