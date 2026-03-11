#!/bin/bash
# 豆包对话 - 最终版 (纯 Browser Relay，CSS 选择器，零窗口跳动)
# 用法: ./send-message.sh "问题内容" [模型]

set -e

MESSAGE="$1"
MODEL="${2:-专家}"
SLEEP_TIME=20
CHAT_URL="https://www.doubao.com/chat/38416305792801026"

if [ -z "$MESSAGE" ]; then
    echo "用法: $0 \"问题内容\" [模型]"
    exit 1
fi

echo "=== 豆包对话 (后台模式) ==="

# 1. 导航
echo "导航..."
openclaw browser navigate "$CHAT_URL"
sleep 3

# 2. 切换模型
echo "切换到 $MODEL 模式..."
SNAPSHOT=$(openclaw browser snapshot 2>&1)
MODEL_BTN=$(echo "$SNAPSHOT" | grep -o 'button "[^"]*" \[ref=e[0-9]*\].*cursor=pointer' | grep -E "快速|思考|专家" | head -1)
MODEL_BTN_REF=$(echo "$MODEL_BTN" | grep -o 'ref=e[0-9]*' | head -1)

if [ -n "$MODEL_BTN_REF" ]; then
    openclaw browser click "$MODEL_BTN_REF" 2>/dev/null
    sleep 1
    MENU_SNAPSHOT=$(openclaw browser snapshot 2>&1)
    case "$MODEL" in
        "专家") MENU_ITEM=$(echo "$MENU_SNAPSHOT" | grep -o 'menuitem "[^"]*专家[^"]*" \[ref=e[0-9]*\]' | head -1) ;;
        "思考") MENU_ITEM=$(echo "$MENU_SNAPSHOT" | grep -o 'menuitem "[^"]*思考[^"]*" \[ref=e[0-9]*\]' | head -1) ;;
        "快速") MENU_ITEM=$(echo "$MENU_SNAPSHOT" | grep -o 'menuitem "[^"]*快速[^"]*" \[ref=e[0-9]*\]' | head -1) ;;
    esac
    MENU_ITEM_REF=$(echo "$MENU_ITEM" | grep -o 'ref=e[0-9]*' | head -1)
    [ -n "$MENU_ITEM_REF" ] && openclaw browser click "$MENU_ITEM_REF" 2>/dev/null
    sleep 1
fi

# 3. 用 CSS 选择器输入并发送 (零窗口跳动)
echo "输入并发送..."

openclaw browser evaluate --fn "
(function() {
    var textarea = document.querySelector('textarea');
    if (!textarea) return 'no textarea';
    
    // 输入文字
    textarea.value = '$MESSAGE';
    textarea.dispatchEvent(new Event('input', {bubbles: true}));
    
    // 找到输入框父容器中的发送按钮
    var parent = textarea.parentElement;
    while (parent && parent.tagName !== 'BODY') {
        var btns = parent.querySelectorAll('button');
        // 找到最后一个带 SVG 的按钮（发送按钮）
        for (var i = btns.length - 1; i >= 0; i--) {
            if (btns[i].querySelector('svg')) {
                btns[i].click();
                return 'sent';
            }
        }
        parent = parent.parentElement;
    }
    
    // 备选：按回车
    textarea.focus();
    textarea.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
    return 'pressed enter';
})()
" 2>/dev/null

# 4. 等待响应
echo "等待响应 ($SLEEP_TIME 秒)..."
sleep $SLEEP_TIME

# 5. 获取回答
echo "获取回答..."
RESPONSE=$(openclaw browser evaluate --fn 'document.body.innerText' 2>/dev/null)

# 6. 提取回答
echo ""
echo "=== 回答 ==="
echo "$RESPONSE" | grep -v "^$" | tail -15

echo ""
echo "=== 完成 ==="
