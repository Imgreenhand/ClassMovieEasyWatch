# Class Movie Easy Watch

属于是菜鸟的猎奇想法 + Vibe Coding 大人神力，代码看不得（悲）。 
正在试图看懂AI给的代码

---

课堂观影一键隐藏 / 还原工具  
支持 **全局热键** 和 **浮动按钮** 两种触发方式，一键隐藏浏览器播放窗口并暂停视频，再次触发恢复窗口并继续播放。    

---

## 功能特性

- **一键隐藏**：隐藏正在播放视频的浏览器窗口（Edge / Chrome），同时自动暂停视频。
- **一键恢复**：还原窗口并继续播放。
- **两种触发方式**：
  - **全局热键**（默认 `Ctrl+Alt+Q` 隐藏，`Ctrl+Alt+F9` 恢复）
  - **鼠标控制**（屏幕上的半透明圆钮，点击切换隐藏/恢复）
- **静音**：防止全局的暂停出现意外
- **多配置档案**：通过 `SaveData/*.json` 轻松切换浏览器、热键等设置。
- **系统托盘图标**：隐藏后托盘显示图标，支持右键还原或退出程序。

---

## 依赖安装

pynput
pywin32
psutil
pystray
Pillow
PySide6
pycaw

本项目基于 Python 3.10+ 开发，依赖以下库：
| Package | Version   |
|-|-|
|pynput	|1.8.2|
|pywin32|311|
|psutil	|7.2.2|
|pystray|0.19.5|
|Pillow	|12.2.0|
|PySide6|6.11.1|
|pycaw	|20251023|

通过requirements.txt直接安装

```bash
pip install -r requirements.txt
```

---

## 快速开始

### 1. 克隆/下载项目

```bash
git clone https://github.com/Imgreenhand/ClassMovieEasyWatch.git
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

程序会创建一个托盘图标，点击图标弹出选择菜单，按选择方式启动（热键或按钮）。

- 运行图片：    
![](/ReadMeNeed/屏幕截图%202026-07-05%20085804.png)
![](/ReadMeNeed/屏幕截图%202026-07-05%20085828.png)
![](/ReadMeNeed/屏幕截图%202026-07-05%20085841.png)
![](/ReadMeNeed/屏幕截图%202026-07-05%20085851.png)
![](/ReadMeNeed/屏幕截图%202026-07-05%20085913.png)

---

## 配置说明

### 配置文件结构 (`SaveData/*.json`)

每个 `.json` 文件对应一个配置档案，例如 `default.json`：

```json
{
    "name": "default",
    "hotkey_hide": "<ctrl>+<alt>+q",
    "hotkey_restore": "<ctrl>+<alt>+<f9>",
    "browser_names": "msedge.exe",
    "auto_pause": true,
    "hotspot_width": 220,
    "hotspot_height": 120,
    "hotspot_x": 1.0,
    "hotspot_y": 1.0,
    "pause_method": "appcommand",
    "highlight_seconds": 3
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
    "way": "hotkey",
    "save_file": "default"
}
```

你可以手动修改 `way` 来切换触发方式（hotkey, button），或修改 `save_file` 来加载其他配置档案（如 `chrome`）。

---

## 使用指南

### 热键模式

- 按下配置的隐藏热键 → 浏览器窗口被隐藏，视频暂停，托盘图标出现。
- 按下恢复热键 → 窗口恢复显示，视频继续播放。
- 托盘图标右键菜单也可还原或退出程序。

### 按钮模式

- 屏幕右下角会出现一个鼠标监测区域。
- **单击按钮**：隐藏窗口并暂停，按钮文字变为“恢复”。
- **再次单击**：恢复窗口并继续播放，按钮文字变回“隐藏”。

---

## 项目结构

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

---

## 开发进度

- 核心功能已完成（Maybe?）但代码不够健壮。