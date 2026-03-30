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


## 2026-03-29 视频生成综合教训（补充）

### 今天犯的错误

1. **没有先确认已有的内容就开始生成**
   - 没有先检查 ~/Movies 下已有哪些视频
   - 直接开始生成新的，没有对比
   - 用户提醒后才去搜索

2. **每次只测一个分辨率/帧数，效率低下**
   - 一个一个测，浪费时间
   - 应该设计一个批量测试脚本

3. **不理解 SVD 的 VRAM 需求根源**
   - 不知道 temporal attention 需要同时加载多帧
   - 反复 OOM 后才理解是架构问题而非配置问题

4. **用户给优化提示词后才意识到要提前准备**
   - 自己写的提示词太简单
   - 应该一开始就请用户优化或自己先优化好

5. **Interactive Card 内容看不到**
   - 飞书卡片消息内容无法通过 API 获取
   - 应该早点告知用户这个限制

6. **狡辩而不是行动**
   - 用户说"确实有视频"，我还在找借口
   - 应该立刻承认"我找不到，请你告诉我路径"而不是辩解

### 根本问题
- 遇到问题习惯性地用嘴解释，而不是用手找答案
- 搜索引擎（语义缓存）坏了就停了，没有兜底方案
- 对自己的"记忆"过度自信，忽视文件系统这个事实来源


### 7. 不知道飞书能直接发视频到用户手机
   - 不知道 `openclaw message send --channel feishu --media <path>` 可以直接发视频
   - 浪费很多时间查 API

### 做对的地方（最后）
- 用 `openclaw message send` 命令直接发送到飞书成功
- 发送视频格式：`--channel feishu --media <本地路径>`
- 目标用户：`--target ou_18ed3541348294718c48833176aea3b8`


## 2026-03-29: Chrome 146 扩展加载完全失败

### 错误
- 尝试用 `--load-extension` 在 Chrome 146 上加载 Browser Relay 扩展
- 全新 profile 能加载但 Chrome 自动禁用（state=None）
- 已有 profile 的 Secure Preferences 完整性校验导致扩展注册被重置
- 浪费了约 2 小时尝试各种方法

### 教训
- Chrome 146+ 完全阻止命令行加载未打包扩展
- 应该先检查 Chrome 版本和文档，而不是直接试
- OpenClaw 托管浏览器（18800）是更好的方案，应该优先考虑

## 2026-03-29: Semantic Cache 索引问题

### 错误
- 语义缓存服务器只在启动时加载 sessions
- 新的聊天记录不会被自动索引
- sync_and_reindex.py 是空脚本，没有实现
- 导致 memory_search 找不到今天的记录

### 教训
- 需要重启服务器或实现 reindex API 才能搜索新内容
- HEARTBEAT 里的同步逻辑需要补充 reindex 步骤

---

## 2026-03-29: Semantic Cache 7 项优化 - 3 Subagent 并行编辑冲突

### 错误
- 同时派 3 个 subagent 修改同一个 server.py 文件
- Subagent C（增量索引 + BM25）的修改被 Subagent B 覆盖，BM25 代码丢失
- 根因：Subagent B 完成时间晚于 C，写文件时覆盖了 C 的改动

### 影响
- BM25 混合检索功能丢失，需要重新实现
- 浪费了 subagent C 的 3 分 52 秒运行时间

### 教训
- **同一文件不能同时交给多个 subagent 编辑**
- 正确做法：拆成 3 个独立文件（模块），或串行执行，或最后手动合并
- 或者：每个 subagent 改文件的不同部分（用行号定位 sed），但仍有风险

---

## 2026-03-29: Semantic Cache 角色过滤导致搜索返回 0 条

### 错误
- Subagent B 添加了 `roles=["user","assistant"]` 默认过滤
- 但 text_store 中 57% 的记录 role 是 `"toolResult"`（不是 `"assistant"`）
- 导致所有查询返回 0 条结果，看起来像索引坏了

