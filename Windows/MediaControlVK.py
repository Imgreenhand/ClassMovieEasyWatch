
import logging
import pythoncom
import win32gui
import win32api
from pycaw.pycaw import AudioUtilities

# 虚拟键码（保留全局媒体键，作为 fallback）
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002

# WM_APPCOMMAND 媒体控制常量（浏览器原生支持）
WM_APPCOMMAND = 0x0319
APPCOMMAND_MEDIA_PLAY_PAUSE = 14

_user32 = win32api

def send_appcommand_play_pause(hwnd: int) -> bool:
    """向目标窗口发送 WM_APPCOMMAND 媒体播放/暂停切换消息"""
    if not hwnd or not win32gui.IsWindow(hwnd):
        logging.warning(f"send_appcommand_play_pause: 无效窗口句柄 {hwnd}")
        return False
    try:
        lparam = (APPCOMMAND_MEDIA_PLAY_PAUSE << 16) | 0
        win32gui.PostMessage(hwnd, WM_APPCOMMAND, hwnd, lparam)
        print(f"WM_APPCOMMAND PLAY_PAUSE 已发送到窗口 {hwnd}")
        return True
    except Exception as e:
        logging.error(f"send_appcommand_play_pause: 发送失败 {e}，尝试使用toggle_play_pause发送全局媒体键")
        toggle_play_pause()
        return False

def toggle_play_pause() -> None:
    """旧方案：全局媒体暂停键，容易被其他应用劫持，不推荐"""
    _user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
    _user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)


def _get_volume():
    try:
        return AudioUtilities.GetSpeakers().EndpointVolume
    except Exception:
        logging.error("获取音量接口失败", exc_info=True)
        raise


def sound_to_zero() -> float:
    pythoncom.CoInitialize()
    try:
        vol = _get_volume()
        current = vol.GetMasterVolumeLevelScalar()
        vol.SetMasterVolumeLevelScalar(0.0, None)
        return current
    except Exception as e:
        logging.error(f"sound_to_zero: {e}", exc_info=True)
        return 0.0
    finally:
        pythoncom.CoUninitialize()


def back_to_sound(level: float) -> None:
    if level < 0.0 or level > 1.0:
        logging.error(f"back_to_sound: 参数不合法 {level}")
        return
    pythoncom.CoInitialize()
    try:
        vol = _get_volume()
        vol.SetMasterVolumeLevelScalar(level, None)
    except Exception as e:
        logging.error(f"back_to_sound: {e}", exc_info=True)
    finally:
        pythoncom.CoUninitialize()