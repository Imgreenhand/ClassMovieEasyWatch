"""
【Infrastructure Layer】配置档案管理器

实现 IProfileStore 接口，管理 JSON 格式的配置档案。
"""

import json
import logging
import threading
from pathlib import Path
from dataclasses import dataclass, asdict
from decision.interfaces import IProfileStore
from infrastructure.path_utils import get_data_dir


@dataclass
class Profile:
    """单份配置档案的数据结构"""
    name: str = "default"
    hotkey_hide: str = "<ctrl>+<alt>+q"
    hotkey_restore: str = "<ctrl>+<alt>+<f9>"
    browser_names: str = "msedge.exe"
    auto_pause: bool = True
    hotspot_width: int = 220
    hotspot_height: int = 120
    hotspot_x: float = 1.0
    hotspot_y: float = 1.0
    pause_method: str = "appcommand"
    highlight_seconds: int = 3


class ProfileStore(IProfileStore):
    """配置档案存取实现（线程安全单例）"""

    _instance: "ProfileStore | None" = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache: dict[str, Profile] = {}
                    cls._instance._loaded = False
        return cls._instance

    def __init__(self):
        # 只加载一次
        if not self._loaded:
            with self._lock:
                if not self._loaded:
                    self._load_all()
                    self._loaded = True

    # ── IProfileStore 实现 ────────────────────────────────

    def load_profile(self, name: str) -> dict | None:
        profile = self._cache.get(name)
        if profile is None:
            return None
        return asdict(profile)

    def save_profile(self, name: str, data: dict) -> bool:
        try:
            data["name"] = name
            profile = Profile(**{k: v for k, v in data.items() if k in Profile.__dataclass_fields__})
            self._cache[name] = profile

            file_path = get_data_dir() / f"{name}.json"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(profile), f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error("保存配置档案 '%s' 失败: %s", name, e)
            return False

    def list_profiles(self) -> list[str]:
        return sorted(self._cache.keys())

    # ── 扩展方法 ──────────────────────────────────────────

    def update_profile(self, name: str, **kwargs) -> bool:
        """部分更新配置档案，只修改传入的非 None 字段"""
        if name not in self._cache:
            logging.error("配置档案 '%s' 不存在", name)
            return False
        profile = self._cache[name]
        for key, value in kwargs.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)
        return self.save_profile(name, asdict(profile))

    def create_profile(self, name: str) -> bool:
        """创建新的配置档案（使用默认值）"""
        if name in self._cache:
            logging.warning("配置档案 '%s' 已存在", name)
            return False
        return self.save_profile(name, asdict(Profile(name=name)))

    def get_profile(self, name: str) -> Profile | None:
        """获取 Profile 对象（非字典）"""
        return self._cache.get(name)

    def reload(self) -> None:
        """从磁盘重新加载所有配置档案（用于外部修改后同步）"""
        self._load_all()

    # ── 内部方法 ──────────────────────────────────────────

    def _load_all(self) -> None:
        data_dir = get_data_dir()
        if not data_dir.exists():
            # 首次运行：从模板目录复制
            self._copy_templates()
        self._cache.clear()
        if not data_dir.exists():
            return
        for file_path in data_dir.glob("*.json"):
            try:
                raw = json.loads(file_path.read_text(encoding="utf-8"))
                raw["name"] = file_path.stem
                profile = Profile(**{k: v for k, v in raw.items() if k in Profile.__dataclass_fields__})
                self._cache[file_path.stem] = profile
            except (json.JSONDecodeError, TypeError) as e:
                logging.error("加载 %s 失败: %s，已跳过", file_path.name, e)

    @staticmethod
    def _copy_templates() -> None:
        """首次运行时将项目内 default.json 复制到用户数据目录"""
        import shutil
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        template_dir = Path(__file__).parent.parent / "SaveData"
        for name in ("default.json",):
            src = template_dir / name
            dst = data_dir / name
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
                logging.info("已复制模板文件: %s", name)
