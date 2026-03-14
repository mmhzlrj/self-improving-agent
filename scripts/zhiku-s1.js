#!/usr/bin/env node
// 智库 subagent1 - 修复版
// 负责：向千问/智谱/Kimi提问，收集豆包/DeepSeek回复

const { chromium } = require('playwright');
const QUESTION = process.argv[2] || "用一句话介绍深圳";
const MAX_ROUNDS = 4;

async function ensureBrowser() {
    for (let i = 0; i < 10; i++) {
        try {
            const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
            await browser.close();
            return true;
        } catch(e) { await new Promise(r => setTimeout(r, 1000)); }
    }
    return false;
}

async function main() {
    console.log(`[步骤] 连接浏览器 (subagent1)`);
    const ok = await ensureBrowser();
    if (!ok) { console.log("[步骤] Browser 未运行"); return; }
    
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800', {
        headers: { 'Client-Wants-Ephemeral-DevTools-Context': 'true' }
    });
    const ctx = browser.contexts()[0];
    
    const collected = { '豆包': '', 'DeepSeek': '' };
    
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
    
    // 创建新对话 - 千问/智谱用+号，Kimi用Command+K
    async function newChat(page, name) {
        if (!page) return false;
        await page.waitForTimeout(1000);
        try {
            // 千问/智谱：找+号按钮
            const plusBtn = page.locator('button[aria-label*="新"], text=+').first();
            if (await plusBtn.count() > 0) {
                await plusBtn.click();
                await page.waitForTimeout(1500);
                return true;
            }
        } catch(e) {}
        // Kimi: Command+K
        if (name === 'Kimi') {
            await page.keyboard.press('Meta+k');
            await page.waitForTimeout(1500);
            return true;
        }
        return true;
    }
    
    async function ask(page, q) {
        if (!page) return;
        await page.waitForTimeout(2000);
        try {
            const ta = page.locator('textarea').first();
            if (await ta.count() > 0 && await ta.isVisible()) {
                await ta.fill(q); 
                await page.waitForTimeout(500);
                await ta.press('Enter');
                return true;
            }
        } catch(e) {}
        try {
            const ed = page.locator('div[contenteditable="true"]').first();
            if (await ed.count() > 0 && await ed.isVisible()) {
                await ed.fill(q); 
                await page.waitForTimeout(500);
                await ed.press('Enter');
                return true;
            }
        } catch(e) {}
        return false;
    }
    
    async function collectAndShow(name, url, keyword) {
        if (collected[name]) return collected[name];
        let p = await findOrOpen(url, name);
        if (!p) return '';
        
        const text = await p.evaluate(() => document.body.innerText);
        
        const hasQuestion = text.includes(keyword.slice(0, 6));
        const isGenerating = text.includes('正在搜索') || text.includes('正在思考') || text.includes('正在读取');
        const hasNewAnswer = text.includes('已阅读') && !text.includes('历史对话');
        
        const lines = text.split('\n').filter(l => l.trim().length > 2);
        const latestLines = lines.slice(-30).join('\n');
        
        if (hasQuestion && (isGenerating || hasNewAnswer || latestLines.includes('回答') || latestLines.includes('总结'))) {
            collected[name] = latestLines;
            console.log(`【${name}】${latestLines}`);
            console.log(`[步骤] ${name}回复收集完成`);
            return latestLines;
        }
        return '';
    }
    
    // 向千问/智谱/Kimi提问
    console.log(`[步骤] 检查/打开千问页面`);
    let p1 = await findOrOpen('https://chat.qwen.ai/', '千问');
    await newChat(p1, '千问');
    await ask(p1, QUESTION);
    console.log(`[步骤] 已向千问提问`);
    
    console.log(`[步骤] 检查/打开智谱页面`);
    let p2 = await findOrOpen('https://chatglm.cn/', '智谱');
    await newChat(p2, '智谱');
    await ask(p2, QUESTION);
    console.log(`[步骤] 已向智谱提问`);
    
    console.log(`[步骤] 检查/打开Kimi页面`);
    let p3 = await findOrOpen('https://www.kimi.com/', 'Kimi');
    await newChat(p3, 'Kimi');
    await ask(p3, QUESTION);
    console.log(`[步骤] 已向Kimi提问`);
    
    console.log(`[步骤] 开始收集回复`);
    
    // 收集豆包/DeepSeek
    for (let round = 1; round <= MAX_ROUNDS; round++) {
        console.log(`[步骤] 第${round}轮收集`);
        await collectAndShow('豆包', 'https://www.doubao.com/chat/', QUESTION);
        await collectAndShow('DeepSeek', 'https://chat.deepseek.com/', QUESTION);
        
        const count = Object.values(collected).filter(v => v).length;
        if (count >= 2) break;
        if (round < MAX_ROUNDS) {
            console.log(`[步骤] 等待10秒...`);
            await new Promise(r => setTimeout(r, 10000));
        }
    }
    
    console.log(`[步骤] subagent1任务完成`);
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
