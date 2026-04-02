# F-001: 修复代码块亮色模式 CSS 硬编码 Bug

## 问题描述
`docs-server.py` 中 `pre` 和 `code` 的背景色写死了深色值（`#0d0d14`、`#1a1a28`），切到亮色主题后代码块仍然是黑色背景，文字看不见。

## 文件
- `/Users/lr/.openclaw/workspace/tools/docs-server.py`

## 修复步骤

### Step 1: 定位硬编码的 CSS 行
在文件中搜索以下两行：
```css
pre{{background:#0d0d14;border:1px solid var(--border);padding:16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6}}
code{{background:#1a1a28;padding:2px 6px;border-radius:4px;font-size:0.9em;color:var(--accent2)}}
```
以及 `tr:hover` 行：
```css
tr:hover{{background:#1a1a28}}
```

### Step 2: 替换为 CSS 变量
将这三行的硬编码颜色替换为 CSS 变量：

**替换前：**
```css
pre{{background:#0d0d14;border:1px solid var(--border);padding:16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6}}
code{{background:#1a1a28;padding:2px 6px;border-radius:4px;font-size:0.9em;color:var(--accent2)}}
tr:hover{{background:#1a1a28}}
```

**替换后：**
```css
pre{{background:var(--surface);border:1px solid var(--border);padding:16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6}}
code{{background:var(--surface2);padding:2px 6px;border-radius:4px;font-size:0.9em;color:var(--accent2)}}
tr:hover{{background:var(--surface2)}}
```

### Step 3: 修复 header 背景色硬编码
在文件中搜索：
```css
.header{{position:fixed;top:0;left:0;right:0;height:var(--header-h);background:rgba(10,10,15,0.95);border-bottom:1px solid var(--border);...
```

**替换前：**
```css
.header{{position:fixed;top:0;left:0;right:0;height:var(--header-h);background:rgba(10,10,15,0.95);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 20px;z-index:100; backdrop-filter:blur(10px)}}
```

**替换后：**
```css
.header{{position:fixed;top:0;left:0;right:0;height:var(--header-h);background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 20px;z-index:100; backdrop-filter:blur(10px)}}
```

### Step 4: 在亮色主题 CSS 变量中添加代码块专用颜色
在 `:root[data-theme="light"]{{...}}` 块中，添加一个 pre 专用变量（可选但更好看）。
实际上 Step 2 已经用 `var(--surface)` 和 `var(--surface2)` 替代了硬编码值，所以亮色主题会自动适配。

### Step 5: 重启 docs-server 验证
```bash
# 找到并杀掉旧进程
lsof -ti:18998 | xargs kill -9 2>/dev/null
# 启动新进程
cd /Users/lr/.openclaw/workspace && nohup python3 tools/docs-server.py > /tmp/docs-server.log 2>&1 &
# 等待 2 秒
sleep 2
# 验证端口
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18998/docs.0-1.ai/
```

### Step 6: 验证亮色模式
在浏览器中打开 http://127.0.0.1:18998/docs.0-1.ai/，点击亮色切换按钮 ☀️：
- 代码块 `pre` 背景应为浅色（`#f8f9fa`）
- 行内代码 `code` 背景应为浅灰（`#e9ecef`）
- header 背景应为浅色
- 表格行 hover 应为浅灰

## 验证标准
- [x] 暗色模式代码块正常显示
- [x] 亮色模式代码块正常显示（浅色背景+深色文字）
- [x] header 在两种模式下都正常
- [x] 服务启动成功，http_code=200
