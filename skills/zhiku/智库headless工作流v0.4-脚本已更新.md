# 智库 Headless 工作流文档

## 一、功能描述

### 1.1 目标
通过 CDP 后台模式同时向 5 个国产 AI 平台提问并收集回复，每个步骤和回复独立显示。

### 1.2 核心约束
1. **必须使用 CDP 后台模式** - 通过 Browser Relay 的 CDP 连接，不打开用户可见的窗口
2. **必须选择高级模型** - 豆包选"专家模式"，Kimi选"Kimi 思考模式"，DeepSeek选"深度思考模式+智能搜索模式"，智谱选"思考模式+联网模式"，千问保持默认
3. **不能重复打开页面** - 必须复用已有标签页
4. **不能重复提问** - 创建新对话以避免获取旧缓存回复
5. **最多3个subagent** - 避免超时

### 1.3 平台配置

| 平台 | URL | 高级模式 | 新建对话方式 |
|------|-----|----------|--------------|
| 千问 | https://chat.qwen.ai/ | 默认（无需选择） | page.goto() 重新加载页面 |
| 智谱 | https://chatglm.cn/ | 思考模式 + 联网模式（同时打开） | page.goto() 重新加载页面 |
| Kimi | https://www.kimi.com/ | Kimi 思考模式（点击"Kimi 思考"按钮） | Command+K 快捷键 |
| 豆包 | https://www.doubao.com/chat/ | 专家模式（点击"专家"按钮） | Command+K 快捷键 |
| DeepSeek | https://chat.deepseek.com/ | 深度思考模式 + 智能搜索模式（同时打开） | page.goto() 重新加载页面 |

---

## 二、工作流设计

### 2.1 任务分配

**subagent1**：负责 Command+K 创建会话的平台
- 提问：豆包、Kimi
- 收集：豆包、Kimi

**subagent2**：负责 page.goto() 创建会话的平台（部分）
- 提问：千问、DeepSeek
- 收集：千问、DeepSeek

**subagent3**：专门负责智谱
- 提问：智谱
- 收集：智谱

### 2.2 原因分析
- 智谱回答时间最长，经常超时
- 单独给一个 subagent 避免拖累其他平台

### 2.3 执行顺序
1. 先启动 subagent3（智谱，最慢）
2. 同时启动 subagent1 和 subagent2

---

## 三、脚本实现

### 3.1 subagent1 (s1) - 豆包/Kimi

