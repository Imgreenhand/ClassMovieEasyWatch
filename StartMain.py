import sys
import time
import win32gui
import logging

from PySide6.QtCore import QEventLoop

from Inputs.InputEvents import InputsEvents
from Inputs.ButtonEvents import ButtonEvents
from Windows.WindowManager import WindowManager
from Windows.MediaControlVK import send_appcommand_play_pause, toggle_play_pause, sound_to_zero, back_to_sound
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
        self._last_action_time = 0.0
        self._min_interval = 0.3  # 秒

    #隐藏
    def hide(self) -> bool:
        now = time.time()
        if now - self._last_action_time < self._min_interval:
            logging.warning("[防抖] 忽略重复的隐藏请求")
            return False
        self._last_action_time = now
        if self._window.is_hidden:
            logging.warning("[!] 已有窗口处于隐藏状态，忽略")
            return False

        # 先获取目标窗口句柄（尚未隐藏），以便快捷键模式精准发送
        hwnd_list = self._window.hider.return_hwnd()
        if not hwnd_list:
            logging.warning("[!] 未能获取目标窗口，请确认浏览器正在前台播放视频")
            return False
        
        """for hwnd in hwnd_list:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.05)"""

        if self._profile.auto_pause:
            self._do_pause(hwnd_list)
            time.sleep(0.2)

        ok = self._window.hide_window()
        if not ok:
            return False

        self._back_sound = sound_to_zero()
        return True

    # 还原
    def restore(self) -> bool:
        if not self._window.is_hidden:
            logging.warning("[!] 当前没有隐藏的窗口，忽略")
            return False

        hwnd = self._window.restore()
        if hwnd is None:
            logging.warning("[!] 原窗口已不存在")
            return False

        if self._back_sound is not None:
            back_to_sound(self._back_sound)
            self._back_sound = None

        """for hw in hwnd:
            win32gui.SetForegroundWindow(hw)
            time.sleep(0.05)"""
            
        if self._profile.auto_pause:
            self._do_pause(hwnd)
            time.sleep(0.2)
        return True

    def _do_pause(self, hwnd_list: list[int]) -> None:
        """根据配置档案的 pause_method 选择暂停方式"""
        method = getattr(self._profile, "pause_method", "appcommand")
        for hwnd in hwnd_list:
            if not win32gui.IsWindow(hwnd):
                continue
            if method == "keybd_event":
                toggle_play_pause()
                logging.debug("全局媒体键已发送")
            else:
                success = send_appcommand_play_pause(hwnd)
                logging.debug("窗口 %s 发送结果: %s", hwnd, success)

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
        hotspot_width=hider._profile.hotspot_width,
        hotspot_height=hider._profile.hotspot_height,
        hotspot_x=hider._profile.hotspot_x,
        hotspot_y=hider._profile.hotspot_y,
        highlight_seconds=hider._profile.highlight_seconds,
    )
    events.start()
    return events