---
name: rpa-automation
description: macOS 自动化工具集 - 桌面软件控制、文件操作、Excel处理、定时任务（完全本地，隐私安全）
---

# RPA Automation Skill

**重要规则**：
1. 禁止使用 `openclaw browser` 命令
2. 操作用户 Chrome 必须用 `osascript`
3. 先确认 Browser Relay 状态再操作

macOS 自动化工具集，完全本地运行，隐私安全，不依赖 VPN。

## 核心工具

| 工具 | 用途 | 隐私 |
|------|------|------|
| AppleScript | 控制 macOS 应用 | ✅ 本地 |
| Python + openpyxl | Excel 操作 | ✅ 本地 |
| Python + os/shutil | 文件操作 | ✅ 本地 |
| Cron | 定时任务 | ✅ 本地 |

## 使用方式

### 1. AppleScript - 桌面应用控制

通过 exec 运行 osascript：

```bash
# 打开应用
osascript -e 'tell application "Safari" to activate'

# 打开网页
osascript -e 'tell application "Safari"
    activate
    open location "https://example.com"
end tell'

# 关闭窗口
osascript -e 'tell application "Safari" to close window 1'

# 获取应用列表
osascript -e 'tell application "System Events" to get name of every process whose background only is false'
```

### 2. 文件操作

```bash
# 用 Python 处理
python3 << 'EOF'
import os
import shutil

# 复制文件
shutil.copy('source.txt', 'dest.txt')

# 移动文件
shutil.move('file.txt', 'folder/')

# 创建目录
os.makedirs('new_folder', exist_ok=True)

# 列出文件
for f in os.listdir('.'):
    print(f)
EOF
```

### 3. Excel 操作

```bash
# 安装 openpyxl（如果需要）
pip3 install openpyxl pandas

# 读取 Excel
python3 << 'EOF'
import openpyxl

wb = openpyxl.load_workbook('data.xlsx')
sheet = wb.active

# 读取
for row in sheet.iter_rows(values_only=True):
    print(row)

# 写入
sheet['A1'] = 'Hello'
wb.save('data.xlsx')
EOF
```

### 4. 定时任务

通过 OpenClaw cron 设置：

```bash
openclaw cron add --name "daily-report" --schedule "0 9 * * *" --command "python3 ~/scripts/report.py"
```

## 隐私保护

- ✅ 所有操作在本地执行
- ✅ 不上传任何数据到云端
- ✅ 不依赖 VPN
- ✅ 不使用第三方云服务

## 安全注意事项

1. **辅助功能权限**：PyAutoGUI 等工具需要授权
   - 系统偏好设置 → 安全性与隐私 → 辅助功能
   - 添加 Python 或 OpenClaw

2. **应用权限**：AppleScript 需要应用授权
   - 首次运行时会弹窗授权

## 常用脚本示例

### 打开多个应用
```bash
osascript -e 'tell application "Notes" to activate'
osascript -e 'tell application "Calendar" to activate'
osascript -e 'tell application "Mail" to activate'
```

### 批量重命名文件
```bash
python3 << 'EOF'
import os
folder = '~/Downloads'
for i, f in enumerate(os.listdir(os.path.expanduser(folder)), 1):
    if f.endswith('.pdf'):
        os.rename(os.path.join(folder, f), f'file_{i}.pdf')
EOF
```

### 读取 CSV 并处理
```bash
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data.csv')
print(df.head())
df['total'] = df['a'] + df['b']
df.to_csv('result.csv', index=False)
EOF
```

### Chrome 扩展自动化（加载/刷新/启动调试）

**⚠️ 重要**：Chrome 扩展页面使用 **Shadow DOM**，直接用 querySelector 无效。

**简化方案（推荐）**：刷新扩展页面即可重新加载代码

```bash
# 方法1：刷新扩展页面（最简单，推荐）
osascript -e 'tell application "Google Chrome" to open location "chrome://extensions"'
```

**完整流程（复杂，仅供参考）**：

由于 Shadow DOM 限制，完整自动化需要：
1. 打开扩展页面
2. 用 JavaScript 遍历 Shadow DOM
3. 模拟键盘操作文件对话框

```bash
osascript << 'EOF'
-- 配置
property extensionPath : "$HOME/.openclaw/browser/chrome-extension"

-- 1. 打开扩展页面
tell application "Google Chrome"
    activate
    open location "chrome://extensions"
end tell

delay 1

-- 2. 点击开发者模式（如果需要）
tell application "Google Chrome"
    tell active tab
        execute javascript "
            const toolbar = document.querySelector('extensions-toolbar');
            if (toolbar && toolbar.shadowRoot) {
                const toggle = toolbar.shadowRoot.querySelector('cr-toggle');
                if (toggle && !toggle.checked) {
                    toggle.click();
                }
            }
        "
    end tell
end tell

delay 0.5

-- 3. 点击加载按钮（通过键盘）
tell application "System Events"
    tell process "Google Chrome"
        -- 使用键盘导航
        keystroke tab
        keystroke tab
        keystroke return
    end tell
end tell

delay 0.5

-- 4. 文件选择对话框
tell application "System Events"
    tell process "Finder"
        try
            set theWindow to window "打开"
            keystroke extensionPath
            delay 0.5
            keystroke return
            delay 0.5
            keystroke return
        end try
    end tell
end tell

return "完成"
EOF
```

**最实用的工作流**：
1. 手动加载扩展一次
2. 后续只需刷新页面：`osascript -e 'tell app "Chrome" to open location "chrome://extensions"'`

### 定时清理下载文件夹
```bash
python3 << 'EOF'
import os
import time
from datetime import datetime

downloads = os.path.expanduser('~/Downloads')
now = time.time()
age_days = 30

for f in os.listdir(downloads):
    path = os.path.join(downloads, f)
    if os.stat(path).st_mtime < now - (age_days * 86400):
        if os.path.isfile(path):
            os.remove(path)
            print(f'Deleted: {f}')
EOF
```

## 限制

- ❌ 无法控制未支持 AppleScript 的应用
- ❌ 无法从 macOS 控制 iOS
- ❌ 无 GUI 录制器（需用 Automator 手动创建）
- ⚠️ 需要授权辅助功能

## 依赖安装

如需完整功能：

```bash
# Python 自动化库
pip3 install openpyxl pandas pyautogui

# 授权辅助功能（系统偏好设置 → 安全性与隐私 → 辅助功能）
```

## 官方文档

- AppleScript: https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptX/
- PyAutoGUI: https://pyautogui.readthedocs.io/
- openpyxl: https://openpyxl.readthedocs.io/
