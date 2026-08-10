# 开发相关

## 架构

项目采用四层架构，依赖方向始终从上向下：

```
【Composition Root】main.py            — 上帝层，组装所有组件，预飞检查
【Entry Layer】    entry/             — GUILogic（PySide6 + Toast） + ListenLogic（热键/鼠标）
【Decision Layer】  decision/          — FSM 防抖状态机 + Orchestrator 编排器 + Interfaces 抽象
【Infrastructure】  infrastructure/    — 线程池、信箱、窗口/媒体/浏览器管理器、配置存取
```

GUILogic 与 ListenLogic 在 Entry 层平级，互不依赖。

## 项目结构

```
ClassMovieEasyWatch/
├── main.py                     # Composition Root 入口
├── ClassMovieEasyWatch.spec    # PyInstaller 打包配置
├── entry/
│   ├── gui_logic.py            # GUILogic — 窗口管理 + Toast
│   └── listen_logic.py         # ListenLogic — 热键/鼠标事件
├── decision/
│   ├── interfaces.py           # 抽象接口
│   ├── finite_state_machine.py # 状态机 + 防抖
│   └── orchestrator.py         # 编排器
├── infrastructure/
│   ├── thread_pool.py          # 线程池
│   ├── mailbox.py              # 跨线程信箱
│   ├── window_manager.py       # 窗口隐藏/还原
│   ├── media_control.py        # 媒体控制
│   ├── browser_finder.py       # 浏览器窗口查找
│   ├── hotkey_listener.py      # pynput 热键监听
│   ├── data_manager.py         # 配置档案单例
│   └── path_utils.py           # 路径工具 + save.txt
├── GUI/
│   ├── toast.py                # 警告 Toast
│   ├── StartWindow.py          # 开始窗口
│   ├── FloatingButton.py       # 浮动按钮
│   ├── AboutWindow.py          # 关于窗口
│   ├── SettingMainScroll.py    # 设置主内容区
│   └── Art/                    # 美术资源
├── SettingWindow.py            # 设置窗口
├── SaveData/                   # 配置模板
│   └── default.json
├── About/                      # 关于页面 Markdown
└── ReadMeNeed/                 # README 图片
```

## 依赖

| 包 | 用途 |
|----|------|
| PySide6 | Qt UI 框架 |
| pywin32 | Win32 API |
| pynput | 全局热键 + 鼠标钩子 |
| pycaw | 系统音量控制 |
| psutil | 进程枚举 |
| Pillow | 图像处理 |

## 构建

```bash
# 源码运行
pip install -r requirements.txt
python main.py
