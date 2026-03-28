#!/usr/bin/env python3
"""
semantic_memory_injector.py
在每次 session 开始时，从 Semantic Cache 检索相关历史，输出到 stdout
"""
import sys
import json
import urllib.request

SEMANTIC_CACHE_URL = "http://192.168.1.18:5050"

def get_recent_topics(n=5):
    """获取最近的对话主题"""
    # 查询一些宽泛的话题，获取最近相关的历史
    queries = ["ubuntu", "jetson", "openclaw", "gpu", "聊天记录"]
    all_results = {}

    for q in queries:
        try:
            data = json.dumps({"query": q, "top_k": n, "threshold": 0.4}).encode()
            req = urllib.request.Request(
                f"{SEMANTIC_CACHE_URL}/search",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                for r in result.get("results", []):
                    key = r["text"][:100]
                    if key not in all_results or r["similarity"] > all_results[key]["similarity"]:
                        all_results[key] = r
        except Exception as e:
            pass

    # 按相似度排序
    sorted_results = sorted(all_results.values(), key=lambda x: x["similarity"], reverse=True)
    return sorted_results[:10]

def format_context(results):
    if not results:
        return ""

    lines = ["## 相关历史上下文\n"]
    lines.append(f"（从 {len(results)} 条相关记录中提取）\n")
    lines.append("---\n")

    current_topic = ""
    for r in results:
        text = r["text"].replace("\n", " ").strip()[:300]
        sim = r["similarity"]
        lines.append(f"**[{sim:.2f}]** {text}\n")
        lines.append("---\n")

    return "".join(lines)

if __name__ == "__main__":
    print("正在检索相关历史上下文...")
    results = get_recent_topics()
    context = format_context(results)

    if context:
        print(context)
    else:
        print("（无相关历史记录）")
