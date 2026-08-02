"""
【Infrastructure Layer】路径工具

提供资源路径解析、用户数据目录定位等功能。
兼容 PyInstaller 打包和开发环境。
"""

import os
import sys
import json
import logging
from pathlib import Path
from dataclasses import dataclass


def resource_path(relative_path: str) -> str:
    """返回资源文件的绝对路径，兼容 PyInstaller 打包和开发环境"""
    base = getattr(sys, "_MEIPASS", "")
    if base:
        return str(Path(base) / relative_path)
    return str(Path(__file__).parent.parent / relative_path)


def get_data_dir() -> Path:
    """返回用户数据目录：%APPDATA%/ClassMovieEasyWatch/"""
    return Path(os.environ["APPDATA"]) / "ClassMovieEasyWatch"


# ── 用户偏好 save.txt ──────────────────────────────────────

SAVE_FILE = get_data_dir() / "save.txt"


@dataclass
class SaveData:
    way: str = "hotkey"             # hotkey | button
    save_file: str = "default"      # 当前激活的配置档案名


def _read_save() -> dict:
    """读取 save.txt，失败时返回空字典"""
    try:
        if SAVE_FILE.exists():
            return json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logging.warning("读取 save.txt 失败: %s", e)
    return {}


def _write_save(data: dict) -> None:
    """写入 save.txt"""
    try:
        SAVE_FILE.parent.mkdir(parents=True, exist_ok=True)
        SAVE_FILE.write_text(
            json.dumps(data, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as e:
        logging.error("写入 save.txt 失败: %s", e)


def get_trigger_mode() -> str:
    """返回当前触发方式："hotkey" 或 "button"，默认 "hotkey" """
    data = _read_save()
    way = data.get("way", "hotkey")
    if way not in ("hotkey", "button"):
        way = "hotkey"
    return way


def set_trigger_mode(mode: str) -> None:
    """写入触发方式（保留其他字段）"""
    data = _read_save()
    data["way"] = mode
    _write_save(data)


def get_current_profile_name() -> str:
    """返回当前激活的配置档案名，默认 "default" """
    data = _read_save()
    return data.get("save_file", "default")


def set_current_profile_name(name: str) -> None:
    """写入当前激活的配置档案名（保留其他字段）"""
    data = _read_save()
    data["save_file"] = name
    _write_save(data)
