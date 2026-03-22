# 各平台高级模式 — MCP 实际调用参数

> 更新：2026-03-22
> 用途：记录每次提问时 MCP 实际传递的 API 参数，供调试和核实用

---

## 一、参数速查表

| 平台 | 模式 | MCP 文件 | API 参数 | 状态 |
|------|------|---------|---------|------|
| Doubao | 专家模式 | `webauth-mcp/server.mjs` | `ext.use_deep_think: '1'` | ✅ 已启用 |
| Kimi | K2.5思考模式 | `webauth-mcp/server.mjs` | `options.thinking: true` | ✅ 已启用 |
| GLM | 思考+联网 | `webauth-mcp/server.mjs` | `assistantId: glm-4-think` + `is_networking: true` | ✅ 已修复联网参数 |
| DeepSeek | 深度思考+智能搜索 | `deepseek-mcp-server/deepseek-mcp-server.mjs` | `thinking_enabled: true` + `search_enabled: true` | ✅ 已启用 |
| Qwen | 默认（qwen-plus）| `webauth-mcp/server.mjs` | 无显式参数，依赖页面当前状态 | ✅ 保持默认 |

---

## 二、详细代码位置

### Doubao — 专家模式
**文件**：`~/.openclaw/extensions/webauth-mcp/server.mjs`
**行号**：227
```javascript
ext: {
  use_deep_think: '1',  // 专家模式
  fp: '',
},
```
**调用方式**：`webauth_doubao_chat(message, model)`

---

### Kimi — K2.5思考模式
**文件**：`~/.openclaw/extensions/webauth-mcp/server.mjs`
**行号**：135
```javascript
options: { thinking: true }
```
**调用方式**：`webauth_kimi_chat(message, model)`

---

### GLM — 思考+联网
**文件**：`~/.openclaw/extensions/webauth-mcp/server.mjs`
**行号**：357
```javascript
assistantId: 'glm-4-think',  // 思考模式
// ...
is_networking: false,         // ⚠️ 联网未启用，需要修复
```
**问题**：`is_networking` 当前是 `false`，联网搜索未开启
**调用方式**：`webauth_glm_chat(message, model)`

---

### DeepSeek — 深度思考+智能搜索
**文件**：`~/.openclaw/extensions/deepseek-mcp-server/deepseek-mcp-server.mjs`
**行号**：126-127
```javascript
thinking_enabled: thinking,  // 默认 true
search_enabled: search,      // 默认 true
```
**调用方式**：`deepseek_deepseek_chat(message, thinking=true, search=true)`

---

### Qwen — 默认（qwen-plus）
**文件**：`~/.openclaw/extensions/webauth-mcp/server.mjs`
**说明**：无显式模型参数，页面默认使用 qwen-plus，保持默认即可
**调用方式**：`webauth_qwen_chat(message, model)`

---

## 三、待修复问题

### GLM 联网模式未启用
- **现象**：`is_networking: false`，智谱不会联网搜索
- **位置**：`webauth-mcp/server.mjs` line 357
- **状态**：✅ 已修复并验证（2026-03-22）
