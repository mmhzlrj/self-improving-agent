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

## 2026-03-22 新增教训

### 1. 收到任务必须先记录再执行
- **问题：** 收到任务后直接执行，没有记录。导致任务内容丢失，无法追溯
- **教训：** 先在 memory/YYYY-MM-DD.md 记录 `hh-mm 收到任务：<内容>`
- **格式：** 完成任务后更新 `hh-mm 完成：<总结>`

### 2. zhiku MCP 是用来问各平台知识的
- **错误：** 用 zhiku MCP 问"模型能不能在iPhone跑"（应该是问平台知识，不是问模型本身）
- **正确：** 问"iPhone AI 目标检测方案有哪些"（让平台给出建议）
- **不能用 zhiku 问：** 模型技术细节、纯实现问题（应该 web_fetch 官方文档）

### 3. zhiku MCP 超时问题
- **原因1：** goto timeout 太短（15-20s），'load' 等待太久
- **原因2：** Qwen textarea 有两个元素，用 `.first()` 选中了只读隐藏的那个
- **调试方法：** 先单独测试各平台，确认 browser 能打开，再看 evaluate 逻辑

### 4. Playwright locator 选错元素
- **问题：** Qwen 的 `textarea` 有两个，一个 readonly/hidden，一个可见
- **解决：** 用 `textarea:not([readonly]):not([aria-hidden="true"])` 选择可见元素

### 5. Chrome+webauth 调试（2026-03-22 重大失误）
- **症状：** Gateway 重启后 webauth_doubao/kimi/glm/qwen 全部报 "Tool not found"
- **根因1：** alsoAllow 里工具名没有 `webauth_` 前缀（因为 toolPrefix: true）
- **根因2：** Gateway 重启杀死了 Chrome（LaunchAgent fork 机制）
- **根因3：** GLM 的 `is_networking: false` 未开启联网搜索
- **修复1：** alsoAllow 加上 `webauth_` 前缀，重启 Gateway
- **修复2：** 启动 Chrome-Debug-Profile（端口 9223）
- **修复3：** `webauth-mcp/server.mjs` line 357：`is_networking: true`
- **验证：** 5个工具全部正常

### 6. 绝对不能再犯的错误
- ❌ `osascript -e 'quit app "Google Chrome"'` — 关所有窗口，用户正常页面全丢
- ❌ `--user-data-dir=/tmp/chrome-debug` — 空白 profile，登录状态丢失
- ❌ 用 curl 操作 Chrome DevTools — 无法跳转 URL，只创建 about:blank
- ❌ 没有用 Playwright —放着现成 skill 不用，乱搞
- ❌ Gateway 重启前不确认 Chrome 状态
- ✅ 用 Playwright 连接已有 Chrome（`chromium.connectOverCDP(wsUrl)`）
- ✅ Chrome-Debug-Profile 路径正确
- ✅ 操作前先问用户

### 7. webauth-mcp 修复：SSE流式检测 vs 固定等待（2026-03-22）

**问题**：Doubao/Kimi/GLM/Qwen 四个工具在长回复时超时，因为用了 `waitForTimeout(1000)` 固定等待，不知道AI什么时候回复完成。

**根因**：
1. `goto(timeout: 45000)` 会因页面加载慢而超时
2. `waitForTimeout(1000)` 是固定等待，不管回复有没有开始
3. GLM/Qwen/Kimi 的响应时间是动态的（思考模式30-60秒）

**修复方案**：
1. 去掉 `goto` 的固定 timeout 参数
2. 去掉所有 `waitForTimeout` 固定等待
3. 每个平台用 SSE 的 `done` 信号检测回复完成：
   - Doubao: `data.event === 'message_end' || data.event === 'done'`
   - Kimi: `chunk.op === 'complete' || chunk.result?.finish`
   - GLM: `chunk.status === 'completed' || chunk.done`
   - Qwen: `window._qwenSSEDone === true`（通过 `waitForFunction()` 检测）
