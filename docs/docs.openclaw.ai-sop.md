# docs.0-1.ai 技术改造方案 & 运维 SOP

> 状态：✅ 部分实施中
> 更新时间：2026-04-01
> 源码：`~/.openclaw/workspace/tools/docs-server.py`

---

## 实施进度

| 改进项 | 状态 | 说明 |
|--------|------|------|
| Prism.js 代码高亮 | ✅ 已完成 | Tomorrow Night 主题，支持 10+ 语言 |
| Fuse.js 模糊搜索 | ✅ 已完成 | Ctrl+K 快捷键，threshold=0.4 |
| 模块详情页 | ✅ 已完成 | `/modules/{slug}.html`，支持 Markdown 内容 |
| 暗黑/亮色主题切换 | 🔲 待做 | CSS 变量 + JS 切换 |
| 模块 Markdown 文档 | 🔲 进行中 | `docs/modules/` 目录下各模块 .md 文件 |
| 调研报告审阅工作流 | 🔲 待做 | Q2 方案未实施 |
| alsoAllow 自动追踪 | 🔲 待做 | Q4 方案未实施 |
| 版本号系统 | 🔲 待做 | Q3 方案未实施 |

> 来源：Kimi 调研（2026-04-01）
> 约束：保持 Python Flask 后端 + Markdown 文件，不强制构建工具

---

## 一、框架选型结论

| 网站/方案 | 结论 |
|-----------|------|
| docs.openclaw.ai | Mintlify（闭源 SaaS） |
| Mintlify 免费自托管 | ❌ 不支持，仅官方托管 |
| **Docsify**（推荐） | ✅ CDN 零配置，Flask 配合最好 |
| VitePress | 需构建，适合前后端分离部署 |

**最终推荐：Docsify + 自定义 CSS**，实现 Mintlify 风格，无需任何构建工具。

---

## 二、Q1：Flask + Markdown → Mintlify 风格文档站

### 2.1 核心技术栈（纯 CDN）

```html
<!-- 放在 <head> 中 -->
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

<!-- 搜索: Fuse.js（可选）-->
<script src="https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js"></script>

<!-- 目录 TOC（可选）-->
<script src="https://cdn.jsdelivr.net/npm/tocbot@4.25.0/dist/tocbot.min.js"></script>
```

### 2.2 Flask 路由设计

```python
from flask import Flask, render_template, jsonify, send_from_directory
import os

app = Flask(__name__)
DOCS_DIR = 'docs'  # Markdown 文件目录

@app.route('/')
def index():
    return render_template('docs.html')

@app.route('/api/docs/<path:filename>')
def get_doc(filename):
    """读取 Markdown 文件"""
    filepath = os.path.join(DOCS_DIR, f"{filename}.md")
    if not os.path.exists(filepath):
        return jsonify({'error': 'Not found'}), 404
    with open(filepath, 'r', encoding='utf-8') as f:
        return jsonify({'content': f.read()})

@app.route('/api/docs/list')
def list_docs():
    """获取文档目录结构（侧边栏数据）"""
    return jsonify({
        '实施指南': [
            {'title': '快速开始', 'slug': 'quickstart', 'icon': 'Zap'},
            {'title': '安装指南', 'slug': 'installation', 'icon': 'Download'},
        ],
        '模块文档': [
            {'title': '贵庚记忆系统', 'slug': 'memory', 'icon': 'Brain'},
            {'title': 'LeWM 世界模型', 'slug': 'lewm', 'icon': 'Globe'},
            {'title': '机械臂模块', 'slug': 'arm', 'icon': 'Arm'},
        ],
    })
```

