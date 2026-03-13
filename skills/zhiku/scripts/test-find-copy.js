#!/usr/bin/env node
// 查找复制图标

const { chromium } = require('playwright');

async function findCopyIcon(platform, url) {
    console.log(`\n=== 查找复制图标 ${platform} ===`);
    
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
    
    // 查找所有SVG
    const svgs = await page.evaluate(() => {
        const allSvgs = Array.from(document.querySelectorAll('svg'));
        
        return allSvgs.slice(0, 30).map((svg, i) => {
            const path = svg.querySelector('path');
            const d = path?.getAttribute('d') || '';
            const parent = svg.parentElement;
            const parentClass = parent?.className?.toString().slice(0, 40) || '';
            const grandparent = parent?.parentElement;
            const gpClass = grandparent?.className?.toString().slice(0, 40) || '';
            
            return {
                index: i,
                d: d.slice(0, 50),
                parentClass,
                gpClass
            };
        });
    });
    
    console.log('SVG信息:');
    svgs.forEach(s => {
        console.log(`  [${s.index}] d="${s.d}" parent="${s.parentClass}" gp="${s.gpClass}"`);
    });
    
    // 查找包含"复制"相关文字的元素
    const copyElements = await page.evaluate(() => {
        const all = Array.from(document.querySelectorAll('*'));
        return all.filter(el => {
            const text = el.textContent?.toLowerCase() || '';
            return text.includes('复制') || text.includes('copy');
        }).slice(0, 10).map(el => ({
            tag: el.tagName,
            text: el.textContent?.trim().slice(0, 30),
            class: el.className?.toString().slice(0, 40)
        }));
    });
    
    console.log('\n包含"复制"的元素:');
    copyElements.forEach(e => {
        console.log(`  <${e.tag}> "${e.text}" class="${e.class}"`);
    });
    
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
findCopyIcon(cfg.platform, cfg.url).catch(console.error);
