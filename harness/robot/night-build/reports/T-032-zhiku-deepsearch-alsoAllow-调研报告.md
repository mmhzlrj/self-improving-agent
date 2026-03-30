# T-032 调研报告：zhiku/deepsearch MCP 工具注册到 alsoAllow

## 1. zhiku/deepsearch 创建历史时间线

### deep-research Skill
| 日期 | 事件 |
|------|------|
| 2026-03-24 | ff323dd: feat(deep-research): 集成zhiku+tavily+web_fetch多工具并行调研 |
| 2026-03-24 | 00e9203: 新增deep-research使用规范、SOUL.md行为约束、exec-approvals白名单配置 |
| 2026-03-29 | 322607a: feat: 新增 deep-research 工具检查 SOP，详细规范检查流程 |

### zhiku Skill
| 日期 | 事件 |
|------|------|
| 2026-03-11 | 首次引入多平台并行搜索概念（Kimi/GLM/Qwen分别测试） |
| 2026-03-12 | zhiku-s1/s2/s3 并行方式被单脚本替代（`zhiku-ask.js`） |
| 2026-03-22 | webauth_mcp 修复：alsoAllow 工具名加 `webauth_` 前缀 |
| 2026-03-29 | 322607a: 夜间任务规划 + zhiku修复 |

### 当前架构（SSE+MCP adapter）

```
用户问题
    │
    ├── zhiku-ask.js（主脚本）
    │   ├── mcpCall(deepseek-mcp-server) → deepseek_deepseek_chat
    │   ├── mcpCall(kimi-mcp-server)     → kimi_kimi_chat
    │   ├── mcpCall(doubao-mcp-server)  → doubao_doubao_chat
    │   ├── mcpCall(glm-mcp-server)     → glm_glm_chat
    │   └── mcpCall(qwen-mcp-server)    → qwen_qwen_chat
    │
    ▼
  各自 MCP Server → 读取 cookie → 构造 SSE 请求 → 模拟浏览器发送
  拦截 SSE 流 → 提取参数 → 返回结果
```

**关键文件：**
- 主脚本：`~/.openclaw/workspace/skills/zhiku/scripts/zhiku-ask.js`
- 各平台 MCP Server：每个独立 stdio JSON-RPC server
- MCP Adapter：`~/.openclaw/extensions/openclaw-mcp-adapter/index.ts`

---

## 2. alsoAllow 注册现状

### 当前已注册的 MCP 工具（via openclaw-mcp-adapter）

| 服务器名 | 工具名（toolPrefix=true） | alsoAllow 状态 | 说明 |
|---------|--------------------------|----------------|------|
| deepseek | `deepseek_deepseek_chat` | ✅ 已注册 | 读取本地 creds JSON |
| doubao | `doubao_doubao_chat` | ✅ 已注册 | webauth-mcp（Chrome cookie）|
| kimi | `kimi_kimi_chat` | ❌ 未注册 | 需要添加到 alsoAllow |
| glm | `glm_glm_chat` | ❌ 未注册 | 需要添加到 alsoAllow |
| qwen | `qwen_qwen_chat` | ❌ 未注册 | 需要添加到 alsoAllow |
| webauth | `webauth_doubao_chat` | ❌ 未注册 | 实际上只暴露 doubao_chat |
| playwright | `playwright_*` | ❌ 未注册 | 不需要 |
| cdp | `cdp_*` | ❌ 未注册 | 不需要 |

### alsoAllow 当前配置

```json
// ~/.openclaw/openclaw.json
"alsoAllow": [
  "doubao_doubao_chat",
  "deepseek_deepseek_chat",
  "kimi_kimi_chat",
  "qwen_qwen_chat",
  "glm_glm_chat"
]
```

### 工具名对照表

| Skill | zhiku-ask.js 中的调用名 | alsoAllow 名 |
|-------|------------------------|-------------|
| DeepSeek | `deepseek_deepseek_chat` | ✅ 已注册 |
| Doubao | `doubao_doubao_chat` | ✅ 已注册 |
| Kimi | `kimi_kimi_chat` | ✅ 已注册 |
| GLM | `glm_glm_chat` | ✅ 已注册 |
| Qwen | `qwen_qwen_chat` | ✅ 已注册 |

---

## 3. 用户想要的架构

**当前架构（SSE+MCP adapter）：**
- zhiku-ask.js 通过 stdio JSON-RPC 启动各 MCP server
- 每个 MCP server 读取 cookie → 构造 SSE 请求 → 模拟浏览器
- 问题：依赖 Playwright/Chrome CDP，每次调用都要启动进程

**目标架构：**
- 工具已通过 openclaw-mcp-adapter 注册到 Gateway
- 大模型直接调用 `deepseek_deepseek_chat` 等工具
- 无需 zhiku-ask.js 派生进程，纯后台 API 调用
- 通过 alsoAllow 授权 main agent 使用

