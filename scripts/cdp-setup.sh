#!/bin/bash
# CDP 平台设置脚本（使用 Browser Relay 获取按钮位置）

PLATFORM="$1"

case "$PLATFORM" in
    deepseek)
        echo "Setting DeepSeek..."
        # 聚焦输入框让按钮显示
        openclaw browser evaluate --fn 'document.querySelector("textarea").focus()'
        sleep 1
        
        # 获取快照找按钮
        SNAPSHOT=$(openclaw browser snapshot 2>&1)
        
        # 深度思考按钮
        DEEP_BTN=$(echo "$SNAPSHOT" | grep -o 'button "深度思考" \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
        
        if [ -n "$DEEP_BTN" ]; then
            openclaw browser click "$DEEP_BTN"
            echo "Clicked 深度思考"
        fi
        ;;
        
    doubao)
        echo "Setting Doubao..."
        # 点击模型选择
        SNAPSHOT=$(openclaw browser snapshot 2>&1)
        
        # 快速按钮
        FAST_BTN=$(echo "$SNAPSHOT" | grep -o 'button "快速" \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
        
        if [ -n "$FAST_BTN" ]; then
            openclaw browser click "$FAST_BTN"
            sleep 1
            
            # 选择专家
            MENU=$(openclaw browser snapshot 2>&1)
            EXPERT_BTN=$(echo "$MENU" | grep -o 'menuitem "专家[^"]*" \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
            
            if [ -n "$EXPERT_BTN" ]; then
                openclaw browser click "$EXPERT_BTN"
                echo "Switched to 专家"
            fi
        fi
        ;;
        
    qwen)
        echo "Setting Qwen..."
        # 点击模型选择
        openclaw browser click e83
        sleep 1
        
        # 选择思考
        MENU=$(openclaw browser snapshot 2>&1)
        THINK_BTN=$(echo "$MENU" | grep -o 'menuitem "[^"]*思考[^"]*" \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
        
        if [ -n "$THINK_BTN" ]; then
            openclaw browser click "$THINK_BTN"
            echo "Switched to 思考"
        fi
        ;;
        
    glm)
        echo "Setting GLM..."
        # 点击思考和联网按钮
        SNAPSHOT=$(openclaw browser snapshot 2>&1)
        
        THINK_BTN=$(echo "$SNAPSHOT" | grep -o 'button "思考" \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
        NET_BTN=$(echo "$SNAPSHOT" | grep -o 'button "联网" \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
        
        if [ -n "$THINK_BTN" ]; then
            openclaw browser click "$THINK_BTN"
            echo "Clicked 思考"
        fi
        
        if [ -n "$NET_BTN" ]; then
            openclaw browser click "$NET_BTN"
            echo "Clicked 联网"
        fi
        ;;
        
    kimi)
        echo "Setting Kimi..."
        # 点击模型选择
        openclaw browser click e83
        sleep 1
        
        # 选择思考
        MENU=$(openclaw browser snapshot 2>&1)
        THINK_BTN=$(echo "$MENU" | grep -o 'menuitem "[^"]*思考[^"]*" \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
        
        if [ -n "$THINK_BTN" ]; then
            openclaw browser click "$THINK_BTN"
            echo "Switched to 思考"
        fi
        ;;
        
    *)
        echo "Usage: $0 [deepseek|doubao|qwen|glm|kimi]"
        ;;
esac
