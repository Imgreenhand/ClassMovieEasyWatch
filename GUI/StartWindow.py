"""开始窗口：选择触发方式与配置档案，然后启动监听。

窗口整体为圆角卡片：左侧插画区，右侧为标题、表单与开始按钮。
所有图标来自矢量素材，不使用字符表情。
"""

from __future__ import annotations

import json

from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QComboBox, QFrame,
    QVBoxLayout, QHBoxLayout,
)

from GUI import theme
from infrastructure.path_utils import get_data_dir, resource_path

SAVE_DIR = get_data_dir()
SAVE_FILE = SAVE_DIR / "save.txt"

WINDOW_W = 800
WINDOW_H = 352
ILLUSTRATION_W = 292


class _FieldRow(QFrame):
    """一行表单：左侧图标 + 标题，下方下拉框"""

    def __init__(self, icon_name: str, title: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(6)

        icon_label = QLabel()
        icon_label.setPixmap(theme.icon_pixmap(icon_name, 15, theme.PINK))
        icon_label.setFixedSize(15, 15)
        icon_label.setStyleSheet("background: transparent; border: none;")
        head.addWidget(icon_label)

        text_label = QLabel(title)
        text_label.setFont(QFont(theme.FONT_FAMILY, 10))
        text_label.setStyleSheet(f"color: {theme.TEXT_SUB}; background: transparent; border: none;")
        head.addWidget(text_label)
        head.addStretch()

        layout.addLayout(head)

        self.combo = QComboBox()
        self.combo.setFont(QFont(theme.FONT_FAMILY, 10))
        self.combo.setFixedHeight(38)
        self.combo.setCursor(Qt.PointingHandCursor)
        self.combo.setStyleSheet(theme.combo_qss(height=36))
        layout.addWidget(self.combo)


class StartWindow(QWidget):
    """开始窗口：选择本次运行的配置后点击开始"""

    def __init__(self, on_start=None, on_close=None):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("ClassMovieEasyWatch")
        self.setFixedSize(WINDOW_W, WINDOW_H)

        self._on_start = on_start
        self._on_close = on_close
        self._drag_pos: QPoint | None = None
        self._started = False

        self._setup_ui()
        self._refresh_profiles()
        self._load_current_save()
        self._update_hint()

    # ══════════════════════════════════════════════════════
    # 界面
    # ══════════════════════════════════════════════════════

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        margin = theme.CARD_MARGIN
        outer.setContentsMargins(margin, margin, margin, margin)
        outer.setSpacing(0)

        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(theme.card_qss(theme.RADIUS_CARD))
        theme.add_shadow(card, blur=44, dy=10, alpha=46)
        outer.addWidget(card)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        card_layout.addWidget(self._build_illustration())
        card_layout.addWidget(self._build_form(), 1)

    def _build_illustration(self) -> QWidget:
        """左侧插画区：浅粉渐变底 + 2233 形象（白底图片做成圆角小卡）"""
        panel = QFrame()
        panel.setObjectName("illustration")
        panel.setFixedWidth(ILLUSTRATION_W)
        panel.setStyleSheet(
            f"""
            QFrame#illustration {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 {theme.PINK_SOFT}, stop:1 #ffe6ef);
                border: none;
                border-top-left-radius: {theme.RADIUS_CARD}px;
                border-bottom-left-radius: {theme.RADIUS_CARD}px;
            }}
            """
        )

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 22, 20, 22)
        layout.setSpacing(0)

        art_card = QFrame()
        art_card.setObjectName("artCard")
        art_card.setStyleSheet(
            f"QFrame#artCard {{ background: {theme.BG};"
            f" border: 1px solid #ffe3ec; border-radius: 14px; }}"
        )
        theme.add_shadow(art_card, blur=20, dy=4, alpha=30)

        art_layout = QVBoxLayout(art_card)
        art_layout.setContentsMargins(10, 10, 10, 10)

        art = QLabel()
        art.setAlignment(Qt.AlignCenter)
        art.setStyleSheet("background: transparent; border: none;")
        pix = QPixmap(resource_path("GUI/Art/2233Start.png"))
        if not pix.isNull():
            art.setPixmap(
                pix.scaled(
                    ILLUSTRATION_W - 60, WINDOW_H - 130,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation,
                )
            )
        art_layout.addWidget(art)

        layout.addWidget(art_card, 0, Qt.AlignCenter)
        layout.insertStretch(0, 1)
        layout.addStretch(1)
        return panel

    def _build_form(self) -> QWidget:
        """右侧表单区：标题、两个下拉框、开始按钮"""
        panel = QWidget()
        panel.setStyleSheet("background: transparent; border: none;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 20, 22, 22)
        layout.setSpacing(0)

        # ── 标题行 ──
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(3)

        title = QLabel("ClassMovieEasyWatch")
        title.setFont(QFont(theme.FONT_FAMILY, 14, QFont.Bold))
        title.setStyleSheet(f"color: {theme.TEXT}; background: transparent; border: none;")
        title_box.addWidget(title)

        subtitle = QLabel("课堂观影，一键隐藏与还原")
        subtitle.setFont(QFont(theme.FONT_FAMILY, 9))
        subtitle.setStyleSheet(
            f"color: {theme.TEXT_SUB}; background: transparent; border: none;"
        )
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self._btn_close = QPushButton()
        self._btn_close.setIcon(theme.icon("close", 16, theme.TEXT_SUB))
        self._btn_close.setIconSize(QSize(16, 16))
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.setStyleSheet(theme.ghost_button_qss(30))
        self._btn_close.setToolTip("关闭")
        self._btn_close.clicked.connect(self.close)
        header.addWidget(self._btn_close, 0, Qt.AlignTop)

        layout.addLayout(header)
        layout.addSpacing(18)

        # ── 表单字段 ──
        self._way_field = _FieldRow("toggle", "触发方式")
        self._way_field.combo.addItem("快捷键", "hotkey")
        self._way_field.combo.addItem("鼠标控制", "button")
        self._way_field.combo.currentIndexChanged.connect(self._update_hint)
        layout.addWidget(self._way_field)

        layout.addSpacing(12)

        self._profile_field = _FieldRow("profile", "配置档案")
        layout.addWidget(self._profile_field)

        layout.addStretch()

        # ── 底部操作 ──
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(16)

        self._hint = QLabel()
        self._hint.setFont(QFont(theme.FONT_FAMILY, 9))
        self._hint.setStyleSheet(
            f"color: {theme.TEXT_SUB}; background: transparent; border: none;"
        )
        footer.addWidget(self._hint, 1)

        self._start_btn = QPushButton("开始")
        self._start_btn.setIcon(theme.icon("start", 18, "#ffffff"))
        self._start_btn.setIconSize(QSize(18, 18))
        self._start_btn.setFont(QFont(theme.FONT_FAMILY, 11, QFont.Bold))
        self._start_btn.setFixedSize(132, 44)
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.setStyleSheet(theme.primary_button_qss(height=44, font_size=11))
        self._start_btn.setDefault(True)
        self._start_btn.clicked.connect(self._on_start_clicked)
        footer.addWidget(self._start_btn, 0, Qt.AlignVCenter)

        layout.addLayout(footer)
        return panel

    @property
    def _way_combo(self) -> QComboBox:
        return self._way_field.combo

    @property
    def _profile_combo(self) -> QComboBox:
        return self._profile_field.combo

    # ══════════════════════════════════════════════════════
    # 数据
    # ══════════════════════════════════════════════════════

    def _refresh_profiles(self) -> None:
        """扫描 SaveData/*.json 填充配置下拉栏"""
        self._profile_combo.blockSignals(True)
        self._profile_combo.clear()
        if SAVE_DIR.exists():
            for f in sorted(SAVE_DIR.glob("*.json")):
                if f.stem == "save":
                    continue
                self._profile_combo.addItem(f.stem)
        if self._profile_combo.count() == 0:
            self._profile_combo.addItem("default")
        self._profile_combo.blockSignals(False)

    def _load_current_save(self) -> None:
        """读取 save.txt 预填下拉栏"""
        data: dict = {}
        if SAVE_FILE.exists():
            try:
                data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

        way = data.get("way", "hotkey")
        idx = self._way_combo.findData(way)
        if idx >= 0:
            self._way_combo.setCurrentIndex(idx)

        profile = data.get("save_file", "default")
        idx = self._profile_combo.findText(profile)
        if idx >= 0:
            self._profile_combo.setCurrentIndex(idx)

    def _update_hint(self) -> None:
        """根据触发方式与配置档案显示底部提示"""
        if not hasattr(self, "_hint"):
            return
        if self._way_combo.currentData() == "button":
            self._hint.setText("热区模式：点击屏幕右下角热区即可隐藏与还原")
            return

        hide_key = self._profile_hotkey("hotkey_hide", "")
        restore_key = self._profile_hotkey("hotkey_restore", "")
        if hide_key and restore_key:
            self._hint.setText(f"{hide_key} 隐藏  ·  {restore_key} 还原")
        else:
            self._hint.setText("启动后监听在后台运行，可从系统托盘结束")

    def _profile_hotkey(self, field: str, fallback: str) -> str:
        """读取当前配置档案的热键并转成易读形式"""
        name = self._profile_combo.currentText()
        path = SAVE_DIR / f"{name}.json"
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return fallback
        return _pretty_hotkey(str(raw.get(field, ""))) or fallback

    def _on_start_clicked(self) -> None:
        """保存选择到 save.txt，关闭窗口，触发回调"""
        way = self._way_combo.currentData()
        profile = self._profile_combo.currentText()

        data = {"way": way, "save_file": profile}
        try:
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            SAVE_FILE.write_text(
                json.dumps(data, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass

        self._started = True
        callback = self._on_start
        self.close()
        if callback:
            callback()

    # ══════════════════════════════════════════════════════
    # 窗口事件
    # ══════════════════════════════════════════════════════

    def closeEvent(self, event):
        """用户直接关闭窗口时通知外层取消阻塞等待"""
        if not self._started and self._on_close:
            callback = self._on_close
            self._started = True
            callback()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._on_start_clicked()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


def _pretty_hotkey(raw: str) -> str:
    """把 '<ctrl>+<alt>+q' 转成 'Ctrl+Alt+Q' 便于阅读"""
    if not raw:
        return ""
    names = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift", "cmd": "Win"}
    parts: list[str] = []
    for chunk in raw.split("+"):
        chunk = chunk.strip()
        if not chunk:
            continue
        key = chunk[1:-1] if chunk.startswith("<") and chunk.endswith(">") else chunk
        if key.lower() in names:
            parts.append(names[key.lower()])
        elif len(key) == 1:
            parts.append(key.upper())
        else:
            parts.append(key.replace("_", " ").title())
    return "+".join(parts)
