#!/usr/bin/env node
// Playwright CDP 平台设置脚本

const { chromium } = require('playwright');

async function setupPlatform(platform, action) {
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
    const ctx = browser.contexts()[0];
    
    for (const p of ctx.pages()) {
        const url = p.url();
        
        if (platform === 'deepseek' && url.includes('deepseek')) {
            console.log('Setting up DeepSeek...');
            
            // 深度思考和智能搜索是互斥的，默认设置为深度思考
            const textarea = p.locator('textarea');
            if (await textarea.count() > 0) {
                await textarea.click();
                await p.waitForTimeout(500);
            }
            
            const deepBtn = p.locator('button:has-text("深度思考")');
            if (await deepBtn.count() > 0) {
                await deepBtn.click();
                console.log('Clicked 深度思考');
            }
        }
        
        if (platform === 'doubao' && url.includes('doubao')) {
            console.log('Setting up Doubao...');
            
            const modelBtn = p.locator('button:has-text("快速")');
            if (await modelBtn.count() > 0) {
                await modelBtn.click();
                await p.waitForTimeout(1000);
                
                const expertItem = p.locator('menuitem:has-text("专家")');
                if (await expertItem.count() > 0) {
                    await expertItem.click();
                    console.log('Switched to 专家');
                }
            }
        }
        
        if (platform === 'qwen' && url.includes('qwen')) {
            console.log('Setting up Qwen...');
            
            const modelCombo = p.locator('combobox');
            if (await modelCombo.count() > 0) {
                await modelCombo.click();
                await p.waitForTimeout(1000);
                
                const thinkItem = p.locator('div:has-text("思考")').first();
                if (await thinkItem.count() > 0) {
                    await thinkItem.click();
                    console.log('Switched to 思考');
                }
            }
        }
        
        if (platform === 'glm' && url.includes('chatglm')) {
            console.log('Setting up GLM...');
            
            const thinkBtn = p.locator('button:has-text("思考")');
            if (await thinkBtn.count() > 0) {
                await thinkBtn.click();
                console.log('Clicked 思考');
            }
            
            const netBtn = p.locator('button:has-text("联网")');
            if (await netBtn.count() > 0) {
                await netBtn.click();
                console.log('Clicked 联网');
            }
        }
        
        if (platform === 'kimi' && url.includes('kimi')) {
            console.log('Setting up Kimi...');
            
            const modelBtn = p.locator('button:has-text("K2.5")');
            if (await modelBtn.count() > 0) {
                await modelBtn.click();
                await p.waitForTimeout(1000);
                
                const thinkItem = p.locator('div:has-text("思考")').first();
                if (await thinkItem.count() > 0) {
                    await thinkItem.click();
                    console.log('Switched to 思考');
                }
            }
        }
    }
    
    await browser.close();
}

async function main() {
    const platform = process.argv[2] || 'all';
    const action = process.argv[3] || 'setup';
    
    if (platform === 'all') {
        console.log('Setting up all platforms...');
        const platforms = ['deepseek', 'doubao', 'qwen', 'glm', 'kimi'];
        for (const p of platforms) {
            await setupPlatform(p, action);
        }
    } else {
        await setupPlatform(platform, action);
    }
    
    console.log('Done!');
}

main();