4. 最多等 90 秒（`timeout: 90000`）

**架构教训**：
- Node.js 函数（如 `readKimiSSE()`）不能在 `p.evaluate()` 里调用——evaluate 运行在浏览器 V8 上下文，访问不到 Node.js 的函数
- **解决**：把解析逻辑内联到 evaluate 内部，或者用 `waitForFunction()` 检测全局变量

**GLM 特殊问题**：refresh_token 已失效（HTTP 400），无法通过 API 刷新 token
- **解决**：改用 Playwright 注入 fetch 拦截器，在页面上下文捕获 SSE 流，用 cookies 自动认证

**GLM 当前状态**：能返回但思考过程和最终回复混在一起，需要过滤 `think` 类型的 chunk

### 8. webauth-glm 的特殊架构（2026-03-22）

**问题**：GLM 的 token 是 JWT（`chatglm_token`）不是简单的 Bearer token，而且 refresh_token 已失效

**方案**：不用 token 认证，直接用浏览器 cookies
```javascript
const cookies = await ctx.cookies(['https://chatglm.cn']);
const cookieStr = cookies.map(c => `${c.name}=${c.value}`).join('; ');
// 然后注入 fetch 拦截器捕获 SSE
```

**关键区别**：Doubao/Kimi/Qwen 用 API token；GLM 用浏览器 cookies 的 JWT

### 9. Gateway 重启会杀 Chrome（2026-03-22）

**每次重启 Gateway 后必须手动重启 Chrome-Debug-Profile**：
```bash
nohup /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9223 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome/Chrome-Debug-Profile" \
  2>/dev/null &
```

### 10. webauth-mcp v2.0 最终成功（2026-03-22）

**成功**：
- 4个工具全部正常工作（SSE流式检测替代固定等待）
- Doubao/Kimi/Qwen/DeepSeek：API token + SSE done 信号
- GLM：浏览器 cookies JWT + fetch拦截器 + SSE done 信号
- GLM思考过程混入：去重逻辑修复（`t.length >= _lastText.length`）

**失败/教训**：
- Node函数不能在`p.evaluate()`里调用（browser V8隔离）→ 解析逻辑必须内联
- `goto(timeout:45000)` 会因页面慢而失败 → 去掉固定timeout
- GLM refresh_token已失效（HTTP 400）→ 改用浏览器cookies JWT认证
- Gateway重启杀Chrome → 每次重启后手动重开Chrome-Debug-Profile
- 5个webauth工具长调研全部超时 → webauth只适合短问答（<10秒），长调研用subagent

**文件位置**：`~/.openclaw/extensions/webauth-mcp/server.mjs`（v2.0.1）

## 2026-03-23 新增

### 5. webauth 工具 SSE 超时问题（未解决）

**现象**：Chrome 9223 端口正常运行，但 Kimi/GLM/Qwen 的 SSE 流持续超时（45秒），Doubao/DeepSeek 正常。

**可能的根因**：
1. Kimi/GLM/Qwen 的页面 URL 或 cookie 状态问题
2. SSE 流检测逻辑问题：`waitForFunction()` 或 SSE 解析函数在某些平台不触发
3. 页面加载完成但 SSE 流始终不来（平台侧问题）

**正确的应对流程（必须先做！）**：
1. **第一步：记录** → 先把问题写入 LEARNINGS.md / ERRORS.md，不要先动手修
2. 第二步：排查 → 确认是工具问题还是平台页面问题
3. 第三步：修复 → 改代码或调整参数
4. 第四步：验证 → 测试确认修复
5. 第五步：更新记录 → 把修复方案记入文档

**教训**：遇到问题先写下来，不要边修边想。

## 2026-03-23 webauth-mcp 大修复（5平台全部通）

### 问题现象
Chrome 9223 重启后，Kimi/GLM/Qwen 报 SSE 超时（Doubao/DeepSeek 正常）

