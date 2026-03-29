# HEARTBEAT.md

# 定期任务

## 不定时任务

### Jetson Thor Nano 爆料监控
- **任务**：定期搜索 Jetson Thor Nano 最新消息
- **频率**：每月一次
- **搜索关键词**：Jetson Thor Nano release, specs, price, rumor
- **发现新消息时**：立即通过飞书通知用户

#### 2026年3月8日 监控结果
- Jetson AGX Thor 已发布（$3,499，2025年9月发货，Blackwell 架构）
- Jetson Thor（非Nano）已发布：$3,499，Blackwell 架构，2070 TFLOPS，2025年9月发货
- Jetson Thor Nano：截至 2026年3月21日，仍无明确产品发布消息
- 社区讨论的 "Jetson Nano 2026年底停产继任者" 名称未确认
- 继续监控

#### 2026年3月22日 监控结果
- Jetson AGX Thor 已正式上市，$3,499，128GB，2070 TFLOPS，Blackwell 架构
- Jetson Thor Nano：**仍然不存在**，NVIDIA 目前 Nano 级别主力仍是 Jetson Orin Nano Super（$249）
- Jetson AGX Thor 应用案例：卡特彼勒Cat AI助手（语音+挖掘机）、GR00T机器人（UIUC黑客松冠军）
- 结论：Thor Nano 短期内无望，继续监控即可，无需频繁检查

---

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Last check: 2026-03-29 19:59 CST (11:59 UTC)
# MiniMax 套餐状态：周期 20:00-00:00，已用 513/600 (85.5%)，剩余 87
# 阈值状态：⚠️ 85% 已触发
# Wan 2.1 T2V 1.3B 下载中：2.1GB/~10GB（后台继续）
# 注意：umt5-xxl text encoder 8GB，6GB 显存可能跑不动，需评估

## MiniMax Coding Plan 额度监控

### 任务信息
- **任务**：检查 MiniMax Coding Plan 套餐剩余额度
- **频率**：每天 3 次（早、中、晚）
- **查询方式**：curl 直接查询，不用 API

### 套餐信息
- 总量：600 次 / 5小时（最后一个周期4小时）
- 周期：20:00-00:00 (UTC+8)
- 重置：每5小时滚动

### ⚠️ 提醒阈值（仅在这些阈值触发时通知）
| 阈值 | 剩余次数 | 状态 |
|------|---------|------|
| 80% | < 120 | ⚠️ 提醒 |
| 90% | < 60 | ⚠️ 提醒 |
| 95% | < 30 | 🔴 提醒 |
| 99% | < 6 | 🚨 紧急 |

### 提醒时不显示完整信息，只显示：
- 当前已用比例
- 距离重置时间
- 剩余次数
```bash
curl -s -X GET "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains" \
  -H "Authorization: Bearer sk-cp-Zosvx8d6zR6EI34fzFEWopC1kvtXdtzpMPWObv8goBG4MyNJTzK-vuniGGQV5TPOcICyJP-qIjWQ66KlY5mtOm6Z1oAVA1lugbkRDjE1QyMFX6phXsGVOPA" | python3 -c "
import json, sys
from datetime import datetime, timezone, timedelta

data = json.load(sys.stdin)
tz = timezone(timedelta(hours=8))
now = datetime.now(tz)

for m in data['model_remains']:
    start_ts = m['start_time'] / 1000
    end_ts = m['end_time'] / 1000
    remaining = m['current_interval_usage_count']
    total = m['current_interval_total_count']
    used = total - remaining
    
    start_dt = datetime.fromtimestamp(start_ts, tz)
    end_dt = datetime.fromtimestamp(end_ts, tz)
    remaining_seconds = (end_dt - now).total_seconds()
    hours = int(remaining_seconds // 3600)
    minutes = int((remaining_seconds % 3600) // 60)
    pct_used = (used / total) * 100
    
    print(f'模型: {m[\"model_name\"]}')
    print(f'周期: {start_dt.strftime(\"%H:%M\")} - {end_dt.strftime(\"%H:%M\")}')
    print(f'剩余: {remaining} ({100-pct_used:.1f}%)')
    print(f'已用: {used} ({pct_used:.1f}%)')
    print(f'重置: {hours}小时{minutes}分钟后')
"
```

### 提醒文案
- 80%：⚠️ MiniMax 套餐剩余不足 20%
- 90%：⚠️ MiniMax 套餐剩余不足 10%
- 95%：🔴 MiniMax 套餐剩余不足 5%
- 99%：🚨 MiniMax 套餐即将用完！

## Ubuntu 节点 + Semantic Memory 检查

每次心跳时运行：
1. 同步 MacBook 新 sessions 到 Ubuntu（rsync）
2. 检查 Ubuntu 节点是否在线
3. 在线 → 重启 Semantic Cache 服务器（重新加载所有 sessions）
4. 获取相关上下文，更新 semantic-memory.md
5. 离线 → 记录离线状态

```bash
# 1. 同步 sessions（静默）
rsync -avz --ignore-existing ~/.openclaw/agents/main/sessions/ jet@192.168.1.18:~/.openclaw/agents/main/sessions/ 2>/dev/null

# 2. 检查 Ubuntu 在线
ping -c 1 -W 2 192.168.1.18 > /dev/null 2>&1 || exit

# 3. 同步后触发增量索引（不重启服务器）
curl -s -X POST --connect-timeout 5 "http://192.168.1.18:5050/reindex" | python3 -c "
import json,sys
try:
    d = json.load(sys.stdin)
    print(f\"索引更新: {d.get('new_entries',0)} 条, 总计 {d.get('total',0)} 条\")
except: print('索引更新失败')
" 2>/dev/null

# 4. 获取上下文
python3 ~/.openclaw/workspace/scripts/smart_context_hook.py
```

**注意**：静默执行，不主动通知用户。
