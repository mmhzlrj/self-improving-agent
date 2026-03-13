#!/usr/bin/env node
// 智库 subagent2 - CDP 后台模式 v0.5
// 使用复制按钮获取回复内容

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
        
        // 重新加载页面创建新对话
        await page.goto(page.url());
        await page.waitForTimeout(5000);
        console.log("[重新加载]");
        
        // 千问需要等待textarea可编辑
        if (platform === '千问') {
            try {
                await page.waitForFunction(() => {
                    const ta = document.querySelector('textarea');
                    return ta && !ta.readOnly && ta.offsetParent !== null;
                }, { timeout: 30000 });
                console.log("[千问textarea已可编辑]");
            } catch(e) {
                console.log(`[千问等待textarea失败: ${e.message}]`);
            }
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
    
    // v0.5: 使用复制按钮获取内容
    async function collect(page, name, platform) {
        if (!page) return;
        
        let content = '';
        
        // 1. 等待回复完成 - 检测完成标记
        try {
            await page.waitForFunction(() => {
                const body = document.body.innerText;
                return body.includes('已完成') || 
                       body.includes('参考') ||
                       body.includes('已阅读') ||
                       body.includes('思考结束') ||
                       body.includes('内容由AI生成') ||
                       (body.length > 500 && body.split('\n').length > 10);
            }, { timeout: 60000 }).then(() => {
                console.log(`[${name}] 检测到回复完成`);
            }).catch(() => {
                console.log(`[${name}] 等待回复超时`);
            });
            
            // 等待额外渲染时间
            await page.waitForTimeout(3000);
            
        } catch(e) {
            console.log(`[${name}] 等待回复异常: ${e.message}`);
        }
        
        // 2. 尝试点击复制按钮
        try {
            // 先hover回复区域让按钮出现
            const lastMsg = page.locator('[data-role="assistant"], .message-content, .assistant-message').last();
            if (await lastMsg.count() > 0) {
                await lastMsg.hover().catch(() => {});
                await page.waitForTimeout(500);
            }
            
            // 查找复制按钮 - 多策略
            const copySelectors = [
                'button[aria-label*="复制"]',
                'button[aria-label*="Copy"]',
                'button:has-text("复制")',
                'button:has-text("Copy")',
                '[class*="copy"] button'
            ];
            
            let clicked = false;
            for (const sel of copySelectors) {
                const btn = page.locator(sel).last();
                if (await btn.count() > 0) {
                    try {
                        await btn.click({ timeout: 3000 });
                        console.log(`[${name}] 点击复制按钮成功`);
                        clicked = true;
                        await page.waitForTimeout(1000);
                        break;
                    } catch(e) {
                        continue;
                    }
                }
            }
            
            // 3. 从剪贴板读取
            if (clicked) {
                content = await page.evaluate(async () => {
                    try {
                        return await navigator.clipboard.readText();
                    } catch(e) {
                        return '';
                    }
                });
            }
            
        } catch(e) {
            console.log(`[${name}] 点击复制按钮失败: ${e.message}`);
        }
        
        // 4. 备用：如果没获取到内容，用innerText
        if (!content || content.length < 50) {
            console.log(`[${name}] 使用备用方案获取内容`);
            const allText = await page.evaluate(() => document.body.innerText);
            const lines = allText.split('\n');
            // 找到AI回复标记位置
            for (let i = lines.length - 1; i >= 0; i--) {
                if (lines[i].includes('已完成') || 
                    lines[i].includes('参考') ||
                    lines[i].includes('思考结束') ||
                    lines[i].includes('内容由AI生成')) {
                    content = lines.slice(i).join('\n');
                    break;
                }
            }
            if (!content) {
                content = allText;
            }
        }
        
        console.log(`\n=== ${name} ===`);
        console.log(content.slice(0, 500));
        
        // 保存到文件
        saveToFile(name, content);
    }
    
    // 平台配置
    const configs = [
        { url: 'https://chat.qwen.ai/', name: '千问', platform: '千问' },
        { url: 'https://chat.deepseek.com/', name: 'DeepSeek', platform: 'deepseek' }
    ];
    
    // 执行
    for (const cfg of configs) {
        const page = await findOrOpen(cfg.url, cfg.name);
        if (page) {
            await ask(page, QUESTION, cfg.platform);
            await collect(page, cfg.name, cfg.platform);
        }
    }
    
    console.log("=== subagent2 完成 ===");
    await browser.close();
}

main().catch(console.error);
