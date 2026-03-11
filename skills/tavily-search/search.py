#!/usr/bin/env python3
"""
Tavily Search Script
Usage: python3 search.py "<query>" [max_results]
"""

import sys
import json
from tavily import TavilyClient

# Tavily API Key
API_KEY = "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"

def search(query, max_results=5):
    client = TavilyClient(api_key=API_KEY)
    results = client.search(
        query=query,
        max_results=max_results,
        include_answer=True,
        include_images=True
    )
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 search.py \"<query>\" [max_results]")
        sys.exit(1)
    
    query = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    try:
        results = search(query, max_results)
        
        # 打印结果
        print(f"\n🔍 搜索: {query}")
        print(f"📊 返回 {len(results.get('results', []))} 个结果\n")
        
        for i, r in enumerate(results.get('results', []), 1):
            print(f"{i}. {r.get('title', 'No title')}")
            print(f"   📎 {r.get('url', 'No URL')}")
            print(f"   📝 {r.get('content', 'No content')[:200]}...")
            print(f"   ⭐ 相关度: {r.get('score', 0):.2f}")
            print()
        
        if results.get('answer'):
            print(f"💡 AI 摘要:\n{results.get('answer')}")
        
        print(f"\n⏱️ 响应时间: {results.get('response_time', 0):.2f}s")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
