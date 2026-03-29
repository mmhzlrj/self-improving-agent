# OpenClaw 2026.3.28 升级后功能验证

## 任务1：验证 node.pending 功能

**状态：❌ 未找到**

搜索了 `docs/nodes/` 和 `dist/` 目录下所有 JS 文件，没有找到 `node.pending`、`enqueue`、`drain` 等 API。

`runtime-schema-Z7mwE1O9.js` 中只有 `pendingBytes` / `pendingMessages` 用于 session compaction tracking，与 node API 无关。

**结论：** 这个功能不存在，或尚未实现。

---

## 任务2：配置 Per-Model Cooldowns

**状态：✅ 已默认启用（无需配置）**

源码证据：
- `auth-profiles-B5ypC5S-.js` 第 185510-185516 行：存在 `cooldownModel` 字段，说明 cooldown 是按模型独立计算的
- `runtime-schema-Z7mwE1O9.js` 第 1380 行：schema 中有 `cooldowns` 配置节
- 429 时 `cooldownModel` 被设为当前 model ID，下次请求只对 cooldown 模型跳过

**当前模型配置：**
```json
"primary": "minimax/MiniMax-M2.7"  // 默认
"minimax/MiniMax-M2.7": {}        // fallback
```

**操作：** 无需任何配置，默认已启用。

---

## 任务3：研究 before_tool_call requireApproval

**状态：✅ 功能存在，文档完整**

**API 位置：** `docs/automation/hooks.md` 和 `docs/concepts/agent-loop.md`

**before_tool_call 返回字段：**
- `params` — 覆盖工具参数（与原始参数合并）
- `block` — 设为 `true` 阻止工具调用（优先级最高）
- `blockReason` — 阻止时显示给 agent 的原因
- `requireApproval` — 暂停执行，等待用户通过 channel 批准

**requireApproval 结构：**
```typescript
{
  title: "Sensitive operation",
  description: "This tool call modifies production data",
  severity: "info" | "warning" | "critical",
  timeoutMs: 120000,
  timeoutBehavior: "allow" | "deny",
  onResolution: async (decision) => {
    // "allow-once", "allow-always", "deny", "timeout", "cancelled"
  }
}
```

**关键机制：**
- `block` 优先级高于 `requireApproval`（同时设置时 block 生效）
- 如果 gateway 不支持 plugin approval，降级为 soft block
- `onResolution` 回调在 plugin 进程内同步调用（非 gateway），用于持久化决策或更新缓存

**示例文件：** `~/.openclaw/workspace/docs/before_tool_call-example.md`

---

## 任务4：验证 MiniMax 图片生成

**状态：⚠️ 部分可用，需检查 provider 配置**

**发现：**
1. `minimax-portal` provider 已存在：`dist/extensions/minimax/index.js` 第 19 行定义了 `PORTAL_PROVIDER_ID = "minimax-portal"`
2. 图片生成 provider 已实现：`dist/extensions/minimax/image-generation-provider.js` 有 `buildMinimaxPortalImageGenerationProvider`
3. 当前配置的模型：

| Provider | 模型 | input types |
|----------|------|-------------|
| minimax-cn | MiniMax-M2.7 | text, image |
| minimax-cn | MiniMax-M2.5 | text, image |
| minim | MiniMax-M2.5 | text |

**结论：**
- M2.7 在 `minimax-cn` provider 下支持图片输入
- `minimax-portal` provider 已注册但需要 OAuth 配置
- 当前配置没有使用 `minimax-portal` provider
- 图片生成（`image_generate` 工具）需要检查 `models.json` 中 provider 的 `imageGenerate` capability

**操作：** 检查 `~/.openclaw/models.json` 中各 provider 的图片生成 capability 配置。

---

## 任务5：搜索 6 个垂直领域 Agent

**状态：❌ 未找到任何这些 Agent**

搜索了：
- `dist/` 下所有 JS 文件（含控制台 UI 资源）
- `dist/extensions/acpx/` 目录
- `agents-BPOxZDBr.js`（Control UI agents 面板）
- 源码中 grep "CMS Developer" "Filament Optimization" 等关键词

**结果：**
- 没有找到 CMS Developer
- 没有找到 Filament Optimization Specialist
- 没有找到 Video Optimization Specialist
- 没有找到 Civil Engineer
- 没有找到 China Market Localization Strategist
- 没有找到 Email Intelligence Engineer

**结论：** 这些 Agent 可能是在另一个分支/版本中引入的，或命名方式不同。搜索了 agentId、specialist、developer、engineer 等通用关键词也未发现对应条目。

---

## 总结

| 功能 | 状态 | 说明 |
|------|------|------|
| node.pending | ❌ 不存在 | 功能未实现或已更名 |
| Per-Model Cooldowns | ✅ 默认启用 | 无需配置 |
| before_tool_call requireApproval | ✅ 可用 | 文档完整，示例已生成 |
| MiniMax 图片生成 | ⚠️ 部分可用 | M2.7 支持图片输入，portal provider 已注册 |
| 垂直领域 Agent (6个) | ❌ 未找到 | 可能版本不同或尚未引入 |

---
*生成于 2026-03-29 18:10 GMT+8*