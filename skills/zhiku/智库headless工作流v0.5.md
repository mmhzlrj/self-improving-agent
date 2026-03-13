# 智库 Headless 工作流文档 v0.4

## 一、功能描述

### 1.1 目标
通过 CDP 后台模式同时向 5 个国产 AI 平台提问并收集回复。

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
- 提问+收集：豆包、Kimi

**subagent2**：负责 page.goto() 创建会话的平台
- 提问+收集：千问、DeepSeek

**subagent3**：专门负责智谱
- 提问+收集：智谱（给予更多等待时间）

### 2.2 执行顺序
1. 先启动 subagent3（智谱，最慢）
2. 同时启动 subagent1 和 subagent2

---

## 三、脚本实现

**注意**：以下代码为简化版本，详细完整代码见脚本文件。

### 3.1 subagent1 (s1) - 豆包/Kimi
- 文件：`scripts/zhiku-s1-v4.js`
- 功能：提问+收集豆包、Kimi

### 3.2 subagent2 (s2) - 千问/DeepSeek
- 文件：`scripts/zhiku-s2-v4.js`
- 功能：提问+收集千问、DeepSeek

### 3.3 subagent3 (s3) - 智谱专用
- 文件：`scripts/zhiku-s3-v4.js`
- 功能：提问+收集智谱（给予更多等待时间）

---

## 四、关键改进（v0.4）

### 4.1 等待回复方式
**旧版本（v0.3及之前）**：
- 硬编码等待时间（10秒）
- 用btnCount > 3判断

**新版本（v0.4）**：
- 用DOM元素检测：`waitForFunction` 检测回复标记
- 标记包括：已思考、正在搜索、已完成、参考、已阅读、思考结束

### 4.2 获取内容方式
**旧版本（v0.3及之前）**：
- slice(-50) 限制50行
- 限制输出字符数

**新版本（v0.4）**：
- 获取完整内容，不限制行数
- 输出完整内容，不限制字符数

### 4.3 新建对话等待时间
- 增加到3秒确保页面加载完成

---

## 五、错误与修复记录

### 5.1 错误1：使用非无头模式
**修复**：只使用 `chromium.connectOverCDP()`

### 5.2 错误2：获取内容包含历史对话
**修复**：检测AI回复标记，从标记位置开始获取

### 5.3 错误3：智谱收集超时
**修复**：单独创建subagent3专门处理

### 5.4 错误4：硬编码等待时间
**修复**：用DOM元素检测

### 5.5 错误5：获取内容不完整
**修复**：移除行数限制，获取完整内容

---

## 六、版本历史

### v0.4 (2026-03-12)
- 修复硬编码等待时间，改用DOM元素检测
- 修复btnCount判断依赖网页结构
- 移除行数限制，获取完整内容
- 移除输出字符限制

### v0.5 (2026-03-12) - 当前版本
- 改用复制按钮获取回复内容
- 等待回复完成标记：已完成、参考、已阅读、思考结束、内容由AI生成
- 多策略查找复制按钮
- 从剪贴板读取内容
- 千问特殊处理：等待textarea可编辑
- 备用方案：innerText获取

### v0.3
- 修复点击复制按钮问题
- 优化等待时间

### v0.2
- 增加到3个subagent

### v0.1
- 初始版本
#!/usr/bin/env node
// 智库 subagent1 - CDP 后台模式

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const QUESTION = process.argv[2] || "用一句话介绍深圳";

