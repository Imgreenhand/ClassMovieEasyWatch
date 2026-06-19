import json
import threading
import logging
from dataclasses import dataclass, asdict
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
    """配置档案管理器，提供一个str, Data字典单例"""
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        # 笔记：new负责个对象分配内存，重写可以控制“是否构造对象”
        if cls._instance is None:
            # 笔记：with语句：正确打开资源并关闭
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # 先查在锁是因为锁耗资源大
        return cls._instance

    def __init__(self):
        # 笔记：init负责初始化对象
        if DataManager._initialized:
            return
        with DataManager._lock:
            if DataManager._initialized:
                return
            self.data = self.load()
            DataManager._initialized = True

    def load(self) -> dict[str, Data]:
        data_dict: dict[str, Data] = {}
        data_load = Path("SaveData") # 指定SaveData文件夹
        for file in data_load.rglob("*.json"):
            data_name = file.stem
            if data_name == "save":
                # 猎奇石山发力了
                continue
            try:
                with open(str(file), "r", encoding = "utf-8") as f:
                    nj = json.load(f)
                    data_dict[data_name] = Data(**nj)
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                logging.error(f"加载文件 {file.name} 失败: {e}，已跳过")
                continue
        return data_dict
    
    def save(self, name: str) -> bool:
        if name not in self.data:
            logging.error(f"档案 '{name}' 不存在，无法保存")
            return False
        data_load = Path(f"SaveData/{name}.json")
        data_load.parent.mkdir(parents = True, exist_ok = True)
        # 如果没有父目录则创建父目录
        try:
            with open(data_load, "w", encoding = "utf-8") as f:
                json.dump(asdict(self.data[name]), f, indent = 4, ensure_ascii = False)
                # 需存对象（asdict转换格式），文件对象，缩进，是否支持中文
        except Exception as e:
            logging.error(f"保存 {name}.json 失败: {e}")
            return False
        return True
    
    def change(self, name: str,
                hotkey_hide: str|None = None,
                hotkey_restore: str|None = None,  
                browser_names: str|None = None,  
                auto_pause: bool|None = None,  
                tray_icon_enabled: bool|None = None) -> bool:
        """
        修改指定档案的配置项，只修改传入的非 None 参数
        修改后自动保存到硬盘
        """
        # 检查档案是否存在
        if name not in self.data:
            logging.error(f"档案 '{name}' 不存在，无法修改")
            return False
        # 拿到要修改的对象
        config = self.data[name]
        # 逐一判断，只修改明确传入了新值的字段
        if hotkey_hide is not None:
            config.hotkey_hide = hotkey_hide
        if hotkey_restore is not None:
            config.hotkey_restore = hotkey_restore
        if browser_names is not None:
            config.browser_names = browser_names
        if auto_pause is not None:
            config.auto_pause = auto_pause
        if tray_icon_enabled is not None:
            config.tray_icon_enabled = tray_icon_enabled
        # 修改完后，自动调用 save 持久化
        return self.save(name)