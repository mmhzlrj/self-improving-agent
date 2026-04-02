# F-007: 搜索索引扩展（模块+报告）

## 问题描述
`_build_search_index()` 只索引 `docs/*.md`（根目录 18 个旧文档）和 SOP 内容，但模块文档（modules/*.md）和调研报告（reports/*.md）不在搜索范围内。

## 文件
- `/Users/lr/.openclaw/workspace/tools/docs-server.py`

## 当前状态
搜索索引覆盖：
- `docs/*.md`（18 个根目录 md）
- SOP（harness/robot/ROBOT-SOP.md）

未覆盖：
- `docs/modules/*.md`（7 个模块文档）
- `harness/robot/night-build/reports/*.md`（34 个调研报告）

## 修复步骤

### Step 1：读取当前 _build_search_index() 函数
```bash
sed -n '88,130p' /Users/lr/.openclaw/workspace/tools/docs-server.py
```

### Step 2：在搜索索引中添加模块文档和调研报告

在 `_build_search_index()` 函数的 SOP 索引代码之后、`return json.dumps(index, ensure_ascii=False)` 之前，添加：

```python
    # Also index module docs
    modules_dir = DOCS_ROOT / "modules"
    if modules_dir.exists():
        for md_file in sorted(modules_dir.glob("*.md")):
            try:
                text = md_file.read_text(encoding="utf-8")
                title_m = re.match(r'^#\s+(.+)$', text)
                title = title_m.group(1).strip() if title_m else md_file.stem
                plain = re.sub(r'#{1,6}\s+', '', text)
                plain = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', plain)
                plain = re.sub(r'[*_`~]', '', plain)
                plain = re.sub(r'\n+', ' ', plain).strip()[:500]
                index.append({
                    "title": f"[模块] {title}",
                    "text": plain,
                    "url": f"{SCRIPT_PREFIX}/modules/{md_file.stem}.html"
                })
            except Exception:
                pass

    # Also index research reports
    reports_dir = SOP_ROOT / "night-build" / "reports"
    if reports_dir.exists():
        for md_file in sorted(reports_dir.glob("*.md")):
            try:
                text = md_file.read_text(encoding="utf-8")
                title_m = re.match(r'^#\s+(.+)$', text)
                title = title_m.group(1).strip() if title_m else md_file.stem
                plain = re.sub(r'#{1,6}\s+', '', text)
                plain = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', plain)
                plain = re.sub(r'[*_`~]', '', plain)
                plain = re.sub(r'\n+', ' ', plain).strip()[:500]
                index.append({
                    "title": f"[报告] {title}",
                    "text": plain,
                    "url": f"{SCRIPT_PREFIX}/reports/{md_file.name}"
                })
            except Exception:
                pass
```

### Step 3：重启并验证
```bash
lsof -ti:18998 | xargs kill -9 2>/dev/null; sleep 1; cd /Users/lr/.openclaw/workspace && nohup python3 tools/docs-server.py > /tmp/docs-server.log 2>&1 & sleep 2; curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18998/docs.0-1.ai/
```

### Step 4：验证搜索能找到模块和报告
用浏览器打开 docs.0-1.ai，在搜索框输入 "机械臂"、"Ebbinghaus" 等关键词，确认能搜到模块文档和调研报告。

## 验证标准
- [ ] 搜索"机械臂"能找到 arm.md
- [ ] 搜索"Ebbinghaus"能找到调研报告
- [ ] 搜索"贵庚"能找到 gui-geng.md
- [ ] 搜索结果显示正确的前缀标签（[模块] 或 [报告]）
