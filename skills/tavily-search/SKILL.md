---
name: tavily-search
description: 使用 Tavily 搜索引擎进行实时网络搜索
---

# Tavily Search Skill

使用 Tavily AI 搜索引擎进行实时网络搜索。

## 安装

确保已安装 tavily Python 包：
```bash
pip3 install tavily
```

## 使用方式

通过 exec 运行 Python 脚本进行搜索：

```bash
python3 ~/.openclaw/workspace/skills/tavily-search/search.py "<搜索查询>" [max_results]
```

示例：
```bash
python3 ~/.openclaw/workspace/skills/tavily-search/search.py "Tesla stock price" 5
python3 ~/.openclaw/workspace/skills/tavily-search/search.py "最新 AI 新闻" 3
```

## 使用场景

- 查找最新新闻和信息
- 获取实时股票价格
- 搜索特定主题的最新发展
- 研究问题和事实核查

## 搜索参数

- `query`: 搜索查询字符串（必需）
- `max_results`: 最大结果数量（可选，默认 5）

## 输出格式

搜索返回结果，包含：
- 标题和 URL
- 内容摘要
- 相关度评分
- AI 生成的摘要（如果可用）
- 响应时间
