# 经验教训 - MCP Server 接入 AI 网页

## 2026-03-19

### 成功经验

#### 1. DeepSeek MCP Server 完整接入流程
- 创建 MCP Server（使用 @modelcontextprotocol/sdk）
- PoW 解算：复用 zero-token 的 WASM 模块（从 dist 提取 SHA3_WASM_B64）
- API 调用：先创建 session → 获取 PoW challenge → 解算 → 发消息 → 收集 SSE
- SSE 格式：`{"v":"文字内容"}`（不是标准 data: 格式）
- 默认参数：thinking=true, search=true（深度思考和智能搜索默认开启）

#### 2. MCP Server 在 openclaw.json 的配置
```json
"plugins": {
  "entries": {
    "openclaw-mcp-adapter": {
      "enabled": true,
      "config": {
        "servers": [{
          "name": "deepseek",
          "transport": "stdio",
          "command": "node",
          "args": ["/path/to/mcp-server.mjs"]
        }],
        "toolPrefix": true
      }
    }
  }
}
```
- toolPrefix: true → 工具名变成 `deepseek_deepseek_chat`
- 工具注册到 main agent 后用 alsoAllow

#### 3. Chrome CDP 连接成功过的方式
- WS URL 格式：`ws://127.0.0.1:18800/devtools/browser/{browser-id}`
- Browser ID 从 `curl http://127.0.0.1:18800/json/version` 获取
- 今天成功抓取时：browser ID = `58257918-e864-499f-bf4f-22bca20c26d1`

#### 4. Agent 工具授权
- main agent 添加 alsoAllow 即可调用 MCP 工具
```json
"agents": {
  "list": [{
    "id": "main",
    "tools": {
      "profile": "coding",
      "alsoAllow": ["deepseek_deepseek_chat"]
    }
  }]
}
```

### 失败教训

#### 1. 端口混淆（严重！）
- ❌ 9222 = Chrome-OpenClaw-Debug profile（空的，没有登录）
- ❌ 18792 = Browser Relay HTTP = OpenClaw web UI 专用，**绝对不能连！连了会崩！**
- ✅ 18800 = Chrome Remote Debugging Port = 用户主 Chrome，有登录状态

#### 2. 连 18792 导致 Gateway 崩溃
- 18792 是 OpenClaw web UI 和 Browser Relay 扩展之间的通信端口
- Playwright 连 18792 会占用 Chrome 扩展的 WebSocket
- 导致 Browser Relay 断连 → web UI 崩溃
- 教训：**永远不要连 18792**

#### 3. CDP WebSocket 只能同时一个连接
- Chrome 调试端口只能有一个客户端
- 同一时间只能有 Playwright 或 Chrome 扩展连接，不能同时两个

#### 4. Chrome cookies 加密
- macOS Chrome 的 cookies 用 Keychain 加密，encrypted_value 无法本地解密
- 只有 Chrome 运行时通过 CDP 才能读到明文 cookies

### 正确的 CDP 连接步骤

1. **确认 Browser Relay 扩展已关闭**（ps 检查没有 extension 进程）
2. **连 18800**：`curl http://127.0.0.1:18800/json/version` 返回 WS URL
3. Playwright 用 `chromium.connectOverCDP(wsUrl)` 连接
4. 抓完 cookies 后立刻断开

### 平台 API 关键信息

| 平台 | 关键 Cookie | API 端点 | 特殊参数 |
|------|-------------|----------|----------|
| DeepSeek | ds_session_id | /api/v0/chat/completion | PoW (WASM) |
| Doubao | sessionid | /samantha/chat/completion | a_bogus, msToken |
| Kimi | kimi-auth | localStorage 直接取 token | Bearer Token |
| GLM | chatglm_refresh_token | /api/v2/chat/completion | X-Sign (MD5) |
| Qwen | token | /chat/ | 未知 |

### Gateway 崩溃原因

1. 连 18792 触发 Browser Relay 断开 → web UI 崩溃
2. MCP Server 启动失败可能也影响 Gateway 稳定性

## 2026-03-19 WebAuth 测试

### 成功
- Playwright CDP 连接 Chrome 调试端口 9223
- Kimi/Doubao/GLM Cookie 捕获
- Kimi API 调用成功（200 OK）

### 失败
- GLM API 需要 X-Sign 签名
- Doubao API 需要 a_bogus 动态参数

### 关键
- API 必须从 page.evaluate 调用（跨域限制）
- 必须连接 browser-level WS URL

## 2026-03-19 19:20 WebAuth MCP Server

### 路径
- Server: `~/.openclaw/extensions/webauth-mcp/server.mjs`
- 凭证: `~/.openclaw/workspace/auth-credentials/{doubao,kimi,glm}.json`

### 架构
- Playwright CDP 连接 Chrome 9223
- page.evaluate() 调用 API（解决跨域）

