#!/usr/bin/env node
// 详细检查按钮和消息

const { chromium } = require('playwright');

async function testDetailed(platform, url) {
    console.log(`\n=== 详细检查 ${platform} ===`);
    
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800', {
        headers: { 'Client-Wants-Ephemeral-DevTools-Context': 'true' }
    });
    const ctx = browser.contexts()[0];
    
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
    
    // 详细检查按钮
    const buttonInfo = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        
        return buttons.slice(0, 20).map((btn, i) => {
            return {
                index: i,
                text: btn.textContent?.trim().slice(0, 20) || '',
                ariaLabel: btn.getAttribute('aria-label') || '',
                title: btn.getAttribute('title') || '',
                className: btn.className?.slice(0, 40) || '',
                role: btn.getAttribute('role') || '',
                id: btn.id || '',
                parentClass: btn.parentElement?.className?.slice(0, 30) || ''
            };
        });
    });
    
    console.log('按钮详情:');
    buttonInfo.forEach(b => {
        console.log(`  [${b.index}] "${b.text}" aria="${b.ariaLabel}" title="${b.title}" class="${b.className}" parent="${b.parentClass}"`);
    });
    
    // 检查消息区域
    const msgInfo = await page.evaluate(() => {
        const selectors = [
            '[data-role="assistant"]',
            '.message-content',
            '.assistant-message',
            '.chat-message',
            '[class*="message"]',
            '[class*="response"]'
        ];
        
        const result = {};
        for (const sel of selectors) {
            const els = document.querySelectorAll(sel);
            result[sel] = els.length;
        }
        return result;
    });
    
    console.log('\n消息容器统计:', msgInfo);
    
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
testDetailed(cfg.platform, cfg.url).catch(console.error);
