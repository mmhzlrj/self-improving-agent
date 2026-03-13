# LEARNINGS.md - 经验教训记录

> 重要：所有错误和经验教训都应该记录在这里，方便下次遇到同样问题时查阅。

---

## 2026-03-11

### 主题：豆包网页版自动化对话

#### 失败的尝试

**1. 直接 API 调用**
- 方法：`curl` 直接调用豆包 API
- 结果：❌ 失败，需要 `a_bogus` 签名参数
- 原因：豆包 API 需要动态生成的防爬虫签名

**2. osascript 激活窗口输入**
- 方法：`osascript` 激活 Chrome → 输入 → 发送
- 结果：⚠️ 窗口会跳到最前面，打扰用户
- 原因：每次操作都需要激活目标应用

**3. JavaScript 键盘事件模拟**
- 方法：`dispatchEvent(new KeyboardEvent("keydown", {key: "Enter"}))`
- 结果：❌ 不稳定，豆包页面检测到是自动化操作
- 原因：豆包有反自动化机制，JavaScript 模拟的键盘事件被拦截

**4. DOM 点击发送按钮（第一次尝试）**
- 方法：`document.querySelector('button').click()`
- 结果：❌ 不触发发送
- 原因：豆包使用 React + 自定义事件处理，简单的 click() 不够

#### 成功的方案

**最终方案：纯 Browser Relay + CSS 选择器遍历父容器**
- 方法：
  1. `document.querySelector('textarea')` 找到输入框
  2. 设置 `value` 并触发 `input` 事件
  3. **遍历父容器**，找到带 SVG 的按钮并点击
  4. 使用 `openclaw browser evaluate` 执行 JavaScript
- 结果：✅ 成功，零窗口跳动
- 关键代码：
  ```javascript
  var parent = textarea.parentElement;
  while (parent && parent.tagName !== 'BODY') {
      var btns = parent.querySelectorAll('button');
      for (var i = btns.length - 1; i >= 0; i--) {
          if (btns[i].querySelector('svg')) {
              btns[i].click();
              return 'sent';
          }
      }
      parent = parent.parentElement;
  }
  ```

---

## 2026-03-10

### Browser Relay 调试经验

#### 错误记录

**ERR-20260310-001**: 消息缓冲机制问题
- 问题：用户说"停下来"后消息仍在队列中执行
- 解决：**执行交给 subagents，我负责终止**

**ERR-20260310-004**: Browser Relay 连接失败
- 问题：使用了错误方法 `openclaw browser start`
- 教训：**禁止使用 openclaw browser 命令**，这些命令会创建新 Chrome 进程

**ERR-20260310-005**: 没用 subagents 自己执行任务
- 问题：调试时自己执行了任务
- 教训：按照 SOUL.md 规则，执行交给 subagents

**ERR-20260310-007, ERR-20260310-008**: 使用 openclaw browser 命令错误
- 解决：用 osascript 代替

#### 重要规则

1. **禁止自己执行任务**，交给 subagents
2. **指令不明确时**，先列出可能性让用户选择
3. **Browser Relay 问题**：用 osascript 代替 openclaw browser 命令

---

## 2026-03-09

### 微信公众号文章获取

#### 失败的尝试
1. **curl 直接请求** → 返回"环境异常"验证页面
2. **jina.ai 服务** → 请求超时

#### 成功方法
- 使用 `openclaw browser open "链接"` 打开页面
- 使用 `openclaw browser snapshot --json` 获取内容
- 关键：**微信公众号需要登录态，OpenClaw Browser 可以保持登录**

#### 重要要点
1. 微信公众号文章需要登录态
2. 不要用 curl/网络请求工具直接抓取
3. 优先使用 OpenClaw 自带浏览器

---

## 2026-03-09

### 豆包自动化输入技术

#### 问题
豆包页面使用 React 动态渲染，aria-ref 不稳定

#### 解决
使用 JavaScript 注入直接操作 DOM：
1. `document.querySelector('div[role="textbox"]')?.focus()` 聚焦
2. `document.execCommand('insertText', false, '文字')` 输入

---

## 2026-03-09

### Homebrew Node 安装问题

#### 问题
VPN 代理配置未清理导致 brew 无法连接

#### 解决
```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY
```

---

## 2026-03-08

### MiniMax Tools 调试

#### 问题
必须添加 model 参数，图片 URL 必须是字符串格式

---

## 2026-03-07

### 子Agent任务经验

