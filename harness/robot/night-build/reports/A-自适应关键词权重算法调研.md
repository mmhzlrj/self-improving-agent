# 自适应关键词权重衰减算法调研报告

**调研时间：** 2026-03-30  
**调研范围：** TF-IDF+时间衰减、Ebbinghaus遗忘曲线、Transformer Attention Decay、Bayesian Adaptive Filtering  
**应用背景：** 对话AI中的动态用户兴趣追踪 + Semantic Cache缓存优化

---

## 一、需求拆解

用户目标：
- 话题被讨论越多 → 相关关键词权重越高 → 响应更快更精准
- 长时间不讨论 → 权重自然衰减

本质上是**带时间维度的关键词重要性建模**，需要解决两个核心问题：
1. **如何衡量"重要性"**（多话题并发时的权重分配）
2. **如何处理"遗忘"**（时间衰减的函数形式）

---

## 二、五种方案对比

### 2.1 TF-IDF + 时间衰减

**核心思想：** 传统TF-IDF衡量词在文档中的静态重要性，叠加指数/线性时间衰减因子。

**公式：**
```
weight(w, t) = TF-IDF(w) × δ(t, t_last)

指数衰减：δ = e^(-λ × Δt)
线性衰减：δ = max(0, 1 - Δt / T_half)
```

**伪代码：**
```python
class TimeDecayTFIDF:
    def __init__(self, decay_rate=0.1):
        self.decay_rate = decay_rate  # λ

    def get_weight(self, word, current_time):
        delta_t = current_time - self.last_mention[word]
        tfidf = self.tfidf_scores.get(word, 0.0)
        return tfidf * exp(-self.decay_rate * delta_t)
```

| 优点 | 缺点 |
|------|------|
| ✅ 实现简单，计算开销极低 | ❌ 仅考虑词频，忽略语义关联 |
| ✅ 可解释性强，调参直观 | ❌ 时间衰减函数需手动设置（λ不可学习） |
| ✅ 与现有Semantic Cache无缝集成 | ❌ 对语义相似词无法自动聚合 |
| ✅ 适合短期上下文衰减 | ❌ 长期依赖建模能力弱 |

---

### 2.2 Word2Vec/GloVe + 衰减

**核心思想：** 用词向量捕捉语义相关性，关键词权重不仅受自身频率影响，还受语义邻域词的影响。

**公式：**
```
语义增强权重 = base_weight(w) × e^(-λΔt) + Σ(sim(w, w_neighbor) × weight(w_neighbor)) / K
```

| 优点 | 缺点 |
|------|------|
| ✅ 语义相近词自动关联（"Jetson"和"Nano"可关联） | ❌ 预训练词向量对垂直领域覆盖不足 |
| ✅ 可以做词语义聚类 | ❌ 词向量静态，无法在线更新 |
| ✅ 适合多话题交叉场景 | ❌ 计算量比纯TF-IDF大 |

---

### 2.3 Ebbinghaus 遗忘曲线建模 ⭐推荐

**核心思想：** 直接复用心理学遗忘曲线 R = e^(-t/S)，每次关键词被提及，记忆稳定性S增强，下次衰减变慢。

**核心公式：**
```
记忆保留率：R(t) = e^(-Δt / S)
记忆强化：S_new = S_old × strength_factor  （每次被提及）

最终权重：weight(w, t) = base_weight(w) × e^(-Δt / S(w))
```

**伪代码：**
```python
class EbbinghausKeywordTracker:
    def __init__(self, initial_strength=1.0, strength_factor=1.5):
        self.strength = {}   # {word: stability S}
        self.last_time = {} # {word: last mention timestamp}

    def mention(self, word, current_time):
        """关键词被提及时调用"""
        if word not in self.strength:
            self.strength[word] = initial_strength
        else:
            self.strength[word] *= strength_factor  # 重复提及 → S增大
        self.last_time[word] = current_time

    def get_weight(self, word, current_time):
        if word not in self.last_time:
            return 0.0
        delta_t = current_time - self.last_time[word]
        retention = exp(-delta_t / self.strength[word])
        base = self.base_weights.get(word, 1.0)
        return base * retention

    def decay_all(self, current_time):
        """定时对所有关键词做衰减（模拟自然遗忘）"""
        for word in list(self.strength.keys()):
            delta_t = current_time - self.last_time[word]
            retention = exp(-delta_t / self.strength[word])
            if retention < 0.01:  # 保留率<1%则清除
                del self.strength[word]
                del self.last_time[word]
```

