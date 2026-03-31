# SOP 补充：贵庚系统 记忆架构 — 数据结构设计

> **补充章节**：原 ROBOT-SOP.md §1.2.4 记忆索引与检索 — 数据结构设计详解
> **补充日期**：2026-03-30
> **补充内容**：Layer 1 向量索引 + 元数据存储 + 时间线索引的底层数据结构选型

---

## 1. 语义缓存的数据结构（Layer 1：向量索引）

### 1.1 技术栈选择依据

**sentence-transformers + FAISS** 是目前本地 RAG 语义缓存的最佳组合，原因是：

| 维度 | sentence-transformers | FAISS |
|------|----------------------|-------|
| 模型质量 | MTEB 排行榜 benchmark，all-MiniLM-L6-v2 / all-mpnet-base-v2 | — |
| 推理性能 | ONNX 可导出，CPU 推理 < 50ms/句 | — |
| 索引速度 | 离线下 embedding | CPU/GPU 批量建索引 |
| 内存效率 | 模型 ~ 90MB（miniLM）~ 420MB（mpnet） | 只存向量，1M vectors ≈ 4GB（768d, float32）|
| 本地化 | 100% 本地，无需 API Key | 100% 本地 |

### 1.2 语义缓存 JSON 结构（in-memory / 文件持久化）

```python
{
    "cache_version": "1.0",
    "created_at": "2026-03-20T10:00:00Z",
    "model_name": "all-MiniLM-L6-v2",
    "embedding_dim": 384,
    "total_entries": 1247,
    "entries": [
        {
            "entry_id": "uuid-v4",
            "content": "用户提到想去日本旅游",
            "content_hash": "sha256:abc123...",          # 精确去重
            "embedding": [0.123, -0.456, ...],       # 384d float32
            "response": "上次聊到日本是2025年12月...",
            "timestamp": "2026-03-20T14:30:00Z",
            "importance": 0.8,
            "access_count": 3,
            "last_accessed": "2026-03-24T10:00:00Z",
            "expires_at": "2027-03-20T10:00:00Z"      # TTL: 1年
        }
    ]
}
```

**语义缓存淘汰策略**（FIFO + LRU 混合）：

```python
def evict(cache, max_entries=5000):
    if len(cache["entries"]) >= max_entries:
        # 淘汰策略：优先淘汰低访问 + 旧条目
        # score = access_count * 0.3 + age_days * -0.1 + importance * 0.6
        cache["entries"].sort(key=lambda x: x["access_count"] * 0.3
                              - (now - x["timestamp"]).days * 0.1
                              + x["importance"] * 0.6)
        cache["entries"] = cache["entries"][:max_entries // 10 * 9]  # 保留90%
```

### 1.3 FAISS 索引操作

```python
import faiss
import numpy as np

# --- 模型加载 ---
from sentence_transformers import SentenceTransformer
encoder = SentenceTransformer('all-MiniLM-L6-v2')  # 384d, 22M params
# 可选升级：all-mpnet-base-v2 → 768d, 110M params, MTEB 精度更高

# --- FAISS 索引初始化 ---
EMBEDDING_DIM = 384

# 方案A：Flat（暴力精确搜索，适合 < 10万 条目）
index_flat = faiss.IndexFlatL2(EMBEDDING_DIM)       # L2 距离
# index_flat = faiss.IndexFlatIP(EMBEDDING_DIM)    # 内积（需 normalize，向量余弦相似度）

# 方案B：IVF（倒排索引，聚类加速，适合 > 10万 条目）
quantizer = faiss.IndexFlatL2(EMBEDDING_DIM)
index_ivf = faiss.IndexIVFFlat(quantizer, EMBEDDING_DIM, nlist=100)
index_ivf.train(embeddings.astype(np.float32))     # 训练聚类中心
index_ivf.nprobe = 10                               # 搜索探针数（召回率 vs 速度）

# 方案C：HNSW（NSW 图，适合毫秒级低延迟需求）
index_hnsw = faiss.IndexHNSWFlat(EMBEDDING_DIM, m=16, efConstruction=200)
index_hnsw.hnsw.efSearch = 64                       # 搜索宽度
index_hnsw.hnsw.efConstruction = 200               # 建索引宽度

# --- 添加向量 ---
embedding = encoder.encode(["用户提到想去日本旅游"])
index_flat.add(embeddings.astype(np.float32))

# --- 语义检索 ---
query_emb = encoder.encode(["有没有聊过去日本玩"])
D, I = index_flat.search(query_emb.astype(np.float32), k=5)
# D: 距离数组, I: 索引数组
```