#### Agent 1: OpenClaw Lite 调研
- 结论：存在社区轻量版（nanobot, nanoclaw, clawlet），但它们是独立实现，**不支持连接 Gateway**

#### Agent 2: Cyber Bricks 调研
- 接入方案：WiFi HTTP / MQTT / WebSocket

#### Agent 3: Ubuntu 台式机对接 Gateway
- 命令：`openclaw node run --host <Gateway-IP> --port 18789`

---

## 2026-03-06

### QQ 机器人配置

#### 关键教训
- **OCR 识别容易把字母 O 和数字 0 混淆**
- 识别结果：`KU03...` → 正确：`KUO3...`
- **配置完成后务必核对原始图片中的字符**

---

## 2026-03-06

### 图片管理优化

#### 解决方案
创建各平台专用目录：
- 飞书：`~/.openclaw/workspace/feishu-images/`
- Telegram：`~/.openclaw/workspace/telegram-images/`
- Discord：`~/.openclaw/workspace/discord-images/`
- WhatsApp：`~/.openclaw/workspace/whatsapp-images/`
- Signal：`~/.openclaw/workspace/signal-images/`
- WeChat：`~/.openclaw/workspace/wechat-images/`

#### 命名规则
精确到秒：`YYYY-MM-DD-HH-mm-ss.png`

---

## 重要安全规则

1. **危险命令必须先确认**：删除、移动等操作前先问用户
2. **rm -rf 不能随便用**：删除前先检查内容，问用户确认
3. **不要在没确认的情况下合并目录**：先检查有没有重要数据

---

## 相关文件

- Skill: `~/.openclaw/workspace/skills/doubao-osascript/`
- 日志: `~/.openclaw/workspace/memory/2026-03-*.md`
- Browser Relay: `~/.openclaw/workspace/memory/browser-relay-*.md`

---

## 重要规则（必须遵守）- 2026-03-11

### 1. 图片分析必须用 minimax-tools
- ❌ 禁止用 exec + read 命令读取图片
- ✅ 必须用 `python3 ~/.openclaw/workspace/skills/minimax-tools/minimax.py image` 命令
- ⚠️ 工具输出为空时，很可能是用错工具了

### 2. 测试时必须等待用户指示
- 用户说执行哪步就执行哪步
- ❌ 禁止自动执行后续步骤
- ✅ 等用户明确指示后再继续

### 3. DeepSeek 自动化要点
- JavaScript 设置 value 无效（页面不显示）
- 必须用 osascript + 键盘输入
- 用 cliclick 点击坐标激活输入框
- 然后用 osascript 逐字输入
- **重要**：osascript 命令要**合并成一次执行**，不能分多次（会内容连在一起）

### 4. DeepSeek 截图要点
- 截图前必须先确认窗口是否正确
- 不要假设页面是对的，必须先验证
- 用 minimax.py 分析整个 Chrome 窗口，确认是哪个页面

### 5. DeepSeek 发送要点
- 发送前必须确保窗口激活
- 先 `osascript -e 'tell application "Google Chrome" to activate'`
- 然后再按回车发送

### 6. 后台键盘输入不可能的原因（豆包分析）

#### 三层安全机制
1. **macOS**：Accessibility API 要求目标应用必须前台
2. **Chrome**：检测 `isTrusted` 属性
3. **DeepSeek 前端**：丢弃 `isTrusted=false` 的事件

#### 可行方案
| 方案 | 难度 | 说明 |
|------|------|------|
| DeepSeek API | ⭐ | 付费，稳定 |
| 网络请求逆向 | ⭐⭐⭐ | 模拟 HTTP 请求 |
| Playwright + Stealth | ⭐⭐⭐⭐ | 反检测插件 |
| 虚拟桌面 | ⭐ | osascript + 切换桌面 |

#### 结论
- ❌ 不要尝试 osascript/dispatchEvent 模拟键盘
- ✅ 豆包/千问/智谱/Kimi 可以用 JavaScript 后台发送
- ✅ DeepSeek：可以用 Playwright CDP 后台发送！

### 7. Playwright CDP 后台发送（成功！）

#### 尝试过程
1. ❌ 直接用 curl 调用 CDP API - 失败
2. ✅ 用 Playwright 连接 CDP - 成功！

#### 关键发现
- Browser Relay 端口 18800 就是 CDP 端口
- 可以用 Playwright 连接并控制

