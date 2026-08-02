"""
【Decision Layer】Interfaces —— 抽象执行层

只定义方法签名，不关心线程模型。
由 Infrastructure Layer 负责实现。
"""

from abc import ABC, abstractmethod


class IWindowController(ABC):
    """窗口控制接口：隐藏 / 还原浏览器窗口"""

    @abstractmethod
    def hide_specific_windows(self, hwnd_list: list[int]) -> bool:
        """隐藏指定的窗口句柄列表，返回是否成功"""
        ...

    @abstractmethod
    def restore_window(self) -> bool:
        """还原之前隐藏的浏览器窗口，返回是否成功"""
        ...

    @abstractmethod
    def is_hidden(self) -> bool:
        """当前是否有窗口处于隐藏状态"""
        ...


class IMediaController(ABC):
    """媒体控制接口：暂停 / 静音"""

    @abstractmethod
    def pause(self, hwnd_list: list[int] | None = None, method: str = "appcommand") -> bool:
        """向目标窗口发送暂停 / 播放指令，返回是否成功"""
        ...

    @abstractmethod
    def mute(self) -> float:
        """将系统音量静音，返回静音前的音量值 (0.0~1.0)"""
        ...

    @abstractmethod
    def mute(self) -> float:
        """将系统音量静音，返回静音前的音量值 (0.0~1.0)"""
        ...

    @abstractmethod
    def restore_volume(self, level: float) -> None:
        """恢复到指定音量值"""
        ...


class IBrowserFinder(ABC):
    """浏览器窗口查找接口"""

    @abstractmethod
    def find_windows(self, process_name: str) -> list[int]:
        """根据进程名查找可见窗口句柄列表"""
        ...


class IProfileStore(ABC):
    """配置档案存取接口"""

    @abstractmethod
    def load_profile(self, name: str) -> dict | None:
        """加载指定名称的配置档案，返回字典或 None"""
        ...

    @abstractmethod
    def save_profile(self, name: str, data: dict) -> bool:
        """保存配置档案"""
        ...

    @abstractmethod
    def list_profiles(self) -> list[str]:
        """列出所有可用的配置档案名"""
        ...


class IUserPrefs(ABC):
    """用户偏好存取接口（触发方式、当前档案名）"""

    @abstractmethod
    def get_trigger_mode(self) -> str:
        """获取触发方式: "hotkey" | "button" """
        ...

    @abstractmethod
    def set_trigger_mode(self, mode: str) -> None:
        """设置触发方式"""
        ...

    @abstractmethod
    def get_current_profile_name(self) -> str:
        """获取当前激活的配置档案名"""
        ...

    @abstractmethod
    def set_current_profile_name(self, name: str) -> None:
        """设置当前激活的配置档案名"""
        ...
