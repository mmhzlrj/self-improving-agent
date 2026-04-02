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

# Last check: 2026-03-31 00:03 CST (16:03 UTC)

## 2026-03-31 凌晨状态

### LeWM Vision训练 ✅ 调参成功
- tworoom: loss=0.004 ✅
- pusht图像(tuned): loss从0.95降至0.119（epoch 17 best），早停机制正常
- Checkpoint: ~/.stable-wm/lewm_vision_best.pt
- 参数: lr=3e-6, weight_decay=0.01, dropout=0.2, grad_clip=0.5

### Ubuntu节点
- IP: 192.168.1.18
- pusht数据集: ~/.stable-wm/pusht_full/ (7.7GB, 206 episodes)
- LeWM代码+数据: ~/.stable-wm/

### A序列任务: 7/7 完成 ✅
# MiniMax: ✅ 6.7%已用, 560次剩余, 4h46m后重置
# Ubuntu: ❌ 离线
# Night Build: Orchestrator运行中(A序列9个任务)
# rsync: 已同步，等待Ubuntu上线后自动索引
# Ubuntu: ❌ 离线
# Ebbinghaus InterestTracker: ✅ 已实现，6/6测试通过，详见 reports/A-Ebbinghaus-InterestTracker-实现报告.md
# 缓存检查: 0个新session同步完成 (05:37 UTC)
# MiniMax: 69.8%已用, 剩余181次, 1h21m后重置 → ✅ 正常
# Ubuntu: ❌ 离线
# 2个subagent调研中：影响力平台(d88d3af3) + 关键词权重衰减(2b3d91a3)
# MiniMax 套餐状态：周期 10:00-15:00，已用 50.8%，剩余 295次，2h25m后重置
# 阈值状态：✅ 正常（远低于80%阈值）
# Ubuntu 节点：❌ 离线（12:33 CST）— Semantic Cache 不可用
# Semantic Cache：上次已知在线（11:15 CST），7620条索引，rsync正常（Ubuntu离线前）
# MCP Server：发现重复进程（doubao/kimi/glm），需要Gateway重启解决
# TurboQuant 调研 4/4 份报告全部完成 ✅
# LeCun论文调研报告已保存：memory/2026-03-30-LeCun-Papers-0-1-Roadmap.md
# 飞书指令漏接问题：已完成，详见 memory/2026-03-30-Channel-Messages-Feishu-QQ.md
# Session 缓存检测：24h内全部缓存完成，1个44h前cron session缺失（已知，无法恢复）
# 新周期（10:00-15:00）刚进入，额度充足

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
3. 在线 → 触发 Semantic Cache 增量索引（重新加载所有 sessions）
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

## Session 缓存完整性检查（每次心跳）

检查 sessions.json 中是否有最近活跃但未缓存的 session，并自动补救。

**检测逻辑**：按 24h → 48h → 72h 顺序查找缺失的 .jsonl 文件，避免重复缓存。

```bash
python3 ~/.openclaw/workspace/scripts/cache-missing-sessions.py 2>&1
```

**已知限制**：超过 48h 的历史 session，Gateway 已不保留内存数据，`openclaw session export` 拿不到内容（不影响，因为这些多为 cron 元数据，非用户对话）。

## 2026-03-30 13:54 CST 更新

### Ebbinghaus InterestTracker 实现完成 ✅
- **位置**：Ubuntu `~/semantic_cache/server.py`
- **备份**：MacBook `~/.openclaw/backup/pre-interest-tracking/`
- **报告**：`harness/robot/night-build/reports/A-Ebbinghaus-InterestTracker-实现报告.md`
- **测试结果**：6/6 项全部通过
- **注意**：服务启动需用 `~/miniconda/bin/python3 server.py`（不能用系统 python3）
- **已知问题**：进程曾因资源超限被 SIGKILL，确保内存充足
- **新增端点**：`/interest/update`、`/interest/search`、`/interest/reset`、`/interest/list`

## 2026-03-30 18:46 CST 更新

### LeWM 训练完成 ✅
- Ubuntu RTX 2060 已就绪
- LeWM 训练脚本已验证（2.84M 参数，10 epochs 完成）
- Checkpoint: `/home/jet/lewm_checkpoint.pt`

### A序列任务全部完成 ✅
- A-0001~A-0011 共7个任务全部完成
- B序列待执行（Phase 3 iPhone感知）

### Ubuntu 节点状态
- IP: 192.168.1.18
- SSH: ✅ 在线
- GPU: ✅ RTX 2060 可用
- Semantic Cache: ✅ 在线 (:5050)

## 2026-03-30 19:12 CST 更新

### MiniMax 状态
- 62.7%已用 | 224次剩余 | 46分钟后重置