---

## 4. 转为 alsoAllow 工具的具体步骤

### 步骤 1：验证 MCP 工具已正确注册

```bash
# 检查 openclaw-mcp-adapter 是否连接了所有 5 个平台
# 查看 Gateway 日志中是否有 "Registered: xxx" 字样
openclaw gateway logs | grep -i "Registered\|mcp-adapter"
```

### 步骤 2：更新 alsoAllow 配置

修改 `~/.openclaw/openclaw.json` 中的 agents.list[0].tools.alsoAllow：

```json
"alsoAllow": [
  "doubao_doubao_chat",
  "deepseek_deepseek_chat",
  "kimi_kimi_chat",
  "qwen_qwen_chat",
  "glm_glm_chat"
]
```

**注意：** 目前配置已是完整 5 个平台，说明已注册。

### 步骤 3：重启 Gateway 使 alsoAllow 生效

```bash
openclaw gateway restart
```

### 步骤 4：验证工具可被 main agent 直接调用

```bash
# 测试单个平台
openclaw tools call deepseek_deepseek_chat '{"message": "1+1等于几"}'
openclaw tools call doubao_doubao_chat '{"message": "你好"}'
```

### 步骤 5（可选）：改造 zhiku-ask.js

当前 zhiku-ask.js 通过 `spawn` 派生独立进程调用各 MCP server。

**改造方向：** 改为直接调用已注册的 MCP 工具（通过 OpenClaw API 或 MCP JSON-RPC）。

**但注意：** zhiku-ask.js 目前用的是 `mcpCall(scriptPath, ...)` 启动独立 stdio 进程。如果要让 main agent 直接调用，需要：
1. 删除 zhiku-ask.js 中的 `mcpCall` 逻辑
2. 改为调用 `deepseek_deepseek_chat` 等已注册工具（但这需要通过 API 或 Agent 上下文）

---

## 5. 需要修改的代码文件清单

| 文件 | 修改内容 | 风险 |
|------|---------|------|
| `~/.openclaw/openclaw.json` | alsoAllow 已完整，无需修改 | 低 |
| `~/.openclaw/extensions/webauth-mcp/server.mjs` | 只暴露 `doubao_chat`，需要添加 kimi/glm/qwen | 高 |
| `~/.openclaw/workspace/skills/zhiku/scripts/zhiku-ask.js` | 改造为调用已注册的 MCP 工具（而非派生进程） | 中 |
| `~/.openclaw/extensions/openclaw-mcp-adapter/index.ts` | toolPrefix: true 配置（已确认） | 低 |

### 关键发现：webauth-mcp 只暴露了 doubao_chat

```javascript
// server.mjs line 138
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: 'doubao_chat',  // ← 只暴露了 doubao！
    description: '豆包 AI 对话...',
    inputSchema: { ... }
  }]
}));
```

**这意味着：**
- `webauth_kimi_chat`、`webauth_glm_chat`、`webauth_qwen_chat` 是**通过各自的独立 MCP server** 暴露的（kimi-mcp-server, glm-mcp-server, qwen-mcp-server）
- 而非通过 webauth-mcp
- 5 个平台的 MCP server 都已在 `plugins.entries.openclaw-mcp-adapter.config.servers` 中配置

---

## 6. 每个步骤的风险点

### 风险 1：alsoAllow 配置已完整，但工具可能未正确注册

- **风险：** Gateway 启动时 MCP adapter 连接失败
- **检查：** `openclaw gateway logs | grep mcp-adapter`
- **应对：** 重启 Gateway，重新连接

### 风险 2：deepseek-mcp-server 依赖 PoW 解算

- **风险：** deepseek_deepseek_chat 需要读取 `creds-18800-full.json`，cookie 过期会导致失败
- **检查：** 确认文件存在且 cookie 有效
- **应对：** 重新登录 DeepSeek 网页更新 cookie

### 风险 3：webauth 平台（Kimi/GLM/Qwen）cookie 过期

- **风险：** Chrome CDP 仍连接正常，但 cookie 过期导致 API 返回空
- **检查：** 调用后返回空或错误信息
- **应对：** 刷新 Chrome 中对应平台页面，重新获取 cookie

### 风险 4：zhiku-ask.js 改造后兼容性问题

- **风险：** 如果改造为调用已注册工具，需要确保 OpenClaw API 支持
- **当前状态：** zhiku-ask.js 通过 stdio JSON-RPC 直接调用各 MCP server，与 Gateway 中的注册是**独立的**
- **结论：** zhiku-ask.js 可以继续独立运行，也可以改为调用已注册工具

### 风险 5：toolPrefix: true 导致工具名前缀

- **已确认：** 所有工具名都带平台前缀（如 `deepseek_deepseek_chat`）
- **已正确配置：** alsoAllow 中工具名都带前缀

---