#### 代码
```javascript
const { chromium } = require('playwright');

const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
const ctx = browser.contexts()[0];

for (const p of ctx.pages()) {
    if (p.url().includes('deepseek')) {
        // 输入
        await p.fill('textarea', '问题');
        // 发送
        await p.keyboard.press('Enter');
    }
}
```

#### 验证结果
- 输入成功：✅
- 发送成功：✅
- 后台运行：✅（窗口不跳动）

### 8. Playwright CDP 通用代码（5个平台测试通过）

```javascript
const { chromium } = require('playwright');

const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
const ctx = browser.contexts()[0];

for (const p of ctx.pages()) {
    if (p.url().includes('平台域名')) {
        // 通用输入（textarea 或 div）
        const textarea = p.locator('textarea');
        const editable = p.locator('div[contenteditable=true]');
        
        if (await textarea.count() > 0) {
            await textarea.first().fill('问题');
        } else if (await editable.count() > 0) {
            await editable.first().fill('问题');
        }
        
        // 发送
        await p.keyboard.press('Enter');
    }
}
```

| 平台 | 选择器 | CDP 状态 |
|------|--------|----------|
| DeepSeek | textarea | ✅ |
| 豆包 | textarea | ✅ |
| 千问 | textarea | ✅ |
| 智谱 | textarea | ✅ |
| Kimi | div[contenteditable] | ✅ |

### 9. 平台模型设置

| 平台 | 需要设置的模式 | 选择器/Ref |
|------|----------------|------------|
| DeepSeek | 深度思考 | button:has-text("深度思考") |
| 豆包 | 专家模式 | button:has-text("快速") → menuitem:has-text("专家") |
| 千问 | 思考模式 | 自动 → option:has-text("思考") |
| 智谱 | 思考+联网 | 点击按钮开启 |
| Kimi | 思考模式 | 默认已是思考模式 |

### 设置脚本

```bash
# DeepSeek - 打开深度思考
openclaw browser click e36

# 豆包 - 切换到专家
openclaw browser click e1070  # 快速按钮
openclaw browser click e1182  # 专家选项

# 千问 - 切换到思考
openclaw browser click e86    # 自动按钮
openclaw browser click e116  # 思考选项

# 智谱 - 打开思考和联网
openclaw browser click e117  # 思考
openclaw browser click e119  # 联网
```

### 10. 平台设置脚本优化过程

#### v1.0 (cdp-setup.sh)
- 硬编码 ref
- 问题：每次页面加载 ref 都变

#### v2.0 (cdp-setup-dynamic.sh)
- 尝试用 grep 动态获取 ref
- 问题：bash 语法复杂，解析有问题

#### v3.0 (cdp-setup-v3.sh) - 当前版本
- 简化版：每次只获取第一个匹配的 ref
- 特点：
  - 统一流程：snapshot → grep → click
  - 简化选择器：用文本匹配
  - 代码简洁易维护
- 测试结果：5/5 平台成功
- 文件：`~/.openclaw/workspace/scripts/cdp-setup-v3.sh`

#### v3.2 (cdp-setup-v3.sh) - 最终版
- 添加 all 模式导航
- 每个平台设置前先 navigate 到对应 URL
- 测试结果：5/5 全部成功

### 11. Subagent 工作流设计原则

**分配逻辑**：
- subagent1 分配：千问、智谱、Kimi（3个）
- subagent2 分配：豆包、DeepSeek（2个）
- 先后动的时间差被充分利用

**subagent1**：
```
步骤1：打开千问网页 → 提问
步骤2：打开智谱网页 → 提问
步骤3：打开Kimi网页 → 提问
步骤4：切换到豆包网页 → 收集回复
步骤5：切换到DeepSeek网页 → 收集回复
```

**subagent2**：
```
步骤1：打开豆包网页 → 提问
步骤2：打开DeepSeek网页 → 提问
步骤3：切换到千问网页 → 收集回复
步骤4：切换到智谱网页 → 收集回复
步骤5：切换到Kimi网页 → 收集回复
```

**关键点**：
- 利用 subagent 先后动的时间差
- Browser Relay 是 Chrome 插件，多个标签页共享
- 通过 CDP 可以获取同一个 Chrome PID 下的所有标签页

**表述方式**：
- ❌ 错误："直接切换到已打开的标签页"
- ✅ 正确："如果之前没关，就直接接着问，如果关了就重新打开"

### 12. Subagent 工作流实战（两个 subagent 配合）

**核心问题**：
- 2个 subagent 如何分工合作？
- 如何复用已打开的页面？

