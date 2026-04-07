# SOP 补充：贵庚系统 记忆架构 — 数据结构设计 + 检索算法

> **补充章节**：原 ROBOT-SOP.md §1.2.4 记忆索引与检索 — 数据结构设计详解 + 检索算法详解
> **补充日期**：2026-03-30（数据结构）；2026-04-01（检索算法）
> **补充内容**：Layer 1 向量索引 + 元数据存储 + 时间线索引 + **检索算法完整实现**

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

---

## 9. 检索算法完整实现（两阶段融合排序）

> 本节补充 §1.2.4 检索算法 的代码级实现细节，对应 ROBOT-SOP.md 中"两阶段融合排序"的技术方案。

### 9.1 算法总览

```
用户查询
  ↓
第一阶段：候选集生成（并行）
├─ 语义路径：Embedding → FAISS Top-K_sem（如 K=200）
└─ 时间路径：时间解析 → SQLite timestamp → N 条
  ↓
第二阶段：融合重排序
├─ 语义得分（余弦相似度，已知）
├─ 时间邻近得分（时间窗口衰减函数）
├─ 重要性得分（importance 字段归一化）
└─ 轻量级交叉编码器打分（如有，阶段二引入）
  ↓
加权求和 → Top-K_ret（如 K=5）返回
```

### 9.2 第一阶段：多路候选集并行生成

```python
import faiss
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
from datetime import datetime, timedelta
import json

class GuigengRetriever:
    def __init__(self, config):
        # Layer 1：向量模型 + FAISS 索引
        self.encoder = SentenceTransformer(config['model_name'])  # all-MiniLM-L6-v2
        self.faiss_index = faiss.read_index(config['faiss_index_path'])
        # Layer 3：SQLite 时序索引
        self.conn = sqlite3.connect(config['timeline_db_path'])
        self.embedding_dim = config['embedding_dim']  # 384

    # ── 第一阶段：语义路径 ────────────────────────────────────────────
    def semantic_search(self, query: str, top_k: int = 200) -> list[tuple]:
        """Layer 1 向量语义检索，返回 (entry_id, similarity) 列表"""
        query_emb = self.encoder.encode([query]).astype(np.float32)
        # L2 距离转余弦相似度（近似）
        D, I = self.faiss_index.search(query_emb, top_k)
        results = []
        for dist, idx in zip(D[0], I[0]):
            if idx == -1:
                break
            # L2 距离转相似度：dist=0 → 1.0，dist=4 → 0（正交），dist>4 → <0
            similarity = max(0, 1 - dist / 4.0)
            results.append((idx, float(similarity)))
        return results  # [(faiss_idx, similarity), ...]

    # ── 第一阶段：时间路径 ────────────────────────────────────────────
    def time_filter(self, time_phrase: str, now: datetime) -> list[int]:
        """Layer 3 时序过滤，返回 memory_id 列表"""
        start, end = self._parse_time_phrase(time_phrase, now)
        cur = self.conn.execute('''
            SELECT id FROM memories
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        ''', (start.isoformat(), end.isoformat()))
        return [row[0] for row in cur.fetchall()]

    def _parse_time_phrase(self, phrase: str, now: datetime):
        """自然语言时间解析 → (start, end)"""
        phrase = phrase.strip()
        # 精确匹配
        mapping = {
            "今天": (now.replace(hour=0, minute=0, second=0), now),
            "昨天": (now - timedelta(days=1), now - timedelta(days=1) + timedelta(hours=23, minutes=59, seconds=59)),
            "上周": (now - timedelta(weeks=1), now - timedelta(weeks=1) + timedelta(days=6, hours=23, minutes=59)),
            "上个月": (now - timedelta(days=30), now - timedelta(days=1)),
            "去年": (now.replace(year=now.year - 1), now.replace(year=now.year - 1, month=12, day=31)),
            "去年这时候": (
                now.replace(year=now.year - 1, month=now.month, day=now.day, hour=now.hour, minute=now.minute),
                now.replace(year=now.year - 1, month=now.month, day=now.day, hour=now.hour, minute=now.minute)
            ),
        }
        if phrase in mapping:
            return mapping[phrase]
        # 模糊匹配：包含"去年"/"上月"等关键词
        if "去年" in phrase and "这时" in phrase:
            return mapping["去年这时候"]
        # 默认返回全天
        return now.replace(hour=0, minute=0), now

    # ── 第一阶段：候选集合并 ───────────────────────────────────────────
    def generate_candidates(self, query: str, time_phrase: str = None,
                             k_sem: int = 200, k_time: int = 500) -> set:
        """多路候选集生成 + 合并去重"""
        # 语义路径
        sem_results = self.semantic_search(query, top_k=k_sem)
        sem_ids = {idx for idx, _ in sem_results}

        # 时间路径（如指定）
        if time_phrase:
            time_ids = set(self.time_filter(time_phrase, datetime.now()))
            # 取语义和时间路径的并集（时间路径扩大候选集覆盖面）
            candidate_ids = sem_ids | time_ids
        else:
            candidate_ids = sem_ids

        return candidate_ids, sem_results  # 返回候选 ID 和语义得分备用
```

### 9.3 第二阶段：多维度融合重排序

```python
    # ── 第二阶段：融合打分 ─────────────────────────────────────────────
    def fuse_rerank(self, candidate_ids: set, sem_results: list,
                    time_phrase: str, now: datetime,
                    k: int = 5, use_cross_encoder: bool = False) -> list[dict]:
        """
        融合排序：语义分 + 时间邻近分 + 重要性分 → 综合得分 Top-K

        得分公式：
            score = w_sem * sim_sem + w_time * sim_time + w_imp * importance
            其中 w_sem + w_time + w_imp = 1.0
        """
        w_sem  = 0.50   # 语义权重
        w_time = 0.25   # 时间邻近权重
        w_imp  = 0.25  # 重要性权重

        # 建立语义得分查找表（O(1)）
        sem_score_map = {idx: sim for idx, sim in sem_results}

        # 解析时间范围（用于计算时间邻近得分）
        if time_phrase:
            t_start, t_end = self._parse_time_phrase(time_phrase, now)
            t_center = t_start + (t_end - t_start) / 2
            t_range = max((t_end - t_start).total_seconds(), 1)  # 避免除零
        else:
            t_center = None
            t_range = 1

        scored = []
        for memory_id in candidate_ids:
            # 读取记忆元数据
            row = self.conn.execute(
                'SELECT * FROM memories WHERE id = ?', (memory_id,)
            ).fetchone()
            if not row:
                continue
            # row: (id, content, content_hash, timestamp, importance, entity_json,
            #       faiss_idx, access_count, last_accessed, tags)
            col = self.conn.execute('PRAGMA table_info(memories)').fetchall()
            col_names = [c[1] for c in col]
            mem = dict(zip(col_names, row))

            # ─ 语义得分（归一化到 [0,1]）────────────────────────────
            faiss_idx = mem.get('faiss_idx')
            sim_sem = sem_score_map.get(faiss_idx, 0.0)

            # ─ 时间邻近得分 ────────────────────────────────────────
            if t_center:
                mem_ts = datetime.fromisoformat(mem['timestamp'])
                # 时间越接近查询窗口中心，得分越高；使用高斯衰减
                hours_diff = abs((mem_ts - t_center).total_seconds()) / 3600
                sim_time = np.exp(- (hours_diff ** 2) / (2 * (t_range / 3600) ** 2))
            else:
                sim_time = 1.0  # 无时间约束时给满分

            # ─ 重要性得分（归一化到 [0,1]）─────────────────────────
            importance = mem.get('importance', 0.5)  # 默认 0.5

            # ─ 综合得分 ────────────────────────────────────────────
            score = w_sem * sim_sem + w_time * sim_time + w_imp * importance

            scored.append({
                'memory_id': memory_id,
                'content': mem['content'],
                'timestamp': mem['timestamp'],
                'importance': importance,
                'score': round(score, 4),
                'breakdown': {
                    'sim_sem': round(sim_sem, 4),
                    'sim_time': round(sim_time, 4),
                    'importance': round(importance, 4),
                }
            })

        # 按综合得分降序排列，返回 Top-K
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:k]

    # ── 完整检索入口 ─────────────────────────────────────────────────
    def retrieve(self, query: str, time_phrase: str = None, k: int = 5) -> list[dict]:
        """对外暴露的检索 API"""
        now = datetime.now()
        candidate_ids, sem_results = self.generate_candidates(query, time_phrase)
        return self.fuse_rerank(candidate_ids, sem_results, time_phrase, now, k=k)
```

### 9.4 交叉编码器重排序（阶段二引入）

阶段一只用向量相似度（双塔模型），阶段二引入轻量级交叉编码器进一步提升排序精度：

```python
# 阶段二：交叉编码器重排序（可选叠加层）
# 备选模型：cross-encoder/ms-marco-MiniLM-L-6-v2（100M params，精度高于双塔）

from sentence_transformers import CrossEncoder

class CrossEncoderReranker:
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        self.reranker = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        """
        输入：候选记忆列表（已有一轮语义得分）
        输出：交叉编码器重排后的 Top-K

        cross-encoder 同时输入 query + passage，输出相关度分数（比双塔更精准但更慢）
        适用场景：候选集已缩小到 20-50 条，逐一打分开销可接受
        """
        doc_texts = [f"{query} [SEP] {c['content']}" for c in candidates]
        scores = self.reranker.predict(doc_texts)

        for c, s in zip(candidates, scores):
            c['cross_score'] = float(s)

        # 与第一阶段得分加权融合
        alpha = 0.4  # 第一阶段权重
        beta  = 0.6  # 交叉编码器权重
        for c in candidates:
            c['final_score'] = (
                alpha * c['score'] + beta * c['cross_score']
            )

        candidates.sort(key=lambda x: x['final_score'], reverse=True)
        return candidates[:top_k]
```

**何时引入交叉编码器**：
- 阶段一：跳过，Top-K=5，双塔精度足够
- 阶段二（候选集 > 100）：作为第二阶段重排序工具，Top-K 从 200→20
- 注意：交叉编码器需要 GPU 或 NPU 加速，CPU 推理约 50ms/条 × 200 = 10s（不可接受）

### 9.5 检索质量反馈闭环（代码级实现）