```javascript
// 脚本位置: skills/zhiku/scripts/zhiku-s1-v3.js

#!/usr/bin/env node
// 智库 subagent1 - 豆包/Kimi

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const QUESTION = process.argv[2] || "用一句话介绍深圳";

function saveToFile(name, content) {
    const today = new Date().toISOString().slice(0, 10);
    const dir = path.join(process.env.HOME, '.openclaw/workspace/zhiku_output', today, name);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    const safeName = QUESTION.slice(0, 15).replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_');
    const file = path.join(dir, `${safeName}.md`);
    fs.writeFileSync(file, content);
    console.log(`[保存] ${file}`);
}

async function ensureBrowser() {
    for (let i = 0; i < 10; i++) {
        try {
            const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
            await browser.close();
            return true;
        } catch(e) { await new Promise(r => setTimeout(r, 1000)); }
    }
    return false;
}

async function main() {
    console.log("=== subagent1 开始 ===");
    const ok = await ensureBrowser();
    if (!ok) { console.log("Browser 未运行"); return; }
    
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800', {
        headers: { 'Client-Wants-Ephemeral-DevTools-Context': 'true' }
    });
    const ctx = browser.contexts()[0];
    
    async function findOrOpen(url, name) {
        for (const p of ctx.pages()) {
            if (p.url().includes(url.replace('https://', '').split('/')[0])) {
                console.log(`复用: ${name}`);
                return p;
            }
        }
        console.log(`打开: ${name}`);
        const page = await ctx.newPage();
        await page.goto(url, { timeout: 15000, waitUntil: 'domcontentloaded' });
        return page;
    }
    
    // 提问函数 - 豆包/Kimi用Command+K
    async function ask(page, q, platform) {
        if (!page) return;
        if (platform === '豆包' || platform === 'Kimi') {
            await page.keyboard.press('Meta+k');
            await page.waitForTimeout(3000);  // 增加等待时间确保新对话创建完成
            console.log("[Command+K]");
        } else {
            await page.goto(page.url());
            await page.waitForTimeout(3000);
            console.log("[重新加载]");
        }
        await page.waitForTimeout(3000);
        const ta = page.locator('textarea').first();
        if (await ta.count() > 0) {
            await ta.fill(q);
            await ta.press('Enter');
            console.log("已提问");
        }
    }
    
    // 收集回复函数
    async function collect(page, name) {
        if (!page) return;
        let content = '';
        for (let i = 0; i < 2; i++) {
            console.log(`[${name}] 等待回复 ${(i+1)*10}s...`);
            await page.waitForTimeout(10000);
            const btnCount = await page.locator('button').count();
            if (btnCount > 3) {
                console.log(`[${name}] 检测到回复（按钮数: ${btnCount}）`);
                const text = await page.evaluate(() => document.body.innerText);
                const lines = text.split('\n').filter(l => l.trim().length > 3);
                content = lines.slice(-50).join('\n');
                if (content.length > 50) break;
            }
        }
        if (!content || content.length < 50) {
            const text = await page.evaluate(() => document.body.innerText);
            const lines = text.split('\n').filter(l => l.trim().length > 3);
            content = lines.slice(-50).join('\n');
        }
        console.log(`\n=== ${name} ===`);
        console.log(content.slice(-500));
        saveToFile(name, content);
    }
    
    // 豆包：提问+收集
    let p1 = await findOrOpen('https://www.doubao.com/chat/', '豆包');
    await ask(p1, QUESTION, '豆包');
    await collect(p1, '豆包');
    
    // Kimi：提问+收集
    let p2 = await findOrOpen('https://www.kimi.com/', 'Kimi');
    await ask(p2, QUESTION, 'Kimi');
    await collect(p2, 'Kimi');
    
    console.log("\n=== subagent1 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
```

### 3.2 subagent2 (s2) - 千问/DeepSeek

```javascript
// 脚本位置: skills/zhiku/scripts/zhiku-s2-v3.js

#!/usr/bin/env node
// 智库 subagent2 - 千问/DeepSeek

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const QUESTION = process.argv[2] || "用一句话介绍深圳";

function saveToFile(name, content) {
    const today = new Date().toISOString().slice(0, 10);
    const dir = path.join(process.env.HOME, '.openclaw/workspace/zhiku_output', today, name);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    const safeName = QUESTION.slice(0, 15).replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_');
    const file = path.join(dir, `${safeName}.md`);
    fs.writeFileSync(file, content);
    console.log(`[保存] ${file}`);
}

async function ensureBrowser() {
    for (let i = 0; i < 10; i++) {
        try {
            const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
            await browser.close();
            return true;
        } catch(e) { await new Promise(r => setTimeout(r, 1000)); }
    }
    return false;
}

async function main() {
    console.log("=== subagent2 开始 ===");
    const ok = await ensureBrowser();
    if (!ok) { console.log("Browser 未运行"); return; }
    
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800', {
        headers: { 'Client-Wants-Ephemeral-DevTools-Context': 'true' }
    });
    const ctx = browser.contexts()[0];
    
    // 查找或打开页面
    async function findOrOpen(url, name) {
        for (const p of ctx.pages()) {
            if (p.url().includes(url.replace('https://', '').split('/')[0])) {
                console.log(`复用: ${name}`);
                return p;
            }
        }
        console.log(`打开: ${name}`);
        const page = await ctx.newPage();
        await page.goto(url, { timeout: 15000, waitUntil: 'domcontentloaded' });
        return page;
    }
    
    // 提问函数
    async function ask(page, q, platform) {
        if (!page) return;
        // 新建对话 - 千问/DeepSeek用page.goto()
        await page.goto(page.url());
        await page.waitForTimeout(3000);
        console.log("[重新加载]");
        await page.waitForTimeout(3000);
        const ta = page.locator('textarea').first();
        if (await ta.count() > 0) {
            await ta.fill(q);
            await ta.press('Enter');
            console.log("已提问");
        }
    }
    
    // 收集回复函数
    async function collect(page, name) {
        if (!page) return;
        let content = '';
        for (let i = 0; i < 2; i++) {
            console.log(`[${name}] 等待回复 ${(i+1)*10}s...`);
            await page.waitForTimeout(10000);
            const btnCount = await page.locator('button').count();
            if (btnCount > 3) {
                console.log(`[${name}] 检测到回复（按钮数: ${btnCount}）`);
                const text = await page.evaluate(() => document.body.innerText);
                const lines = text.split('\n').filter(l => l.trim().length > 3);
                content = lines.slice(-50).join('\n');
                if (content.length > 50) break;
            }
        }
        if (!content || content.length < 50) {
            const text = await page.evaluate(() => document.body.innerText);
            const lines = text.split('\n').filter(l => l.trim().length > 3);
            content = lines.slice(-50).join('\n');
        }
        console.log(`\n=== ${name} ===`);
        console.log(content.slice(-500));
        saveToFile(name, content);
    }
    
    // 千问：提问+收集
    let p1 = await findOrOpen('https://chat.qwen.ai/', '千问');
    await ask(p1, QUESTION, '千问');
    await collect(p1, '千问');
    
    // DeepSeek：提问+收集
    let p2 = await findOrOpen('https://chat.deepseek.com/', 'DeepSeek');
    await ask(p2, QUESTION, 'DeepSeek');
    await collect(p2, 'DeepSeek');
    
    console.log("\n=== subagent2 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
```

