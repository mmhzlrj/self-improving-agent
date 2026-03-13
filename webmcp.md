# WebMCP 配置指南

## 概述
WebMCP（Web Model Context Protocol）是 W3C Web Machine Learning Community Group 孵化的 Web 端 MCP 扩展标准，谷歌 Chrome 团队是核心参与者。

## 相关仓库

### 1. WebMCP 官方标准仓库
- 地址：https://github.com/webmachinelearning/webmcp
- 说明：W3C Web Machine Learning Community Group 孵化、谷歌 Chrome 团队核心参与制定的 WebMCP 官方规范仓库。

### 2. 底层 Model Context Protocol（MCP）官方主仓库
- 地址：https://github.com/modelcontextprotocol/modelcontextprotocol
- 说明：底层 MCP 协议官方核心规范与文档仓库。

### 3. MCP 官方组织主页
- 地址：https://github.com/modelcontextprotocol
- 说明：包含各语言 SDK、官方服务器、工具等全生态仓库。38 个公开仓库，44,316 关注者。

### 4. WebMCP 官方演示与开发沙箱（webmcp.sh）
- 地址：https://github.com/WebMCP-org/webmcp-sh
- 网站：https://webmcp.sh
- 说明：基于浏览器的 MCP playground，内置 PostgreSQL（PGlite）。

### 5. MCP 官方 TypeScript SDK
- 地址：https://github.com/modelcontextprotocol/typescript-sdk
- 说明：构建 MCP 服务器和客户端的 TypeScript SDK，支持 Node.js、Bun、Deno。

---

## 完整总结

### 1. WebMCP 是什么

**定义**：W3C 孵化的 Web 标准提案，让网页可以暴露 JavaScript 工具给 AI 代理调用。

**核心概念**：
- 网页通过 `navigator.modelContext` API 注册工具
- AI 代理通过 MCP 协议调用这些工具
- 工具在客户端执行，不需要后端服务器

**与后端集成的区别**：
- 后端集成：AI 平台直接调用服务的后端 API
- WebMCP：AI 通过网页暴露的工具操作，共享同一界面

**目标**：
- 支持人机协作工作流
- 简化 AI 代理集成
- 减少开发者负担
- 改善无障碍访问

### 2. MCP 是什么

**定义**：Model Context Protocol，让 LLM 应用与外部数据源和工具无缝集成的开放协议。

**作者**：David Soria Parra 和 Justin Spahr-Summers

**核心组件**：
- MCP Server：暴露工具、资源、提示
- MCP Client：连接服务器，调用工具
- 传输方式：stdio、WebSocket（SSE）

### 3. webmcp.sh 是什么

**定义**：WebMCP 的在线 playground。

**功能**：
- 同时连接多个 MCP 服务器
- 执行工具并实时验证参数
- 浏览和管理服务器资源
- 内置 PostgreSQL 数据库（PGlite）
- 交互式 SQL REPL

**技术栈**：React 19、TypeScript 5.8、PGlite、Drizzle ORM

### 4. TypeScript SDK 是什么

**定义**：构建 MCP 服务器和客户端的 TypeScript SDK。

**支持平台**：Node.js、Bun、Deno

**包**：
- `@modelcontextprotocol/server` - 构建 MCP 服务器
- `@modelcontextprotocol/client` - 构建 MCP 客户端

**中间件**：
- `@modelcontextprotocol/node` - Node.js HTTP
- `@modelcontextprotocol/express` - Express
- `@modelcontextprotocol/hono` - Hono

---

## 在当前任务中的应用

### 智库 5 平台测试

**问题**：需要同时测试 5 个 AI 平台（千问、智谱、Kimi、豆包、DeepSeek）

**如果平台支持 WebMCP**：
- 可以直接调用工具提问
- 不需要启动新浏览器

**如果平台不支持 WebMCP**：
- 仍需用 Playwright MCP + CDP 18800 连接已有浏览器

### WebMCP 优势

- 不需要启动新浏览器
- 工具在客户端执行，更可靠
- 用户和代理共享界面，协作更自然

---

## 待完成
- [ ] 研究如何将 WebMCP 配置到 OpenClaw
- [ ] 检查 5 个 AI 平台是否支持 WebMCP
- [ ] 决定使用 WebMCP 还是 Playwright MCP + CDP 18800