// 保存到文件
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
        } catch(e) {
            await new Promise(r => setTimeout(r, 1000));
        }
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
    console.log("页面数:", ctx.pages().length);
    
    async function findOrOpen(url, name) {
        for (const p of ctx.pages()) {
            if (p.url().includes(url.replace('https://', '').split('/')[0])) {
                console.log(`复用: ${name}`);
                return p;
            }
        }
        console.log(`打开: ${name}`);
        try {
            const page = await ctx.newPage();
            await page.goto(url, { timeout: 15000, waitUntil: 'domcontentloaded' });
            return page;
        } catch(e) {
            console.log(`失败: ${e.message}`);
            return null;
        }
    }
    
    async function ask(page, q, platform) {
        if (!page) return;
        
        // 根据平台创建新对话
        if (platform === '豆包' || platform === 'Kimi') {
            // 豆包/Kimi 用 Command+K
            await page.keyboard.press('Meta+k');
            await page.waitForTimeout(3000);  // 增加等待时间
            console.log("[Command+K]");
        } else {
            // 千问/智谱/DeepSeek 重新加载页面创建新对话
            await page.goto(page.url());
            await page.waitForTimeout(3000);  // 增加等待时间
            console.log("[重新加载]");
        }
        
        await page.waitForTimeout(1500);
        const ta = page.locator('textarea').first();
        if (await ta.count() > 0) {
            await ta.fill(q);
            await ta.press('Enter');
            console.log("已提问");
        } else {
            const ed = page.locator('div[contenteditable="true"]').first();
            if (await ed.count() > 0) {
                await ed.fill(q);
                await ed.press('Enter');
                console.log("已提问");
            }
        }
    }
    
    async function collect(page, name) {
        if (!page) return;
        
        let content = '';
        
        // 等待回复出现 - 使用DOM元素检测而非固定时间
        try {
            // 等待回复区域出现（通过检测特定的回复元素）
            await page.waitForFunction(() => {
                // 检测是否有回复内容出现
                const body = document.body.innerText;
                // 检查是否包含AI回复的标志性文本
                return body.includes('已思考') || 
                       body.includes('正在搜索') || 
                       body.includes('已完成') ||
                       body.includes('已阅读') ||
                       body.includes('参考') ||
                       (body.length > 200 && body.split('\n').length > 5);
            }, { timeout: 30000 }).then(() => {
                console.log(`[${name}] 检测到回复内容`);
            }).catch(() => {
                console.log(`[${name}] 等待回复超时`);
            });
            
            // 等待额外时间确保回复渲染完成
            await page.waitForTimeout(3000);
            
        } catch(e) {
            console.log(`[${name}] 等待回复异常: ${e.message}`);
        }
        
        // 获取页面内容 - 改进获取方式
        const text = await page.evaluate(() => {
            // 优先获取回复区域内容
            // 查找可能的回复容器
            const selectors = [
                '[data-role="assistant"]',
                '.message-content',
                '.assistant-message',
                '[class*="response"]',
                '[class*="reply"]'
            ];
            
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.innerText.length > 50) {
                    return el.innerText;
                }
            }
            
            // 备选：获取整个body但过滤掉UI元素
            const allText = document.body.innerText;
            // 移除历史对话列表，只保留最新回复
            const lines = allText.split('\n');
            // 找到包含AI回复标记的位置
            for (let i = lines.length - 1; i >= 0; i--) {
                if (lines[i].includes('已思考') || 
                    lines[i].includes('正在搜索') || 
                    lines[i].includes('已完成') ||
                    lines[i].includes('参考') ||
                    lines[i].includes('已阅读')) {
                    // 返回从这行开始到最后的所有内容
                    return lines.slice(i).join('\n');
                }
            }
            // 如果没找到标记，返回最后100行
            return lines.slice(-100).join('\n');
        });
        
        content = text;
        
        // 如果内容太短或包含太多历史对话，尝试另一种方式
        if (content.length < 100 || (content.includes('新建对话') && content.includes('历史对话'))) {
            const allText = await page.evaluate(() => document.body.innerText);
            const allLines = allText.split('\n').filter(l => l.trim().length > 2);
            // 获取完整内容，不限制行数
            content = allLines.join('\n');
        }
        
        console.log(`\n=== ${name} ===`);
        console.log(content);
        
        // 保存到文件
        saveToFile(name, content);
    }
    
    // 豆包/Kimi
    let p1 = await findOrOpen('https://www.doubao.com/chat/', '豆包');
    await ask(p1, QUESTION, '豆包');
    await collect(p1, '豆包');
    
    let p2 = await findOrOpen('https://www.kimi.com/', 'Kimi');
    await ask(p2, QUESTION, 'Kimi');
    await collect(p2, 'Kimi');
    
    console.log("\n=== subagent1 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));


===== s2 =====

#!/usr/bin/env node
// 智库 subagent2 - CDP 后台模式

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const QUESTION = process.argv[2] || "用一句话介绍深圳";

// 保存到文件
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
        } catch(e) {
            await new Promise(r => setTimeout(r, 1000));
        }
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
    console.log("页面数:", ctx.pages().length);
    
    async function findOrOpen(url, name) {
        for (const p of ctx.pages()) {
            if (p.url().includes(url.replace('https://', '').split('/')[0])) {
                console.log(`复用: ${name}`);
                return p;
            }
        }
        console.log(`打开: ${name}`);
        try {
            const page = await ctx.newPage();
            await page.goto(url, { timeout: 15000, waitUntil: 'domcontentloaded' });
            return page;
        } catch(e) {
            console.log(`失败: ${e.message}`);
            return null;
        }
    }
    
    async function ask(page, q, platform) {
        if (!page) return;
        
        // 根据平台创建新对话
        if (platform === '豆包' || platform === 'Kimi') {
            await page.keyboard.press('Meta+k');
            await page.waitForTimeout(1500);
            console.log("[Command+K]");
        } else {
            // 千问/智谱/DeepSeek 重新加载页面创建新对话
            await page.goto(page.url());
            await page.waitForTimeout(3000);
            console.log("[重新加载]");
        }
        
        await page.waitForTimeout(1500);
        const ta = page.locator('textarea').first();
        if (await ta.count() > 0) {
            await ta.fill(q);
            await ta.press('Enter');
            console.log("已提问");
        } else {
            const ed = page.locator('div[contenteditable="true"]').first();
            if (await ed.count() > 0) {
                await ed.fill(q);
                await ed.press('Enter');
                console.log("已提问");
            }
        }
    }
    
    async function collect(page, name) {
        if (!page) return;
        
        let content = '';
        
        // 等待回复出现 - 使用DOM元素检测
        try {
            await page.waitForFunction(() => {
                const body = document.body.innerText;
                return body.includes('已思考') || 
                       body.includes('正在搜索') || 
                       body.includes('已完成') ||
                       body.includes('已阅读') ||
                       body.includes('参考') ||
                       (body.length > 200 && body.split('\n').length > 5);
            }, { timeout: 30000 }).then(() => {
                console.log(`[${name}] 检测到回复内容`);
            }).catch(() => {
                console.log(`[${name}] 等待回复超时`);
            });
            
            await page.waitForTimeout(3000);
            
        } catch(e) {
            console.log(`[${name}] 等待回复异常: ${e.message}`);
        }
        
        // 获取页面内容
        const text = await page.evaluate(() => {
            const selectors = [
                '[data-role="assistant"]',
                '.message-content',
                '.assistant-message',
                '[class*="response"]',
                '[class*="reply"]'
            ];
            
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.innerText.length > 50) {
                    return el.innerText;
                }
            }
            
            const allText = document.body.innerText;
            const lines = allText.split('\n');
            for (let i = lines.length - 1; i >= 0; i--) {
                if (lines[i].includes('已思考') || 
                    lines[i].includes('正在搜索') || 
                    lines[i].includes('已完成') ||
                    lines[i].includes('参考') ||
                    lines[i].includes('已阅读')) {
                    return lines.slice(i).join('\n');
                }
            }
            return lines.join('\n');
        });
        
        content = text;
        
        if (content.length < 100 || (content.includes('新建对话') && content.includes('历史对话'))) {
            const allText = await page.evaluate(() => document.body.innerText);
            const allLines = allText.split('\n').filter(l => l.trim().length > 2);
            content = allLines.join.join('\n');
        }
        
        console.log(`\n=== ${name} ===`);
        console.log(content);
        
        // 保存到文件
        saveToFile(name, content);
    }
    
    // 千问
    let p1 = await findOrOpen('https://chat.qwen.ai/', '千问');
    await ask(p1, QUESTION, '千问');
    await collect(p1, '千问');
    
    // DeepSeek
    let p2 = await findOrOpen('https://chat.deepseek.com/', 'DeepSeek');
    await ask(p2, QUESTION, 'DeepSeek');
    await collect(p2, 'DeepSeek');
    
    console.log("\n=== subagent2 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));


===== s3 =====

#!/usr/bin/env node
// 智库 subagent2 - CDP 后台模式

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const QUESTION = process.argv[2] || "用一句话介绍深圳";

// 保存到文件
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
        } catch(e) {
            await new Promise(r => setTimeout(r, 1000));
        }
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
    console.log("页面数:", ctx.pages().length);
    
    async function findOrOpen(url, name) {
        for (const p of ctx.pages()) {
            if (p.url().includes(url.replace('https://', '').split('/')[0])) {
                console.log(`复用: ${name}`);
                return p;
            }
        }
        console.log(`打开: ${name}`);
        try {
            const page = await ctx.newPage();
            await page.goto(url, { timeout: 15000, waitUntil: 'domcontentloaded' });
            return page;
        } catch(e) {
            console.log(`失败: ${e.message}`);
            return null;
        }
    }
    
    async function ask(page, q, platform) {
        if (!page) return;
        
        // 根据平台创建新对话
        if (platform === '豆包' || platform === 'Kimi') {
            await page.keyboard.press('Meta+k');
            await page.waitForTimeout(1500);
            console.log("[Command+K]");
        } else {
            // 千问/智谱/DeepSeek 重新加载页面创建新对话
            await page.goto(page.url());
            await page.waitForTimeout(2000);
            console.log("[重新加载]");
        }
        
        await page.waitForTimeout(1500);
        const ta = page.locator('textarea').first();
        if (await ta.count() > 0) {
            await ta.fill(q);
            await ta.press('Enter');
            console.log("已提问");
        } else {
            const ed = page.locator('div[contenteditable="true"]').first();
            if (await ed.count() > 0) {
                await ed.fill(q);
                await ed.press('Enter');
                console.log("已提问");
            }
        }
    }
    
    async function collect(page, name) {
        if (!page) return;
        
        let content = '';
        
        // 等待回复出现 - 使用DOM元素检测
        try {
            await page.waitForFunction(() => {
                const body = document.body.innerText;
                return body.includes('已思考') || 
                       body.includes('正在搜索') || 
                       body.includes('已完成') ||
                       body.includes('已阅读') ||
                       body.includes('参考') ||
                       body.includes('思考结束') ||
                       (body.length > 200 && body.split('\n').length > 5);
            }, { timeout: 45000 }).then(() => {
                console.log(`[${name}] 检测到回复内容`);
            }).catch(() => {
                console.log(`[${name}] 等待回复超时`);
            });
            
            await page.waitForTimeout(3000);
            
        } catch(e) {
            console.log(`[${name}] 等待回复异常: ${e.message}`);
        }
        
        // 获取页面内容
        const text = await page.evaluate(() => {
            const selectors = [
                '[data-role="assistant"]',
                '.message-content',
                '.assistant-message',
                '[class*="response"]',
                '[class*="reply"]'
            ];
            
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.innerText.length > 50) {
                    return el.innerText;
                }
            }
            
            const allText = document.body.innerText;
            const lines = allText.split('\n');
            for (let i = lines.length - 1; i >= 0; i--) {
                if (lines[i].includes('已思考') || 
                    lines[i].includes('正在搜索') || 
                    lines[i].includes('已完成') ||
                    lines[i].includes('参考') ||
                    lines[i].includes('已阅读') ||
                    lines[i].includes('思考结束')) {
                    return lines.slice(i).join('\n');
                }
            }
            return lines.join('\n');
        });
        
        content = text;
        
        if (content.length < 100 || (content.includes('新建对话') && content.includes('历史对话'))) {
            const allText = await page.evaluate(() => document.body.innerText);
            const allLines = allText.split('\n').filter(l => l.trim().length > 2);
            content = allLines.join.join('\n');
        }
        
        console.log(`\n=== ${name} ===`);
        console.log(content);
        
        // 保存到文件
        saveToFile(name, content);
    }
    
    // 智谱
    let p1 = await findOrOpen('https://chatglm.cn/', '智谱');
    await ask(p1, QUESTION, '智谱');
    await collect(p1, '智谱');
    
    console.log("\n=== subagent3 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