```python
import threading
import time

class RetrievalFeedbackLoop:
    """
    检索质量反馈闭环：
    1. 记录每次检索 query + result + user feedback
    2. 分析错误类型（漏召回 / 排序错误 / 时间错误）
    3. 自动调整权重或补充记忆
    """

    def __init__(self, feedback_db_path: str):
        self.conn = sqlite3.connect(feedback_db_path)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS retrieval_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                returned_memory_id TEXT,
                user_feedback TEXT,          -- "对" / "错（漏召回）" / "错（排序）" / "错（时间）"
                user_supplement TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                corrected_memory_id TEXT,    -- 用户纠正后的记忆 ID（如果有）
                applied BOOLEAN DEFAULT 0     -- 是否已根据反馈修正
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS weight_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dimension TEXT,              -- 'sem' / 'time' / 'imp'
                adjustment REAL,             -- 权重调整量
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    def record(self, query: str, returned_memory_ids: list[str],
               user_feedback: str, user_supplement: str = None,
               corrected_memory_id: str = None):
        """记录用户反馈"""
        for mem_id in returned_memory_ids:
            self.conn.execute('''
                INSERT INTO retrieval_feedback
                (query, returned_memory_id, user_feedback, user_supplement, corrected_memory_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (query, mem_id, user_feedback, user_supplement, corrected_memory_id))
        self.conn.commit()

    def analyze_and_adjust(self) -> dict:
        """
        分析反馈数据，自动调整检索权重

        策略：
        - 如果"漏召回"反馈多 → 提高 importance 权重（让重要记忆更容易被召回）
        - 如果"时间错误"反馈多 → 提高 time 权重
        - 如果"排序错误"反馈多 → 提高 sem 权重（信任语义相似度）
        """
        cur = self.conn.execute('''
            SELECT user_feedback, COUNT(*) as cnt
            FROM retrieval_feedback
            GROUP BY user_feedback
        ''')
        stats = {row[0]: row[1] for row in cur.fetchall()}

        adjustments = {}
        total = sum(stats.values())

        if total < 10:
            return {"status": "样本不足，等待更多反馈"}

        if stats.get("错（漏召回）", 0) / total > 0.4:
            adjustments['imp'] = +0.05
        if stats.get("错（时间）", 0) / total > 0.3:
            adjustments['time'] = +0.05
        if stats.get("错（排序）", 0) / total > 0.3:
            adjustments['sem'] = +0.05

        # 记录调整
        for dim, adj in adjustments.items():
            self.conn.execute('''
                INSERT INTO weight_adjustments (dimension, adjustment, reason)
                VALUES (?, ?, ?)
            ''', (dim, adj, f"反馈分析：{stats}"))
        self.conn.commit()

        return {
            "status": "已调整",
            "adjustments": adjustments,
            "feedback_stats": stats
        }
```

### 9.6 检索算法各阶段复杂度分析

| 阶段 | 操作 | 时间复杂度 | 空间复杂度 | 备注 |
|------|------|----------|----------|------|
| ① 时间过滤 | B-tree 范围扫描 | O(log N + K_time) | O(1) | K_time = 结果条数 |
| ② 向量检索 | FAISS HNSW 搜索 | O(log N) | O(N × D) | D=384/768d |
| ③ 候选集合并 | 集合并集 | O(K_sem + K_time) | O(K_sem + K_time) | 最多 700 条 |
| ④ 融合打分 | 遍历候选集读元数据 | O(C × 1) | O(C) | C=候选集大小 |
| ⑤ 排序 | Python sort | O(C log C) | O(C) | C ≤ 700 |
| ⑥ 交叉编码器（阶段二）| 模型推理 | O(C × M) | O(M) | M=模型参数 |
| **合计（阶段一）** | | **O(log N + C log C)** | **O(N × D)** | N=总记忆数 |

**预估延迟（阶段一，N=10万记忆条目）**：
- 步骤 ① B-tree：< 1ms
- 步骤 ② FAISS Top-200：< 5ms（HNSW）
- 步骤 ③④⑤ 融合排序：< 2ms
- **端到端：< 10ms**（不含 LLM 生成）

### 9.7 Mem0 检索 API 对接（阶段二）

Mem0 提供统一记忆检索接口，可直接替代自研两阶段融合：

```python
from mem0 import Memory

client = Memory()

# 检索记忆
results = client.search(
    query="上次说想去云南是什么时候",
    user_id="guigeng",
    limit=5,
    version="v1.1"
)
# 返回格式：
# [{'id': '...', 'memory': '...', 'score': 0.94, 'metadata': {...}}, ...]

# 写入记忆
client.add(
    memories=[{"role": "user", "content": "想去云南旅行"}],
    user_id="guigeng"
)

# 反馈修正
client.update(memory_id=results[0]['id'], content="用户纠正：实际是去桂林")
```

**Mem0 vs 自研检索选型**：

| 维度 | Mem0 OSS | 自研两阶段融合 |
|------|---------|--------------|
| 部署难度 | 低（pip install）| 中（需自建 FAISS + SQLite）|
| 定制化 | 较低（受 API 限制）| 高（完全可控）|
| 多模态（视频帧）| 需对接 RynnBrain | 原生支持 |
| 长期维护 | 依赖社区更新 | 自维护 |
| 推荐阶段 | 阶段一 MVP 快速验证 | 阶段二/三精细控制 |

---

## 10. 备份恢复流程（Backup & Restore）

> **补充章节**：原 ROBOT-SOP.md §1.2.4 记忆索引与检索 — 备份恢复完整流程
> **补充日期**：2026-04-01
> **适用范围**：阶段一 JSON 缓存 → 阶段二 SQLite 迁移 → 阶段三 PostgreSQL 升级，全阶段适用

### 10.1 备份策略总览

记忆系统包含三层数据，每层备份策略不同：

| 数据层 | 文件路径 | 备份频率 | 备份方式 | 恢复粒度 |
|--------|---------|---------|---------|---------|
| **Layer 0 原始数据** | `~/.openclaw/guigeng-memory/raw/` | 实时镜像（rsync）| 增量备份 + 每日全量 | 文件级 |
| **Layer 1 语义缓存** | `~/.openclaw/guigeng-memory/cache/semantic_cache.json` | 每小时增量 | JSON + content_hash 校验 | 条目级 |
| **FAISS 索引** | `~/.openclaw/guigeng-memory/faiss/` | 与语义缓存同步 | 索引快照（每4小时）| 索引级 |
| **Layer 3 时序数据** | `~/.openclaw/guigeng-memory/timeline/timeline.db` | 每小时增量 | SQLite `.backup` API | 记录级 |
| **配置文件** | `~/.openclaw/guigeng-memory/config.json` | 每次修改 | Git 版本控制 | 版本级 |
| **MEMORY.md** | `~/.openclaw/workspace/MEMORY.md` | 每次修改 | Git 自动提交 | 文件级 |

**备份介质原则**：
- **本地磁盘**：每日备份（自动 cron）
- **异地（NAS/外接硬盘）**：每周全量冷备份
- **云端加密**（可选）：每月归档，用 `gocryptfs` 加密后再上传

### 10.2 Layer 0 原始数据备份

```bash
#!/usr/bin/env bash
# ~/.openclaw/guigeng-memory/scripts/backup-raw.sh
# 增量备份原始数据到 NAS

SRC="/Users/lr/.openclaw/guigeng-memory/raw/"
DEST="/Volumes/NAS/guigeng-backup/raw/"
LOG="/Users/lr/.openclaw/guigeng-memory/logs/backup-raw.log"

mkdir -p "$(dirname "$LOG")"
echo "[$(date)] Starting raw backup: $SRC -> $DEST" >> "$LOG"

# rsync 增量备份，保留 30 天版本快照
rsync -avh --delete \
    --link-dest="$DEST/../latest" \
    "$SRC" "$DEST/$(date +%Y-%m-%d)/" \
    2>> "$LOG"

# 更新 latest 软链接
rm -f "$DEST/../latest"
ln -sf "$(date +%Y-%m-%d)" "$DEST/../latest"

echo "[$(date)] Raw backup complete" >> "$LOG"
```

### 10.3 Layer 1 语义缓存备份（JSON + FAISS）

```python
#!/usr/bin/env python3
# backup_semantic.py
# 备份语义缓存 JSON + FAISS 索引，带 content_hash 完整性校验

import json
import shutil
import hashlib
import gzip
from datetime import datetime
from pathlib import Path

BACKUP_ROOT = Path("/Volumes/NAS/guigeng-backup/semantic/")
CACHE_PATH  = Path("~/.openclaw/guigeng-memory/cache/").expanduser()
FAISS_PATH  = Path("~/.openclaw/guigeng-memory/faiss/").expanduser()

def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def backup_semantic_cache():
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = BACKUP_ROOT / ts
    backup_dir.mkdir(parents=True, exist_ok=True)

    # ── 备份 semantic_cache.json ────────────────────────────────────
    cache_file = CACHE_PATH / "semantic_cache.json"
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            cache = json.load(f)

        # 完整性校验：每条 entry 的 content_hash 验证
        errors = []
        for entry in cache.get("entries", []):
            computed = content_hash(entry["content"])
            if computed != entry.get("content_hash"):
                errors.append(f"Hash mismatch for {entry['entry_id']}")

        if errors:
            print(f"⚠️  WARNING: {len(errors)} hash errors detected")
            # 写入错误报告
            with open(backup_dir / "hash_errors.json", 'w') as ef:
                json.dump(errors, ef, ensure_ascii=False)

        # 压缩备份
        with gzip.open(backup_dir / "semantic_cache.json.gz", 'wt', compresslevel=6) as zf:
            json.dump(cache, zf, ensure_ascii=False)

        # 写入元信息
        meta = {
            "timestamp": ts,
            "total_entries": cache.get("total_entries", 0),
            "hash_errors": len(errors),
            "model_name": cache.get("model_name", "unknown"),
            "version": cache.get("cache_version", "unknown")
        }
        with open(backup_dir / "meta.json", 'w') as mf:
            json.dump(meta, mf, ensure_ascii=False)

        print(f"✅ Semantic cache backed up: {cache['total_entries']} entries, {len(errors)} hash errors")

    # ── 备份 FAISS 索引 ────────────────────────────────────────────
    for idx_file in FAISS_PATH.glob("*.seqs"):
        shutil.copy2(idx_file, backup_dir / idx_file.name)
        print(f"✅ FAISS index backed up: {idx_file.name}")

    print(f"Backup complete: {backup_dir}")

if __name__ == "__main__":
    backup_semantic_cache()
```

### 10.4 Layer 3 SQLite 时序数据库备份

```python
#!/usr/bin/env python3
# backup_timeline.py
# 使用 SQLite 内置 backup API 实现热备份（不影响写入）

import sqlite3
import gzip
import shutil
from datetime import datetime
from pathlib import Path

BACKUP_ROOT = Path("/Volumes/NAS/guigeng-backup/timeline/")
DB_PATH     = Path("~/.openclaw/guigeng-memory/timeline/timeline.db").expanduser()

def backup_timeline():
    ts = datetime.now().strftime("%Y%m-%d-%H%M%S")
    backup_dir = BACKUP_ROOT / ts
    backup_dir.mkdir(parents=True, exist_ok=True)

    # SQLite 热备份 API（在线备份，不锁库）
    dest_db = backup_dir / "timeline.db"
    with sqlite3.connect(DB_PATH) as src, \
         sqlite3.connect(dest_db) as dst:
        src.backup(dst)

    # 压缩
    with open(dest_db, 'rb') as f_in, \
         gzip.open(backup_dir / "timeline.db.gz", 'wb', compresslevel=6) as f_out:
        shutil.copyfileobj(f_in, f_out)
    dest_db.unlink()  # 删除未压缩副本

    # 记录备份信息
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM memories")
        mem_count = cur.fetchone()[0]
        cur = conn.execute("SELECT MAX(timestamp) FROM memories")
        latest = cur.fetchone()[0]

    meta = {
        "timestamp": ts,
        "memory_count": mem_count,
        "latest_entry": latest,
        "db_size_bytes": DB_PATH.stat().st_size
    }
    with open(backup_dir / "meta.json", 'w') as mf:
        json.dump(meta, open(backup_dir / "meta.json", 'w'), ensure_ascii=False)

    print(f"✅ Timeline backed up: {mem_count} memories, latest={latest}")
    return backup_dir

if __name__ == "__main__":
    import json as _json
    backup_timeline()
```

### 10.5 定时备份 Cron 配置

