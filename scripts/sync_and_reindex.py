#!/usr/bin/env python3
"""
增量同步 MacBook sessions 到 Ubuntu 并触发重建索引
每 5 分钟由 cron 调度
"""
import os
import json
import subprocess
import urllib.request
import shutil
from datetime import datetime

UBUNTU_HOST = "jet@192.168.1.18"
UBUNTU_SESSIONS = "/home/jet/.openclaw/agents/main/sessions"
UBUNTU_SEMANTIC = "/home/jet/semantic_cache"
MACBOOK_SESSIONS = os.path.expanduser("~/.openclaw/agents/main/sessions")
STATE_FILE = os.path.expanduser("~/.openclaw/workspace/.session_sync_state.json")

def get_last_sync():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            d = json.load(f)
        return d.get("last_sync", ""), d.get("last_file", "")
    return "", ""

def save_state(last_sync, last_file):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_sync": last_sync, "last_file": last_file, "updated": datetime.now().isoformat()}, f)

def sync_sessions():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 同步 sessions 到 Ubuntu...")

    # rsync 增量同步
    result = subprocess.run([
        "rsync", "-avz", "--ignore-existing",
        f"{MACBOOK_SESSIONS}/", f"{UBUNTU_HOST}:{UBUNTU_SESSIONS}/"
    ], capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        print(f"rsync 失败: {result.stderr}")
        return

    # 统计
    count = result.stdout.count(".jsonl")
    print(f"同步完成: {count} 个新文件")

    # 触发 Ubuntu 重建索引
    try:
        # 先删除旧索引
        subprocess.run([
            "ssh", UBUNTU_HOST,
            f"rm -f {UBUNTU_SEMANTIC}/index.faiss {UBUNTU_SEMANTIC}/texts.json"
        ], timeout=10)

        # 触发 server 重启（会自动重建索引）
        subprocess.run([
            "ssh", UBUNTU_HOST,
            "pkill -f semantic_cache; sleep 1; "
            f"cd {UBUNTU_SEMANTIC} && "
            "HF_HUB_OFFLINE=1 HF_ENDPOINT=https://hf-mirror.com "
            "nohup python3 server.py > semantic_cache.log 2>&1 &"
        ], timeout=15)
        print("索引重建已触发")
    except Exception as e:
        print(f"触发索引重建失败: {e}")

    save_state(datetime.now().isoformat(), "")

if __name__ == "__main__":
    sync_sessions()
