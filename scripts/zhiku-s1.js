#!/usr/bin/env node
// 智库 subagent1 - 实时完整回复展示

const { chromium } = require('playwright');
const QUESTION = process.argv[2] || "用一句话介绍深圳";
const MAX_ROUNDS = 3;

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
    console.log(`\n🤖 智库问答`);
    console.log(`问题: ${QUESTION}\n`);
    
    const ok = await ensureBrowser();
    if (!ok) { console.log("Browser 未运行"); return; }
    
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800', {
        headers: { 'Client-Wants-Ephemeral-DevTools-Context': 'true' }
    });
    const ctx = browser.contexts()[0];
    
    const collected = { '千问': '', '智谱': '', 'Kimi': '', '豆包': '', 'DeepSeek': '' };
    
    async function findOrOpen(url, name) {
        for (const p of ctx.pages()) {
            if (p.url().includes(url.replace('https://', '').split('/')[0])) return p;
        }
        try {
            const page = await ctx.newPage();
            await page.goto(url, { timeout: 15000, waitUntil: 'domcontentloaded' });
            return page;
        } catch(e) { return null; }
    }
    
    async function ask(page, q) {
        if (!page) return;
        await page.waitForTimeout(1500);
        const ta = page.locator('textarea').first();
        if (await ta.count() > 0) {
            await ta.fill(q); await ta.press('Enter');
        } else {
            const ed = page.locator('div[contenteditable="true"]').first();
            if (await ed.count() > 0) {
                await ed.fill(q); await ed.press('Enter');
            }
        }
    }
    
    async function collectAndShow(name, url) {
        if (collected[name]) return;
        let p = await findOrOpen(url, name);
        if (!p) return;
        const text = await p.evaluate(() => document.body.innerText);
        // 获取完整内容
        const lines = text.split('\n').filter(l => l.trim().length > 3);
        const reply = lines.slice(-50).join('\n').trim();
        if (reply.includes(QUESTION.slice(0, 3))) {
            collected[name] = reply;
            console.log(`【${name}】`);
            console.log(reply);
            console.log(`进度: ${Object.values(collected).filter(v => v).length}/5 已收集\n`);
        }
    }
    
    // 提问
    await findOrOpen('https://chat.qwen.ai/', '千问');
    await ask(await findOrOpen('https://chat.qwen.ai/', '千问'), QUESTION);
    await findOrOpen('https://chatglm.cn/', '智谱');
    await ask(await findOrOpen('https://chatglm.cn/', '智谱'), QUESTION);
    await findOrOpen('https://www.kimi.com/', 'Kimi');
    await ask(await findOrOpen('https://www.kimi.com/', 'Kimi'), QUESTION);
    
    await new Promise(r => setTimeout(r, 15000));
    
    // 收集
    for (let round = 1; round <= MAX_ROUNDS; round++) {
        await collectAndShow('豆包', 'https://www.doubao.com/chat/');
        await collectAndShow('DeepSeek', 'https://chat.deepseek.com/');
        
        if (Object.values(collected).filter(v => v).length === 5) break;
        if (round < MAX_ROUNDS) await new Promise(r => setTimeout(r, 10000));
    }
    
    console.log("✅ 完成\n");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