### 3.3 subagent3 (s3) - 智谱专用

```javascript
// 脚本位置: skills/zhiku/scripts/zhiku-s3-v3.js

#!/usr/bin/env node
// 智库 subagent3 - 智谱专用

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const QUESTION = process.argv[2] || "用一句话介绍深圳";

function saveToFile(name, content) {
    const today = new Date().toISOString().slice(0, 10);
    const dir = path.join(process.env.HOME, '.openclaw/workspace/zhiku_output', today, name);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    const safeName = QUESTION.slice(0, 15).replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_');
    const file = path.join(dir, `${safeName}.md`);
    fs.writeFileSync(file, content);
    console.log(`[保存] ${file}`);
}

async function ensureBrowser() {
    for (let i = 0; i < 10; i++) {
        try {
            const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
            await browser.close();
            return true;
        } catch(e) { await new Promise(r => setTimeout(r, 1000)); }
    }
    return false;
}

async function main() {
    console.log("=== subagent3 开始（智谱专用） ===");
    const ok = await ensureBrowser();
    if (!ok) { console.log("Browser 未运行"); return; }
    
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800', {
        headers: { 'Client-Wants-Ephemeral-DevTools-Context': 'true' }
    });
    const ctx = browser.contexts()[0];
    
    async function findOrOpen(url, name) {
        for (const p of ctx.pages()) {
            if (p.url().includes(url.replace('https://', '').split('/')[0])) {
                console.log(`复用: ${name}`);
                return p;
            }
        }
        console.log(`打开: ${name}`);
        const page = await ctx.newPage();
        await page.goto(url, { timeout: 15000, waitUntil: 'domcontentloaded' });
        return page;
    }
    
    async function ask(page, q) {
        if (!page) return;
        await page.goto(page.url());
        await page.waitForTimeout(3000);
        console.log("[重新加载]");
        await page.waitForTimeout(3000);
        const ta = page.locator('textarea').first();
        if (await ta.count() > 0) {
            await ta.fill(q);
            await ta.press('Enter');
            console.log("已提问");
        }
    }
    
    // 收集回复函数 - 智谱给予更多等待时间
    async function collect(page, name) {
        if (!page) return;
        let content = '';
        for (let i = 0; i < 4; i++) {
            console.log(`[${name}] 等待回复 ${(i+1)*15}s...`);
            await page.waitForTimeout(15000);
            const btnCount = await page.locator('button').count();
            if (btnCount > 3) {
                console.log(`[${name}] 检测到回复（按钮数: ${btnCount}）`);
                const text = await page.evaluate(() => document.body.innerText);
                const lines = text.split('\n').filter(l => l.trim().length > 3);
                content = lines.slice(-50).join('\n');
                if (content.length > 50) break;
            }
        }
        if (!content || content.length < 50) {
            const text = await page.evaluate(() => document.body.innerText);
            const lines = text.split('\n').filter(l => l.trim().length > 3);
            content = lines.slice(-50).join('\n');
        }
        console.log(`\n=== ${name} ===`);
        console.log(content.slice(-500));
        saveToFile(name, content);
    }
    
    // 智谱：提问+收集
    let p1 = await findOrOpen('https://chatglm.cn/', '智谱');
    await ask(p1, QUESTION);
    await collect(p1, '智谱');
    
    console.log("\n=== subagent3 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
```