```bash
# ~/.openclaw/guigeng-memory/scripts/setup-backup-cron.sh
# 添加到 crontab，每日自动执行

cat << 'CRON' | crontab -
# 贵庚记忆系统备份任务
# 每小时：语义缓存 + Timeline 增量
0 * * * * /usr/bin/python3 ~/.openclaw/guigeng-memory/scripts/backup_semantic.py >> ~/.openclaw/guigeng-memory/logs/backup-semantic.log 2>&1
5 * * * * /usr/bin/python3 ~/.openclaw/guigeng-memory/scripts/backup_timeline.py >> ~/.openclaw/guigeng-memory/logs/backup-timeline.log 2>&1

# 每日 03:00：全量 raw 数据 rsync 备份
0 3 * * * /usr/bin/bash ~/.openclaw/guigeng-memory/scripts/backup-raw.sh

# 每周日 04:00：清理超过 30 天的备份快照
0 4 * * 0 /usr/bin/find /Volumes/NAS/guigeng-backup/ -maxdepth 2 -type d -mtime +30 -exec rm -rf {} + 2>/dev/null
CRON

echo "Backup cron installed"
```

### 10.6 完整恢复流程

#### 10.6.1 全量恢复（灾难性故障）

```python
#!/usr/bin/env python3
# restore_full.py
# 从最新备份全量恢复贵庚记忆系统

import json
import gzip
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

BACKUP_ROOT  = Path("/Volumes/NAS/guigeng-backup/")
MEMORY_ROOT  = Path("~/.openclaw/guigeng-memory/").expanduser()

def restore_full(backup_ts: str = None):
    """
    全量恢复
    backup_ts: 备份时间戳，如 "2026-04-01-030000"，None = 最新
    """
    # 找到指定或最新备份
    if backup_ts is None:
        backups = sorted((BACKUP_ROOT / "semantic").glob("*"))
        backup_ts = backups[-1].name
        print(f"Using latest backup: {backup_ts}")

    sem_backup = BACKUP_ROOT / "semantic" / backup_ts
    tl_backup  = BACKUP_ROOT / "timeline" / backup_ts

    # ── 完整性校验 ────────────────────────────────────────────────
    for subdir in [sem_backup, tl_backup]:
        meta_file = subdir / "meta.json"
        if not meta_file.exists():
            print(f"⚠️  No meta.json in {subdir}")
            continue
        meta = json.loads(meta_file.read_text())
        print(f"  Backup info: {meta}")

    # ── 恢复 semantic_cache.json ──────────────────────────────────
    cache_gz = sem_backup / "semantic_cache.json.gz"
    if cache_gz.exists():
        with gzip.open(cache_gz, 'rt') as f:
            cache = json.load(f)

        # 再次校验 hash
        import hashlib
        errors = 0
        for entry in cache.get("entries", []):
            computed = hashlib.sha256(entry["content"].encode()).hexdigest()
            if computed != entry.get("content_hash"):
                errors += 1

        if errors:
            print(f"⚠️  Hash validation FAILED: {errors} errors — aborting restore")
            return False

        dest = MEMORY_ROOT / "cache" / "semantic_cache.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'w') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        print(f"✅ semantic_cache.json restored: {cache['total_entries']} entries")

    # ── 恢复 FAISS 索引 ────────────────────────────────────────────
    for idx_file in sem_backup.glob("*.seqs"):
        dest = MEMORY_ROOT / "faiss" / idx_file.name
        shutil.copy2(idx_file, dest)
        print(f"✅ FAISS index restored: {idx_file.name}")

    # ── 恢复 timeline.db ────────────────────────────────────────────
    tl_gz = tl_backup / "timeline.db.gz"
    if tl_gz.exists():
        dest = MEMORY_ROOT / "timeline" / "timeline.db"
        with gzip.open(tl_gz, 'rb') as f_in, open(dest, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        print(f"✅ timeline.db restored")

    print(f"\n✅ Full restore complete from {backup_ts}")
    return True

if __name__ == "__main__":
    import sys
    ts = sys.argv[1] if len(sys.argv) > 1 else None
    restore_full(ts)
```

#### 10.6.2 条目级选择性恢复

```python
#!/usr/bin/env python3
# restore_entry.py
# 根据 entry_id 或 content_hash 选择性恢复单条记忆

import json
import gzip
import sqlite3
import hashlib
from pathlib import Path

BACKUP_ROOT = Path("/Volumes/NAS/guigeng-backup/semantic/")

def restore_entry(entry_id: str = None, content_hash: str = None):
    """
    条目级恢复：给定 entry_id 或 content_hash，从备份中找到并恢复该记忆
    """
    assert entry_id or content_hash, "Must provide entry_id or content_hash"

    # 从所有备份中搜索
    backups = sorted(BACKUP_ROOT.glob("*"))
    found = None
    found_in_backup = None

    for backup_dir in reversed(backups):
        cache_gz = backup_dir / "semantic_cache.json.gz"
        if not cache_gz.exists():
            continue
        with gzip.open(cache_gz, 'rt') as f:
            cache = json.load(f)

        for entry in cache.get("entries", []):
            if entry_id and entry["entry_id"] == entry_id:
                found = entry
                found_in_backup = backup_dir.name
                break
            if content_hash and hashlib.sha256(entry["content"].encode()).hexdigest() == content_hash:
                found = entry
                found_in_backup = backup_dir.name
                break
        if found:
            break

    if not found:
        print(f"❌ Entry not found: id={entry_id}, hash={content_hash}")
        return False

    print(f"Found entry in backup {found_in_backup}:")
    print(f"  content: {found['content'][:80]}...")
    print(f"  timestamp: {found['timestamp']}")
    print(f"  importance: {found['importance']}")

    # 追加写入当前 semantic_cache.json（不去重，保留历史版本）
    current_cache = MEMORY_ROOT / "cache" / "semantic_cache.json"
    if current_cache.exists():
        with open(current_cache, 'r') as f:
            cache = json.load(f)
    else:
        cache = {"cache_version": "1.0", "model_name": "unknown", "total_entries": 0, "entries": []}

    # 如果当前已有该 entry_id，覆盖；否则追加
    existing_ids = {e["entry_id"] for e in cache["entries"]}
    if found["entry_id"] in existing_ids:
        for i, e in enumerate(cache["entries"]):
            if e["entry_id"] == found["entry_id"]:
                cache["entries"][i] = found
                break
    else:
        cache["entries"].append(found)

    cache["total_entries"] = len(cache["entries"])

    with open(current_cache, 'w') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"✅ Entry restored and appended to current cache")
    return True
```

### 10.7 跨阶段迁移（JSON → SQLite → PostgreSQL）

```python
#!/usr/bin/env python3
# migrate_memory.py
# 阶段一 JSON → 阶段二 SQLite → 阶段三 PostgreSQL 数据迁移脚本

import json
import sqlite3
import hashlib
from datetime import datetime

def migrate_json_to_sqlite(json_path: str, db_path: str):
    """阶段一 → 阶段二：JSON 迁移到 SQLite"""
    print(f"Migrating {json_path} -> {db_path}")

    with open(json_path, 'r') as f:
        cache = json.load(f)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 创建表结构
    cur.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            content_hash TEXT UNIQUE,
            timestamp TEXT,
            importance REAL DEFAULT 0.5,
            entity_json TEXT,
            faiss_idx INTEGER,
            access_count INTEGER DEFAULT 0,
            last_accessed TEXT,
            tags TEXT,
            migrated_at TEXT,
            raw_entry TEXT
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)')

    migrated = 0
    errors = 0
    for entry in cache.get("entries", []):
        try:
            # 校验 hash
            computed = hashlib.sha256(entry["content"].encode()).hexdigest()
            if computed != entry.get("content_hash"):
                print(f"  ⚠️ Hash mismatch for {entry['entry_id']}")
                errors += 1

            cur.execute('''
                INSERT OR REPLACE INTO memories
                (id, content, content_hash, timestamp, importance,
                 entity_json, faiss_idx, access_count, last_accessed,
                 migrated_at, raw_entry)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry["entry_id"],
                entry["content"],
                entry.get("content_hash", computed),
                entry.get("timestamp"),
                entry.get("importance", 0.5),
                json.dumps(entry.get("entities", [])),
                None,  # faiss_idx 需重建
                entry.get("access_count", 0),
                entry.get("last_accessed"),
                datetime.now().isoformat(),
                json.dumps(entry)
            ))
            migrated += 1
        except Exception as e:
            print(f"  ❌ Error migrating {entry.get('entry_id')}: {e}")
            errors += 1

    conn.commit()
    conn.close()
    print(f"\n✅ Migration complete: {migrated} entries migrated, {errors} errors")

    # 生成 FAISS 重建批注
    with open(db_path + ".rebuild_faiss.txt", 'w') as f:
        f.write(f"# FAISS rebuild needed after JSON->SQLite migration\n")
        f.write(f"# Migrated at: {datetime.now().isoformat()}\n")
        f.write(f"# Total entries: {migrated}\n")
        f.write(f"# Errors: {errors}\n")
    print("⚠️  Note: Run FAISS rebuild after migration to update vector indices")

def migrate_sqlite_to_postgresql(sqlite_db: str, pg_dsn: str):
    """阶段二 → 阶段三：SQLite 迁移到 PostgreSQL（pgvector）"""
    import psycopg2

    sqlite_conn = sqlite3.connect(sqlite_db)
    pg_conn = psycopg2.connect(dsn)

    # PostgreSQL 建表
    with pg_conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                content_hash TEXT UNIQUE,
                timestamp TIMESTAMP,
                importance REAL DEFAULT 0.5,
                entity_json JSONB,
                faiss_idx INTEGER,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                tags TEXT[],
                migrated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_pg_timestamp ON memories(timestamp)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_pg_importance ON memories(importance DESC)')

        # pgvector 字段（需要单独 ALTER TABLE 添加）
        cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
        cur.execute('''
            ALTER TABLE memories ADD COLUMN IF NOT EXISTS embedding vector(384)
        ''')

    # 迁移数据
    cur = sqlite_conn.execute('SELECT * FROM memories')
    rows = cur.fetchall()

    for row in rows:
        pg_conn.execute('''
            INSERT INTO memories (id, content, content_hash, timestamp, importance,
                                 entity_json, faiss_idx, access_count, last_accessed, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content
        ''', row[:10])  # 10 个字段匹配

    pg_conn.commit()
    sqlite_conn.close()
    pg_conn.close()
    print(f"✅ PostgreSQL migration complete: {len(rows)} rows transferred")
```

### 10.8 数据完整性校验（备份验证自动化）

