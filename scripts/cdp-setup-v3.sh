#!/bin/bash
# CDP 平台设置脚本 - 最终版 (v3.2)
# 添加 all 模式导航

PLATFORM="$1"

case "$PLATFORM" in
    deepseek)
        echo "=== DeepSeek ==="
        openclaw browser navigate "https://chat.deepseek.com/"
        sleep 2
        openclaw browser evaluate --fn 'document.querySelector("textarea")?.focus()'
        sleep 1
        SNAP=$(openclaw browser snapshot 2>&1)
        DEEP=$(echo "$SNAP" | grep -o 'button "深度思考" \[ref=e[0-9]*' | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$DEEP" ] && openclaw browser click "$DEEP" && echo "✓ 点击了深度思考"
        ;;
        
    doubao)
        echo "=== Doubao ==="
        openclaw browser navigate "https://www.doubao.com/chat/38416305792801026"
        sleep 2
        SNAP=$(openclaw browser snapshot 2>&1)
        MODEL=$(echo "$SNAP" | grep -E 'button "(快速|思考|专家)"' | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$MODEL" ] && openclaw browser click "$MODEL" && sleep 1
        SNAP2=$(openclaw browser snapshot 2>&1)
        EXPERT=$(echo "$SNAP2" | grep -o 'menuitem "专家[^"]*" \[ref=e[0-9]*' | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$EXPERT" ] && openclaw browser click "$EXPERT" && echo "✓ 切换到专家"
        ;;
        
    qwen)
        echo "=== Qwen ==="
        openclaw browser navigate "https://chat.qwen.ai/"
        sleep 2
        SNAP=$(openclaw browser snapshot 2>&1)
        AUTO=$(echo "$SNAP" | grep "自动" | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$AUTO" ] && openclaw browser click "$AUTO" && sleep 1
        SNAP2=$(openclaw browser snapshot 2>&1)
        THINK=$(echo "$SNAP2" | grep -o 'option "[^"]*思考[^"]*" \[ref=e[0-9]*' | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$THINK" ] && openclaw browser click "$THINK" && echo "✓ 切换到思考"
        ;;
        
    glm)
        echo "=== GLM ==="
        openclaw browser navigate "https://chatglm.cn/"
        sleep 2
        SNAP=$(openclaw browser snapshot 2>&1)
        THINK=$(echo "$SNAP" | grep -B2 "思考" | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$THINK" ] && openclaw browser click "$THINK" && sleep 1
        SNAP2=$(openclaw browser snapshot 2>&1)
        NET=$(echo "$SNAP2" | grep -B2 "联网" | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$NET" ] && openclaw browser click "$NET" && echo "✓ 开启了思考和联网"
        ;;
        
    kimi)
        echo "=== Kimi ==="
        openclaw browser navigate "https://kimi.moonshot.cn/"
        sleep 2
        SNAP=$(openclaw browser snapshot 2>&1)
        if echo "$SNAP" | grep -q "思考"; then
            echo "✓ 已是思考模式"
        fi
        ;;
        
    all)
        echo "=== 设置所有平台 ==="
        $0 deepseek
        sleep 1
        $0 doubao
        sleep 1
        $0 qwen
        sleep 1
        $0 glm
        sleep 1
        $0 kimi
        echo "=== 全部完成 ==="
        ;;
        
    *)
        echo "Usage: $0 [deepseek|doubao|qwen|glm|kimi|all]"
        ;;
esac
