#!/usr/bin/env node
// 测试复制按钮功能

const { chromium } = require('playwright');

async function testCopyButton(platform, url) {
    console.log(`\n=== 测试 ${platform} ===`);
    
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800', {
        headers: { 'Client-Wants-Ephemeral-DevTools-Context': 'true' }
    });
    const ctx = browser.contexts()[0];
    
    // 找到页面
    let page = null;
    for (const p of ctx.pages()) {
        if (p.url().includes(url.replace('https://', '').split('/')[0])) {
            page = p;
            break;
        }
    }
    
    if (!page) {
        console.log(`未找到页面`);
        await browser.close();
        return;
    }
    
    console.log(`页面URL: ${page.url()}`);
    
    // 1. 先看看页面上有哪些按钮
    const buttons = await page.locator('button').all();
    console.log(`按钮数量: ${buttons.length}`);
    
    for (let i = 0; i < Math.min(buttons.length, 10); i++) {
        try {
            const btn = buttons[i];
            const text = await btn.innerText().catch(() => '');
            const ariaLabel = await btn.getAttribute('aria-label').catch(() => '');
            const title = await btn.getAttribute('title').catch(() => '');
            const className = await btn.getAttribute('class').catch(() => '');
            
            console.log(`按钮${i}: text="${text}" aria-label="${ariaLabel}" title="${title}" class="${className.slice(0,30)}"`);
        } catch(e) {
            console.log(`按钮${i}: ${e.message}`);
        }
    }
    
    // 2. 尝试找复制按钮
    const copySelectors = [
        'button[aria-label*="复制"]',
        'button[aria-label*="Copy"]',
        'button[title*="复制"]',
        'button[title*="Copy"]',
        'button:has-text("复制")',
        'button:has-text("Copy")',
    ];
    
    console.log('\n尝试找复制按钮:');
    for (const sel of copySelectors) {
        const btns = await page.locator(sel).all();
        console.log(`  ${sel}: ${btns.length}个`);
        for (let i = 0; i < Math.min(btns.length, 3); i++) {
            try {
                const text = await btns[i].innerText();
                const visible = await btns[i].isVisible();
                console.log(`    [${i}] "${text}" visible=${visible}`);
            } catch(e) {}
        }
    }
    
    // 3. 尝试hover后找按钮
    console.log('\n尝试hover后找按钮:');
    const msgContainers = await page.locator('[data-role="assistant"], .message-content, .assistant-message, .chat-message').all();
    console.log(`消息容器数量: ${msgContainers.length}`);
    
    if (msgContainers.length > 0) {
        const lastMsg = msgContainers[msgContainers.length - 1];
        await lastMsg.hover();
        await page.waitForTimeout(1000);
        
        for (const sel of copySelectors) {
            const btns = await page.locator(sel).all();
            if (btns.length > 0) {
                console.log(`  hover后 ${sel}: ${btns.length}个`);
            }
        }
    }
    
    await browser.close();
}

const args = process.argv.slice(2);
const platform = args[0] || 'doubao';

const configs = {
    'doubao': { platform: '豆包', url: 'https://www.doubao.com/chat/' },
    'kimi': { platform: 'Kimi', url: 'https://www.kimi.com/' },
    'qwen': { platform: '千问', url: 'https://chat.qwen.ai/' },
    'deepseek': { platform: 'DeepSeek', url: 'https://chat.deepseek.com/' },
    'zhipu': { platform: '智谱', url: 'https://chatglm.cn/' }
};

const cfg = configs[platform] || configs.doubao;
testCopyButton(cfg.platform, cfg.url).catch(console.error);