---

## 2. 向量维度选择（192 / 384 / 768）

### 2.1 三档对比

| 维度 | 代表模型 | MTEB 精度 | 推理速度 | 内存占用 | 推荐场景 |
|------|---------|----------|---------|---------|---------|
| **192d** | paraphrase-MiniLM-L3-v2 | ~55% | ~5ms/句 | 极低 | 阶段一 MVP，NAS 性能受限 |
| **384d** | all-MiniLM-L6-v2 ⭐ | ~62% | ~15ms/句 | 低 | 阶段一/二首选，均衡之选 |
| **768d** | all-mpnet-base-v2 | ~68% | ~40ms/句 | 中等 | 阶段二后期，精度优先 |

### 2.2 选型建议

```
阶段一（当前）：384d — all-MiniLM-L6-v2
  → 精度够用，推理快，模型小（90MB），CPU 可推理
  → FAISS IndexFlatL2 完全够用（< 5万 条目）

阶段二（2026-2027）：768d — all-mpnet-base-v2
  → 视频标注增多，语义理解精度要求提高
  → FAISS IndexHNSWFlat，efSearch=64，毫秒级检索

阶段三（5年+）：自训练 embedding 模型
  → 用贵庚积累的对话数据 fine-tune 专属 embedding
  → 维度按需设定（192d 压缩或 1024d 扩展）
```

---

## 3. 索引类型选择（Flat / IVF / HNSW）

### 3.1 三种索引特性对比

| 索引类型 | 构建速度 | 查询延迟 | 召回率 | 内存占用 | 适合规模 |
|---------|---------|---------|--------|---------|---------|
| **Flat (IndexFlatL2)** | O(N) 即时 | O(N) 暴力 | **100%** | 高（全量向量）| < 10万 |
| **IVF (IndexIVFFlat)** | 需训练 O(N) | O(N/nlist × nprobe) | 90-99% | 中（+倒排）| 10万-1000万 |
| **HNSW (IndexHNSWFlat)** | O(N log N) | O(log N) | 95-99% | 较高（图结构）| 10万-1亿 |

### 3.2 选型建议

```
数据量 < 5万 条目（阶段一）：
  → IndexFlatL2
  → 优点：100% 召回率，实现简单，调试方便
  → 缺点：O(N) 查询，但 5万 × 384d = 76MB，毫秒级

数据量 5万-100万 条目（阶段二）：
  → IndexHNSWFlat(m=16, efConstruction=200, efSearch=64)
  → 优点：O(log N) 查询，精度接近 Flat，GPU 可加速
  → 缺点：建索引慢（但离线一次性），内存占用较高

数据量 > 100万 条目（阶段三长视频数据）：
  → IndexIVFFlat + IndexHNSWFlat 组合
  → IVF 聚类降量 → HNSW 图搜索子聚类
  → nlist=1024, nprobe=32
```

### 3.3 混合查询（实际生产用法）

```python
# 语义相似度阈值过滤 + 结果验证
def semantic_search(query, top_k=5, threshold=0.35):
    query_emb = encoder.encode([query])
    D, I = index.search(query_emb.astype(np.float32), top_k * 3)  # 多取几倍

    results = []
    for dist, idx in zip(D[0], I[0]):
        if idx == -1:
            break
        # L2 距离转余弦相似度（近似）
        # dist=0 → 相同, dist=4 → 正交, dist>8 → 完全不相关
        similarity = max(0, 1 - dist / 4)
        if similarity >= threshold:
            results.append((cache_entry[idx], similarity))
    return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]
```