### 根因（分3层）

**第一层：Token 过期**
- Kimi/GLM/Qwen 的认证 token 存在 `auth-credentials/*.json` 文件里
- 这些 token 是 HTTP-only Cookie，文件里的版本已过期
- 之前 token 是通过 loadCredentials() 从文件读取

**第二层：Kimi API URL 错误**
- 之前 Kimi 用了 `https://moonshot.cn/api/chat/completion`（错误）
- Kimi 正确端点是 `https://www.kimi.com/apiv2/kimi.gateway.chat.v1.ChatService/Chat`

**第三层：Token 获取方式**
- HTTP-only Cookie（kimi-auth）JavaScript `document.cookie` 读不到
- 必须用 Playwright 的 `ctx.cookies()` 读取，再传进 `page.evaluate()`
- 正确流程：Playwright 从浏览器拿 cookie → 注入 page context → 调用 API

### 修复方案

**1. Token 刷新脚本（每次 Gateway 重启后都要做）：**
```javascript
// 用 Playwright 从当前浏览器会话提取 token
const browser = await chromium.connectOverCDP(wsUrl);
const ctx = browser.contexts()[0];
const cookies = await ctx.cookies(['https://www.kimi.com']);
const kimiAuth = cookies.find(c => c.name === 'kimi-auth')?.value;
// 写入 auth-credentials/kimi.json
```

**2. Kimi API URL 修复：**
- ✅ 正确：`https://www.kimi.com/apiv2/kimi.gateway.chat.v1.ChatService/Chat`
- ❌ 错误：`https://moonshot.cn/api/chat/completion`（会返回 HTML）

**3. Kimi Token 获取修复：**
```javascript
// 从浏览器 cookie 获取（不用文件里的）
const cookies = await ctx.cookies(['https://www.kimi.com']);
const kimiAuth = cookies.find(c => c.name === 'kimi-auth')?.value;
if (!kimiAuth) throw new Error('[Kimi] 未找到 kimi-auth Cookie，请在 Chrome 中登录 www.kimi.com');
// 在 page.evaluate 里用 Authorization: Bearer ${kimiAuth} 调用 API
```

**4. GLM/Qwen 直接复用机制：**
- GLM：fetch 拦截器注入到页面，读取 window._glmText
- Qwen：fetch 拦截器注入到页面，读取 window._qwenText
- 两者不需要手动拿 token（拦截器自动捕获）

### 关键教训

1. **HTTP-only Cookie 必须从浏览器读**，不能读文件（文件里的是旧版，会过期）
2. **API URL 必须和页面域名一致**（www.kimi.com 不是 moonshot.cn）
3. **Gateway 重启会杀 Chrome**，Chrome 重启后 token 仍是新的（从浏览器 cookie 刷新）
4. **遇到问题先记录再修复**（已写入 ERRORS.md）

### 验证方法

```javascript
// 快速验证 5 平台是否都通
webauth_doubao_chat("1+1")  // ✅
webauth_kimi_chat("1+1")     // ✅
webauth_glm_chat("1+1")     // ✅
webauth_qwen_chat("1+1")    // ✅
deepseek_deepseek_chat("1+1") // ✅
```

### 错误标识格式（已加上）
- `[Kimi] ...` — Kimi 相关错误
- `[GLM] ...` — GLM 相关错误
- `[Qwen] ...` — Qwen 相关错误

## 2026-03-23 第二次 SSE 超时的教训

### 问题
deep-search 测试时，Kimi/GLM/Qwen 在简单问题（"1+1等于几"）上就超时了，但之前 12:00 测试明明全部通过。

### 可能原因
1. 工具通了之后又超时 → Token 可能在页面刷新时失效
2. Gateway 重启导致 Chrome CDP session 状态变化
3. 长时间未使用的 cookie 自动失效

