# SOP: 0-1 记忆系统三步建设方案

> **版本**: v1.0
> **创建日期**: 2026-04-02
> **更新日期**: 2026-04-02
> **SOP 路径**: `harness/robot/night-build/SOP-Self-Memory-3Step.md`

---

## 一、背景与目标

### 1.1 为什么自己做

MemOS 是一个通用记忆系统，功能完整但：
- 数据 Schema 必须遵循 MemOS 规范
- 架构是通用设计，不一定契合 0-1 的五阶段路线图
- 引入外部依赖增加维护成本
- Skill Evolution、Task 归纳的逻辑我们可以按需定制

**自己做 = 完全自主 + 按需扩展 + 无外部依赖**

### 1.2 现有资源盘点

| 资源 | 位置/状态 | 可用于 |
|------|----------|--------|
| Semantic Cache | Ubuntu 192.168.1.18:5050, FAISS, 1166 条索引 | Task 归纳 + Multi-agent 共享 |
| InterestTracker | Ubuntu server.py, 已有跨 session 追踪 | Multi-agent namespace 参考 |
| Session 历史 | MacBook `sessions/`, 每天新增 | Task 归纳训练数据 |
| LLM API | 豆包/DeepSeek/GLM 等 | 提炼、聚类 |
| Smart Context Hook | `scripts/smart_context_hook.py` | 注入逻辑参考 |

### 1.3 三步规划

```
Step 1: Task 归纳（Session → 结构化任务）
         ↓
Step 2: Multi-agent 共享（Semantic Cache + namespace）
         ↓
Step 3: Skill Evolution（聚类 → 技能提炼 → 自动化）
```

---

## 二、Step 1: Task 归纳

### 2.1 目标

在每个 session 结束时（或定时），自动调用 LLM 提炼摘要：

```json
{
  "task_id": "session_xxx",
  "task_name": "Jetson Nano 网络配置",
  "outcome": "解决了 WiFi 断开问题",
  "decisions": ["改用 linux-firmware", "设置静态 IP"],
  "open_issues": ["尚未验证稳定性"],
  "key_insights": ["ESP32-Cam 需要独立电源"],
  "related_tasks": ["T-01-A05", "T-01-A08"],
  "timestamp": "2026-04-02T00:30:00+08:00"
}
```

### 2.2 数据流

```
Session 结束触发
    ↓
提取 session 内容（最近的 user/assistant 对话）
    ↓
LLM 提炼（prompt 工程）
    ↓
存入 tasks 表（SQLite 或 JSON 文件）
    ↓
关联相关 sessions（embedding 相似度）
    ↓
输出到记忆文件（memory/YYYY-MM-DD-TaskSummary.md）
```

### 2.3 实现方案

**文件存储**（轻量，够用）：
- 主文件：`~/.semantic_cache/tasks/tasks_index.jsonl`
- 每日摘要：`~/.semantic_cache/tasks/daily/YYYY-MM-DD.md`

**LLM Prompt 模板**：

```
你是 0-1 项目的任务归纳助手。以下是一个 session 的对话记录：

{对话内容}

请提炼为结构化任务记录，输出 JSON 格式：
{
  "task_name": "简短任务名称",
  "outcome": "最终结果/产出",
  "decisions": ["决策点1", "决策点2"],
  "open_issues": ["未解决的问题1"],
  "key_insights": ["关键洞察1"],
  "related_task_ids": ["相关任务ID（如果有）"],
  "confidence": "high/medium/low（提炼把握度）"
}

注意：
- task_name 要具体，不要泛泛
- 只输出 JSON，不要解释
- 如果对话内容太少（<3轮），confidence 设为 low
```

### 2.4 触发机制

**方案 A：Session 结束时触发**（推荐）
- 在 Smart Context Hook 中，session 结束时调用
- 需要检测 session 结束事件

**方案 B：定时触发**（简单）
- 每天 23:00 cron 扫描当天所有 sessions
- 批量提炼

**初期先用方案 B**，快速验证效果，后续再接方案 A。

### 2.5 验收标准

- [ ] 每天定时扫描当天 sessions
- [ ] LLM 提炼输出格式正确
- [ ] tasks_index.jsonl 正确追加
- [ ] 每日摘要文件生成
- [ ] 与 Semantic Cache 的关联（相似 session 链接）

---

## 三、Step 2: Multi-agent 共享

### 3.1 目标

扩展 Semantic Cache 支持多层级 namespace，实现跨 session 记忆共享。

### 3.2 Namespace 设计

```
Semantic Cache namespace 层级：

namespace: "session"（现有，默认）
  └── 每个 session 独立索引
  └── 只在 session 内召回

namespace: "user"（新增）
  └── 跨 session 共享
  └── session 结束时写入重要记忆
  └── 用于： InterestTracker、跨项目知识

namespace: "project"（新增）
  └── 按项目隔离（robot / 0-1-报名 / 小红书 等）
  └── 定向召回

namespace: "global"（新增）
  └── 全局知识（技术文档、最佳实践）
  └── 只读，所有 agent 可用
```

### 3.3 实现方案

**在 Semantic Cache server.py 中增加 namespace 支持**：

```python
# Ubuntu: ~/.semantic_cache/server.py

NAMESPACES = {
    "session": {"isolated": True, "write_on_session_end": False},
    "user": {"isolated": False, "write_on_session_end": True, "source": "auto_extract"},
    "project": {"isolated": True, "write_on_session_end": True, "projects": ["robot", "0-1"]},
    "global": {"isolated": False, "write_on_session_end": False, "readonly": True}
}

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    namespaces = data.get('namespaces', ['session'])  # 可查多个 namespace
    query_text = data['query']
    
    results = []
    for ns in namespaces:
        ns_results = vector_db.query(query_text, filter={"namespace": ns})
        results.extend(ns_results)
    
    # 重排返回
    return sorted(results, key=lambda x: x['score'], reverse=True)

@app.route('/index', methods=['POST'])
def index():
    data = request.json
    namespace = data.get('namespace', 'session')
    # 写入对应 namespace
```

