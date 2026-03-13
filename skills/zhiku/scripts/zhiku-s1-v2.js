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
        
        // 轮询等待复制按钮出现（按钮数量增加表示回复完成）
        for (let i = 0; i < 2; i++) {
            console.log(`[${name}] 等待回复 ${(i+1)*10}s...`);
            await page.waitForTimeout(10000);
            
            // 检查按钮数量（回复完成后按钮会增加）
            const btnCount = await page.locator('button').count();
            if (btnCount > 3) {
                console.log(`[${name}] 检测到回复（按钮数: ${btnCount}）`);
                
                // 直接用 innerText 获取内容，不点击
                const text = await page.evaluate(() => document.body.innerText);
                const lines = text.split('\n').filter(l => l.trim().length > 3);
                content = lines.slice(-50).join('\n');
                
                if (content.length > 50) break;
            }
        }
        
        // 备选
        if (!content || content.length < 50) {
            const text = await page.evaluate(() => document.body.innerText);
            const lines = text.split('\n').filter(l => l.trim().length > 3);
            content = lines.slice(-50).join('\n');
        }
        
        console.log(`\n=== ${name} ===`);
        console.log(content.slice(-500));
        
        // 保存到文件
        saveToFile(name, content);
    }
    
    // 时间点1-3: 提问 (智谱, 千问, Kimi)
    let p1 = await findOrOpen('https://chatglm.cn/', '智谱');
    await ask(p1, QUESTION, '智谱');
    
    let p2 = await findOrOpen('https://chat.qwen.ai/', '千问');
    await ask(p2, QUESTION, '千问');
    
    let p3 = await findOrOpen('https://www.kimi.com/', 'Kimi');
    await ask(p3, QUESTION, 'Kimi');
    
    // 收集 (豆包, DeepSeek)
    let p4 = await findOrOpen('https://www.doubao.com/chat/', '豆包');
    await collect(p4, '豆包');
    
    let p5 = await findOrOpen('https://chat.deepseek.com/', 'DeepSeek');
    await collect(p5, 'DeepSeek');
    
    console.log("\n=== subagent1 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
