#!/usr/bin/env node
// 智库 subagent1 - CDP 后台模式

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
        
        // 轮询等待回复生成，每10秒检查一次，最多60秒
        let content = '';
        let done = false;
        
        for (let i = 0; i < 6; i++) {
            console.log(`[${name}] 等待回复 ${(i+1)*10}s...`);
            await page.waitForTimeout(10000);
            
            // 检查是否有回复内容
            const pageText = await page.evaluate(() => document.body.innerText);
            if (pageText.includes('回答') || pageText.includes('完成') || pageText.includes('正在') === false) {
                console.log(`[${name}] 检测到回复`);
                
                // 尝试点击复制按钮获取完整内容
                try {
                    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
                    await page.waitForTimeout(1000);
                    
                    const copyBtn = page.locator('button, [role="button"]').first();
                    if (await copyBtn.count() > 0) {
                        await copyBtn.click();
                        await page.waitForTimeout(500);
                        content = await page.evaluate(async () => {
                            try { return await navigator.clipboard.readText(); } catch(e) { return ''; }
                        });
                    }
                } catch(e) {}
                
                if (content && content.length > 20) {
                    done = true;
                    break;
                }
            }
        }
        
        // 备选：用 innerText
        if (!content || content.length < 20) {
            const text = await page.evaluate(() => document.body.innerText);
            const lines = text.split('\n').filter(l => l.trim().length > 3);
            content = lines.slice(-50).join('\n');
        }
        
        console.log(`\n=== ${name} ===`);
        console.log(content.slice(-500));
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
