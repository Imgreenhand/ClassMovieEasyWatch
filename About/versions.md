# 版本管理

ClassMovieEasyWatch 的版本通过 [GitHub Releases](https://github.com/Imgreenhand/ClassMovieEasyWatch/releases) 管理。

## 获取最新版本

```bash
git clone https://github.com/Imgreenhand/ClassMovieEasyWatch
cd ClassMovieEasyWatch
git pull origin main
```

或直接下载：[Releases 页面](https://github.com/Imgreenhand/ClassMovieEasyWatch/releases)

## 更新日志

### v0.0.1

- 全新的界面风格：无边框圆角卡片窗口、统一配色与控件样式
- 开始窗口重做：配置下拉带图标、根据所选配置显示当前热键、支持回车/ESC
- 设置窗口重做：品牌顶栏、带图标的侧边栏、卡片式设置分组
- 热键页：快捷键胶囊显示、一键清空组合、键盘布局优化为一屏可见
- 应用页：常用浏览器快捷选择、已安装应用列表样式优化
- 个性化页：热区预览重绘（参考网格、尺寸胶囊、四角手柄）
- 关于窗口：章节图标、Markdown 渲染改进（有序列表、代码块自动换行、表格）
- 托盘菜单：菜单项图标与统一菜单样式
- 提示组件：Toast 与热区高亮浮层支持淡入淡出
- 图标改用项目内置矢量素材，界面不再使用字符表情
- 修复开始窗口直接关闭时事件循环未退出的问题
- 修复设置/关于窗口重复打开会产生多个实例的问题

### v0.0.0 (2026-08)

- 初始版本发布
- 热键隐藏/还原浏览器窗口
- WM_APPCOMMAND 和全局媒体键两种暂停方式
- 多配置档案管理
- 屏幕边缘热区触发
- 系统托盘集成

## 反馈与贡献

遇到 Bug 或有功能建议？欢迎到 [GitHub Issues](https://github.com/Imgreenhand/ClassMovieEasyWatch/issues) 提交。
