#!/usr/bin/env node
// 智库 subagent2 - CDP 后台模式

const { chromium } = require('playwright');
const QUESTION = process.argv[2] || "用一句话介绍深圳";

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
        
        // 轮询等待回复生成，每10秒检查一次，最多60秒
        let content = '';
        
        for (let i = 0; i < 6; i++) {
            console.log(`[${name}] 等待回复 ${(i+1)*10}s...`);
            await page.waitForTimeout(10000);
            
            const pageText = await page.evaluate(() => document.body.innerText);
            if (pageText.includes('回答') || pageText.includes('完成') || pageText.includes('正在') === false) {
                const text = await page.evaluate(() => document.body.innerText);
                const lines = text.split('\n').filter(l => l.trim().length > 3);
                content = lines.slice(-50).join('\n');
                if (content.length > 20) break;
            }
        }
        
        console.log(`\n=== ${name} ===`);
        console.log(content.slice(-500));
    }
    
    // 提问 (豆包, DeepSeek)
    let p1 = await findOrOpen('https://www.doubao.com/chat/', '豆包');
    await ask(p1, QUESTION, '豆包');
    
    let p2 = await findOrOpen('https://chat.deepseek.com/', 'DeepSeek');
    await ask(p2, QUESTION, 'DeepSeek');
    
    // 收集 (千问, Kimi, 智谱)
    let p3 = await findOrOpen('https://chat.qwen.ai/', '千问');
    await collect(p3, '千问');
    
    let p4 = await findOrOpen('https://www.kimi.com/', 'Kimi');
    await collect(p4, 'Kimi');
    
    let p5 = await findOrOpen('https://chatglm.cn/', '智谱');
    await collect(p5, '智谱');
    
    console.log("\n=== subagent2 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