### 待加入配置
- `~/.openclaw/extensions/webauth-mcp/` → openclaw-mcp-adapter

### 待测
- Kimi/Doubao/GLM 完整对话流程

## 2026-03-19

### WebAuth MCP
- Server: `~/.openclaw/extensions/webauth-mcp/server.mjs`
- 凭证: `~/.openclaw/workspace/auth-credentials/`
- Kimi ✅ | Doubao ❌ | GLM ❌

### Chrome 调试
- 端口: 9223
- 连接: browser-level WS URL

### OpenClaw Zero Token
- 流程: 启动Chrome → 登录 → CDP捕获 → 存储 → API调用
- Kimi: Connect RPC, Bearer Token
- Doubao: 需要 a_bogus
- GLM: 需要 X-Sign

## 2026-03-19 WebAuth MCP 完成

### 三平台全部成功
- Kimi ✅ - Connect RPC, Bearer Token
- Doubao ✅ - SSE, Cookie + 浏览器自动算 a_bogus
- GLM ✅ - SSE, X-Sign MD5 + refresh token

### Server
- `~/.openclaw/extensions/webauth-mcp/server.mjs`

### Chrome 调试
- 端口 9223
- 连接 browser-level WS URL

### 凭证
- `~/.openclaw/workspace/auth-credentials/`

### 关键
- a_bogus: page.evaluate() 让浏览器自动生成
- GLM X-Sign: md5(timestamp-nonce-SIGN_SECRET)
- zero-token 是最佳参考

## 2026-03-19 WebAuth MCP 完成

### 三平台
- Kimi ✅ - Connect RPC, Bearer Token
- Doubao ✅ - SSE, Cookie + 浏览器自动算 a_bogus  
- GLM ✅ - SSE, X-Sign MD5 + refresh token

### 关键技巧
- a_bogus: page.evaluate() 让浏览器自动生成
- GLM X-Sign: md5(timestamp-nonce-SIGN_SECRET)
- GLM 去重: 用长度比较取最后版本

### Bug
- Doubao `<|im_start|>` 标签: 发送内容改为纯文本
- 配置文件未授权修改: 必须先问用户

### 路径
- Server: `~/.openclaw/extensions/webauth-mcp/server.mjs`
- 凭证: `~/.openclaw/workspace/auth-credentials/`
- Chrome: 端口 9223，Gateway 重启后需重开

## 2026-03-19 最终完成

### Doubao 专家模式
- 参数: `ext.use_deep_think: '1'`
- 默认已启用专家模式

## 2026-03-19 最终完成

### Kimi K2.5 思考
- 参数: `options.thinking: true`
- 默认已启用 K2.5 思考模式

## 2026-03-19 最终完成

### GLM 思考+联网
- 参数: `meta_data.chat_mode: 'think'`, `is_networking: true`, `use_network: true`, `network_only: false`
- 默认已启用思考+联网模式

## 2026-03-19 Qwen WebAuth 实现

### 核心问题
千问 Authorization header 无法从外部捕获（页面 JS 在 fetch 内部加，Playwright 所有层面都看不到）

### 解决方案：window.fetch override
在页面内 override fetch，拦截 SSE 流，解析 `choices[0].delta.content`，同时把数据传回给页面

### 关键代码
```javascript
window._qwenText = '';
const _origFetch = window.fetch;
window.fetch = async (...args) => {
  const response = await _origFetch(...args);
  const newStream = new ReadableStream({
    async start(controller) {
      while (true) {
        const { done, value } = await reader.read();
        if (done) { controller.close(); break; }
        // 解析 SSE，提取 choices[0].delta.content
        controller.enqueue(value); // 必须传回给页面
      }
    }
  });
  return new Response(newStream, { headers: response.headers });
};
```

### 踩的坑
1. Authorization 看不到 → 用 fetch override
2. SSE 格式 `choices[0].delta.content` 不是 `text`
3. 必须 enqueue 数据，否则页面收不到响应
4. 触发方式：UI 操作（textarea + fill + Enter）

## 2026-03-19 23:27 智库 Skill v1.0 完成

### 架构
- 单脚本并行调用 5 个平台（MCP Promise.all）
- 脚本: `skills/zhiku/scripts/zhiku-ask.js`
- 输出: JSON `{success, summary, raw: {...}}`

### 成功标准
- 5/5 平台并行响应
- 输出格式统一
- 汇总表格清晰

### 关键经验
1. ES Module 里用 `require('child_process')` 会报错 → 用 `await import('child_process')`
2. GLM `waitUntil: 'load'` 超时 → 改 `commit` + 复用已有页面
3. zhiku-s1/s2/s3 并行方式已被单脚本替代（更简单）

### v1.0 版本文件
- `skills/zhiku/SKILL.md`
- `skills/zhiku/scripts/zhiku-ask.js`
