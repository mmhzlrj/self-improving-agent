# Chrome Debug Profile 管理规范

## 经验教训

### 2026-03-22 重大失误

**问题**：Gateway 重启前没有确认 Chrome 调试端口状态，直接杀掉所有 Chrome 窗口，导致：
1. 用户正常浏览的网页全部丢失
2. Chrome-Debug-Profile 里 5 个 AI 页面的登录状态全部丢失
3. 创建了新的 `/tmp/chrome-debug` profile 而不是使用已有的正确 profile

**错误行为**：
- 用 `osascript -e 'quit app "Google Chrome"'` 杀掉所有 Chrome 窗口（一刀切）
- 创建新的 `--user-data-dir=/tmp/chrome-debug` 而不是用已有的 `Chrome-Debug-Profile`
- 没有精细化控制，只关需要关的窗口
- 没有先记录错误就盲目操作

**正确做法**：
1. Gateway 重启前，先确认 Chrome 调试端口状态
2. 如果需要重启 Chrome，用已有的正确 profile 目录
3. 使用 `--user-data-dir="$HOME/Library/Application Support/Google/Chrome/Chrome-Debug-Profile"` 等已有 profile
4. 如果必须用新 profile，先问用户

## Chrome Profile 路径

| Profile 名称 | 路径 | 用途 |
|-------------|------|------|
| `Chrome-Debug-Profile` | `~/Library/Application Support/Google/Chrome/Chrome-Debug-Profile` | 5个AI页面（DeepSeek/Kimi/Doubao/GLM/Qwen） |
| `Chrome-OpenClaw-Debug` | `~/Library/Application Support/Google/Chrome/Chrome-OpenClaw-Debug` | OpenClaw Web |

## 启动命令

```bash
# Chrome-Debug-Profile（5个AI页面），调试端口 9223
nohup /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9223 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome/Chrome-Debug-Profile" \
  2>/dev/null &

# Chrome-OpenClaw-Debug（OpenClaw Web），调试端口 9224
nohup /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9224 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome/Chrome-OpenClaw-Debug" \
  2>/dev/null &
```

## webauth MCP 端口配置

- `webauth-mcp/server.mjs` 硬编码 `CDP_PORT = 9223`
- 连接的是 Chrome-Debug-Profile（5个AI页面）
- Chrome-OpenClaw-Debug (9224) 供 OpenClaw Browser Relay 使用

## 重要原则

1. **不动用户的 Chrome** — Gateway 重启前，先确认调试端口是否存活
2. **用已有 profile** — 不创建新的 `--user-data-dir`
3. **精细化控制** — 只关需要重启的 Chrome 实例，不杀所有窗口
4. **先问用户** — 如果必须重启 Chrome，先说明影响并获得同意

## 2026-03-22 更新：Gateway重启频率记录

今日 Gateway 重启了 ~10+ 次，每次都被杀 Chrome。这说明：
- **webauth-mcp 每次代码修改都要重启 Gateway**
- **每次重启都要手动重开 Chrome**
- 教训：尽量攒多个修改再一次性重启，减少循环
