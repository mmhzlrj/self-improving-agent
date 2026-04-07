# 2026-04-01 Kimi 调研：docs.0-1.ai 改造方案

## Q1: Flask + Markdown → Mintlify 风格（✅ 已收到）

### 核心方案：纯 CDN 前端增强

**CDN 依赖（放在 `<head>`）：**
```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Markdown 渲染: marked -->
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

<!-- 代码高亮: Prism.js -->
<link href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-bash.min.js"></script>

<!-- 图标: Lucide (Mintlify 同款) -->
<script src="https://unpkg.com/lucide@latest"></script>
```

### Flask 路由示例
```python
@app.route('/api/docs/<path:filename>')
def get_doc(filename):
    filepath = os.path.join(DOCS_DIR, f"{filename}.md")
    with open(filepath, 'r', encoding='utf-8') as f:
        return jsonify({'content': f.read()})

@app.route('/api/docs/list')
def list_docs():
    return jsonify({
        '导航': [
            {'title': '快速开始', 'slug': 'quickstart', 'icon': 'Zap'},
            ...
        ]
    })
```

### 可选增强
| 功能 | 库 | CDN |
|------|-----|-----|
| 搜索 | Fuse.js | `https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js` |
| 目录大纲 | tocbot | `https://cdn.jsdelivr.net/npm/tocbot@4.25.0/dist/tocbot.min.js` |
| 复制代码按钮 | clipboard.js | `https://cdn.jsdelivr.net/npm/clipboard@2.0.11/dist/clipboard.min.js` |

---

## Q2: 调研报告审阅工作流（✅ 已收到）

### 存储方案：JSON（段落级）+ Markdown YAML front matter（备份）

**段落审阅 JSON 格式：**
```json
[
  {
    "para_id": 0,
    "action": "approve",
    "comment": "背景阐述清晰",
    "reviewer": "zhangsan",
    "reviewed_at": "2024-01-15T09:23:18Z",
    "anchor_text": "根据工信部2023年数据显示..."
  }
]
```

### Flask 路由
```python
@app.route('/api/reports/upload', methods=['POST'])
def upload_report(): ...

@app.route('/review/<report_id>')
def review_page(report_id): ...

@app.route('/api/reports/<report_id>/comments', methods=['POST'])
def add_comment(report_id): ...

@app.route('/api/reports/<report_id>/decision', methods=['POST'])
def submit_decision(report_id):
    # decision: 'publish' / 'reject' / 'revise'
    ...
```

### 状态机
- pending → reviewing → approved/published 或 rejected 或 revision

---

## Q3: 模块版本号 + Release Note（Kimi 调用失败，待补充）

### 待回答
- 数据存储格式（YAML front matter vs JSON）
- Release Note 模板
- 自动变更追踪方案（Python 脚本 + Git hooks）

---

## Q4: alsoAllow 类配置变更自动记入 Release Note（Kimi 调用失败，待补充）

### 待回答
- 自动追踪方案（Python 脚本 + Git hooks？）
- 变更记录格式模板
- 与 docs.0-1.ai 同步机制

---

## Q5: 技术栈分析（Kimi 调用失败，待补充）

### 待回答
- docs.openclaw.ai 用什么框架
- Mintlify 免费版自托管限制
- 纯前端方案对比

---

## Q3: 模块版本号 + Release Note（✅ 完整收到）

详见 `docs/docs.openclaw.ai-sop.md` 第四章节：
- YAML front matter 存储版本号 + changelog
- `VersionManager` Python 类自动 bump 版本
- Git Hook `pre-commit` 强制版本号更新

## Q4: alsoAllow 配置自动追踪（✅ 完整收到）

详见 SOP 第五章节：
- `pre-commit` hook 捕获 git diff 中的 alsoAllow/MCP 变更
- JSONL 日志文件存储变更记录
- Flask API 定时同步到 docs.0-1.ai

## Q5: 技术栈分析（✅ 完整收到）

| 结论 | 说明 |
|------|------|
| docs.openclaw.ai | Mintlify |
| Mintlify 免费自托管 | ❌ 不支持 |
| **推荐框架** | **Docsify**（CDN 零配置）|
| 备选 | VitePress（需构建）|

## 文档输出

- `memory/2026-04-01-Q-Kimi-docs-0-1-ai.md` - 原始调研草稿
- `docs/docs.openclaw.ai-sop.md` - **正式 SOP 文档（16KB）**

## Kimi MCP 调用经验

- **调用策略**：长问题（>100字）容易被挂起，采用**单独依次调用**策略
- **超时处理**：120s timeout，部分回答会返回在 stderr（不影响）
- **最佳问题长度**：50-200字单个问题效果最好
- **竞争问题**：多进程同时调用同一 Chrome tab 导致连接竞争，建议单次调用

## A-002~A-008 完成记录 (15:49)

### A-002: 暗黑/亮色主题切换 ✅
- docs-server.py: 添加 `:root[data-theme="light"]` CSS变量
- Header添加🌙/☀️切换按钮
- JS实现localStorage持久化
- 验证: curl显示7处theme相关代码

### A-003: 模块Markdown文档 ✅
- docs/modules/ 新增: arm.md, vision.md, suction.md, locomotion.md, face.md

### A-004: 调研报告审阅工作流 ✅
- make_reports_list已正确对接night-build/reports/
- 创建 docs/reports/test-report-1.md 演示文件
- 验证: approved.html显示LeWM报告，10个报告项

### A-005: alsoAllow配置变更追踪脚本 ✅
- scripts/track-alsoAllow.py 已创建
- 用户需手动添加crontab: `0 * * * * python3 ~/.openclaw/workspace/scripts/track-alsoAllow.py`

### A-006: 模块版本号系统 ✅
- bump_module_version()函数添加至line 379

### A-007: Reports路由 ✅
- /reports/approved.html 和 /reports/pending.html 路由已正确

### A-008: SOP截断逻辑 ✅
- sub['content'][:3000] → [:8000] (line 646)
