#!/bin/bash
# CDP 平台设置脚本 - 最终版 (v3.1)
# 简化验证，只确保点击执行

PLATFORM="$1"

case "$PLATFORM" in
    deepseek)
        echo "=== DeepSeek ==="
        openclaw browser evaluate --fn 'document.querySelector("textarea")?.focus()'
        sleep 1
        SNAP=$(openclaw browser snapshot 2>&1)
        DEEP=$(echo "$SNAP" | grep -o 'button "深度思考" \[ref=e[0-9]*' | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$DEEP" ] && openclaw browser click "$DEEP" && echo "✓ 点击了深度思考"
        ;;
        
    doubao)
        echo "=== Doubao ==="
        SNAP=$(openclaw browser snapshot 2>&1)
        MODEL=$(echo "$SNAP" | grep -E 'button "(快速|思考|专家)"' | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$MODEL" ] && openclaw browser click "$MODEL" && sleep 1
        SNAP2=$(openclaw browser snapshot 2>&1)
        EXPERT=$(echo "$SNAP2" | grep -o 'menuitem "专家[^"]*" \[ref=e[0-9]*' | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$EXPERT" ] && openclaw browser click "$EXPERT" && echo "✓ 切换到专家"
        ;;
        
    qwen)
        echo "=== Qwen ==="
        SNAP=$(openclaw browser snapshot 2>&1)
        AUTO=$(echo "$SNAP" | grep "自动" | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$AUTO" ] && openclaw browser click "$AUTO" && sleep 1
        SNAP2=$(openclaw browser snapshot 2>&1)
        THINK=$(echo "$SNAP2" | grep -o 'option "[^"]*思考[^"]*" \[ref=e[0-9]*' | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$THINK" ] && openclaw browser click "$THINK" && echo "✓ 切换到思考"
        ;;
        
    glm)
        echo "=== GLM ==="
        SNAP=$(openclaw browser snapshot 2>&1)
        THINK=$(echo "$SNAP" | grep -B2 "思考" | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$THINK" ] && openclaw browser click "$THINK" && sleep 1
        SNAP2=$(openclaw browser snapshot 2>&1)
        NET=$(echo "$SNAP2" | grep -B2 "联网" | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$NET" ] && openclaw browser click "$NET" && echo "✓ 开启了思考和联网"
        ;;
        
    kimi)
        echo "=== Kimi ==="
        SNAP=$(openclaw browser snapshot 2>&1)
        if echo "$SNAP" | grep -q "思考"; then
            echo "✓ 已是思考模式"
        fi
        ;;
        
    all)
        echo "=== All Platforms ==="
        $0 deepseek
        $0 doubao
        $0 qwen
        $0 glm
        $0 kimi
        ;;
        
    *)
        echo "Usage: $0 [deepseek|doubao|qwen|glm|kimi|all]"
        ;;
esac
