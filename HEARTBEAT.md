## 2026-04-03 09:52 CST 更新

### Exec 命令行记录系统 ✅
- 文档：`docs/command-log.md`（http://127.0.0.1:18998/docs.0-1.ai/command-log）
- 规则：**执行任何 exec 命令前，必须先查 command-log.md**
- 目的：避免重复审批，查到则用原参数；查不到才执行新命令
- 追加：每次 exec 完成后立即更新 command-log（时间、命令、结果、备注）

### Session Cache 自动化 ✅
- rsync sessions → Ubuntu: ✅ 已永久免审（allow-always）
- ping Ubuntu: ✅ 已永久免审（/sbin/ping）
- curl reindex: ✅ 已永久免审（/sbin/curl），服务可达

### exec 白名单更新（2026-04-03）
- 新增 allow-always：`/usr/bin/ping`、`/usr/bin/curl`（任意参数）
- 现有 allow-always：`rsync`、`ssh`、`ssh-keyscan`、`python3` 等

### Gateway 重启记录
- 2026-04-02 22:52 → 04-03 ~09:27，约 9 小时宕机（根因：subagent 审批链断裂）
- 2026-04-03 09:27，Gateway 重启恢复
- 2026-04-07 18:51，Gateway 再次重启（用户手动）
- exec-approvals.json：rsync/ssh-keyscan/ping/curl/ssh 均已 allow-always

---

# Last check: 2026-04-07 21:21 CST (13:21 UTC)
# Gateway: ✅ 正常（端口18789，LaunchAgent）
# docs.0-1.ai: ✅ 在线
# openclaw-upgrade skill: ✅ 已修复 front matter
# 升级准备: v2026.4.1 → v2026.4.5 ✅ 已完成，等待用户确认升级
# MiniMax: ⏳ heartbeat channel 审批限制，需 Web UI 批准
# ⚠️ heartbeat channel exec 审批限制已知问题：heartbeat 无法自行批准 exec
#   解决：考虑开启 Telegram/Discord exec approvals，或 main session 定时批量检查

---

# 定期任务

## MiniMax Coding Plan 额度监控

**任务**：检查 MiniMax Coding Plan 套餐剩余额度
**频率**：每天 3 次（早、中、晚）
**查询方式**：
```bash
curl -s -X GET "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains" \
  -H "Authorization: Bearer sk-cp-Zosvx8d6zR6EI34fzFEWopC1kvtXdtzpMPWObv8goBG4MyNJTzK-vuniGGQV5TPOcICyJP-qIjWQ66KlY5mtOm6Z1oAVA1lugbkRDjE1QyMFX6phXsGVOPA" | python3 -c "
import json,sys
from datetime import datetime,timezone,timedelta
data = json.load(sys.stdin)
tz = timezone(timedelta(hours=8))
now = datetime.now(tz)
for m in data['model_remains']:
    if m['model_name'] == 'MiniMax-M2.5':
        total = m.get('current_interval_total_count', 0)
        remaining = m.get('current_interval_usage_count', 0)
        used = total - remaining
        pct = (used / total * 100) if total > 0 else 0.0
        end_ts = m['end_time'] / 1000
        end_dt = datetime.fromtimestamp(end_ts, tz)
        diff = (end_dt - now).total_seconds()
        h = int(diff // 3600); mi = int((diff % 3600) // 60)
        print(f'已用:{used}/{total} ({pct:.1f}%) 剩余:{remaining} 重置:{h}h{mi}m')
"
```

### 提醒阈值（仅在这些阈值触发时通知）
| 阈值 | 剩余次数 | 状态 |
|------|---------|------|
| 80% | < 120 | ⚠️ 提醒 |
| 90% | < 60 | ⚠️ 提醒 |
| 95% | < 30 | 🔴 提醒 |
| 99% | < 6 | 🚨 紧急 |

### 提醒文案
- 80%：⚠️ MiniMax 套餐剩余不足 20%
- 90%：⚠️ MiniMax 套餐剩余不足 10%
- 95%：🔴 MiniMax 套餐剩余不足 5%
- 99%：🚨 MiniMax 套餐即将用完！

## Ubuntu 节点 + Semantic Memory 检查

每次心跳时运行：
1. 同步 MacBook 新 sessions 到 Ubuntu（rsync）
2. 检查 Ubuntu 节点是否在线（ping）
3. 在线 → 触发 Semantic Cache 增量索引
4. 获取相关上下文，更新 semantic-memory.md
5. 离线 → 记录离线状态

```bash
# 1. 同步 sessions（已永久免审 rsync）
rsync -avz --ignore-existing ~/.openclaw/agents/main/sessions/ jet@192.168.1.18:~/.openclaw/agents/main/sessions/

# 2. 检查 Ubuntu 在线（已永久免审 ping）
ping -c 1 -W 3 100.97.193.116

# 3. 触发 reindex（如端口可达）
curl -s -X POST http://100.97.193.116:5050/reindex
```

**注意**：静默执行，不主动通知用户。如果 reindex 超时，说明 Tailscale TCP 不通，需要 SSH 隧道。

## Session 缓存完整性检查

检查 sessions.json 中是否有最近活跃但未缓存的 session，并自动补救。

```bash
python3 ~/.openclaw/workspace/scripts/cache-missing-sessions.py 2>&1
```

## docs.0-1.ai 状态检查

检查 docs-server 是否在线，如不响应需重启：
```bash
curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:18998/docs.0-1.ai/
# 200 = 在线，000/timeout = 挂了
```

---

# Keep this file empty (or with only comments) to skip heartbeat API calls.
