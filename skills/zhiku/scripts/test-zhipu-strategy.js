#!/usr/bin/env node
// 智谱方案：多策略查找复制按钮

const { chromium } = require('playwright');

async function findCopyButtonMultiStrategy(page, platform) {
    console.log(`\n=== 多策略查找复制按钮 (${platform}) ===`);
    
    // 策略优先级数组
    const strategies = [
        // 策略1: 通过aria-label查找
        async () => {
            const selectors = [
                '[aria-label*="复制"]',
                '[aria-label*="copy" i]',
                '[aria-label*="Copy"]',
                '[title*="复制"]',
                '[title*="copy" i]',
                '[data-tooltip*="复制"]',
                '[data-tip*="复制"]',
            ];
            for (const sel of selectors) {
                const el = await page.$(sel);
                if (el) {
                    const info = await getElementInfo(el);
                    return { strategy: 'aria-label/title', selector: sel, info, element: el };
                }
            }
            return null;
        },

        // 策略2: 通过按钮内的复制图标SVG特征查找
        async () => {
            const copyIconPatterns = [
                'M16 1H4C3 1 2 2 2 3',
                'M7 9V15C7 16.1046 7.89543 17 9 17H15',
                'M9 2a1 1 0 0 0-1 1',
                'M4 4C4 2.89543 4.89543 2 6 2',
            ];
            
            const buttons = await page.$$('button, [role="button"], [class*="btn"], [class*="button"]');
            console.log(`  策略2: 检查 ${buttons.length} 个按钮`);
            
            for (let i = 0; i < buttons.length; i++) {
                try {
                    const btn = buttons[i];
                    const hasCopyIcon = await btn.evaluate((el, patterns) => {
                        const svg = el.querySelector('svg');
                        if (!svg) return false;
                        const path = svg.querySelector('path');
                        if (!path) return false;
                        const d = path.getAttribute('d') || '';
                        return patterns.some(p => d.includes(p.slice(0, 15))) || 
                            d.includes('rect') ||
                            (d.includes('M') && d.split('M').length >= 3);
                    }, copyIconPatterns);
                    
                    if (hasCopyIcon) {
                        const info = await getElementInfo(btn);
                        console.log(`  策略2: 找到可疑按钮 ${i}`);
                        return { strategy: 'SVG图标特征', selector: `button[${i}]`, info, element: btn };
                    }
                } catch(e) {
                    continue;
                }
            }
            return null;
        },

        // 策略3: 通过文字"复制"查找
        async () => {
            const textPatterns = ['复制', 'copy', 'Copy', 'Copier'];
            for (const text of textPatterns) {
                const xpath = `//*[contains(text(), "${text}")]/ancestor-or-self::*[self::button or self::*[@role='button']]`;
                const el = await page.$(xpath);
                if (el) {
                    const info = await getElementInfo(el);
                    return { strategy: '文字匹配', selector: `text: "${text}"`, info, element: el };
                }
            }
            return null;
        },

        // 策略4: 遍历所有可见按钮，分析其图标
        async () => {
            const buttons = await page.$$('button:visible, [role="button"]:visible');
            console.log(`  策略4: 检查 ${buttons.length} 个可见按钮`);
            
            for (let i = 0; i < Math.min(buttons.length, 30); i++) {
                try {
                    const btn = buttons[i];
                    const analysis = await btn.evaluate((el) => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 60 || rect.height > 40) return null;
                        
                        const svg = el.querySelector('svg');
                        if (!svg) return null;
                        
                        const paths = el.querySelectorAll('svg path');
                        let pathCount = paths.length;
                        
                        const viewBox = svg.getAttribute('viewBox') || '';
                        const isSmall = viewBox.includes('16') || viewBox.includes('20') || viewBox.includes('24');
                        
                        return {
                            size: `${rect.width}x${rect.height}`,
                            pathCount,
                            viewBox,
                            isSmall,
                            className: el.className?.slice(0, 50)
                        };
                    });
                    
                    if (analysis && analysis.pathCount >= 1 && analysis.isSmall) {
                        const info = await getElementInfo(btn);
                        console.log(`  策略4: 找到可疑按钮 ${i}: ${analysis.size}, ${analysis.viewBox}`);
                        return { strategy: '小按钮SVG分析', selector: `button[${i}]`, info, element: btn };
                    }
                } catch(e) {
                    continue;
                }
            }
            return null;
        },
    ];

    // 按优先级执行策略
    for (const strategy of strategies) {
        try {
            console.log(`\n尝试策略: ${strategy.name}`);
            const result = await strategy();
            if (result) {
                console.log(` ✓ 成功: ${result.strategy}`);
                return result;
            }
        } catch (e) {
            console.log(` ✗ 错误: ${e.message}`);
        }
    }

    return null;
}

async function getElementInfo(element) {
    return await element.evaluate((el) => ({
        tag: el.tagName,
        class: el.className?.slice(0, 60),
        id: el.id,
        ariaLabel: el.getAttribute('aria-label'),
        title: el.getAttribute('title'),
        text: el.textContent?.trim().slice(0, 30),
        rect: el.getBoundingClientRect().toJSON()
    }));
}

async function main() {
    const platform = process.argv[2] || 'doubao';
    
    const configs = {
        'doubao': { platform: '豆包', url: 'https://www.doubao.com/chat/' },
        'kimi': { platform: 'Kimi', url: 'https://www.kimi.com/' },
        'qwen': { platform: '千问', url: 'https://chat.qwen.ai/' },
        'deepseek': { platform: 'DeepSeek', url: 'https://chat.deepseek.com/' },
        'zhipu': { platform: '智谱', url: 'https://chatglm.cn/' }
    };
    
    const cfg = configs[platform] || configs.doubao;
    
    console.log(`\n开始测试: ${cfg.platform}`);
    
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800', {
        headers: { 'Client-Wants-Ephemeral-DevTools-Context': 'true' }
    });
    const ctx = browser.contexts()[0];
    
    let page = null;
    for (const p of ctx.pages()) {
        if (p.url().includes(cfg.url.replace('https://', '').split('/')[0])) {
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
    
    // 等待页面稳定
    await page.waitForLoadState('networkidle').catch(() => {});
    await page.waitForTimeout(2000);
    
    // 查找复制按钮
    const result = await findCopyButtonMultiStrategy(page, cfg.platform);
    
    if (result) {
        console.log('\n✅ 找到复制按钮!');
        console.log(' 策略:', result.strategy);
        console.log(' 选择器:', result.selector);
        console.log(' 元素信息:', JSON.stringify(result.info, null, 2));
        
        // 尝试点击
        console.log('\n尝试点击...');
        try {
            await result.element.click();
            console.log('✅ 点击成功');
            
            // 读取剪贴板
            await page.waitForTimeout(500);
            const clipboardText = await page.evaluate(async () => {
                try {
                    return await navigator.clipboard.readText();
                } catch(e) {
                    return null;
                }
            });
            
            if (clipboardText) {
                console.log('\n📋 剪贴板内容:');
                console.log(clipboardText.slice(0, 500));
            } else {
                console.log('❌ 无法读取剪贴板');
            }
        } catch(e) {
            console.log(`❌ 点击失败: ${e.message}`);
        }
    } else {
        console.log('\n❌ 未找到复制按钮');
    }
    
    await browser.close();
}

main().catch(console.error);
