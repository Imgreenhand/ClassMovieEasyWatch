import sys
from collections.abc import Callable
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QGuiApplication, QPainter, QColor, QBrush, QFont, QPixmap
from PySide6.QtWidgets import QWidget, QApplication, QPushButton, QLabel, QScrollArea

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        # 窗口属性
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: gray;")
        # 大小
        self.resize(1000, 500)
        # 上一次的位置
        self.pre_position = None
        # 加载图片
        pixmap = QPixmap("GUI/Art/Title.png")
        # 创建图片标签
        self.deco_label = QLabel(self)
        self.deco_label.setPixmap(pixmap)
        self.deco_label.setScaledContents(True)
        self.deco_label.resize(self.width(), int(self.width() * 0.152))
        self.deco_label.move(0, 0)
        # 标题
        self.title_label = QLabel("ClassMovieEasyWatch", self)
        self.title_label.setFont(QFont("微软雅黑", 45, QFont.Bold))
        self.title_label.setStyleSheet("color: black; background-color: rgba(0,0,0,0);")
        self.title_label.adjustSize()
        self.title_label.move(10, 10)
        # GitHub
        self.github_lable = QLabel(
        '<a href="https://github.com/Imgreenhand/ClassMovieEasyWatch">'
        'GitHub仓库</a>',
        self
        )
        self.github_lable.setFont(QFont("微软雅黑", 15, QFont.Bold))
        self.github_lable.setStyleSheet("color: black; background-color: rgba(0,0,0,0);")
        self.github_lable.setOpenExternalLinks(True) 
        self.github_lable.adjustSize()
        self.github_lable.move(10, 90)   
        # 滚动区域
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)   # 让内部控件可随滚动区域调整宽度
        self.scroll_area.setGeometry(self.width() - 260, 10, 250, self.height() - 20)  # 右侧，留边距
        self.margin = 20
        pass

    def showEvent(self, event):
        # 窗口首次显示时，调整滚动区域位置
        self.update_scroll_area_geometry()
        super().showEvent(event)

    def resizeEvent(self, event):
        # 当窗口大小改变时，重新调整装饰图片填满窗口上部
        self.deco_label.resize(self.width(), int(self.width() * 0.152))
        self.deco_label.move(0, 0)
        # 更新滚动区域
        self.update_scroll_area_geometry()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pre_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.pre_position is not None:
            delta = event.globalPosition().toPoint() - self.pre_position
            self.move(self.pos() + delta)
            self.pre_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pre_position = None

    def update_scroll_area_geometry(self):
        """计算并设置滚动区域的位置和大小（留边距，且不覆盖图片）"""
        # 获取图片底部坐标（图片左上是 (0,0)，高度可变）
        image_bottom = self.deco_label.height()  # 图片高度
        # 滚动区域顶部边距 = 图片底部 + 上边距
        top_margin = self.margin
        y = image_bottom + top_margin
        # 左右边距
        left_margin = self.margin
        right_margin = self.margin
        x = left_margin
        width = self.width() - left_margin - right_margin
        # 下边距
        bottom_margin = self.margin
        height = self.height() - y - bottom_margin
        # 只有在宽度和高度有效时才设置
        if width > 0 and height > 0:
            self.scroll_area.setGeometry(x, y, width, height)

if __name__ == "__main__":
    print("[MainWindowsDebug]:start")
    app = QApplication(sys.argv)
    app.setApplicationName("ClassMovieEasyWatch")
    win = MainWindow()
    win.show()
    try:
        app.exec()
    finally:
        print("程序已退出。")