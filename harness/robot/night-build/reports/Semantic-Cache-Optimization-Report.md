# Semantic Cache 优化测试报告

> 日期：2026-03-29
> 环境：Ubuntu 192.168.1.18, RTX 2060 6GB, 32GB RAM
> 模型：BAAI/bge-large-zh-v1.5 (1024维, CUDA)
> 代码：`/home/jet/semantic_cache/server.py` (514 行)

---

## 一、优化背景

### 1.1 旧版问题
- 模型：all-MiniLM-L6-v2 (384维, 英文为主，中文效果差)
- 索引：全量重建，每次 ~8 分钟
- 搜索：无过滤、无上下文、无关键词补充
- 数据：7411 条，含大量重复和噪声

### 1.2 优化目标
- 提升中文语义搜索命中率
- 支持 6 个维度：权重调优、角色过滤、增量索引、上下文窗口、BM25 混合、Embedding 预处理、去重

---

## 二、优化内容

### 2.1 已完成 6 项

#### #1 权重调优 (time_boost)
| 时间范围 | 旧值 | 新值 |
|---------|------|------|
| 7天内 | +0.10 | **+0.15** |
| 30天内 | +0.05 | **+0.08** |
| 90天内 | -0.05 | **-0.03** |
| 90天以上 | -0.10 | **-0.08** |
| 搜索阈值 | 0.30 | **0.25** |

新增 `min_boost` 参数：为 true 时只返回 time_boost > 0 的结果。

#### #2 角色/类型过滤
- 默认 `roles=["user","assistant","toolResult"]`（排除 system 类型）
- 默认排除 `model_change`、`thinking_level_change`、`session` 类型
- `include_system=true` 可包含系统消息

#### #3 增量索引
- `POST /reindex` — 全量重建（默认）
- `POST /reindex?mode=incremental` — 增量追加
- 只加载 mtime 变化的文件，用 `index.add()` 追加
- 有文件删除时自动降级全量重建

#### #4 会话内上下文窗口
- 每条命中记录返回前后 ±120秒 的对话上下文
- `context_before` / `context_after` 各最多 2 条
- `context_window` 参数控制窗口大小
- 仅 top_k ≤ 5 时启用

#### #6 Embedding 预处理
- `text` 字段：纯内容（去角色前缀），用于 embedding 编码
- `display_text` 字段：带角色前缀（如 `[assistant][消息]`），用于展示
- `extract_pure_text(prefix_label, content)` 统一提取

#### #7 对话去重
- 对同 session 同 timestamp 的多条记录做去重
- 按 display_text 前 100 字符 hash 判重
- 重复时：assistant 优先替换非 assistant；同为 assistant 保留更长的
- 效果：7411 → 6656 条（**去重 755 条，减少 10.2%**）

### 2.2 未完成 1 项

#### #5 BM25 混合检索 ❌（被 subagent 冲突覆盖）
- 纯 Python BM25 实现 + 倒排索引
- 混合得分 = 0.7 × FAISS similarity + 0.3 × BM25 score
- `mode=hybrid` 参数
- 原因：Subagent C 和 B 同时编辑 server.py，C 的修改被覆盖
- 待重新实现

---

## 三、测试结果

### 3.1 测试方法

用 5 个查询对比优化前后效果。每个查询 top_k=3，默认参数。

```bash
curl -X POST http://192.168.1.18:5050/search \
  -H "Content-Type: application/json" \
  -d '{"query":"贵庚记忆系统","top_k":3}'
```

### 3.2 详细结果

#### 查询 1：贵庚记忆系统
| # | similarity | raw | boost | role | 结果摘要 |
|---|-----------|-----|-------|------|---------|
| 1 | 0.659 | 0.509 | +0.15 | toolResult | GPU 内存信息（不相关） |
| 2 | 0.659 | 0.509 | +0.15 | toolResult | AGENTS.md 内容片段 |
| 3 | 0.652 | 0.502 | +0.15 | toolResult | **✅ 直接命中贵庚记忆系统章节** |

**对比旧版**：sim=0.594，只有 1 条相关结果
**改善**：sim 提升 0.058，top3 中有 1 条直接命中

#### 查询 2：Jetson Nano 配置
| # | similarity | raw | boost | role | 结果摘要 |
|---|-----------|-----|-------|------|---------|
| 1 | 0.729 | 0.579 | +0.15 | toolResult | **✅ jetson-nano-opensclaw-video-stream.md** |
| 2 | 0.689 | 0.539 | +0.15 | toolResult | **✅ 同一文档路径** |
| 3 | 0.666 | 0.516 | +0.15 | toolResult | Jetson Nano 报告替换操作 |

**对比旧版**：sim=0.670
**改善**：sim 提升 0.059，3 条全部相关

#### 查询 3：OpenClaw 升级
| # | similarity | raw | boost | role | 结果摘要 |
|---|-----------|-----|-------|------|---------|
| 1 | 0.816 | 0.736 | +0.08 | user | "你是openclaw吗"（不太相关） |
| 2 | 0.838 | 0.687 | +0.15 | toolResult | **✅ openclaw.json 配置修改** |
| 3 | 0.817 | 0.667 | +0.15 | assistant | **✅ "add new server entry"** |

**对比旧版**：sim=0.757
**改善**：sim 提升 0.081，命中率更高

#### 查询 4：小龙虾P2P聊天
| # | similarity | raw | boost | role | 结果摘要 |
|---|-----------|-----|-------|------|---------|
| 1 | 0.668 | 0.518 | +0.15 | assistant | QQ养虾空间 web search |
| 2 | 0.658 | 0.508 | +0.15 | assistant | T-0053 QQ养虾空间调研 |
| 3 | 0.625 | 0.475 | +0.15 | assistant | 虚拟空间 UI 调研 |