**工作流设计**：
- subagent1：千问→智谱→Kimi（提问），然后收集豆包/DeepSeek
- subagent2：豆包→DeepSeek（提问），然后收集千问/智谱/Kimi
- 关键：同时开始，复用已有页面

**技术实现**：
- findOrOpen 函数：先查已有页面，找到就复用，找不到才打开
- 复用逻辑：用 URL 关键词匹配

**错误记录**：
1. ❌ 打开空白 URL - "doubao.com" 导致 invalid URL
   - 修复：使用完整 URL "https://www.doubao.com/chat/"
2. ❌ 每次都打开新页面 - 导致重复窗口
   - 修复：先检查现有页面，复用而非新建

**最终脚本**：
- zhiku-subagent1.js - 负责 3 个平台提问 + 2 个平台收集
- zhiku-subagent2.js - 负责 2 个平台提问 + 3 个平台收集

**测试结果**：
- 全部复用已有页面，没有打开新页面
- 5 个平台的回复都成功获取

### 13. 真正的后台模式 (CDP)

**方案**：
- 使用 Playwright CDP 连接到 Browser Relay
- 通过 `Client-Wants-Ephemeral-DevTools-Context` 头实现真正后台
- 复用已有页面，无需登录

**脚本**：
- zhiku-s1.js - subagent1 (千问→智谱→Kimi→收集豆包/DeepSeek)
- zhiku-s2.js - subagent2 (豆包→DeepSeek→收集千问/智谱/Kimi)

**关键代码**：
```javascript
const browser = await chromium.connectOverCDP('http://127.0.0.1:18800', {
    headers: { 'Client-Wants-Ephemeral-DevTools-Context': 'true' }
});
```

**优势**：
- 无窗口跳动
- 复用已登录会话
- 真正的后台操作

### 14. 智库工作流实战总结

#### 试错过程

1. **同时派发导致重复打开**
   - 最初每个 subagent 都尝试打开全部5个页面
   - 导致重复窗口

2. **URL 错误**
   - "doubao.com" → "invalid URL"
   - 修复：使用完整 URL

3. **Headless 需要登录**
   - chromium-headless-shell 无法登录
   - 修复：CDP 连接已有会话

4. **自动启动打开 Google**
   - 中国大陆无法访问
   - 修复：改用百度

#### 最终方案

```javascript
// CDP 后台模式
const browser = await chromium.connectOverCDP('http://127.0.0.1:18800', {
    headers: { 'Client-Wants-Ephemeral-DevTools-Context': 'true' }
});
```

#### 关键代码

```javascript
// 复用已有页面
async function findOrOpen(url, name) {
    for (const p of ctx.pages()) {
        if (p.url().includes(url.replace('https://', '').split('/')[0])) {
            return p;  // 复用
        }
    }
    // 没找到才打开新页面
    const page = await ctx.newPage();
    await page.goto(url);
    return page;
}
```

### 15. 多轮收集轮询优化

**问题**：AI 生成回复需要时间，单次收集可能获取不到

**解决方案**：多轮轮询收集

```javascript
const MAX_ROUNDS = 3;

for (let round = 1; round <= MAX_ROUNDS; round++) {
    // 检查每个平台是否有新回复
    if (text.includes(QUESTION.slice(0, 5))) {
        console.log("已收集");
        collected[name] = true;
    }
    
    // 检查是否全部完成
    if (全部收集完成) break;
    
    // 等待下一轮
    await new Promise(r => setTimeout(r, 10000));
}
```

**测试结果**：
- 3轮轮询，每轮间隔10秒
- 自动检测问题关键词判断是否有新回复
- 5个平台回复全部成功获取

### 16. 智库 subagent 方案

#### 痛点
- 脚本输出合并到一个内容块
- 无法看到独立步骤进度

#### 方案
使用 subagent 并行执行，每个 subagent 独立输出

#### 架构
- 5个 subagent 并行运行
- 复用现有浏览器标签页
- 每个步骤/回复独立显示

#### 总结块格式
```
【总结】
收到 X/5 个平台的回复：
千问：简短观点
智谱：简短观点
...
综合观点：...
```

#### 测试验证
- sessions_spawn 测试成功
- 每个 subagent 输出是独立内容块

### 工作模式定义

#### 测试模式
- 每一步都要听用户指挥
- 问了才能做
- 用于调试和验证

#### 自动模式
- 自己按照流程自主执行
- 遇到问题自己判断解决
- 用于正式运行

