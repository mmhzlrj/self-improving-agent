#!/usr/bin/env python3
"""
TaskBroadcast: Multi-agent 任务状态共享模块
基于 Semantic Cache 实现任务结果广播与订阅

功能：
1. 发布：将任务结果写入 Semantic Cache (namespace=task_results)
2. 订阅：从 Semantic Cache 读取已完成任务列表
3. 去重：通过 task_id 避免重复执行
4. TTL：结果保留 7 天（通过时间戳过滤）

Usage:
    python task_broadcast.py --publish <task_id> <status> <outcome>
    python task_broadcast.py --subscribe [--since-days 7]
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Semantic Cache 配置
SEMANTIC_CACHE_URL = "http://192.168.1.18:5050"  # Ubuntu server
LOCAL_FALLBACK_URL = "http://127.0.0.1:5050"     # 本地回退

# 命名空间
NAMESPACE_TASK_RESULTS = "task_results"
NAMESPACE_TASKS = "tasks"

# TTL 配置
DEFAULT_TTL_DAYS = 7


def get_semantic_cache_url():
    """获取可用的 Semantic Cache URL"""
    # 尝试 Ubuntu server
    try:
        import urllib.request
        req = urllib.request.Request(SEMANTIC_CACHE_URL + "/health", 
                                     method='GET')
        urllib.request.urlopen(req, timeout=2)
        return SEMANTIC_CACHE_URL
    except Exception:
        pass
    
    # 回退到本地
    try:
        import urllib.request
        req = urllib.request.Request(LOCAL_FALLBACK_URL + "/health",
                                     method='GET')
        urllib.request.urlopen(req, timeout=2)
        return LOCAL_FALLBACK_URL
    except Exception:
        pass
    
    return None


# 本地存储路径（mock 模式）
LOCAL_STORAGE_DIR = Path.home() / ".semantic_cache" / "task_broadcast"


def _ensure_local_storage():
    """确保本地存储目录存在"""
    LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _get_local_file(namespace: str) -> Path:
    """获取 namespace 对应的本地文件"""
    return LOCAL_STORAGE_DIR / f"{namespace}.jsonl"


def query_semantic_cache(query: str, namespace: str, top_k: int = 10) -> list:
    """查询 Semantic Cache（远程或本地模拟）"""
    url = get_semantic_cache_url()
    
    if url:
        try:
            import urllib.request
            import urllib.error
            
            data = json.dumps({
                "query": query,
                "top_k": top_k,
                "namespace": namespace
            }).encode('utf-8')
            
            req = urllib.request.Request(
                url + "/query",
                data=data,
                headers={"Content-Type": "application/json"},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("results", [])
        except Exception as e:
            print(f"[Warning] Remote query failed: {e}, using local fallback", file=sys.stderr)
    
    # 本地模拟：简单文本匹配
    _ensure_local_storage()
    local_file = _get_local_file(namespace)
    
    if not local_file.exists():
        return []
    
    results = []
    query_lower = query.lower()
    
    with open(local_file, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                text = entry.get("text", "").lower()
                # 简单关键词匹配
                if any(q in text for q in query_lower.split()):
                    results.append(entry)
                    if len(results) >= top_k:
                        break
            except json.JSONDecodeError:
                continue
    
    return results


def add_to_semantic_cache(text: str, metadata: dict, namespace: str) -> bool:
    """添加内容到 Semantic Cache（远程或本地模拟）"""
    url = get_semantic_cache_url()
    
    if url:
        try:
            import urllib.request
            
            # 构建包含元数据的文本
            full_text = f"{text}\n\n<!-- METADATA: {json.dumps(metadata, ensure_ascii=False)} -->"
            
            data = json.dumps({
                "text": full_text,
                "metadata": metadata,
                "namespace": namespace
            }).encode('utf-8')
            
            req = urllib.request.Request(
                url + "/add",
                data=data,
                headers={"Content-Type": "application/json"},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("success", False)
        except Exception as e:
            print(f"[Warning] Remote add failed: {e}, using local fallback", file=sys.stderr)
    
    # 本地模拟：写入 JSONL 文件
    _ensure_local_storage()
    local_file = _get_local_file(namespace)
    
    entry = {
        "text": text,
        "metadata": metadata,
        "timestamp": datetime.now(timezone(timedelta(hours=8))).isoformat()
    }
    
    with open(local_file, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    return True


def publish_task(task_id: str, status: str, outcome: str, details: dict = None) -> bool:
    """
    发布任务结果到 Semantic Cache
    
    Args:
        task_id: 任务唯一标识
        status: 状态 (completed/failed/in_progress)
        outcome: 任务结果描述
        details: 额外详情
    
    Returns:
        bool: 是否成功发布
    """
    # 构建任务结果文本
    text = f"Task {task_id}: {status} - {outcome}"
    
    # 合并元数据
    metadata = {
        "task_id": task_id,
        "status": status,
        "outcome": outcome,
        "timestamp": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "ttl_days": DEFAULT_TTL_DAYS
    }
    
    if details:
        metadata.update(details)
    
    # 发布到 task_results namespace
    success = add_to_semantic_cache(text, metadata, NAMESPACE_TASK_RESULTS)
    
    if success:
        print(f"[TaskBroadcast] Published: {task_id} -> {status}")
    else:
        print(f"[TaskBroadcast] Failed to publish: {task_id}")
    
    return success


def subscribe_tasks(since_days: int = 7) -> list:
    """
    订阅已完成的任务列表
    
    Args:
        since_days: 只返回最近 N 天的任务
    
    Returns:
        list: 已完成任务列表
    """
    # 计算时间窗口
    cutoff_time = datetime.now(timezone(timedelta(hours=8))) - timedelta(days=since_days)
    
    # 查询 task_results namespace
    results = query_semantic_cache(
        query="task status completed failed",
        namespace=NAMESPACE_TASK_RESULTS,
        top_k=50
    )
    
    tasks = []
    for r in results:
        metadata = r.get("metadata", {})
        task_time = metadata.get("timestamp", "")
        
        # 时间过滤
        if task_time:
            try:
                task_dt = datetime.fromisoformat(task_time.replace('Z', '+00:00'))
                if task_dt.replace(tzinfo=timezone(timedelta(hours=8))) < cutoff_time:
                    continue
            except Exception:
                pass
        
        tasks.append({
            "task_id": metadata.get("task_id", ""),
            "status": metadata.get("status", ""),
            "outcome": metadata.get("outcome", ""),
            "timestamp": task_time
        })
    
    return tasks


def check_task_exists(task_id: str) -> bool:
    """检查任务是否已存在（已完成/失败）"""
    tasks = subscribe_tasks(since_days=DEFAULT_TTL_DAYS)
    return any(t["task_id"] == task_id for t in tasks)


def main():
    parser = argparse.ArgumentParser(description="TaskBroadcast - Multi-agent 任务状态共享")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # publish 子命令
    publish_parser = subparsers.add_parser("publish", help="发布任务结果")
    publish_parser.add_argument("task_id", help="任务 ID")
    publish_parser.add_argument("status", help="状态 (completed/failed/in_progress)")
    publish_parser.add_argument("outcome", help="任务结果")
    publish_parser.add_argument("--details", type=str, default="{}", 
                               help="额外详情 (JSON 格式)")
    
    # subscribe 子命令
    subscribe_parser = subparsers.add_parser("subscribe", help="订阅已完成任务")
    subscribe_parser.add_argument("--since-days", type=int, default=7,
                                 help="只返回最近 N 天的任务 (默认 7)")
    
    # check 子命令
    check_parser = subparsers.add_parser("check", help="检查任务是否存在")
    check_parser.add_argument("task_id", help="任务 ID")
    
    args = parser.parse_args()
    
    if args.command == "publish":
        details = json.loads(args.details) if args.details != "{}" else {}
        success = publish_task(args.task_id, args.status, args.outcome, details)
        sys.exit(0 if success else 1)
    
    elif args.command == "subscribe":
        tasks = subscribe_tasks(since_days=args.since_days)
        print(f"[TaskBroadcast] Found {len(tasks)} tasks in last {args.since_days} days:")
        for t in tasks:
            print(f"  - {t['task_id']}: {t['status']} ({t['outcome'][:50]})")
        return tasks
    
    elif args.command == "check":
        exists = check_task_exists(args.task_id)
        print(f"[TaskBroadcast] Task {args.task_id}: {'exists' if exists else 'not found'}")
        sys.exit(0 if exists else 1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()