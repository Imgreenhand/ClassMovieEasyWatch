"""
【Entry Layer】ListenLogic

监听用户的两种输入：
- HotkeyEvents: 全局热键触发事件（基于 pynput）
- MouseEvents: 鼠标点击设定热区事件（基于 pynput 鼠标钩子 + FloatingButton 叠加层）

收到用户输入后，通过回调上报给 Decision Layer。
"""

import logging
from collections.abc import Callable

from infrastructure.mailbox import Mailbox
from infrastructure.hotkey_listener import HotkeyListener


class ListenLogic:
    """
    输入监听逻辑层。

    持有 HotkeyListener 和 FloatingButton 的引用，
    将用户输入转换为统一的 hide / restore 回调。
    """

    def __init__(
        self,
        mailbox: Mailbox,
        on_hide: Callable[[], None],
        on_restore: Callable[[], None],
        error_reporter: Callable[[str], None],
    ):
        """
        on_hide: 隐藏指令回调（投递到 Decision Layer）
        on_restore: 还原指令回调（投递到 Decision Layer）
        error_reporter: 错误上报回调（投递到 GUI Layer 的 Toast）
        """
        self._mailbox = mailbox
        self._on_hide = on_hide
        self._on_restore = on_restore
        self._error_reporter = error_reporter

        self._hotkey_listener: HotkeyListener | None = None
        self._floating_button = None  # FloatingButton 实例（懒加载）
        self._is_running = False
        self._mode: str = "hotkey"  # "hotkey" | "button"

    # ── 生命周期 ──────────────────────────────────────────

    def start_hotkey_mode(self, hotkey_hide: str, hotkey_restore: str) -> bool:
        """启动热键监听模式"""
        try:
            self._mode = "hotkey"
            self._hotkey_listener = HotkeyListener(self._mailbox)
            self._hotkey_listener.set_hotkeys(hotkey_hide, hotkey_restore)
            self._hotkey_listener.set_callbacks(self._on_hide, self._on_restore)
            self._hotkey_listener.start()
            self._is_running = True
            logging.info("ListenLogic: 热键模式已启动 (%s / %s)", hotkey_hide, hotkey_restore)
            return True
        except Exception:
            logging.error("ListenLogic: 启动热键模式失败", exc_info=True)
            self._error_reporter("热键监听启动失败，请检查热键是否被其他程序占用")
            return False

    def start_button_mode(
        self,
        hotspot_width: int = 220,
        hotspot_height: int = 120,
        hotspot_x: float = 1.0,
        hotspot_y: float = 1.0,
        highlight_seconds: int = 3,
    ) -> bool:
        """启动鼠标热区模式"""
        try:
            from GUI.FloatingButton import FloatingButton

            self._mode = "button"
            self._floating_button = FloatingButton(
                on_hide=self._wrap_callback(self._on_hide),
                on_restore=self._wrap_callback(self._on_restore),
                hotspot_width=hotspot_width,
                hotspot_height=hotspot_height,
                hotspot_x=hotspot_x,
                hotspot_y=hotspot_y,
                highlight_seconds=highlight_seconds,
            )
            self._floating_button.show()
            self._is_running = True
            logging.info("ListenLogic: 鼠标热区模式已启动")
            return True
        except Exception:
            logging.error("ListenLogic: 启动鼠标热区模式失败", exc_info=True)
            self._error_reporter("鼠标热区启动失败")
            return False

    def stop(self) -> None:
        """停止所有监听"""
        if self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
            self._hotkey_listener = None

        if self._floating_button:
            try:
                self._floating_button.close()
            except Exception:
                pass
            self._floating_button = None

        self._is_running = False
        logging.info("ListenLogic: 监听已停止")

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def mode(self) -> str:
        return self._mode

    # ── 内部 ──────────────────────────────────────────────

    def _wrap_callback(self, callback: Callable[[], None]) -> Callable[[], None]:
        """包装回调，捕获异常并通过 error_reporter 上报"""

        def _wrapped() -> None:
            try:
                callback()
            except Exception:
                logging.error("ListenLogic: 回调执行异常", exc_info=True)
                self._error_reporter("操作执行失败")

        return _wrapped
