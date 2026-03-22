# Playwright + Chrome CDP 经验规范

> 最后更新：2026-03-22

## 一、Chrome Debug Profile 信息

### 当前运行状态
| 项目 | 值 |
|------|-----|
| Profile | Chrome-Debug-Profile |
| Profile 路径 | `~/Library/Application Support/Google/Chrome/Chrome-Debug-Profile` |
| 调试端口 | 9223 |
| WebSocket URL | 动态（每次重启 Chrome 变化）|
| 获取方式 | `curl -s http://127.0.0.1:9223/json/version` |
| Chrome 进程数 | ~12（含 Helper 进程）|
| 启动命令 | 见下方 |

### 启动命令（正确方式）
```bash
nohup /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9223 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome/Chrome-Debug-Profile" \
  2>/dev/null &
```

### 不要这样做
- ❌ 不要用 `--user-data-dir=/tmp/chrome-debug`（空白 profile，丢失所有登录状态）
- ❌ 不要用 `--user-data-dir=其他新路径`
- ❌ 不要用 `osascript -e 'quit app "Google Chrome"'`（关所有窗口）
- ❌ 不要在 Gateway 重启前不确认 Chrome 状态

---

## 二、Playwright 连接 Chrome CDP

### 方式1：WebSocket URL（webauth-mcp 使用）
```javascript
const { chromium } = require('playwright');
// 获取 WS URL
const wsUrl = /* 从 curl http://127.0.0.1:9223/json/version 获取 */;
const browser = await chromium.connectOverCDP(wsUrl);
const ctx = browser.contexts()[0];
```

### 方式2：HTTP URL + Ephemeral Header（zhiku headless 脚本使用）
```javascript
const { chromium } = require('playwright');
// 注意：zhiku 用的是 18800 端口！
const browser = await chromium.connectOverCDP('http://127.0.0.1:18800', {
    headers: { 'Client-Wants-Ephemeral-DevTools-Context': 'true' }
});
const ctx = browser.contexts()[0];
```
- **ephemeral header** 的作用：创建隔离的新 CDP context，不影响也不可见已有页面
- 适用于：脚本自动化，不干扰用户现有页面

---

## 三、端口对应关系

| 端口 | 用途 | 说明 |
|------|------|------|
| **9223** | Chrome-Debug-Profile（5个AI页面）| webauth-mcp 连接端口 |
| 18792 | Browser Relay（OpenClaw 扩展）| OpenClaw 内置 |
| 18800 | 旧版 zhiku headless 脚本 | 仅作参考，已废弃 |

---

## 四、zhiku Headless 工作流核心规范（v0.5）

> 来源：`skills/zhiku/智库headless工作流v0.5.md`

### 4.1 平台配置
| 平台 | URL | 高级模式 | 新建对话方式 |
|------|-----|----------|--------------|
| 千问 | https://chat.qwen.ai/ | 默认 | page.goto() 重新加载 |
| 智谱 | https://chatglm.cn/ | 思考+联网 | page.goto() 重新加载 |
| Kimi | https://www.kimi.com/ | Kimi思考 | Command+K |
| 豆包 | https://www.doubao.com/chat/ | 专家模式 | Command+K |
| DeepSeek | https://chat.deepseek.com/ | 深度思考+智能搜索 | page.goto() 重新加载 |

### 4.2 新建对话策略
- **Command+K**：豆包、Kimi（键盘快捷键）
- **page.goto()**：千问、智谱、DeepSeek（重新加载当前 URL）

### 4.3 等待回复检测
用 DOM 元素检测，不用固定时间：
```javascript
await page.waitForFunction(() => {
    const body = document.body.innerText;
    return body.includes('已思考') || 
           body.includes('正在搜索') || 
           body.includes('已完成') ||
           body.includes('参考') ||
           body.includes('已阅读') ||
           body.includes('思考结束') ||
           (body.length > 200 && body.split('\n').length > 5);
}, { timeout: 30000 });
```

### 4.4 获取内容
- 不限制行数（移除 slice(-50)）
- 优先查 data-role="assistant" 等选择器
- 备用：`document.body.innerText`

### 4.5 任务分配（最多3个subagent）
- **s1**：豆包 + Kimi（Command+K 组）
- **s2**：千问 + DeepSeek（page.goto() 组）
- **s3**：智谱（单独，给予更长等待时间 45s+）

### 4.6 常见错误修复
1. **获取到历史对话** → 用 Command+K 或 page.goto() 新建对话
2. **等待超时** → 用 DOM 检测替代固定时间
3. **内容不完整** → 移除行数/字符限制
4. **60秒 subagent 超时** → 分离平台到不同 subagent

---

## 五、webauth-mcp 工作机制

### 5.1 连接方式
- 通过 `chromium.connectOverCDP(WS_URL)` 连接 Chrome 9223
- WS URL 从 `http://127.0.0.1:9223/json/version` 获取
- 复用已有 context 中的已有页面

### 5.2 复用逻辑
```javascript
const ctx = b.contexts()[0];
const pg = ctx.pages().find(pg => pg.url().includes('doubao')) || await ctx.newPage();
```

### 5.3 当前问题
- Gateway 重启会杀掉 Chrome（因为 Gateway fork 了 Chrome 进程？）
- webauth-mcp 的 CDP 连接缓存旧的 WS URL
- 解决：Gateway 重启后，Chrome 重新启动，webauth server 重建连接

### 5.4 Gateway 重启正确顺序
1. 杀 Chrome（用 profile 路径精确匹配，不杀所有 Chrome）
2. 重启 Gateway
3. 重新启动 Chrome（用正确的 profile）
4. 验证 webauth 工具

---

## 六、经验教训（2026-03-22）

### 重大失误
1. **用 osascript 关闭所有 Chrome** → 用户正常浏览页面全部丢失
2. **创建新 profile** → `/tmp/chrome-debug` 是空白 profile，登录状态丢失
3. **用 curl 操作 Chrome 标签页** → `curl /json/new` 创建的是 about:blank，无法跳转 URL
4. **没有用 Playwright** → 放着现成的 Playwright skill 不用，自己乱搞

### 正确做法
1. Gateway 重启前，先用 `pgrep -f "Chrome.*Chrome-Debug-Profile"` 确认 Chrome 状态
2. 只杀特定 Chrome 实例（用进程名匹配），不杀所有 Chrome
3. 始终用已有正确 profile，不创建新的
4. 页面操作用 Playwright，不尝试 curl/其他方式
5. 先读 SKILL.md 找正确 API，再执行

---

## 七、文件路径速查

| 用途 | 路径 |
|------|------|
| Playwright SKILL.md | `~/.openclaw/workspace/skills/playwright-api/SKILL.md` |
| zhiku 工作流文档 | `~/.openclaw/workspace/skills/zhiku/智库headless工作流v0.5.md` |
| Chrome Profile | `~/Library/Application Support/Google/Chrome/Chrome-Debug-Profile` |
| Playwright 源码 | `~/.openclaw/extensions/playwright-mcp-server/node_modules/playwright/` |
| webauth MCP | `~/.openclaw/extensions/webauth-mcp/server.mjs` |
