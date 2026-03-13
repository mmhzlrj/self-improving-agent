# 智库任务书

## 背景
需要同时测试 5 个 AI 平台（千问、智谱、Kimi、豆包、DeepSeek）的回答质量，评估各平台的响应能力。

## 现有工具调研

### 0. WebMCP

**定义**：W3C 孵化的 Web 标准提案，让网页可以暴露 JavaScript 工具给 AI 代理调用。

**核心概念**：
- 网页通过 `navigator.modelContext` API 注册工具
- AI 代理通过 MCP 协议调用这些工具
- 工具在客户端执行，不需要后端服务器

**与后端集成的区别**：
- 后端集成：AI 平台直接调用服务的后端 API
- WebMCP：AI 通过网页暴露的工具操作，共享同一界面

**相关仓库**：
- WebMCP 官方：https://github.com/webmachinelearning/webmcp
- MCP 官方：https://github.com/modelcontextprotocol
- webmcp.sh playground：https://webmcp.sh

**在智库任务中的作用**：
- 如果 5 个 AI 平台支持 WebMCP → 可以直接调用工具提问，不需要启动浏览器
- 目前可能还不支持 → 仍需用 Playwright MCP + CDP 18800

**优势**：
- 不需要启动新浏览器
- 工具在客户端执行，更可靠
- 用户和代理共享界面，协作更自然

---

### 1. CDP (Chrome DevTools Protocol)

**定义**：Chrome DevTools Protocol，允许工具检测、调试和分析 Chromium 内核浏览器的协议。

**核心概念**：
- 通过 JSON 消息与浏览器通信
- 分为多个域（DOM、Debugger、Network 等）
- 支持 HTTP 和 WebSocket 两种方式

**HTTP 端点**：
- `GET /json/version` - 获取浏览器版本信息
- `GET /json` 或 `/json/list` - 获取所有可用的 websocket targets
- `GET /json/protocol/` - 获取当前协议的 JSON 定义
- `PUT /json/new?{url}` - 打开新标签页
- `GET /json/activate/{targetId}` - 激活标签页
- `GET /json/close/{targetId}` - 关闭标签页
- WebSocket `/devtools/page/{targetId}` - 协议通信端点

**在智库任务中的作用**：
- 提供底层浏览器控制能力
- 通过 CDP 可以获取页面列表、操作 DOM、截图等

**当前使用端口**：18800（OpenClaw CDP）

---

### 2. Playwright

**定义**：Microsoft 开发的浏览器自动化库，专门为端到端测试设计。

**特点**：
- 支持多种浏览器：Chromium、WebKit、Firefox
- 支持 Windows、Linux、macOS
- 可在 CI 环境运行
- 支持有头（headed）和无头（headless）模式
- 支持移动端模拟

**核心 API**：
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()  # 启动浏览器
    page = browser.new_page()      # 创建新页面
    page.goto("https://...")      # 导航
    page.click("#button")         # 点击
    page.fill("#input", "text")   # 输入
    browser.close()
```

**在智库任务中的作用**：
- 提供高级浏览器自动化 API
- 可以模拟用户操作（点击、输入、导航）
- MCP 工具使用 Playwright 控制浏览器

**当前 MCP 配置**：
- 工具：`@playwright/mcp`
- 提供 22 个浏览器自动化工具

---

### 3. Browser Relay

**定义**：OpenClaw 的 Chrome 扩展，允许控制用户已有的 Chrome 浏览器标签页。

**与 OpenClaw Browser 的区别**：
- Browser Relay：控制用户已有的 Chrome（需要安装扩展）
- OpenClaw Browser：OpenClaw 自带的专用浏览器

**核心功能**：
- 通过 Chrome 扩展连接 CDP
- 将 CDP 能力暴露给 OpenClaw
- 支持多标签页管理

**安装步骤**：
1. 安装扩展：`npx openclaw browser extension install`
2. 加载到 Chrome：`chrome://extensions` → Load unpacked
3. 启动 Chrome 带调试端口：`--remote-debugging-port=18800`
4. 配置扩展：填写 Gateway URL、Token、Relay Port

**端口配置**：
- Gateway HTTP：18789
- Browser Relay CDP：18800

**在智库任务中的作用**：
- 连接用户已有的浏览器（不启动新窗口）
- 复用已打开的 AI 平台页面

---

### 4. Chrome 开发者工具

**定义**：Chrome 内置的开发工具集，包含元素检查、网络监控、调试等功能。

**组成部分**：
- Elements：检查和编辑 DOM
- Console：JavaScript 控制台
- Network：网络请求监控
- Sources：JavaScript 调试
- Performance：性能分析
- Application：应用存储检查
- Protocol Monitor：CDP 命令监控

**Protocol Monitor 功能**（重要）：
- 查看所有 CDP 请求和响应
- 直接发送 CDP 命令
- 从 Chrome 117+ 可用

**使用方式**：
1. 打开 DevTools → Settings → Experiments
2. 启用 "Protocol Monitor"
3. 重新打开 DevTools
4. More Tools → Protocol Monitor

**在智库任务中的作用**：
- 调试浏览器自动化问题
- 查看 CDP 命令执行情况
- 监控 AI 平台的请求/响应

---

## 任务目标

### 目标 1：建立稳定的浏览器控制方案

**方案 A：使用 WebMCP**
- 检查 5 个 AI 平台是否支持 WebMCP
- 如果支持，直接调用工具提问
- 优势：不需要启动浏览器，工具在客户端执行

**方案 B：使用 Playwright MCP + CDP 18800**
- 连接到用户已有的浏览器（不启动新窗口）
- 复用已打开的页面
- 当前正在测试的方案

### 目标 2：实现 5 平台同时提问

**需要解决的问题**：
1. 如何为每个平台创建新对话
2. 如何发送问题
3. 如何等待响应完成（动态检测）
4. 如何提取响应内容
5. 如何保存到文件

---

## 执行计划

### 阶段 1：工具验证

1. 验证 CDP 18800 连接
2. 获取 5 个平台的页面
3. 测试基本操作（点击、输入）

### 阶段 2：功能模块开发

1. 模块 1：检查 CDP 连接
2. 模块 2：获取页面列表
3. 模块 3：创建新对话（每个平台方式不同）
4. 模块 4：发送问题
5. 模块 5：等待响应完成
6. 模块 6：提取响应内容
7. 模块 7：保存到文件

### 阶段 3：集成测试

1. 5 平台同时提问
2. 收集响应
3. 生成对比报告

---

## 关键约束

- ❌ 禁止启动新浏览器窗口（会"电脑乱动"）
- ✅ 必须连接 CDP 18800（复用已有浏览器）
- ✅ 必须等待响应完成后再提取
- ✅ 必须保存完整响应（不截断）

---

## 待调研

- [ ] 5 个 AI 平台的 WebMCP 支持情况
- [ ] 每个平台创建新对话的最佳方式
- [ ] 响应完成的动态检测方法
- [ ] 响应内容提取的最佳实践

---

## 参考资料

- CDP 官方文档：https://chromedevtools.github.io/devtools-protocol/
- Playwright 文档：https://playwright.dev/
- Browser Relay 文档：~/.openclaw/workspace/docs/browser-relay-full-guide.md
- WebMCP 文档：~/.openclaw/workspace/webmcp.md
