#!/bin/bash
# 发送问题 - 每次重新连接

QUESTION="$1"

node -e "
const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
    const ctx = browser.contexts()[0];
    
    let count = 0;
    for (const page of ctx.pages()) {
        const url = page.url();
        if (url.includes('deepseek') || url.includes('doubao') || 
            url.includes('qwen') || url.includes('chatglm') || url.includes('kimi')) {
            
            let name = 'Unknown';
            if (url.includes('deepseek')) name = 'DeepSeek';
            else if (url.includes('doubao')) name = '豆包';
            else if (url.includes('qwen')) name = '千问';
            else if (url.includes('chatglm')) name = '智谱';
            else if (url.includes('kimi')) name = 'Kimi';
            
            console.log('Sending to ' + name + '...');
            
            const ta = page.locator('textarea').first();
            if (await ta.count() > 0) {
                await ta.fill('$QUESTION');
                await ta.press('Enter');
                count++;
                continue;
            }
            
            const ed = page.locator('div[contenteditable]').first();
            if (await ed.count() > 0) {
                await ed.fill('$QUESTION');
                await ed.press('Enter');
                count++;
            }
        }
    }
    
    console.log('Sent to ' + count + ' platform(s)');
    await browser.close();
})();
"
