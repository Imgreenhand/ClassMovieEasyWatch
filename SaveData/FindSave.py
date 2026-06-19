"""读取 / 写入用户上一次的触发方式和Data"""

import json
from pathlib import Path
from dataclasses import dataclass

SAVE_FILE = Path("SaveData/save.json")

@dataclass
class Save:
    way: str = "hotkey"             # hotkey: 快捷键 | button: 浮动按钮
    save_file: str = "default"      # 当前激活的配置档案名

def _read_save() -> dict:
    """读取整个 save.json，失败时返回空字典"""
    try:
        return json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _write_save(data: dict) -> None:
    """写入 save.json"""
    SAVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SAVE_FILE.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")

# way
def get_way() -> str:
    """返回当前触发方式："hotkey" 或 "button"，默认 "hotkey" """
    data = _read_save()
    way = data.get("way", "hotkey")
    if way not in ("hotkey", "button"):
        way = "hotkey"
    return way

# save_file
def get_current_profile_name() -> str:
    """返回当前激活的配置档案名，默认 "default" """
    data = _read_save()
    return data.get("save_file", "default")

def set_current_profile_name(name: str) -> None:
    """写入当前激活的配置档案名（保留 way 字段）"""
    data = _read_save()
    data["save_file"] = name
    _write_save(data)