#!/usr/bin/env python3
"""
Tavily Extract Script
Usage: python3 extract.py "<url>" [query]
"""

import sys
from tavily import TavilyClient

# Tavily API Key
API_KEY = "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"

def extract(urls, query=None):
    client = TavilyClient(api_key=API_KEY)
    results = client.extract(
        urls=urls,
        query=query
    )
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract.py <url> [query]")
        sys.exit(1)
    
    urls = [sys.argv[1]]
    query = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        results = extract(urls, query)
        
        print(f"\n📄 提取内容: {urls[0]}\n")
        
        for result in results.get('results', []):
            print(f"📎 URL: {result.get('url')}")
            print(f"📝 内容:\n{result.get('content', 'No content')[:2000]}")
            if result.get('content') and len(result.get('content', '')) > 2000:
                print("... (truncated)")
            print()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