```python
#!/usr/bin/env python3
# verify_backup.py
# 备份完成后自动验证完整性，不合格时告警

import json
import gzip
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

BACKUP_ROOT = Path("/Volumes/NAS/guigeng-backup/")

def verify_backup(backup_ts: str) -> dict:
    """验证指定备份的完整性，返回校验报告"""
    report = {
        "backup_ts": backup_ts,
        "timestamp": datetime.now().isoformat(),
        "checks": [],
        "passed": True
    }

    sem_backup = BACKUP_ROOT / "semantic" / backup_ts
    tl_backup  = BACKUP_ROOT / "timeline" / backup_ts

    # ── 检查1：meta.json 存在 ────────────────────────────────────
    for subdir, name in [(sem_backup, "semantic"), (tl_backup, "timeline")]:
        meta = subdir / "meta.json"
        if not meta.exists():
            report["checks"].append({"check": f"{name}_meta", "status": "FAIL", "detail": "meta.json missing"})
            report["passed"] = False
        else:
            report["checks"].append({"check": f"{name}_meta", "status": "PASS"})

    # ── 检查2：semantic_cache.json.gz 解压正常 ──────────────────
    cache_gz = sem_backup / "semantic_cache.json.gz"
    if cache_gz.exists():
        try:
            with gzip.open(cache_gz, 'rt') as f:
                cache = json.load(f)
            # hash 校验
            errors = 0
            for entry in cache.get("entries", []):
                computed = hashlib.sha256(entry["content"].encode()).hexdigest()
                if computed != entry.get("content_hash"):
                    errors += 1
            report["checks"].append({
                "check": "semantic_hash_integrity",
                "status": "PASS" if errors == 0 else "FAIL",
                "detail": f"{errors} hash errors in {cache['total_entries']} entries"
            })
            if errors > 0:
                report["passed"] = False
        except Exception as e:
            report["checks"].append({"check": "semantic_decompress", "status": "FAIL", "detail": str(e)})
            report["passed"] = False

    # ── 检查3：timeline.db.gz 解压后 SQLite 完整性 ──────────────
    tl_gz = tl_backup / "timeline.db.gz"
    if tl_gz.exists():
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
                with gzip.open(tl_gz, 'rb') as f_in:
                    f_in.readinto(tmp)
                tmp_path = tmp.name
            conn = sqlite3.connect(tmp_path)
            cur = conn.execute("SELECT COUNT(*) FROM memories")
            count = cur.fetchone()[0]
            cur = conn.execute("PRAGMA integrity_check")
            integrity = cur.fetchone()[0]
            conn.close()
            Path(tmp_path).unlink()

            status = "PASS" if integrity == "ok" else "FAIL"
            report["checks"].append({
                "check": "timeline_integrity",
                "status": status,
                "detail": f"{count} rows, integrity={integrity}"
            })
            if status == "FAIL":
                report["passed"] = False
        except Exception as e:
            report["checks"].append({"check": "timeline_db", "status": "FAIL", "detail": str(e)})
            report["passed"] = False

    # ── 告警：不合格时发飞书消息 ────────────────────────────────
    if not report["passed"]:
        alert_msg = f"⚠️ 贵庚记忆备份校验失败\n备份时间：{backup_ts}\n{json.dumps(report['checks'], ensure_ascii=False, indent=2)}"
        print(alert_msg)
        # TODO: 接入飞书告警（feishu message tool）

    return report

if __name__ == "__main__":
    import sys
    ts = sys.argv[1] if len(sys.argv) > 1 else None
    if ts is None:
        backups = sorted((BACKUP_ROOT / "semantic").glob("*"))
        ts = backups[-1].name if backups else None
    if ts:
        result = verify_backup(ts)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("No backup found")
```

### 10.9 备份恢复流程总结

| 场景 | 恢复方式 | 预计时间 | 数据损失 |
|------|---------|---------|---------|
| 误删单条记忆 | `restore_entry.py` 条目级恢复 | < 1 分钟 | 最小（仅丢失该条）|
| 语义索引损坏 | 重新 `python3 backup_semantic.py` 覆盖恢复 | < 5 分钟 | 最近一次备份间隔 |
| SQLite 时序库损坏 | `restore_full.py` 全量恢复 | < 10 分钟 | 最近一次备份间隔 |
| 灾难性丢失（全盘故障）| NAS 全量恢复 + rsync | 数小时 | 每日备份间隔 |
| 阶段升级（JSON→SQLite）| `migrate_memory.py` | 视数据量 | 无（双写过渡期）|

**关键原则**：
- Layer 0 原始数据：永远不删除，只新增备份
- Layer 1/3 缓存：每小时增量，每天全量，保留 30 天
- 每次备份后自动运行 `verify_backup.py`，不合格立即告警
- 跨阶段迁移前先在测试目录验证，确认无误再切换生产路径

---

## 10. 隐私加密方案（补充章节）

> **补充章节**：原 ROBOT-SOP.md §1.2.4 记忆架构 — 隐私加密方案
> **补充日期**：2026-04-01
> **补充内容**：威胁模型 + 静态加密 + 密钥管理 + 访问控制 + 各阶段实施路径
> **核心问题**：Windows Recall 的 VBS Enclave + TPM 密钥保护让贵庚的 NAS 存储安全显得过于简陋——本节填补这一空白。

---

### 10.1 威胁模型分析

#### 1.1 资产定义

贵庚记忆系统涉及的核心资产：

| 资产类型 | 示例 | 敏感等级 |
|---------|------|---------|
| 原始对话文本 | 用户与贵庚的聊天记录 | 🔴 极高（私密对话、情感表达）|
| 语音转写文本 | 7×24 语音采集的转录 | 🔴 极高 |
| 视频关键帧 / 全量视频 | RynnBrain 标注后的视频数据 | 🔴 极高（包含场景、人员、行为）|
| 实体关系图谱 | 人物关系、地点轨迹、事件因果 | 🟠 高（可推断用户生活习惯）|
| 向量 embedding | 语义索引数据 | 🟡 中（可推断话题偏好）|
| 记忆重要性权重 | 边权重实例型模型参数 | 🟡 中（反映用户价值判断）|

#### 1.2 威胁向量分析

| 威胁向量 | 攻击场景 | 对应风险 |
|---------|---------|---------|
| **物理盗窃** | NAS/硬盘被偷，攻击者直接读取存储介质 | 静态数据泄露 |
| **同设备其他用户** | 家人/室友共用一台 Mac/NAS，能接触文件系统 | 横向越权访问 |
| **恶意软件** | macOS/路由器被入侵，恶意进程读取记忆文件 | 运行时数据窃取 |
| **网络窃听** | 传输过程中（Mac ↔ NAS）数据被抓包 | 传输层泄露 |
| **管理员滥用** | IT 管理员或服务商后台人员访问数据 | 内部人员威胁 |
| **继承人风险** | 继承设备时，继承人获得全部记忆数据 | 隐私边界模糊 |

> ⚠️ **对比 Recall**：Windows Recall 假设设备所有者是合法用户，通过 VBS Enclave 将数据与设备管理员/其他用户隔离。贵庚的威胁模型更复杂——**同住一室的人既是物理接触者，也是潜在隐私侵犯者**，不能简单套用 Recall 的安全设计。

---

### 10.2 静态数据加密（At-Rest Encryption）

#### 2.1 加密层级设计

贵庚采用**四级加密**架构，层层递进：

```
┌─────────────────────────────────────────────────┐
│  Layer A：全盘加密（防物理盗窃）                  │
│  - NAS: LUKS2 全盘加密（离线状态数据保护）        │
│  - Mac: FileVault 2（APFS 加密）                 │
└─────────────────────────────────────────────────┘
         ↓ 突破全盘加密后
┌─────────────────────────────────────────────────┐
│  Layer B：文件级加密（防同设备用户横向访问）       │
│  - 记忆数据库加密（SQLite with SQLCipher）       │
│  - 向量索引文件加密（独立加密层）                │
│  - JSON 记忆缓存加密（aespipe /age）             │
└─────────────────────────────────────────────────┘
         ↓ 突破文件级加密后（内存中）
┌─────────────────────────────────────────────────┐
│  Layer C：运行时内存加密（防恶意软件）            │
│  - 敏感字段（如人脸特征向量）单独加密存内存       │
│  - 进程隔离：记忆服务独立于主对话进程             │
│  - 访问令牌 + 临时密钥，进程退出后自动失效        │
└─────────────────────────────────────────────────┘
         ↓ 解密后使用
┌─────────────────────────────────────────────────┐
│  Layer D：敏感字段级加密（防内部人员滥用）        │
│  - 人脸特征向量、精确位置、可推断身份的信息       │
│  - 单独加密，需二次认证才能解密查看              │
└─────────────────────────────────────────────────┘
```

#### 2.2 全盘加密方案对比

| 方案 | 适用平台 | 密钥来源 | 启动体验 | 密钥泄露风险 |
|------|---------|---------|---------|------------|
| **FileVault 2** | macOS | Apple T2 / M-series Secure Enclave | 自动解锁（已登录用户）| 低（硬件绑定）|
| **LUKS2** | Linux NAS | TPM 2.0 或密码 | 启动时输入密码 | 中（密码可被肩窥）|
| **dm-crypt** | Linux | TPM 或软件 | 密码或密钥文件 | 中 |
| **BestCrypt/ VeraCrypt** | 跨平台 | 密码 + 密钥文件 | 手动挂载 | 低（双因素）|
| **age 加密** | 跨平台（文件级）| SSH 私钥或密码 | 自动（无守护进程）| 低（可配合 gpg-agent）|

**阶段一推荐**：macOS FileVault 2（已有，无需额外配置）+ `age` 做文件级加密
**阶段二推荐**：NAS 使用 LUKS2 + TPM 2.0 自动解锁（无密码泄露风险）

#### 2.3 文件级加密实现（age + SSH）

`age` 是现代文件加密工具（Go 实现，100% 本地，无网络依赖），比 GPG 更适合自动化场景：

```bash
# 安装 age（macOS）
brew install age

# 生成加密密钥（一次性）
age-keygen -o ~/.config/guigeng/memory.key

# 加密记忆文件（静态加密，磁盘上始终是密文）
age -r <公钥> -o memory.db.age memory.db

# 解密读取（内存中解密，不落盘明文）
age -d -i ~/.config/guigeng/memory.key -o memory.db memory.db.age
```

```python
# Python 集成（pycleid 或调用 age CLI）
import subprocess
import os

class AgeEncryptedStore:
    """记忆文件加密存储，支持自动解密"""
    KEY_PATH = os.path.expanduser("~/.config/guigeng/memory.key")
    CACHE_DIR = os.path.expanduser("~/.cache/guigeng/")

    def __init__(self, encrypted_path: str):
        self.encrypted_path = encrypted_path
        self._decrypted = None

    def _decrypt(self) -> bytes:
        """解密到内存，不落盘明文"""
        result = subprocess.run(
            ["age", "-d", "-i", self.KEY_PATH, "-o", "-", self.encrypted_path],
            capture_output=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"age decrypt failed: {result.stderr.decode()}")
        return result.stdout

    def read(self) -> dict:
        """读取并解析记忆（自动解密）"""
        import json
        decrypted = self._decrypt()
        return json.loads(decrypted)

    def write(self, data: dict):
        """加密写入（原子操作，防止中间状态泄露）"""
        import json, tempfile, os
        # 先写到临时文件（原子 rename）
        tmp = tempfile.NamedTemporaryFile(
            mode='w', dir=self.CACHE_DIR, delete=False, suffix='.tmp'
        )
        json.dump(data, tmp)
        tmp.close()
        # 加密覆盖原文件
        age_key = os.environ.get("AGE_KEY") or self.KEY_PATH
        subprocess.run(
            ["age", "-r", self._get_public_key(), "-o",
             self.encrypted_path + ".new",
             tmp.name],
            check=True
        )
        os.replace(self.encrypted_path + ".new", self.encrypted_path)
        os.unlink(tmp.name)
```

#### 2.4 SQLite 加密（SQLCipher）

阶段二 SQLite 迁移后，使用 SQLCipher 替代标准 SQLite：

```bash
# macOS 安装 SQLCipher
brew install sqlcipher
# 编译 Python 绑定
pip install SQLCipher

# 连接加密数据库
SQL_PASSWORD=$(age -d -i ~/.config/guigeng/memory.key ~/.config/guigeng/sqlite.key.age)
python3 -c "
import sqlite3
conn = sqlite3.connect('file:guigeng.db?cipher=sqlcipher&kdf_iter=256000&fast_kdf=1&hmac_algorithm=SHA256&cipher=AES-256-CBC',
                       uri=True,
                       conn=conn)
conn.execute(f\"PRAGMA key = '{os.environ['SQL_PASSWORD']}'\")
"
```

