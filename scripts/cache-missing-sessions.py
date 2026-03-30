#!/usr/bin/env python3
"""
检测并缓存最近活跃但尚未写入 .jsonl 的 session。

逻辑：
1. 读取 sessions.json，找出 updatedAt 在 24h 内且无 .jsonl 的 session
2. 若无，扩展到 48h
3. 若还无，扩展到 72h
4. 对每个缺失的 session，尝试用 openclaw session export 导出内容
5. 写入 .jsonl 并同步到 Ubuntu

Usage:
    python3 ~/.openclaw/workspace/scripts/cache-missing-sessions.py [--dry-run]
"""

import json
import os
import sys
import glob
import subprocess
import time
import urllib.request
import urllib.error

SESSIONS_JSON = os.path.expanduser("~/.openclaw/agents/main/sessions/sessions.json")
SESSIONS_DIR = os.path.expanduser("~/.openclaw/agents/main/sessions")
UBUNTU_HOST = "jet@192.168.1.18"
UBUNTU_SESSIONS_DIR = "~/.openclaw/agents/main/sessions"
UBUNTU_SC_URL = "http://127.0.0.1:5050"
OPENCLAW_BIN = "/usr/local/bin/openclaw"  # 实际路径由 which 确定

DRY_RUN = "--dry-run" in sys.argv