### 预防措施
- 每次调用失败立即记录，不要等
- 如果工具通了之后又出问题，说明修的是表象，根因还在
- 需要一个"工具健康检查"机制：定期 ping 各平台，发现 Token 失效立即刷新

## [LRN-20260324-001] deep-research-工具检查

**Logged**: 2026-03-24T09:30:00+08:00
**Priority**: high
**Status**: pending
**Area**: docs

### Summary
执行 deep-research 调研前，必须先确认所有工具状态，发现不可用工具要先问用户是修复还是继续

### Details
用户布置了系统性调研 ROBOT-SOP 的任务（10章节深度验证）。Subagent 完成任务后发现 NemoClaw 漏掉了官方文档。用户指出 subagent 没有充分使用所有工具（web_search、web_fetch、5平台并行、subagent 等），而且我没有先用新 Chrome 窗口验证工具状态就开始调研。

**核心问题：**
1. 没有在调研前检查工具是否可用
2. 调研过程中工具状态变化没有及时发现
3. 应该先问用户"工具XX不可用，要先修还是继续用能用的调研"

### Suggested Action
1. 每次 deep-research 前：先检查 webauth 5平台、tavily_search、web_search、sessions_spawn 的可用性
2. 发现工具不可用 → 立即问用户"XXX工具不可用，要先去修复还是直接用能用的工具继续？"
3. 检查结果记录到 HEARTBEAT.md 或 memory/YYYY-MM-DD.md
4. 已将此规范写入 AGENTS.md

### Metadata
- Source: user_feedback
- Related Files: ~/.openclaw/workspace/AGENTS.md, ~/.openclaw/workspace/harness/robot/ROBOT-SOP.md
- Tags: deep-research, tool-check, workflow

---

## [LRN-20260324-002] HTML 模板中 CSS 变量必须包裹 <style> 标签

**Logged**: 2026-03-24T11:41:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: frontend

### Summary
Python f-string 生成 HTML 时，CSS 变量直接插入 `<head>` 会导致浏览器将 CSS 文本当作页面内容显示。

### Details
重构 mdview.py 时，把写死在字符串里的 `<style>` CSS 提取为 `BASE_CSS` 和 `REVIEW_CSS` 变量，但忘记在 f-string 中加回 `<style>` 包裹。
- ❌ 错误：`<title>{title}</title>\n{BASE_CSS}`
- ✅ 正确：`<title>{title}</title>\n<style>{BASE_CSS}</style>`

注意：如果变量值自带标签（如 `REVIEW_JS` 已包含 `<script>`），则不需要额外包裹。

### Suggested Action
1. 重构 HTML 模板时，提取的 CSS/JS 变量要检查是否自带标签
2. 生成后用 grep 确认：`grep -c "<style>" output.html` 应 >= 1
3. 变量命名规范：自带标签的叫 `XXX_HTML`，纯内容的叫 `XXX_CSS`

### Metadata
- Source: bug_fix
- Related Files: tools/mdview.py
- Tags: html, css, template, f-string

## [LRN-20260324-003] large-doc-edit——edit工具处理大文档的正确方式

**Logged**: 2026-03-24T17:55:00+08:00
**Priority**: high
**Status**: resolved
**Area**: docs

### Summary
对数千行大文档做精确编辑时，edit 工具的 oldText 匹配会因隐藏字符、空格、缩进而失败，应该用 Python 脚本读写文件来替代。

### Details
今天两次需要修改 ROBOT-SOP.md（3000+行，约115KB）：
1. 修改 §2.5 五条技术路线（段落内有特殊字符导致 oldText 匹配失败）
2. 移动 GR00T N1.6 章节（涉及多行精确匹配）

edit 工具报错"Could not find the exact text"，即使反复核对行号和内容也找不到差异。原因是段落中的隐含字符（可能有非ASCII字符）、多行字符串中的空白差异。

解决方案：用 Python 脚本 `str.replace()` 精确替换。