---

### 10.3 密钥管理方案

#### 3.1 密钥层级架构

```
                    ┌──────────────────┐
                    │  主密钥 MK       │  （从不存储，只存在于内存/硬件中）
                    │  age-256-GCM     │
                    └────────┬─────────┘
                             │ 派生
              ┌──────────────┼──────────────┐
              ↓              ↓              ↓
     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
     │ KEK 文件密钥│ │ KEK 数据库密钥│ │ KEK 权重密钥 │
     │ (文件加密)  │ │ (SQLCipher) │ │ (模型权重)  │
     └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
            │               │               │
            ↓               ↓               ↓
    存储在 Keychain    存储在 Keychain   存储在 Keychain
    (macOS Secure      (macOS Secure    (TPM 绑定，
     Enclave 绑定)      Enclave 绑定)    如果可用)
```

#### 3.2 macOS Keychain + Secure Enclave 方案（阶段一）

macOS 的 Keychain 服务自动将密钥受限于 T2 / Apple Silicon Secure Enclave：

```python
import keyring
import os

# 主密钥存储在 Keychain，受 Secure Enclave 保护
SERVICE_NAME = "com.guigeng.memory"

def store_master_key():
    """首次设置时生成并安全存储主密钥"""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    import secrets

    # 生成随机主密钥
    master_key = secrets.token_bytes(32)  # 256-bit

    # 用用户登录密码派生 KEK（不直接存储 MK）
    user_password = os.environ.get("GUIGENG_PASSWORD")  # 首次设置时用户输入
    if not user_password:
        raise RuntimeError("需要设置 GUIGENG_PASSWORD 环境变量")

    kdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"guigeng-memory-kek",
        info=b"master-key-derivation",
    )
    kek = kdf.derive(user_password.encode())

    # KEK 存入 Keychain（Secure Enclave 绑定，用户解锁后可用）
    keyring.set_password(SERVICE_NAME, "kek", kek.hex())

    # 用 KEK 加密主密钥，存入文件
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(kek)
    encrypted_mk = aesgcm.encrypt(b"guigeng-memory-iv", master_key, None)

    with open(os.path.expanduser("~/.config/guigeng/master_key.age"), "wb") as f:
        f.write(encrypted_mk)

    return master_key  # 仅首次返回，之后不存储

def get_master_key() -> bytes:
    """运行时获取主密钥（需用户认证）"""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import keyring

    kek_hex = keyring.get_password(SERVICE_NAME, "kek")
    if not kek_hex:
        raise RuntimeError("未初始化，请先运行 store_master_key()")
    kek = bytes.fromhex(kek_hex)

    with open(os.path.expanduser("~/.config/guigeng/master_key.age"), "rb") as f:
        encrypted_mk = f.read()

    aesgcm = AESGCM(kek)
    return aesgcm.decrypt(encrypted_mk[:12], encrypted_mk[12:], None)  # iv=前12字节
```

#### 3.3 TPM 2.0 方案（阶段二，NAS/Linux）

NAS 部署使用 TPM 2.0 做硬件级密钥保护：

```bash
# 检查 TPM 设备
ls /dev/tpm0  # Linux TPM 设备节点

# 使用 TPM2-Tools 管理密钥
tpm2_createprimary -C o -g sha256 -G ek -c ek.ctx
tpm2_create -G aes256 -u key.pub -r key.priv -C ek.ctx
tpm2_load -C ek.ctx -u key.pub -r key.priv -c key.ctx

# 用 TPM 保护的密钥加密 LUKS
cryptsetup luksAddKey /dev/sda1 --key-file=- <<< $(tpm2_unseal -c key.ctx)
```

#### 3.4 密钥轮换策略

| 密钥类型 | 轮换频率 | 轮换方式 | 数据迁移 |
|---------|---------|---------|---------|
| 主密钥 MK | 每年或设备丢失时 | 重加密所有数据 | 增量重加密 |
| KEK | 每季度 | 重新派生 | 用新 KEK 重加密 MK |
| 临时会话密钥 | 每次会话 | 随机生成，会话结束销毁 | 不需要（不持久化）|
| age 文件密钥 | 每年或 KEK 轮换时 | 用新 KEK 重新加密 | 批量重加密脚本 |

```python
# 密钥轮换脚本（每年执行一次）
def rotate_encryption_keys(old_kek: str, new_kek: str, data_dir: str):
    """
    用新 KEK 重新加密所有记忆数据
    警告：此操作不可中断，需备份
    """
    import glob, age, shutil
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    public_key = age.public_key_from_file(new_kek + ".pub")
    files = glob.glob(f"{data_dir}/**/*.age", recursive=True)

    for f in files:
        # 1. 解密
        with open(f, "rb") as fp:
            plaintext = age.decrypt(open(old_kek + ".key").read(), fp.read())
        # 2. 用新密钥重新加密
        encrypted = age.encrypt(public_key, plaintext)
        with open(f + ".new", "wb") as fp:
            fp.write(encrypted)
        os.replace(f + ".new", f)
```

---

### 10.4 访问控制设计

#### 4.1 多用户访问控制模型

**问题**：贵庚的记忆数据在同一台 Mac/NAS 上，贵庚本人（用户）和家人可能共用设备。

**解决思路**：区分"设备使用者"和"记忆所有者"，用认证层隔离：

```
┌────────────────────────────────────────────┐
│           设备物理层（FileVault/LUKS）       │
│    设备管理员密码 = 设备使用权限 ≠ 记忆权限   │
└────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────┐
│           认证层（生物识别 / PIN）           │
│    Face ID / Touch ID / 专属 PIN            │
│    = 记忆访问权限                            │
└────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────┐
│           记忆加密层（始终加密存盘）          │
│    解密后的数据仅在认证用户的内存中存在        │
└────────────────────────────────────────────┘
```

#### 4.2 认证流程实现

```python
import os, hashlib, hmac
from pathlib import Path

CONFIG_DIR = Path("~/.config/guigeng").expanduser()
PASSWD_FILE = CONFIG_DIR / "auth.saltpepper"
pepper_salt = b"guigeng-memory-pepper-v1"  # 服务端盐，存储在代码外

class GuigengAuth:
    """
    记忆访问认证：区分"设备使用"和"记忆访问"
    策略：即使设备有其他人使用，记忆数据也需要额外认证才能访问
    """
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # 5分钟

    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def setup(self, password: str):
        """首次设置：存储密码盐"""
        import secrets
        salt = secrets.token_bytes(32)
        stored = self._hash(password, salt)
        with open(PASSWD_FILE, "wb") as f:
            f.write(salt + stored)
        # 同时初始化 Keychain KEK
        self._init_keychain_kek(password)

    def authenticate(self, password: str) -> bool:
        """验证密码，返回是否通过"""
        if not PASSWD_FILE.exists():
            raise RuntimeError("未设置认证密码")

        with open(PASSWD_FILE, "rb") as f:
            salt = f.read(32)
            stored = f.read()

        if self._hash(password, salt) == stored:
            self._clear_lockout()
            return True

        self._record_failed_attempt()
        return False

    def _hash(self, password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            'sha512', password.encode(), salt + pepper_salt, 600000, dklen=64
        )

    def _init_keychain_kek(self, password: str):
        """用认证密码派生 KEK，存入 Keychain（Secure Enclave）"""
        import keyring
        salt = b"guigeng-kek-salt-v1"
        kek = hashlib.pbkdf2_hmac(
            'sha256', password.encode(), salt, 100000, dklen=32
        )
        keyring.set_password("com.guigeng.memory", "kek", kek.hex())

    def _record_failed_attempt(self):
        """失败计数，达到阈值后锁定"""
        lockout_file = CONFIG_DIR / "lockout"
        attempts = 0
        if lockout_file.exists():
            attempts = int(lockout_file.read_text().strip())
        attempts += 1
        lockout_file.write_text(str(attempts))
        if attempts >= self.MAX_ATTEMPTS:
            lockout_file.write_text(f"{attempts},{__import__('time').time()}")

    def _clear_lockout(self):
        lockout_file = CONFIG_DIR / "lockout"
        if lockout_file.exists():
            lockout_file.unlink()
```

#### 4.3 敏感字段二次认证

**场景**：查看"人脸特征"、"精确位置"等高敏感字段时，需要额外的生物认证：

```python
import os, subprocess

class SensitiveFieldAccess:
    """
    高敏感字段的二次认证：
    - 人脸特征向量
    - 精确 GPS 坐标
    - 私密对话标记
    - 第三方隐私内容（涉及他人）
    """
    SENSITIVE_FIELDS = {"face_embedding", "gps_exact", "third_party_content"}

    def access(self, field_name: str, encrypted_value: bytes) -> bytes:
        if field_name not in self.SENSITIVE_FIELDS:
            return encrypted_value  # 不需要二次认证

        # macOS 生物认证
        result = subprocess.run(
            ["security", "authorizationdb", "read", "system.evaluation.usage"],
            capture_output=True
        )
        # 使用 Touch ID / Face ID 做二次认证
        # 这里用简化的 PIN 验证演示，实际部署用 LocalAuthentication.framework
        result = subprocess.run(
            ["osascript", "-e",
             'display dialog "查看敏感记忆需要额外认证" '
             'default answer "" buttons {"取消", "确认"} '
             'default button 2 with hidden answer'],
            capture_output=True
        )
        if result.returncode != 0:
            raise PermissionError("二次认证失败")

        # 认证通过，解密敏感字段
        return self._decrypt(encrypted_value)
```

---

### 10.5 传输加密（In-Transit）

#### 5.1 Mac ↔ NAS 数据传输加密

```
阶段一（当前）：本地存储，Mac 和 NAS 在同一局域网
  → 无需额外传输加密（局域网内物理安全）

阶段二（远程访问）：通过tailscale/vpn 访问 NAS
  → WireGuard VPN 隧道（内置加密）

阶段三（多设备同步）：设备间 P2P 同步
  → age 加密内容 + WebRTC DTLS 传输
  → Signal Protocol（如果引入消息同步）
```

```bash
# tailscale 查看连接（已自动加密）
tailscale status

# age 加密后通过 tailscale P2P 传输
age -r <recipient_public_key> -o - memory_backup.json | \
  nc -N <nas-ip> 7777
```

#### 5.2 备份加密流程

```python
class EncryptedBackup:
    """加密备份到异地（冷存储）"""
    def __init__(self, backup_public_key: str):
        import age
        self.recipient = age.PublicKey.from_string(backup_public_key)

    def backup(self, memory_dir: str, backup_path: str):
        """
        备份流程：
        1. 将记忆目录打包（tar）
        2. 用 age 加密打包文件
        3. 写入备份路径
        """
        import tarfile, age, io
        # 打包目录（流式处理，不落盘）
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            tar.add(memory_dir, arcname="guigeng-memory")
        tar_buffer.seek(0)

        # age 加密
        encrypted = age.encrypt(self.recipient, tar_buffer.read())

        # 写入备份
        with open(backup_path, "wb") as f:
            f.write(encrypted)

    def restore(self, backup_path: str, target_dir: str):
        """从加密备份恢复"""
        import tarfile, age, io
        with open(backup_path, "rb") as f:
            decrypted = age.decrypt(open_age_key(), f.read())
        tar_buffer = io.BytesIO(decrypted)
        with tarfile.open(fileobj=tar_buffer, mode="r") as tar:
            tar.extractall(target_dir)
```