### 测试模式规则

**停下来 = 停掉所有运作中的 subagents**
- 立即执行 subagents kill
- 不能只是暂停或等待

### 创建新对话的方法（按平台）

| 平台 | 方法 |
|------|------|
| 豆包 | Command+K 快捷键 |
| 千问 | + 按钮 |
| 智谱 | + 按钮 |
| Kimi | Command+K 快捷键 |
| DeepSeek | + 按钮 |

### 调试时的原则

1. **只检查需要的页面**：检查千问就只检查千问，不要打开豆包和Kimi
2. **只做必要的操作**：不需要的操作不要做，避免浪费资源
3. **先想清楚再行动**：不要想一出是一出

### 各平台高级模型选择

| 平台 | 高级模式 |
|------|----------|
| 豆包 | 专家模式 |
| Kimi | 思考模式 |
| DeepSeek | 深度思考 + 智能搜索 |
| 千问 | 默认 |
| 智谱 | 思考 + 联网 |

### 智库 Skill 激活方式
- 看到"智库"关键字时，激活此技能执行问答

### 待修复BUG - 智库 Skill

1. **无头模式**：不打开用户可见的Chrome标签页
2. **网页正常打开**：确保页面加载完成
3. **正确收集回复**：找到对的按钮
4. **保存本地文件**：把回复保存到文件
5. **读取总结**：读取文件并总结给用户

### 智库测试结果判断标准

**成功**：获取到当前问题的完整回复
**失败**：历史列表、搜索中、空白

---

## 2026-03-12 智库v0.5优化 - 复制按钮点击方案

### 问题背景
当前智库脚本存在以下问题：
1. 千问输入框readonly超时
2. 获取内容不完整/获取到历史对话
3. 应该用复制按钮而非innerText获取内容

### AI回复优化方案（来自智库5个平台）

#### 1. 等待回复完成
不要只等"正在搜索"，要等以下标记出现：
- "已完成"、"参考"、"已阅读"、"思考结束"
- 或检测到复制按钮出现

#### 2. 复制按钮选择器（各平台）

| 平台 | 选择器 |
|------|--------|
| 千问 | `button[aria-label*="复制"]` 或 `button:has-text("复制")` |
| 智谱 | `button[title*="复制"]` |
| 豆包 | `button[aria-label*="复制"]` 或 `.copy-icon` |
| Kimi | `button[aria-label*="复制"]` |
| DeepSeek | `button[aria-label*="Copy"], button[aria-label*="复制"]` |

#### 3. 点击策略
```javascript
// 先找到最后一条AI回复容器
const lastAssistant = page.locator('[data-role="assistant"]').last();

// 在回复容器内找复制按钮
const copyBtn = lastAssistant.locator('button[aria-label*="复制"]');

// 等待按钮可见（有些平台需要hover才显示）
await copyBtn.waitFor({ state: 'visible' });
await copyBtn.click();

// 如果按钮隐藏，先hover回复容器
await lastAssistant.hover();
await page.waitForTimeout(300);
```

#### 4. 从剪贴板读取内容
```javascript
const content = await page.evaluate(async () => {
    return await navigator.clipboard.readText();
});
```

#### 5. 完整collect函数示例
```javascript
async function collect(page, name) {
    if (!page) return;
    
    // 等待回复完成
    await page.waitForFunction(() => {
        const body = document.body.innerText;
        return body.includes('已完成') || 
               body.includes('参考') ||
               body.includes('已阅读') ||
               body.includes('思考结束');
    }, { timeout: 60000 });
    
    // 等待额外渲染时间
    await page.waitForTimeout(2000);
    
    // 点击复制按钮
    try {
        const copyBtn = page.locator('button[aria-label*="复制"], button:has-text("复制")').last();
        await copyBtn.waitFor({ state: 'visible', timeout: 5000 });
        await copyBtn.click();
        await page.waitForTimeout(500);
        
        // 从剪贴板读取
        const content = await page.evaluate(async () => {
            return await navigator.clipboard.readText();
        });
        
        saveToFile(name, content);
    } catch(e) {
        // 备用：用innerText
        const text = await page.evaluate(() => document.body.innerText);
        saveToFile(name, text);
    }
}
```

### 文件位置
- 脚本：`~/.openclaw/workspace/skills/zhiku/scripts/zhiku-s1-v4.js`
- 文档：`~/.openclaw/workspace/skills/zhiku/智库headless工作流v0.4.md`