### Suggested Action
处理大文档（>500行）的精确编辑时：
1. 优先用 Python 脚本读写文件 + `str.replace()`
2. 如果 edit 报错，先用 `python3 -` 内联脚本确认目标字符串是否真的存在于文件中
3. `repr(content[idx:idx+N])` 比肉眼更容易看到隐藏字符

### Metadata
- Source: error_recovery
- Related Files: harness/robot/ROBOT-SOP.md
- Tags: edit-tool, large-file, python-script
- See Also: LRN-20260323-001 (edit tool whitespace sensitivity)

---

## [LRN-20260324-004] subagent-rate-limit——调研任务不要全开并行

**Logged**: 2026-03-24T18:00:00+08:00
**Priority**: critical
**Status**: resolved
**Area**: infra

### Summary
一次性并行启动 5 个 subagent 调研 + 多轮 tavily/minimax 搜索，触发了 API 限速，导致所有 subagent 全部失败。

### Details
今天调研机器人竞品时：
1. 一次 spawn 5 个 subagent（宇树/Tesla/Atlas/优必选/国产其他）
2. 每轮并行 3-6 个 tavily/minimax 搜索
3. 结果：5 个 subagent 全部报 web_search BRAVE_API_KEY 缺失错误或 Execution context destroyed
4. API 限速导致调研失败

教训：并行调用的 API 有严格限速，应该分批进行，每批不超过 2 个。

### Suggested Action
调研类任务的工作流：
1. 先确认 web_search 工具是否有 API key（没有就不用 web_search）
2. 用 tavily/minimax 等备选工具时，每轮最多 2 个并行
3. 大调研任务拆成多个 session，逐步推进
4. 遇到限速后，等待至少 1 分钟再继续

### Metadata
- Source: error
- Tags: subagent, rate-limit, parallel-execution
- See Also: LRN-20260321-001

---

## [LRN-20260324-005] mini-max-tools-api——minimax search 工具使用注意

**Logged**: 2026-03-24T18:00:00+08:00
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
minimax search 工具连续调用容易被限速，但比 subagent 更可控；tavily 和 minimax 混用可以分散风险。

### Details
今天调研时用 minimax search 连续查了约 10 轮，中途没有被限速。但之前同时开了 5 个 subagent 全部调用 web_search 就触发了限速。

minimax search 的优势：
- 按需调用，不像 subagent 有并发问题
- 每轮耗时 2-5 秒，结果立即返回
- 配合 tavily search 交叉验证

### Suggested Action
调研信息时：
- 主用 minimax search（按需调用）
- 辅用 tavily search（交叉验证）
- subagent 仅在确认不会被限速时使用，或仅用 1 个 agent
- 避免 3 个以上工具同时调用

### Metadata
- Source: best_practice
- Tags: minimax, tavily, rate-limit, research

---

## [LRN-20260324-006] today-summary-20260324——今日工作总结

**Logged**: 2026-03-24T18:00:00+08:00
**Priority**: medium
**Status**: pending
**Area**: docs

### Summary
今天完成了大量 ROBOT-SOP 调研和整合工作，追加了多个新技术章节（竞品/稚晖君/3DGS/NVIDIA）。

### Details
**今日主要工作：**
1. 调研宇树/Tesla Optimus/Atlas/优必选/Figure 等竞品 → 补充到 §2.3.1（电池换电）、§5.1.1（手部自由度）、§6.5（技能训练）
2. 调研稚晖君开源项目（Dummy-Robot/AgiBot World/AimRT）→ 补充到第十章 + 附录 A.X
3. 调研 3D Gaussian Splatting（RoboGSim/LangSplat/MonoGS）→ 补充到 §5.4
4. 调研 NVIDIA 机器人开源生态（Newton/GR00T N1.6/Cosmos/15TB数据集）→ 补充到 §5.3/§5.4/§6.5/附录 A.X
5. 系统优化 ROBOT-SOP（修复目录层级、五条路线分段、GR00T 移位、页脚重复）

