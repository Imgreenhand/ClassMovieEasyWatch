import win32gui
import win32con
import logging
from .GetWindow import GetMainWindow

class WindowManager:
    """负责将当前活跃窗口隐藏到后台，并在需要时恢复"""

    def __init__(self, browser_name: str = "msedge.exe"):
        self._hidden_hwnd: list | None = None
        self.hider = GetMainWindow(browser_name=browser_name)

    def hide_window(self) -> bool:
        if self._hidden_hwnd is not None:
            return False

        hwnd = self.hider.return_hwnd()

        if not hwnd:
            return False

        self._hidden_hwnd = hwnd

        for h in hwnd:
            win32gui.ShowWindow(h, win32con.SW_HIDE)
        # SW_HIDE：窗口状态常量——隐藏
        return True

    def restore(self) -> list | None:
        """恢复之前隐藏的窗口，返回窗口句柄；若无隐藏窗口则返回 None"""
        hwnd_list = self._hidden_hwnd
        if hwnd_list is None:
            return None

        # 检查窗口是否还存在并尝试恢复
        for hwnd in hwnd_list:
            logging.debug("[WindowManager] 恢复窗口 %s", hwnd)
            if win32gui.IsWindow(hwnd):
                try:
                    # 先用 ShowWindow 恢复窗口（非阻塞）
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                except Exception:
                    # ShowWindow 一般不会抛，但保险起见捕获
                    pass

                try:
                    # 尝试把窗口设为前台；此调用可能被系统拒绝，捕获异常防止 crash
                    win32gui.SetForegroundWindow(hwnd)
                except Exception as e:
                    # 打印诊断信息并尝试一个温和的后备方案
                    logging.error("[WindowManager] SetForegroundWindow 失败: %s", e)
                    try:
                        # 尝试短暂置顶然后还原（有时能把窗口带到前台）
                        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0,0,0,0,
                                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0,0,0,0,
                                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                    except Exception:
                        # 忽略失败
                        logging.error("[WindowManager] SetForegroundWindow 后备方案也失败了")
                        pass

        self._hidden_hwnd = None
        return hwnd_list

    @property
    def is_hidden(self) -> bool:
        return self._hidden_hwnd is not None