---

### 10.6 与 Windows Recall VBS Enclave 的详细对比

| 维度 | Windows Recall | 贵庚（补充后）|
|------|--------------|--------------|
| **硬件隔离** | VBS Enclave（Hyper-V 隔离区）| Mac Secure Enclave / TPM 2.0 |
| **密钥保护** | TPM 2.0 + Windows Hello | macOS Keychain + Secure Enclave / TPM 2.0（NAS）|
| **全盘加密** | BitLocker（默认开启）| FileVault 2 / LUKS2（全盘）|
| **文件级加密** | 无（OS 级隔离）| age + SQLCipher（记忆数据层）|
| **认证** | Windows Hello（生物识别）| Touch ID / Face ID + 专属 PIN |
| **运行时保护** | VBS 隔离进程内存 | 进程隔离 + 内存加密 |
| **多用户隔离** | Windows 用户账号隔离 | Keychain per-user + 认证层隔离 |
| **继承人访问** | 无（设备清除后继承）| 多级密钥管理（可设置"遗产密钥"）|
| **物理盗窃保护** | BitLocker + TPM（设备绑定）| FileVault + 认证密码（双因素更灵活）|

**贵庚的隐私优势**：
1. **认证层与设备层完全解耦**：即使设备被全盘解密，记忆数据仍是加密的（文件级加密保护）
2. **多级敏感字段控制**：不是"全有或全无"，而是部分可见
3. **开放架构**：不依赖特定 OS 的 enclave，可跨 macOS/Linux 部署

---

### 10.7 隐私加密各阶段实施路径

| 阶段 | 时间 | 加密方案 | 密钥管理 | 优先级 |
|------|------|---------|---------|--------|
| **阶段一** | 当前 | age 文件加密 + FileVault | Keychain（Secure Enclave 绑定）| P0 |
| **阶段二** | 2026-2027 | SQLCipher + FAISS 索引加密 | Keychain + TPM 2.0（NAS）| P0 |
| **阶段三** | 2027+ | 全量视频流加密 + 模型权重加密 | TPM 2.0 + 硬件安全模块 | P1 |

#### 阶段一实施清单（当前可落地）

```
[ ] 1. 确认 macOS FileVault 2 已开启
     命令：fdesetup status

[ ] 2. 安装 age
     命令：brew install age

[ ] 3. 生成加密密钥
     命令：age-keygen -o ~/.config/guigeng/memory.key

[ ] 4. 初始化 Keychain 认证
     运行：guigeng_auth_setup.py（首次设置密码）

[ ] 5. 修改记忆存储路径为加密版本
     原：~/.openclaw/guigeng-memory/
     新：~/.config/guigeng/encrypted-memory/

[ ] 6. 配置自动加密写入
     挂载：age_encrypted_store 包装现有读写逻辑

[ ] 7. 测试密钥丢失场景（密钥丢失 = 数据不可恢复，预期行为）
```

---

### 10.8 隐私合规 Checklist（GDPR / 个保法 参考）

| 检查项 | 说明 | 状态 |
|--------|------|------|
| **数据最小化** | 只采集实现功能必需的数据 | ✅ Whisper 语音转文本而非存储原始音频 |
| **目的限制** | 记忆数据仅用于贵庚服务，不作他用 | ✅ 加密隔离，不开放第三方读取 |
| **存储期限** | 用户可设置自动过期（TTL）| ✅ semantic_cache.json TTL=1年 |
| **访问权** | 用户可查看、导出、删除自己的记忆 | ✅ 导出为 JSON，删除即销毁密钥 |
| **携带权** | 用户可迁移记忆到新设备 | ✅ age 加密备份，可在任意平台恢复 |
| **被遗忘权** | 用户可彻底删除所有记忆 | ✅ 删除密钥文件 = 数据不可恢复 |
| **第三方共享限制** | 继承人不自动获得私密对话（涉及第三方隐私）| ⚠️ 待设计：区分"我的记忆"和"涉及他人的记忆" |

---

### 10.9 技术风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| **密钥丢失** | 数据永久不可恢复 | 纸质备份主密钥 + 加密 USB 备份 |
| **认证密码被猜出** | 记忆泄露 | PBKDF2 600k 迭代 + 盐 + pepper + 失败锁定 |
| **TPM 故障** | NAS 无法启动 | 备用密码（独立于 TPM 的 LUKS 恢复密钥）|
| **社会工程**（骗取密码）| 记忆泄露 | 不在聊天中询问密码；物理隔离的设置界面 |
| **多设备同步密钥分发** | 设备间同步密钥被截获 | WireGuard VPN 隧道 + age 端到端加密 |
| **遗产密钥设计** | 继承纠纷 | 明确告知用户：遗产密钥 ≠ 全部记忆；涉及第三方内容不可继承 |

---

## 10. 数据导入导出（备份 / 迁移 / 恢复）

> **补充章节**：原 ROBOT-SOP.md §1.2.4 记忆架构 — 数据导入导出完整方案
> **补充日期**：2026-04-01
> **补充内容**：全层级数据（Layer 1/2/3）的导出格式、导入流程、增量同步、跨设备迁移

---

### 10.1 导出场景与格式选择

| 场景 | 推荐格式 | 适用阶段 | 工具 |
|------|---------|---------|------|
| 日常备份（JSON）| `semantic_cache.json` | 阶段一 | Python json / jq |
| 数据库完整备份 | SQLite `.db` + FAISS `.index` | 阶段二 | sqlite3 CLI / .backup |
| 跨平台迁移 | JSON Lines (`.jsonl`) | 任意阶段 | 自研脚本 |
| 图谱数据迁移 | Cypher Dump (`.cypher`) | 阶段二/三 | Neo4j `neo4j-admin dump` |
| 增量同步 | JSON Patch (RFC 6902) | 任意阶段 | 自研 diff 脚本 |
| 隐私导出（用户数据）| 加密 ZIP | 任意阶段 | `gpg` / `zip -e` |

---

### 10.2 Layer 1 语义缓存导出 / 导入（阶段一）

#### 10.2.1 JSON 完整导出

```python
import json
import hashlib
from datetime import datetime

def export_semantic_cache(cache_path: str, output_path: str, include_embeddings: bool = True):
    """
    导出语义缓存为可移植 JSON 格式

    include_embeddings=True  → 导出向量（恢复时无需重新 embedding）
    include_embeddings=False → 仅导出元数据（轻量，适合分享）
    """
    with open(cache_path, 'r') as f:
        cache = json.load(f)

    export_meta = {
        "export_version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "cache_version": cache.get("cache_version"),
        "model_name": cache.get("model_name"),
        "embedding_dim": cache.get("embedding_dim"),
        "total_entries": len(cache["entries"]),
    }

    entries = []
    for entry in cache["entries"]:
        exp = {
            "entry_id": entry["entry_id"],
            "content": entry["content"],
            "content_hash": entry["content_hash"],
            "response": entry.get("response", ""),
            "timestamp": entry["timestamp"],
            "importance": entry.get("importance", 0.5),
            "access_count": entry.get("access_count", 0),
            "last_accessed": entry.get("last_accessed"),
            "expires_at": entry.get("expires_at"),
        }
        if include_embeddings:
            exp["embedding"] = entry.get("embedding")
        entries.append(exp)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "meta": export_meta,
            "entries": entries
        }, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(entries)} entries → {output_path}")
    print(f"  File size: {len(open(output_path,'rb').read()) / 1024 / 1024:.2f} MB")
```

#### 10.2.2 JSON 导入恢复

```python
import json
import hashlib
import uuid

def import_semantic_cache(export_path: str, target_cache_path: str,
                           merge_policy: str = "skip-existing"):
    """
    从 JSON 备份恢复语义缓存

    merge_policy:
      - "skip-existing"   ：已有 content_hash 的条目跳过（默认，安全）
      - "overwrite"      ：覆盖已有条目（用备份版本）
      - "keep-both"       ：保留两份（生成新 entry_id）
    """
    with open(export_path, 'r', encoding='utf-8') as f:
        backup = json.load(f)

    # 读取目标缓存
    try:
        with open(target_cache_path, 'r') as f:
            target = json.load(f)
    except FileNotFoundError:
        target = {
            "cache_version": backup["meta"].get("cache_version", "1.0"),
            "created_at": datetime.now().isoformat(),
            "model_name": backup["meta"].get("model_name", "all-MiniLM-L6-v2"),
            "embedding_dim": backup["meta"].get("embedding_dim", 384),
            "total_entries": 0,
            "entries": []
        }

    existing_hashes = {e["content_hash"] for e in target["entries"]}
    added = skipped = overwritten = 0

    for exp_entry in backup["entries"]:
        content_hash = exp_entry["content_hash"]

        if content_hash in existing_hashes:
            if merge_policy == "skip-existing":
                skipped += 1
                continue
            elif merge_policy == "overwrite":
                # 找到并替换
                for i, e in enumerate(target["entries"]):
                    if e["content_hash"] == content_hash:
                        # 保留原始 entry_id，但更新内容
                        target["entries"][i] = {
                            **exp_entry,
                            "entry_id": e["entry_id"],  # 保留原 ID
                            "last_accessed": e.get("last_accessed"),
                            "access_count": e.get("access_count", 0),
                        }
                        overwritten += 1
                        break
        else:
            # 新条目
            if "entry_id" not in exp_entry or exp_entry["entry_id"] in {e["entry_id"] for e in target["entries"]}:
                exp_entry["entry_id"] = str(uuid.uuid4())
            target["entries"].append(exp_entry)
            added += 1

    target["total_entries"] = len(target["entries"])

    with open(target_cache_path, 'w', encoding='utf-8') as f:
        json.dump(target, f, ensure_ascii=False, indent=2)

    print(f"Import complete: {added} added, {skipped} skipped, {overwritten} overwritten")
    return {"added": added, "skipped": skipped, "overwritten": overwritten}
```

#### 10.2.3 CSV 导出（轻量、用户可读）

```python
import csv

def export_to_csv(cache_path: str, output_path: str):
    """导出为 CSV（无向量，仅元数据，适合用户查看或迁移到其他平台"""
    with open(cache_path, 'r') as f:
        cache = json.load(f)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "entry_id", "content", "timestamp", "importance",
            "access_count", "last_accessed", "expires_at"
        ])
        writer.writeheader()
        for entry in cache["entries"]:
            writer.writerow({
                "entry_id": entry["entry_id"],
                "content": entry["content"],
                "timestamp": entry["timestamp"],
                "importance": entry.get("importance", ""),
                "access_count": entry.get("access_count", 0),
                "last_accessed": entry.get("last_accessed", ""),
                "expires_at": entry.get("expires_at", ""),
            })

    print(f"CSV export: {len(cache['entries'])} rows → {output_path}")
```

---

### 10.3 Layer 1 FAISS 索引导出 / 导入

#### 10.3.1 FAISS 索引序列化