**文档数据变化：**
- 起始：v3.3，约 82500 字
- 最终：v3.4，约 115200 字（+32700 字）

### Suggested Action
无

### Metadata
- Source: workflow
- Tags: robot-sop, research, daily-log

## [LRN-20260325-001] mdview --review 解析规则 & 浏览器缓存问题

**Logged**: 2026-03-25T08:54:00+08:00
**Priority**: high
**Status**: resolved
**Area**: tools

### Summary
mdview review 解析器按 `### N.` 标题分割条目，列表项（`- **N**.`）会被完全忽略。HTML 更新后浏览器会显示缓存版本。

### Details
**解析规则：**
- mdview review 解析器按 `### N.` 标题分割条目（正则：`\n###\s*(\d+)\.\s*`）
- 每个 `### N.` 标题 + 下面内容 = 一条 review 条目
- **列表项（`- **N**.`）不会被解析**，会被完全忽略
- 条目编号必须连续

**浏览器缓存问题：**
- HTML 文件更新后，浏览器可能显示缓存的老版本
- 每次用 --review 模式打开文件时，**必须告知用户 Cmd+Shift+R 刷新**
- 不要只说"已刷新"/"已更新"，要明确提示强制刷新

### Suggested Action
1. mdview review 文件必须用 `### N.` 标题格式，不能用列表
2. 每次打开 review 文件后，明确告知用户："请 Cmd+Shift+R 强制刷新"
3. 记录到 TOOLS.md 的 mdview 章节

### Metadata
- Source: bug_fix
- Related Files: tools/mdview.py
- Tags: mdview, review, cache, browser

## [LRN-20260325-002] mdview review HTML 解析深度 bug 修复

**Logged**: 2026-03-25T09:05:00+08:00
**Priority**: critical
**Status**: fixed
**Area**: tools

### Bug 1: 正则表达式在 raw string 中不解释 \u 转义
- **症状**：review 条目里"问题/修正方案/来源"全部不显示
- **根因**：mdview.py 第 438-443 行用了 `r'^\*\*\u539f\u6587\*\*[：:]\s*'` 这样的 raw string，但 raw string 里 `\u` **不被解释为 Unicode 转义**，所以匹配永远失败
- **修复**：把正则改为直接写中文 `r'^\*\*原文\*\*[：:]\s*'`，不用 `\uXXXX` 转义
- **涉及行**：438-443 行（mdview.py）

### Bug 2: section header 被错误包裹进 item div
- **症状**：item-2 的备注框跑到 🟡 中优先级修正标题下面去了
- **根因**：按 `### N.` 分割后，`rest_html = markdown.markdown('\n'.join(lines))` 把 item 内容之后、下一个 `##` 之前的所有东西都包进来了，包括 `## 🟡 中优先级修正`
- **修复**：在分割 lines 时，遇到 `^##\s` 就停止，不把它纳入 item content
- **涉及行**：434-448 行（分割逻辑 + rest_html 生成）

### Bug 3: mdview review 解析器只识别 ### 标题
- **症状**：文件里用列表 `- **3**.**` 的条目全部被忽略
- **根因**：正则 `\n###\s*(\d+)\.\s*` 只能匹配 `### N.` 格式，不匹配列表项
- **修复**：把所有条目改成 `### N.` 标题格式

### Suggested Action
1. mdview review 文件必须用 `### N.` 标题格式，禁止列表格式
2. mdview review 解析器修复后要验证：检查 HTML 中 diff-new/diff-old 是否非空
3. 每次用 --review 模式打开文件时，明确告知用户 Cmd+Shift+R 强制刷新
4. 不要用 `\uXXXX` 在 raw string 里写中文 Unicode，用直接中文更安全

### Metadata
- Source: bug_fix
- Related Files: tools/mdview.py, harness/robot/review/round1-review.md
- Tags: mdview, review, regex, raw-string, unicode
