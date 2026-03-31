# A序列任务建议：自适应兴趣权重追踪系统

**任务编号：** A-001  
**创建时间：** 2026-03-30  
**状态：** 建议中，待确认

---

## 任务名称
**自适应兴趣权重追踪系统（Adaptive Interest Weight Tracker）**

---

## 任务类型
🔧 **功能开发** | 🧪 **算法实现**

---

## 背景与动机

当前 Semantic Cache（见 `Semantic-Cache-Optimization-Report.md`）使用固定 `time_boost`（0.08~0.15）来优先近期消息，但存在以下问题：

1. **静态权重**：用户反复讨论的长期话题没有额外加权，久远但重要的概念被遗忘
2. **无兴趣追踪**：无法识别用户当前最关心的N个话题
3. **语义漂移**：多义词场景（"小龙虾P2P"漂移到"养虾"）说明仅靠Embedding不够
4. **上下文窗口问题**：context_after 全空，timestamp排序存疑

**用户需求**：讨论越多 → 权重越高 → 响应越精准；长时间不讨论 → 自然衰减

---

## 具体描述

### 目标
实现一个基于 **Ebbinghaus 遗忘曲线建模** 的关键词权重衰减算法，作为 Semantic Cache 的外挂权重层，无需修改底层 FAISS/BM25 索引。

### 核心算法

```
记忆保留率：R(t) = e^(-Δt / S)
记忆强化：   S_new = S_old × strength_factor  （每次被提及）
最终权重：   w = TF-IDF(w) × R(t)
```

### 关键参数

| 参数 | 建议值 | 说明 |
|------|--------|------|
| initial_strength | 1.0 | 初始记忆稳定性 |
| strength_factor | 1.5 | 每次提及S增大50% |
| min_retention | 0.01 | 保留率<1%时清除 |
| 半衰期（初始） | ~42秒 | S=1.0时，T½=S×ln2 |

### 集成点

1. **相似度重排层**：查询时叠加 Ebbinghaus 权重到 raw_similarity
2. **缓存淘汰层**：retention < 阈值时主动淘汰
3. **缓存分层**：高频词（S > 阈值）下沉到长期缓存

---

## 交付物

### 1. 核心代码
```
src/ebbinghaus_tracker.py   # 遗忘曲线追踪器（纯Python，O(1)计算）
tests/test_ebbinghaus.py     # 单元测试（pytest）
```

### 2. Semantic Cache 集成
```
修改 semantic_search() 函数，增加 keyword_weight_factor 参数
公式：final_score = raw_sim × (0.5 + 0.5 × avg_keyword_weight) + time_boost
```

### 3. 监控接口
```
GET /api/keywords/top?n=10   # 返回当前权重最高的N个关键词
GET /api/keywords/stats      # 返回统计信息（总词数、平均S值、保留率分布）
POST /api/keywords/reset    # 重置追踪状态（测试用）
```

### 4. 配置项
```json
{
  "ebbinghaus": {
    "enabled": true,
    "initial_strength": 1.0,
    "strength_factor": 1.5,
    "min_retention": 0.01,
    "decay_interval_seconds": 300
  }
}
```

---

## 技术约束

1. **计算复杂度**：单次提及更新 O(1)，批量查询 O(K)，K=关键词数
2. **内存**：状态仅存储 `{word: (S, last_time, base_weight)}`，每词约100字节
3. **持久化**：状态每10分钟或会话结束时异步写入 Redis/文件
4. **兼容性**：Python 3.8+，无新增外部依赖

---

## 分阶段计划

### Phase 1：核心追踪器（预计1天）
- [ ] 实现 `EbbinghausKeywordTracker` 类
- [ ] 单元测试覆盖：提及、强化、衰减、清除
- [ ] 性能基准测试（10万词级别）

### Phase 2：Semantic Cache 集成（预计1天）
- [ ] 修改相似度计算，加入 keyword_factor
- [ ] A/B测试：新旧策略对比（相同查询集的命中率）
- [ ] 修复 context_after 全空问题（timestamp排序）

### Phase 3：持久化与监控（预计0.5天）
- [ ] Redis持久化（pickle/json格式）
- [ ] 管理API接口
- [ ] 监控面板（grafana指标）

### Phase 4：调参与优化（预计0.5天）
- [ ] A/B测试 strength_factor（1.3 vs 1.5 vs 1.7）
- [ ] 分析"小龙虾P2P"等边界case
- [ ] 与长期记忆层集成

---

## 验收标准

| 指标 | 目标 | 测量方法 |
|------|------|---------|
| 重复话题命中率 | > 90%（第3次提及后） | 相同查询3次命中测试 |
| 遗忘恢复时间 | < 5秒（重新提及后权重恢复） | 权重恢复曲线测量 |
| 内存占用 | < 50MB（10万词状态） | 内存profiling |
| API延迟 | < 10ms（单次查询） | Flask/ FastAPI benchmarks |
| context_after修复 | 100%（timestamp正确排序） | 单元测试验证 |

---

## 风险与备选

| 风险 | 应对 |
|------|------|
| strength_factor调参困难 | 提供自适应版本（根据mention频率自动调整） |
| 高并发下状态不一致 | 使用Redis HASH存储，支持分布式 |
| 冷启动问题（新用户无历史） | 降级为固定 time_boost（现有逻辑） |

**备选方案**：如果 Ebbinghaus 效果不佳，可降级为简单的 TF-IDF+指数衰减（参见调研报告第二章）。

---

## 相关文档

- 调研报告：`harness/robot/night-build/reports/A-自适应关键词权重算法调研.md`
- 现有架构：`harness/robot/night-build/reports/Semantic-Cache-Optimization-Report.md`
- NIGHT-BUILD策略：`harness/robot/night-build/NIGHT-BUILD-STRATEGY-v2.md`

---

*任务建议完毕 | 2026-03-30*
