"""
【Infrastructure Layer】热键监听器

基于 pynput 的全局热键监听，通过 Mailbox 将回调调度到 Qt 主线程。
"""

import logging
from collections.abc import Callable
from pynput import keyboard
from infrastructure.mailbox import Mailbox


class HotkeyListener:
    """全局热键监听器，支持动态设置热键"""

    def __init__(self, mailbox: Mailbox):
        self._mailbox = mailbox
        self._listener: keyboard.GlobalHotKeys | None = None
        self._hotkey_hide: str = "<ctrl>+<alt>+q"
        self._hotkey_restore: str = "<ctrl>+<alt>+<f9>"
        self._on_hide: Callable[[], None] | None = None
        self._on_restore: Callable[[], None] | None = None

    # ── 配置 ──────────────────────────────────────────────

    def set_hotkeys(self, hide: str, restore: str) -> None:
        self._hotkey_hide = hide
        self._hotkey_restore = restore

    def set_callbacks(self, on_hide: Callable[[], None], on_restore: Callable[[], None]) -> None:
        self._on_hide = on_hide
        self._on_restore = on_restore

    # ── 生命周期 ──────────────────────────────────────────

    def start(self) -> None:
        """启动全局热键监听"""
        if self._listener is not None:
            logging.warning("HotkeyListener: 已经在运行")
            return
        try:
            self._listener = keyboard.GlobalHotKeys({
                self._hotkey_hide: self._handle_hide,
                self._hotkey_restore: self._handle_restore,
            })
            self._listener.start()
            logging.info("HotkeyListener: 热键已注册 %s / %s", self._hotkey_hide, self._hotkey_restore)
        except Exception:
            logging.error("HotkeyListener: 启动失败", exc_info=True)

    def stop(self) -> None:
        """停止全局热键监听"""
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                logging.warning("HotkeyListener: 停止时出错", exc_info=True)
            self._listener = None
        logging.info("HotkeyListener: 已停止")

    # ── 内部处理 ──────────────────────────────────────────

    def _handle_hide(self) -> None:
        """pynput 线程回调 → Mailbox 投递到主线程"""
        if self._on_hide:
            self._mailbox.post(self._on_hide)

    def _handle_restore(self) -> None:
        """pynput 线程回调 → Mailbox 投递到主线程"""
        if self._on_restore:
            self._mailbox.post(self._on_restore)
