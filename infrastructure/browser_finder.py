"""
【Infrastructure Layer】浏览器窗口查找器

实现 IBrowserFinder 接口，通过进程名查找可见窗口句柄。
"""

import logging
import os
import psutil
import win32gui
import win32process
from decision.interfaces import IBrowserFinder


class BrowserFinder(IBrowserFinder):
    """通过进程名查找对应的可见窗口句柄列表"""

    def find_windows(self, process_name: str) -> list[int]:
        if not process_name:
            logging.warning("BrowserFinder: 进程名为空")
            return []

        try:
            all_pids: list[int] = []
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    exe = proc.info.get("exe")
                    if exe and process_name.lower() == os.path.basename(exe).lower():
                        all_pids.append(proc.info["pid"])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            logging.error("BrowserFinder: 枚举进程时出错", exc_info=True)
            return []

        if not all_pids:
            return []

        target_windows: list[int] = []

        def _enum_callback(hwnd: int, _lparam: object) -> bool:
            try:
                if win32gui.IsWindowVisible(hwnd):
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid in all_pids:
                        target_windows.append(hwnd)
            except Exception:
                pass
            return True

        try:
            win32gui.EnumWindows(_enum_callback, None)
        except Exception:
            logging.error("BrowserFinder: 枚举窗口时出错", exc_info=True)

        return target_windows
