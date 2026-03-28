#!/usr/bin/env python3
"""
Smart Context Hook - 每次 session 前自动调用
检查 Ubuntu 节点是否在线：
- 在线: 从 Semantic Cache 拉取相关上下文
- 离线: 跳过，不阻塞

用法: 放在 ~/.openclaw/workspace/ 作为一个可被引用的文件
"""
import sys
import os
import json
import urllib.request
import socket
from datetime import datetime

UBUNTU_HOST = "192.168.1.18"
SEMANTIC_CACHE_URL = "http://192.168.1.18:5050"
CONTEXT_FILE = os.path.expanduser("~/.openclaw/workspace/semantic-memory.md")

def check_ubuntu_online():
    """检查 Ubuntu 是否在线"""
    try:
        socket.setdefaulttimeout(3)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((UBUNTU_HOST, 22))
        sock.close()
        return True
    except:
        return False

def check_semantic_cache_online():
    """检查 Semantic Cache 是否可用"""
    try:
        req = urllib.request.Request(f"{SEMANTIC_CACHE_URL}/health")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read()).get("status") == "ok"
    except:
        return False

def fetch_context():
    """从 Semantic Cache 获取上下文"""
    queries = ["ubuntu node", "jetson", "openclaw", "贵庚", "gpu 训练", "robot", "聊天记录"]
    all_results = {}

    for q in queries:
        try:
            data = json.dumps({"query": q, "top_k": 3, "threshold": 0.4}).encode()
            req = urllib.request.Request(
                f"{SEMANTIC_CACHE_URL}/search",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read())
                for r in result.get("results", []):
                    key = r["text"][:80]
                    if key not in all_results or r["similarity"] > all_results[key]["similarity"]:
                        all_results[key] = r
        except Exception as e:
            pass

    return sorted(all_results.values(), key=lambda x: x["similarity"], reverse=True)[:10]

def write_context(results):
    """写入上下文文件"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# Semantic Memory - 相关历史上下文\n\n> 自动更新于 {now}\n\n"]
    lines.append(f"**Ubuntu 节点状态**: 在线\n\n")
    lines.append("## 相关历史上下文\n\n")
    for r in results:
        sim = r["similarity"]
        text = r["text"].replace("\n", " ").strip()[:250]
        lines.append(f"- **[{sim:.2f}]** {text}\n\n")
    with open(CONTEXT_FILE, "w") as f:
        f.write("".join(lines))
    return len(results)

def write_offline_context():
    """写入离线状态"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# Semantic Memory - 相关历史上下文\n\n> 自动更新于 {now}\n\n"]
    lines.append("**Ubuntu 节点状态**: 离线（Semantic Cache 不可用）\n\n")
    lines.append("## 相关历史上下文\n\n")
    lines.append("（Ubuntu 节点离线，无法获取实时上下文）\n")
    with open(CONTEXT_FILE, "w") as f:
        f.write("".join(lines))

if __name__ == "__main__":
    print(f"[Smart Context Hook] {datetime.now().strftime('%H:%M:%S')} - 检查 Ubuntu 节点...", file=sys.stderr)

    if not check_ubuntu_online():
        print("[Hook] Ubuntu 离线，跳过上下文获取", file=sys.stderr)
        write_offline_context()
        sys.exit(0)

    print("[Hook] Ubuntu 在线，检查 Semantic Cache...", file=sys.stderr)

    if not check_semantic_cache_online():
        print("[Hook] Semantic Cache 不可用，跳过", file=sys.stderr)
        write_offline_context()
        sys.exit(0)

    print("[Hook] 获取语义上下文...", file=sys.stderr)
    results = fetch_context()
    count = write_context(results)
    print(f"[Hook] 完成，写入 {count} 条记录到 {CONTEXT_FILE}", file=sys.stderr)
