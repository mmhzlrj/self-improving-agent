#!/usr/bin/env node
// 智库 subagent1 - CDP 后台模式

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
            await page.waitForTimeout(3000);  // 增加等待时间
            console.log("[Command+K]");
        } else {
            // 千问/智谱/DeepSeek 重新加载页面创建新对话
            await page.goto(page.url());
            await page.waitForTimeout(3000);  // 增加等待时间
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
        
        // 等待回复出现 - 使用DOM元素检测而非固定时间
        try {
            // 等待回复区域出现（通过检测特定的回复元素）
            await page.waitForFunction(() => {
                // 检测是否有回复内容出现
                const body = document.body.innerText;
                // 检查是否包含AI回复的标志性文本
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
            
            // 等待额外时间确保回复渲染完成
            await page.waitForTimeout(3000);
            
        } catch(e) {
            console.log(`[${name}] 等待回复异常: ${e.message}`);
        }
        
        // 获取页面内容 - 改进获取方式
        const text = await page.evaluate(() => {
            // 优先获取回复区域内容
            // 查找可能的回复容器
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
            
            // 备选：获取整个body但过滤掉UI元素
            const allText = document.body.innerText;
            // 移除历史对话列表，只保留最新回复
            const lines = allText.split('\n');
            // 找到包含AI回复标记的位置
            for (let i = lines.length - 1; i >= 0; i--) {
                if (lines[i].includes('已思考') || 
                    lines[i].includes('正在搜索') || 
                    lines[i].includes('已完成') ||
                    lines[i].includes('参考') ||
                    lines[i].includes('已阅读')) {
                    // 返回从这行开始到最后的所有内容
                    return lines.slice(i).join('\n');
                }
            }
            // 如果没找到标记，返回最后100行
            return lines.slice(-100).join('\n');
        });
        
        content = text;
        
        // 如果内容太短或包含太多历史对话，尝试另一种方式
        if (content.length < 100 || (content.includes('新建对话') && content.includes('历史对话'))) {
            const allText = await page.evaluate(() => document.body.innerText);
            const allLines = allText.split('\n').filter(l => l.trim().length > 2);
            // 获取完整内容，不限制行数
            content = allLines.join('\n');
        }
        
        console.log(`\n=== ${name} ===`);
        console.log(content);
        
        // 保存到文件
        saveToFile(name, content);
    }
    
    // 豆包/Kimi
    let p1 = await findOrOpen('https://www.doubao.com/chat/', '豆包');
    await ask(p1, QUESTION, '豆包');
    await collect(p1, '豆包');
    
    let p2 = await findOrOpen('https://www.kimi.com/', 'Kimi');
    await ask(p2, QUESTION, 'Kimi');
    await collect(p2, 'Kimi');
    
    console.log("\n=== subagent1 完成 ===");
    await browser.close();
}

main().catch(e => console.error("错误:", e.message));
