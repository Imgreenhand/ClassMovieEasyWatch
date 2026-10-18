"""关于窗口：左侧章节导航 + 右侧 Markdown 内容，风格与设置窗口一致。"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFrame,
    QVBoxLayout, QHBoxLayout, QTextBrowser,
)

from GUI import theme
from GUI.widgets import NavItem
from infrastructure.path_utils import resource_path
from infrastructure.version import APP_VERSION

CHAPTERS = [
    ("项目简介", "intro", "home"),
    ("功能说明", "features", "star"),
    ("使用方法", "usage", "guide"),
    ("开发相关", "dev", "dev"),
    ("版本管理", "versions", "version"),
]

ABOUT_DIR = Path(__file__).parent.parent / "About"

TOPBAR_H = 58
SIDEBAR_W = 168


class AboutWindow(QWidget):
    """关于窗口：侧边栏章节导航 + 右侧 Markdown 内容"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("关于 ClassMovieEasyWatch")
        self.resize(780, 580)
        self.setMinimumSize(620, 420)

        self._drag_pos: QPoint | None = None
        self._sidebar_items: dict[str, NavItem] = {}
        self._md_cache: dict[str, str] = {}

        self._setup_card()
        self._setup_topbar()
        self._setup_sidebar()
        self._setup_content()

        # 默认选中第一章
        self._on_chapter_click(CHAPTERS[0][1])

    # ═══════════════════════════════════════
    # 圆角卡片
    # ═══════════════════════════════════════

    def _setup_card(self) -> None:
        margin = theme.CARD_MARGIN
        self._card = QFrame(self)
        self._card.setObjectName("card")
        self._card.setStyleSheet(theme.card_qss(theme.RADIUS_CARD))
        theme.add_shadow(self._card, blur=48, dy=10, alpha=46)
        self._card.setGeometry(
            margin, margin,
            self.width() - margin * 2, self.height() - margin * 2,
        )

    # ═══════════════════════════════════════
    # 顶栏
    # ═══════════════════════════════════════

    def _setup_topbar(self) -> None:
        self._topbar = QFrame(self._card)
        self._topbar.setObjectName("topbar")
        self._topbar.setStyleSheet(theme.topbar_qss(theme.RADIUS_CARD))
        self._topbar.setFixedHeight(TOPBAR_H)

        layout = QHBoxLayout(self._topbar)
        layout.setContentsMargins(18, 0, 14, 0)
        layout.setSpacing(10)

        brand = QLabel()
        logo = QPixmap(resource_path("GUI/Art/Sign.svg"))
        if not logo.isNull():
            brand.setPixmap(logo.scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        brand.setFixedSize(26, 26)
        brand.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(brand)

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(1)

        title = QLabel("关于 ClassMovieEasyWatch")
        title.setFont(QFont(theme.FONT_FAMILY, 11, QFont.Bold))
        title.setStyleSheet(f"color: {theme.TEXT}; background: transparent; border: none;")
        title_box.addWidget(title)

        subtitle = QLabel("课堂观影一键隐藏与还原")
        subtitle.setFont(QFont(theme.FONT_FAMILY, 8))
        subtitle.setStyleSheet(
            f"color: {theme.TEXT_MUTED}; background: transparent; border: none;"
        )
        title_box.addWidget(subtitle)

        layout.addLayout(title_box)
        layout.addStretch()

        self._btn_close = QPushButton()
        self._btn_close.setIcon(theme.icon("close", 16, theme.TEXT_SUB))
        self._btn_close.setIconSize(QSize(16, 16))
        self._btn_close.setFixedSize(32, 32)
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.setStyleSheet(theme.ghost_button_qss(32))
        self._btn_close.setToolTip("关闭")
        self._btn_close.clicked.connect(self.close)
        layout.addWidget(self._btn_close)

        self._bar_h = TOPBAR_H

    # ═══════════════════════════════════════
    # 侧边栏
    # ═══════════════════════════════════════

    def _setup_sidebar(self) -> None:
        self._sidebar = QFrame(self._card)
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setStyleSheet(theme.sidebar_qss(theme.RADIUS_CARD))
        self._sidebar.setFixedWidth(SIDEBAR_W)

        layout = QVBoxLayout(self._sidebar)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(4)

        for text, key, icon_name in CHAPTERS:
            item = NavItem(key, text, icon_name, on_activated=self._on_nav_activated)
            layout.addWidget(item)
            self._sidebar_items[key] = item

        layout.addStretch()

        version = QLabel(f"v{APP_VERSION}")
        version.setFont(QFont(theme.FONT_FAMILY, 8))
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet(
            f"color: {theme.TEXT_MUTED}; background: transparent; border: none;"
        )
        layout.addWidget(version)

    # ═══════════════════════════════════════
    # 内容区
    # ═══════════════════════════════════════

    def _setup_content(self) -> None:
        self._browser = QTextBrowser(self._card)
        self._browser.setOpenExternalLinks(True)
        self._browser.setStyleSheet(
            f"""
            QTextBrowser {{
                background: {theme.BG};
                border: none;
                color: {theme.TEXT};
                padding: 10px 22px;
            }}
            """
            + theme.scroll_qss()
        )
        self._browser.setFont(QFont(theme.FONT_FAMILY, 10))
        self._browser.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    # ═══════════════════════════════════════
    # 章节切换
    # ═══════════════════════════════════════

    def _on_nav_activated(self, item: NavItem) -> None:
        self._on_chapter_click(item.key)

    def _on_chapter_click(self, key: str) -> None:
        for name, item in self._sidebar_items.items():
            item.set_selected(name == key)

        html = self._load_md(key)
        self._browser.setHtml(html)
        self._browser.verticalScrollBar().setValue(0)

    def _load_md(self, key: str) -> str:
        if key in self._md_cache:
            return self._md_cache[key]
        path = ABOUT_DIR / f"{key}.md"
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            logging.error("无法读取关于页面内容: %s", path)
            self._md_cache[key] = (
                f"<p style='color:{theme.TEXT_MUTED};'>内容加载失败</p>"
            )
            return self._md_cache[key]
        html = _md_to_html(raw)
        self._md_cache[key] = html
        return html

    # ═══════════════════════════════════════
    # 窗口事件
    # ═══════════════════════════════════════

    def resizeEvent(self, event):
        if not hasattr(self, "_card"):
            super().resizeEvent(event)
            return

        margin = theme.CARD_MARGIN
        card_w = self.width() - margin * 2
        card_h = self.height() - margin * 2

        self._card.setGeometry(margin, margin, card_w, card_h)
        self._topbar.setGeometry(0, 0, card_w, TOPBAR_H)
        self._sidebar.setGeometry(0, TOPBAR_H, SIDEBAR_W, card_h - TOPBAR_H)
        self._browser.setGeometry(
            SIDEBAR_W, TOPBAR_H, card_w - SIDEBAR_W, card_h - TOPBAR_H
        )
        super().resizeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# ═══════════════════════════════════════
# 简易 Markdown → HTML
# ═══════════════════════════════════════

def _md_to_html(md: str) -> str:
    """将简易 Markdown 转为 HTML，供 QTextBrowser 渲染"""
    lines = md.strip().split("\n")
    html_lines: list[str] = []
    in_code = False
    in_table = False
    table_rows: list[str] = []
    list_tag: str | None = None

    def close_list() -> None:
        """结束当前的 ul/ol 列表"""
        nonlocal list_tag
        if list_tag:
            html_lines.append(f"</{list_tag}>")
            list_tag = None

    for line in lines:
        # 代码块
        if line.startswith("```"):
            close_list()
            if in_code:
                html_lines.append("</div>")
                in_code = False
            else:
                html_lines.append(
                    '<div style="background:#f8f4f6; border-radius:6px; padding:10px;'
                    " font-family:Consolas,'Courier New',monospace; font-size:9pt;"
                    ' white-space:pre-wrap;">'
                )
                in_code = True
            continue
        if in_code:
            html_lines.append(_escape(line))
            continue

        # 表格
        if "|" in line and line.strip().startswith("|"):
            close_list()
            if not in_table:
                in_table = True
                table_rows = []
                html_lines.append(
                    '<table style="border-collapse:collapse; width:100%; margin:10px 0;">'
                )
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                # 分隔行，跳过
                continue
            tag = "th" if len(table_rows) == 0 else "td"
            row_html = "<tr>" + "".join(
                f'<{tag} style="border:1px solid {theme.BORDER}; padding:6px 10px; '
                f'text-align:left;">{_escape(c)}</{tag}>'
                for c in cells
            ) + "</tr>"
            table_rows.append(row_html)
            continue
        else:
            if in_table:
                html_lines.extend(table_rows)
                html_lines.append("</table>")
                in_table = False
                table_rows = []

        # 标题
        if line.startswith("### "):
            close_list()
            html_lines.append(
                f'<h4 style="color:{theme.TEXT_SUB}; margin:16px 0 6px 0;">'
                f'{_inline(line[4:])}</h4>')
            continue
        if line.startswith("## "):
            close_list()
            html_lines.append(
                f'<h3 style="color:{theme.PINK_DEEP}; margin:20px 0 8px 0; '
                f'border-bottom:1px solid {theme.PINK_EDGE}; padding-bottom:5px;">'
                f'{_inline(line[3:])}</h3>')
            continue
        if line.startswith("# "):
            close_list()
            html_lines.append(
                f'<h2 style="color:{theme.TEXT}; margin:8px 0 12px 0; font-size:16pt;">'
                f'{_inline(line[2:])}</h2>')
            continue

        # 无序列表 / 有序列表
        bullet = re.match(r"^- ", line)
        ordered = re.match(r"^\d+\.\s+(.*)$", line)
        if bullet or ordered:
            tag = "ul" if bullet else "ol"
            if list_tag != tag:
                close_list()
                list_tag = tag
                html_lines.append(f'<{tag} style="margin:8px 0 8px 8px;">')
            content = line[2:] if bullet else ordered.group(1)
            html_lines.append(
                f'<li style="margin-left:6px; color:{theme.TEXT}; '
                f'line-height:1.7;">{_inline(content)}</li>')
            continue

        close_list()

        # 空行
        if line.strip() == "":
            html_lines.append('<div style="height:6px;"></div>')
            continue

        # 普通段落
        html_lines.append(
            f'<p style="margin:5px 0; line-height:1.75;">{_inline(line)}</p>')

    # 收尾未关闭的代码块 / 表格 / 列表
    close_list()
    if in_code:
        html_lines.append("</div>")
    if in_table:
        html_lines.extend(table_rows)
        html_lines.append("</table>")

    css = f"""
    <style>
        body {{ font-family: "{theme.FONT_FAMILY}", sans-serif; color: {theme.TEXT}; }}
        p {{ margin: 5px 0; }}
        li {{ margin: 3px 0; }}
        a {{ color: {theme.PINK}; text-decoration: none; }}
        code {{ background: #f6f1f3; padding: 1px 4px; border-radius: 3px;
                font-size: 9pt; }}
    </style>
    """
    return css + "\n".join(html_lines)


def _inline(text: str) -> str:
    """处理行内格式：链接、粗体、行内代码"""
    # 先转义 HTML 特殊字符，再应用 Markdown 转换
    text = _escape(text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        rf'<a href="\2" style="color:{theme.PINK}; text-decoration:none;">\1</a>',
        text,
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(
        r"`([^`]+)`",
        r'<code style="background:#f6f1f3; padding:1px 4px; border-radius:3px;">\1</code>',
        text,
    )
    return text


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AboutWindow()
    win.show()
    app.exec()