### Ubuntu 节点状态
- IP: 192.168.1.18
- SSH: ✅ 在线
- GPU: ✅ RTX 2060 可用（87MB已用/6GB总容量，空闲）
- rsync: ✅ 已同步sessions到Ubuntu

### LeWM 数据集下载
- HF镜像(hf-mirror.com)：❌ 文件不存在(404)
- HF直连：❌ 超时
- 解决方案待定

### Night Build 状态
- A序列：✅ 全部完成(7/7)
- B序列：待执行

## 2026-03-30 19:32 CST 更新

### LeWM 数据集下载进展
- tworoom.h5 (12GB) ✅ 已下载到 ~/.stable-wm/
- h5py 无法安装（Ubuntu pip/apt均网络超时）
- 待解决：sudo apt install python3-h5py 或其他方案

### LeWM 训练 Checkpoint
- ~/lewm_checkpoint.pt (11MB) - dummy数据训练结果

### Ubuntu 节点
- 当前状态：❌ 离线
- IP: 192.168.1.18

## 2026-03-30 20:04 CST 更新

### LeWM 训练完成 ✅
- Ubuntu RTX 2060 可用
- tworoom数据集已加载（920809步，numpy格式）
- Checkpoint: ~/.stable-wm/lewm_tworoom.pt (1.7MB)
- ⚠️ loss=NaN（简化SIGReg + 无归一化，需后续调参）
- MiniMax: 3.3%已用，580次剩余，3h55后重置 ✅

## 2026-03-30 23:27 CST 更新

### LeWM Vision训练 ✅
- pusht图像 Vision Encoder 训练成功
- loss从0.94降至0.10后发散（学习率太高）
- Checkpoint: ~/.stable-wm/lewm_vision_v4.pt (3.2MB, 812K params)
- 206 episodes, 25650 frames, seq_len=8

### Ubuntu节点
- IP: 192.168.1.18
- 当前状态: ❌ 离线

### MiniMax额度
- 27.0%已用 | 438次剩余 | 32分钟后重置 ✅

# Last check: 2026-03-30 23:57 CST (15:57 UTC)
# MiniMax-M*: 434/600 remaining (166 used), 大量剩余
# Ubuntu: ❌ 离线
# rsync: ✅ 所有session已同步
# cache-missing: 0个缺失

# Last check: 2026-03-31 00:33 CST (16:33 UTC)
# MiniMax-M*: 581/600 remaining (19 used), 新周期
# Ubuntu: ❌ 离线
# rsync: ✅ 2个文件同步（含1个deleted session file）
# cache-missing: 0个缺失

# Last check: 2026-03-31 00:34 CST
# MiniMax-M*: 575/600 (⚠️ 25次剩余，几乎耗尽)
# Ubuntu: ❌ 离线

# Last check: 2026-03-31 01:05 CST
# MiniMax-M*: 476/600 (124 remaining)
# Ubuntu: ❌ 离线

# Last check: 2026-03-31 01:35 CST
# MiniMax-M*: 470/600 (新周期), 130次剩余, 3h24m后重置
# Ubuntu: ❌ 离线

# Last check: 2026-03-31 02:05 CST (18:05 UTC)n# MiniMax-M*: 467/600 (新周期, 133次剩余)n# Ubuntu: ❌ 离线

# Last check: 2026-03-31 02:35 CSTn# MiniMax-M*: 新周期, 136次剩余 ✅n# Ubuntu: ✅ 在线 (7个新session已同步)n# InterestTracker: 内存态待验证n
# Last check: 2026-03-31 03:05 CST (19:05 UTC)
# MiniMax-M*: 459/600 (141 remaining, 新周期刚重置)
# Ubuntu: rsync可达但ping超时（可能在休眠）

# Last check: 2026-03-31 10:38 CST (02:38 UTC)
- MiniMax-M*: 14.8%已用, 511次剩余, 4h20m后重置 ✅
- Ubuntu: ❌ 离线
- MT3方案B: ✅ T1-T5全部验证通过，软件链路PASS
- Git push: ✅ 已推送(62c8fc5)
- Ubuntu sessions同步: ✅ 完成(8417条索引)
- 待用户确认: AS5600编码器采购任务(优先级A)是否加入任务序列

# Last check: 2026-03-31 11:11 CST (03:11 UTC)
- MiniMax-M*: 27.8%已用, 433次剩余, 3h48m后重置 ✅
- Ubuntu: ❌ 离线
- Harness Engineering Skill: ✅ 已创建(skills/harness-engineering/)
- orchestrator-prompt.md: 更新到v6，Stage 0-4标准嵌入
- MT3方案B: ✅ 完成，T1-T5全部PASS
- 4个问题调研: ✅ 完成，报告在memory/2026-03-31-Q-AResearch.md
- Git push: ✅ 已推送(c0c8abd)
- 等待用户: Q2关节反馈方案A+D是否推进

