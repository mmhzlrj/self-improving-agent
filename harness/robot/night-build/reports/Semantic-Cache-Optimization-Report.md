## Semantic Cache 7项优化测试报告

**测试时间：** 2026-03-29 21:00 GMT+8  
**服务器：** http://192.168.1.18:5050  
**索引规模：** 6656 条消息

---

### 测试 1：基础语义搜索（#1 权重调优 + #6 Embedding 预处理 + #7 去重）

| 查询 | hit_count | top1 similarity | top1 raw_sim | top1 time_boost | top1 role | top1 text（前80字） | 语义相关？ |
|------|-----------|----------------|--------------|-----------------|-----------|---------------------|-----------|
| 贵庚记忆系统 | 3 | 0.659 | 0.509 | 0.15 | toolResult | memory.used [MiB], memory.free [MiB] 232 MiB, 5500 MiB | ⚠️ 部分相关（搜索"贵庚记忆系统"但第1条是内存监控，第2条是 MEMORY.md 相关，第3条是贵庚章节目录） |
| Jetson Nano 配置 | 3 | 0.729 | 0.579 | 0.15 | toolResult | /Users/lr/.openclaw/workspace/docs//jetson-nano-opensclaw-video-stream.md | ✅ 相关（Jetson Nano 文档路径） |
| OpenClaw 升级 | 3 | 0.816 | 0.736 | 0.08 | user | 你是openclaw吗 | ✅ 相关（与 openclaw 版本升级相关） |
| 小龙虾P2P聊天 | 3 | 0.668 | 0.518 | 0.15 | assistant | Let me also do a direct web search for QQ养虾空间 specifically: | ❌ 不相关（搜索 P2P 却找到养虾相关内容，语义漂移） |
| T-020 | 3 | 0.748 | 0.598 | 0.15 | toolResult | T-0002 updated to success | ✅ 相关（T-00xx 任务编号序列） |

**观察：**
- time_boost 统一为 0.15（新消息）或 0.08（早期消息），权重调优生效
- 所有结果 raw_similarity + time_boost = similarity，公式正确
- context_before 有内容但 context_after 全部为空（见测试3）
- "小龙虾P2P聊天" 语义漂移明显，Embedding 预处理可能对中文多义词效果有限

---

### 测试 2：角色过滤（#2）

**查询 "贵庚"：**

| 模式 | hit_count | 结果 |
|------|-----------|------|
| roles=["user"] | 1 | 文本: "配置"，role: user，session: c375d830（早期会话） |
| roles=["user","assistant","toolResult","system"] + include_system=true | 3 | 文本: "129"、"Successfully wrote..."、"Python 5.23.0"，role: toolResult/system |

**结论：✅ 通过** — roles 参数有效过滤结果：
- 仅 user 时只返回 1 条（"配置"）
- 包含所有角色时返回 3 条（toolResult/system 为主）
- 不同 roles 参数确实返回不同结果集

---

### 测试 3：上下文窗口（#4 timestamp 修复）

| 查询 | context_before 非空？ | context_after 非空？ |
|------|----------------------|-------------------|
| 贵庚记忆系统 top_k=3 context_window=300 | ✅ 是（所有3条都有 context_before，内容为 session 中的前序消息） | ❌ 否（所有3条 context_after=[]） |

**问题：context_after 全部为空。** 这说明 timestamp 解析可能还有问题，导致无法正确找到会话中的后序消息。需要检查服务器端 timestamp 是否正确解析 session 内消息的顺序。

---

### 测试 4：BM25 精确匹配（#5）

#### T-020 三种模式对比

| 模式 | top1 similarity | top1 raw_sim/faiss_sim | top1 bm25_sim | top1 text |
|------|---------------|----------------------|--------------|-----------|
| semantic | 0.748 | raw=0.598 | - | T-0002 updated to success |
| bm25 | 1.15 | faiss=0 | 1.0 | T-0002 pending\nT-0003 pending\n...T-0034 pending |
| hybrid | 0.568 | faiss=0.598 | 0.0 | T-0002 updated to success |

