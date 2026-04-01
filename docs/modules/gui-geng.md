# 贵庚记忆系统

> 核心：Semantic Cache — Ubuntu 32GB RAM 节点

## 系统架构

```
MacBook (Gateway) ←→ Ubuntu (192.168.1.18:5050)
                              ↓
                    sentence-transformers
                    (all-MiniLM-L6-v2)
                              ↓
                         FAISS 索引
```

## 核心能力

- **语义搜索**：自然语言查询相关聊天记录
- **上下文补全**：注入历史相关对话到 prompt
- **InterestTracker**：基于 Ebbinghaus 遗忘曲线的兴趣追踪

## 索引状态

- 当前索引：**9669 条**聊天记录
- 类型分布：session, text, model_change, thinking_level_change, custom:model-snapshot

## InterestTracker

- 端点：`POST /interest/update`
- 查询：`GET /interest/search?query=...`
- 重置：`POST /interest/reset`
- 内存态：服务重启后数据清空

## 调用方式

```bash
# 语义搜索
curl -X POST http://192.168.1.18:5050/search \
  -H "Content-Type: application/json" \
  -d '{"query": "LeWM训练参数", "top_k": 5}'

# 上下文注入
curl -X POST http://192.168.1.18:5050/context \
  -d '{"query": "当前训练状态"}'
```

## 相关文档

- Smart Context Hook：`~/.openclaw/workspace/scripts/smart_context_hook.py`
- 服务脚本：`~/semantic_cache/server.py`
