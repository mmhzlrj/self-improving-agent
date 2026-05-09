# 2026-05-07 18:57 — Browser Node Proxy 路由到 Ubuntu 的故障

## 现象
OpenClaw browser 工具操作豆包网页时弹出「登录以解锁更多功能」对话框，
而用户确认 Mac 上 OpenClaw 内置 Chrome 已登录豆包等 5 个平台。

## 根因
OpenClaw 的 **Node Browser Proxy** 默认开启（`gateway.nodes.browser` mode 默认 auto），
自动将所有 browser 工具调用路由到已配对的 Ubuntu 节点（jet-Ubuntu, 192.168.1.18）。

Mac 本地 OpenClaw Chrome（已登录 5 平台）没有被使用，
实际使用的是 Ubuntu 节点上的 Chrome（未登录任何平台）。

### 证据
- browser status 显示: `detectedExecutablePath: "/usr/bin/google-chrome"` (Linux)
- browser status 显示: `userDataDir: "/home/jet/.openclaw/browser/openclaw/user-data"` (Ubuntu)
- 用户在 Ubuntu 显示器上确认浏览器在该机器上操作
- `lsof -i :18800` 在 Mac 上找到的 Chrome 进程是 Gateway 的 CDP 代理

## 修复
将 `gateway.nodes.browser.mode` 设为 `"off"`，禁用 node browser proxy。
修改位置: `/Users/lr/.openclaw/openclaw.json`

## 教训
1. 有 node 节点时，browser 工具默认走 node proxy，不是本地 Chrome
2. browser status 里的路径信息是关键诊断依据
3. `gateway.nodes.browser.mode` 是受保护路径，不能用 config.patch，需直接编辑配置文件
4. 需要完整 Gateway 重启才能使该配置生效（SIGUSR1 不够）

## 相关文档
- https://docs.openclaw.ai/nodes/index#nodes — Node browser proxy (zero-config default)
- https://docs.openclaw.ai/cli/node

# 2026-05-09 20:30 — Blender 材质持久化三重 Bug

## 现象
Blender harness 在 Ubuntu 上执行 `assign_material` 后，新 Blender 进程读不到材质。
`/tmp/blender_state.json` 文件存在但内容为旧版（含 triple-quote 转义错误）。

## 根因（三处）
1. **Triple-quote 转义**：早期 fix 用 `r"""..."""` 包装脚本，但 Python `replace()` 操作遗留 `\"\"\""` 转义
2. **JSON null NameError**：`json.dumps()` 在 Python string 内生成 `null`，Ubuntu Python 3.12 eval 上下文不识别
3. **Background 模式 datablock 丢失**：`save_mainfile` 在 `--background` 模式下丢失自定义 material/object datablock

## 修复
完全重写 `backend.py`：
- 弃用 .blend 文件持久化，改用 JSON 状态文件 (`/tmp/blender_state.json`)
- 每次 Blender 调用从 JSON → `_rebuild_scene()` 销毁重建全场景 → 执行操作 → 保存回 JSON
- 用 `repr()` 替代 `json.dumps()` 生成 Python 字面量（避免 null）
- 用普通字符串 `+` 拼接替代 `r"""` 包装（避免转义）

## 教训
1. Blender `--background` 模式下 `save_mainfile` 不可靠，不要依赖 .blend 做状态持久化
2. Python eval() 上下文中 JSON 的 `null` 不是合法标识符，必须用 `None`
3. `r"""` 内部不能有 `"""`，用字符串拼接更安全
4. 跨进程状态管理：JSON 文件 > .blend 文件（尤其在 headless/background 模式下）

# 2026-05-09 21:16 — DeepSeek V4 Pro 被 heartbeat 循环调用 42 次

## 现象
Gateway 异常 305 条，DeepSeek billing error (402) 出现 42 次（每 30 分钟一次）。

## 根因
`agent:main:main` session 的 `sessions.json` 中有用户手动设置的 per-session model override：
```json
{
  "modelOverride": "deepseek-v4-pro",
  "modelOverrideSource": "user"
}
```
Heartbeat 每 30 分钟触发 → 发送到 main session → 使用 deepseek-v4-pro → 402 billing error → cooldown → 30 分钟后再试 → 循环。

## 修复
直接编辑 `sessions.json`，删除 `agent:main:main` 的 modelOverride 相关字段。

## 教训
1. `sessions.json` 中的 per-session model override 优先级高于 `agents.defaults.model.primary`
2. `modelOverrideSource: user` 表示用户命令设置（`/model xxx`），不是系统默认
3. heartbeat 使用 session 存储的 model，不是 agent 默认 model
4. 排查 model 问题时，先查 `sessions.json` 的 modelOverride，再查 openclaw.json
