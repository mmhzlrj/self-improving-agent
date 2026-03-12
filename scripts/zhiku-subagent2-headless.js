#!/usr/bin/env node
// 智库工作流 - subagent2 (headless模式)

const { chromium } = require('playwright');
const QUESTION = process.argv[2] || "用一句话介绍深圳";

async function ensureBrowser() {
    for (let i = 0; i < 10; i++) {
        try {
            const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
            await browser.close();
            console.log("Browser 已就绪");
            return true;
        } catch(e) {
            if (i === 0) console.log("等待 Browser...");
            await new Promise(r => setTimeout(r, 1000));
        }
    }
    return false;
}

async function main() {
    console.log("=== subagent2 开始 (headless) ===");
    
    const ok = await ensureBrowser();
    if (!ok) { console.log("Browser 未就绪"); return; }
    
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800', {
        headers: { 'Client-Wants-Ephemeral-DevTools-Context': 'true' }
    });
    const ctx = browser.contexts()[0];
    
    console.log("已有页面:", ctx.pages().length);
    
    async function findOrOpen(url, name) {
        for (const p of ctx.pages()) {
            if (p.url().includes(url.replace('https://', '').replace('http://', '').split('/')[0])) {
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
    
    async function ask(page, q) {
        if (!page) return;
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
        await page.waitForTimeout(1000);
        const text = await page.evaluate(() => document.body.innerText);
        console.log(`=== ${name} ===`);
        console.log(text.slice(-300));
    }
    
    // 提问 (豆包, DeepSeek)
    let p1 = await findOrOpen('https://www.doubao.com/chat/', '豆包');
    await ask(p1, QUESTION);
    
    let p2 = await findOrOpen('https://chat.deepseek.com/', 'DeepSeek');
    await ask(p2, QUESTION);
    
    // 收集 (千问, 智谱, Kimi)
    let p3 = await findOrOpen('https://chat.qwen.ai/', '千问');
    await collect(p3, '千问');
    
    let p4 = await findOrOpen('https://chatglm.cn/', '智谱');
    await collect(p4, '智谱');
    
    let p5 = await findOrOpen('https://www.kimi.com/', 'Kimi');
    await collect(p5, 'Kimi');
    
    console.log("=== 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
