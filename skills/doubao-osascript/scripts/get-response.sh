#!/bin/bash
# 豆包对话 - 获取响应脚本
# 从豆包页面提取最新的回答

# 获取页面内容并提取回答部分
openclaw browser evaluate --fn '
(function() {
    const text = document.body.innerText;
    const lines = text.split("\n");
    
    // 找到最后几行有用的回答
    const result = [];
    let capture = false;
    
    for (let i = lines.length - 1; i >= 0; i--) {
        const line = lines[i].trim();
        if (line.length > 0) {
            result.unshift(line);
            if (result.length > 20) break;
        }
    }
    
    return result.join("\n");
})()
' 2>/dev/null
