"""
【Decision Layer】有限状态机

持有状态值，进行防抖处理。
收到 Entry Layer 的指令后先经过 FSM 判断是否放行。
"""

import time
import logging
from enum import Enum, auto


class AppState(Enum):
    IDLE = auto()           # 空闲：窗口可见，等待隐藏指令
    HIDDEN = auto()         # 已隐藏：窗口不可见，等待还原指令
    TRANSITIONING = auto()  # 过渡中：正在执行隐藏 / 还原操作


class FiniteStateMachine:
    """状态机 + 防抖"""

    def __init__(self, debounce_seconds: float = 0.3):
        self._state: AppState = AppState.IDLE
        self._debounce_seconds = debounce_seconds
        self._last_action_time: float = 0.0

    @property
    def state(self) -> AppState:
        return self._state

    @property
    def is_hidden(self) -> bool:
        return self._state == AppState.HIDDEN

    @property
    def is_idle(self) -> bool:
        return self._state == AppState.IDLE

    def request_hide(self) -> bool:
        """
        请求隐藏。

        返回 True 表示放行，调用方应继续执行隐藏流程。
        返回 False 表示拒绝（状态不符或防抖拦截）。
        """
        if self._state != AppState.IDLE:
            logging.warning("FSM: 拒绝隐藏请求，当前状态=%s", self._state.name)
            return False

        if not self._debounce_check():
            return False

        self._state = AppState.TRANSITIONING
        return True

    def request_restore(self) -> bool:
        """
        请求还原。

        返回 True 表示放行，调用方应继续执行还原流程。
        返回 False 表示拒绝。
        """
        if self._state != AppState.HIDDEN:
            logging.warning("FSM: 拒绝还原请求，当前状态=%s", self._state.name)
            return False

        if not self._debounce_check():
            return False

        self._state = AppState.TRANSITIONING
        return True

    def mark_hidden(self) -> None:
        """标记隐藏操作已完成"""
        self._state = AppState.HIDDEN
        logging.debug("FSM: 状态 → HIDDEN")

    def mark_restored(self) -> None:
        """标记还原操作已完成"""
        self._state = AppState.IDLE
        logging.debug("FSM: 状态 → IDLE")

    def mark_failed(self) -> None:
        """
        操作失败时回滚状态。

        根据上一个状态决定回滚到 IDLE 还是 HIDDEN。
        实际上根据 TRANSITIONING 之前的语义判断：
        - 如果当前是 TRANSITIONING 且之前是 IDLE → 回滚到 IDLE
        - 如果当前是 TRANSITIONING 且之前是 HIDDEN → 回滚到 HIDDEN
        """
        if self._state == AppState.TRANSITIONING:
            # 无法准确知道之前的状态，保守回滚到 IDLE
            self._state = AppState.IDLE
            logging.warning("FSM: 操作失败，回滚到 IDLE")

    # ── 内部 ──────────────────────────────────────────────

    def _debounce_check(self) -> bool:
        """防抖检查：距上次操作时间不足 debounce_seconds 则拒绝"""
        now = time.time()
        if now - self._last_action_time < self._debounce_seconds:
            logging.warning("FSM: 防抖拦截（间隔 %.2f 秒）", now - self._last_action_time)
            return False
        self._last_action_time = now
        return True