## 7. 关键发现：MCP 适配器连接问题

### 历史成功案例（2026-03-29）

昨天 Gateway 启动时，MCP 适配器成功注册了以下工具：

| 工具 | 状态 | 备注 |
|------|------|------|
| `doubao_doubao_chat` | ✅ 已注册 | |
| `glm_glm_chat` | ✅ 已注册 | |
| `kimi_kimi_chat` | ✅ 已注册 | |
| `qwen_qwen_chat` | ✅ 已注册 | |
| `deepseek_deepseek_chat` | ❌ **连接失败** | `McpError: Connection closed` |
| `playwright_*` | ✅ 已注册 | |

### 当前问题（2026-03-30）

今天 Gateway 已重启 3 次（10:47, 10:50, 10:53），但**日志中完全没有 MCP 适配器的注册消息**。可能原因：

1. MCP 适配器的 `console.log` 输出到 stderr，不走结构化日志
2. MCP server 进程启动后立即崩溃（Connection closed）
3. 昨天 deepseek-mcp-server 就已失败，今天可能更严重

**验证方法：**
```bash
# 直接测试 deepseek MCP server
node ~/.openclaw/extensions/deepseek-mcp-server/deepseek-mcp-server.mjs
# 如果立即退出或报错，说明 server 本身有问题
```

---

## 8. 结论与建议

### 当前状态

1. **alsoAllow 已完整配置**：5 个平台工具名都已在列表中
2. **MCP 适配器工具注册有问题**：今天 Gateway 重启后未看到注册日志
3. **deepseek-mcp-server 历史上有连接失败记录**
4. **zhiku-ask.js 是独立路径**：不依赖 MCP 适配器，通过 stdio JSON-RPC 直接调用各 MCP server

### 立即可执行的诊断

```bash
# 1. 检查 MCP server 是否可独立运行
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  node ~/.openclaw/extensions/deepseek-mcp-server/deepseek-mcp-server.mjs 2>&1 | head -5

# 2. 检查 Gateway 最新状态
tail -50 /tmp/openclaw/openclaw-2026-03-30.log | grep -i "mcp\|registered\|failed" | tail -10

# 3. 检查 Chrome CDP 是否运行
curl -s http://127.0.0.1:18800/json/version | head -3
```

### 用户需求理解

**目标：** 大模型在后台直接调用工具，无需 Playwright/前端交互

**现状分析：**
- `deepseek_deepseek_chat` — 通过 PoW + 本地 cookie 发 API，纯后台 ✅（历史上有连接失败问题）
- `doubao_doubao_chat` 等 — 通过 webauth-mcp 连接 Chrome CDP，需要 Chrome 运行 ❌

**zhiku-ask.js 的作用：**
- 它启动独立的 MCP server 进程（不经过 Gateway 注册）
- 调用方式：`mcpCall(scriptPath, toolName, args)`
- 这是**独立于 alsoAllow 的另一条路径**

### 建议执行步骤

**Step 1: 诊断 MCP server 是否可运行**
- 单独测试每个 MCP server 的 tools/list
- 确认哪个 server 坏了

**Step 2: 修复 MCP server**
- deepseek: 检查 PoW solver 和 cookie 有效期
- doubao/kimi/glm/qwen: 检查 Chrome CDP 连接（端口 18800）

**Step 3: 重启 Gateway 确认工具注册**
- 检查日志中是否出现 `Registered: xxx_chat`

**Step 4: 验证 alsoAllow 工具可被大模型调用**
- 通过 Agent 对话测试直接调用工具

---

## 附录：关键配置文件

### MCP Adapter Config（~/.openclaw/openclaw.json）

```json
"openclaw-mcp-adapter": {
  "enabled": true,
  "config": {
    "servers": [
      { "name": "deepseek", "transport": "stdio", "command": "node", "args": ["deepseek-mcp-server.mjs"] },
      { "name": "doubao", "transport": "stdio", "command": "node", "args": ["doubao-mcp-server.mjs"] },
      { "name": "glm", "transport": "stdio", "command": "node", "args": ["glm-mcp-server.mjs"] },
      { "name": "kimi", "transport": "stdio", "command": "node", "args": ["kimi-mcp-server.mjs"] },
      { "name": "qwen", "transport": "stdio", "command": "node", "args": ["qwen-mcp-server.mjs"] },
      { "name": "webauth", "transport": "stdio", "command": "node", "args": ["webauth-mcp/server.mjs"] }
    ],
    "toolPrefix": true
  }
}
```

### main agent alsoAllow

```json
"id": "main",
"tools": {
  "profile": "coding",
  "alsoAllow": [
    "doubao_doubao_chat",
    "deepseek_deepseek_chat",
    "kimi_kimi_chat",
    "qwen_qwen_chat",
    "glm_glm_chat"
  ]
}
```

---

*报告生成时间：2026-03-30 11:55 GMT+8*
