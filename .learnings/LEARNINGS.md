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

---

## 调研方法论（2026-03-21 新增）

### 规则：调研必须多源交叉验证

**触发条件**：用户说"调研一下 XXX"或"你去查一下 XXX"

**必须同时调用以下工具（并行）：**

1. **deepseek_deepseek_chat**（智库平台）
   - 用搜索模式（thinking=false, search=true）
   - 作为主要深度调研工具

2. **web_fetch**（直接获取一手页面）
   - 目标：官方文档、官方博客、产品页面
   - 绕过 AI 的知识截止限制
   - 注意：禁止带 maxChars 参数

3. **deep-research skill**
   - 路径：`~/.openclaw/workspace/skills/deep-research/SKILL.md`
   - 使用方法：先读 SKILL.md，按 skill 要求执行

4. **sessions_spawn（多个子 Agent）**
   - 用 3-5 个子 Agent 并行调研不同角度
   - 每个 Agent 负责调研一个具体维度

5. **其他 AI 平台**
   - 如用户提到具体平台（千问、智谱、Kim 等），也调用

### 不允许的调研方式
- ❌ 只调用 DeepSeek Chat 一个工具
- ❌ 直接凭 AI 的知识库回答，不做实时搜索
- ❌ 用过期的 AI 知识回答新问题

### 调研流程
1. 确定调研维度（3-5 个）
2. 并行调用多种工具
3. 交叉验证结果
4. 整理结论，明确哪些是确认的事实，哪些是估算


## 2026-03-21 教训追加

### 1. Genesis 硬件门槛必须调研后写入
- **错误**：写成了"RTX 4090 即可"
- **正确**：最低 GTX 1080 6GB，RTX 3060 12GB 推荐入门
- **教训**：所有技术数据必须经过调研验证，不能凭感觉写进文档

### 2. SOP 重组时不能留空引用
- **错误**：写了"详见第十章"但没写内容
- **教训**：不能只写目录结构就交差

### 3. 调研必须用多个平台
- **规则**：deepseek_deepseek_chat + web_fetch + deep-research skill + 3-5个子Agent + 其他AI平台
- **教训**：用户明确要求就要遵守，不能偷懒只用一个工具

### 4. iPhone 作为 OpenClaw 节点的 GPIO 价值
- Jetson Nano 和 ESP32-Cam 都有 40 针 GPIO
- 有线 GPIO 应急停止 <1ms，无线 WiFi >100ms
- 这个洞察是被用户提醒后才想到的，要主动考虑