| 优点 | 缺点 |
|------|------|
| ✅ **符合人类认知规律**，用户接受度高 | ❌ 参数（initial_strength, strength_factor）需调优 |
| ✅ 重复提及自动强化，长期话题自然保留 | ❌ 每个词需维护状态，内存占用随词数线性增长 |
| ✅ 衰减速度可学习（通过S参数） | ❌ 语义相似词无法自动聚合 |
| ✅ 可与TF-IDF叠加：base_weight=TF-IDF | ❌ 高并发场景下状态管理复杂 |

---

### 2.4 Transformer Attention Decay

**核心思想：** 在Transformer架构中直接建模注意力衰减，有两种实现：
1. **位置衰减**：attention score叠加位置距离的惩罚
2. **递归记忆衰减**：历史隐状态通过遗忘门逐渐衰减

**公式（RWKV/Transformer-XL风格）：**
```
h_t = LN(α_t ⊙ Attn(x_t, h_{t-1}) + (1-α_t) ⊙ h_{t-1})
其中 α_t = sigmoid(gate_t) 为遗忘门，值越大记忆越完整
```

**位置衰减实现：**
```python
def attention_with_decay(Q, K, V, positions, decay_rate=0.1):
    scores = (Q @ K.transpose(-2,-1)) / sqrt(d_k)
    # 距离矩阵：越近的token注意力越强
    distance = torch.abs(positions.unsqueeze(-1) - positions.unsqueeze(-2))
    scores = scores - decay_rate * distance  # 距离越远，score越低
    return softmax(scores, dim=-1) @ V
```

| 优点 | 缺点 |
|------|------|
| ✅ 与LLM架构天然融合，可端到端训练 | ❌ 需要修改模型结构或fine-tune |
| ✅ 可学习衰减参数，自适应强 | ❌ 推理延迟增加，缓存查询时开销大 |
| ✅ 能同时建模语义+时序 | ❌ 解释性弱，难以调试 |
| ✅ 长上下文建模能力强 | ❌ 不适合作为独立的外挂权重层 |

---

### 2.5 Bayesian Adaptive Filtering（卡尔曼滤波）

**核心思想：** 将每个关键词的重要性视为隐状态，用贝叶斯滤波在线估计，每次观测（用户输入）更新后验分布，同时通过状态转移方程实现自然衰减。

**公式（一维卡尔曼滤波）：**
```
预测步：
  x̂_{t|t-1} = α × x_{t-1}        （α<1 实现状态衰减）
  P_{t|t-1} = α² × P_{t-1} + Q    （不确定性传播）

更新步：
  K_t = P_{t|t-1} / (P_{t|t-1} + R)   （卡尔曼增益）
  x_t = x̂_{t|t-1} + K_t(z_t - x̂_{t|t-1})   （融合观测）
  P_t = (1 - K_t) × P_{t|t-1}
```

**伪代码：**
```python
class BayesianKeywordFilter:
    def __init__(self, alpha=0.95, process_noise=0.01, obs_noise=0.1):
        self.alpha = alpha
        self.Q = process_noise
        self.R = obs_noise
        self.x = {}  # 后验均值（关键词重要性）
        self.P = {}  # 后验方差（不确定性）

    def observe(self, word, z, current_time):
        if word not in self.x:
            self.x[word], self.P[word] = 0.0, 1.0

        # 预测（时间衰减）
        self.x[word] = self.alpha * self.x[word]
        self.P[word] = self.alpha**2 * self.P[word] + self.Q

        # 卡尔曼更新
        K = self.P[word] / (self.P[word] + self.R)
        self.x[word] = self.x[word] + K * (z - self.x[word])
        self.P[word] = (1 - K) * self.P[word]

        return self.x[word]
```

