import sys
import time

from PySide6.QtCore import QEventLoop

from Inputs.InputEvents import InputsEvents
from Inputs.ButtonEvents import ButtonEvents
from Windows.WindowManager import WindowManager
from Windows.MediaControlVK import toggle_play_pause, sound_to_zero, back_to_sound
from SaveData.DataManager import DataManager
from SaveData.FindSave import get_way, get_current_profile_name
from GUI.StartWindow import StartWindow


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

        hwnd = self._window.restore()
        if hwnd is None:
            print("[!] 原窗口已不存在")
            return

        if self._back_sound is not None:
            back_to_sound(self._back_sound)
            self._back_sound = None

        if self._profile.auto_pause:
            time.sleep(0.3)
            toggle_play_pause()

def main():
    """初始化并返回 (MovieHider, events) 元组"""
    # 显示开始窗口，等待用户选择后继续
    loop = QEventLoop()
    start_win = StartWindow(on_start=loop.quit)
    start_win.show()
    loop.exec()

    # 从存档读取触发方式和配置档案名
    way = get_way()
    profile_name = get_current_profile_name()

    # 加载配置档案
    dm = DataManager()
    profile = dm.data.get(profile_name) or dm.data.get("default")
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
    return events


def run_button_mode(hider):
    """浮动按钮模式，返回 ButtonEvents 实例供外部持有引用"""
    events = ButtonEvents(
        on_hide=hider.hide,
        on_restore=hider.restore,
    )
    events.start()
    return events