---

## 4. 元数据存储（JSON / SQLite）

### 4.1 选型对比

| 维度 | JSON 文件 | SQLite | PostgreSQL (pgvector) |
|------|----------|--------|----------------------|
| 存储容量 | < 100MB（单文件）| 理论上无限（文件级）| 理论上无限 |
| 查询能力 | 全读内存，O(N) | B-tree 索引，O(log N) | B-tree + 向量混合索引 |
| 事务支持 | ❌ | ✅ ACID | ✅ ACID |
| 并发写入 | ❌（需文件锁）| ✅ | ✅ |
| 向量字段 | ❌ | ❌（需扩展）| ✅ 原生 pgvector |
| 部署复杂度 | 无 | 零依赖 | 需要 PG 服务 |
| 适用场景 | 阶段一 MVP | 阶段二扩展（中等规模）| 阶段二/三生产级 |

### 4.2 推荐架构（分阶段）

```
阶段一（< 1万 条记忆条目）：
  JSON 文件存储 + FAISS IndexFlatL2
  → 零依赖，调试简单，数据随取随用
  → 路径：~/.openclaw/workspace/guigeng-memory/semantic_cache.json

阶段二（1万-100万 条记忆条目）：
  SQLite 存储元数据 + FAISS 索引
  → 元数据：timestamp, entities, importance, content_hash
  → 向量：FAISS 独立索引文件
  → SQLite schema:
    CREATE TABLE memories (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        content_hash TEXT UNIQUE,
        timestamp DATETIME,
        importance REAL DEFAULT 0.5,
        entity_json TEXT,          -- JSON 存储 entities 数组
        faiss_idx INTEGER,          -- 指向 FAISS 索引中的位置
        access_count INTEGER DEFAULT 0,
        last_accessed DATETIME
    );
    CREATE INDEX idx_timestamp ON memories(timestamp);
    CREATE INDEX idx_importance ON memories(importance DESC);

阶段三（> 100万 条记忆条目 + 视频帧标注）：
  PostgreSQL + pgvector 扩展
  → 混合检索：向量相似度 + 时间范围 + 实体过滤
  → 同时支持 Layer 2 图谱（Neo4j）联动查询
```

### 4.3 JSON → SQLite 迁移脚本（阶段一→阶段二）

```python
import json
import sqlite3
import hashlib

def migrate_json_to_sqlite(json_path, db_path):
    with open(json_path, 'r') as f:
        cache = json.load(f)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 创建表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            content_hash TEXT UNIQUE,
            timestamp TEXT,
            importance REAL,
            entity_json TEXT,
            faiss_idx INTEGER,
            access_count INTEGER DEFAULT 0,
            last_accessed TEXT,
            raw_entry TEXT  -- 完整原始 entry JSON
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)')

    for entry in cache['entries']:
        cur.execute('''
            INSERT OR IGNORE INTO memories
            (id, content, content_hash, timestamp, importance,
             entity_json, access_count, last_accessed, raw_entry)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry['entry_id'],
            entry['content'],
            hashlib.sha256(entry['content'].encode()).hexdigest(),
            entry['timestamp'],
            entry.get('importance', 0.5),
            json.dumps(entry.get('entities', [])),
            entry.get('access_count', 0),
            entry.get('last_accessed'),
            json.dumps(entry)
        ))

    conn.commit()
    conn.close()
    print(f"Migrated {len(cache['entries'])} entries to {db_path}")
```

---

## 5. 时间线索引设计（Layer 3）

### 5.1 时间线索引核心需求

回答"上次是什么时候"需要：
1. **按时间范围快速过滤**（B-tree on timestamp）
2. **按时间窗口聚合**（日/周/月聚合视图）
3. **时间线回溯浏览**（分页向前向后）
4. **时间语义解析**（"上周"、"上个月"、"去年这时候"→具体时间范围）

