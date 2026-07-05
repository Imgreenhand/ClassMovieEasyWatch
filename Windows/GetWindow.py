"""通过用户数据中进程名获取窗口句柄"""
import win32gui
import win32process
import psutil
import os


class GetMainWindow:
    """通过 return_hwnd() 获取目标窗口的 hwnd 列表"""

    def __init__(self, browser_name: str = "msedge.exe"):
        self._browser_name = browser_name

    @property
    def browser_name(self) -> str:
        return self._browser_name

    @browser_name.setter
    def browser_name(self, value: str):
        self._browser_name = value

    def find_windows_by_exe(self, exe_name: str) -> list[int]:
        """找到全部名称为 exe_name 的可见窗口"""
        all_pids = []
        for pr in psutil.process_iter(["pid", "name", "exe"]):
            try:
                if pr.info["exe"] and exe_name.lower() == os.path.basename(pr.info["exe"]).lower():
                    all_pids.append(pr.info["pid"])
            except Exception:
                continue

        if not all_pids:
            return []

        target_windows: list[int] = []
        def enum_callback(hwnd: int, hwnd_list: list[int]) -> bool:
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid in all_pids:
                    hwnd_list.append(hwnd)
            return True

        win32gui.EnumWindows(enum_callback, target_windows)
        return target_windows

    def return_hwnd(self) -> list[int]:
        return self.find_windows_by_exe(self._browser_name)
