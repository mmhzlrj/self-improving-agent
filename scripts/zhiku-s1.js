#!/usr/bin/env node
// 智库 subagent1 - CDP 后台模式 + 多轮收集

const { chromium } = require('playwright');
const QUESTION = process.argv[2] || "用一句话介绍深圳";
const MAX_ROUNDS = 3; // 最多收集轮数

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
    
    const platforms = [
        { url: 'https://chat.qwen.ai/', name: '千问' },
        { url: 'https://chatglm.cn/', name: '智谱' },
        { url: 'https://www.kimi.com/', name: 'Kimi' },
        { url: 'https://www.doubao.com/chat/', name: '豆包' },
        { url: 'https://chat.deepseek.com/', name: 'DeepSeek' }
    ];
    
    // 记录每个平台是否已收集
    const collected = {};
    platforms.forEach(p => collected[p.name] = false);
    
    async function findOrOpen(url, name) {
        for (const p of ctx.pages()) {
            if (p.url().includes(url.replace('https://', '').split('/')[0])) {
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
    
    // 时间点1-3: 提问 (千问, 智谱, Kimi)
    console.log("\n=== 提问阶段 ===");
    let p1 = await findOrOpen('https://chat.qwen.ai/', '千问');
    await ask(p1, QUESTION);
    
    let p2 = await findOrOpen('https://chatglm.cn/', '智谱');
    await ask(p2, QUESTION);
    
    let p3 = await findOrOpen('https://www.kimi.com/', 'Kimi');
    await ask(p3, QUESTION);
    
    // 等待回复后再收集
    console.log("\n等待回复 (15秒)...");
    await new Promise(r => setTimeout(r, 15000));
    
    // 收集阶段 - 多轮轮询
    console.log("\n=== 收集阶段 ===");
    for (let round = 1; round <= MAX_ROUNDS; round++) {
        console.log(`\n--- 第 ${round}/${MAX_ROUNDS} 轮 ---`);
        
        // 收集豆包
        if (!collected['豆包']) {
            let p4 = await findOrOpen('https://www.doubao.com/chat/', '豆包');
            if (p4) {
                const text = await p4.evaluate(() => document.body.innerText);
                // 检查是否有新回复（包含问题关键词）
                if (text.includes(QUESTION.slice(0, 5))) {
                    console.log(`\n=== 豆包 ===`);
                    console.log(text.slice(-400));
                    collected['豆包'] = true;
                }
            }
        }
        
        // 收集 DeepSeek
        if (!collected['DeepSeek']) {
            let p5 = await findOrOpen('https://chat.deepseek.com/', 'DeepSeek');
            if (p5) {
                const text = await p5.evaluate(() => document.body.innerText);
                if (text.includes(QUESTION.slice(0, 5))) {
                    console.log(`\n=== DeepSeek ===`);
                    console.log(text.slice(-400));
                    collected['DeepSeek'] = true;
                }
            }
        }
        
        // 检查是否全部收集完成
        const remaining = Object.values(collected).filter(v => !v).length;
        console.log(`进度: ${5 - remaining}/5 已收集`);
        
        if (remaining === 0) {
            console.log("全部收集完成!");
            break;
        }
        
        // 继续等待
        if (round < MAX_ROUNDS) {
            console.log("等待下一轮...");
            await new Promise(r => setTimeout(r, 10000));
        }
    }
    
    console.log("\n=== subagent1 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