# Last check: 2026-03-31 17:46 CST (09:46 UTC)
- MiniMax-M*: 41.0%已用, 354次剩余, 2h12m后重置 ✅
- Ubuntu: ❌ 离线（rsync可达但ping超时）
- rsync: ✅ 2个文件同步
- cache-missing: ✅ 48-72h内所有session均已缓存
- 今日调研：iPhone摄像头深度调研×2 + 影响力平台 + LeWM联动 + H2C精准抓取 + 章鱼触手抓夹方案


# Last check: 2026-03-31 18:03 CST (10:03 UTC)
# MiniMax: 49.7%已用, 302次剩余, 1h55m后重置 ✅
# Ubuntu: ✅ 在线(rsync+Semantic Cache可达, 0条索引可能重启过)
# rsync: ✅ 成功
# cache-missing: ✅ 0个缺失

# Last check: 2026-03-31 21:38 CST (13:38 UTC)
# MiniMax: 24.2%已用, 455次剩余, 2h21m后重置 ✅ (阈值正常)
# Ubuntu: ❌ 离线
# rsync: ✅ 成功
# cache-missing: ✅ 全部缓存完成

# Last check: 2026-03-31 23:50 CST (15:50 UTC)
# MiniMax: ⚠️ 80.2%已用, 119次剩余, 8分钟后重置 (⚠️ 触及80%阈值)
# Ubuntu: rsync成功 (154MB total), ping不可达
# cache-missing: ✅ 0个缺失
# docs.0-1.ai: ✅ 已重启(http://127.0.0.1:18998/)

# Last check: 2026-04-01 00:59 CST (16:59 UTC)
# MiniMax: ✅ 新周期 00:00-05:00, 53.2%已用, 281次剩余, 4h后重置
# Ubuntu: ❌ 离线
# rsync: ✅ 成功(159MB total)
# docs.0-1.ai: ✅ 运行中(http://127.0.0.1:18998/)
# cache-missing: 脚本超时，跳过

# Last check: 2026-03-31 23:50 CST → 04-01 02:35 CST
# MiniMax: ⚠️ 88.0%已用, 72次剩余, 2h24m后重置 (⚠️ 超过80%阈值)
# rsync: ✅ 成功
# docs.0-1.ai: ✅ 在线
# Last check: 04-01 02:35 CST | MiniMax: ⚠️88%已用,72次剩余,2h24m后重置 | docs: ✅
# Last check: 2026-04-01 04:38 CST (20:38 UTC)
# MiniMax: ⚠️ 91.7%已用, 50次剩余, 21分钟后重置 (⚠️ 超过90%阈值)
# Ubuntu: ❌ 离线
# rsync: ✅ 成功
# docs.0-1.ai: ✅ 在线

# Last check: 2026-04-01 04:05 CST (20:05 UTC)
# MiniMax: ⚠️ 90.3%已用, 58次剩余, 53分钟后重置 (⚠️ 超过90%阈值)
# Ubuntu: ❌ 离线
# rsync: ✅ 成功
# cache-missing: 脚本超时，跳过

# Last check: 2026-04-01 08:19 CST (00:19 UTC)
# MiniMax: ✅ 9.8%已用, 541次剩余, 1h39m后重置 ✅
# Ubuntu: ❌ 离线
# rsync: ✅ 成功
# docs.0-1.ai: ✅ 在线
# Note: 3个cron session报错 "crontab: tmp/tmp.XXXXX: Operation not permitted" — sandbox限制，不影响主流程

# Last check: 2026-04-01 06:39 CST (22:39 UTC)
# MiniMax: ✅ 新周期刚进入, 97.7%剩余, 586次剩余, 3h19m后重置
# Ubuntu: ❌ 离线
# rsync: ✅ 成功

# Last check: 2026-04-01 09:44 CST (01:44 UTC)
# MiniMax: ✅ 28.8%已用, 427次剩余, 15分钟后重置
# Kimi调研subagent: 运行中(35m)，通过Playwright Chrome方式，尚未完成
# docs.0-1.ai: ✅ 在线(http://127.0.0.1:18998/)
# 待用户确认: kimi_kimi_chat是否能在主agent直接调用（alsoAllow已配置）

# Last check: 2026-04-01 10:03 CST (02:03 UTC)
# MiniMax: ✅ 2.3%已用, 586次剩余, 4h56m后重置 (新周期10:00-15:00)
# Ubuntu: ❌ 离线(rsync可达, ping不可达)
# rsync: ✅ 成功(15KB sent)
# docs.0-1.ai: ❌ 不响应(连接失败，需重启)
# Kimi调研subagent: 已中止(用户操作)
# cache-missing: 脚本超时，跳过