**Task 归纳结果自动写入 user namespace**：
- Step 1 的 tasks 归纳结果 → 写入 `user` namespace
- InterestTracker 已有类似逻辑，直接复用

### 3.4 验收标准

- [ ] Semantic Cache 支持 namespace 参数
- [ ] session 结束自动写入 user namespace
- [ ] 跨 namespace 查询正确合并结果
- [ ] 与 InterestTracker 的数据互通
- [ ] Task 归纳结果可被其他 session 召回

---

## 四、Step 3: Skill Evolution

### 4.1 目标

从历史 Task 归纳数据中，自动提炼出可复用的技能模板。

### 4.2 数据流

```
定期扫描 tasks（每天/每周）
    ↓
Embedding 聚类（相似 task_name + similar decisions → 归为一类）
    ↓
每类积累 N 个样本后（N = 建议 3-5）
    ↓
LLM 提炼为技能模板：
{
  "skill_name": "Jetson_Nano_WiFi_Fix",
  "description": "解决 Jetson Nano WiFi 断开问题",
  "trigger": "什么情况下调用这个技能",
  "input_schema": { ... },
  "output_schema": { ... },
  "steps": ["步骤1", "步骤2"],
  "examples": [task1, task2, task3],
  "version": "1.0",
  "confidence": 0.85,
  "source_tasks": ["task_id_1", "task_id_2"]
}
    ↓
存入 skills 表
    ↓
下次遇到类似场景 → 自动建议使用这个技能
```

### 4.3 聚类算法

```python
# 基于 Semantic Cache 的 FAISS 聚类
from sentence_transformers import SentenceTransformer
import faiss

model = SentenceTransformer('all-MiniLM-L6-v2')

# 所有 tasks 的 task_name + outcome 合并为文本
texts = [f"{t['task_name']} {t['outcome']}" for t in tasks]
embeddings = model.encode(texts)

# FAISS 聚类
n_clusters = 5
quantizer = faiss.IndexFlatL2(embeddings.shape[1])
index = faiss.IndexIVFFlat(quantizer, embeddings.shape[1], n_clusters)
index.train(embeddings)
index.add(embeddings)

# 查找最近邻
D, I = index.search(query_embedding.reshape(1,-1), k=5)
```

### 4.4 LLM 提炼 Prompt

```
你是 0-1 项目的技能提炼助手。以下是一组相似的任务记录：

{JSON 列表 of 3-5 个 tasks}

这些任务有相似的模式和解决方案。请提炼为一个可复用的技能模板，输出 JSON：

{
  "skill_name": "技能名称（用下划线连接，如 Jetson_Nano_WiFi_Fix）",
  "description": "一句话描述技能用途",
  "trigger": "什么情况下应该调用这个技能（触发条件）",
  "input_schema": {
    "type": "object",
    "properties": { ... },
    "required": [...]
  },
  "output_schema": {
    "type": "object", 
    "properties": { ... }
  },
  "steps": ["步骤1", "步骤2", "步骤3"],
  "prerequisites": ["前置条件1"],
  "anti_patterns": ["常见的错误做法"],
  "examples_count": 3,
  "confidence": 0.0-1.0,
  "version": "1.0"
}

注意：
- skill_name 要有语义，用下划线分隔
- steps 要具体可执行
- anti_patterns 要有实际参考价值
```

### 4.5 验收标准

- [ ] 定时扫描 tasks 积累数据
- [ ] 聚类算法正确运行
- [ ] LLM 提炼输出格式正确
- [ ] skills 库正确存储
- [ ] 新 session 可查询/建议相关技能

---

## 五、任务分工

| Step | Task ID | 任务 | 优先级 | 依赖 |
|------|---------|------|--------|------|
| 1 | T-01-A21 | Task 归纳实现 | P0 | 无 |
| 2 | T-01-A22 | Multi-agent 共享 | P1 | A21 完成 |
| 3 | T-01-A23 | Skill Evolution | P2 | A22 完成 |

---

## 六、错误处理规范

### 6.1 遇到不懂的地方

**规则**：
1. 先用 `memory_search` 检索相关历史记录
2. 再用 `deep-research`（zhiku/tavily）调研
3. 调研无果 → 记录到 `problem-log.md` → 跳过该步骤继续
4. 绝不能卡在一个点上不动

**记录格式**：
```markdown
## [时间] 问题：<问题描述>

**尝试过的方案**：
- 方案A：...
- 方案B：...

**调研结果**：
- 链接1：...
- 链接2：...

**决定**：
- 暂时跳过 / 用替代方案 / 继续深挖
```

### 6.2 遇到错误

**立即记录**：
```markdown
## [时间] 错误：<错误描述>

**错误信息**：
```
<粘贴错误输出>
```

**原因分析**：
- ...

**解决方案**：
- ...

**验证结果**：
- ✅/❌
```

---

## 七、参考资料

| 资源 | 路径/链接 |
|------|----------|
| Semantic Cache Server | Ubuntu: `~/.semantic_cache/server.py` |
| Smart Context Hook | `scripts/smart_context_hook.py` |
| InterestTracker | Ubuntu: `~/semantic_cache/server.py` |
| Session 历史 | `~/.openclaw/agents/main/sessions/` |
| MemOS Skill Evolution | https://github.com/MemTensor/MemOS |
| Deep Research Skill | `skills/deep-research/SKILL.md` |
| Self-improving Agent | `skills/self-improving-agent/SKILL.md` |
