# 项目简介

ClassMovieEasyWatch 是一款 Windows 平台的课堂视频辅助工具。通过热键或屏幕边缘浮动按钮，一键隐藏浏览器播放窗口并暂停视频，再次触发即可还原。

欢迎到 [GitHub](https://github.com/Imgreenhand/ClassMovieEasyWatch) 提交 Issues 或 PR。

## 设计理念

- **极简操作**：一键隐藏，一键还原
- **高度可配置**：多配置档案，自定义热键、浏览器、热区
- **分层架构**：Composition Root → Entry → Decision → Infrastructure 四层解耦

## 技术栈

| 层级 | 技术 |
|------|------|
| UI 框架 | PySide6 (Qt for Python) |
| 窗口管理 | Win32 API |
| 热键监听 | pynput |
| 音量控制 | pycaw |
| 配置存储 | JSON |
| 打包分发 | PyInstaller |
