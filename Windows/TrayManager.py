"""系统托盘管理器：视频隐藏后在系统托盘显示图标，点击可还原"""

import threading
import pystray
from PIL import Image, ImageDraw


def _create_icon_image() -> Image.Image:
    """绘制一个简单的托盘图标（绿色圆 + 白色播放三角）"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 深绿圆形背景
    margin = 4
    draw.ellipse([margin, margin, size - margin, size - margin],
                 fill=(34, 139, 34, 240))

    # 白色三角形（暂停/隐藏示意）
    cx, cy = size // 2, size // 2
    r = 14
    draw.polygon([
        (cx - r, cy - r),
        (cx - r, cy + r),
        (cx + r, cy),
    ], fill=(255, 255, 255, 255))

    return img


class TrayManager:
    """管理系统托盘图标——隐藏视频时出现，点击或快捷键可还原"""

    def __init__(self, on_restore_callback):
        """
        on_restore_callback: 用户点击托盘「还原窗口」时的回调，无参数
        """
        self._icon = None  # pystray.Icon | None
        self._on_restore = on_restore_callback
        self._icon_image = _create_icon_image()

    # ── 显示 / 隐藏托盘 ──────────────────────────────────────────

    def show(self) -> None:
        """在系统托盘中显示图标（如果尚未显示）"""
        if self._icon is not None:
            return

        menu = pystray.Menu(
            pystray.MenuItem("还原窗口", self._on_menu_restore, default=True),
            pystray.MenuItem("退出程序", self._on_menu_quit),
        )
        self._icon = pystray.Icon(
            "ClassMovieEasyWatch",
            self._icon_image,
            "视频已隐藏 — 右键菜单还原",
            menu,
        )
        threading.Thread(target=self._icon.run, daemon=True).start()

    def hide(self) -> None:
        """从系统托盘中移除图标"""
        if self._icon is None:
            return
        self._icon.stop()
        self._icon = None

    # ── 菜单回调 ─────────────────────────────────────────────────

    def _on_menu_restore(self, icon, item):
        self.hide()
        self._on_restore()

    def _on_menu_quit(self, icon, item):
        self.hide()
        import os
        os._exit(0)
