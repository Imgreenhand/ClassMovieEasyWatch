# 开发相关

## 项目结构

```
ClassMovieEasyWatch/
├── main.py                 # 入口：系统托盘、启动窗口
├── StartMain.py            # 核心：隐藏 / 还原流程编排
├── SettingWindow.py        # 设置窗口
├── GUI/
│   ├── StartWindow.py      # 开始窗口
│   ├── SettingMainScroll.py # 设置主内容区
│   ├── FloatingButton.py   # 浮动按钮组件
│   └── Art/                # 图片资源
├── Inputs/
│   ├── InputEvents.py      # 热键监听
│   └── ButtonEvents.py     # 鼠标控制监听（至于为什么叫button不要管。。。）
├── Windows/
│   ├── WindowManager.py    # 窗口隐藏 / 还原
│   ├── GetWindow.py        # 获取目标窗口句柄
│   └── MediaControlVK.py   # 媒体控制（暂停 / 播放）
├── SaveData/
│   ├── DataManager.py      # 配置档案管理器（单例）
│   ├── FindSave.py         # 存档路径工具
│   ├── default.json        # 默认配置模板
│   └── save.json           # 运行时状态
└── About/                  # 关于页面内容
```

## 依赖

| 包 | 用途 |
|----|------|
| PySide6 | Qt UI 框架 |
| pywin32 | Win32 API 调用 |
| pynput | 全局热键监听 |

## 构建

```bash
git clone https://github.com/Imgreenhand/ClassMovieEasyWatch
pip install -r requirements.txt
python main.py
```
