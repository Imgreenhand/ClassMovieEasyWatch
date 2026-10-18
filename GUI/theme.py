"""GUI 主题层：色板、字体、矢量图标与统一控件样式。

设计要点
--------
* 图标全部来自 ``GUI/Art/icons``（Material Symbols 单色 SVG），
  运行时按需要着色生成，避免为每种颜色维护多份文件；
* 颜色、圆角、字号集中在此处定义，各窗口只引用语义化常量；
* 样式表统一由本模块拼装，避免各窗口散落着不一致的 QSS 副本。
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QColor, QGuiApplication, QIcon, QImage, QPainter, QPixmap,
)
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget
from PySide6.QtSvg import QSvgRenderer

from infrastructure.path_utils import resource_path

# ══════════════════════════════════════════════════════════
# 设计令牌
# ══════════════════════════════════════════════════════════

PINK = "#fb7299"          # 主色
PINK_DARK = "#e9638b"     # 悬停
PINK_DEEP = "#d8557b"     # 按下
PINK_LIGHT = "#fff0f4"    # 浅色填充
PINK_SOFT = "#fff7fa"     # 极浅底色
PINK_EDGE = "#ffe0ea"     # 浅色描边

TEXT = "#2f2a2e"          # 正文
TEXT_SUB = "#8b8086"      # 次要文本
TEXT_MUTED = "#b6abb1"    # 弱化文本
TEXT_INVERT = "#ffffff"

BG = "#ffffff"            # 内容底色
BG_SIDEBAR = "#fcf7f9"    # 侧栏底色
BORDER = "#f0e4e9"        # 常规描边
BORDER_STRONG = "#e6d5dc"

FONT_FAMILY = "微软雅黑"
RADIUS = 8
RADIUS_CARD = 14
CARD_MARGIN = 10          # 窗口圆角卡片四周留白（用于投影）

ICON_DIR = Path(resource_path("GUI/Art/icons"))

# ══════════════════════════════════════════════════════════
# 矢量图标
# ══════════════════════════════════════════════════════════

_pixmap_cache: dict[tuple[str, int, str], QPixmap] = {}
_svg_cache: dict[tuple[str, str], str] = {}
_generated_dir: Path | None = None


def _icon_source(name: str) -> Path:
    """返回图标源文件路径，缺失时给出可读错误"""
    path = ICON_DIR / f"{name}.svg"
    if not path.exists():
        raise FileNotFoundError(f"缺少图标资源: {path}")
    return path


def _device_ratio() -> float:
    """当前主屏的像素比，用于生成清晰的高分屏图标"""
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return 1.0
    return max(1.0, float(screen.devicePixelRatio()))


def icon_pixmap(name: str, size: int = 18, color: str = PINK) -> QPixmap:
    """把单色 SVG 渲染成指定尺寸、指定颜色的 QPixmap（带缓存）"""
    key = (name, size, color.lower())
    cached = _pixmap_cache.get(key)
    if cached is not None:
        return cached

    renderer = QSvgRenderer(str(_icon_source(name)))
    ratio = _device_ratio()
    side = max(1, int(round(size * ratio)))
    image = QImage(side, side, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter, QRectF(0, 0, side, side))
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(image.rect(), QColor(color))
    painter.end()

    pixmap = QPixmap.fromImage(image)
    pixmap.setDevicePixelRatio(ratio)
    _pixmap_cache[key] = pixmap
    return pixmap


def icon(name: str, size: int = 18, color: str = PINK) -> QIcon:
    """把单色 SVG 渲染成可着色的 QIcon"""
    return QIcon(icon_pixmap(name, size, color))


def svg_url(name: str, color: str) -> str:
    """生成指定颜色的 SVG 副本并返回 QSS 可用的正斜杠路径。

    Qt 的样式表 ``image: url(...)`` 不会对 SVG 重新着色，
    因此按颜色把图标写到临时目录后引用绝对路径。
    """
    global _generated_dir
    key = (name, color.lower())
    cached = _svg_cache.get(key)
    if cached is not None:
        return cached

    if _generated_dir is None:
        _generated_dir = Path(tempfile.gettempdir()) / "ClassMovieEasyWatch" / "icons"
        _generated_dir.mkdir(parents=True, exist_ok=True)

    text = _icon_source(name).read_text(encoding="utf-8")
    # 只替换十六进制颜色，保留 fill="none" 之类的声明
    text = re.sub(r'fill="#[0-9a-fA-F]{3,8}"', f'fill="{color}"', text)
    text = re.sub(r"(fill:\s*)#[0-9a-fA-F]{3,8}", rf"\1{color}", text)

    target = _generated_dir / f"{name}-{color.lstrip('#').lower()}.svg"
    target.write_text(text, encoding="utf-8")

    url = target.as_posix()
    _svg_cache[key] = url
    return url


# ══════════════════════════════════════════════════════════
# 投影
# ══════════════════════════════════════════════════════════

def add_shadow(widget: QWidget, blur: int = 40, dy: int = 8, alpha: int = 44) -> None:
    """给卡片添加柔和投影，配合透明窗口形成圆角悬浮效果"""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, dy)
    effect.setColor(QColor(146, 96, 118, alpha))
    widget.setGraphicsEffect(effect)


# ══════════════════════════════════════════════════════════
# 卡片 / 容器
# ══════════════════════════════════════════════════════════

def card_qss(radius: int = RADIUS_CARD) -> str:
    return (
        f"QFrame#card {{ background: {BG}; border: 1px solid {BORDER};"
        f" border-radius: {radius}px; }}"
    )


def topbar_qss(radius: int = RADIUS_CARD) -> str:
    return (
        f"QFrame#topbar {{ background: {BG}; border: none;"
        f" border-top-left-radius: {radius}px; border-top-right-radius: {radius}px;"
        f" border-bottom: 1px solid {BORDER}; }}"
    )


def sidebar_qss(radius: int = RADIUS_CARD) -> str:
    return (
        f"QFrame#sidebar {{ background: {BG_SIDEBAR}; border: none;"
        f" border-bottom-left-radius: {radius}px; }}"
    )


# ══════════════════════════════════════════════════════════
# 按钮
# ══════════════════════════════════════════════════════════

def primary_button_qss(height: int = 38, radius: int = RADIUS, font_size: int = 10) -> str:
    return f"""
        QPushButton {{
            background: {PINK};
            color: {TEXT_INVERT};
            border: none;
            border-radius: {radius}px;
            padding: 0 20px;
            min-height: {height}px;
            font-size: {font_size}pt;
            font-weight: bold;
        }}
        QPushButton:hover {{ background: {PINK_DARK}; }}
        QPushButton:pressed {{ background: {PINK_DEEP}; }}
        QPushButton:disabled {{ background: {PINK_EDGE}; color: {TEXT_INVERT}; }}
    """


def secondary_button_qss(height: int = 30, radius: int = RADIUS, font_size: int = 9) -> str:
    return f"""
        QPushButton {{
            background: {BG};
            color: {PINK};
            border: 1px solid {PINK_EDGE};
            border-radius: {radius}px;
            padding: 0 14px;
            min-height: {height}px;
            font-size: {font_size}pt;
        }}
        QPushButton:hover {{ background: {PINK_LIGHT}; border-color: {PINK}; }}
        QPushButton:pressed {{ background: {PINK_EDGE}; }}
        QPushButton:disabled {{ color: {TEXT_MUTED}; border-color: {BORDER}; }}
    """


def chip_button_qss(height: int = 28, font_size: int = 9) -> str:
    """小号胶囊按钮：用于快捷选项"""
    return f"""
        QPushButton {{
            background: {BG_SIDEBAR};
            color: {TEXT_SUB};
            border: 1px solid {BORDER};
            border-radius: {height // 2}px;
            padding: 0 14px;
            min-height: {height}px;
            font-size: {font_size}pt;
        }}
        QPushButton:hover {{
            background: {PINK_LIGHT};
            border-color: {PINK};
            color: {PINK};
        }}
        QPushButton:pressed {{ background: {PINK_EDGE}; color: {PINK_DEEP}; }}
    """


def ghost_button_qss(size: int = 30, radius: int = RADIUS) -> str:
    """无边框图标按钮：用于关闭等窗口操作"""
    return f"""
        QPushButton {{
            background: transparent;
            border: none;
            border-radius: {radius}px;
            min-width: {size}px;
            min-height: {size}px;
            max-width: {size}px;
            max-height: {size}px;
        }}
        QPushButton:hover {{ background: {PINK_LIGHT}; }}
        QPushButton:pressed {{ background: {PINK_EDGE}; }}
    """


# ══════════════════════════════════════════════════════════
# 输入控件
# ══════════════════════════════════════════════════════════

def combo_qss(height: int = 30, radius: int = RADIUS, arrow: str = "drop-down-pink") -> str:
    arrow_pink = svg_url(arrow, "#fb7299")
    return f"""
        QComboBox {{
            background: {BG};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: {radius}px;
            padding: 0 8px 0 12px;
            min-height: {height}px;
        }}
        QComboBox:hover {{ border-color: {PINK}; }}
        QComboBox:focus {{ border-color: {PINK}; }}
        QComboBox:on {{ border-color: {PINK}; background: {PINK_SOFT}; }}
        QComboBox::drop-down {{
            border: none;
            width: 26px;
        }}
        QComboBox::down-arrow {{
            image: url("{arrow_pink}");
            width: 14px;
            height: 14px;
        }}
        QComboBox QAbstractItemView {{
            background: {BG};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: {radius}px;
            padding: 4px;
            outline: none;
            selection-background-color: {PINK_LIGHT};
            selection-color: {PINK};
        }}
    """


def line_edit_qss(height: int = 34, radius: int = RADIUS) -> str:
    return f"""
        QLineEdit {{
            background: {BG};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: {radius}px;
            padding: 0 12px;
            min-height: {height}px;
            selection-background-color: {PINK_LIGHT};
            selection-color: {PINK};
        }}
        QLineEdit:hover {{ border-color: {BORDER_STRONG}; }}
        QLineEdit:focus {{ border-color: {PINK}; }}
    """


def spin_qss(height: int = 30, radius: int = RADIUS) -> str:
    up = svg_url("caret_up", PINK)
    down = svg_url("arrow_down", PINK)
    return f"""
        QSpinBox {{
            background: {BG};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: {radius}px;
            padding: 0 8px 0 12px;
            min-height: {height}px;
        }}
        QSpinBox:hover {{ border-color: {PINK}; }}
        QSpinBox:focus {{ border-color: {PINK}; }}
        QSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 22px;
            border: none;
            background: transparent;
        }}
        QSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 22px;
            border: none;
            background: transparent;
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {PINK_LIGHT}; }}
        QSpinBox::up-arrow {{ image: url("{up}"); width: 9px; height: 9px; }}
        QSpinBox::down-arrow {{ image: url("{down}"); width: 9px; height: 9px; }}
    """


def checkbox_qss(font_size: int = 10) -> str:
    tick = svg_url("check", "#ffffff")
    return f"""
        QCheckBox {{
            color: {TEXT};
            spacing: 10px;
            font-size: {font_size}pt;
            background: transparent;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {BORDER_STRONG};
            border-radius: 5px;
            background: {BG};
        }}
        QCheckBox::indicator:hover {{ border-color: {PINK}; }}
        QCheckBox::indicator:checked {{
            background: {PINK};
            border-color: {PINK};
            image: url("{tick}");
        }}
    """


def list_qss(radius: int = RADIUS) -> str:
    return f"""
        QListWidget {{
            background: {BG};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: {radius}px;
            padding: 4px;
            outline: none;
        }}
        QListWidget::item {{
            border-radius: 6px;
            padding: 6px 8px;
            margin: 1px 0;
        }}
        QListWidget::item:hover {{ background: {PINK_LIGHT}; color: {PINK_DEEP}; }}
        QListWidget::item:selected {{ background: {PINK}; color: {TEXT_INVERT}; }}
    """


def scroll_qss() -> str:
    return f"""
        QScrollArea {{ background: transparent; border: none; }}
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 4px 2px 4px 0;
        }}
        QScrollBar::handle:vertical {{
            background: {BORDER_STRONG};
            border-radius: 3px;
            min-height: 36px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {PINK}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        QScrollBar:horizontal {{ height: 0; }}
    """


def menu_qss() -> str:
    return f"""
        QMenu {{
            background: {BG};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 6px;
        }}
        QMenu::item {{
            padding: 8px 26px 8px 10px;
            border-radius: 6px;
            font-size: 10pt;
            min-width: 150px;
        }}
        QMenu::item:selected {{ background: {PINK_LIGHT}; color: {PINK_DEEP}; }}
        QMenu::icon {{ padding-left: 8px; }}
        QMenu::separator {{
            height: 1px;
            background: {BORDER};
            margin: 5px 10px;
        }}
    """


def tooltip_qss() -> str:
    return f"""
        QToolTip {{
            background: {BG};
            color: {TEXT};
            border: 1px solid {PINK_EDGE};
            border-radius: 6px;
            padding: 5px 9px;
            font-size: 9pt;
        }}
    """


def dialog_qss() -> str:
    """原生消息框/输入框的统一样式（应用级）"""
    return f"""
        QMessageBox, QInputDialog {{ background: {BG}; }}
        QMessageBox QLabel, QInputDialog QLabel {{
            color: {TEXT};
            font-size: 10pt;
            background: transparent;
        }}
        QMessageBox QPushButton, QInputDialog QPushButton {{
            background: {BG};
            color: {PINK};
            border: 1px solid {PINK_EDGE};
            border-radius: 6px;
            padding: 5px 18px;
            min-width: 62px;
            min-height: 24px;
        }}
        QMessageBox QPushButton:hover, QInputDialog QPushButton:hover {{
            background: {PINK_LIGHT};
            border-color: {PINK};
        }}
        QMessageBox QPushButton:pressed, QInputDialog QPushButton:pressed {{
            background: {PINK_EDGE};
        }}
        QInputDialog QLineEdit {{
            background: {BG};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 5px 10px;
            min-height: 24px;
        }}
        QInputDialog QLineEdit:focus {{ border-color: {PINK}; }}
    """


def section_title_qss(size: int = 11) -> str:
    return (
        f"color: {TEXT}; background: transparent; border: none;"
        f" font-size: {size}pt; font-weight: bold;"
    )


def hint_qss(size: int = 9) -> str:
    return f"color: {TEXT_MUTED}; background: transparent; border: none; font-size: {size}pt;"


def body_qss(size: int = 10) -> str:
    return f"color: {TEXT_SUB}; background: transparent; border: none; font-size: {size}pt;"
