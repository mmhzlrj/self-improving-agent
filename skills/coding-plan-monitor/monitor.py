#!/usr/bin/env python3
"""
MiniMax Coding Plan 额度监控脚本
- 检查当前用量
- 根据阈值控制任务节奏
"""

import json
import sys
import subprocess
from datetime import datetime, timezone, timedelta
import requests

API_KEY = "sk-cp-wEiHHliuPGtLE9x63yViVXozeZu0UxOicm7MIuRpzBs-b7pkz78gr61YYCZ46yNjauf6eFh8LkBFnP4fhvBzmxFWSjAbWZo5S7ag7d5vDtijN9akDB6NNA4"
API_URL = "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains"

# 阈值配置
THRESHOLD_WARNING = 90   # 90% - 减缓任务
THRESHOLD_CRITICAL = 95  # 95% - 暂停任务

def get_usage():
    """获取当前使用量"""
    try:
        response = requests.get(API_URL, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=10)
        data = response.json()
        
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz)
        
        for m in data.get('model_remains', []):
            if m['model_name'] == 'MiniMax-M2.5':
                start_ts = m['start_time'] / 1000
                end_ts = m['end_time'] / 1000
                remaining = m['current_interval_usage_count']
                total = m.get('current_interval_total_count', 0)
                used = total - remaining
                
                pct_used = (used / total * 100) if total > 0 else 0.0
                pct_remaining = (remaining / total * 100) if total > 0 else 0.0
                
                start_dt = datetime.fromtimestamp(start_ts, tz)
                end_dt = datetime.fromtimestamp(end_ts, tz)
                remaining_seconds = (end_dt - now).total_seconds()
                hours = int(remaining_seconds // 3600)
                minutes = int((remaining_seconds % 3600) // 60)
                
                return {
                    'model': m['model_name'],
                    'total': total,
                    'remaining': remaining,
                    'used': used,
                    'pct_used': pct_used,
                    'pct_remaining': pct_remaining,
                    'cycle_start': start_dt.strftime("%H:%M"),
                    'cycle_end': end_dt.strftime("%H:%M"),
                    'reset_in': f"{hours}小时{minutes}分钟"
                }
        return None
    except Exception as e:
        print(f"❌ 获取用量失败: {e}")
        return None

def check_status():
    """检查状态并返回建议"""
    usage = get_usage()
    if not usage:
        return "error"
    
    print(f"\n📊 MiniMax Coding Plan 状态")
    print(f"模型: {usage['model']}")
    print(f"周期: {usage['cycle_start']} - {usage['cycle_end']}")
    print(f"已用: {usage['used']} ({usage['pct_used']:.1f}%)")
    print(f"剩余: {usage['remaining']} ({usage['pct_remaining']:.1f}%)")
    print(f"重置: {usage['reset_in']}后")
    print()
    
    # 根据阈值返回状态
    if usage['pct_used'] >= THRESHOLD_CRITICAL:
        print("🔴 状态: 严重超额 - 暂停任务")
        print(f"建议: 记录当前进度，等待重置")
        return "critical"
    elif usage['pct_used'] >= THRESHOLD_WARNING:
        print("⚠️ 状态: 额度紧张 - 减缓任务")
        print("建议: 减少并发，降低请求频率")
        return "warning"
    else:
        print("✅ 状态: 正常 - 可以继续任务")
        return "ok"

def should_continue():
    """判断是否应该继续任务"""
    usage = get_usage()
    if not usage:
        return True  # 如果获取失败，默认继续
    
    return usage['pct_used'] < THRESHOLD_CRITICAL

def get_remaining_seconds():
    """获取距离重置的剩余秒数"""
    usage = get_usage()
    if not usage:
        return 0
    
    # 从周期结束时间计算
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    
    # 简化：假设周期结束就是重置时间
    # 实际应该根据当前时间计算当前周期
    for m in [usage]:
        # 计算当前周期
        hour = now.hour
        if hour >= 20:
            # 20:00-00:00 周期
            end_hour = 24
        elif hour >= 15:
            # 15:00-20:00 周期
            end_hour = 20
        elif hour >= 10:
            # 10:00-15:00 周期
            end_hour = 15
        elif hour >= 5:
            # 05:00-10:00 周期
            end_hour = 10
        else:
            # 00:00-05:00 周期
            end_hour = 5
        
        remaining = (end_hour - hour) * 3600
        return max(0, remaining)
    
    return 0

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 monitor.py check      # 检查状态")
        print("  python3 monitor.py status    # 返回状态码")
        print("  python3 monitor.py should    # 判断是否继续")
        print("  python3 monitor.py reset     # 获取重置倒计时")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check":
        check_status()
    elif command == "status":
        status = check_status()
        sys.exit(0 if status == "ok" else 1)
    elif command == "should":
        if should_continue():
            print("ok")
            sys.exit(0)
        else:
            print(f"waiting_reset:{get_remaining_seconds()}")
            sys.exit(1)
    elif command == "reset":
        seconds = get_remaining_seconds()
        print(f"重置倒计时: {seconds // 3600}小时{(seconds % 3600) // 60}分钟")
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
