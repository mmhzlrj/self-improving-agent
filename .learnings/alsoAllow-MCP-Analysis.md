# alsoAllow + MCP 工具注册问题 - 完整分析报告

> 日期：2026-03-31
> 状态：✅ 已解决

## 问题描述

MCP 工具（doubao_doubao_chat 等）通过 openclaw-mcp-adapter 注册后，subagent 工具列表中不可见。

## 症状

1. Gateway 启动时警告：`tools: agents.main.tools.allow allowlist contains unknown entries (doubao_doubao_chat, deepseek_deepseek_chat, ...)`
2. Subagent 调用 alsoAllow 工具时报错：工具不存在
3. zhiku-ask 脚本（直接 stdio 调用 MCP）正常工作

## 根因分析

### 源码级分析

**Pipeline 执行顺序**（applyToolPolicyPipeline）：
```
Step 1: profilePolicy（profileAlsoAllow = alsoAllow工具）
    ↓ stripPluginOnlyAllowlist
    → 剥离 alsoAllow 未知工具
    → 如果还有 core entries → 剩余 allowlist 有效（block 非列表工具）
    → 如果无 core entries → allow=void → 全部允许

Step 2: globalPolicy（无 alsoAllow）
Step 3: agentPolicy（alsoAllow 未知工具 → 警告 + 剥离）
Step 4: agentProviderPolicy
Step 5+: groupPolicy, sandboxPolicy, subagentPolicy
```

**关键代码**（auth-profiles-B5ypC5S-.js, tool-policy-DG7GGbxQ.js）：
- `stripPluginOnlyAllowlist()`：剥离不在 core/plugin 列表的 allowlist 条目
- `mergeAlsoAllowPolicy()`：合并 alsoAllow 到 allow
- `expandPluginGroups()`：展开 group:* 条目
- `filterToolsByPolicy()`：按最终 allowlist 过滤工具

**alsoAllow 工具的命运**：
- 不是 core tool → 不是 plugin tool → 被标记为 "unknown"
- 剥离后：如果 allowlist 还有其他 core entries → 保留 allowlist → MCP 工具被 block
- 剥离后：如果 allowlist 无其他 entries → allow=void → 全部允许

### 配置级别问题

**错误配置**（无效）：
```json
{
  "agents": {
    "list": [{
      "tools": {
        "alsoAllow": ["doubao_doubao_chat", ...],
        "profile": "coding"
      }
    }]
  }
}
```
- alsoAllow 在 agent 级别
- profile=coding → coding profile 有 core tools allowlist
- 合并后：alsoAllow 工具被剥离，但 core entries 还在 → allowlist 保留 → MCP 工具被 block

**正确配置**：
```json
{
  "tools": {
    "profile": "full",
    "alsoAllow": ["doubao_doubao_chat", ...]
  }
}
```
- alsoAllow 在 global 级别
- profile=full → 无 core tools allowlist
- 合并后：alsoAllow 工具被剥离，但无 core entries → allow=void → 全部允许

## 解决方案

### 最终配置

```json
{
  "tools": {
    "profile": "full",
    "alsoAllow": [
      "doubao_doubao_chat",
      "deepseek_deepseek_chat",
      "kimi_kimi_chat",
      "qwen_qwen_chat",
      "glm_glm_chat"
    ]
  },
  "agents": {
    "list": [{
      "tools": {
        "profile": "full"
      }
    }]
  }
}
```

### 验证方法

1. `zhiku-ask.js "问题"` - 验证 MCP server 正常工作
2. Subagent 无法使用 alsoAllow 工具（正常，alsoAllow 只给 main agent）

## 技术细节

### 工具名格式
- MCP server 工具名：`doubao_chat`
- Adapter 注册名（toolPrefix=true）：`doubao_doubao_chat`

### MCP Server 列表
| 服务器 | 工具名 | 通信方式 |
|--------|--------|---------|
| doubao | doubao_chat | Playwright + CDP |
| kimi | kimi_chat | Playwright + CDP |
| glm | glm_chat | Playwright + CDP |
| qwen | qwen_chat | Playwright + CDP |
| deepseek | deepseek_chat | 独立 fetch API |

### Pipeline 步骤详解

```
resolveEffectiveToolPolicy()
  ├─ profilePolicy = resolveToolProfilePolicy("full") → {}
  ├─ profileAlsoAllow = resolveExplicitProfileAlsoAllow(agentTools) | resolveImplicitProfileAlsoAllow()
  ├─ mergeAlsoAllowPolicy({}, profileAlsoAllow) → allow=void (因为 full 无 core tools)
  ├─ expandPluginGroups({}, pluginGroups)
  ├─ filterToolsByPolicy(allTools, allow=void) → 全部工具
```

## 经验教训

1. **alsoAllow 必须放在 global 级别**（`tools` 下），不能放在 agent 级别
2. **profile=full 解锁所有工具**：`full: {}` = 无 core tools allowlist
3. **"unknown entries" 警告是正常的**：不代表功能失效
4. **subagent 不能用 alsoAllow 工具**：alsoAllow 是 main agent 专属
5. **zhiku-ask 走不同路径**：直接 stdio JSON-RPC 调用 MCP server

## 修复时间线

| 时间 | 事件 |
|------|------|
| 20:27 | 发现 alsoAllow 在根级别报错（Unrecognized key） |
| 20:35 | 移到 agents.list[0].tools.alsoAllow，profile=coding |
| 20:38 | Gateway 重启，警告还在 |
| 21:08 | 又重启，警告持续 |
| 21:50 | 开始深入分析源码 |
| 22:15 | 发现 profile=coding 导致 alsoAllow 工具被 block |
| 22:20 | 改用 profile=full |
| 22:28 | Gateway 重启，警告变为 tools.allow |
| 22:45 | 完成记录 |

## 相关文件

- `~/.openclaw/openclaw.json` - 主配置
- `~/.openclaw/extensions/openclaw-mcp-adapter/index.ts` - MCP adapter
- `~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/dist/auth-profiles-B5ypC5S-.js` - 工具策略核心
- `~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/dist/tool-policy-DG7GGbxQ.js` - 工具策略工具函数
- `~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/dist/tool-policy-match-qwLsTvyG.js` - 工具匹配逻辑
