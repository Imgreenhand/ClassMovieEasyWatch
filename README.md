# Class Movie Easy Watch

属于是菜鸟的猎奇想法 + Vibe Coding 大人神力，代码看不得（悲）

---

课堂观影一键隐藏 / 还原工具  
支持 **全局热键** 和 **浮动按钮** 两种触发方式，一键隐藏浏览器播放窗口并暂停视频，再次触发恢复窗口并继续播放。

---

## 功能特性

- **一键隐藏**：隐藏正在播放视频的浏览器窗口（Edge / Chrome），同时自动暂停视频。
- **一键恢复**：还原窗口并继续播放。
- **两种触发方式**：
  - **全局热键**（默认 `Ctrl+Alt+Q` 隐藏，`Ctrl+Alt+F9` 恢复）
  - **浮动按钮**（屏幕上的半透明圆钮，点击切换隐藏/恢复）
- **多配置档案**：通过 `SaveData/*.json` 轻松切换浏览器、热键等设置。
- **系统托盘图标**：隐藏后托盘显示图标，支持右键还原或退出程序。

---

## 依赖安装

本项目基于 Python 3.10+ 开发，依赖以下库：

```
**pynput pywin32 psutil pystray Pillow PySide6**
```

通过requirements.txt直接安装

```bash
pip install -r requirements.txt
```

- `pynput`：全局热键监听  
- `pywin32`：Windows API 调用（窗口管理、进程枚举）  
- `psutil`：进程信息获取  
- `pystray` + `Pillow`：系统托盘图标  
- `PySide6`：浮动按钮（Qt 界面）

---

## 快速开始

### 1. 克隆/下载项目

```bash
git clone https://github.com/yourname/ClassMovieEasyWatch.git
cd ClassMovieEasyWatch
```

### 2. 准备配置文件

- 配置文件放在 `SaveData/` 目录下。
- 至少需要 `default.json`（示例见下文）。
- 用户存档 `SaveData/save.json` 用于记录当前激活的配置档案和触发方式（**程序会自动创建**）。

### 3. 运行程序

```bash
python main.py
```

程序会读取 `SaveData/save.json` 中的配置，按设定方式启动（热键或按钮）。

---

## 配置说明

### 配置文件结构 (`SaveData/*.json`)

每个 `.json` 文件对应一个配置档案，例如 `default.json`：

```json
{
    "hotkey_hide": "<ctrl>+<alt>+q",
    "hotkey_restore": "<ctrl>+<alt>+<f9>",
    "browser_names": "msedge.exe",
    "auto_pause": true,
    "tray_icon_enabled": true
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `hotkey_hide` | string | 隐藏热键（pynput 格式），如 `<ctrl>+<alt>+q` |
| `hotkey_restore` | string | 恢复热键，功能键需用尖括号，如 `<f9>` |
| `browser_names` | string | 目标浏览器进程名（如 `chrome.exe`、`msedge.exe`） |
| `auto_pause` | bool | 隐藏时是否自动暂停/恢复播放 |
| `tray_icon_enabled` | bool | 隐藏后是否显示系统托盘图标 |

> 注意：热键中的功能键（F1~F12）必须写成 `<f1>` 等形式，否则 `pynput` 会报错。

### 用户存档 (`SaveData/save.json`)

程序自动创建/读取该文件，内容示例：

```json
{
    "way": "hotkey",        // "hotkey" 或 "button"
    "save_file": "default"  // 当前激活的配置档案名（不含 .json）
}
```

你可以手动修改 `way` 来切换触发方式，或修改 `save_file` 来加载其他配置档案（如 `chrome`）。

---

## 使用指南

### 热键模式

- 按下配置的隐藏热键 → 浏览器窗口被隐藏，视频暂停，托盘图标出现。
- 按下恢复热键 → 窗口恢复显示，视频继续播放。
- 托盘图标右键菜单也可还原或退出程序。

### 按钮模式

- 屏幕右下角会出现一个圆形浮动按钮（默认文字“隐藏”）。
- **单击按钮**：隐藏窗口并暂停，按钮文字变为“恢复”。
- **再次单击**：恢复窗口并继续播放，按钮文字变回“隐藏”。
- 同样支持托盘图标右键菜单。

---

## 项目结构

```
ClassMovieEasyWatch/
├── main.py                     # 主入口
├── Inputs/
│   ├── InputEvents.py          # 全局热键监听
│   └── ButtonEvents.py         # 浮动按钮事件封装
├── Windows/
│   ├── GetWindow.py            # 根据进程名获取窗口句柄
│   ├── WindowManager.py        # 窗口隐藏/恢复逻辑
│   ├── MediaControlVK.py       # 媒体播放/暂停控制
│   └── TrayManager.py          # 系统托盘图标管理
├── GUI/
│   └── FloatingButton.py       # PySide6 浮动按钮界面
├── SaveData/
│   ├── ProfileManager.py       # 配置档案加载
│   ├── FindSave.py             # 读写用户存档
│   ├── default.json            # 默认配置示例
│   ├── chrome.json             # Chrome 配置示例
│   └── save.json               # 用户运行状态（自动生成）
└── README.md
```

---

## 开发进度

- 核心功能已完成（Maybe?）
- 还需轻量化AI写的数据管理器等 
- 缺少GUI通过窗口配置JSON 
- 目前全局的媒体暂停会影响到其他播放 

---

**Enjoy your class movie time without worry!** 