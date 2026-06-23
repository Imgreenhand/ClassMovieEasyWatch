import ctypes
import logging
import pythoncom
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL

# 虚拟键码
VK_MEDIA_PLAY_PAUSE = 0xB3       # 播放 / 暂停 切换键
KEYEVENTF_KEYUP     = 0x0002     # 按键释放标志

_user32 = ctypes.windll.user32

def toggle_play_pause() -> None:
    _user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)           # 按下
    _user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)  # 释放

def _get_volume() -> IAudioEndpointVolume:
    """获取系统默认音频端点音量接口"""
    try:
        return AudioUtilities.GetSpeakers().EndpointVolume
    except Exception:
        logging.error("获取音量接口失败", exc_info=True)
        raise

def sound_to_zero() -> float:
    """获取当前系统音量并将音量设为0，返回原音量值(0.0~1.0)"""
    # 笔记：pynput 热键回调在后台线程，必须初始化 COM
    pythoncom.CoInitialize()
    try:
        vol = _get_volume()
        current = vol.GetMasterVolumeLevelScalar()
        vol.SetMasterVolumeLevelScalar(0.0, None)
        return current
    except Exception:
        logging.error("sound_to_zero: 音量操作失败", exc_info = True)
        return 0.0
    finally:
        pythoncom.CoUninitialize()

def back_to_sound(level: float) -> None:
    """将系统音量恢复到指定值"""
    if level < 0.0 or level > 1.0:
        logging.error(f"back_to_sound: 参数不合法: {level}")
        return
    pythoncom.CoInitialize()
    try:
        vol = _get_volume()
        vol.SetMasterVolumeLevelScalar(level, None)
    except Exception:
        logging.error("back_to_sound: 音量恢复失败", exc_info=True)
    finally:
        pythoncom.CoUninitialize()
