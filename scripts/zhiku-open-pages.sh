#!/bin/bash
# 打开 5 个 AI 平台 - 串行版本

echo "=== 打开 5 个 AI 平台 ==="

for url in \
    "https://chat.deepseek.com/" \
    "https://www.doubao.com/chat/38416305792801026" \
    "https://chat.qwen.ai/" \
    "https://chatglm.cn/" \
    "https://www.kimi.com/"; do
    
    echo "打开: $url"
    openclaw browser navigate "$url"
    sleep 2
done

echo "完成!"