| 优点 | 缺点 |
|------|------|
| ✅ **自适应性强**，无需手动调衰减率 | ❌ 实现复杂，每个词维护(均值,方差)两个标量 |
| ✅ 提供**不确定性估计**（可用于缓存淘汰决策） | ❌ 参数（Q,R,α）对结果影响大，需贝叶斯调参 |
| ✅ 天然融合多模态观测（TF-IDF、BM25等） | ❌ 对大量关键词时计算/存储开销线性增长 |
| ✅ 冷启动快速收敛 | ❌ 与现有Semantic Cache集成需要较大改动 |

---

## 三、优缺点对比总表

| 方案 | 核心机制 | 实现复杂度 | 自适应性 | 存储开销 | 与Semantic Cache兼容性 | 推荐场景 |
|------|----------|------------|----------|----------|------------------------|---------|
| TF-IDF+时间衰减 | 指数/线性衰减 | ⭐ 低 | 低（手动调参） | 低 | ⭐⭐⭐⭐⭐ 直接可用 | 快速实现、短期缓存 |
| Word2Vec+衰减 | 语义+时间衰减 | ⭐⭐ 中 | 中 | 中 | ⭐⭐⭐ 需改索引 | 语义关联需求 |
| **Ebbinghaus遗忘曲线** | 重复增强+指数衰减 | ⭐⭐ 中 | 高（S可学习） | 中 | ⭐⭐⭐⭐ 状态层外挂 | ⭐**首选方案** |
| Transformer Attention | 位置/递归衰减 | ⭐⭐⭐⭐ 高 | 高（可训练） | 高 | ⭐⭐ 需fine-tune | LLM深度集成 |
| Bayesian Filtering | 贝叶斯状态估计 | ⭐⭐⭐⭐ 高 | 最高（自动） | 中 | ⭐⭐ 需重构 | 高精度场景 |

---

## 四、推荐方案及理由

### 🏆 首选方案：Ebbinghaus遗忘曲线 + TF-IDF叠加

**理由：**
1. **认知科学背书**：直接复用人类记忆模型，用户对"遗忘后再提及时重新记住"的行为模式接受度高
2. **与现有架构兼容**：可作为Semantic Cache的外挂权重层，无需修改底层FAISS/BM25索引
3. **计算效率高**：每次提及只需一次乘法+时间差计算，O(1)复杂度
4. **参数可解释**：initial_strength、strength_factor都有明确物理含义，易调参
5. **与现有time_boost兼容**：当前Semantic Cache已有time_boost机制，Ebbinghaus可作为更精细化的替代

**具体做法：**
- `base_weight(w)` = TF-IDF(w) 或固定权重
- `S(w)` 初始值设为实验确定（建议1.0）
- `strength_factor` 建议1.3~1.7（每次提及记忆稳定性增加30%~70%）
- 衰减函数：R(t) = e^(-Δt / S)

---

## 五、具体实现思路

### 5.1 伪代码（推荐实现）

