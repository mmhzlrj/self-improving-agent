#!/usr/bin/env python3
"""Semantic Memory Skill - 查询历史聊天上下文"""
import sys
import json
import urllib.request

SEMANTIC_CACHE_URL = "http://192.168.1.18:5050"

def search(query, top_k=5, threshold=0.5):
    data = json.dumps({
        "query": query,
        "top_k": top_k,
        "threshold": threshold
    }).encode()

    req = urllib.request.Request(
        f"{SEMANTIC_CACHE_URL}/search",
        data=data,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

def format_results(result):
    if not result["results"]:
        return "没有找到相关的历史聊天记录。"

    hit_count = len(result["results"])
    total = result.get("total", 0)
    lines = [f"**相关历史记录** (共 {hit_count} 条，索引库 {total} 条)：\n"]
    for i, r in enumerate(result["results"], 1):
        sim = r["similarity"]
        text = r["text"].replace("\n", " ")[:200]
        lines.append(f"{i}. [{sim:.2f}] {text}...")

    return "\n".join(lines)

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5

    if not query:
        print("用法: python3 semantic_search.py <查询内容> [top_k] [threshold]")
        sys.exit(1)

    try:
        result = search(query, top_k, threshold)
        print(format_results(result))
    except Exception as e:
        print(f"Semantic Cache 查询失败: {e}")
        sys.exit(1)
