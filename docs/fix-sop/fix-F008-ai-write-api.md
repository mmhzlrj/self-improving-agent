# F-008: AI 写入 API（提交报告/更新文档）

## 问题描述
docs.0-1.ai 是 AI 和人协作的文件管理系统，但目前只有人能在浏览器里操作。AI 做完调研后无法自动提交报告或更新文档，需要手动放文件。

## 文件
- `/Users/lr/.openclaw/workspace/tools/docs-server.py`

## 修复步骤

### Step 1：读取现有 do_POST 方法
```bash
grep -n "def do_POST" /Users/lr/.openclaw/workspace/tools/docs-server.py
```
目前 do_POST 只处理 `/api/review` 路由。

### Step 2：在 do_POST 中添加新的 API 路由

在 `def do_POST(self):` 中，在 `self.send_error(404)` 之前，添加以下路由：

#### 路由 A：提交调研报告 `/api/reports/submit`
```python
        # Submit new research report
        if path == "/api/reports/submit":
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))
            title = body.get('title', 'Untitled Report')
            content = body.get('content', '')
            filename = body.get('filename', '')  # 可选，指定文件名

            if not filename:
                # 自动生成文件名：用日期+标题简写
                from datetime import datetime as _dt
                date_str = _dt.now().strftime('%Y-%m-%d')
                safe_title = re.sub(r'[^\w\u4e00-\u9fff-]', '', title)[:50]
                filename = f"{date_str}-{safe_title}.md"

            # 确保文件名以 .md 结尾
            if not filename.endswith('.md'):
                filename += '.md'

            reports_dir = SOP_ROOT / "night-build" / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            report_file = reports_dir / filename
            report_file.write_text(f"# {title}\n\n{content}", encoding='utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "filename": filename, "url": f"{SCRIPT_PREFIX}/reports/{filename}"}).encode())
            return
```

#### 路由 B：更新模块文档 `/api/modules/update`
```python
        # Update module document
        if path == "/api/modules/update":
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))
            slug = body.get('slug', '')
            content = body.get('content', '')

            if not slug:
                self.send_error(400)
                return

            # 验证 slug 是合法的模块名
            valid_slugs = ['gui-geng', 'lewm', 'arm', 'vision', 'suction', 'locomotion', 'face']
            if slug not in valid_slugs:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": f"无效模块: {slug}"}).encode())
                return

            modules_dir = DOCS_ROOT / "modules"
            modules_dir.mkdir(parents=True, exist_ok=True)
            module_file = modules_dir / f"{slug}.md"
            module_file.write_text(content, encoding='utf-8')

            # 更新版本号
            try:
                bump_module_version(slug, "modified", f"API 更新 {slug}.md")
            except Exception:
                pass

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "slug": slug}).encode())
            return
```

#### 路由 C：获取文档内容 `/api/docs/get`（GET 方法）
```python
# 这个在 do_GET 中添加
```

在 `def do_GET(self):` 中找到合适位置（如在 reports 路由附近）添加：
```python
        # API: get document content for AI reading
        if path == "/api/docs/get":
            from urllib.parse import parse_qs as _parse_qs
            params = _parse_qs(self.query_string)
            doc_type = params.get('type', [''])[0]  # 'module' or 'report'
            doc_name = params.get('name', [''])[0]

            if doc_type == 'module':
                f = DOCS_ROOT / "modules" / f"{doc_name}.md"
            elif doc_type == 'report':
                f = SOP_ROOT / "night-build" / "reports" / doc_name
            else:
                self.send_error(400)
                return

            if not f.exists():
                self.send_error(404)
                return

            content = f.read_text(encoding='utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            return
```

### Step 3：重启并验证
```bash
lsof -ti:18998 | xargs kill -9 2>/dev/null; sleep 1; cd /Users/lr/.openclaw/workspace && nohup python3 tools/docs-server.py > /tmp/docs-server.log 2>&1 & sleep 2
```

### Step 4：用 curl 测试 API

**测试提交报告：**
```bash
curl -s -X POST http://127.0.0.1:18998/docs.0-1.ai/api/reports/submit \
  -H "Content-Type: application/json" \
  -d '{"title":"测试报告","content":"这是AI自动提交的测试报告。\n\n## 测试内容\n- 项目1\n- 项目2"}'
```
期望返回：`{"ok": true, "filename": "2026-04-01-测试报告.md", "url": "/docs.0-1.ai/reports/2026-04-01-测试报告.md"}`

**测试获取文档：**
```bash
curl -s "http://127.0.0.1:18998/docs.0-1.ai/api/docs/get?type=module&name=arm"
```
期望返回：arm.md 的 Markdown 内容

**测试更新模块：**
```bash
curl -s -X POST http://127.0.0.1:18998/docs.0-1.ai/api/modules/update \
  -H "Content-Type: application/json" \
  -d '{"slug":"arm","content":"# 机械臂模块\n\n> 测试更新\n\n测试内容"}'
```

**清理测试数据：**
```bash
rm -f /Users/lr/.openclaw/workspace/harness/robot/night-build/reports/2026-04-01-测试报告.md
```

## 验证标准
- [ ] POST /api/reports/submit 能创建新报告
- [ ] GET /api/docs/get?type=module&name=arm 能读取模块文档
- [ ] POST /api/modules/update 能更新模块文档
- [ ] 测试完成后清理测试数据
