#!/bin/bash
# 智库脚本 - 完整版
# 功能：自动打开5个平台 → 发送问题 → 等待30秒 → 获取回复 → 显示结果

QUESTION="$1"

if [ -z "$QUESTION" ]; then
    echo "用法: $0 <问题>"
    exit 1
fi

echo "=== 智库问答: $QUESTION ==="
echo ""

# 确保 playwright 可用
if ! node -e "require('playwright')" 2>/dev/null; then
    echo "错误: 需要安装 playwright"
    exit 1
fi

# 使用 Node.js 脚本完成所有操作（避免多次连接断开）
node -e "
const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
    const ctx = browser.contexts()[0];
    
    const question = process.argv[2];
    const platforms = [
        { name: 'DeepSeek', url: 'https://chat.deepseek.com/', keyword: 'deepseek' },
        { name: '豆包', url: 'https://www.doubao.com/chat/38416305792801026', keyword: 'doubao' },
        { name: '千问', url: 'https://chat.qwen.ai/', keyword: 'qwen.ai' },
        { name: '智谱', url: 'https://chatglm.cn/', keyword: 'chatglm' },
        { name: 'Kimi', url: 'https://www.kimi.com/', keyword: 'kimi.com' }
    ];
    
    // 1. 检查并打开需要的页面
    console.log('检查页面状态...');
    let pages = ctx.pages();
    console.log('当前页面数:', pages.length);
    
    // 检查每个平台是否已打开
    const existingUrls = pages.map(p => p.url());
    const needOpen = platforms.filter(p => !existingUrls.some(u => u.includes(p.keyword)));
    
    if (needOpen.length > 0) {
        console.log('打开新平台页面...');
        for (const p of needOpen) {
            const page = await ctx.newPage();
            await page.goto(p.url);
            console.log('已打开:', p.name);
            await page.waitForTimeout(1500);
        }
    }
    
    // 2. 发送问题到所有平台
    console.log('');
    console.log('发送问题...');
    pages = ctx.pages();
    let sentCount = 0;
    
    for (const page of pages) {
        const url = page.url();
        const p = platforms.find(pl => url.includes(pl.keyword));
        if (!p) continue;
        
        console.log('→ ' + p.name + ': 发送中...');
        
        // 尝试找到输入框
        let inputFilled = false;
        
        // 方法1: textarea
        const ta = page.locator('textarea').first();
        if (await ta.count() > 0) {
            await ta.fill(question);
            await ta.press('Enter');
            inputFilled = true;
        }
        // 方法2: contenteditable div
        else {
            const ed = page.locator('div[contenteditable=\"true\"]').first();
            if (await ed.count() > 0) {
                await ed.fill(question);
                await ed.press('Enter');
                inputFilled = true;
            }
        }
        
        if (inputFilled) {
            console.log('  ✓ 已发送');
            sentCount++;
        } else {
            console.log('  ✗ 未找到输入框');
        }
        
        await page.waitForTimeout(500);
    }
    
    console.log('');
    console.log('已发送到', sentCount, '个平台');
    console.log('等待回复 (30秒)...');
    
    // 3. 等待30秒
    await new Promise(r => setTimeout(r, 30000));
    
    // 4. 获取回复
    console.log('');
    console.log('=== 各平台回复 ===');
    console.log('');
    
    pages = ctx.pages();
    for (const page of pages) {
        const url = page.url();
        const p = platforms.find(pl => url.includes(pl.keyword));
        if (!p) continue;
        
        await page.waitForTimeout(1000);
        
        // 获取页面文本
        const text = await page.evaluate(() => document.body.innerText);
        
        // 提取回复（取最后500字符）
        const reply = text.slice(-500).trim();
        
        console.log('【' + p.name + '】');
        console.log(reply || '(无回复)');
        console.log('');
    }
    
    await browser.close();
    console.log('完成!');
})();
" "$QUESTION"
