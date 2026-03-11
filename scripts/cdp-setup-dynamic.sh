#!/bin/bash
# CDP 平台设置脚本 - 动态获取 ref

PLATFORM="$1"

# 动态获取 ref 的函数
get_ref() {
    local pattern="$1"
    openclaw browser snapshot 2>&1 | grep -o "${pattern} \[ref=e[0-9]*\]" | grep -o 'ref=e[0-9]*' | head -1
}

# 获取按钮文本
get_button_ref() {
    local text="$1"
    openclaw browser snapshot 2>&1 | grep -o "button \"${text}\" \[ref=e[0-9]*\]" | grep -o 'ref=e[0-9]*' | head -1
}

case "$PLATFORM" in
    deepseek)
        echo "=== Setting up DeepSeek ==="
        
        # 聚焦输入框让按钮显示
        openclaw browser evaluate --fn 'document.querySelector("textarea")?.focus()'
        sleep 1
        
        # 获取深度思考按钮 ref
        DEEP_REF=$(get_button_ref "深度思考")
        if [ -n "$DEEP_REF" ]; then
            openclaw browser click "$DEEP_REF"
            echo "Clicked 深度思考 ($DEEP_REF)"
        fi
        
        # 获取智能搜索按钮 ref
        SEARCH_REF=$(get_button_ref "智能搜索")
        if [ -n "$SEARCH_REF" ]; then
            openclaw browser click "$SEARCH_REF"
            echo "Clicked 智能搜索 ($SEARCH_REF)"
        fi
        ;;
        
    doubao)
        echo "=== Setting up Doubao ==="
        
        # 点击模型选择按钮（快速/思考/专家）
        MODEL_REF=$(get_button_ref "快速")
        [ -z "$MODEL_REF" ] && MODEL_REF=$(get_button_ref "思考")
        [ -z "$MODEL_REF" ] && MODEL_REF=$(get_button_ref "专家")
        
        if [ -n "$MODEL_REF" ]; then
            openclaw browser click "$MODEL_REF"
            echo "Clicked 模型选择 ($MODEL_REF)"
            sleep 1
            
            # 选择专家模式
            EXPERT_REF=$(openclaw browser snapshot 2>&1 | grep -o 'menuitem "专家[^"]*" \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
            
            if [ -n "$EXPERT_REF" ]; then
                openclaw browser click "$EXPERT_REF"
                echo "Selected 专家 ($EXPERT_REF)"
            fi
        fi
        ;;
        
    qwen)
        echo "=== Setting up Qwen ==="
        
        # 点击模型选择（自动）- 可能是 generic 或 combobox
        AUTO_REF=$(openclaw browser snapshot 2>&1 | grep -o 'generic "[^"]*自动[^"]*" \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
        
        # 也可能是 combobox
        [ -z "$AUTO_REF" ] && AUTO_REF=$(openclaw browser snapshot 2>&1 | grep -o 'combobox \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
        
        if [ -n "$AUTO_REF" ]; then
            openclaw browser click "$AUTO_REF"
            echo "Clicked 自动 ($AUTO_REF)"
            sleep 1
            
            # 选择思考模式
            THINK_REF=$(openclaw browser snapshot 2>&1 | grep -o 'option "[^"]*思考[^"]*" \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
            
            if [ -n "$THINK_REF" ]; then
                openclaw browser click "$THINK_REF"
                echo "Selected 思考 ($THINK_REF)"
            fi
        fi
        ;;
        
    glm)
        echo "=== Setting up GLM ==="
        
        # 思考按钮
        THINK_REF=$(openclaw browser snapshot 2>&1 | grep -o 'button "思考" \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
        
        if [ -n "$THINK_REF" ]; then
            openclaw browser click "$THINK_REF"
            echo "Clicked 思考 ($THINK_REF)"
        fi
        
        # 联网按钮
        NET_REF=$(openclaw browser snapshot 2>&1 | grep -o 'button "联网" \[ref=e[0-9]*\]' | grep -o 'ref=e[0-9]*' | head -1)
        
        if [ -n "$NET_REF" ]; then
            openclaw browser click "$NET_REF"
            echo "Clicked 联网 ($NET_REF)"
        fi
        ;;
        
    kimi)
        echo "=== Setting up Kimi ==="
        
        # Kimi 默认是思考模式，检查是否为思考
        CURRENT=$(openclaw browser snapshot 2>&1 | grep -o 'generic "[^"]*K2.5[^"]*" \[ref=e[0-9]*\]' | head -1)
        
        if [ -n "$CURRENT" ]; then
            echo "Kimi already in 思考 mode"
        fi
        ;;
        
    all)
        echo "=== Setting up ALL platforms ==="
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
