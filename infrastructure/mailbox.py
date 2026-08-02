"""
【Infrastructure Layer】跨线程信箱

利用 Qt 的信号槽机制，将后台线程的回调安全地调度到 Qt 主线程执行。
"""

import logging
from collections.abc import Callable
from PySide6.QtCore import QObject, Signal


class _MailboxSignal(QObject):
    """Qt 信号桥接器：跨线程 emit 时自动使用 QueuedConnection"""
    deliver = Signal(object)  # 传递一个可调用对象


class Mailbox:
    """
    跨线程信箱。

    后台线程调用 post() 投递一个可调用对象，
    该对象会在 Qt 主线程的事件循环中被安全执行。
    """

    def __init__(self):
        self._signal = _MailboxSignal()
        self._signal.deliver.connect(self._on_deliver)
        self._pending: Callable[[], None] | None = None

    def post(self, task: Callable[[], None]) -> None:
        """
        将任务投递到 Qt 主线程执行。

        线程安全：可在任意线程调用。
        """
        self._pending = task
        try:
            self._signal.deliver.emit(task)
        except Exception:
            logging.error("Mailbox 投递失败", exc_info=True)

    def _on_deliver(self, task: Callable[[], None]) -> None:
        """在主线程中被调用"""
        try:
            task()
        except Exception:
            logging.error("Mailbox 任务执行异常", exc_info=True)
