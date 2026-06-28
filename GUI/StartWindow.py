import json
from pathlib import Path
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QWidget, QApplication, QPushButton, QLabel,
    QComboBox, QFrame, QVBoxLayout, QHBoxLayout,
)

SAVE_DIR = Path("SaveData")
SAVE_FILE = SAVE_DIR / "save.json"

BTN_STYLE = """
    QPushButton {
        background: #ffffff; border: 1px solid #fb7299;
        border-radius: 4px; color: #fb7299; padding: 6px 20px;
    }
    QPushButton:hover { background: #fff0f4; }
    QPushButton:pressed { background: #ffe0ea; }
"""

START_BTN_STYLE = """
    QPushButton {
        background: #fb7299; color: #ffffff; border: none;
        border-radius: 6px; font-weight: bold; padding: 8px 28px;
    }
    QPushButton:hover { background: #e55a80; }
    QPushButton:pressed { background: #cc4d70; }
"""


class StartWindow(QWidget):
    """开始窗口：选择本次运行的配置后点击开始"""

    def __init__(self, on_start=None):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: #ffffff;")
        self.setFixedSize(650, 260)

        self._on_start = on_start
        self._drag_pos: QPoint | None = None

        self._setup_ui()
        self._load_current_save()

    def _setup_ui(self) -> None:
        # 外层水平布局
        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(16, 16, 16, 16)
        h_layout.setSpacing(0)

        # ── 左侧图片 ──
        pix = QPixmap("GUI/Art/2233Start.png")
        self._image_label = QLabel()
        if not pix.isNull():
            self._image_label.setPixmap(pix.scaledToHeight(200, Qt.SmoothTransformation))
        self._image_label.setStyleSheet("background: transparent;")
        self._image_label.setFixedWidth(220)
        h_layout.addWidget(self._image_label)

        h_layout.addSpacing(20)

        # ── 中间下拉栏区域 ──
        mid_widget = QFrame()
        mid_widget.setStyleSheet("background: transparent; border: none;")
        mid_layout = QVBoxLayout(mid_widget)
        mid_layout.setContentsMargins(0, 30, 0, 30)
        mid_layout.setSpacing(18)

        # 触发方式
        way_label = QLabel("触发方式")
        way_label.setFont(QFont("微软雅黑", 11))
        way_label.setStyleSheet("color: #333; background: transparent;")
        mid_layout.addWidget(way_label)

        self._way_combo = QComboBox()
        self._way_combo.addItem("快捷键", "hotkey")
        self._way_combo.addItem("浮动按钮", "button")
        self._way_combo.setFont(QFont("微软雅黑", 10))
        self._way_combo.setFixedWidth(180)
        self._way_combo.setStyleSheet("""
            QComboBox {
                background: #ffffff; color: #333; border: 1px solid #ddd;
                border-radius: 4px; padding: 5px 10px;
            }
            QComboBox:hover { border-color: #fb7299; }
            QComboBox QAbstractItemView {
                background: #ffffff; color: #333; selection-background-color: #fff0f4;
                outline: none;
            }
        """)
        mid_layout.addWidget(self._way_combo)

        # 配置档案
        profile_label = QLabel("配置档案")
        profile_label.setFont(QFont("微软雅黑", 11))
        profile_label.setStyleSheet("color: #333; background: transparent;")
        mid_layout.addWidget(profile_label)

        self._profile_combo = QComboBox()
        self._profile_combo.setFont(QFont("微软雅黑", 10))
        self._profile_combo.setFixedWidth(180)
        self._profile_combo.setStyleSheet(self._way_combo.styleSheet())
        mid_layout.addWidget(self._profile_combo)

        h_layout.addWidget(mid_widget)

        h_layout.addStretch()

        # ── 右侧开始按钮 ──
        btn_area = QFrame()
        btn_area.setStyleSheet("background: transparent; border: none;")
        btn_v = QVBoxLayout(btn_area)
        btn_v.setContentsMargins(0, 60, 10, 60)
        btn_v.setAlignment(Qt.AlignCenter)

        self._start_btn = QPushButton("开始")
        self._start_btn.setFont(QFont("微软雅黑", 14, QFont.Bold))
        self._start_btn.setStyleSheet(START_BTN_STYLE)
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.clicked.connect(self._on_start_clicked)
        self._start_btn.adjustSize()
        btn_v.addWidget(self._start_btn)

        h_layout.addWidget(btn_area)

        self._refresh_profiles()

    def _refresh_profiles(self) -> None:
        """扫描 SaveData/*.json 填充配置下拉栏"""
        self._profile_combo.clear()
        if SAVE_DIR.exists():
            for f in sorted(SAVE_DIR.glob("*.json")):
                if f.stem == "save":
                    continue
                self._profile_combo.addItem(f.stem)
        if self._profile_combo.count() == 0:
            self._profile_combo.addItem("default")

    def _load_current_save(self) -> None:
        """读取 save.json 预填下拉栏"""
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

    def _on_start_clicked(self) -> None:
        """保存选择到 save.json，关闭窗口，触发回调"""
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

        callback = self._on_start
        self.close()
        if callback:
            callback()

    # ── 窗口拖动 ──

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