### 5.2 时间线索引数据结构

```python
# --- 时间窗口聚合索引（预计算）---
class TimelineIndex:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)

    def add_entry(self, memory_id, timestamp, content, importance):
        # 写入主表
        self.conn.execute('''
            INSERT INTO memories (id, timestamp, content, importance)
            VALUES (?, ?, ?, ?)
        ''', (memory_id, timestamp, content, importance))

        # 预计算时间窗口聚合（以天为单位）
        day_key = timestamp[:10]  # "2026-03-20"
        self.conn.execute('''
            INSERT INTO timeline_daily (day_key, memory_ids, count, avg_importance)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(day_key) DO UPDATE SET
                memory_ids = timeline_daily.memory_ids || ',' || ?,
                count = count + 1,
                avg_importance = (avg_importance * count + ?) / (count + 1)
        ''', (day_key, memory_id, importance, memory_id, importance))

    def query_range(self, start_ts, end_ts):
        """时间范围查询"""
        cur = self.conn.execute('''
            SELECT id, timestamp, content, importance
            FROM memories
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        ''', (start_ts, end_ts))
        return cur.fetchall()

    def query_relative(self, phrase):
        """自然语言时间解析"""
        now = datetime.now()
        # 简单规则解析（可升级为 LLM 解析）
        relative_map = {
            "今天": (now.replace(hour=0, minute=0), now),
            "昨天": (now - timedelta(days=1), now - timedelta(days=1) + timedelta(hours=23, minutes=59)),
            "上周": (now - timedelta(weeks=1), now - timedelta(weeks=1) + timedelta(days=6, hours=23, minutes=59)),
            "上个月": (now - timedelta(days=30), now - timedelta(days=30) + timedelta(days=29)),
            "去年": (now.replace(year=now.year-1), now.replace(year=now.year-1)),
            "去年这时候": (
                now.replace(year=now.year-1, month=now.month, day=now.day,
                           hour=now.hour, minute=now.minute),
                now.replace(year=now.year-1, month=now.month, day=now.day,
                           hour=now.hour, minute=now.minute)
            ),
        }
        if phrase in relative_map:
            return self.query_range(*relative_map[phrase])
        return []

    def get_timeline_page(self, anchor_ts, direction='before', page_size=20):
        """时间线分页浏览"""
        if direction == 'before':
            cur = self.conn.execute('''
                SELECT id, timestamp, content, importance
                FROM memories
                WHERE timestamp < ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (anchor_ts, page_size))
        else:
            cur = self.conn.execute('''
                SELECT id, timestamp, content, importance
                FROM memories
                WHERE timestamp > ?
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (anchor_ts, page_size))
        return cur.fetchall()

    def get_daily_summary(self, day_key):
        """某天的记忆摘要"""
        cur = self.conn.execute('''
            SELECT content, importance, timestamp
            FROM memories
            WHERE timestamp LIKE ?
            ORDER BY importance DESC, timestamp DESC
        ''', (f"{day_key}%",))
        return cur.fetchall()
```

### 5.3 时间线索引 SQLite Schema

```sql
-- 主记忆表
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    content_hash TEXT UNIQUE,
    timestamp DATETIME NOT NULL,
    importance REAL DEFAULT 0.5,
    entity_json TEXT,
    faiss_idx INTEGER,
    access_count INTEGER DEFAULT 0,
    last_accessed DATETIME,
    tags TEXT  -- 手动标签：["重要", "待跟进"]
);

CREATE INDEX idx_memories_timestamp ON memories(timestamp);
CREATE INDEX idx_memories_importance ON memories(importance DESC);

-- 时间线聚合表（预计算）
CREATE TABLE timeline_daily (
    day_key TEXT PRIMARY KEY,          -- "2026-03-20"
    memory_ids TEXT,                    -- 逗号分隔的 memory_id 列表
    count INTEGER DEFAULT 0,
    avg_importance REAL DEFAULT 0.5,
    first_ts DATETIME,
    last_ts DATETIME
);

-- 事件序列表（连续事件标记）
CREATE TABLE event_sequences (
    sequence_id TEXT PRIMARY KEY,
    start_ts DATETIME,
    end_ts DATETIME,
    memory_ids TEXT,
    label TEXT,                        -- "做饭", "外出", "通话"
    location TEXT,
    persons TEXT                        -- 逗号分隔的人名
);

CREATE INDEX idx_event_sequences_ts ON event_sequences(start_ts, end_ts);
```

