#!/usr/bin/env python3
"""检测 OpenClaw alsoAllow 配置变更并记录到 changelog"""
import subprocess, json, re
from pathlib import Path
from datetime import datetime

CONFIG_PATH = Path.home() / ".openclaw/openclaw.json"
LOG_FILE = Path.home() / ".openclaw/config-change-log.jsonl"

def get_latest_change():
    try:
        diff = subprocess.run(
            ["git", "-C", str(CONFIG_PATH.parent), "diff", "HEAD~1", "--", CONFIG_PATH.name],
            capture_output=True, text=True, timeout=5
        ).stdout
    except:
        return None
    
    if not any(k in diff for k in ["alsoAllow", "kimi_", "doubao_", "glm_", "qwen_"]):
        return None
    
    try:
        commit = subprocess.run(
            ["git", "-C", str(CONFIG_PATH.parent), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except:
        commit = "unknown"
    
    return {
        "timestamp": datetime.now().isoformat(),
        "commit": commit,
        "type": "alsoAllow",
        "diff_lines": diff.count("\n")
    }

if __name__ == "__main__":
    entry = get_latest_change()
    if entry:
        logs = []
        if LOG_FILE.exists():
            logs = [json.loads(l) for l in open(LOG_FILE)]
        logs.insert(0, entry)
        LOG_FILE.write_text("\n".join(json.dumps(l, ensure_ascii=False) for l in logs))
        print(f"✅ 记录 alsoAllow 变更: {entry['commit']}")
    else:
        print("ℹ️  无 alsoAllow 变更")
