"""通过用户数据中进程名获取窗口句柄"""
import win32gui
import win32process
import psutil
import os


class GetMainWindow:
    """通过 return_hwnd() 获取目标窗口父窗口的 hwnd"""

    def __init__(self, browser_name: str = "msedge.exe"):
        """
        browser_name: 目标浏览器进程名，如 msedge.exe / chrome.exe / firefox.exe
        """
        self._browser_name = browser_name

    # ── 动态浏览器名 ──────────────────────────────────────────

    @property
    def browser_name(self) -> str:
        return self._browser_name

    @browser_name.setter
    def browser_name(self, value: str):
        self._browser_name = value

    # ── 窗口查找 ──────────────────────────────────────────────

    def find_windows_by_exe(self, exe_name: str):
        """找到全部名称为 exe_name 的可见窗口"""
        all_pids = []

        for pr in psutil.process_iter(["pid", "name", "exe"]):
            try:
                if pr.info["exe"] and exe_name.lower() == os.path.basename(pr.info["exe"]).lower():
                    all_pids.append(pr.info["pid"])
                    print(f"[GetWindow] 找到对应任务，pid = {pr.info['pid']}")
            except Exception:
                continue

        if not all_pids:
            return []

        target_windows = []

        def enum_callback(hwnd, hwnd_list: list):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid in all_pids:
                    hwnd_list.append(hwnd)
            return True

        win32gui.EnumWindows(enum_callback, target_windows)
        return target_windows

    def return_hwnd(self) -> list[int]:
        """返回当前目标浏览器的所有可见窗口句柄"""
        value = self.find_windows_by_exe(self._browser_name)
        print(f"[DEBUG] return_hwnd 返回 {len(value)} 个窗口句柄: {value}")
        return value
