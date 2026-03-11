#!/bin/bash
# CDP 平台设置脚本 - 简化版

set -e

PLATFORM="$1"

case "$PLATFORM" in
    deepseek)
        echo "=== DeepSeek ==="
        openclaw browser evaluate --fn 'document.querySelector("textarea")?.focus()'
        sleep 1
        SNAP=$(openclaw browser snapshot 2>&1)
        DEEP=$(echo "$SNAP" | grep -o 'button "深度思考" \[ref=e[0-9]*' | grep -o 'ref=e[0-9]*' | head -1)
        SEARCH=$(echo "$SNAP" | grep -o 'button "智能搜索" \[ref=e[0-9]*' | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$DEEP" ] && openclaw browser click "$DEEP"
        [ -n "$SEARCH" ] && openclaw browser click "$SEARCH"
        echo "Done"
        ;;
        
    doubao)
        echo "=== Doubao ==="
        SNAP=$(openclaw browser snapshot 2>&1)
        MODEL=$(echo "$SNAP" | grep -o 'button "[^"]*" \[ref=e[0-9]*' | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$MODEL" ] && openclaw browser click "$MODEL"
        sleep 1
        SNAP2=$(openclaw browser snapshot 2>&1)
        EXPERT=$(echo "$SNAP2" | grep -o 'menuitem "专家[^"]*" \[ref=e[0-9]*' | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$EXPERT" ] && openclaw browser click "$EXPERT"
        echo "Done"
        ;;
        
    qwen)
        echo "=== Qwen ==="
        SNAP=$(openclaw browser snapshot 2>&1)
        AUTO=$(echo "$SNAP" | grep "自动" | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$AUTO" ] && openclaw browser click "$AUTO"
        sleep 1
        SNAP2=$(openclaw browser snapshot 2>&1)
        THINK=$(echo "$SNAP2" | grep -o 'option "[^"]*思考[^"]*" \[ref=e[0-9]*' | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$THINK" ] && openclaw browser click "$THINK"
        echo "Done"
        ;;
        
    glm)
        echo "=== GLM ==="
        SNAP=$(openclaw browser snapshot 2>&1)
        THINK=$(echo "$SNAP" | grep -B2 "思考" | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$THINK" ] && openclaw browser click "$THINK"
        sleep 1
        SNAP2=$(openclaw browser snapshot 2>&1)
        NET=$(echo "$SNAP2" | grep -B2 "联网" | grep -o 'ref=e[0-9]*' | head -1)
        [ -n "$NET" ] && openclaw browser click "$NET"
        echo "Done"
        ;;
        
    kimi)
        echo "=== Kimi ==="
        SNAP=$(openclaw browser snapshot 2>&1)
        if echo "$SNAP" | grep -q "思考"; then
            echo "Already in 思考 mode"
        fi
        echo "Done"
        ;;
        
    all)
        echo "=== All ==="
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
