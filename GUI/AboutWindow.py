import re
import logging
from pathlib import Path
from infrastructure.path_utils import resource_path
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QFrame, QVBoxLayout,
    QHBoxLayout, QTextBrowser,
)

CHAPTERS = [
    ("项目简介", "intro"),
    ("功能说明", "features"),
    ("使用方法", "usage"),
    ("开发相关", "dev"),
    ("版本管理", "versions"),
]

ABOUT_DIR = Path(__file__).parent.parent / "About"

CLOSE_BTN_STYLE = """
    QPushButton {
        background: #ffffff; border: 1px solid #fb7299;
        border-radius: 4px; color: #fb7299; font-weight: bold;
        padding: 2px 8px;
    }
    QPushButton:hover { background: #fb7299; color: #ffffff; }
"""


class AboutSidebarItem(QFrame):
    """侧边栏章节项"""

    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setCursor(Qt.PointingHandCursor)
        self._text = text

        self.label = QLabel(text, self)
        self.label.setFont(QFont("微软雅黑", 11))
        self.label.setStyleSheet("color: #666; background: transparent; padding-left: 16px;")
        self.label.setFixedHeight(38)
        self._selected = False

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        if selected:
            self.setStyleSheet("background: #fff0f4; border-left: 3px solid #fb7299;")
            self.label.setStyleSheet("color: #fb7299; background: transparent; padding-left: 13px;")
        else:
            self.setStyleSheet("background: transparent; border-left: 3px solid transparent;")
            self.label.setStyleSheet("color: #666; background: transparent; padding-left: 16px;")

    def mousePressEvent(self, event):
        parent = self.parent()
        if parent and hasattr(parent, "parent") and hasattr(parent.parent(), "_on_chapter_click"):
            parent.parent()._on_chapter_click(self._text)


