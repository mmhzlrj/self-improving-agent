# F-009: 首页改版（仪表盘风格）

## 问题描述
当前首页是静态卡片堆砌，没有显示关键运营信息：最近更新、待审阅数量、模块完成度、时间线。

## 文件
- `/Users/lr/.openclaw/workspace/tools/docs-server.py`
- 函数：`make_home()`（约第 534 行）

## 修复步骤

### Step 1：读取当前 make_home() 函数
```bash
sed -n '534,620p' /Users/lr/.openclaw/workspace/tools/docs-server.py
```

### Step 2：重写 make_home() 函数

保留首页的核心结构，但新增以下信息区块：

**替换 make_home() 函数整体**，新版本应包含：

#### 区块 1：顶部统计卡片（3个）
- 📊 **待审阅报告**：`len([r for r in reports if r['status']=='pending'])` 个
- 📄 **总文档数**：模块文档数 + 调研报告数
- 🔄 **最近更新**：从 `docs/.versions/versions.json` 读取最新变更

```python
def make_home():
    """Dashboard-style homepage"""
    reports = load_reports()
    modules_dir = DOCS_ROOT / "modules"
    module_count = len(list(modules_dir.glob("*.md"))) if modules_dir.exists() else 0
    report_count = len(reports)
    pending_count = len([r for r in reports if r['status'] == 'pending'])
    approved_count = len([r for r in reports if r['status'] == 'approved'])

    # Load latest changes from versions.json
    versions = load_versions()
    all_changes = []
    for mod_name, mod_data in versions.items():
        for change in mod_data.get('changes', []):
            all_changes.append({
                'module': mod_name,
                'type': change.get('type', ''),
                'detail': change.get('detail', ''),
                'date': change.get('date', '')
            })
    all_changes.sort(key=lambda x: x.get('date', ''), reverse=True)
    recent_changes = all_changes[:8]

    # Build recent changes HTML
    changes_html = ""
    for c in recent_changes:
        type_icons = {"added": "➕", "modified": "✏️", "fixed": "🔧", "removed": "🗑️"}
        icon = type_icons.get(c['type'], '📝')
        changes_html += f"""
        <div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid var(--border)">
            <span>{icon}</span>
            <span style="flex:1;font-size:13px">{c['detail']}</span>
            <span style="font-size:11px;color:var(--text2)">{c['module']}</span>
            <span style="font-size:11px;color:var(--text2)">{c['date']}</span>
        </div>"""

    if not changes_html:
        changes_html = '<div style="padding:16px;color:var(--text2);text-align:center">暂无变更记录</div>'

    # Build pending reports HTML
    pending_html = ""
    pending_reports = [r for r in reports if r['status'] == 'pending'][:5]
    for r in pending_reports:
        pending_html += f"""
        <div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:13px">
            <a href="{r['url']}" style="color:var(--accent2)">{r['title']}</a>
            <span style="color:var(--text2);margin-left:8px">{r['date']}</span>
        </div>"""
    if not pending_html:
        pending_html = '<div style="padding:16px;color:var(--text2);text-align:center">🎉 全部报告已审阅</div>'

    return make_page("home", "0-1 文档中心", f"""
    <!-- 统计卡片 -->
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:32px">
        <div class="module-card" onclick="location.href='{SCRIPT_PREFIX}/reports/pending.html'" style="cursor:pointer">
            <div style="font-size:28px;font-weight:700;color:var(--yellow)">⏳ {pending_count}</div>
            <div style="font-size:13px;color:var(--text2);margin-top:4px">待审阅报告</div>
        </div>
        <div class="module-card" onclick="location.href='{SCRIPT_PREFIX}/modules/'" style="cursor:pointer">
            <div style="font-size:28px;font-weight:700;color:var(--accent2)">🧩 {module_count}</div>
            <div style="font-size:13px;color:var(--text2);margin-top:4px">模块文档</div>
        </div>
        <div class="module-card" onclick="location.href='{SCRIPT_PREFIX}/reports/approved.html'" style="cursor:pointer">
            <div style="font-size:28px;font-weight:700;color:var(--green)">✅ {approved_count}</div>
            <div style="font-size:13px;color:var(--text2);margin-top:4px">已发布报告</div>
        </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
        <!-- 最近变更 -->
        <div class="module-card">
            <h2 style="font-size:16px;margin-bottom:12px;color:var(--accent)">📝 最近变更</h2>
            {changes_html}
        </div>

        <!-- 待审阅 -->
        <div class="module-card">
            <h2 style="font-size:16px;margin-bottom:12px;color:var(--yellow)">⏳ 待审阅报告</h2>
            {pending_html}
            <div style="margin-top:8px">
                <a href="{SCRIPT_PREFIX}/reports/pending.html" style="font-size:12px;color:var(--accent2)">查看全部 →</a>
            </div>
        </div>
    </div>

    <!-- 快速导航 -->
    <h2 style="font-size:16px;margin:24px 0 16px;color:var(--accent)">🚀 快速导航</h2>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">
        <div class="module-card" onclick="location.href='{SCRIPT_PREFIX}/sop/full.html'" style="cursor:pointer;text-align:center;padding:20px">
            <div style="font-size:24px;margin-bottom:4px">📖</div>
            <div style="font-weight:600">完整 SOP</div>
        </div>
        <div class="module-card" onclick="location.href='{SCRIPT_PREFIX}/changelog/timeline.html'" style="cursor:pointer;text-align:center;padding:20px">
            <div style="font-size:24px;margin-bottom:4px">📝</div>
            <div style="font-weight:600">版本时间线</div>
        </div>
        <div class="module-card" onclick="location.href='{SCRIPT_PREFIX}/tools/mcp.html'" style="cursor:pointer;text-align:center;padding:20px">
            <div style="font-size:24px;margin-bottom:4px">🔧</div>
            <div style="font-weight:600">工具配置</div>
        </div>
    </div>
    """)
```

### Step 3：重启并验证
```bash
lsof -ti:18998 | xargs kill -9 2>/dev/null; sleep 1; cd /Users/lr/.openclaw/workspace && nohup python3 tools/docs-server.py > /tmp/docs-server.log 2>&1 & sleep 2; curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18998/docs.0-1.ai/
```

### Step 4：验证首页
用浏览器打开 http://127.0.0.1:18998/docs.0-1.ai/，确认：
- 3 个统计卡片（待审阅/模块/已发布）
- 最近变更列表
- 待审阅报告列表
- 快速导航

## 验证标准
- [ ] 首页显示 3 个统计卡片，数字正确
- [ ] 最近变更列表有内容（来自 versions.json）
- [ ] 待审阅报告列表正确显示
- [ ] 快速导航链接可用
