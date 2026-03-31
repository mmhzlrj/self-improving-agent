# 各平台高级模式 — MCP 实际调用参数

> ⚠️ 已过期（2026-03-30 起）- 架构变更，MCP 已迁移到 openclaw-mcp-adapter
> 当前配置请参考：MEMORY.md 第 395-410 行

---

## 当前正确架构（2026-03-30 起）

- MCP server 由 **openclaw-mcp-adapter**（Gateway 插件）统一管理
- `toolPrefix: null`，工具名**无前缀**
- alsoAllow 配置在 `agents.list[0].tools.alsoAllow`

### 正确工具名

| 平台 | 工具名（无前缀） |
|------|-----------------|
| Doubao | `doubao_chat` |
| Kimi | `kimi_chat` |
| GLM | `glm_chat` |
| Qwen | `qwen_chat` |
| DeepSeek | `deepseek_chat` |

### 配置文件位置
- MCP server 配置：`~/.openclaw/openclaw.json` → `plugins.entries.openclaw-mcp-adapter.config.servers`
- alsoAllow：`~/.openclaw/openclaw.json` → `agents.list[0].tools.alsoAllow`
