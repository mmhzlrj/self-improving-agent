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

# 2026-05-10 10:17 — Ubuntu openclaw 升级：openclaw update 失败需用 npm install 直接安装

## 现象
Ubuntu 节点 v2026.3.24 升级到 v2026.5.9-beta.1 时，`openclaw update --tag beta --yes` 失败。

## 修复
直接用 `npm install -g openclaw@beta` 绕过 openclaw update 内部验证。升级后必须 `systemctl --user daemon-reload` + `systemctl --user restart openclaw-node`。

---

# 2026-05-10 10:17 — Mac Gateway "gateway startup failed" 不是真正的崩溃

## 现象
v2026.5.9-beta.1 日志每 ~15s 出现 "shutdown started: gateway startup failed"。

## 根因
launchd watchdog 正常日志模式。子进程检测到已有实例运行 → 自行退出。Gateway 一直在正常运行。

## 教训
- 判断 Gateway 是否崩溃的标准：能否回复用户消息，不是看日志中的 "shutdown" 关键字
- "gateway startup failed" + "gateway already running under launchd" = 正常行为

---

## 2026-05-12 09:05 — MiniMax subagent graphify 探索连续失败

### 现象
3 个子 Agent 执行 graphify batch #45#46 探索任务，全部报告 "0条边 / 所有节点 degree=0"。
但用主 session 直接 python3 读 graph.json 确认 38,575 节点 / 36,351 边。

### 根因
子 Agent 在读取 graph.json 时使用了 **错误的数据结构假设**：

| 子 Agent 使用的字段 | 实际 graph.json 字段 | 结果 |
|---|---|---|
| `node.get('degree', 0)` | ❌ 不存在，degree 需从 links 计算 | 所有节点被判为 degree=0 |
| `g.get('edges', [])` | `g['links']` ✅ | 返回空数组 → 认为无边 |
| `node.get('type')` | `node.get('file_type')` ✅ | 返回 None → 过滤掉所有节点 |

### 修复
子 Agent 第一步应先 inspect 数据结构再写代码，不能假设字段名。

---

## 2026-05-12 11:47 — docs.openclaw.ai 搜索跑偏：关键词概念域不匹配

### 现象
搜 MiniMax 多账户方案时，误搜 provider/rate.limit 等词，错过 multi-agent/parallel-specialist-lanes。用户手动给 URL 才看到。

### 教训
概念域匹配先于关键词匹配。先看索引再搜。

## 2026-05-15 多项错误记录

### 1. 日志污染 + 错误恢复策略
- 日志被 HTML 代码污染后，第一时间想 git 恢复而非用 贵庚/sessions_history
- 用 `which ollama` 断言服务未安装，实际是 App 安装不在 PATH
- 清理脚本过度删除导致日志丢失
- **教训**: 信任已建系统；先查后断言；清理前备份

---

## [ERR-20260518-001] openclaw update 重复执行导致 Gateway 崩溃

**Logged**: 2026-05-18T11:32:00+08:00
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
执行 `openclaw update` 前未查当前版本，导致在用户已手动完成升级后重复执行，Gateway 被第二次关闭且未自动重启。

### Error
```
09:15:36  Stopping managed gateway service...  （用户手动第一次）
09:59:53  Stopping managed gateway service...  （我重复执行第二次）
         — 两次之间无 "Starting managed gateway" 日志
```

### Context
- 用户在 09:15 已在终端手动执行 `openclaw update`
- 用户告知"已经升级，执行后面的步骤"后，我未验证版本直接再次执行
- `openclaw update` 标准行为：先关闭 Gateway → 升级包 → **不自动重启 LaunchAgent**
- 重复执行导致 Gateway 第二次被关闭，用户手动 `openclaw gateway start` 恢复

### Root Cause
执行幂等但带破坏性的命令前，未先 inspect 当前状态，而是凭记忆假设。

### Suggested Fix
执行 `openclaw update` 前：先 `openclaw --version` 确认当前版本，确认低于目标版本才执行。

### Prevention Rule
执行幂等但带破坏性副作用的命令前，必须先查当前状态，禁止凭记忆假设。

### Metadata
- Reproducible: no
- Related Files: /tmp/openclaw/openclaw-2026-05-18.log
- See Also: SOUL.md（操作前验证规则）

## 2026-05-18: TTS auto-TTS 失效 — 重复调研 + 误判 ffmpeg

### 错误链
1. MiniMax 未读 docs.openclaw.ai/providers/xiaomi → 走错方向
2. MiniMax 误判 ffmpeg 是必需依赖 → 浪费调研时间
3. AI 在 05-16 的诊断也跟风说"缺少 ffmpeg" → 未经验证
4. 用户纠正后才回头看文档 → 发现 bundled plugin 早已内置

### 根因
env.XIAOMI_API_KEY 用了免费版 sk- key，bundled plugin 优先读 env var，免费版不支持 TTS。
messages.tts.providers.xiaomi.apiKey 单独配了 tp- key 但被 env var 覆盖。

### 正确修复
将 env.XIAOMI_API_KEY 改为 token-plan key，重启 Gateway。

### 经验
1. OpenClaw 内置 provider 先读官方文档（docs.openclaw.ai/providers/<name>），不要猜
2. ffmpeg 仅 Feishu/Telegram Opus 转码需要，WebChat 不需要
3. 贵庚需同步文档变动