```python
import faiss
import numpy as np

def export_faiss_index(index_path: str, output_dir: str):
    """导出 FAISS 索引为单个文件（可移植，跨 Python 版本）"""
    import os
    os.makedirs(output_dir, exist_ok=True)

    index = faiss.read_index(index_path)

    # 方案 A：直接序列化（最快，推荐）
    index_file = os.path.join(output_dir, "faiss_index.bin")
    faiss.write_index(index, index_file)

    # 方案 B：导出为 numpy（可读性备份）
    vectors_file = os.path.join(output_dir, "vectors.npy")
    np.save(vectors_file, index.reconstruct())

    # 导出索引元信息
    meta = {
        "ntotal": index.ntotal,
        "dim": index.d,
        "index_type": type(index).__name__,
        "is_trained": index.is_trained,
    }
    import json
    with open(os.path.join(output_dir, "index_meta.json"), 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"FAISS index: {meta['ntotal']} vectors, dim={meta['dim']}")
    print(f"  → {index_file} ({os.path.getsize(index_file)/1024/1024:.1f} MB)")

    return index_file

def import_faiss_index(export_dir: str, target_index_path: str):
    """从备份恢复 FAISS 索引"""
    index_file = os.path.join(export_dir, "faiss_index.bin")
    if not os.path.exists(index_file):
        raise FileNotFoundError(f"No index file found in {export_dir}")

    index = faiss.read_index(index_file)
    faiss.write_index(index, target_index_path)
    print(f"Restored FAISS index: {index.ntotal} vectors → {target_index_path}")
    return index
```

#### 10.3.2 向量 + 元数据联合导出（推荐方案）

```python
import json
import faiss
import numpy as np

def full_layer1_export(cache_path: str, faiss_index_path: str, output_path: str):
    """
    完整导出 Layer 1：语义缓存 JSON + FAISS 索引
    保证向量和元数据严格对齐
    """
    # 读取缓存
    with open(cache_path, 'r') as f:
        cache = json.load(f)

    # 读取 FAISS 索引
    index = faiss.read_index(faiss_index_path)

    # 验证一致性
    assert len(cache["entries"]) == index.ntotal, \
        f"Entry count mismatch: {len(cache['entries'])} vs {index.ntotal}"

    # 重建向量数组
    vectors = np.zeros((index.ntotal, index.d), dtype=np.float32)
    for i in range(index.ntotal):
        vectors[i] = index.reconstruct(i)

    # 打包
    export = {
        "meta": {
            "export_version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "model_name": cache["model_name"],
            "embedding_dim": cache["embedding_dim"],
            "total_entries": index.ntotal,
        },
        "entries": cache["entries"],
        "vectors": vectors.tolist(),
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export, f, ensure_ascii=False)

    size_mb = len(json.dumps(export)) / 1024 / 1024
    print(f"Full Layer-1 export: {index.ntotal} entries, {size_mb:.1f} MB → {output_path}")

def full_layer1_import(export_path: str, target_cache_path: str,
                        target_faiss_path: str):
    """从完整备份恢复 Layer 1"""
    with open(export_path, 'r', encoding='utf-8') as f:
        export = json.load(f)

    # 恢复缓存
    cache = {
        "cache_version": export["meta"]["cache_version"],
        "created_at": datetime.now().isoformat(),
        "model_name": export["meta"]["model_name"],
        "embedding_dim": export["meta"]["embedding_dim"],
        "total_entries": export["meta"]["total_entries"],
        "entries": export["entries"],
    }
    with open(target_cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    # 恢复 FAISS 索引
    vectors = np.array(export["vectors"], dtype=np.float32)
    index = faiss.IndexFlatL2(cache["embedding_dim"])
    index.add(vectors)
    faiss.write_index(index, target_faiss_path)

    print(f"Layer-1 import: {index.ntotal} entries restored")
```

---

### 10.4 Layer 3 SQLite 数据库备份 / 恢复

#### 10.4.1 SQLite 在线备份（不锁库）

```python
import sqlite3
import shutil
import os
from datetime import datetime

def backup_sqlite(db_path: str, backup_dir: str,
                  compress: bool = True) -> str:
    """
    在线备份 SQLite 数据库（使用 backup API，不阻塞读写）

    backup_dir：备份目标目录
    compress  ：是否 gzip 压缩
    """
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"guigeng_timeline_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)

    conn_src = sqlite3.connect(db_path)
    conn_dst = sqlite3.connect(backup_path)
    conn_src.backup(conn_dst)
    conn_src.close()
    conn_dst.close()

    if compress:
        import gzip, tarfile
        tar_path = backup_path + ".tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(backup_path, arcname=backup_filename)
        os.remove(backup_path)
        backup_path = tar_path

    size_mb = os.path.getsize(backup_path) / 1024 / 1024
    print(f"SQLite backup: {backup_path} ({size_mb:.1f} MB)")
    return backup_path

def restore_sqlite(backup_path: str, target_db_path: str):
    """从备份恢复 SQLite 数据库"""
    import tarfile, gzip

    # 解压（如需要）
    if backup_path.endswith(".tar.gz"):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(tmpdir)
            extracted = os.path.join(tmpdir, [f for f in os.listdir(tmpdir) if f.endswith(".db")][0])
            shutil.copy2(extracted, target_db_path)
    else:
        shutil.copy2(backup_path, target_db_path)

    print(f"SQLite restored → {target_db_path}")
```

#### 10.4.2 SQLite 增量备份（只备份变更）

```python
def incremental_backup_sqlite(db_path: str, last_backup_path: str,
                               backup_dir: str) -> str:
    """
    增量备份：对比上次备份以来变更的记录
    使用 WAL 的 checkpoint log 实现差异备份
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 获取上次备份时间
    if os.path.exists(last_backup_path):
        with open(last_backup_path, 'r') as f:
            last_meta = json.load(f)
        last_ts = last_meta.get("backup_timestamp")
    else:
        last_ts = "1970-01-01T00:00:00"

    # 找出变更记录
    cur.execute('''
        SELECT id, content, timestamp, importance, entity_json,
               access_count, last_accessed, tags
        FROM memories
        WHERE last_accessed > ? OR timestamp > ?
        ORDER BY timestamp DESC
    ''', (last_ts, last_ts))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No changes since last backup")
        return last_backup_path

    # 导出变更集
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    diff_path = os.path.join(backup_dir, f"incremental_{timestamp}.jsonl")

    with open(diff_path, 'w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps({
                "id": row[0], "content": row[1], "timestamp": row[2],
                "importance": row[3], "entity_json": row[4],
                "access_count": row[5], "last_accessed": row[6], "tags": row[7]
            }, ensure_ascii=False) + "\n")

    print(f"Incremental backup: {len(rows)} changed records → {diff_path}")
    return diff_path
```

---

### 10.5 Layer 2 知识图谱导出 / 导入（Neo4j）

#### 10.5.1 Cypher 完整导出

```python
def export_neo4j_graph(uri: str, user: str, password: str, output_path: str):
    """
    导出 Neo4j 图谱为 Cypher 脚本（可跨 Neo4j 版本迁移）
    """
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        # 导出节点
        nodes = session.run("""
            MATCH (n)
            RETURN labels(n) as labels, properties(n) as props, id(n) as neo_id
        """).data()

        # 导出关系
        rels = session.run("""
            MATCH (a)-[r]->(b)
            RETURN type(r) as rel_type, properties(r) as props,
                   id(a) as start_id, id(b) as end_id
        """).data()

    driver.close()

    # 生成 Cypher 脚本
    cypher_lines = ["// Guigeng Knowledge Graph Export", f"// {datetime.now().isoformat()}"]

    for node in nodes:
        labels = ":".join(node["labels"])
        props = json.dumps(node["props"], ensure_ascii=False)
        cypher_lines.append(
            f'CREATE (n:{labels} {{{props}}})'
        )

    for rel in rels:
        rel_type = rel["rel_type"]
        props = json.dumps(rel["props"], ensure_ascii=False)
        cypher_lines.append(
            f"MATCH (a), (b) WHERE id(a)={rel['start_id']} AND id(b)={rel['end_id']}"
            f" CREATE (a)-[r:{rel_type} {{{props}}}]->(b)"
        )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(cypher_lines))

    print(f"Neo4j export: {len(nodes)} nodes, {len(rels)} relationships → {output_path}")

def import_neo4j_graph(uri: str, user: str, password: str, cypher_path: str):
    """从 Cypher 脚本恢复图谱"""
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with open(cypher_path, 'r', encoding='utf-8') as f:
        cypher_script = f.read()

    with driver.session() as session:
        # 分批执行（每 1000 条一个事务）
        statements = [s.strip() for s in cypher_script.split(";") if s.strip()]
        for i in range(0, len(statements), 1000):
            tx = session.begin_transaction()
            for stmt in statements[i:i+1000]:
                tx.run(stmt)
            tx.commit()
            print(f"Imported batch {i//1000 + 1}: {min(1000, len(statements)-i)} statements")

    driver.close()
    print(f"Neo4j import complete from {cypher_path}")
```

#### 10.5.2 JSON Graph 导出（更通用的格式）

```python
def export_neo4j_to_json(uri: str, user: str, password: str, output_path: str):
    """导出为 JSON 格式（可读性强，可转换为其他图数据库格式）"""
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        nodes = session.run("""
            MATCH (n) RETURN labels(n) as labels, properties(n) as props, id(n) as neo_id
        """).data()

        rels = session.run("""
            MATCH (a)-[r]->(b)
            RETURN type(r) as rel_type, properties(r) as props,
                   id(a) as start_id, id(b) as end_id
        """).data()

    driver.close()

    graph = {
        "meta": {
            "export_version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "node_count": len(nodes),
            "relationship_count": len(rels),
        },
        "nodes": [
            {"id": n["neo_id"], "labels": n["labels"], "properties": n["props"]}
            for n in nodes
        ],
        "relationships": [
            {"type": r["rel_type"], "start_id": r["start_id"],
             "end_id": r["end_id"], "properties": r["props"]}
            for r in rels
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(f"Graph export: {len(nodes)} nodes, {len(rels)} rels → {output_path}")
```

---

### 10.6 全量一键备份脚本

