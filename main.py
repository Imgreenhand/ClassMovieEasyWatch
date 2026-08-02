"""
【Composition Root】组装层 —— main.py

上帝层，知晓所有层级的存在，负责：
1. 组装业务逻辑（依赖注入）
2. 启动前检查资源是否存在（音频设备、浏览器窗口）
3. 如果可以降级，弹出 Toast 并降级运行
4. 程序入口
"""

import sys
import logging
import atexit
from pathlib import Path

# ── 配置日志 ────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

# ── 确保数据目录存在（首次运行复制模板） ──────────────────

from infrastructure.path_utils import get_data_dir


def _ensure_data_dir() -> None:
    """首次运行时将项目内 default.json 复制到用户数据目录"""
    import shutil
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    template_dir = Path(__file__).parent / "SaveData"
    for name in ("default.json",):
        src = template_dir / name
        dst = data_dir / name
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
            logging.info("已复制模板文件: %s", name)


_ensure_data_dir()

# ── 导入各层组件 ────────────────────────────────────────────

from decision.finite_state_machine import FiniteStateMachine
from decision.orchestrator import Orchestrator

from infrastructure.thread_pool import ThreadPool
from infrastructure.mailbox import Mailbox
from infrastructure.window_manager import WindowManager
from infrastructure.media_control import MediaController
from infrastructure.browser_finder import BrowserFinder
from infrastructure.data_manager import ProfileStore

from entry.gui_logic import GUILogic
from entry.listen_logic import ListenLogic


# ══════════════════════════════════════════════════════════════
# Composition Root —— 组装业务逻辑
# ══════════════════════════════════════════════════════════════