```python
import math
import time
from collections import defaultdict

class EbbinghausKeywordTracker:
    """
    基于Ebbinghaus遗忘曲线的关键词权重追踪器
    公式: weight(w, t) = base_weight(w) × e^(-Δt / S(w))
    每次提及: S(w) ← S(w) × strength_factor
    """
    DEFAULT_INITIAL_STRENGTH = 1.0
    DEFAULT_STRENGTH_FACTOR = 1.5
    DEFAULT_BASE_WEIGHT = 1.0

    def __init__(self, strength_factor=None, initial_strength=None):
        self.strength_factor = strength_factor or self.DEFAULT_STRENGTH_FACTOR
        self.initial_strength = initial_strength or self.DEFAULT_INITIAL_STRENGTH
        self.strength = {}      # {keyword: stability S}
        self.base_weights = {}   # {keyword: TF-IDF or fixed}
        self.last_time = {}     # {keyword: last mention timestamp}
        self.mention_count = {} # {keyword: mention count}

    def mention(self, keyword: str, base_weight: float = None, timestamp: float = None):
        """
        关键词被提及时调用此方法
        自动更新记忆强度 S 和时间戳
        """
        t = timestamp or time.time()
        w = base_weight or self.DEFAULT_BASE_WEIGHT

        if keyword not in self.strength:
            self.strength[keyword] = self.initial_strength
            self.mention_count[keyword] = 0
        else:
            self.strength[keyword] *= self.strength_factor
            self.mention_count[keyword] += 1

        self.base_weights[keyword] = w
        self.last_time[keyword] = t

    def get_weight(self, keyword: str, timestamp: float = None) -> float:
        """
        获取关键词在时刻 t 的权重
        """
        t = timestamp or time.time()

        if keyword not in self.last_time:
            return 0.0

        delta_t = t - self.last_time[keyword]
        base = self.base_weights.get(keyword, self.DEFAULT_BASE_WEIGHT)
        s = self.strength.get(keyword, self.initial_strength)

        retention = math.exp(-delta_t / s)
        return base * retention

    def get_weights_batch(self, keywords: list, timestamp: float = None) -> dict:
        """批量获取权重"""
        return {kw: self.get_weight(kw, timestamp) for kw in keywords}

    def decay_and_cleanup(self, timestamp: float = None, min_retention: float = 0.01):
        """
        清理保留率过低的关键词，释放内存
        可定时调用（如每次查询前）
        """
        t = timestamp or time.time()
        to_delete = []
        for kw in list(self.strength.keys()):
            delta_t = t - self.last_time[kw]
            s = self.strength[kw]
            retention = math.exp(-delta_t / s)
            if retention < min_retention:
                to_delete.append(kw)

        for kw in to_delete:
            del self.strength[kw]
            del self.base_weights[kw]
            del self.last_time[kw]
            del self.mention_count[kw]

        return to_delete

    def to_dict(self) -> dict:
        """序列化，支持持久化存储"""
        return {
            "strength": self.strength,
            "base_weights": self.base_weights,
            "last_time": self.last_time,
            "mention_count": self.mention_count,
            "config": {
                "strength_factor": self.strength_factor,
                "initial_strength": self.initial_strength,
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EbbinghausKeywordTracker":
        tracker = cls(
            strength_factor=data["config"]["strength_factor"],
            initial_strength=data["config"]["initial_strength"],
        )
        tracker.strength = data["strength"]
        tracker.base_weights = data["base_weights"]
        tracker.last_time = data["last_time"]
        tracker.mention_count = data["mention_count"]
        return tracker
```

### 5.2 与Semantic Cache的集成方式

```
用户输入 → 分词/NER提取关键词
              ↓
    EbbinghausTracker.get_weight(kw)
              ↓
    原始相似度 × ebbinghaus_weight(kw)
              ↓
    结合 time_boost（现有机制）
              ↓
    重排序 → Top-K 返回
```

**命中策略改进：**
```python
def compute_final_score(raw_similarity: float, keyword_weights: dict, time_boost: float) -> float:
    """
    raw_similarity: FAISS/BM25原始相似度
    keyword_weights: Ebbinghaus追踪器返回的权重字典
    time_boost: 现有time_boost（0.08~0.15）
    """
    avg_keyword_weight = sum(keyword_weights.values()) / max(len(keyword_weights), 1)
    keyword_factor = 0.5 + 0.5 * avg_keyword_weight  # 归一化到[0.5, 1.0]
    return raw_similarity * keyword_factor + time_boost
```

### 5.3 公式速查

| 函数 | 公式 | 说明 |
|------|------|------|
| 记忆保留率 | R = e^(-Δt/S) | Δt=时间差，S=记忆稳定性 |
| 记忆强化 | S_new = S_old × f | f=strength_factor，每次提及×1.5 |
| 权重计算 | w = base × R | base=TF-IDF，可选 |
| 半衰期 | T_half = S × ln(2) | S=1.0时约50秒后保留50% |

---

## 六、对Semantic Cache现有架构的影响

### 6.1 改动范围分析

基于 `Semantic-Cache-Optimization-Report.md`（2026-03-29）的测试结论：

