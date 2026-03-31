# Ebbinghaus 遗忘曲线 InterestTracker 实现报告

## 基本信息
- **日期**：2026-03-30
- **负责人**：OpenClaw Subagent
- **服务器**：Ubuntu (192.168.1.18)
- **文件**：`~/semantic_cache/server.py`

---

## 实现内容

### 核心类：InterestTracker

基于 Ebbinghaus 遗忘曲线 `R(t) = e^(-Δt / S)`：

- **S 参数**：初始为 3.0，每次更新关键词时 × 1.5（记忆强化）
- **衰减因子**：`np.exp(-dt_hours / (S * 24))`，S 以天为单位
- **boost 上限**：0.5，防止过度加权

```python
class InterestTracker:
    def __init__(self, decay_base=3.0):
        self.interests = {}   # {(session_id, keyword): {"S": strength, "last_seen": ts}}
        self.decay_base = decay_base

    def decay_factor(self, entry):
        dt_hours = (datetime.now().timestamp() - entry["last_seen"]) / 3600
        return np.exp(-dt_hours / (entry["S"] * 24))

    def update(self, keywords, session_id="global"):
        for kw in keywords:
            key = (session_id, kw.lower())
            if key in self.interests:
                self.interests[key]["S"] *= 1.5   # 强化
                self.interests[key]["last_seen"] = now
            else:
                self.interests[key] = {"S": self.decay_base, "last_seen": now}

    def interest_boost(self, text, session_id="global"):
        # 累加所有匹配关键词的衰减因子，上限 0.5
        ...

    def reset(self, session_id="global"):
        # 删除指定会话的兴趣数据
        ...
```

### 辅助函数：extract_keywords

简单词频 TF-IDF，提取 top_n=10 个关键词（长度≥2，跳过停用词）。

### 新增 API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/interest/update` | POST | 更新关键词（触发 S×1.5 强化） |
| `/interest/search` | POST | 查询文本的兴趣 boost 值 |
| `/interest/reset` | POST | 重置某会话的兴趣数据 |
| `/interest/list` | GET | 列出当前活跃兴趣关键词及 S 值 |

### 搜索注入点

在 `expand_query(q)` 之后注入 `extract_keywords` + `interest_tracker.update`：
- **BM25 模式**：`final_sim = max(0, bm25_norm + time_boost) + interest_boost`
- **Hybrid 模式**：`boosted = max(0, final_raw + time_boost) + interest_boost`
- **语义搜索模式**：`boosted_sim = max(0, raw_sim + time_boost) + interest_boost`

每条结果返回字段新增 `interest_boost`。

---

## 测试结果

### 6/6 项全部通过

| 测试 | 预期 | 实际 | 结果 |
|------|------|------|------|
| 更新关键词 | `{"ok":true,"tracked":3}` | 同左 | ✅ |
| 首次 boost 查询 | `interest_boost: 0.5` | `{"active_interests":3,"interest_boost":0.5}` | ✅ |
| 列出关键词 | 显示 S=3.0, decay_factor=1.0 | 正确 | ✅ |
| 重复更新 jetson | S: 3.0→4.5→6.75 | 3次后 S=6.75 | ✅ |
| Reset | `{"ok":true}` | 同左 | ✅ |
| 实际搜索注入 | 结果含 `interest_boost` | similarity=1.32, 含 0.5 boost | ✅ |

### Interest Boost 对搜索分数的影响示例

搜索 "OpenClaw配置" 时，包含 "openclaw" 关键词的结果：
- `raw_similarity`: 0.746（embedding 语义相似度）
- `time_boost`: +0.08（7天内）
- `interest_boost`: +0.5（global session 追踪到 "OpenClaw"）
- **`similarity`**: 1.326（>1.0，正常，因为 boost 叠加）

---

## 重要工程细节

1. **Python 环境**：必须用 `~/miniconda/bin/python3 server.py`，系统 python3 缺少 faiss 模块
2. **服务重启**：只用 `pkill` + `nohup` 重启 semantic_cache 进程，不影响服务器其他服务
3. **内存态**：interest_tracker 是内存态，服务器重启后丢失（设计预期）
4. **并发安全**：单进程 Flask，无需额外锁

---

## 备份位置

| 文件 | MacBook 路径 |
|------|-------------|
| 原始备份 | `~/.openclaw/backup/pre-interest-tracking/server.py.ebbinghaus_backup.py` |
| 实现后版本 | `~/.openclaw/backup/pre-interest-tracking/server.py.with_interest.py` |

---

## 下一步建议

1. **持久化**：可将 `interest_tracker.interests` 定期写入磁盘（JSON），避免重启丢失
2. **per-session boost**：目前 global session 可以工作，但 per-user session 隔离尚未完全验证
3. **衰减曲线可视化**：可增加 `/interest/debug` 端点输出 S 随时间变化的曲线数据
4. **搜索集成**：可让 AI assistant 在发起 search 前主动 POST `/interest/update`，提升主动兴趣追踪精度
