# F-013: AI 搜索 API

## 问题描述
人用 Fuse.js 模糊搜索，但 AI agent 需要程序化搜索 API。当前搜索是前端 JS 实现，没有后端接口。

## 文件
- `/Users/lr/.openclaw/workspace/tools/docs-server.py`

## 修复步骤

### Step 1：在 do_GET 中添加搜索 API 路由

```python
        # AI Search API: /api/search?q=xxx&limit=10
        if path == "/api/search":
            from urllib.parse import parse_qs as _parse_qs
            params = _parse_qs(self.query_string)
            query = params.get('q', [''])[0].strip()
            limit = int(params.get('limit', ['10'])[0])

            if not query:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "missing q parameter"}).encode())
                return

            # Use the same search index as Fuse.js
            index = json.loads(_build_search_index())
            # Simple keyword matching (case-insensitive)
            results = []
            q_lower = query.lower()
            for item in index:
                text = item.get('text', '').lower()
                title = item.get('title', '').lower()
                # Score: title match > text match, count occurrences
                title_score = text.count(q_lower) * 1 + title.count(q_lower) * 3
                if title_score > 0:
                    results.append({
                        'title': item['title'],
                        'url': item['url'],
                        'score': title_score,
                        'snippet': item['text'][:200] + '...'
                    })

            # Sort by score descending, take top N
            results.sort(key=lambda x: x['score'], reverse=True)
            results = results[:limit]

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"query": query, "count": len(results), "results": results}, ensure_ascii=False).encode())
            return
```

### Step 2：重启并验证

```bash
lsof -ti:18998 | xargs kill -9 2>/dev/null; sleep 1; cd /Users/lr/.openclaw/workspace && nohup python3 tools/docs-server.py > /tmp/docs-server.log 2>&1 & sleep 2
```

### Step 3：用 curl 测试
```bash
curl -s "http://127.0.0.1:18998/docs.0-1.ai/api/search?q=机械臂&limit=5" | python3 -m json.tool
curl -s "http://127.0.0.1:18998/docs.0-1.ai/api/search?q=Ebbinghaus&limit=3" | python3 -m json.tool
curl -s "http://127.0.0.1:18998/docs.0-1.ai/api/search?q=Phase+4&limit=5" | python3 -m json.tool
```

## 验证标准
- [ ] `/api/search?q=机械臂` 返回 JSON，包含 arm.md 的结果
- [ ] `/api/search?q=Ebbinghaus` 返回调研报告结果
- [ ] 结果有 score 排序和 snippet
- [ ] 无 q 参数时返回 400
