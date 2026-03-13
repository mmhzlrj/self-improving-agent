#!/usr/bin/env node
// 智库 subagent2 - CDP 后台模式

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
            await page.waitForTimeout(3000);
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
        
        // 等待回复出现 - 使用DOM元素检测
        try {
            await page.waitForFunction(() => {
                const body = document.body.innerText;
                return body.includes('已思考') || 
                       body.includes('正在搜索') || 
                       body.includes('已完成') ||
                       body.includes('已阅读') ||
                       body.includes('参考') ||
                       (body.length > 200 && body.split('\n').length > 5);
            }, { timeout: 30000 }).then(() => {
                console.log(`[${name}] 检测到回复内容`);
            }).catch(() => {
                console.log(`[${name}] 等待回复超时`);
            });
            
            await page.waitForTimeout(3000);
            
        } catch(e) {
            console.log(`[${name}] 等待回复异常: ${e.message}`);
        }
        
        // 获取页面内容
        const text = await page.evaluate(() => {
            const selectors = [
                '[data-role="assistant"]',
                '.message-content',
                '.assistant-message',
                '[class*="response"]',
                '[class*="reply"]'
            ];
            
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.innerText.length > 50) {
                    return el.innerText;
                }
            }
            
            const allText = document.body.innerText;
            const lines = allText.split('\n');
            for (let i = lines.length - 1; i >= 0; i--) {
                if (lines[i].includes('已思考') || 
                    lines[i].includes('正在搜索') || 
                    lines[i].includes('已完成') ||
                    lines[i].includes('参考') ||
                    lines[i].includes('已阅读')) {
                    return lines.slice(i).join('\n');
                }
            }
            return lines.join('\n');
        });
        
        content = text;
        
        if (content.length < 100 || (content.includes('新建对话') && content.includes('历史对话'))) {
            const allText = await page.evaluate(() => document.body.innerText);
            const allLines = allText.split('\n').filter(l => l.trim().length > 2);
            content = allLines.join.join('\n');
        }
        
        console.log(`\n=== ${name} ===`);
        console.log(content);
        
        // 保存到文件
        saveToFile(name, content);
    }
    
    // 千问
    let p1 = await findOrOpen('https://chat.qwen.ai/', '千问');
    await ask(p1, QUESTION, '千问');
    await collect(p1, '千问');
    
    // DeepSeek
    let p2 = await findOrOpen('https://chat.deepseek.com/', 'DeepSeek');
    await ask(p2, QUESTION, 'DeepSeek');
    await collect(p2, 'DeepSeek');
    
    console.log("\n=== subagent2 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
