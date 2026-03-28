# ERRORS.md - 错误记录

## 2026-03-28: mdview.py 打开文件后浏览器停在 dashboard

### 错误描述
Minimax subagent 调用 mdview.py 打开 markdown 文件后，浏览器实际显示的是 `dashboard.html` 内容，而非目标文件内容。用户看到的是 night-build dashboard，而非预期的 SOP supplement 文件。

### 症状
- mdview.py 输出：`✅ 已打开（普通预览）: xxx.md, URL: http://127.0.0.1:18999/index.html`
- 浏览器实际：停留在 `dashboard.html` 或无变化

### 根因（三层叠加）

**Layer 1 - webbrowser.open() 默认行为**
- `webbrowser.open(url)` 默认 `new=0`，会激活已有 tab 而非打开新 URL
- 当 18999 端口已有 dashboard tab 开着，浏览器激活那个 tab 而非导航到新 URL
- 修复：`webbrowser.open(url, new=2)` 强制新 tab

**Layer 2 - mdview 与 dashboard 端口冲突**
- mdview.py 和 dashboard_mcp_server.py 都用 18999 端口
- mdview.py 检测到"已有 mdview 进程"就直接调用 `webbrowser.open(..., new=2)` 退出
- 但此时 18999 端口上跑的是 dashboard_mcp_server.py（不是 mdview.py）
- `webbrowser.open(..., new=2)` 打开的是 `http://127.0.0.1:18999/index.html`
- 而 18999 的 dashboard 服务器对 `/index.html` 返回 302 重定向到 `/dashboard.html`
- 所以浏览器最终显示的是 dashboard
- 修复：mdview.py 改用独立端口 **18990**

**Layer 3 - 复用逻辑只认进程不认端口**
- `existing_pids` 检查只搜索 `mdview.py` 进程名
- 找到任意 mdview.py 进程就用 PORT（18990）打开
- 但实际占用 18990 的可能不是 mdview（如有其他 Python 服务）
- 修复：先 `socket.connect_ex(('127.0.0.1', PORT))` 确认端口监听，再用 ps 找正确 PID

### 修复内容（mdview.py）
1. `PORT = 18999` → `PORT = 18990`
2. `webbrowser.open(url)` → `webbrowser.open(url, new=2)`（两处）
3. `existing_pids` 检查 → 改为 `socket.connect_ex()` 确认端口监听后再打开

### 教训
- 复用已有实例时，不仅要检查进程名，还要确认端口是否匹配
- 第三方服务（dashboard）跟自定义工具（mdview）不能用同一端口
- `new=0` 导致浏览器不复用标签页的情况只有在新旧 URL 不同时才会出现，容易被忽略

---

## 2026-03-28: dashboard 点击 .md 文件打开 2 个 tab

### 错误描述
在 dashboard (http://127.0.0.1:18999/dashboard.html) 里点击任务详情中的 .md 参考文件链接，会打开 2 个标签页。

### 根因
点击 → `fetch('/api/open?file=...')` → dashboard server spawn `mdview.py` → mdview.py 调用 `webbrowser.open()` → **Tab 1 (Python)** → API 返回 URL → JS 调用 `window.open(url)` → **Tab 2 (JS)**

mdview.py 自己打开了一个 tab，JS 又打开了一个 tab，双重打开。

### 修复
1. mdview.py 加 `--no-browser` 参数：生成 HTML 但不打开浏览器
2. server.py 的 `/api/open` 调用 mdview 时加 `--no-browser`
3. dashboard server 重启生效

### 文件
- 修改：`server.py`（加 `--no-browser`）
- 修改：`mdview.py`（加 `--no-browser` 参数和判断）
