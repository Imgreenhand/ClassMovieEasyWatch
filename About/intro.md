# 项目简介

ClassMovieEasyWatch 是一款 Windows 平台的课堂视频辅助工具，帮助你在摸鱼时快速隐藏 / 还原浏览器窗口，避免被他人看到屏幕内容。（如你所见，代码写得非常糟糕，有可能出现各种bug，欢迎来[GitHub](https://github.com/Imgreenhand/ClassMovieEasyWatch)）提交Issues！！！

## 设计理念

- **极简操作**：一键隐藏，一键还原，不打断“学习”节奏
- **高度可配置**：支持多套配置档案，适应不同使用场景（OS：高度在哪）

## 技术栈

| 层级 | 技术 |
|------|------|
| UI 框架 | PySide6 (Qt for Python) |
| 窗口管理 | Win32 API |
| 热键监听 | pynput |
| 配置存储 | JSON |
