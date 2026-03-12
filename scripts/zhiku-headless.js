#!/usr/bin/env node
// 智库工作流 - 真正的 headless 模式

const playwright = require('playwright');
const QUESTION = process.argv[2] || "用一句话介绍深圳";

async function main() {
    console.log("=== 智库工作流 (真正的 headless) ===");
    
    // 启动 headless 浏览器
    console.log("启动 headless 浏览器...");
    const browser = await playwright.chromium.launch({
        headless: true,
        channel: 'chromium-headless-shell'
    });
    
    const ctx = await browser.newContext();
    
    // 打开5个平台
    const platforms = [
        { url: 'https://chat.qwen.ai/', name: '千问' },
        { url: 'https://chatglm.cn/', name: '智谱' },
        { url: 'https://www.kimi.com/', name: 'Kimi' },
        { url: 'https://www.doubao.com/chat/', name: '豆包' },
        { url: 'https://chat.deepseek.com/', name: 'DeepSeek' }
    ];
    
    // 提问
    console.log("\n=== 提问阶段 ===");
    for (const p of platforms) {
        try {
            console.log(`打开: ${p.name}`);
            const page = await ctx.newPage();
            await page.goto(p.url, { timeout: 15000, waitUntil: 'domcontentloaded' });
            await page.waitForTimeout(2000);
            
            // 提问
            const ta = page.locator('textarea').first();
            if (await ta.count() > 0) {
                await ta.fill(QUESTION);
                await ta.press('Enter');
                console.log(`提问: ${p.name}`);
            } else {
                const ed = page.locator('div[contenteditable="true"]').first();
                if (await ed.count() > 0) {
                    await ed.fill(QUESTION);
                    await ed.press('Enter');
                    console.log(`提问: ${p.name}`);
                }
            }
        } catch(e) {
            console.log(`失败: ${p.name} - ${e.message}`);
        }
    }
    
    // 等待回复
    console.log("\n等待回复 (20秒)...");
    await new Promise(r => setTimeout(r, 20000));
    
    // 收集回复
    console.log("\n=== 收集回复 ===");
    const pages = ctx.pages();
    for (const p of platforms) {
        for (const page of pages) {
            if (page.url().includes(p.name === 'Kimi' ? 'kimi' : p.name)) {
                const text = await page.evaluate(() => document.body.innerText);
                console.log(`\n=== ${p.name} ===`);
                console.log(text.slice(-400));
                break;
            }
        }
    }
    
    console.log("\n=== 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