### 诊断过程
1. 先怀疑 FAISS 索引损坏 → 用 Python 直接测试，距离正常 (0.5+)
2. 再怀疑阈值太高 → 降到 0.0 还是 0 条
3. 最后用 `all roles` 参数测试 → 5 条命中，确认是 roles 过滤问题
4. 发现 `sed` 修复第一次引号转义失败，第二次才成功

### 教训
- 添加过滤条件时必须检查数据分布（`Counter(role)`）
- `sed` 在远程 SSH 中引号转义容易出错，改完后必须 `grep` 验证
- 搜索返回空时，按顺序排查：索引 → 维度 → 过滤条件 → 阈值

---

## 2026-03-29: ComfyUI + Wan 2.1 方案不可行（6GB 显存限制）

### 错误
- 调研报告推荐 Wan 2.1 I2V 1.3B，但 HuggingFace 上没有这个模型
- Wan-AI 只发布了 14B 的 I2V 版本（6GB 跑不动）
- T2V 1.3B 虽然扩散模型小，但文本编码器 umt5-xxl 是 4.6B 参数
- 模型下载（~10GB）在 9 分钟内完不成，subagent 超时

### 教训
- 调研报告的模型名称必须实际验证（hf-mirror.com 上搜一下确认存在）
- 6GB 显存的图生视频本地方案几乎没有——考虑云端 API（可灵/Kling/Luma）
- 大文件下载任务不适合 subagent（超时），应该后台运行 + 定时检查

---

## 2026-03-29: SSH pkill 导致连接断开

### 错误
- 在 SSH session 中执行 `pkill -f "server.py"` 导致整个 SSH 连接断开
- 因为 pkill 杀掉了 SSH 进程链中的子进程
- 连续 3 次 exit code 255

### 教训
- 不要在 SSH session 中 pkill 带有通配符的进程名
- 正确做法：先用 `pgrep` 找到具体 PID，再用 `kill <pid>` 精确杀
- 或者用 `nohup ... & disown` 启动进程，确保不受 SSH 断连影响

---

## 2026-03-29: DeepSeek MCP Server WASM 模块路径变更导致永久卡死

### 错误
- DeepSeek MCP server (`deepseek-mcp-server`) 调用时一直超时，60秒无响应
- server 进程没有任何输出，连 initialize 都不返回

### 根因
- `deepseek-mcp-server.mjs` 引用路径：
  ```
  COMPILED_FILE = '/Users/lr/.openclaw/workspace/openclaw-zero-token/dist/deepseek-web-client-oV3jRi_T.mjs'
  ```
- 该文件在 workspace 目录清理或 git 操作后丢失
- MCP server 尝试 `readFileSync(COMPILED_FILE)` 时文件不存在，代码试图从 `sha3_wasm_b64.txt` 读取，但逻辑有 fallback 缺陷导致一直等待

### 修复
- 实际解决方案：从 `~/.openclaw/extensions/deepseek-web-chat/sha3_wasm_b64.txt` 提取 WASM base64 数据
- 写入目标路径：
  ```bash
  SHA3_B64=$(cat ~/.openclaw/extensions/deepseek-web-chat/sha3_wasm_b64.txt | tr -d '\n')
  echo "const SHA3_WASM_B64 = \"${SHA3_B64}\";" > ~/.openclaw/workspace/openclaw-zero-token/dist/deepseek-web-client-oV3jRi_T.mjs
  ```
- 注意：`deepseek-web-chat` 是 Channel 插件，有独立的 WASM 文件
- `deepseek-mcp-server` 和 `deepseek-web-chat` 共用同一个 WASM 模块，只是引用路径不同

### 教训
- workspace 清理时不能动 `openclaw-zero-token/dist/` 目录
- 这个目录不在 git 备份里，是 npm 包安装的产物
- 以后清理前要先确认所有依赖路径是否还在

---

## 2026-03-29: 误用 CDP HTTP API 方法导致浏览器控制失败

### 错误
- 尝试用 `POST /json/new` 创建 Chrome 新标签页，返回 405 Method Not Allowed
- `openclaw browser` CLI 命令全部报 `unknown method: browser.request`

