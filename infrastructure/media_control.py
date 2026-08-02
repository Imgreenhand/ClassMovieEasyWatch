"""
【Infrastructure Layer】媒体控制器

实现 IMediaController 接口，负责：
- 向目标浏览器窗口发送播放 / 暂停指令（WM_APPCOMMAND / keybd_event）
- 系统音量的静音与恢复（pycaw）
"""

import logging
import pythoncom
import win32gui
import win32api
from pycaw.pycaw import AudioUtilities
from decision.interfaces import IMediaController

# ── 常量 ────────────────────────────────────────────────────

VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002
WM_APPCOMMAND = 0x0319
APPCOMMAND_MEDIA_PLAY_PAUSE = 14


class MediaController(IMediaController):
    """媒体控制器实现"""

    def __init__(self):
        self._volume_interface = None

    # ── IMediaController 实现 ─────────────────────────────

    def pause(self, hwnd_list: list[int] | None = None, method: str = "appcommand") -> bool:
        """
        暂停 / 播放目标窗口中的媒体。

        method:
          - "appcommand": 发送 WM_APPCOMMAND（推荐，浏览器原生支持）
          - "keybd_event": 全局媒体键（fallback）
        """
        if not hwnd_list:
            logging.warning("MediaController: 窗口句柄列表为空，无法发送暂停指令")
            return False

        success = False
        for hwnd in hwnd_list:
            try:
                if not win32gui.IsWindow(hwnd):
                    continue
                if method == "keybd_event":
                    self._global_media_key()
                    success = True
                else:
                    ok = self._send_appcommand(hwnd)
                    if ok:
                        success = True
            except Exception:
                logging.error("MediaController: 向窗口 %s 发送暂停指令失败", hwnd, exc_info=True)
        return success

    def mute(self) -> float:
        """静音并返回之前的音量值"""
        previous = 0.0
        try:
            pythoncom.CoInitialize()
        except Exception:
            pass
        try:
            vol = self._get_volume_interface()
            if vol is not None:
                previous = vol.GetMasterVolumeLevelScalar()
                vol.SetMasterVolumeLevelScalar(0.0, None)
        except Exception:
            logging.error("MediaController: 静音失败", exc_info=True)
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
        return previous

    def restore_volume(self, level: float) -> None:
        """恢复到指定音量值"""
        if level < 0.0 or level > 1.0:
            logging.warning("MediaController: 音量值 %s 不合法", level)
            return
        try:
            pythoncom.CoInitialize()
        except Exception:
            pass
        try:
            vol = self._get_volume_interface()
            if vol is not None:
                vol.SetMasterVolumeLevelScalar(level, None)
        except Exception:
            logging.error("MediaController: 恢复音量失败", exc_info=True)
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

    # ── 内部方法 ─────────────────────────────────────────

    def _get_volume_interface(self):
        if self._volume_interface is None:
            try:
                self._volume_interface = AudioUtilities.GetSpeakers().EndpointVolume
            except Exception:
                logging.error("MediaController: 获取音量接口失败", exc_info=True)
                return None
        return self._volume_interface

    @staticmethod
    def _send_appcommand(hwnd: int) -> bool:
        """向目标窗口发送 WM_APPCOMMAND 播放 / 暂停消息"""
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False
        try:
            lparam = (APPCOMMAND_MEDIA_PLAY_PAUSE << 16) | 0
            win32gui.PostMessage(hwnd, WM_APPCOMMAND, hwnd, lparam)
            logging.debug("WM_APPCOMMAND PLAY_PAUSE 已发送到窗口 %s", hwnd)
            return True
        except Exception:
            logging.error("MediaController: 发送 WM_APPCOMMAND 失败", exc_info=True)
            return False

    @staticmethod
    def _global_media_key() -> None:
        """全局媒体暂停键（fallback 方案）"""
        try:
            win32api.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            win32api.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)
        except Exception:
            logging.error("MediaController: 发送全局媒体键失败", exc_info=True)