**分析：**
- **BM25 对精确字符串 "T-020" 效果极强**：bm25_sim=1.0 找到完全匹配，但返回的是包含 "T-0020 pending" 等长列表，噪声大
- **语义模式**找到的是 "T-0002 updated"（相关但非精确），相似度 0.748
- **混合模式**和语义模式结果相同，但 similarity 明显偏低（0.568 vs 0.748），且 bm25_sim 全部为 0，说明 BM25 部分几乎没有贡献

#### FramePack / P2P 对比

| 关键词 | 模式 | hit_count | bm25_sim | text（首条） |
|--------|------|-----------|----------|-------------|
| FramePack | semantic | 3 | - | 正克隆到 'FramePack'... |
| FramePack | bm25 | 3 | 1.0 | Latest: windows / framepack_cu126_torch26.7z |
| P2P | semantic | 3 | - | 额度：600 - 315 = **285** ✅ |
| P2P | bm25 | 3 | 1.0 | drwxr-xr-x  lobster-p2p |

**结论：✅ BM25 功能正常，对精确关键词效果显著。** 但当前索引中 BM25 数据可能需要优化（长文本列表降低了可用性）。

---

### 测试 5：增量索引（#3）

```
{"message":"no changes","new_entries":0,"status":"ok"}
```

**结论：✅ 增量索引 API 正常** — 无新变化时返回 "no changes"，API 工作正常。实际增量更新需要在新文件写入时触发。

---

### 测试 6：min_boost 参数

| 查询 | 返回结果数 | 所有 time_boost > 0？ | min time_boost |
|------|-----------|---------------------|----------------|
| 贵庚 top_k=5 min_boost=true | 5 | ✅ 是 | 0.08 |

**结论：✅ 通过** — min_boost=true 时所有结果 time_boost > 0（0.08 ~ 0.15），过滤了无 boost 结果。5条结果全部来自有时间戳的记录。

---

### 总结

| 优化项 | 功能 | 测试结果 | 备注 |
|--------|------|---------|------|
| #1 权重调优 | time_boost 叠加到 similarity | ✅ 通过 | 0.15（新）/ 0.08（早）公式正确 |
| #2 角色过滤 | roles 参数过滤 | ✅ 通过 | user-only 返回1条，all-roles 返回3条 |
| #3 增量索引 | reindex?mode=incremental | ✅ 通过 | API 正常，逻辑待实际文件变化验证 |
| #4 上下文窗口 | context_before/after | ⚠️ 部分通过 | context_before 有内容；**context_after 全空**（疑似 timestamp 排序问题） |
| #5 BM25 精确匹配 | mode=semantic/bm25/hybrid | ✅ 通过 | BM25 对精确关键词效果显著（bm25_sim=1.0），但长文本需优化 |
| #6 Embedding 预处理 | 语义搜索质量 | ⚠️ 部分通过 | "贵庚记忆系统" 第1条是内存监控（不够精确）；"小龙虾P2P聊天" 漂移到养虾内容 |
| #7 去重 | 返回无重复 | ✅ 通过 | 未观察到重复条目 |

### 建议

1. **🔴 修复 context_after 为空问题**：检查 timestamp 解析逻辑，确认 session 内消息是否按时间正确排序
2. **🟡 优化 Embedding 预处理**：中文多义词（P2P→养虾）问题可能需要更精细的中文分词或 embedding 模型
3. **🟡 优化 BM25 长文本**：T-020 返回的 pending 列表太长，可以考虑按句子/行拆分索引
4. **🟢 混合模式调参**：hybrid 模式当前 similarity 偏低（0.568 vs semantic 0.748），BM25 权重可能需要上调

---

*测试执行：subagent | 2026-03-29 21:00 GMT+8*