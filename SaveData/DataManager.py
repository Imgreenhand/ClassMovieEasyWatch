import json
import threading
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Data:
    """单份配置档案"""
    name: str = "default"                       # 档案名（不含 .json）
    hotkey_hide: str = "<ctrl>+<alt>+q"         # 隐藏热键
    hotkey_restore: str = "<ctrl>+<alt>+<f9>"   # 还原热键
    browser_names: str = "msedge.exe"           # 目标浏览器进程名
    auto_pause: bool = True                     # 隐藏时自动暂停
    tray_icon_enabled: bool = True              # 是否显示系统托盘图标

class DataManager:
    """配置档案管理器，提供一个Data单例"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            print("创建线程安全的单例实例")
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.data = {}
            self._initialized = True
