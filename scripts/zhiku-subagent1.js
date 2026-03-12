#!/usr/bin/env node
// 智库工作流 - subagent1

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
    console.log("=== subagent1 开始 ===");
    
    const ok = await ensureBrowser();
    if (!ok) { console.log("Browser 未就绪"); return; }
    
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
    const ctx = browser.contexts()[0];
    
    // 获取已有页面
    const existingUrls = ctx.pages().map(p => p.url());
    console.log("已有页面:", existingUrls.length);
    
    async function findOrOpen(url, name) {
        // 先在已有页面中查找
        for (const p of ctx.pages()) {
            if (p.url().includes(url.replace('https://', '').replace('http://', '').split('/')[0])) {
                console.log(`复用: ${name} (${p.url().slice(0,40)})`);
                return p;
            }
        }
        // 没找到才打开新页面
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
    
    // 提问 (千问, 智谱, Kimi)
    let p1 = await findOrOpen('https://chat.qwen.ai/', '千问');
    await ask(p1, QUESTION);
    
    let p2 = await findOrOpen('https://chatglm.cn/', '智谱');
    await ask(p2, QUESTION);
    
    let p3 = await findOrOpen('https://www.kimi.com/', 'Kimi');
    await ask(p3, QUESTION);
    
    // 收集 (豆包, DeepSeek)
    let p4 = await findOrOpen('https://www.doubao.com/chat/', '豆包');
    await collect(p4, '豆包');
    
    let p5 = await findOrOpen('https://chat.deepseek.com/', 'DeepSeek');
    await collect(p5, 'DeepSeek');
    
    console.log("=== 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