class AboutWindow(QWidget):
    """关于窗口：侧边栏章节导航 + 右侧 Markdown 内容"""

    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: #ffffff;")
        self.resize(720, 520)
        self.setMinimumSize(560, 380)

        self._drag_pos: QPoint | None = None
        self._sidebar_items: dict[str, AboutSidebarItem] = {}
        self._md_cache: dict[str, str] = {}

        self._setup_topbar()
        self._setup_sidebar()
        self._setup_content()

        # 默认选中第一章
        first = CHAPTERS[0][0]
        self._on_chapter_click(first)

    # ═══════════════════════════════════════
    # 顶栏
    # ═══════════════════════════════════════

    def _setup_topbar(self) -> None:
        bar_h = 44
        self._topbar = QFrame(self)
        self._topbar.setFixedHeight(bar_h)
        self._topbar.setStyleSheet("background: #ffffff; border-bottom: 1px solid #eee;")

        # 标题
        title = QLabel("关于 ClassMovieEasyWatch", self._topbar)
        title.setFont(QFont("微软雅黑", 12, QFont.Bold))
        title.setStyleSheet("color: #333; background: transparent; border: none;")
        title.move(16, (bar_h - 22) // 2)

        # 图标
        icon_label = QLabel(self._topbar)
        icon_pix = QPixmap(resource_path("GUI/Art/Sign.svg"))
        if not icon_pix.isNull():
            icon_label.setPixmap(icon_pix.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.move(self.width() - 64, (bar_h - 20) // 2)

        # 关闭按钮
        self._btn_close = QPushButton("X", self._topbar)
        self._btn_close.setFont(QFont("微软雅黑", 11, QFont.Bold))
        self._btn_close.setFixedSize(30, 26)
        self._btn_close.setStyleSheet(CLOSE_BTN_STYLE)
        self._btn_close.clicked.connect(self.close)

        self._bar_h = bar_h

    # ═══════════════════════════════════════
    # 侧边栏
    # ═══════════════════════════════════════

    def _setup_sidebar(self) -> None:
        sidebar_w = 140
        self._sidebar = QFrame(self)
        self._sidebar.setStyleSheet("background: #fafafa; border-right: 1px solid #eee;")
        self._sidebar.setFixedWidth(sidebar_w)

        y = 12
        for text, _ in CHAPTERS:
            item = AboutSidebarItem(text, self._sidebar)
            item.setFixedWidth(sidebar_w)
            item.move(0, y)
            self._sidebar_items[text] = item
            y += 42

    # ═══════════════════════════════════════
    # 内容区
    # ═══════════════════════════════════════

    def _setup_content(self) -> None:
        self._browser = QTextBrowser(self)
        self._browser.setOpenExternalLinks(True)
        self._browser.setStyleSheet("""
            QTextBrowser {
                background: #ffffff; border: none; color: #333;
                padding: 12px 20px;
            }
        """)
        self._browser.setFont(QFont("微软雅黑", 10))

    # ═══════════════════════════════════════
    # 章节切换
    # ═══════════════════════════════════════

    def _on_chapter_click(self, text: str) -> None:
        for name, item in self._sidebar_items.items():
            item.set_selected(name == text)

        for disp, key in CHAPTERS:
            if disp == text:
                html = self._load_md(key)
                self._browser.setHtml(html)
                break

    def _load_md(self, key: str) -> str:
        if key in self._md_cache:
            return self._md_cache[key]
        path = ABOUT_DIR / f"{key}.md"
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            logging.error(f"无法读取关于页面内容: {path}")
            self._md_cache[key] = "<p style='color:#999;'>内容加载失败</p>"
            return self._md_cache[key]
        html = _md_to_html(raw)
        self._md_cache[key] = html
        return html

    # ═══════════════════════════════════════
    # 窗口事件
    # ═══════════════════════════════════════

    def resizeEvent(self, event):
        bar_h = self._bar_h
        sidebar_w = self._sidebar.width()
        self._topbar.setGeometry(0, 0, self.width(), bar_h)
        self._btn_close.move(self.width() - 40, (bar_h - 26) // 2)
        self._sidebar.setGeometry(0, bar_h, sidebar_w, self.height() - bar_h)
        self._browser.setGeometry(
            sidebar_w, bar_h, self.width() - sidebar_w, self.height() - bar_h,
        )
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

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

    for line in lines:
        # 代码块
        if line.startswith("```"):
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                html_lines.append('<pre style="background:#f5f5f5; border-radius:4px; '
                                  'padding:10px; font-size:9pt; overflow-x:auto;">'
                                  '<code>')
                in_code = True
            continue
        if in_code:
            html_lines.append(_escape(line))
            continue

        # 表格
        if "|" in line and line.strip().startswith("|"):
            if not in_table:
                in_table = True
                table_rows = []
                html_lines.append('<table style="border-collapse:collapse; width:100%; '
                                  'margin:8px 0;">')
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                # 分隔行，跳过
                continue
            tag = "th" if len(table_rows) == 0 else "td"
            row_html = "<tr>" + "".join(
                f'<{tag} style="border:1px solid #ddd; padding:4px 10px; '
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
            html_lines.append(
                f'<h4 style="color:#555; margin:14px 0 6px 0;">{_inline(line[4:])}</h4>')
            continue
        if line.startswith("## "):
            html_lines.append(
                f'<h3 style="color:#fb7299; margin:18px 0 8px 0; '
                f'border-bottom:1px solid #eee; padding-bottom:4px;">{_inline(line[3:])}</h3>')
            continue
        if line.startswith("# "):
            html_lines.append(
                f'<h2 style="color:#fb7299; margin:20px 0 10px 0; '
                f'border-bottom:2px solid #fb7299; padding-bottom:6px;">{_inline(line[2:])}</h2>')
            continue

        # 无序列表
        if re.match(r"^- ", line):
            html_lines.append(
                f'<li style="margin-left:20px; color:#333;">{_inline(line[2:])}</li>')
            continue

        # 空行
        if line.strip() == "":
            html_lines.append("<br>")
            continue

        # 普通段落
        html_lines.append(f'<p style="margin:4px 0; line-height:1.7;">{_inline(line)}</p>')

    # 收尾未关闭的代码块 / 表格
    if in_code:
        html_lines.append("</code></pre>")
    if in_table:
        html_lines.extend(table_rows)
        html_lines.append("</table>")

    css = """
    <style>
        body { font-family: "微软雅黑", sans-serif; }
        p { margin: 4px 0; }
        li { margin: 2px 0; }
        code { background: #f0f0f0; padding: 1px 4px; border-radius: 2px; font-size: 9pt; }
    </style>
    """
    return css + "\n".join(html_lines)


def _inline(text: str) -> str:
    """处理行内格式：链接、粗体、行内代码"""
    # 先转义 HTML 特殊字符，再应用 Markdown 转换
    text = _escape(text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  r'<a href="\2" style="color:#fb7299; text-decoration:none;">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<code style="background:#f0f0f0; padding:1px 4px; '
                  r'border-radius:2px;">\1</code>', text)
    return text


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
