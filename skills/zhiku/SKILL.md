---
name: zhiku
description: 智库五平台并行搜索 - DeepSeek/Kimi/Doubao/GLM/Qwen 同时思考
---

# 智库 Skill

## 介绍
将同一个问题同时广播给 5 个 AI 平台（DeepSeek、Kimi、Doubao、GLM、Qwen），并行收集回复，对比各平台的方案和思路，由 OpenClaw 汇总整理。

## 激活方式
看到"智库"关键字时激活，例如：
- "问一下智库"
- "让五个平台同时思考"
- "对比一下各平台的方案"

## 架构

```
用户问题
    │
    ├── subagent-ds  ──→  deepseek_mcp  ──→  DeepSeek
    ├── subagent-kimi ──→  webauth_mcp  ──→  Kimi
    ├── subagent-doubao──→  webauth_mcp  ──→  Doubao
    ├── subagent-glm  ──→  webauth_mcp  ──→  GLM
    └── subagent-qwen ──→  webauth_mcp  ──→  Qwen
    │
    ▼
主会话汇总 → 对比表格 + 各平台亮点 + 综合建议
```

## 核心脚本

- `zhiku-ask.js` — 主脚本，派生 5 个 subagent 并行提问

## 使用方式

**方式一：直接对话（推荐）**
```
用户：让智库分析一下"为什么AI会火"
助手：→ 调用 zhiku-ask.js → 汇总输出
```

**方式二：直接调用脚本**
```bash
node ~/.openclaw/workspace/skills/zhiku/scripts/zhiku-ask.js "问题"
```

## 主 Agent 调用流程

当用户触发智库时：

1. 解析用户问题
2. 调用 `zhiku-ask.js`，传入问题
3. 解析 JSON 输出中的 `summary` 字段
4. 以 Markdown 格式展示给用户

## 输出示例

```markdown
## 🧠 智库对比分析

**问题：** 为什么AI会火？请从技术、经济、社会三个角度分析

### 各平台回复

**🔵 DeepSeek（深度思考+联网搜索）**
[完整回复，内容全面，有结构化要点]

**🟣 Kimi（K2.5 思考模式，200万字上下文）**
[表格+代码块，格式清晰]

**🟠 Doubao（专家模式，研究级深度思考）**
[简洁精炼]

**🟢 GLM（思考+联网，中文语境）**
[中文语境深入分析]

**🔷 Qwen 3.5 Plus（通义千问，阿里大模型）**
[逻辑清晰]

---
*以上为5个平台并行回复的综合整理，完整内容可在各自平台对话窗口查看。*
```

## 内部实现

- `zhiku-ask.js` 用 `Promise.all` 并行调用 5 个平台
- 每个平台独立 MCP 调用，互不阻塞
- 总耗时 = 最慢平台的耗时（约 30-60 秒）
- JSON 输出格式：`{success, summary, raw: {deepseek, kimi, doubao, glm, qwen}}`

## 各平台默认模式

| 平台 | 工具 | 模式 | 特点 |
|------|------|------|------|
| DeepSeek | `deepseek_deepseek_chat` | 深度思考+智能搜索 | 推理能力强，联网搜索 |
| Kimi | `webauth_kimi_chat` | K2.5思考模式 | 超长上下文，200万字 |
| Doubao | `webauth_doubao_chat` | 专家模式 | 深度思考，研究级 |
| GLM | `webauth_glm_chat` | 思考+联网 | 中文语境强，联网搜索 |
| Qwen | `webauth_qwen_chat` | qwen3.5-plus | 阿里大模型，逻辑清晰 |

## 输出格式

收到 5 个平台回复后，主会话汇总输出：

```
## 🧠 智库对比分析

### 问题
<用户问题>

### 各平台回复

| 平台 | 核心方案 | 亮点 |
|------|----------|------|
| DeepSeek | ... | ... |
| Kimi | ... | ... |
| Doubao | ... | ... |
| GLM | ... | ... |
| Qwen | ... | ... |

### 综合建议
<汇总各平台最佳方案，给出推荐>
```

## 依赖条件

- Chrome 调试端口 9223 需运行（各平台页面已登录）
- 各 MCP Server 已注册到 openclaw-mcp-adapter
- DeepSeek MCP Server 已注册

## 注意事项

- ⚠️ Chrome 重启后调试端口会断，需重新启动
- 所有 5 个 subagent 并行执行，总等待时间 ≈ 最慢平台的时间
- 各 subagent 超时时间：90 秒