### 根因
- CDP HTTP API 的 new tab 端点需要 **PUT** 方法，不是 POST
- `openclaw browser` 命令走 Gateway RPC，而 browser plugin 的 HTTP 控制服务（端口 18791）未启动
- Gateway 2026.3.28 升级后 browser plugin 的服务注册方式变更

### 修复
- 创建 Chrome 新 tab：`curl -X PUT http://127.0.0.1:18800/json/new`
- 用 osascript 在主 Chrome 中打开 URL（如果 Chrome 绑定到主进程）
- 直接启动 Chrome：`"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=18800 --user-data-dir=...`

### auto-start-services Hook 修复
- 旧：`execFile("openclaw", ["browser", "--browser-profile", "openclaw", "start"])` → 走 Gateway RPC 报错
- 新：直接启动 Chrome 进程，不通过 Gateway
  ```typescript
  execFile(CHROME_PATH, [
    `--remote-debugging-port=${BROWSER_PORT}`,
    `--user-data-dir=${BROWSER_PROFILE}`,
    "--no-first-run",
    "--no-default-browser-check",
  ], { detached: true, stdio: "ignore" });
  ```

---

## 2026-03-29: zhiku-ask.js MCP server 路径变更

### 错误
- 5 个 AI 平台（豆包/Kimi/GLM/千问/DeepSeek）的 MCP 工具全部报 `Unknown tool`
- zhiku-ask.js 调用时返回 `MCP error: bad request`

### 根因
- 今天 MCP server 从 `webauth-mcp` 迁移到独立 server（`doubao-mcp-server` 等）
- zhiku-ask.js 中：
  - DeepSeek：路径从 `webauth-mcp` 改到 `deepseek-mcp-server`，但工具名还是 `deepseek_chat`（无前缀）
  - 其他 4 个：工具名从 `doubao_chat` 等改为 `doubao_doubao_chat`（加了插件名前缀）
- 根本原因：`toolPrefix: true` 导致工具名变成 `{插件名}_{原始名}`，但 zhiku-ask.js 还在用旧的工具名

### 修复
- 改 `WEBAUTH_MCP` → 各平台独立 MCP server
- 工具名加前缀：`doubao_chat` → `doubao_doubao_chat`（除了 DeepSeek，DeepSeek 独立 server 无前缀）
- 注意：MCP 协议直接调用不走 OpenClaw 前缀机制，所以 server 注册的原始工具名才是正确的

### 教训
- 改了 MCP server 配置后要检查 `alsoAllow` 和 zhiku 脚本
- `toolPrefix` 对 `alsoAllow` 和 zhiku 脚本的影响不同

---

## 2026-03-29: context_after 永远为空的 bug

### 错误
- context window 功能中，`context_before` 正常返回，但 `context_after` 始终为空数组
- 即使确认 session 中有后续消息（离线测试能找到），search API 仍然返回空

### 根因
- `context_before` 和 `context_after` 在同一个 for 循环中收集
- text_store 按时间顺序排列，循环先遇到 before 消息
- `if len(ctx_b) >= 2: break` 提前跳出整个循环
- context_after 的消息排在 text_store 后面，永远没机会被遍历到

### 修复
```python
# 旧代码（bug）
for e2 in text_store:
    if -context_window <= diff < 0:
        ctx_b.append(...)
        if len(ctx_b) >= 2: break  # ← 跳出整个循环
    elif 0 <= diff <= context_window:
        ctx_a.append(...)

# 新代码（修复）
for e2 in text_store:
    if -context_window <= diff < 0:
        ctx_b.append(...)
    elif 0 <= diff <= context_window:
        ctx_a.append(...)
# 遍历完后截断
ctx_b = ctx_b[-2:]
ctx_a = ctx_a[:2]
```

### 教训
- 同一循环中收集两类数据并分别 break 是经典 bug 模式
- 正确做法：完整遍历后再截断/排序，不要在循环中 break
- server.py 中有两处相同代码（semantic 模式和 hybrid 模式），都要修
