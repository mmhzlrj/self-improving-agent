#!/usr/bin/env node
// 智库工作流 - subagent1 (headless模式，自动启动浏览器)

const { chromium } = require('playwright');
const { execSync } = require('child_process');

const QUESTION = process.argv[2] || "用一句话介绍深圳";

async function ensureBrowser() {
    // 先尝试启动浏览器（如果未运行）
    try {
        console.log("尝试启动 Browser...");
        execSync('openclaw browser open https://www.baidu.com', { stdio: 'ignore' });
    } catch(e) {}
    
    // 等待 Browser 就绪，最多 30 秒
    for (let i = 0; i < 30; i++) {
        try {
            const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
            await browser.close();
            console.log("Browser 已就绪");
            return true;
        } catch(e) {
            if (i === 0) console.log("等待 Browser 启动...");
            await new Promise(r => setTimeout(r, 1000));
        }
    }
    return false;
}

async function main() {
    console.log("=== subagent1 开始 ===");
    
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
    
    let p1 = await findOrOpen('https://chat.qwen.ai/', '千问');
    await ask(p1, QUESTION);
    
    let p2 = await findOrOpen('https://chatglm.cn/', '智谱');
    await ask(p2, QUESTION);
    
    let p3 = await findOrOpen('https://www.kimi.com/', 'Kimi');
    await ask(p3, QUESTION);
    
    let p4 = await findOrOpen('https://www.doubao.com/chat/', '豆包');
    await collect(p4, '豆包');
    
    let p5 = await findOrOpen('https://chat.deepseek.com/', 'DeepSeek');
    await collect(p5, 'DeepSeek');
    
    console.log("=== 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