| 组件 | 当前实现 | Ebbinghaus叠加影响 | 改动量 |
|------|---------|------------------|--------|
| 相似度计算 | `raw_sim + time_boost` | 增加 `keyword_factor × raw_sim` | 小 |
| 缓存命中 | FAISS向量相似度Top-K | 增加Ebbinghaus权重重排 | 小 |
| 索引结构 | FAISS + BM25并存 | **无需改动索引** | 无 |
| time_boost | 固定0.08~0.15 | 可保留time_boost作为兜底 | 无 |
| 增量索引 | reindex?mode=incremental | Ebbinghaus状态独立于索引，异步更新 | 无 |
| context窗口 | 正常返回 | 无影响 | 无 |

**结论：改动集中在相似度重排层，索引层和API层无需改动。**

### 6.2 缓存淘汰策略增强

当前Semantic Cache淘汰策略基于LRU+time_boost。引入Ebbinghaus后可增加：
- **保留率阈值淘汰**：retention < 1%时自动淘汰
- **重要性分层**：
  - 高频词（S > 10）：放入长期缓存层
  - 中频词（S 1~10）：标准缓存层
  - 低频词（S < 1）：快速衰减层

### 6.3 缓存结构分层建议

```
┌─────────────────────────────────────┐
│         实时查询层 (Ebbinghaus)       │  ← O(1) 权重计算
├─────────────────────────────────────┤
│  短期缓存层 (最近对话, high retention) │
│  淘汰策略: time_boost + Ebbinghaus  │
├─────────────────────────────────────┤
│  长期记忆层 (反复讨论的概念)            │
│  淘汰策略: S > threshold             │
├─────────────────────────────────────┤
│        FAISS/BM25 索引层              │  ← 现有实现，无需改动
└─────────────────────────────────────┘
```

---

## 七、对话记录索引优化建议

### 7.1 当前问题

根据Semantic Cache测试报告：
- "小龙虾P2P聊天" 语义漂移到"养虾"内容
- "贵庚记忆系统" 第1条命中内存监控而非记忆系统
- context_after 全空（timestamp排序问题）

### 7.2 关键词提取增强

```python
# 改进：从对话中提取关键词时叠加Ebbinghaus权重
def extract_keywords_with_boost(message: str, tracker: EbbinghausKeywordTracker,
                                 top_n: int = 10) -> list[tuple[str, float]]:
    # 1. 基础TF-IDF关键词提取
    keywords = extract_tfidf_keywords(message, top_n=top_n * 2)

    # 2. 获取Ebbinghaus权重
    scored = []
    for kw, tfidf_score in keywords:
        ebbinghaus_weight = tracker.get_weight(kw)
        combined = 0.6 * normalize(tfidf_score) + 0.4 * ebbinghaus_weight
        scored.append((kw, combined))

    # 3. 排序返回Top-N
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]
```

### 7.3 分层索引策略

| 层级 | 存储内容 | 淘汰策略 | Ebbinghaus作用 |
|------|---------|---------|--------------|
| L0 (热) | 最近50条对话的完整记录 | 时间+权重双维度 | 权重>0.8时永不淘汰 |
| L1 (温) | 最近1000条对话摘要 | LRU + 保留率<5% | 高频词下沉到L1 |
| L2 (冷) | 全量FAISS向量索引 | 仅BM25精确命中唤醒 | 长期知识保留 |

### 7.4 索引更新频率

- **Ebbinghaus状态更新**：每次消息时实时更新（O(1)）
- **持久化**：每10分钟或每次会话结束时写入磁盘
- **FAISS索引重建**：维持现有增量索引策略，Ebbinghaus不影响

---

## 八、参考资料

1. Ebbinghaus, H. (1885). *Memory: A Contribution to Experimental Psychology*
2. FOREVER: Forgetting Curve-Inspired Memory Replay for Language Models - arXiv:2601.03938
3. The Ebbinghaus Forgetting Curve Predicts AI Agent Memory Decay - moltbook.com
4. Semantic Cache Optimization Report - night-build/reports/Semantic-Cache-Optimization-Report.md
5. Transformer-XL: Attentive Language Models Beyond Fixed-Length Context
6. RWKV: Reinventing RNNs for the Transformer Era

---

*调研完成 | 2026-03-30*