### 2.3 前端单页模板（docs.html）

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>docs.0-1.ai</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {
            --sidebar-bg: #fafafa;
            --sidebar-border: #e5e5e5;
            --accent: #0ea5e9;
            --text-primary: #171717;
            --text-secondary: #737373;
        }
        .prose h1 { font-size: 2.25rem; font-weight: 700; margin: 2rem 0 1rem; }
        .prose h2 { font-size: 1.5rem; font-weight: 600; margin: 2rem 0 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #e5e5e5; }
        .prose h3 { font-size: 1.25rem; font-weight: 600; margin: 1.5rem 0 0.75rem; }
        .prose p { margin: 1rem 0; line-height: 1.75; color: #374151; }
        .prose ul { list-style: disc; padding-left: 1.5rem; margin: 1rem 0; }
        .prose code:not(pre code) { background: #f3f4f6; padding: 0.2rem 0.4rem; border-radius: 0.375rem; font-size: 0.875rem; color: #ec4899; }
        .prose pre { border-radius: 0.75rem; margin: 1.5rem 0; background: #1e1e1e !important; }
    </style>
</head>
<body class="bg-white text-gray-900">
    <div class="flex min-h-screen">
        <!-- 侧边栏 -->
        <aside class="w-72 bg-[var(--sidebar-bg)] border-r border-[var(--sidebar-border)] fixed h-full overflow-y-auto hidden lg:block">
            <div class="p-6">
                <div class="flex items-center gap-3 mb-8">
                    <div class="w-8 h-8 bg-sky-500 rounded-lg flex items-center justify-center">
                        <i data-lucide="book-open" class="w-5 h-5 text-white"></i>
                    </div>
                    <span class="font-bold text-lg">0-1 文档站</span>
                </div>
                <div class="relative mb-6">
                    <i data-lucide="search" class="absolute left-3 top-2.5 w-4 h-4 text-gray-400"></i>
                    <input type="text" placeholder="搜索文档..." id="search-input"
                           class="w-full pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-sky-500">
                </div>
                <nav id="sidebar-nav"></nav>
            </div>
        </aside>

        <!-- 主内容 -->
        <main class="flex-1 lg:ml-72">
            <div class="max-w-4xl mx-auto px-6 py-12">
                <article id="content" class="prose max-w-none"></article>
                <div id="page-nav" class="flex justify-between mt-16 pt-8 border-t"></div>
            </div>
        </main>
    </div>

    <script>
        const config = { defaultPage: 'quickstart' };
        let docsStructure = {};

        document.addEventListener('DOMContentLoaded', () => {
            lucide.createIcons();
            loadSidebar();
            const page = new URLSearchParams(location.search).get('page') || config.defaultPage;
            loadPage(page);
        });

        async function loadSidebar() {
            const res = await fetch('/api/docs/list');
            docsStructure = await res.json();
            const nav = document.getElementById('sidebar-nav');
            nav.innerHTML = '';
            for (const [section, items] of Object.entries(docsStructure)) {
                nav.innerHTML += `<h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2">${section}</h3>`;
                nav.innerHTML += items.map(item => `
                    <a href="?page=${item.slug}" onclick="event.preventDefault(); loadPage('${item.slug}')"
                       data-slug="${item.slug}" class="nav-item flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors mb-1">
                        <i data-lucide="${item.icon}" class="w-4 h-4"></i>
                        ${item.title}
                    </a>`).join('');
            }
            lucide.createIcons();
        }

        async function loadPage(slug) {
            history.pushState({page: slug}, '', `?page=${slug}`);
            document.querySelectorAll('.nav-item').forEach(el => {
                el.classList.toggle('bg-sky-50', el.dataset.slug === slug);
                el.classList.toggle('text-sky-600', el.dataset.slug === slug);
                el.classList.toggle('font-medium', el.dataset.slug === slug);
            });
            const res = await fetch(`/api/docs/${slug}`);
            const data = await res.json();
            document.getElementById('content').innerHTML = marked.parse(data.content);
            Prism.highlightAllUnder(document.getElementById('content'));
        }

        window.onpopstate = e => loadPage(new URLSearchParams(location.search).get('page') || config.defaultPage);
    </script>
</body>
</html>
```

### 2.4 文件结构

```
docs-site/
├── app.py                  # Flask 后端
├── templates/
│   └── docs.html           # 单页应用（上述代码）
└── docs/                   # Markdown 文档
    ├── quickstart.md
    ├── installation.md
    ├── memory.md
    ├── lewm.md
    └── ...
```

### 2.5 可选功能增强

| 功能 | 库 | CDN |
|------|-----|-----|
| 模糊搜索 | Fuse.js | `https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js` |
| 页面内目录 | tocbot | `https://cdn.jsdelivr.net/npm/tocbot@4.25.0/dist/tocbot.min.js` |
| 代码复制按钮 | clipboard.js | `https://cdn.jsdelivr.net/npm/clipboard@2.0.11/dist/clipboard.min.js` |

---

## 三、Q2：调研报告审阅工作流

### 3.1 整体架构

```
调研报告(Markdown) → 上传解析 → 审阅界面 → 决策存储 → 自动发布
                              ↑___________↓
                              (采纳/拒绝/备注)
```

### 3.2 段落审阅数据格式

```json
[
  {
    "para_id": 0,
    "action": "approve",
    "comment": "背景阐述清晰，数据引用准确",
    "reviewer": "zhangsan",
    "reviewed_at": "2024-01-15T09:23:18Z",
    "anchor_text": "根据工信部2023年数据显示..."
  },
  {
    "para_id": 3,
    "action": "reject",
    "comment": "第三章数据来源未标注",
    "reviewer": "zhangsan",
    "reviewed_at": "2024-01-15T09:25:42Z",
    "anchor_text": "市场规模预计达到500亿元"
  }
]
```

### 3.3 Flask 路由

```python
from flask import Flask, render_template, request, jsonify
import markdown
import hashlib

app = Flask(__name__)

# 阶段1: 上传
@app.route('/api/reports/upload', methods=['POST'])
def upload_report():
    file = request.files['report']
    report_id = hashlib.md5(f"{file.filename}{datetime.utcnow()}".encode()).hexdigest()[:16]
    filepath = f"uploads/{report_id}.md"
    file.save(filepath)
    return jsonify({'report_id': report_id, 'review_url': f'/review/{report_id}'})

# 阶段2: 审阅界面
@app.route('/review/<report_id>')
def review_page(report_id):
    with open(f"uploads/{report_id}.md", 'r') as f:
        content = f.read()
    rendered = markdown.markdown(content)
    return render_template('review.html', report_id=report_id, rendered_html=rendered)

# 阶段3: 保存批注
@app.route('/api/reports/<report_id>/comments', methods=['POST'])
def add_comment(report_id):
    data = request.get_json()
    # 追加到审阅记录 JSON 文件
    ...

# 阶段4: 最终决策
@app.route('/api/reports/<report_id>/decision', methods=['POST'])
def submit_decision(report_id):
    decision = request.json['decision']  # 'publish' / 'reject' / 'revise'
    if decision == 'publish':
        publish_report(report_id)
    return jsonify({'decision': decision})
```

### 3.4 审阅界面核心逻辑

```html
<!-- 每个段落绑定操作按钮 -->
<script>
document.querySelectorAll('.markdown-body > *').forEach((para, index) => {
    para.dataset.paraId = index;
    para.style.borderLeft = '3px solid transparent';
    para.onmouseenter = () => para.style.borderLeftColor = '#0366d6';
    para.onmouseleave = () => para.style.borderLeftColor = 'transparent';
});

async function saveDecision(paraId, action, comment) {
    await fetch(`/api/reports/${reportId}/comments`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ para_id: paraId, action, comment })
    });
    // 颜色反馈：绿(采纳) / 红(拒绝) / 黄(备注)
}
</script>
```

### 3.5 状态机

```
pending → reviewing → approved → published
                      ↘ rejected / revision
```

---

## 四、Q3：模块版本号 + Release Note 系统

### 4.1 数据存储：YAML Front Matter

```yaml
---
module: lewm
version: v0.2.1
since: v0.1.0
status: stable
openclaw_compat: v0.9.x
changelog:
  - date: 2026-04-01
    version: v0.2.1
    changes:
      - type: feat
        desc: Vision Encoder 支持 pusht 图像微调
      - type: fix
        desc: 修复 loss=NaN 问题
  - date: 2026-03-28
    version: v0.2.0
    changes:
      - type: feat
        desc: 初始版本
---
```

### 4.2 Python 版本管理器

```python
# version/manager.py
import re, yaml
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ModuleVersion:
    name: str
    version: str
    changelog: list

    def bump(self, change_type: str, description: str) -> str:
        major, minor, patch = map(int, self.version.lstrip('v').split('.'))
        if change_type == "major":   major += 1; minor = patch = 0
        elif change_type == "minor": minor += 1; patch = 0
        else:                        patch += 1
        new_ver = f"v{major}.{minor}.{patch}"
        self.changelog.insert(0, {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "version": new_ver,
            "changes": [{"type": change_type, "desc": description}]
        })
        return new_ver

class VersionManager:
    MODULES_DIR = Path("docs/模块文档")

    def bump(self, module: str, change_type: str, description: str) -> str:
        path = next(self.MODULES_DIR.glob(f"{module}/index.md"), None)
        content = path.read_text()
        meta = yaml.safe_load(re.search(r'^---\n(.*?)\n---', content, re.DOTALL).group(1))
        mv = ModuleVersion(module, meta['version'], meta.get('changelog', []))
        new_ver = mv.bump(change_type, description)
        # 回写 YAML front matter
        ...
        return new_ver
```

### 4.3 Git Hook 强制版本追踪

```bash
#!/bin/bash
# .git/hooks/pre-commit
CHANGED=$(git diff --cached --name-only --diff-filter=M | grep '^docs/')
if [ -n "$CHANGED" ]; then
    for f in $CHANGED; do
        module=$(echo "$f" | cut -d/ -f2)
        staged_ver=$(git show :"$f" | grep "^version:" | awk '{print $2}')
        work_ver=$(grep "^version:" "$f" | awk '{print $2}')
        if [ "$staged_ver" = "$work_ver" ]; then
            echo "⚠️  $module: 变更但版本号未更新"
            exit 1
        fi
    done
fi
```

---

## 五、Q4：alsoAllow 配置变更自动追踪

### 5.1 Git Hook 变更检测

```python
#!/usr/bin/env python3
# .git/hooks/post-commit 或定时 Cron
import re, json, subprocess
from pathlib import Path
from datetime import datetime

CONFIG_PATH = Path.home() / '.openclaw/openclaw.json'
LOG_FILE = Path.home() / '.openclaw/config-change-log.jsonl'

def detect_alsoAllow_change():
    diff = subprocess.run(
        ['git', '-C', str(CONFIG_PATH.parent), 'diff', 'HEAD~1', '--', CONFIG_PATH.name],
        capture_output=True, text=True
    ).stdout

    if not any(k in diff for k in ['alsoAllow', 'kimi_', 'doubao_', 'glm_', 'qwen_']):
        return

    commit = subprocess.run(
        ['git', '-C', str(CONFIG_PATH.parent), 'rev-parse', 'HEAD'],
        capture_output=True, text=True
    ).stdout.strip()[:8]

    entry = {
        "timestamp": datetime.now().isoformat(),
        "commit": commit,
        "type": "alsoAllow",
        "diff_summary": '\n'.join(diff.split('\n')[:20])
    }

    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(f"[AutoLog] alsoAllow 变更已记录: {commit}")
```

### 5.2 变更日志格式

```json
{"timestamp": "2026-04-01T12:00:00", "commit": "a1b2c3d", "type": "alsoAllow", "diff_summary": "+ kimi_kimi_chat\n- old_tool"}
```

### 5.3 与 docs.0-1.ai 同步

```python
# 定时任务（Cron）或 GitHub Actions
@app.route('/api/changelog/sync', methods=['POST'])
def sync_changelog():
    log_file = Path.home() / '.openclaw/config-change-log.jsonl'
    entries = [json.loads(l) for l in open(log_file) if not json.loads(l).get('synced')]
    for entry in entries[:10]:
        # 写入 docs/版本变更/openclaw-config-YYYY-MM-DD.md
        write_changelog_entry(entry)
        entry['synced'] = True
    # 回写已同步标记
    ...
```

---

## 六、Q5：技术栈分析汇总

| 维度 | Mintlify | Docsify | VitePress |
|------|---------|---------|-----------|
| 框架性质 | 闭源 SaaS | 开源 CDN | 开源 SSG |
| 自托管 | ❌ 不支持 | ✅ 支持 | ✅ 支持 |
| 构建工具 | 无 | 无（CDN） | ✅ Vite |
| SEO | 好 | 弱 | 极好 |
| Flask 配合度 | ❌ 需代理 | ✅ 最佳 | ⚠️ 需构建 |
| 维护成本 | 低 | 低 | 中 |

### 最终推荐

| 场景 | 推荐方案 |
|------|---------|
| **当前阶段（保持 Flask + Markdown）** | Docsify + 自定义 CSS |
| **未来演进（可接受构建）** | VitePress 构建产物放 Flask `/static` |
| **docs.openclaw.ai 参考目标** | Mintlify SaaS（仅参考风格，不可自托管） |

---

## 七、快速启动 Checklist

```bash
# 1. 克隆/创建 docs 目录结构
mkdir -p docs/{实施指南,模块文档,调研报告,版本变更,工具配置}
mkdir -p templates

# 2. 初始化第一个模块的 YAML front matter
cat > docs/模块文档/lewm/index.md << 'EOF'
---
module: lewm
version: v0.1.0
status: stable
openclaw_compat: v0.9.x
changelog:
  - date: 2026-04-01
    version: v0.1.0
    changes:
      - type: feat
        desc: 初始版本
---
EOF

# 3. 运行 Flask
python app.py

# 4. 安装 Git hooks（版本追踪）
chmod +x .git/hooks/pre-commit
```

---

## 八、运维命令参考

| 操作 | 命令 |
|------|------|
| 启动文档站 | `python app.py` |
| 更新模块版本 | `python -m version bump lewm minor "新增XXX"` |
| 生成 Release Note | `python -m version release` |
| 检查配置变更 | `git diff ~/.openclaw/openclaw.json` |
| 触发变更同步 | `python scripts/sync-changelog.py` |

---

## 实施记录（2026-04-01）

### 改进1：Prism.js 代码高亮（✅ 已完成）

**改动文件**：`docs-server.py`

**CDN 引入**：
```html
<link href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js"></script>
<!-- bash, javascript, typescript, json, yaml, markdown, sql, docker 同理 -->
```

**代码高亮转换函数**：
```python
def _convert_codehilite(html):
    html = re.sub(r'class="codehilite"', 'class="codehilite line-numbers"', html)
    html = re.sub(r'<div class="codehilite"><pre><code class="(\w+)"',
                  r'<div class="codehilite"><pre class="language-\1"><code class="language-\1"', html)
    return html
```

**页面加载时触发**：
```javascript
Prism.highlightAll();
```

---

### 改进2：Fuse.js 模糊搜索（✅ 已完成）

**改动文件**：`docs-server.py`

**CDN 引入**：
```html
<script src="https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js"></script>
```

**搜索索引构建**（Python，服务启动时生成，嵌入每个页面）：
```python
def _build_search_index():
    index = []
    for md_file in docs_dir.glob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        index.append({"title": title, "text": plain_text, "url": "..."})
    # 也索引 SOP 内容
    return index
```

**Fuse.js 配置**：
```javascript
const fuse = new Fuse(searchIndex, {
    keys: ['title', 'text'],
    threshold: 0.4,      // 模糊度（越小越精确）
    includeScore: true,
    minMatchCharLength: 2
});
```

---

### 改进3：模块详情页（✅ 已完成）

**改动文件**：`docs-server.py`

**新增数据层**：
```python
MODULE_DATA = [
    ("贵庚记忆系统", "gui-geng", "🧠", "描述..."),
    ("LeWM 世界模型", "lewm", "🌍", "描述..."),
    ...
]
```

**路由修复**：之前 `/modules/[slug].html` 跳回 index，现在正确渲染详情页。

**Markdown 内容**：各模块文档放在 `docs/modules/{slug}.md`，读取并渲染。

**已创建模块文档**：
- `docs/modules/lewm.md` ✅
- `docs/modules/gui-geng.md` ✅

---

### 遇到的问题

**问题1：Prism 颜色方案不明显**
- 原因：Python 关键字少，Tomorrow Night 对 dictionary 语法高亮不明显
- 解决：使用 `prism-tomorrow` 主题，代码块背景 #1e1e1e 已够用

**问题2：模块详情页 404**
- 原因：路由 regex 正确但直接 redirect to index，未实现详情渲染
- 解决：提取 `MODULE_DATA` 共享数据，新建 `make_module_detail(slug)` 函数
