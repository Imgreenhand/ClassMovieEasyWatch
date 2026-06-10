"""窗口管理器：隐藏 / 恢复当前前台窗口"""

import win32gui
import win32con
from .GetWindow import GetMainWindow

class WindowManager:
    """负责将当前活跃窗口隐藏到后台，并在需要时恢复"""

    def __init__(self, browser_name: str = "msedge.exe"):
        self._hidden_hwnd: list | None = None   # 被隐藏窗口的句柄
        self.hider = GetMainWindow(browser_name=browser_name)

    # ── 隐藏 ─────────────────────────────────────────────────────

    def hide_window(self) -> bool:
        """隐藏当前前台窗口，返回是否成功"""
        if self._hidden_hwnd is not None:
            return False  # 已经隐藏了一个窗口，防止重复隐藏

        hwnd = self.hider.return_hwnd()

        if not hwnd:
            return False

        self._hidden_hwnd = hwnd

        for h in hwnd:
            win32gui.ShowWindow(h, win32con.SW_HIDE)

        return True

    # ── 恢复 ─────────────────────────────────────────────────────

    def restore(self) -> list | None:
        """恢复之前隐藏的窗口，返回窗口句柄；若无隐藏窗口则返回 None"""
        hwnd_list = self._hidden_hwnd
        if hwnd_list is None:
            return None

        # 检查窗口是否还存在
        for hwnd in hwnd_list:
            if win32gui.IsWindow(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)

        self._hidden_hwnd = None

        return hwnd_list

    # ── 状态 ─────────────────────────────────────────────────────

    @property
    def is_hidden(self) -> bool:
        return self._hidden_hwnd is not None
