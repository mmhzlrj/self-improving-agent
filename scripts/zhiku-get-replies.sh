#!/bin/bash
# 获取各平台回复

echo "=== 等待回复 (20秒) ==="
sleep 20

node -e "
const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
    const ctx = browser.contexts()[0];
    
    const platforms = [
        { name: 'DeepSeek', keyword: 'deepseek' },
        { name: '豆包', keyword: 'doubao' },
        { name: '千问', keyword: 'qwen.ai' },
        { name: '智谱', keyword: 'chatglm' },
        { name: 'Kimi', keyword: 'kimi.com' }
    ];
    
    for (const p of platforms) {
        for (const page of ctx.pages()) {
            if (!page.url().includes(p.keyword)) continue;
            
            await page.waitForTimeout(2000);
            
            const text = await page.evaluate(() => {
                // 获取 body 文本
                return document.body.innerText;
            });
            
            // 提取最后 300 字符
            const reply = text.slice(-300).trim();
            
            console.log('=== ' + p.name + ' ===');
            console.log(reply || '(无回复)');
            console.log('');
            break;
        }
    }
    
    await browser.close();
})();
"
