# F-003: Reports 审阅工作流实现

## 问题描述
Reports 页面只有静态列表，缺少审阅功能（采纳/拒绝按钮、备注栏、状态变更）。

## 文件
- `/Users/lr/.openclaw/workspace/tools/docs-server.py`

## 当前状态
- `load_reports()` 函数已存在，读取 `harness/robot/night-build/reports/*.md`
- `make_reports_list()` 已有 approved/pending 过滤
- `make_report_detail()` 已有报告详情页
- `REPORTS_STATUS = DOCS_ROOT / "reports" / "status.json"` 已定义
- 但**没有任何 API 接口**来修改状态，也没有前端审阅 UI

## 实现步骤

### Step 1: 确认 status.json 结构
创建 `docs/reports/status.json` 文件（如果不存在）：
```json
{}
```
每个报告的状态记录格式：
```json
{
  "A-Ebbinghaus-InterestTracker-实现报告.md": {
    "status": "pending",
    "reviewed_at": null,
    "reviewer_note": ""
  }
}
```

### Step 2: 添加状态变更 API 路由
在 `Handler.do_GET` 附近，添加 `do_POST` 方法或在现有路由中添加 POST 处理。

在 `Handler` 类中添加以下路由处理：

```python
def do_POST(self):
    path = self.path
    # 审阅 API：更新报告状态
    if path == f"{SCRIPT_PREFIX}/api/review":
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length))
        filename = body.get('filename', '')
        action = body.get('action', '')  # 'approve' or 'reject'
        note = body.get('note', '')
        
        # 验证文件存在
        reports_dir = SOP_ROOT / "night-build" / "reports"
        if not (reports_dir / filename).exists():
            self.send_error(404)
            return
        
        # 加载/创建 status.json
        status_file = REPORTS_STATUS
        if status_file.exists():
            statuses = json.loads(status_file.read_text())
        else:
            statuses = {}
        
        # 更新状态
        statuses[filename] = {
            "status": "approved" if action == "approve" else "rejected",
            "reviewed_at": datetime.now().isoformat(),
            "reviewer_note": note
        }
        status_file.parent.mkdir(parents=True, exist_ok=True)
        status_file.write_text(json.dumps(statuses, indent=2, ensure_ascii=False))
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())
        return
    
    self.send_error(404)
```

### Step 3: 修改 load_reports() 使用 status.json
在 `load_reports()` 函数中，合并 status.json 的状态信息：

```python
def load_reports():
    """Load research reports"""
    reports_dir = SOP_ROOT / "night-build" / "reports"
    reports = []
    if reports_dir.exists():
        # 加载状态文件
        statuses = {}
        if REPORTS_STATUS.exists():
            statuses = json.loads(REPORTS_STATUS.read_text())
        
        for f in sorted(reports_dir.glob("*.md"), reverse=True):
            content = f.read_text()
            # ... 现有解析逻辑保持不变 ...
            
            # 从 status.json 读取状态（如果有的话）
            if f.name in statuses:
                status = statuses[f.name]["status"]
            elif "实现报告" in content[:500]:
                status = "approved"
            else:
                status = "pending"
            
            reports.append({
                # ... 现有字段 ...
                "status": status,
                "reviewer_note": statuses.get(f.name, {}).get("reviewer_note", "")
            })
    return reports
```

### Step 4: 在报告详情页添加审阅 UI
修改 `make_report_detail()` 函数，在报告内容下方添加审阅表单：

在 `make_report_detail` 的返回 HTML 中，在 `{html}` 之后添加：

```html
{review_ui_html}
```

其中 review_ui_html 的生成逻辑：
```python
# 检查当前状态
statuses = {}
if REPORTS_STATUS.exists():
    statuses = json.loads(REPORTS_STATUS.read_text())
current = statuses.get(filename, {})
current_status = current.get("status", "pending")

if current_status == "pending":
    review_ui = f"""
    <div style="margin-top:32px;padding:24px;background:var(--surface);border:1px solid var(--border);border-radius:12px">
      <h2 style="margin-bottom:16px">📋 审阅此报告</h2>
      <div style="margin-bottom:12px">
        <label style="font-size:13px;color:var(--text2)">审阅备注（可选）：</label><br>
        <textarea id="reviewNote" rows="3" style="width:100%;margin-top:6px;padding:8px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;color:var(--text);resize:vertical"></textarea>
      </div>
      <div style="display:flex;gap:8px">
        <button onclick="submitReview('{filename}', 'approve')" style="padding:8px 20px;background:var(--green);color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600">✅ 采纳</button>
        <button onclick="submitReview('{filename}', 'reject')" style="padding:8px 20px;background:var(--red);color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600">❌ 拒绝</button>
      </div>
      <div id="reviewResult" style="margin-top:12px;font-size:13px"></div>
    </div>
    <script>
    function submitReview(filename, action) {{
        var note = document.getElementById('reviewNote').value;
        fetch('{SCRIPT_PREFIX}/api/review', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{filename: filename, action: action, note: note}})
        }})
        .then(r => r.json())
        .then(d => {{
            if (d.ok) {{
                document.getElementById('reviewResult').innerHTML = 
                    '<span style="color:var(--green)">✅ ' + (action === 'approve' ? '已采纳' : '已拒绝') + '！</span>';
                setTimeout(() => location.reload(), 1000);
            }}
        }});
    }}
    </script>"""
else:
    review_ui = f"""
    <div style="margin-top:24px;padding:16px;background:var(--surface);border:1px solid var(--border);border-radius:12px">
      <div style="display:flex;align-items:center;gap:8px">
        <span style="font-size:18px">{'✅' if current_status == 'approved' else '❌'}</span>
        <span style="font-weight:600">{'已采纳' if current_status == 'approved' else '已拒绝'}</span>
        <span style="color:var(--text2);font-size:12px">{current.get('reviewed_at', '')}</span>
      </div>
      {f'<div style="margin-top:8px;font-size:13px;color:var(--text2)">备注：{current.get("reviewer_note", "无")}</div>' if current.get('reviewer_note') else ''}
    </div>"""
```

### Step 5: 确保 do_POST 方法存在
检查 Handler 类中是否已有 `do_POST` 方法。如果没有，添加。如果已有，在其中添加新路由。

### Step 6: 重启并验证
```bash
lsof -ti:18998 | xargs kill -9 2>/dev/null
cd /Users/lr/.openclaw/workspace && nohup python3 tools/docs-server.py > /tmp/docs-server.log 2>&1 &
sleep 2
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18998/docs.0-1.ai/
```

验证：
1. 打开 http://127.0.0.1:18998/docs.0-1.ai/reports/pending.html
2. 点击任一报告
3. 应该看到审阅表单（采纳/拒绝按钮 + 备注栏）
4. 点击采纳，应显示成功并自动刷新

## 验证标准
- [ ] pending 报告详情页有审阅 UI
- [ ] 采纳按钮点击后状态更新
- [ ] 拒绝按钮点击后状态更新
- [ ] 备注能保存
- [ ] 已审阅的报告显示审阅结果和备注
- [ ] status.json 文件正确写入