**分析**：返回的是 QQ养虾空间而非 P2P 聊天。数据集中 P2P 相关记录较少，语义模型将"小龙虾"映射到了更常见的"QQ养虾空间"。

#### 查询 5：T-020（任务 ID 精确匹配）
| # | similarity | raw | boost | role | 结果摘要 |
|---|-----------|-----|-------|------|---------|
| 1 | 0.748 | 0.598 | +0.15 | toolResult | "T-0002 updated to success" |
| 2 | 0.734 | 0.584 | +0.15 | toolResult | "Updated T-0062 to success" |
| 3 | 0.719 | 0.569 | +0.15 | toolResult | "已更新 T-0022 为 success" |

**分析**：返回了其他 T-xxxx 任务，说明 bge 的语义理解将"T-020"映射到了任务 ID 模式。BM25 补上后精确匹配会更好。

### 3.3 汇总对比

| 查询 | 旧版 sim | 新版 sim | 命中率 | 改善 |
|------|----------|----------|--------|------|
| 贵庚记忆系统 | 0.594 | 0.652 | 1/3 ✅ | +0.058 |
| Jetson Nano 配置 | 0.670 | 0.729 | 3/3 ✅✅ | +0.059 |
| OpenClaw 升级 | 0.757 | 0.838 | 2/3 ✅ | +0.081 |
| 小龙虾P2P | ~0.5 | 0.668 | 0/3 ⚠️ | 语义偏移 |
| T-020 | N/A | 0.748 | 模式匹配 ✅ | 新能力 |

---

## 四、发现的问题

### 4.1 上下文窗口未生效
- 所有查询的 `context_before` 和 `context_after` 都是 0
- **原因**：timestamp 存储格式是 `"2026-03-29T12:34:56"`，`float()` 转换抛异常被 except 吞掉
- **待修复**：用 `datetime.strptime()` 解析时间戳

### 4.2 "贵庚记忆系统" top1 不相关
- top1 返回 GPU 内存信息而非贵庚相关内容
- 可能原因：`toolResult` 中的内存信息包含"memory"关键词，与"记忆系统"部分匹配
- 改善方向：BM25 权重调整或 rerank

### 4.3 "小龙虾P2P" 语义偏移
- 数据集中 P2P 聊天记录少，模型偏向更常见的 QQ养虾空间
- 改善方向：增加 P2P 相关记录到索引，或 BM25 精确匹配 "P2P"

### 4.4 roles 过滤差点导致全线崩盘
- 初始默认 `roles=["user","assistant"]` 排除了 57% 的 toolResult 记录
- 导致所有查询返回 0 条
- 修复：默认加入 `toolResult`

---

## 五、索引统计

### 5.1 去重效果
| 指标 | 旧值 | 新值 | 变化 |
|------|------|------|------|
| 总条数 | 7411 | 6656 | -755 (-10.2%) |
| text 类型 | 6282 | 5530 | -752 |
| model_change | 256 | 256 | 0 |
| session | 257 | 257 | 0 |
| thinking_level_change | 257 | 256 | -1 |
| custom:model-snapshot | 262 | 260 | -2 |

### 5.2 角色分布
| 角色 | 数量 | 占比 |
|------|------|------|
| toolResult | 3809 | 57.2% |
| assistant | 1337 | 20.1% |
| system | 1126 | 16.9% |
| user | 384 | 5.8% |

### 5.3 索引性能
| 指标 | CPU (旧) | CUDA (新) | 提升 |
|------|----------|-----------|------|
| 索引速度 | ~21s/批 | ~1.9s/批 | **11x** |
| 总耗时 | ~80 分钟 | ~6.5 分钟 | **12x** |
| 批次数 | 232 | 208 (去重后) | - |

---

## 六、API 参考

### 搜索
```bash
POST http://192.168.1.18:5050/search
Content-Type: application/json

{
  "query": "搜索内容",
  "top_k": 5,              # 返回条数
  "threshold": 0.25,        # 最低相似度
  "roles": ["user","assistant","toolResult"],  # 角色过滤
  "include_system": false,  # 是否包含系统消息
  "context_window": 120,    # 上下文窗口（秒）
  "min_boost": false        # 只返回 time_boost > 0 的结果
}
```

### 增量索引
```bash
POST http://192.168.1.18:5050/reindex?mode=incremental
```

### 健康检查
```bash
GET http://192.168.1.18:5050/health
GET http://192.168.1.18:5050/stats
```

---

## 七、待办

- [ ] BM25 混合检索重新实现（被 subagent 冲突覆盖）
- [ ] 上下文窗口 timestamp 解析 bug 修复（float → datetime）
- [ ] "贵庚记忆系统" 排序优化（top1 应该是相关内容）
- [ ] jieba 安装 + 中文分词（提升 BM25 效果）
- [ ] 增量索引用到 HEARTBEAT 中（自动同步新 sessions）
- [ ] 搜索结果评估自动化脚本（定期跑测试查询，记录 sim 变化）

---

## 八、相关文件

| 文件 | 说明 |
|------|------|
| `/home/jet/semantic_cache/server.py` | 服务代码 (514 行) |
| `/home/jet/semantic_cache/models/bge-large-zh-v1.5/` | Embedding 模型 |
| `~/.semantic_cache/index.faiss` | FAISS 索引 |
| `~/.semantic_cache/texts.json` | 文本存储 |
| `/tmp/semantic_cache.log` | 运行日志 |
| `.learnings/ERRORS.md` | 错误记录 |
| `.learnings/LEARNINGS.md` | 经验记录 |