class App:
    """
    应用程序组装器。

    负责创建所有组件并注入依赖，管理整个应用的生命周期。
    """

    def __init__(self):
        # ── Infrastructure Layer ──────────────────────────
        self._thread_pool = ThreadPool.get_instance(max_workers=4)
        self._mailbox = Mailbox()

        self._window_manager = WindowManager()
        self._media_controller = MediaController()
        self._browser_finder = BrowserFinder()
        self._profile_store = ProfileStore()

        # ── Decision Layer ────────────────────────────────
        self._fsm = FiniteStateMachine(debounce_seconds=0.3)
        self._orchestrator = Orchestrator(
            fsm=self._fsm,
            window_controller=self._window_manager,
            media_controller=self._media_controller,
            browser_finder=self._browser_finder,
        )

        # ── Entry Layer (延迟创建，因为需要 QApplication) ──
        self._gui: GUILogic | None = None
        self._listen: ListenLogic | None = None

        # ── 运行时状态 ────────────────────────────────────
        self._current_profile_name: str = "default"
        self._current_mode: str = "hotkey"

    # ── 预飞检查 ──────────────────────────────────────────

    def preflight_checks(self) -> list[str]:
        """
        启动前检查资源是否存在。

        返回警告列表（空列表表示一切正常）。
        检查项：
        1. 音频设备驱动是否可用
        2. 是否能找到目标浏览器窗口
        """
        warnings: list[str] = []

        # 1. 检查音频设备
        try:
            import pythoncom
            from pycaw.pycaw import AudioUtilities
            pythoncom.CoInitialize()
            try:
                AudioUtilities.GetSpeakers()
                logging.info("预飞检查: 音频设备 OK")
            except Exception:
                warnings.append("未检测到音频输出设备，静音功能可能不可用")
                logging.warning("预飞检查: 音频设备不可用")
            finally:
                pythoncom.CoUninitialize()
        except ImportError:
            warnings.append("pycaw 库未安装，音量控制功能不可用")
        except Exception:
            warnings.append("音频设备检查失败，静音功能可能不可用")

        # 2. 检查浏览器进程
        try:
            profile = self._profile_store.get_profile(self._current_profile_name)
            browser_name = profile.browser_names if profile else "msedge.exe"
            hwnds = self._browser_finder.find_windows(browser_name)
            if not hwnds:
                warnings.append(f"未找到浏览器进程 '{browser_name}'，请确认浏览器正在运行")
                logging.warning("预飞检查: 未找到浏览器窗口")
            else:
                logging.info("预飞检查: 找到 %d 个浏览器窗口", len(hwnds))
        except Exception as e:
            warnings.append(f"浏览器窗口检查失败: {e}")

        return warnings

    # ── 组装启动 ──────────────────────────────────────────

    def initialize(self) -> int:
        """
        组装并启动应用。

        返回 QApplication.exec() 的退出码。
        """
        # 1. 创建 GUI 层
        self._gui = GUILogic(
            on_start=self._on_start_requested,
            on_stop=self._on_stop_requested,
        )
        app = self._gui.initialize()

        if not self._gui.setup_tray():
            logging.error("系统托盘初始化失败")
            return 1

        # 2. 注册清理
        atexit.register(self._cleanup)

        # 3. 运行事件循环
        return app.exec()

    # ── 事件处理 ──────────────────────────────────────────

    def _on_start_requested(self, mode: str, profile_name: str) -> None:
        """
        GUI 层发起"开始监听"请求。

        1. 加载配置档案
        2. 配置 Orchestrator
        3. 创建 ListenLogic
        4. 启动监听
        """
        try:
            self._current_mode = mode
            self._current_profile_name = profile_name

            # 加载配置档案
            profile = self._profile_store.get_profile(profile_name)
            if profile is None:
                self._gui.report_error(f"配置档案 '{profile_name}' 不存在")
                return

            # 配置 Orchestrator
            self._orchestrator.configure(
                browser_name=profile.browser_names,
                auto_pause=profile.auto_pause,
                pause_method=profile.pause_method,
            )

            # 预飞检查
            warnings = self.preflight_checks()
            for w in warnings:
                self._gui.report_warning(w)

            # 创建 ListenLogic
            self._listen = ListenLogic(
                mailbox=self._mailbox,
                on_hide=self._orchestrator.handle_hide,
                on_restore=self._orchestrator.handle_restore,
                error_reporter=self._gui.report_error,
            )

            # 根据模式启动
            ok = False
            if mode == "hotkey":
                ok = self._listen.start_hotkey_mode(
                    hotkey_hide=profile.hotkey_hide,
                    hotkey_restore=profile.hotkey_restore,
                )
            elif mode == "button":
                ok = self._listen.start_button_mode(
                    hotspot_width=profile.hotspot_width,
                    hotspot_height=profile.hotspot_height,
                    hotspot_x=profile.hotspot_x,
                    hotspot_y=profile.hotspot_y,
                    highlight_seconds=profile.highlight_seconds,
                )

            if ok:
                mode_text = "热键" if mode == "hotkey" else "鼠标热区"
                self._gui.report_info(f"监听已启动（{mode_text}模式，配置：{profile_name}）")

        except Exception:
            logging.error("App: 启动监听失败", exc_info=True)
            self._gui.report_error("启动监听时发生异常")

    def _on_stop_requested(self) -> None:
        """GUI 层发起"结束监听"请求"""
        try:
            if self._listen:
                self._listen.stop()
                self._listen = None
            # 如果有隐藏的窗口，先还原
            if self._window_manager.is_hidden():
                self._window_manager.restore_window()
                if self._gui:
                    self._gui.report_warning("监听已停止，窗口已还原")
        except Exception:
            logging.error("App: 停止监听失败", exc_info=True)
            if self._gui:
                self._gui.report_error("停止监听时发生异常")

    def _cleanup(self) -> None:
        """程序退出时的清理工作"""
        try:
            if self._listen:
                self._listen.stop()
        except Exception:
            pass
        try:
            if self._window_manager.is_hidden():
                self._window_manager.restore_window()
        except Exception:
            pass
        try:
            self._thread_pool.shutdown(wait=False)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
# 程序入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    application = App()
    sys.exit(application.initialize())