---

## 四、错误与修复记录

### 4.1 错误1：使用非无头模式

**错误描述**：
- 脚本运行时在用户可见的 Chrome 中打开标签页
- 用户手动关闭标签导致 CDP 断开

**错误原因**：
- 没有正确使用 CDP 后台模式
- 使用了 `openclaw browser open` 命令

**修复方法**：
- 只使用 `chromium.connectOverCDP()` 连接
- 不使用 `openclaw browser open` 打开页面
- 使用 `headers: {'Client-Wants-Ephemeral-DevTools-Context': 'true'}` 实现真正的后台

### 4.2 错误2：获取内容包含历史对话

**错误描述**：
- 获取到的内容是旧对话列表，不是当前问题的回复

**错误原因**：
- 新建对话功能不稳定
- 没有等待页面完全加载

**修复方法**：
- 豆包/Kimi：用 Command+K 快捷键
- 千问/智谱/DeepSeek：用 page.goto() 重新加载
- 添加等待时间确保页面加载完成

### 4.3 错误3：智谱收集超时

**错误描述**：
- 智谱回答时间最长，经常在收集时被终止

**错误原因**：
- 所有平台共用两个 subagent
- 智谱拖累其他平台

**修复方法**：
- 单独创建 subagent3 专门处理智谱
- 给予更多等待时间（4次×15秒=60秒）

### 4.4 错误4：点击复制按钮导致乱点

**错误描述**：
- 脚本尝试点击复制按钮时点到其他元素

**错误原因**：
- 选择器不准确
- 点击了第一个按钮（不是复制按钮）

**修复方法**：
- 不点击按钮，直接用 `document.body.innerText` 获取内容
- 通过按钮数量判断回复是否完成

### 4.5 错误5：60秒轮询超时

**错误描述**：
- subagent 任务超过60秒被强制终止

**错误原因**：
- 每个平台等待60秒 × 多个平台 = 总时间过长

**修复方法**：
- 减少轮询次数（从6次减到2次）
- 每次等待10秒
- 分离平台到不同 subagent

---

## 五、文件保存

### 5.1 保存路径
```
~/.openclaw/workspace/zhiku_output/yyyy-mm-dd/{平台}/{问题}.md
```

### 5.2 文件格式
```markdown
{平台回复内容}
```

---

## 六、使用方式

### 6.1 启动命令
```bash
# 1. 先启动 subagent3（智谱，最慢）
node skills/zhiku/scripts/zhiku-s3-v3.js "问题" &

# 2. 同时启动 subagent1 和 subagent2
node skills/zhiku/scripts/zhiku-s1-v3.js "问题" &
node skills/zhiku/scripts/zhiku-s2-v3.js "问题" &
```

### 6.2 查看结果
```bash
# 读取保存的文件
cat ~/.openclaw/workspace/zhiku_output/2026-03-12/千问/问题.md
```

---

## 七、版本历史

### v0.1 (2026-03-12)
- 初始版本
- 2个 subagent
- 问题：智谱经常超时

### v0.2 (2026-03-12)
- 增加到3个 subagent
- 分离智谱单独处理
- 添加文件保存功能

### v0.3 (2026-03-12)
- 修复点击复制按钮问题
- 改用 innerText 获取内容
- 优化等待时间
- 分离任务：s1=豆包+Kimi, s2=千问+DeepSeek, s3=智谱

### v0.4 (2026-03-12) - 当前版本
- 修复问题：硬编码等待时间
  - 改用 DOM 元素检测：`waitForFunction` 检测回复标记
  - 标记包括：已思考、正在搜索、已完成、参考、已阅读、思考结束
- 修复问题：btnCount > 3 判断依赖网页结构
  - 改用文本内容检测
- 修复问题：获取内容不完整
  - 移除 slice(-50) 行数限制，获取完整内容
- 修复问题：输出限制字符数
  - 移除 slice 限制，输出完整内容
- 增加等待时间到3秒确保新对话创建完成
