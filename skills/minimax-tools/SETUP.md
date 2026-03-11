# MiniMax Tools 配置教程

本文档记录了如何在 OpenClaw 中配置 MiniMax Tools，直接调用 MiniMax Coding Plan API 实现网络搜索和图片理解功能。

---

## 背景

MiniMax Coding Plan MCP 是给 Claude Code / Cursor / OpenCode 用的，OpenClaw 暂不支持 MCP 客户端。因此我们直接用 Python 调用 MiniMax API。

---

## 前置条件

1. MiniMax Coding Plan 订阅
2. API Key（从 https://platform.minimaxi.com/user-center/basic-information/interface-key 获取）

---

## 配置步骤

### 1. 安装 uvx（如需要）

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip3 install uv
```

### 2. 创建 Skill 目录

```bash
mkdir -p ~/.openclaw/workspace/skills/minimax-tools
```

### 3. 创建 minimax.py 脚本

⚠️ **重要：以下是正确的代码，请直接使用**

```python
#!/usr/bin/env python3
"""
MiniMax Tools - 网络搜索和图片理解
使用 MiniMax Coding Plan API
"""

import os
import sys
import json
import base64
import requests
from urllib.parse import urlparse

# MiniMax API 配置
API_KEY = "你的API_KEY"
API_HOST = "https://api.minimaxi.com"

def web_search(query, num_results=5):
    """网络搜索"""
    url = f"{API_HOST}/v1/coding_plan/search"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"q": query}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()
        
        print(f"\n🔍 搜索: {query}")
        print(f"📊 返回 {num_results} 个结果\n")
        
        results = data.get("organic", [])[:num_results]
        for i, r in enumerate(results, 1):
            print(f"{i}. {r.get('title', 'No title')}")
            print(f"   📎 {r.get('link', 'No URL')}")
            print(f"   📝 {r.get('snippet', 'No snippet')[:200]}...")
            print()
        
        related = data.get("related_searches", [])
        if related:
            print(f"💡 相关搜索:")
            for r in related[:5]:
                print(f"   - {r.get('query', '')}")
        
    except Exception as e:
        print(f"❌ 搜索错误: {str(e)}")

def understand_image(prompt, image_source):
    """图片理解"""
    url = f"{API_HOST}/v1/coding_plan/vlm"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # ⚠️ 关键：正确处理图片格式
    if image_source.startswith("http://") or image_source.startswith("https://"):
        # URL - 使用字典格式
        image_url = {"type": "url", "url": image_source}
    elif os.path.isfile(image_source):
        # 本地文件 -> 直接使用 data URL 格式字符串（不是字典！）
        with open(image_source, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
            ext = os.path.splitext(image_source)[1].lower()
            mime = {"jpg": "jpeg", "png": "png", "webp": "webp"}.get(ext.replace(".", ""), "jpeg")
            # ⚠️ 关键：这里必须是字符串格式，不是字典！
            image_url = f"data:image/{mime};base64,{img_data}"
    else:
        # 假设是 base64 data URL
        image_url = image_source
    
    # ⚠️ 关键：必须添加 model 参数！
    payload = {
        "model": "abab6.5s-chat",
        "prompt": prompt,
        "image_url": image_url
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        data = response.json()
        
        print(f"\n🖼️ 图片理解")
        print(f"📝 问题: {prompt}")
        print(f"\n💡 分析结果:\n")
        print(data.get("content", "无结果"))
        
    except Exception as e:
        print(f"❌ 图片理解错误: {str(e)}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 minimax.py search <关键词>")
        print("  python3 minimax.py image <问题> <图片路径或URL>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "search":
        if len(sys.argv) < 3:
            print("Usage: python3 minimax.py search <关键词>")
            sys.exit(1)
        query = sys.argv[2]
        web_search(query)
    
    elif command == "image":
        if len(sys.argv) < 4:
            print("Usage: python3 minimax.py image <问题> <图片路径或URL>")
            sys.exit(1)
        prompt = sys.argv[2]
        image_source = sys.argv[3]
        understand_image(prompt, image_source)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 4. 替换 API Key

在 `minimax.py` 中替换：

```python
API_KEY = "你的API_KEY"
```

---

## ⚠️ 关键修复记录

### 第一次失败的原因

1. **图片理解返回 empty**：开始返回空结果

2. **返回 400 invalid params**：参数错误

### 成功的原因

通过查看 MCP 源码和不断调试，发现：

1. **必须添加 model 参数**：
   ```python
   payload = {
       "model": "abab6.5s-chat",  # ← 这个很重要！
       "prompt": prompt,
       "image_url": image_url
   }
   ```

2. **图片 URL 格式必须是字符串**：
   ```python
   # ❌ 错误（字典格式）
   image_url = {"type": "base64", "url": "data:image/png;base64,..."}
   
   # ✅ 正确（纯字符串）
   image_url = f"data:image/{mime};base64,{img_data}"
   ```

3. **HTTP/HTTPS URL 可以用字典**：
   ```python
   # HTTP URL 可以用字典
   image_url = {"type": "url", "url": "https://..."}
   ```

---

## 测试

```bash
# 测试搜索
python3 ~/.openclaw/workspace/skills/minimax-tools/minimax.py search "测试"

# 测试图片理解
python3 ~/.openclaw/workspace/skills/minimax-tools/minimax.py image "描述图片" "/path/to/image.png"
```

---

## 注意事项

1. 使用会消耗 MiniMax Coding Plan 套餐额度
2. Starter 套餐包含图像理解和联网搜索 MCP
3. OpenClaw 官方支持 MCP 客户端后可替换为官方方案
4. 可以配合 Tavily Search 使用

---

## 相关文档

- MiniMax API 文档：https://platform.minimaxi.com/docs
- Coding Plan MCP 源码：https://github.com/minimax-ai/minimax-coding-plan-mcp
