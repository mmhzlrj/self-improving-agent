#!/bin/bash
# 同时向多个 AI 平台发送问题 - 修复版

QUESTION="$1"

if [ -z "$QUESTION" ]; then
    echo "用法: $0 \"你的问题\""
    echo "示例: $0 \"用一句话介绍你自己\""
    exit 1
fi

echo "=== 群发问题: $QUESTION ==="

# 发送函数
send_to_platform() {
    local platform="$1"
    local url="$2"
    
    echo ""
    echo "--- $platform ---"
    
    # 导航
    openclaw browser navigate "$url"
    sleep 2
    
    # 用 JavaScript 发送消息
    node -e "
const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
    const ctx = browser.contexts()[0];
    
    for (const p of ctx.pages()) {
        const pageUrl = p.url();
        const targetUrl = '$url';
        
        // 更宽松的匹配
        if (pageUrl.includes(targetUrl.split('?')[0].replace('https://', '').replace('http://', ''))) {
            console.log('Found page:', pageUrl);
            
            // 方法1: textarea (取第一个)
            const textarea = p.locator('textarea').first();
            if (await textarea.count() > 0) {
                await textarea.fill('$QUESTION');
                await textarea.press('Enter');
                console.log('Sent via textarea!');
                await browser.close();
                return;
            }
            
            // 方法2: contenteditable div (Kimi)
            const editable = p.locator('div[contenteditable=\"true\"]').first();
            if (await editable.count() > 0) {
                await editable.fill('$QUESTION');
                await editable.press('Enter');
                console.log('Sent via contenteditable!');
                await browser.close();
                return;
            }
        }
    }
    await browser.close();
})();
"
}

# DeepSeek
send_to_platform "DeepSeek" "https://chat.deepseek.com/"

# 豆包
send_to_platform "豆包" "https://www.doubao.com/chat/38416305792801026"

# 千问
send_to_platform "千问" "https://chat.qwen.ai/"

# 智谱
send_to_platform "智谱" "https://chatglm.cn/"

# Kimi
send_to_platform "Kimi" "https://www.kimi.com/"

echo ""
echo "=== 全部发送完成 ==="
