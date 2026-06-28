import json
import winreg
import logging
from collections.abc import Callable
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QFrame, QVBoxLayout,
    QHBoxLayout, QGridLayout, QCheckBox, QLineEdit,
    QSizePolicy, QListWidget, QListWidgetItem, QApplication,
)

from SaveData.DataManager import DataManager

SAVE_DIR = Path("SaveData")

# ── 虚拟键盘布局：(显示文本, pynput值, 宽度比例) ──
KEYBOARD_ROWS = [
    [("F1","f1",1),("F2","f2",1),("F3","f3",1),("F4","f4",1),
     ("F5","f5",1),("F6","f6",1),("F7","f7",1),("F8","f8",1),
     ("F9","f9",1),("F10","f10",1),("F11","f11",1),("F12","f12",1)],
    [("`","`",1),("1","1",1),("2","2",1),("3","3",1),("4","4",1),
     ("5","5",1),("6","6",1),("7","7",1),("8","8",1),("9","9",1),
     ("0","0",1),("-","-",1),("=","=",1),("Back","backspace",2)],
    [("Tab","tab",1.5),("Q","q",1),("W","w",1),("E","e",1),("R","r",1),
     ("T","t",1),("Y","y",1),("U","u",1),("I","i",1),("O","o",1),
     ("P","p",1),("[","[",1),("]","]",1),("\\","\\",1.5)],
    [("Caps","caps_lock",1.8),("A","a",1),("S","s",1),("D","d",1),
     ("F","f",1),("G","g",1),("H","h",1),("J","j",1),("K","k",1),
     ("L","l",1),(";",";",1),("'","'",1),("Enter","enter",2.2)],
    [("Shift","shift",2.3),("Z","z",1),("X","x",1),("C","c",1),
     ("V","v",1),("B","b",1),("N","n",1),("M","m",1),(",",",",1),
     (".",".",1),("/","/",1),("Shift","shift",2.7)],
    [("Ctrl","ctrl",1.3),("Win","win",1.3),("Alt","alt",1.3),
     ("Space","space",5),("Alt","alt",1.3),("Win","win",1.3),
     ("Ctrl","ctrl",1.3)],
]

MODIFIER_KEYS = {"ctrl", "alt", "shift", "win"}
# 需要用 <> 包裹的特殊键（pynput 规范）
BRACKET_KEYS = {
    "f1","f2","f3","f4","f5","f6","f7","f8","f9","f10","f11","f12",
    "space","tab","enter","backspace","esc","caps_lock","delete",
    "up","down","left","right","home","end","page_up","page_down",
    "insert","pause","print_screen",
}


class KeyButton(QPushButton):
    """虚拟键盘上的单个按键"""

    def __init__(self, text: str, key_val: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.key_val = key_val
        self.is_modifier = key_val in MODIFIER_KEYS
        self._active = False
        self.setFont(QFont("微软雅黑", 8))
        self.setFixedHeight(28)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._update_style()

    def active(self) -> bool:
        return self._active

    def _update_style(self) -> None:
        if self._active:
            self.setStyleSheet("""
                QPushButton {
                    background: #fb7299; color: #fff; border: 1px solid #e55a80;
                    border-radius: 3px; font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: #f5f5f5; color: #333; border: 1px solid #ddd;
                    border-radius: 3px;
                }
                QPushButton:hover { background: #ffe0ea; border-color: #fb7299; }
            """)


class VirtualKeyboard(QFrame):
    """虚拟键盘组件，用于选择快捷键组合"""

    def __init__(self, title: str, parent: QWidget | None = None,
                 on_changed: Callable[[], None] | None = None):
        super().__init__(parent)
        self._on_changed = on_changed
        self.setStyleSheet("background: #ffffff; border: 1px solid #eee; border-radius: 6px;")

        self._mod_btns: dict[str, KeyButton] = {}
        self._main_key_btn: KeyButton | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(5)

        # 标题 + 当前选择显示
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("微软雅黑", 11, QFont.Bold))
        title_label.setStyleSheet("color: #fb7299; background: transparent; border: none;")
        header.addWidget(title_label)

        self._current_label = QLabel("未选择")
        self._current_label.setFont(QFont("微软雅黑", 10))
        self._current_label.setStyleSheet(
            "color: #333; background: #fafafa; border: 1px solid #eee; "
            "border-radius: 4px; padding: 2px 10px;"
        )
        header.addWidget(self._current_label)
        header.addStretch()
        layout.addLayout(header)

        # 键盘网格
        for row_data in KEYBOARD_ROWS:
            row_widget = QWidget()
            row_widget.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(2)
            for display, key_val, wf in row_data:
                btn = KeyButton(display, key_val)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                btn.setMinimumWidth(int(26 * wf))
                btn.clicked.connect(lambda checked, b=btn: self._on_key_click(b))
                row_layout.addWidget(btn)
                if key_val in MODIFIER_KEYS and key_val not in self._mod_btns:
                    self._mod_btns[key_val] = btn
            layout.addWidget(row_widget)

    def set_hotkey(self, hotkey_str: str) -> None:
        """根据 '<ctrl>+<alt>+<f9>' 格式设置键盘状态"""
        for btn in self._mod_btns.values():
            btn.set_active(False)
        if self._main_key_btn:
            self._main_key_btn.set_active(False)
            self._main_key_btn = None

        parts = hotkey_str.strip().split("+")
        mods: list[str] = []
        key = ""
        for p in parts:
            p = p.strip()
            if p.startswith("<") and p.endswith(">"):
                inner = p[1:-1].lower()
                if inner in MODIFIER_KEYS:
                    mods.append(inner)
                else:
                    key = inner
            else:
                key = p.lower()

        for m in mods:
            if m in self._mod_btns:
                self._mod_btns[m].set_active(True)
        if key:
            for child in self.findChildren(KeyButton):
                if child.key_val == key and not child.is_modifier:
                    child.set_active(True)
                    self._main_key_btn = child
                    break
        self._update_label()

    def get_hotkey(self) -> str:
        """返回当前快捷键字符串，特殊键用 <> 包裹"""
        mods = [k for k, btn in self._mod_btns.items() if btn.active()]
        key = self._main_key_btn.key_val if self._main_key_btn else ""
        if not key:
            return ""
        key_str = f"<{key}>" if key in BRACKET_KEYS else key
        return "+".join(f"<{m}>" for m in mods) + f"+{key_str}"

    def _on_key_click(self, btn: KeyButton) -> None:
        if btn.is_modifier:
            btn.set_active(not btn.active())
        else:
            if self._main_key_btn and self._main_key_btn is not btn:
                self._main_key_btn.set_active(False)
            btn.set_active(not btn.active())
            self._main_key_btn = btn if btn.active() else None
        self._update_label()
        if self._on_changed:
            self._on_changed()

    def _update_label(self) -> None:
        hk = self.get_hotkey()
        self._current_label.setText(hk if hk else "未选择")