```python
#!/usr/bin/env python3
"""
guigeng_backup.py — 贵庚系统全量一键备份

用法：
  python3 guigeng_backup.py --output ./backups/2026-04-01
  python3 guigeng_backup.py --output ./backups/2026-04-01 --compress
  python3 guigeng_backup.py --restore ./backups/2026-04-01/guigeng_full_backup_2026-04-01.tar.gz
"""

import argparse
import json
import os
import sys
import tarfile
import tempfile
import shutil
from datetime import datetime

BACKUP_DIR = os.path.expanduser("~/.openclaw/guigeng-memory")
MEMORY_SUBDIRS = ["cache", "faiss", "graph", "timeline", "raw"]

def create_backup(output_dir: str, compress: bool = True):
    """一键全量备份（覆盖所有 Layer 的数据）"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"guigeng_full_backup_{timestamp}"
    backup_path = os.path.join(output_dir, backup_name)

    os.makedirs(backup_path, exist_ok=True)

    # Layer 1：语义缓存
    cache_src = os.path.join(BACKUP_DIR, "cache", "semantic_cache.json")
    if os.path.exists(cache_src):
        shutil.copy2(cache_src, os.path.join(backup_path, "semantic_cache.json"))

    # Layer 1：FAISS 索引
    faiss_src = os.path.join(BACKUP_DIR, "faiss", "index_hnsw.seqs")
    if os.path.exists(faiss_src):
        shutil.copy2(faiss_src, os.path.join(backup_path, "index_hnsw.seqs"))

    # Layer 3：SQLite 时间线
    timeline_src = os.path.join(BACKUP_DIR, "timeline", "timeline.db")
    if os.path.exists(timeline_src):
        shutil.copy2(timeline_src, os.path.join(backup_path, "timeline.db"))

    # Layer 2：Neo4j 图谱（JSON 格式）
    graph_json = os.path.join(BACKUP_DIR, "graph", "graph_export.json")
    if os.path.exists(graph_json):
        shutil.copy2(graph_json, os.path.join(backup_path, "graph_export.json"))

    # 元信息
    meta = {
        "backup_version": "1.0",
        "created_at": datetime.now().isoformat(),
        "layers": {
            "layer1_cache": os.path.exists(cache_src),
            "layer1_faiss": os.path.exists(faiss_src),
            "layer2_graph": os.path.exists(graph_json),
            "layer3_timeline": os.path.exists(timeline_src),
        }
    }
    with open(os.path.join(backup_path, "backup_meta.json"), 'w') as f:
        json.dump(meta, f, indent=2)

    # 打包
    if compress:
        tar_path = os.path.join(output_dir, f"{backup_name}.tar.gz")
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(backup_path, arcname=backup_name)
        shutil.rmtree(backup_path)
        final_path = tar_path
        print(f"Full backup: {tar_path}")
    else:
        final_path = backup_path
        print(f"Full backup: {backup_path}")

    size_mb = os.path.getsize(final_path) / 1024 / 1024
    print(f"  Size: {size_mb:.1f} MB")
    return final_path

def restore_backup(backup_archive: str):
    """从备份恢复全量数据"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 解压（如需要）
        if backup_archive.endswith(".tar.gz"):
            with tarfile.open(backup_archive, "r:gz") as tar:
                tar.extractall(tmpdir)
            backup_root = os.path.join(tmpdir, os.listdir(tmpdir)[0])
        else:
            backup_root = backup_archive

        # 读取元信息
        with open(os.path.join(backup_root, "backup_meta.json"), 'r') as f:
            meta = json.load(f)

        print(f"Restoring backup from: {meta['created_at']}")
        print(f"  Layers: {meta['layers']}")

        # 逐层恢复
        for subdir in MEMORY_SUBDIRS:
            os.makedirs(os.path.join(BACKUP_DIR, subdir), exist_ok=True)

        # Layer 1
        cache_file = os.path.join(backup_root, "semantic_cache.json")
        if os.path.exists(cache_file):
            shutil.copy2(cache_file, os.path.join(BACKUP_DIR, "cache", "semantic_cache.json"))

        faiss_file = os.path.join(backup_root, "index_hnsw.seqs")
        if os.path.exists(faiss_file):
            shutil.copy2(faiss_file, os.path.join(BACKUP_DIR, "faiss", "index_hnsw.seqs"))

        # Layer 3
        timeline_file = os.path.join(backup_root, "timeline.db")
        if os.path.exists(timeline_file):
            shutil.copy2(timeline_file, os.path.join(BACKUP_DIR, "timeline", "timeline.db"))

        # Layer 2
        graph_file = os.path.join(backup_root, "graph_export.json")
        if os.path.exists(graph_file):
            shutil.copy2(graph_file, os.path.join(BACKUP_DIR, "graph", "graph_export.json"))

    print("Restore complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Guigeng memory backup tool")
    parser.add_argument("--output", default="./backups", help="Output directory")
    parser.add_argument("--compress", action="store_true", help="Compress to .tar.gz")
    parser.add_argument("--restore", help="Restore from backup path")
    args = parser.parse_args()

    if args.restore:
        restore_backup(args.restore)
    else:
        create_backup(args.output, compress=args.compress)
```

---

### 10.7 增量同步（跨设备 / 跨平台）

#### 10.7.1 JSON Patch 差量同步

```python
import hashlib
import json

def compute_diff(old_cache_path: str, new_cache_path: str, output_path: str):
    """
    计算两次备份之间的增量差异（基于 JSON Patch RFC 6902）
    用于跨设备增量同步
    """
    with open(old_cache_path, 'r') as f:
        old_cache = json.load(f)
    with open(new_cache_path, 'r') as f:
        new_cache = json.load(f)

    old_hashes = {e["content_hash"]: e for e in old_cache["entries"]}
    new_hashes = {e["content_hash"]: e for e in new_cache["entries"]}

    # 新增
    added = [new_hashes[h] for h in new_hashes if h not in old_hashes]
    # 删除
    removed = [old_hashes[h]["entry_id"] for h in old_hashes if h not in new_hashes]
    # 更新
    updated = []
    for h in new_hashes:
        if h in old_hashes:
            old_e, new_e = old_hashes[h], new_hashes[h]
            if old_e.get("response") != new_e.get("response") or \
               old_e.get("importance") != new_e.get("importance"):
                updated.append(new_e)

    patch = {
        "patch_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "added": added,
        "updated": updated,
        "removed_ids": removed,
        "stats": {
            "added_count": len(added),
            "updated_count": len(updated),
            "removed_count": len(removed),
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(patch, f, ensure_ascii=False, indent=2)

    print(f"Diff: +{len(added)} -{len(removed)} ~{len(updated)} → {output_path}")
    return patch

def apply_patch(cache_path: str, patch_path: str):
    """应用增量 Patch 到本地缓存"""
    with open(patch_path, 'r') as f:
        patch = json.load(f)
    with open(cache_path, 'r') as f:
        cache = json.load(f)

    cache_hash_map = {e["content_hash"]: i for i, e in enumerate(cache["entries"])}
    cache_id_map = {e["entry_id"]: i for i, e in enumerate(cache["entries"])}

    # 应用新增
    for entry in patch["added"]:
        if entry["content_hash"] not in cache_hash_map:
            cache["entries"].append(entry)

    # 应用更新
    for entry in patch["updated"]:
        if entry["content_hash"] in cache_hash_map:
            idx = cache_hash_map[entry["content_hash"]]
            cache["entries"][idx].update(entry)

    # 应用删除
    for entry_id in patch["removed_ids"]:
        if entry_id in cache_id_map:
            del cache["entries"][cache_id_map[entry_id]]

    cache["total_entries"] = len(cache["entries"])

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    stats = patch["stats"]
    print(f"Patch applied: +{stats['added_count']} -{stats['removed_count']} ~{stats['updated_count']}")
```

#### 10.7.2 跨设备同步注意事项

```
跨设备同步风险分析：
⚠️  向量维度不一致：不同设备用不同 embedding 模型（384d vs 768d）
    → 同步前检查 model_name 和 embedding_dim，不一致则拒绝同步

⚠️  FAISS 索引版本：faiss 0.x vs 1.x 索引格式不兼容
    → 同步前导出 vectors.npy，在目标设备重新建索引

⚠️  Neo4j 图谱：不同 Neo4j 版本 Cypher 语法差异
    → 使用 JSON 格式导出，比 Cypher 更稳定

⚠️  时间戳时区：跨时区设备需统一使用 UTC ISO 格式
    → 所有 timestamp 强制使用 ISO 8601 UTC

推荐同步策略：
  阶段一（JSON）：直接 rsync / Syncthing 同步整个 cache 目录
  阶段二（SQLite）：使用 Syncthing 同步 .db 文件（WAL 模式安全）
  阶段三（Neo4j）：独立 Neo4j 实例，图谱同步通过 JSON Patch
```

---

### 10.8 隐私导出（用户数据权利）

> GDPR /个人信息保护法 要求：用户有权导出个人数据

```python
def export_user_data(cache_path: str, output_path: str, encrypt: bool = True):
    """
    用户数据导出（隐私合规版）
    - 仅导出用户内容，不包含内部元数据（embedding、faiss_idx 等）
    - 可选加密（密钥由用户掌控）
    """
    with open(cache_path, 'r') as f:
        cache = json.load(f)

    user_entries = []
    for entry in cache["entries"]:
        user_entries.append({
            "content": entry["content"],
            "response": entry.get("response", ""),
            "timestamp": entry["timestamp"],
            "importance": entry.get("importance", 0.5),
            # 注意：不含 embedding、content_hash 等内部字段
        })

    export_data = {
        "exported_at": datetime.now().isoformat(),
        "format_version": "1.0",
        "total_memories": len(user_entries),
        "memories": user_entries
    }

    if encrypt:
        import base64
        import os
        # 生成随机密钥（展示给用户，由用户保管）
        key = base64.b64encode(os.urandom(32)).decode()
        # 简单加密（实际生产用 cryptography.Fernet）
        from cryptography.fernet import Fernet
        f = Fernet(key.encode())
        encrypted = f.encrypt(json.dumps(export_data, ensure_ascii=False).encode())
        with open(output_path, 'wb') as f:
            f.write(encrypted)
        # 密钥需要单独提供（这里简化为生成 key 文件）
        key_path = output_path + ".key"
        with open(key_path, 'w') as f:
            f.write(key)
        print(f"User data exported (encrypted): {output_path}")
        print(f"  Decryption key: {key_path} (KEEP THIS PRIVATE)")
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        print(f"User data exported (unencrypted): {output_path}")
```

---

### 10.9 导入导出质量验证

```python
def verify_backup(backup_dir: str) -> dict:
    """
    备份完整性验证（恢复前必做）
    检查：文件存在、条目数一致、哈希链完整、向量维度一致
    """
    results = {"status": "pass", "issues": []}

    # 1. 检查必要文件
    required = ["semantic_cache.json", "backup_meta.json"]
    for fname in required:
        fpath = os.path.join(backup_dir, fname)
        if not os.path.exists(fpath):
            results["issues"].append(f"Missing file: {fname}")

    # 2. 验证 JSON 结构
    try:
        with open(os.path.join(backup_dir, "semantic_cache.json"), 'r') as f:
            cache = json.load(f)
        entry_count = len(cache["entries"])
        results["entry_count"] = entry_count

        # 3. 验证哈希链连续性
        hashes = [e["content_hash"] for e in cache["entries"]]
        if len(hashes) != len(set(hashes)):
            results["issues"].append("Duplicate content_hash detected!")
        results["hash_integrity"] = "ok"

        # 4. 验证向量维度一致性
        dims = set(len(e.get("embedding", [])) for e in cache["entries"])
        if len(dims) > 1:
            results["issues"].append(f"Inconsistent embedding dims: {dims}")
        else:
            results["embedding_dim"] = dims.pop()

    except Exception as e:
        results["issues"].append(f"JSON parse error: {e}")

    if results["issues"]:
        results["status"] = "fail"

    return results
```

---

### 10.10 数据导入导出技术风险

| 风险 | 影响 | 缓解方案 |
|------|------|---------|
| FAISS 索引版本不兼容 | 索引无法加载 | 始终导出 `.npy` 向量，在目标端重建索引 |
| 跨设备 embedding 模型不一致 | 向量语义错乱 | 同步前验证 `model_name` + `embedding_dim`，不一致则重 embedding |
| SQLite 并发写入时备份 | 备份文件损坏 | 使用 `conn.backup()` API（WAL 安全）或在备份前执行 `PRAGMA wal_checkpoint` |
| 大文件传输中断 | 备份不完整 | 使用 `tar.gz` 分卷压缩，或 rsync `--partial --append` |
| 加密密钥丢失 | 数据永久不可恢复 | 密钥与备份文件分开存储（用户掌控） |
| 导入时 entry_id 冲突 | 图谱节点 ID 重复 | 使用 UUID 重新生成，或建立 `id_mapping` 表 |
| 增量同步循环依赖 | 设备 A 同步 B，B 又同步 A | 使用向量时钟（vector clock）或单向同步拓扑 |

