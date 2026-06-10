"""配置档案管理：支持多配置文件加载，不提供修改功能"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


# ═══════════════════════════════════════════════════════════════════
# 配置数据类
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Profile:
    """单份配置档案"""
    name: str = "default"                       # 档案名（不含 .json）
    hotkey_hide: str = "<ctrl>+<alt>+q"         # 隐藏热键
    hotkey_restore: str = "<ctrl>+<alt>+<f9>"   # 还原热键
    browser_names: str = "msedge.exe"           # 目标浏览器进程名
    auto_pause: bool = True                     # 隐藏时自动暂停
    tray_icon_enabled: bool = True              # 是否显示系统托盘图标


# ═══════════════════════════════════════════════════════════════════
# 档案管理器
# ═══════════════════════════════════════════════════════════════════

class ProfileManager:
    """扫描 SaveData 目录，加载 / 切换配置档案"""

    # 内置默认值（文件缺失时回退）
    _DEFAULTS = {
        "hotkey_hide": "<ctrl>+<alt>+q",
        "hotkey_restore": "<ctrl>+<alt>+<f9>",
        "browser_names": "msedge.exe",
        "auto_pause": True,
        "tray_icon_enabled": True,
    }

    def __init__(self, save_dir: str = "SaveData"):
        self._dir = Path(save_dir).resolve()
        self._profiles: dict[str, Profile] = {}
        self._current: Profile | None = None
        self._scan()

    # ── 扫描 ──────────────────────────────────────────────────

    def _scan(self) -> None:
        """扫描目录下所有 .json 文件"""
        if not self._dir.exists():
            return

        for f in self._dir.glob("*.json"):
            name = f.stem  # 去掉 .json 后缀
            if f.stem == "save":   # 跳过 save.json，因为它不是配置档案
                continue
            self._profiles[name] = self._load_file(f, name)

        # 如果 default.json 不存在，用内置默认值创建一个内存 Profile
        if "default" not in self._profiles:
            self._profiles["default"] = Profile(name="default", **self._DEFAULTS)

    def _load_file(self, path: Path, name: str) -> Profile:
        """从 JSON 文件读取并合并默认值"""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}

        merged = {**self._DEFAULTS, **data}
        return Profile(name=name, **merged)

    # ── 查询 ──────────────────────────────────────────────────

    def list_profiles(self) -> list[str]:
        """返回所有可用档案名（不含 .json）"""
        return sorted(self._profiles.keys())

    def load(self, name: str = "default") -> Profile:
        """加载指定档案为当前档案，未找到时回退到 default"""
        if name not in self._profiles:
            print(f"[Profile] 未找到档案 '{name}'，回退到 'default'")
            name = "default"

        self._current = self._profiles[name]
        print(f"[Profile] 已加载档案: {self._current.name}")
        return self._current

    # ── 当前档案 ──────────────────────────────────────────────

    @property
    def current(self) -> Profile:
        """获取当前档案（未显式 load 时自动加载 default）"""
        if self._current is None:
            self.load("default")
        return self._current  # type: ignore[return-value]

    def __iter__(self) -> Iterator[Profile]:
        return iter(self._profiles.values())

    def __len__(self) -> int:
        return len(self._profiles)