class SettingMainScroll(QFrame):
    """设置窗口主内容区域，管理热键/应用/个性化三个页面"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet("background: #ffffff;")

        self._pages: dict[str, QWidget] = {}
        self._current_page: str = ""
        self._profile_name: str = "default"

        # 外层布局：内容区 + 弹性空间 + 底部图
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 内容容器（占位或页面在此切换）
        self._content_box = QWidget(self)
        self._content_box.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content_box)
        self._content_layout.setContentsMargins(0, 0, 0, 0)

        self._placeholder = QLabel("请从左侧选择设置项")
        self._placeholder.setFont(QFont("微软雅黑", 13))
        self._placeholder.setStyleSheet("color: #bbb; background: transparent;")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._content_layout.addWidget(self._placeholder)

        outer.addWidget(self._content_box)

        # 弹性空间把底部图推到底部
        outer.addStretch()

        # 底部图
        bottom_pix = QPixmap("GUI/Art/2233Seting.png")
        if not bottom_pix.isNull():
            bottom_label = QLabel()
            bottom_label.setPixmap(bottom_pix.scaledToWidth(240, Qt.SmoothTransformation))
            bottom_label.setAlignment(Qt.AlignCenter)
            bottom_label.setStyleSheet("background: transparent;")
            outer.addWidget(bottom_label)

    def load_profile(self, name: str) -> None:
        """从 SaveData/{name}.json 加载配置到各页面"""
        self._profile_name = name
        path = SAVE_DIR / f"{name}.json"
        data: dict = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

        if hasattr(self, "_kb_hide"):
            self._kb_hide.set_hotkey(data.get("hotkey_hide", "<ctrl>+<alt>+q"))
        if hasattr(self, "_kb_restore"):
            self._kb_restore.set_hotkey(data.get("hotkey_restore", "<ctrl>+<alt>+<f9>"))

        if "appname" in self._pages:
            page = self._pages["appname"]
            app_input = page.findChild(QLineEdit, "app_input")
            if app_input:
                app_input.setText(data.get("browser_names", "msedge.exe"))

        if "personal" in self._pages:
            page = self._pages["personal"]
            auto_cb = page.findChild(QCheckBox, "auto_pause")
            if auto_cb:
                auto_cb.setChecked(data.get("auto_pause", True))

    def collect_data(self) -> dict:
        """收集所有页面表单数据为字典"""
        data: dict = {
            "hotkey_hide": "<ctrl>+<alt>+q",
            "hotkey_restore": "<ctrl>+<alt>+<f9>",
            "browser_names": "msedge.exe",
            "auto_pause": True,
        }
        if hasattr(self, "_kb_hide"):
            hk = self._kb_hide.get_hotkey()
            if hk:
                data["hotkey_hide"] = hk
        if hasattr(self, "_kb_restore"):
            hk = self._kb_restore.get_hotkey()
            if hk:
                data["hotkey_restore"] = hk

        if "appname" in self._pages:
            page = self._pages["appname"]
            app_input = page.findChild(QLineEdit, "app_input")
            if app_input and app_input.text().strip():
                data["browser_names"] = app_input.text().strip()

        if "personal" in self._pages:
            page = self._pages["personal"]
            auto_cb = page.findChild(QCheckBox, "auto_pause")
            if auto_cb:
                data["auto_pause"] = auto_cb.isChecked()

        return data

    # ── 实时同步：UI → DataManager 内存 ─────────────────────────

    def _get_current_config(self):
        """获取当前配置档案的 Data 对象，不存在则返回 None"""
        dm = DataManager()
        if self._profile_name not in dm.data:
            return None
        return dm.data[self._profile_name]

    def _sync_hotkey_to_memory(self, which: str) -> None:
        config = self._get_current_config()
        if config is None:
            logging.warning("_sync_hotkey_to_memory: 当前配置档案 %s 不在 DataManager 中", self._profile_name)
            return
        kb = self._kb_hide if which == "hide" else self._kb_restore
        hk = kb.get_hotkey()
        if not hk:
            return
        if which == "hide":
            config.hotkey_hide = hk
        else:
            config.hotkey_restore = hk
        logging.info("热键已同步到内存: %s = %s", which, hk)

    def _sync_appname_to_memory(self, text: str) -> None:
        config = self._get_current_config()
        if config is not None and text.strip():
            config.browser_names = text.strip()

    def _sync_autopause_to_memory(self, state: int) -> None:
        config = self._get_current_config()
        if config is not None:
            config.auto_pause = bool(state)

    def switch_page(self, name: str) -> None:
        """切换到指定页面，按需构建"""
        if name == self._current_page:
            return
        if name not in self._pages:
            self._pages[name] = self._build_page(name)

        # 清空内容区，放入新页面
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
        page = self._pages[name]
        self._content_layout.addWidget(page)
        page.show()
        self._current_page = name
        # 新页面构建后填充当前配置档案数据
        self.load_profile(self._profile_name)

    # ── 页面构建 ────────────────────────────────────────────────

    def _build_page(self, name: str) -> QWidget:
        if name == "热键修改":
            return self._build_hotkey_page()
        elif name == "应用名称":
            return self._build_app_page()
        elif name == "个性化设置":
            return self._build_personal_page()
        return QWidget()

    def _build_hotkey_page(self) -> QWidget:
        page = QWidget(self)
        page.setObjectName("hotkey")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self._kb_hide = VirtualKeyboard("隐藏快捷键", on_changed=lambda: self._sync_hotkey_to_memory("hide"))
        self._kb_hide.setObjectName("kb_hide")
        layout.addWidget(self._kb_hide)

        self._kb_restore = VirtualKeyboard("还原快捷键", on_changed=lambda: self._sync_hotkey_to_memory("restore"))
        self._kb_restore.setObjectName("kb_restore")
        layout.addWidget(self._kb_restore)

        hint = QLabel("点击修饰键切换，再点击一个普通键组合快捷键")
        hint.setFont(QFont("微软雅黑", 9))
        hint.setStyleSheet("color: #999; background: transparent; padding: 2px 0;")
        layout.addWidget(hint)

        layout.addStretch()
        page.hide()
        return page

    def _build_app_page(self) -> QWidget:
        page = QWidget(self)
        page.setObjectName("appname")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        label = QLabel("目标应用进程名：")
        label.setFont(QFont("微软雅黑", 11))
        label.setStyleSheet("color: #333; background: transparent;")
        layout.addWidget(label)

        app_input = QLineEdit()
        app_input.setObjectName("app_input")
        app_input.setPlaceholderText("输入进程名，如 msedge.exe")
        app_input.setFont(QFont("微软雅黑", 10))
        app_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd; border-radius: 4px; padding: 5px 10px;
                color: #333; background: #fff;
            }
            QLineEdit:focus { border-color: #fb7299; }
        """)
        layout.addWidget(app_input)
        app_input.textChanged.connect(self._sync_appname_to_memory)

        # 常用浏览器快捷按钮
        quick_label = QLabel("常用浏览器（点击选择）：")
        quick_label.setFont(QFont("微软雅黑", 10))
        quick_label.setStyleSheet("color: #888; background: transparent;")
        layout.addWidget(quick_label)

        grid = QGridLayout()
        grid.setSpacing(5)
        browsers = [
            ("Edge", "msedge.exe"), ("Chrome", "chrome.exe"),
            ("Firefox", "firefox.exe"), ("Brave", "brave.exe"),
            ("Opera", "opera.exe"),
        ]
        for i, (disp, exe) in enumerate(browsers):
            btn = QPushButton(disp)
            btn.setFont(QFont("微软雅黑", 9))
            btn.setStyleSheet("""
                QPushButton {
                    background: #fff; border: 1px solid #ddd; border-radius: 4px;
                    color: #333; padding: 4px 12px;
                }
                QPushButton:hover { border-color: #fb7299; background: #fff0f4; }
            """)
            btn.clicked.connect(lambda checked, e=exe: app_input.setText(e))
            grid.addWidget(btn, i // 3, i % 3)
        layout.addLayout(grid)

        # 扫描已安装应用
        scan_label = QLabel("已安装应用（点击选择）：")
        scan_label.setFont(QFont("微软雅黑", 10))
        scan_label.setStyleSheet("color: #888; background: transparent;")
        layout.addWidget(scan_label)

        self._app_list = QListWidget()
        self._app_list.setFont(QFont("微软雅黑", 9))
        self._app_list.setMaximumHeight(160)
        self._app_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #eee; border-radius: 4px; color: #333;
                background: #fafafa;
            }
            QListWidget::item:hover { background: #fff0f4; }
            QListWidget::item:selected { background: #fb7299; color: #fff; }
        """)
        self._app_list.itemClicked.connect(
            lambda item: app_input.setText(item.data(Qt.UserRole))
        )
        self._scan_installed_apps()
        layout.addWidget(self._app_list)

        layout.addStretch()
        page.hide()
        return page

    def _build_personal_page(self) -> QWidget:
        page = QWidget(self)
        page.setObjectName("personal")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        title = QLabel("个性化设置")
        title.setFont(QFont("微软雅黑", 13, QFont.Bold))
        title.setStyleSheet("color: #fb7299; background: transparent;")
        layout.addWidget(title)

        auto_cb = QCheckBox("隐藏窗口时自动暂停媒体播放")
        auto_cb.setObjectName("auto_pause")
        auto_cb.setFont(QFont("微软雅黑", 11))
        auto_cb.setStyleSheet("color: #333; background: transparent; spacing: 8px;")
        auto_cb.setChecked(True)
        layout.addWidget(auto_cb)
        auto_cb.stateChanged.connect(self._sync_autopause_to_memory)

        layout.addStretch()
        page.hide()
        return page

    # ── 已安装应用扫描 ──────────────────────────────────────────

    def _scan_installed_apps(self) -> None:
        """扫描注册表中的已安装应用，填入列表"""
        seen: set[str] = set()
        # 先加入常用浏览器
        presets = [
            ("Microsoft Edge", "msedge.exe"),
            ("Google Chrome", "chrome.exe"),
            ("Mozilla Firefox", "firefox.exe"),
        ]
        for disp, exe in presets:
            if exe not in seen:
                seen.add(exe)
                item = QListWidgetItem(disp)
                item.setData(Qt.UserRole, exe)
                self._app_list.addItem(item)

        # 扫描注册表
        reg_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ]
        for reg_path in reg_paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        sub_name = winreg.EnumKey(key, i)
                        sub_key = winreg.OpenKey(key, sub_name)
                        try:
                            disp, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                        except OSError:
                            disp = ""
                        try:
                            exe_path, _ = winreg.QueryValueEx(sub_key, "DisplayIcon")
                            if exe_path and exe_path.lower().endswith(".exe"):
                                exe_name = Path(exe_path).name.lower()
                                if exe_name not in seen and disp:
                                    seen.add(exe_name)
                                    item = QListWidgetItem(disp)
                                    item.setData(Qt.UserRole, exe_name)
                                    self._app_list.addItem(item)
                                    if self._app_list.count() >= 50:
                                        break
                        except OSError:
                            pass
                        winreg.CloseKey(sub_key)
                    except OSError:
                        pass
                winreg.CloseKey(key)
            except OSError:
                pass

        # 扫描 HKCU
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    sub_name = winreg.EnumKey(key, i)
                    sub_key = winreg.OpenKey(key, sub_name)
                    try:
                        disp, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                    except OSError:
                        disp = ""
                    try:
                        exe_path, _ = winreg.QueryValueEx(sub_key, "DisplayIcon")
                        if exe_path and exe_path.lower().endswith(".exe"):
                            exe_name = Path(exe_path).name.lower()
                            if exe_name not in seen and disp:
                                seen.add(exe_name)
                                item = QListWidgetItem(disp)
                                item.setData(Qt.UserRole, exe_name)
                                self._app_list.addItem(item)
                                if self._app_list.count() >= 80:
                                    break
                    except OSError:
                        pass
                    winreg.CloseKey(sub_key)
                except OSError:
                    pass
            winreg.CloseKey(key)
        except OSError:
            pass