### 5.4 时间语义解析（高级）

"去年这时候"等复杂语义用 LLM 解析：

```python
def parse_time_phrase(phrase: str, now: datetime) -> (datetime, datetime):
    """用小模型解析自然语言时间为具体范围"""
    prompt = f"""当前时间：{now.isoformat()}
解析以下时间短语，返回 start 和 end（ISO 格式）：

短语："{phrase}"

规则：
- 如果是单点时间，返回相同 start 和 end
- 如果是模糊时间，返回合理的范围
- 如果是相对时间，以当前时间为基准

返回 JSON：{{"start": "ISO时间", "end": "ISO时间", "confidence": 0.0-1.0}}"""

    # 用 Qwen2.5-0.5B 本地推理（或调用 MiniMax API）
    response = llm_local(prompt)
    return json.loads(response)
```

---

## 6. 完整数据流总览

```
用户输入
    ↓
┌─────────────────────────────────────────────┐
│  Layer 0: 原始数据接收                       │
│  - 对话文本 → 直接存储                        │
│  - 语音 → Whisper 转文本 → 存储              │
│  - 视频 → RynnBrain 标注 → 结构化 JSON      │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Layer 1: 语义缓存（向量索引）                │
│  - sentence-transformers (384d / 768d)      │
│  - FAISS IndexHNSWFlat                      │
│  - 语义去重 + 相似查询 + 新记忆写入           │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Layer 2: 知识图谱（Neo4j）                  │
│  - Mem0 自动抽取实体关系                     │
│  - 人物 / 地点 / 事件 / 概念 节点             │
│  - 时间线边 + 因果边 + 重要性边权重          │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Layer 3: 时序索引（SQLite + 预计算）        │
│  - B-tree on timestamp                      │
│  - 日/周/月聚合视图                         │
│  - 自然语言时间解析（LLM）                   │
└─────────────────────────────────────────────┘
    ↓
检索时：Layer 1（语义）→ Layer 2（图谱）→ Layer 3（时序）联合查询
```

---

## 7. 存储路径规划

```
~/.openclaw/guigeng-memory/
├── cache/
│   ├── semantic_cache.json       # 阶段一 MVP
│   └── semantic_cache.db         # 阶段二 SQLite
├── faiss/
│   ├── index_flat.seqs           # Flat 索引
│   └── index_hnsw.seqs           # HNSW 索引
├── graph/
│   └── neo4j/                    # Neo4j 数据目录
├── timeline/
│   └── timeline.db               # 时间线 SQLite
├── raw/                          # 原始数据备份
│   └── YYYY-MM/                  # 按月分目录
└── config.json                   # 当前配置版本
```

---

## 8. 技术风险与备选方案

| 风险 | 影响 | 备选方案 |
|------|------|---------|
| FAISS 内存爆炸（> 1000万向量）| NAS 内存不足 | 切换到 Qdrant（磁盘索引）或自己实现分层索引 |
| SQLite 并发写入瓶颈 | 多 session 同时写记忆卡顿 | 切换到 PostgreSQL |
| all-mpnet-base-v2 CPU 推理慢 | 语义检索延迟 > 1s | 导出 ONNX + Intel OpenVINO 加速 |
| Neo4j 部署复杂 | 运维成本高 | 降级到 SQLite JSON 实体表 |
| 语义相似度阈值难调 | 缓存命中不准 | 用 RL 从真实交互中学习阈值 |
