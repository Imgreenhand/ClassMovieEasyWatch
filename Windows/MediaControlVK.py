"""媒体控制器：通过 Windows API 发送播放 / 暂停指令（不模拟键盘输入）"""

import ctypes

# 虚拟键码
VK_MEDIA_PLAY_PAUSE = 0xB3       # 播放 / 暂停 切换键
KEYEVENTF_KEYUP     = 0x0002     # 按键释放标志

_user32 = ctypes.windll.user32

def toggle_play_pause() -> None:
    """发送系统级「播放 / 暂停」媒体键事件

    所有主流浏览器（Edge / Chrome / Firefox）都会响应此系统媒体键，
    无需向特定窗口注入按键，比模拟 Space 更干净、更可靠。
    """
    _user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)           # 按下
    _user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)  # 释放
