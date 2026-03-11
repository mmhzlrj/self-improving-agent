# OpenClaw 集成 MiniMax MCP 工具调研报告

## 概述

本报告调研 OpenClaw 集成 MiniMax Coding Plan MCP (web_search, understand_image) 的可行性和具体步骤。

---

## 1. OpenClaw 工具机制说明

### 1.1 工具架构概览

OpenClaw 的工具系统分为三个层次：

1. **内置工具** - 核心功能，如 exec, browser, read, write 等
2. **插件工具** - 通过 OpenClaw 插件注册的工具
3. **Skill 工具** - 通过 Skill 定义的能力

### 1.2 工具注册方式

OpenClaw 支持两种主要方式添加自定义工具：

#### 方式一：插件注册（Plugin）

通过 OpenClaw 插件注册工具：

```typescript
// extensions/feishu/src/chat.ts 示例
api.registerTool(
  {
    name: "feishu_chat",
    label: "Feishu Chat",
    description: "Feishu chat operations. Actions: members, info",
    parameters: FeishuChatSchema,
    async execute(_toolCallId, params) {
      // 工具实现
      return json(result);
    },
  },
  { name: "feishu_chat" }
);
```

工具定义结构：
- `name`: 工具唯一名称
- `label`: UI 显示标签
- `description`: 工具描述
- `parameters`: 参数 schema (TypeBox 类型)
- `execute`: 执行函数

#### 方式二：Skill 定义

通过 SKILL.md 文件定义工具能力：

```markdown
---
name: my-skill
description: My custom skill
metadata:
  {
    "openclaw": {
      "requires": { "bins": ["my-cli"] },
      "primaryEnv": "MY_API_KEY"
    }
  }
---

# Skill Instructions

When the user asks for X, use the `my-cli` tool...
```

### 1.3 MCP 集成方式

OpenClaw 通过 **mcporter** CLI 集成 MCP 服务器。mcporter 是 Model Context Protocol 的 CLI 工具，支持：

- 列出配置的 MCP 服务器
- 调用 MCP 工具
- OAuth 认证
- 生成独立的 CLI

---

## 2. MCP 集成方案

### 2.1 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **mcporter (推荐)** | 无需编写代码、即插即用、支持 HTTP/stdio | 需要额外部署 MCP 服务器 |
| **自定义插件** | 完全控制、可深度集成 | 需要开发工作 |

### 2.2 推荐方案：mcporter

这是最简单的方式，通过 mcporter 调用外部 MCP 服务器。

#### mcporter 配置

在 `~/.mcporter/config.json` 中添加 MCP 服务器：

```json
{
  "mcpServers": {
    "minimax-coding": {
      "baseUrl": "http://localhost:8080/mcp"
    }
  }
}
```

#### 使用方式

```bash
# 列出工具
mcporter list minimax-coding

# 调用工具
mcporter call minimax-coding.web_search query="OpenClaw MCP"

# 或通过 stdio 模式
mcporter call --stdio "bun run ./minimax-mcp-server.ts" web_search query="test"
```

---

## 3. MiniMax MCP 服务器

### 3.1 MiniMax 官方 MCP

截至目前调研，MiniMax 官方提供两种 MCP 能力：

1. **MiniMax API 作为模型提供商** - 通过 API 密钥配置 Claude Code 等工具
2. **第三方 MCP 服务器** - 如 minimax-mcp-server（财务 ERP 集成）

### 3.2 自定义 MCP 服务器

对于 web_search 和 understand_image 功能，需要：

1. **部署自定义 MCP 服务器**，或
2. **使用现有的 MCP 服务器**（如 Brave Search、Exa 等）

#### 示例：使用 Exa MCP 替代 web_search

```bash
# 安装 Exa MCP
npm install -g @exa/mcp-server

# 配置
echo '{
  "mcpServers": {
    "exa": {
      "baseUrl": "https://mcp.exa.ai/mcp"
    }
  }
}' > ~/.mcporter/config.json
```

### 3.3 understand_image 能力

OpenClaw 已内置图像理解能力：

- 内置 `image` 工具（分析图片）
- 可通过插件扩展（如 feishu 的图像分析）

---

## 4. 具体配置步骤

### 步骤 1：安装 mcporter

```bash
npm install -g mcporter
```

或使用 OpenClaw 配套版本：

```bash
# OpenClaw 已自带 mcporter
which mcporter
```

### 步骤 2：配置 MCP 服务器

编辑 `~/.mcporter/config.json`：

```json
{
  "mcpServers": {
    "brave-search": {
      "baseUrl": "https://search.duckduckgo.com/mcp"
    },
    "your-mcp": {
      "baseUrl": "http://localhost:3000/mcp"
    }
  },
  "imports": []
}
```

### 步骤 3：创建 Skill（可选）

在 `~/.openclaw/skills/` 或 `<workspace>/skills/` 创建 Skill 目录：

```
skills/
└── minimax-tools/
    └── SKILL.md
```

SKILL.md 示例：

```markdown
---
name: minimax-tools
description: MiniMax MCP tools for web search and image understanding
metadata:
  {
    "openclaw": {
      "requires": { "bins": ["mcporter"] }
    }
  }
---

# MiniMax Tools

This skill provides access to MCP tools via mcporter.

## Tools

When the user asks to search the web, use the `mcporter` tool:

```
mcporter call <server>.web_search query="<query>"
```

When the user asks to analyze an image, use the `mcporter` tool:

```
mcporter call <server>.understand_image image_path="<path>"
```

Note: Replace `<server>` with your configured MCP server name.
```

### 步骤 4：验证配置

```bash
# 列出可用的 MCP 服务器
mcporter list

# 查看服务器工具
mcporter list <server-name> --schema

# 测试调用
mcporter call <server-name>.web_search query="test"
```

### 步骤 5：在 OpenClaw 中使用

重启 OpenClaw Gateway 后，Skill 将自动加载。Agent 可以通过 Skill 定义的工具调用 MCP 服务器。

---

## 5. 配置文件位置

| 配置项 | 位置 |
|--------|------|
| OpenClaw 主配置 | `~/.openclaw/openclaw.json` |
| mcporter 配置 | `~/.mcporter/config.json` |
| OpenClaw Skills | `~/.openclaw/skills/` |
| Workspace Skills | `<workspace>/skills/` |

---

## 6. 注意事项

1. **MCP 服务器需要独立部署** - OpenClaw 本身不提供 MCP 服务器，需要部署外部 MCP 服务
2. **认证** - 某些 MCP 服务器需要 OAuth 认证，使用 `mcporter auth <server>` 完成
3. **网络** - HTTP MCP 服务器需要可访问的 URL
4. **Skill 加载** - Skill 变更后需要重启 Gateway

---

## 7. 替代方案

如果 MiniMax MCP 不可用，可以考虑：

1. **Brave Search** - Web 搜索 MCP
2. **Exa Search** - AI 搜索 MCP
3. **OpenAI Web Search** - 如果使用 OpenAI 模型
4. **OpenClaw 内置** - 使用 OpenClaw 自带的 web search 和 image 工具

---

## 结论

OpenClaw 通过 mcporter 支持 MCP 工具集成。最简单的方案是：

1. 部署或配置 MCP 服务器
2. 通过 mcporter 配置和测试
3. 创建 Skill 包装工具调用

对于 MiniMax web_search 和 understand_image，需要确认 MiniMax 是否提供对应的 MCP 服务器，或使用替代方案（如 Brave Search、Exa 等）。
