# Semantic Memory Skill

通过语义搜索从历史聊天记录中检索相关内容，作为上下文注入当前对话。

## 工作原理

```
用户输入 → Semantic Cache (Ubuntu 32GB RAM)
            ↓ 语义检索
        相关历史片段 → 注入 system prompt → 回复
```

## 工具调用

**工具名**: `semantic_memory`

**参数**:
- `query` (string): 搜索查询
- `top_k` (number, optional): 返回数量，默认 5
- `threshold` (number, optional): 相似度阈值，默认 0.5

**示例调用**:
```
/semantic_memory 今天聊了什么关于 ubuntu 的内容
/semantic_memory jetson nano 的进度
```

## 返回格式

返回相关历史聊天片段，带相似度分数。

## 注意事项

- Semantic Cache 运行在 Ubuntu (192.168.1.18:5050)
- 索引了 1166 条聊天记录
- 每次对话前可自动调用检索相关上下文
