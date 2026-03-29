#!/usr/bin/env python3
"""
semantic_memory.py - 按需查询语义记忆
用法: python3 semantic_memory.py <搜索query> [top_k] [threshold]
"""
import sys
import json
import urllib.request

SEMANTIC_CACHE_URL = "http://192.168.1.18:5050"

def search(query, top_k=5, threshold=0.3, msg_type=None):
    data = {
        "query": query,
        "top_k": top_k,
        "threshold": threshold
    }
    if msg_type:
        data["type"] = msg_type

    req = urllib.request.Request(
        f"{SEMANTIC_CACHE_URL}/search",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

def format_for_context(result):
    """格式化输出，适合作为上下文注入"""
    if not result.get("results"):
        return ""

    total = result.get("total", 0)
    lines = [f"**[相关历史] {len(result['results'])}/{total} 条**\n"]

    for r in result["results"]:
        text = r["text"]
        role = r.get("role", "")
        msg_type = r.get("msg_type", "")
        ts = r.get("timestamp", "")
        sim = r["similarity"]

        # 格式化标签
        type_label = ""
        if msg_type:
            type_label = f"[{msg_type}]"

        lines.append(f"**[{sim:.2f}]** {type_label} {text[:250]}")
        if ts:
            lines.append(f"   _{ts[:16]}_")
        lines.append("")

    return "\n".join(lines)

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3

    if not query:
        print("用法: semantic_memory.py <搜索内容> [top_k] [threshold]")
        print("示例: semantic_memory.py 'jetson' 5 0.3")
        sys.exit(1)

    try:
        result = search(query, top_k, threshold)
        output = format_for_context(result)
        if output:
            print(output)
        else:
            print("(无相关历史)")
    except Exception as e:
        print(f"查询失败: {e}", file=sys.stderr)
        sys.exit(1)
