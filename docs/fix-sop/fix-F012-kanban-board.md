# F-012: 任务看板页面

## 问题描述
AI 在做任务时（A/B 序列 night-build），没有一个页面能看到所有任务的状态（待做/进行中/完成/阻塞）。当前任务跟踪在 `night-build/A-sequence-tasks.md` 里。

## 文件
- `/Users/lr/.openclaw/workspace/tools/docs-server.py`
- `/Users/lr/.openclaw/workspace/harness/robot/night-build/A-sequence-tasks.md`（数据源）

## 修复步骤

### Step 1：读取当前任务文件
```bash
cat /Users/lr/.openclaw/workspace/harness/robot/night-build/A-sequence-tasks.md
```

### Step 2：在 NAV_CONFIG 中添加"任务看板"导航

在"调研报告"之后添加：
```python
    {"id": "kanban",   "label": "任务看板",   "icon": "📋", "path": "/kanban/"},
```

### Step 3：创建任务解析函数

```python
def load_kanban_tasks():
    """Parse A-sequence/B-sequence task files"""
    tasks = []
    task_files = [
        SOP_ROOT / "night-build" / "A-sequence-tasks.md",
        SOP_ROOT / "night-build" / "B-sequence-tasks.md",
    ]
    for tf in task_files:
        if not tf.exists():
            continue
        sequence = 'A' if 'A-sequence' in tf.name else 'B'
        content = tf.read_text(encoding='utf-8')
        # 解析任务行：- [x] A-001 xxx 或 - [ ] A-002 xxx
        for line in content.split('\n'):
            m = re.match(r'^-\s+\[([ xX])\]\s+(\S+)\s+(.+)', line)
            if m:
                done = m.group(1).lower() == 'x'
                task_id = m.group(2)
                desc = m.group(3).strip()
                # 去掉可能的状态标签
                desc = re.sub(r'✅|❌|🔲|⏳', '', desc).strip()
                tasks.append({
                    'id': task_id,
                    'desc': desc,
                    'done': done,
                    'sequence': sequence,
                })
    return tasks
```

### Step 4：创建看板页面渲染函数

```python
def make_kanban():
    """Task kanban board"""
    tasks = load_kanban_tasks()
    done_tasks = [t for t in tasks if t['done']]
    pending_tasks = [t for t in tasks if not t['done']]

    def task_card(t):
        status = "✅" if t['done'] else "⏳"
        bg = "var(--surface)" if t['done'] else "var(--surface2)"
        opacity = "0.7" if t['done'] else "1"
        return f"""
        <div style="background:{bg};border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:8px;opacity:{opacity}">
            <div style="display:flex;align-items:center;gap:8px">
                <span>{status}</span>
                <span style="font-weight:600;font-size:13px">{t['id']}</span>
                <span style="font-size:12px;color:var(--text2)">{t['sequence']}序列</span>
            </div>
            <div style="font-size:13px;margin-top:4px;color:var(--text)">{t['desc']}</div>
        </div>"""

    return make_page("kanban", "📋 任务看板", f"""
    <div class="content-header">
        <h1>📋 任务看板</h1>
        <div class="content-meta">共 {len(tasks)} 个任务 · {len(done_tasks)} 完成 · {len(pending_tasks)} 待做</div>
    </div>

    <!-- 进度条 -->
    <div style="background:var(--surface2);border-radius:8px;height:24px;margin-bottom:24px;overflow:hidden">
        <div style="background:var(--green);height:100%;width:{(len(done_tasks)/len(tasks)*100) if tasks else 0:.1f}%;border-radius:8px;transition:width .3s"></div>
    </div>
    <div style="font-size:12px;color:var(--text2);margin-bottom:24px">{(len(done_tasks)/len(tasks)*100) if tasks else 0:.1f}% 完成</div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
        <div>
            <h2 style="font-size:16px;margin-bottom:12px;color:var(--yellow)">⏳ 待做（{len(pending_tasks)}）</h2>
            {"".join(task_card(t) for t in pending_tasks) or '<div style="color:var(--text2);text-align:center;padding:24px">🎉 全部完成</div>'}
        </div>
        <div>
            <h2 style="font-size:16px;margin-bottom:12px;color:var(--green)">✅ 已完成（{len(done_tasks)}）</h2>
            {"".join(task_card(t) for t in done_tasks) or '<div style="color:var(--text2);text-align:center;padding:24px">暂无完成的任务</div>'}
        </div>
    </div>
    """)
```

### Step 5：添加路由

在 Handler.do_GET 中添加：
```python
        if path == "/kanban/" or path == "/kanban/index.html":
            return self.send_html(make_kanban())
```

### Step 6：重启并验证

## 验证标准
- [ ] 看板页面显示进度条和完成百分比
- [ ] 待做/已完成分两列显示
- [ ] 任务数量和状态与 A-sequence-tasks.md 一致
