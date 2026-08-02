"""
【Infrastructure Layer】窗口管理器

实现 IWindowController 接口，负责隐藏 / 还原浏览器窗口。
"""

import logging
import win32gui
import win32con
from decision.interfaces import IWindowController


class WindowManager(IWindowController):
    """管理目标浏览器窗口的隐藏与还原"""

    def __init__(self):
        self._hidden_hwnd: list[int] | None = None

    # ── IWindowController 实现 ─────────────────────────────

    def hide_window(self) -> bool:
        if self._hidden_hwnd is not None:
            logging.warning("WindowManager: 已有窗口处于隐藏状态")
            return False

        # hwnd 由外部通过 finder 获取后注入，此处仅执行隐藏
        # 实际使用时由 Orchestrator 先查找再隐藏
        return False  # 由 set_hwnd_and_hide 替代

    def restore_window(self) -> bool:
        hwnd_list = self._hidden_hwnd
        if hwnd_list is None:
            logging.warning("WindowManager: 没有待还原的窗口")
            return False

        restored_any = False
        for hwnd in hwnd_list:
            try:
                if not win32gui.IsWindow(hwnd):
                    logging.debug("WindowManager: 窗口 %s 已不存在，跳过", hwnd)
                    continue

                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                restored_any = True

                try:
                    win32gui.SetForegroundWindow(hwnd)
                except Exception:
                    # SetForegroundWindow 可能被系统拒绝，尝试后备方案
                    try:
                        win32gui.SetWindowPos(
                            hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
                        )
                        win32gui.SetWindowPos(
                            hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
                        )
                    except Exception:
                        pass
            except Exception:
                logging.error("WindowManager: 还原窗口 %s 时出错", hwnd, exc_info=True)

        self._hidden_hwnd = None
        return restored_any

    def is_hidden(self) -> bool:
        return self._hidden_hwnd is not None

    # ── 扩展方法 ────────────────────────────────────────────

    def hide_specific_windows(self, hwnd_list: list[int]) -> bool:
        """隐藏指定的窗口句柄列表"""
        if not hwnd_list:
            logging.warning("WindowManager: 窗口句柄列表为空")
            return False
        if self._hidden_hwnd is not None:
            logging.warning("WindowManager: 已有窗口处于隐藏状态")
            return False

        self._hidden_hwnd = list(hwnd_list)
        for hwnd in hwnd_list:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            except Exception:
                logging.error("WindowManager: 隐藏窗口 %s 时出错", hwnd, exc_info=True)
        return True
