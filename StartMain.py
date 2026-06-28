import sys
import time

from Inputs.InputEvents import InputsEvents
from Inputs.ButtonEvents import ButtonEvents
from Windows.WindowManager import WindowManager
from Windows.MediaControlVK import toggle_play_pause, sound_to_zero, back_to_sound
from SaveData.DataManager import DataManager
from SaveData.FindSave import get_way, get_current_profile_name


# 核心逻辑
class MovieHider:
    """统筹隐藏 / 还原流程"""

    def __init__(self, profile):
        self._profile = profile
        self._window = WindowManager(browser_name=profile.browser_names)
        self._back_sound: float | None = None

    #隐藏
    def hide(self) -> None:
        if self._window.is_hidden:
            print("[!] 已有窗口处于隐藏状态，忽略")
            return

        if self._profile.auto_pause:
            print("[Hide] 正在暂停媒体...")
            toggle_play_pause()
            time.sleep(0.15)

        ok = self._window.hide_window()
        if not ok:
            print("[!] 未能获取目标窗口，请确认浏览器正在前台播放视频")
            return

        self._back_sound = sound_to_zero()

    # 还原
    def restore(self) -> None:
        if not self._window.is_hidden:
            print("[!] 当前没有隐藏的窗口，忽略")
            return

        print("[Restore] 正在还原窗口...")
        hwnd = self._window.restore()
        if hwnd is None:
            print("[!] 原窗口已不存在")
            return

        if self._back_sound is not None:
            back_to_sound(self._back_sound)
            self._back_sound = None

        if self._profile.auto_pause:
            print("[Restore] 窗口已还原，稍后恢复播放...")
            time.sleep(0.3)
            toggle_play_pause()
            print("[Restore] 播放已恢复")

def main():
    """初始化并返回 (MovieHider, events) 元组"""
    # 从存档读取触发方式和配置档案名
    way = get_way()
    profile_name = get_current_profile_name()

    # 加载配置档案
    dm = DataManager()
    profile = dm.data.get(profile_name) or dm.data.get("default")

    print(f"[Config] 触发方式: {way}")
    print(f"[Config] 配置档案: {profile.name}")
    print(f"[Config] 浏览器: {profile.browser_names}")
    print(f"[Config] 自动暂停: {'开' if profile.auto_pause else '关'}")

    # 初始化模块
    hider = MovieHider(profile)

    # 根据 way 选择 events 实现
    if way == "button":
        events = run_button_mode(hider)
    else:
        events = run_hotkey_mode(hider, profile)
    return hider, events


def run_hotkey_mode(hider, profile):
    """快捷键模式，返回 InputsEvents 实例供外部持有引用"""
    events = InputsEvents(
        hotkey_hide=profile.hotkey_hide,
        hotkey_restore=profile.hotkey_restore,
        on_hide=hider.hide,
        on_restore=hider.restore,
    )
    events.start()

    print("=" * 55)
    print(f"  ClassMovieEasyWatch 已就绪  [{profile.name}]")
    print(f"  {profile.hotkey_hide}   — 紧急隐藏（暂停 + 托盘）")
    print(f"  {profile.hotkey_restore}  — 还原继续（窗口 + 播放）")
    print("  托盘图标右键  — 还原 / 退出")
    print("=" * 55)
    return events


def run_button_mode(hider):
    """浮动按钮模式，返回 ButtonEvents 实例供外部持有引用"""
    events = ButtonEvents(
        on_hide=hider.hide,
        on_restore=hider.restore,
    )
    events.start()

    print("=" * 55)
    print("  ClassMovieEasyWatch 已就绪  [浮动按钮模式]")
    print("  点击屏幕上的浮动按钮进行隐藏 / 还原")
    print("  托盘图标右键  — 还原 / 退出")
    print("=" * 55)
    return events