# Last check: 2026-04-02 00:05 CST (16:05 UTC)
# MiniMax: ✅ 0.7%已用, 596次剩余, 4h53m后重置 (新周期 00:00-05:00)
# Ubuntu: ❌ 离线(rsync可达，ping不可达)
# rsync: ✅ 成功(1个新session同步)
# cache-missing: 脚本超时，跳过
# docs.0-1.ai: 未检查

# Last check: 2026-04-01 22:09 CST (14:09 UTC)
# MiniMax: ✅ 9.8%已用, 541次剩余, 1h50m后重置 (阈值正常)
# Ubuntu: ❌ 离线
# rsync: ✅ 成功(466KB sent)
# docs.0-1.ai: ✅ 在线
# docs.0-1.ai修复进度: F-006✅ F-007✅(代码已写入) F-008~F-013⏳

# Last check: 2026-04-01 22:12 CST (14:12 UTC)
# Night Build v5: A-0012 (Buzzy AI调研) 派发到subagent运行中
# MiniMax: ⚠️ 88.5%已用, ~69次剩余, 1h46m后重置 (⚠️ 80%阈值触发)
# A-0012状态: pending -> running
# Ubuntu: ❌ 离线
# rsync: 待确认
# docs.0-1.ai: ✅ 在线

# Last check: 2026-04-01 22:59 CST (14:59 UTC)
# Night Build v5: A-0012 ✅ + T-1802 ✅ → A序列 9/9 完成
# A序列: 全部完成 (A-0001~A-0012, T-1802)
# 产出: 3个py代码文件 + 2份调研/实现报告
# docs.0-1.ai: ✅ 在线

# Last check: 2026-04-02 05:31 CST (21:31 UTC)
# MiniMax: ✅ 2.5%已用, 585次剩余, 4h26m后重置 (阈值正常)
# Ubuntu: ❌ 离线(rsync可达, ping不可达)
# rsync: ✅ 成功(1个session同步: deleted file)
# docs.0-1.ai: ❌ 404(进程可能挂了，需重启)
# 凌晨静默，阈值正常

# Last check: 2026-04-02 01:26 CST (17:26 UTC)
# MiniMax: ✅ 27.0%已用, 438次剩余, 3h33m后重置 (阈值正常)
# Ubuntu: ❌ rsync可达但ping不可达(离线)
# rsync: ✅ 成功(16.8KB sent)
# docs.0-1.ai: ❌ 不响应
# cache-missing: 脚本超时，跳过

# Last check: 2026-04-02 05:01 CST (21:01 UTC)
# MiniMax: ✅ 0.5%已用, 597次剩余, 4h57m后重置
# Ubuntu: ❌ 离线(rsync可达, ping不可达)
# rsync: ✅ 成功(1个session同步: e01c7fe0)
# docs.0-1.ai: ❌ 404(可能需重启)
# 凌晨静默，阈值正常

# Last check: 2026-04-02 07:46 CST (23:46 UTC)
# MiniMax: ✅ 34.8%已用, 391次剩余, 2h12m后重置 (阈值正常)
# Ubuntu: ❌ 离线(rsync可达, ping不可达)
# docs.0-1.ai: ❌ 404(进程挂了，需重启)

# Last check: 2026-04-02 20:58 CST (12:58 UTC)
# Tailscale: ✅ Ubuntu已接入 Tailnet (100.97.193.116)
# Semantic Cache: ✅ Tailnet IP可访问 (10972条索引)
# Ubuntu Tailscale: userspace模式，jets bin/，开机自启已配置
# MiniMax: 未检查(Gateway离线)

### Tailscale 远程访问（已完成 2026-04-02）
- Ubuntu: Tailscale userspace 模式安装在 ~/bin/
- Tailnet IP: 100.97.193.116
- 自启: ~/.config/autostart/tailscale.desktop
- Mac 同账号: 100.106.79.30
- Semantic Cache: http://100.97.193.116:5050

### OpenClaw 版本检查（不定期）
- 每次心跳时检查 GitHub latest release
- 如果发现新版本，按照 `skills/openclaw-upgrade/SKILL.md` 执行升级准备流程
- 询问用户是否执行升级

### Session Cache Cron（已完成 2026-04-02）
- cron ID: e8c93642-c134-481b-9897-595ca27610f0
- 频率: 每30分钟 (xx:30)
- 动作: rsync sessions → Ubuntu + curl reindex
- exec 白名单已设置: rsync, curl, python3, ssh, ssh-keyscan
- 脚本: cache-missing-sessions.py (UPDATED参数增量同步)

### exec-approvals 经验（2026-04-02）
- v4.1 新增 exec 审批：`~/.openclaw/exec-approvals.json` 控制白名单
- `allow-always` 后命令永久免审批
- `security: allowlist` 模式下每个命令路径都要在白名单里
- 推荐流程：把常用命令跑一遍 → 用户批准 allow-always → 以后免审批
