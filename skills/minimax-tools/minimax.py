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
# 请替换为你的 API Key
API_KEY = "sk-cp-wEiHHliuPGtLE9x63yViVXozeZu0UxOicm7MIuRpzBs-b7pkz78gr61YYCZ46yNjauf6eFh8LkBFnP4fhvBzmxFWSjAbWZo5S7ag7d5vDtijN9akDB6NNA4"
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
    
    # 处理图片来源
    if image_source.startswith("http://") or image_source.startswith("https://"):
        # URL - 使用字典格式
        image_url = {"type": "url", "url": image_source}
    elif os.path.isfile(image_source):
        # 本地文件 -> base64 data URL 格式
        with open(image_source, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
            ext = os.path.splitext(image_source)[1].lower()
            mime = {"jpg": "jpeg", "png": "png", "webp": "webp"}.get(ext.replace(".", ""), "jpeg")
            # 直接使用 data URL 格式字符串
            image_url = f"data:image/{mime};base64,{img_data}"
    else:
        # 假设是 base64 data URL
        image_url = image_source
    
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
