#!/bin/bash
# 收集回复脚本

echo "=== 收集回复 (等待30秒) ==="
sleep 30

node -e "
const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
    const ctx = browser.contexts()[0];
    
    const platforms = [
        { name: 'DeepSeek', keywords: ['deepseek'], selector: 'main' },
        { name: '豆包', keywords: ['doubao'], selector: 'main' },
        { name: '千问', keywords: ['qwen'], selector: 'main' },
        { name: '智谱', keywords: ['chatglm'], selector: 'main' },
        { name: 'Kimi', keywords: ['kimi'], selector: 'main' }
    ];
    
    for (const p of platforms) {
        for (const page of ctx.pages()) {
            const matches = p.keywords.some(k => page.url().includes(k));
            if (!matches) continue;
            
            try {
                // 等待内容加载
                await page.waitForTimeout(2000);
                
                // 获取主要内容
                const text = await page.evaluate(() => {
                    // 尝试获取 main 或 body
                    const main = document.querySelector('main');
                    const content = main || document.body;
                    
                    // 获取所有文本，尝试找到 AI 回复
                    let texts = [];
                    
                    // 方法1: 获取所有段落
                    content.querySelectorAll('p, div, span').forEach(el => {
                        const t = el.textContent.trim();
                        if (t.length > 20 && t.length < 1000) {
                            texts.push(t);
                        }
                    });
                    
                    // 返回最后几段
                    return texts.slice(-3).join('\\n');
                });
                
                console.log('=== ' + p.name + ' ===');
                console.log(text.slice(0, 400) || '(无内容)');
                console.log('');
            } catch(e) {
                console.log('=== ' + p.name + ' ===');
                console.log('获取失败');
                console.log('');
            }
            break;
        }
    }
    
    await browser.close();
})();
"
