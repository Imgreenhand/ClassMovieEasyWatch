"""
【Decision Layer】编排器

若 FSM 放行，Orchestrator 负责按顺序编排操作。

Hide 流程：查找窗口 → 自动暂停（可选）→ 隐藏窗口 → 静音
Restore 流程：还原窗口 → 恢复音量 → 自动暂停（可选）
"""

import time
import logging
from decision.finite_state_machine import FiniteStateMachine
from decision.interfaces import IWindowController, IMediaController, IBrowserFinder


class Orchestrator:
    """编排器：持有所有基础设施接口的引用，按顺序执行操作"""

    def __init__(
        self,
        fsm: FiniteStateMachine,
        window_controller: IWindowController,
        media_controller: IMediaController,
        browser_finder: IBrowserFinder,
    ):
        self._fsm = fsm
        self._window = window_controller
        self._media = media_controller
        self._finder = browser_finder

        # 运行时配置（由外部注入）
        self._browser_name: str = "msedge.exe"
        self._auto_pause: bool = True
        self._pause_method: str = "appcommand"
        self._previous_volume: float | None = None

    # ── 配置 ──────────────────────────────────────────────

    def configure(self, browser_name: str, auto_pause: bool, pause_method: str) -> None:
        """更新运行时配置"""
        self._browser_name = browser_name
        self._auto_pause = auto_pause
        self._pause_method = pause_method

    # ── 指令处理 ──────────────────────────────────────────

    def handle_hide(self) -> bool:
        """
        处理隐藏指令。

        流程：FSM 放行 → 查找窗口 → 暂停 → 隐藏 → 静音
        返回 True 表示成功。
        """
        if not self._fsm.request_hide():
            return False

        try:
            # 1. 查找目标窗口
            hwnd_list = self._finder.find_windows(self._browser_name)
            if not hwnd_list:
                logging.warning("Orchestrator: 未找到目标浏览器窗口")
                self._fsm.mark_failed()
                return False

            # 2. 自动暂停（可选）
            if self._auto_pause:
                self._media.pause(hwnd_list, method=self._pause_method)
                time.sleep(0.2)

            # 3. 隐藏窗口
            if not self._window.hide_specific_windows(hwnd_list):
                logging.error("Orchestrator: 隐藏窗口失败")
                self._fsm.mark_failed()
                return False

            # 4. 静音
            self._previous_volume = self._media.mute()

            self._fsm.mark_hidden()
            logging.info("Orchestrator: 隐藏流程完成")
            return True

        except Exception:
            logging.error("Orchestrator: 隐藏流程异常", exc_info=True)
            self._fsm.mark_failed()
            return False

    def handle_restore(self) -> bool:
        """
        处理还原指令。

        流程：FSM 放行 → 还原窗口 → 恢复音量 → 暂停（可选）
        返回 True 表示成功。
        """
        if not self._fsm.request_restore():
            return False

        try:
            # 1. 还原窗口
            if not self._window.restore_window():
                logging.warning("Orchestrator: 还原窗口失败（窗口可能已不存在）")
                self._fsm.mark_restored()  # 就算窗口没了也恢复正常状态
                return False

            # 2. 恢复音量
            if self._previous_volume is not None:
                self._media.restore_volume(self._previous_volume)
                self._previous_volume = None

            # 3. 自动暂停（可选）
            if self._auto_pause:
                hwnd_list = self._finder.find_windows(self._browser_name)
                if hwnd_list:
                    self._media.pause(hwnd_list, method=self._pause_method)
                    time.sleep(0.2)

            self._fsm.mark_restored()
            logging.info("Orchestrator: 还原流程完成")
            return True

        except Exception:
            logging.error("Orchestrator: 还原流程异常", exc_info=True)
            self._fsm.mark_failed()
            return False
