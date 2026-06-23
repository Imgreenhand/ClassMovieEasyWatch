"""通过用户数据中进程名获取窗口句柄"""
import win32gui
import win32process
import psutil
import os


class GetMainWindow:
    """通过 return_hwnd() 获取目标窗口父窗口的 hwnd"""

    def __init__(self, browser_name: str = "msedge.exe"):
        self._browser_name = browser_name

    # 笔记：这相当于get
    @property
    def browser_name(self) -> str:
        return self._browser_name
    # 笔记：set
    @browser_name.setter
    def browser_name(self, value: str):
        self._browser_name = value

    # 窗口查找
    def find_windows_by_exe(self, exe_name: str):
        """找到全部名称为 exe_name 的窗口"""
        all_pids = []

        for pr in psutil.process_iter(["pid", "name", "exe"]):
            try:
                if pr.info["exe"] and exe_name.lower() == os.path.basename(pr.info["exe"]).lower():
                    all_pids.append(pr.info["pid"])
            except Exception:
                continue

        if not all_pids:
            return []

        target_windows = []
        # 枚举回调
        def enum_callback(hwnd, hwnd_list: list) -> bool:
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid in all_pids:
                    hwnd_list.append(hwnd)
            return True
        # EnumW：在枚举每一个窗口时调用回调，hwnd_list => target_win...
        win32gui.EnumWindows(enum_callback, target_windows)
        return target_windows

    def return_hwnd(self) -> list[int]:
        value = self.find_windows_by_exe(self._browser_name)
        return value