def get_openclaw_bin():
    result = subprocess.run(["which", "openclaw"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    # 尝试其他路径
    for path in ["/usr/local/bin/openclaw", "/opt/homebrew/bin/openclaw",
                 os.path.expanduser("~/.nvm/versions/node/v22.22.0/bin/openclaw")]:
        if os.path.exists(path):
            return path
    return "openclaw"  # fallback

def load_sessions():
    with open(SESSIONS_JSON) as f:
        return json.load(f)

def session_age_ms(val):
    """返回 session 多久未更新（毫秒）"""
    updated = val.get("updatedAt", 0)
    if not updated:
        return float("inf")
    return time.time() * 1000 - updated

def session_age_hours(val):
    return session_age_ms(val) / 3600000

def has_jsonl(val):
    """检查 session 是否有对应的 .jsonl 文件"""
    # 直接路径
    sf = val.get("sessionFile")
    if sf and os.path.exists(sf):
        return sf
    
    # 通过 sessionId 猜测路径
    sid = val.get("sessionId", "")
    if sid:
        pattern = f"{SESSIONS_DIR}/{sid}*.jsonl"
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    
    return None

def find_missing_sessions(data, max_hours, min_hours=0):
    """找出更新于 min_hours 到 max_hours 之间、且无 .jsonl 的 session"""
    missing = []
    for key, val in data.items():
        if not isinstance(val, dict):
            continue
        age_h = session_age_hours(val)
        if min_hours <= age_h < max_hours:
            existing = has_jsonl(val)
            if not existing:
                missing.append({
                    "key": key,
                    "sessionId": val.get("sessionId", ""),
                    "sessionFile": val.get("sessionFile", ""),
                    "origin": val.get("origin", {}),
                    "ageHours": round(age_h, 1),
                    "updatedAt": val.get("updatedAt", 0)
                })
    return missing

def export_session(session_key):
    """通过 openclaw session 命令导出 session 内容"""
    bin_path = get_openclaw_bin()
    try:
        # 尝试获取 session 历史
        result = subprocess.run(
            [bin_path, "session", "export", session_key],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout
    except Exception as e:
        pass
    
    # 尝试 sessions history 子命令
    try:
        result = subprocess.run(
            [bin_path, "sessions", "history", session_key],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout
    except Exception:
        pass
    
    return None

def write_session_jsonl(session_id, content_lines, origin_provider):
    """将 session 内容写入 .jsonl 文件"""
    out_path = os.path.join(SESSIONS_DIR, f"{session_id}.jsonl")
    if os.path.exists(out_path):
        print(f"  ⏭️  已存在: {out_path}")
        return out_path, False
    
    with open(out_path, "w") as f:
        for line in content_lines:
            f.write(line + "\n")
    
    print(f"  ✅ 写入: {out_path} ({len(content_lines)} 行)")
    return out_path, True

def sync_to_ubuntu(local_path):
    """同步 .jsonl 到 Ubuntu"""
    try:
        result = subprocess.run(
            ["rsync", "-avz", "--ignore-existing", local_path,
             f"{UBUNTU_HOST}:{UBUNTU_SESSIONS_DIR}/"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"  📡 已同步到 Ubuntu")
            return True
        else:
            print(f"  ❌ rsync 失败: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"  ❌ rsync 异常: {e}")
        return False

def trigger_reindex():
    """触发 Ubuntu Semantic Cache 增量索引"""
    try:
        req = urllib.request.Request(
            f"{UBUNTU_SC_URL}/reindex",
            data=b"",
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            print(f"  🔄 索引更新: {result.get('new_entries', 0)} 条")
            return True
    except Exception as e:
        print(f"  ⚠️  索引触发失败（正常，如果节点离线）: {e}")
        return False

def check_ubuntu_online():
    """检查 Ubuntu 是否在线"""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", "192.168.1.18"],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

def main():
    print("=" * 60)
    print("Session 缓存检测脚本")
    print("=" * 60)
    
    data = load_sessions()
    total_sessions = len([k for k, v in data.items() if isinstance(v, dict)])
    print(f"sessions.json 共 {total_sessions} 个 session 条目\n")
    
    # 阶段1: 24h 内
    missing = find_missing_sessions(data, 24)
    if missing:
        print(f"🕐 24h 内缺失: {len(missing)} 个")
    else:
        print("✅ 24h 内所有 session 均已缓存")
    
    # 阶段2: 24-48h
    if not missing:
        missing = find_missing_sessions(data, 48, 24)
        if missing:
            print(f"🕐 24-48h 内缺失: {len(missing)} 个")
        else:
            print("✅ 24-48h 内所有 session 均已缓存")
    
    # 阶段3: 48-72h
    if not missing:
        missing = find_missing_sessions(data, 72, 48)
        if missing:
            print(f"🕐 48-72h 内缺失: {len(missing)} 个")
        else:
            print("✅ 48-72h 内所有 session 均已缓存")
    
    if not missing:
        print("\n🎉 没有需要缓存的 session！")
        return
    
    print(f"\n需要处理的 session ({len(missing)} 个):")
    for s in missing:
        origin = s["origin"]
        provider = origin.get("provider", "?") if isinstance(origin, dict) else "?"
        print(f"  [{s['ageHours']}h ago] {provider}: {s['key'][:60]}")
    
    if DRY_RUN:
        print("\n[DRY RUN] 跳过实际缓存操作")
        return
    
    print("\n开始缓存...")
    cached_count = 0
    synced_count = 0
    
    for s in missing:
        session_id = s["sessionId"]
        if not session_id:
            print(f"\n⚠️  无 sessionId，跳过: {s['key'][:50]}")
            continue
        
        print(f"\n处理: {session_id} ({s['ageHours']}h ago)")
        
        # 尝试导出 session 内容
        content = export_session(s["key"])
        if content:
            lines = [l.strip() for l in content.strip().split("\n") if l.strip()]
            path, ok = write_session_jsonl(session_id, lines, s["origin"])
            if ok:
                cached_count += 1
                # 同步到 Ubuntu
                if sync_to_ubuntu(path):
                    synced_count += 1
        else:
            print(f"  ⚠️  无法导出 session 内容（可能是历史 session，Gateway 已不含此数据）")
            # 尝试通过 openclaw sessions history 命令
            try:
                bin_path = get_openclaw_bin()
                result = subprocess.run(
                    [bin_path, "sessions", "history", "--session", session_id],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0 and result.stdout.strip():
                    lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
                    path, ok = write_session_jsonl(session_id, lines, s["origin"])
                    if ok:
                        cached_count += 1
                        if sync_to_ubuntu(path):
                            synced_count += 1
            except Exception as e:
                print(f"  备用方法也失败: {e}")
    
    print(f"\n完成: 缓存 {cached_count} 个 session，同步 {synced_count} 个到 Ubuntu")
    
    if synced_count > 0:
        print("触发 Semantic Cache 增量索引...")
        trigger_reindex()

if __name__ == "__main__":
    main()
