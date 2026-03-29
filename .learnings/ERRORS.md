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

## 2026-03-28: Ubuntu node 连接 MacBook Gateway 配对失败

### 错误描述
Ubuntu (192.168.1.18) 作为 node 连接到 MacBook Gateway (192.168.1.13) 时多次失败。

### 错误链

1. **SECURITY ERROR**: 不允许明文 ws:// 连接
   - 解决：`OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1`

2. **ECONNREFUSED 192.168.1.13:18789**: MacBook Gateway 只监听 127.0.0.1
   - 根因：Gateway 配置 `bind=lan` 后需要重启才能生效
   - 解决：`openclaw gateway restart`

3. **pairing required**: Node 需要配对
   - 解决：`openclaw devices approve --latest`

4. **systemd 服务 disconnected**: 环境变量未传递
   - 根因：systemd 服务不继承 shell 环境变量
   - 解决：在 `~/.config/systemd/user/openclaw-node.service` 的 `[Service]` 添加 `Environment=OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1`

### 教训
- Gateway 配置变更（bind/port 等）需要重启服务才能生效
- systemd 服务需要显式声明环境变量，不能依赖 shell 里的设置
- Node 配对流程：`node run` → `devices list` → `devices approve`

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

---

## 2026-03-28: GitHub 下载失败（OpenClaw-RL 克隆）

### 错误描述
Ubuntu 和 MacBook 都无法访问 github.com，git clone 超时。

### 根因
网络对 GitHub 访问受限，但 huggingface.co 可访问（用 hf-mirror.com 镜像解决）

### 教训
- GitHub 访问受限时，用 `gh api repos/.../tarball` 下载
- HuggingFace 模型用 `HF_ENDPOINT=https://hf-mirror.com` 镜像

---

## 2026-03-28: CUDA Toolkit 包名错误

### 错误
`sudo apt install cuda-toolkit-12-9` → E: 无法定位软件包

### 解决
PyTorch 不需要完整 CUDA Toolkit，pip/conda 自带 CUDA runtime：
```bash
conda install -y pytorch torchvision torchaudio -c nvidia -c defaults
```

---

## 2026-03-28: pip install torch 清华镜像地址错误

### 错误
`pip install torch --index-url https://mirrors.tuna.tsinghua.edu.cn/pytorch-wheels/cu121.html` → Could not find a version

### 解决
用 conda 安装，或用阿里云 pypi 镜像：
```bash
pip install torch -i https://mirrors.aliyun.com/pypi/simple/
```

---

## 2026-03-28: sentence-transformers show_progress 参数不兼容

### 错误
`model.encode(..., show_progress=True)` → ValueError: additional keyword arguments that this model does not use: ['show_progress']

### 解决
去掉 show_progress 参数（sentence-transformers 5.x 已不支持）

---

## 2026-03-28: expect/ssh 交互式密码失败

### 错误
expect 脚本中 spawn 不匹配，密码输入失败

### 解决
一次性操作直接手动输入密码：`ssh-copy-id -i <pub_key> user@host`

---

## 2026-03-28: subagent heredoc 传多行脚本失败

### 错误
subagent 的 heredoc 写多行 Python 文件格式错误/超时

### 解决
用 `write` 工具写到本地 → `scp` 传到远程


## 2026-03-29 Semantic Memory 索引失效 + 路径依赖错误

### 错误
1. Semantic Cache 服务器只在启动时加载 sessions，新 sessions 永远不被索引
2. 搜索结果为空时，没有第一时间用 `find`/`grep` 全局搜索文件系统
3. 坚持依赖有 bug 的索引系统，浪费大量时间

### 影响
- 找不到 `robot_0_1_final.mp4`（15秒视频，1.9MB）
- 用户提醒多次后仍然狡辩，没有及时承认错误并用备用方法

### 教训
1. **语义缓存只做辅助，文件系统是兜底**：搜索为空时，立即用 `find ~/Movies ~/.openclaw ~/Downloads` 找视频文件
2. **索引系统必须动态加载**：HEARTBEAT 每次 rsync 后重启 Semantic Cache 服务器
3. **Interactive Card 内容拿不到**：飞书 Interactive Card 内容无法通过 API 获取，只能看到文件路径

### 修复
- HEARTBEAT.md 已更新：rsync 后重启 Semantic Cache 服务器
- 后续搜索时优先搜文件系统

