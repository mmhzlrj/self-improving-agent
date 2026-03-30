# MCP Server 诊断报告

**诊断时间**：2026-03-30 13:22 CST  
**诊断范围**：doubao / kimi / glm / qwen（跳过 deepseek）  
**诊断方式**：tools/list + tools/call ping 测试 + mcporter 列表 + 进程检查

---

## 1. alsoAllow 注册的工具（主要来源）

配置位置：`~/.openclaw/openclaw.json` → `agents.list[0]`（id=main, profile=coding）

| 工具名 | 对应 MCP Server | 状态 |
|--------|-----------------|------|
| `doubao_doubao_chat` | doubao | ✅ 已注册 |
| `kimi_kimi_chat` | kimi | ✅ 已注册 |
| `qwen_qwen_chat` | qwen | ✅ 已注册 |
| `glm_glm_chat` | glm | ✅ 已注册 |
| `deepseek_deepseek_chat` | deepseek | ⏭️ 跳过（服务器端问题） |

**注意**：`alsoAllow` 里用的是**全名**（带平台前缀），实际 MCP server 的 tool name 是**不带前缀**的（如 `doubao_chat`）。这是 openclaw-mcp-adapter 的 name mangling 机制，调用时会自动映射。

---

## 2. MCP Server 进程状态

| Server | 进程数 | 状态 |
|--------|--------|------|
| doubao | 1 | ✅ 运行中 |
| kimi | 1 | ✅ 运行中 |
| glm | **2** | ⚠️ 重复进程 |
| qwen | 1 | ✅ 运行中 |

**问题发现**：`glm-mcp-server` 有 **2 个重复进程**，其他均为单实例。

---

## 3. mcporter 可见性

`mcporter list` 默认配置的 6 个 server：

| Server | 状态 | 原因 |
|--------|------|------|
| xiaohongshu | ❌ offline | localhost:18060 无响应 |
| douyin | ❌ offline | localhost:18070 无响应 |
| linkedin | ❌ offline | localhost:3000 无响应 |
| exa | ✅ online | 3 tools, 1.5s |
| chrome-devtools | ✅ online | 29 tools, 3.8s |
| playwright | ❌ offline | npx stdio 超时 |

**说明**：doubao/kimi/glm/qwen 这 4 个 AI 平台 MCP server **不在 mcporter 的 config/mcporter.json 里注册**，它们由 `openclaw-mcp-adapter`（`plugins.entries.openclaw-mcp-adapter.config.servers[]`）管理，所以 mcporter 看不到。这是正常架构，不是问题。

---

## 4. 功能性测试结果

每个 server 执行了 `tools/list` 和 `tools/call` ping 测试：

| Server | tools/list | chat ping | 功能状态 |
|--------|-----------|-----------|---------|
| doubao | ✅ 1 tool | ✅ 返回 OK | ✅ 正常 |
| kimi | ✅ 1 tool | ✅ 返回 OK | ✅ 正常 |
| glm | ✅ 1 tool | ✅ 返回 OK | ✅ 正常 |
| qwen | ✅ 1 tool | ✅ 返回 OK | ✅ 正常 |

---

## 5. Chrome 调试端口

- **URL**：`http://127.0.0.1:18800/json/list`
- **Tab 数量**：8 个
- **相关 Tab**：
  - DeepSeek（已登录）
  - Kimi AI 官网（K2.5 上线）
  - 智谱清言
  - 豆包
  - Qwen Chat
- Chrome CDP 连接：✅ 正常

---

## 6. openclaw-mcp-adapter 注册的所有 Server

共 10 个 stdio server：

| 名称 | transport | 状态 |
|------|-----------|------|
| deepseek | stdio | ⏭️ 跳过 |
| doubao | stdio | ✅ 正常 |
| glm | stdio | ⚠️ 重复进程 |
| kimi | stdio | ✅ 正常 |
| qwen | stdio | ✅ 正常 |
| glm（第2个） | stdio | ⚠️ 重复 |
| playwright | stdio | 待测 |
| cdp | stdio | 待测 |
| webauth | stdio | 待测 |
| dashboard | python3 stdio | 待测 |

---

## 7. 问题汇总

### 🔴 问题1：glm-mcp-server 重复进程（需 Gateway 重启）

**现象**：ps 显示 glm-mcp-server 有 2 个进程在运行。

**原因**：Gateway 重启时可能没有正确清理旧进程，导致 MCP server 被启动了两次。

**修复步骤**：
1. 确认用户当前是否正在使用任何 MCP 工具
2. 如果没有 → 执行 `openclaw gateway restart`（需用户确认）
3. 重启后验证：`ps aux | grep glm-mcp-server` 确认只剩 1 个进程

### ✅ 问题2（无问题）：glm 有2条注册配置

`openclaw-mcp-adapter.config.servers[]` 里有两条 glm 配置（同一个文件被注册了两次），这是配置重复，不是导致重复进程的原因，但建议清理。

---

## 8. 修复建议

### 立即修复（Gateway 重启）

```bash
# 1. 确认 glm 重复进程
ps aux | grep glm-mcp-server | grep -v grep

# 2. 重启 Gateway（需用户确认）
openclaw gateway restart

# 3. 验证
ps aux | grep glm-mcp-server | grep -v grep
# 应该只剩 1 个
```

### 配置清理（可选）

检查 `openclaw.json` 中 `plugins.entries.openclaw-mcp-adapter.config.servers` 是否 glm 被写了两次，删除重复条目。

### 注意

- deepseek MCP server 崩溃是**服务器端问题**，本地无法修复
- 其余 4 个（doubao/kimi/glm/qwen）**本地均正常**
- 豆包、Qwen 等浏览器 Tab 需要**保持打开状态**才能正常使用
