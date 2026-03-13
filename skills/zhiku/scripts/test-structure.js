#!/usr/bin/env node
// 测试页面结构

const { chromium } = require('playwright');

async function testPageStructure(platform, url) {
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
    
    // 获取页面innerText看看有什么
    const text = await page.evaluate(() => document.body.innerText);
    console.log(`页面内容长度: ${text.length}`);
    console.log(`最后500字: ${text.slice(-500)}`);
    
    // 看看有哪些元素
    const elements = await page.evaluate(() => {
        const all = document.querySelectorAll('*');
        const result = {};
        
        for (const el of all) {
            const tag = el.tagName.toLowerCase();
            result[tag] = (result[tag] || 0) + 1;
        }
        
        return result;
    });
    
    console.log('元素统计:', elements);
    
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
testPageStructure(cfg.platform, cfg.url).catch(console.error);
