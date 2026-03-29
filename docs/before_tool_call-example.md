# before_tool_call requireApproval 示例

> 来源：`docs/automation/hooks.md` + 源码分析

## 功能概述

`before_tool_call` 是 Plugin Hook API 的一部分，在每次工具调用**之前**运行。Plugin 可以：
1. 修改工具参数（`params`）
2. 阻止工具调用（`block`）
3. 请求用户批准（`requireApproval`）

## 返回值结构

```typescript
{
  params?: object,        // 覆盖工具参数（与原始参数合并）
  block?: boolean,        // 阻止工具调用（优先级最高）
  blockReason?: string,   // 阻止原因，显示给 agent
  requireApproval?: {     // 请求用户批准
    title: string,
    description: string,
    severity: "info" | "warning" | "critical",
    timeoutMs?: number,   // 默认 120000ms
    timeoutBehavior?: "allow" | "deny",  // 默认 "deny"
    onResolution?: (decision: string) => Promise<void>
    // decision: "allow-once" | "allow-always" | "deny" | "timeout" | "cancelled"
  }
}
```

## 优先级规则

- **`block: true`** > `requireApproval`（同时设置时，block 生效，不触发审批流程）
- 如果 gateway 不支持 plugin approval，降级为 soft block（用 `description` 作为 block reason）

## 示例场景

### 场景 1：阻止删除操作

```typescript
// HOOK.md
---
name: safe-delete-hook
description: "Blocks dangerous delete operations"
metadata: { "openclaw": { "events": ["tool:before_tool_call"] } }
---

# Safe Delete Hook

在执行 `exec`、`rm`、`trash` 等危险操作前要求用户确认。
```

```typescript
// handler.ts
const handler = async (event) => {
  if (event.type !== "tool" || event.action !== "before_tool_call") return;

  const toolName = event.context?.toolName;
  const dangerousTools = ["exec", "trash", "rm"];

  if (dangerousTools.includes(toolName)) {
    const args = event.context?.params || {};
    const cmd = args.command || "";

    // 检查是否包含危险命令
    if (/\brm\b|\btrash\b|\bpkill\b|\bkill\s/i.test(cmd)) {
      return {
        block: true,
        blockReason: `Dangerous command detected in ${toolName}: ${cmd.slice(0, 100)}`
      };
    }
  }

  return; // 不阻止，返回 undefined
};

export default handler;
```

### 场景 2：敏感文件访问需要审批

```typescript
// handler.ts
const handler = async (event) => {
  if (event.type !== "tool" || event.action !== "before_tool_call") return;

  const toolName = event.context?.toolName;
  const params = event.context?.params || {};

  // 敏感路径列表
  const sensitivePatterns = [
    /\/etc\/passwd/i,
    /\.env$/i,
    /\/~\/\.ssh\//i,
    /\.pem$/i,
    /\.key$/i
  ];

  const filePath = params.file_path || params.path || "";

  const isSensitive = sensitivePatterns.some(p => p.test(filePath));

  if (isSensitive) {
    return {
      requireApproval: {
        title: "Sensitive File Access",
        description: `Attempting to read sensitive file: ${filePath}`,
        severity: "warning",
        timeoutMs: 60000,
        timeoutBehavior: "deny",
        onResolution: async (decision) => {
          console.log(`[safe-file-hook] Decision: ${decision}`);
          // 可以在这里记录审批结果
        }
      }
    };
  }

  return;
};

export default handler;
```

### 场景 3：修改工具参数（注入额外检查）

```typescript
// handler.ts
const handler = async (event) => {
  if (event.type !== "tool" || event.action !== "before_tool_call") return;

  const toolName = event.context?.toolName;
  const params = event.context?.params || {};

  // 为 exec 工具注入安全超时
  if (toolName === "exec" && !params.timeout) {
    return {
      params: {
        ...params,
        timeout: Math.min(params.timeout || 300, 60) // 最多 60 秒
      }
    };
  }

  return;
};

export default handler;
```

## 配置方式

### 方式 1：通过 Hook（已启用）

```json
// openclaw.json
{
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "safe-delete-hook": {
          "enabled": true
        }
      }
    }
  }
}
```

### 方式 2：通过 Plugin（需要先实现 plugin）

```typescript
// plugin.ts
export const hooks = {
  before_tool_call: async (params) => {
    // 实现审批逻辑
  }
};
```

## 审批流程（用户侧）

1. Plugin 返回 `requireApproval`
2. Gateway 通过 channel 显示审批请求（不同 channel 格式不同）
   - Telegram: Inline buttons
   - Discord: Button components
   - WebChat: 内置审批 UI
3. 用户选择：`allow-once` | `allow-always` | `deny`
4. 超过 `timeoutMs` 默认行为：`timeoutBehavior`（默认 deny）
5. `onResolution` 回调在 plugin 进程内调用（非 gateway）

## 注意事项

1. **不要在 `onResolution` 中做耗时操作** — 这是同步回调，会阻塞 gateway
2. **多个 plugin 的冲突处理** — 优先级最高的 plugin 决定结果（第一个返回 `block` 或 `requireApproval` 的 wins）
3. **降级行为** — 如果 gateway 版本不支持 plugin approval，`block` 会被转换为 soft block（agent 看到 reason 但不会真正阻止）
4. **sessionKey 可用** — `event.context.sessionKey` 可用于存储/检索持久化决策

---
*参考：OpenClaw `docs/automation/hooks.md`*