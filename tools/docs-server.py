#!/usr/bin/env python3
"""
docs.0-1.ai HTTP Server
Serves the 0-1 project documentation website at http://127.0.0.1:18998/
"""

import http.server
import socketserver
import os
import json
import re
import hashlib
from pathlib import Path
from urllib.parse import unquote

PORT = 18998
DOCS_ROOT = Path(__file__).parent.resolve()
VERSIONS_FILE = DOCS_ROOT / ".versions" / "versions.json"
REPORTS_STATUS = DOCS_ROOT / "reports" / "status.json"
SOP_ROOT = Path.home() / ".openclaw" / "workspace" / "harness" / "robot"

# ─── Markdown Renderer ────────────────────────────────────────────────────────

try:
    import markdown
    MD = markdown.Markdown(extensions=['tables', 'fenced_code', 'codehilite', 'toc'])
    def render_markdown(text):
        MD.reset()
        return MD.convert(text)
except ImportError:
    def render_markdown(text):
        return "<pre>" + text.replace("&","&amp;").replace("<","&lt;") + "</pre>"

# ─── Navigation ──────────────────────────────────────────────────────────────

NAV_CONFIG = [
    {"id": "home",     "label": "首页",       "icon": "🏠", "path": "/"},
    {"id": "sop",      "label": "实施指南",   "icon": "📖", "path": "/sop/",
     "children": [
        {"id": "sop-ch0", "label": "第0章：启动与配置", "path": "/sop/chapter-0.html"},
        {"id": "sop-ch1", "label": "第1章：概念与愿景", "path": "/sop/chapter-1.html"},
        {"id": "sop-ch2", "label": "第2章：硬件体系",   "path": "/sop/chapter-2.html"},
        {"id": "sop-ch3", "label": "第3章：软件架构",   "path": "/sop/chapter-3.html"},
        {"id": "sop-ch4", "label": "第4章：实施阶段",   "path": "/sop/chapter-4.html"},
        {"id": "sop-ch5", "label": "第5章：安全系统",   "path": "/sop/chapter-5.html"},
        {"id": "sop-ch6", "label": "第6章：数据管理",   "path": "/sop/chapter-6.html"},
        {"id": "sop-ch7", "label": "完整 SOP",          "path": "/sop/full.html"},
     ]},
    {"id": "modules",  "label": "模块文档",   "icon": "🧩", "path": "/modules/",
     "children": [
        {"id": "mod-gui-geng", "label": "贵庚记忆系统",   "path": "/modules/gui-geng.html"},
        {"id": "mod-lewm",     "label": "LeWM 世界模型", "path": "/modules/lewm.html"},
        {"id": "mod-arm",      "label": "机械臂模块",     "path": "/modules/arm.html"},
        {"id": "mod-vision",   "label": "视觉识别",       "path": "/modules/vision.html"},
        {"id": "mod-suction",  "label": "吸盘抓手",       "path": "/modules/suction.html"},
        {"id": "mod-locomotion","label":"移动模块",       "path": "/modules/locomotion.html"},
        {"id": "mod-face",     "label": "面部模块",       "path": "/modules/face.html"},
     ]},
    {"id": "reports",  "label": "调研报告",   "icon": "📊", "path": "/reports/",
     "children": [
        {"id": "rep-approved", "label": "已发布",  "path": "/reports/approved.html"},
        {"id": "rep-pending",  "label": "待审批",  "path": "/reports/pending.html"},
     ]},
    {"id": "changelog","label": "版本变更",   "icon": "📝", "path": "/changelog/",
     "children": [
        {"id": "cl-openclaw", "label": "OpenClaw 核心",  "path": "/changelog/openclaw.html"},
        {"id": "cl-modules",  "label": "模块版本",        "path": "/changelog/modules.html"},
        {"id": "cl-timeline", "label": "完整时间线",      "path": "/changelog/timeline.html"},
     ]},
    {"id": "tools",    "label": "工具配置",   "icon": "🔧", "path": "/tools/",
     "children": [
        {"id": "tools-mcp",    "label": "MCP 工具",      "path": "/tools/mcp.html"},
        {"id": "tools-config", "label": "配置文件",      "path": "/tools/config.html"},
     ]},
    {"id": "refs",     "label": "参考链接",   "icon": "🔗", "path": "/refs/",
     "children": [
        {"id": "ref-dashboard", "label": "Dashboard",    "path": "/refs/dashboard/"},
        {"id": "ref-world",     "label": "World View",  "path": "/refs/world/"},
        {"id": "ref-openclaw",  "label": "OpenClaw 官方文档", "external": "https://docs.openclaw.ai"},
     ]},
]

# ─── Template ────────────────────────────────────────────────────────────────

# ─── Search Index ───────────────────────────────────────────────────────────

def _build_search_index():
    """Build search index from all Markdown files (used by Fuse.js)"""
    index = []
    docs_dir = DOCS_ROOT

    for md_file in docs_dir.glob("*.md"):
        if md_file.name.startswith("."):
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
            title_m = re.match(r'^#\s+(.+)$', text)
            title = title_m.group(1).strip() if title_m else md_file.stem
            # Strip markdown syntax for plain text search
            plain = re.sub(r'#{1,6}\s+', '', text)
            plain = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', plain)
            plain = re.sub(r'[*_`~]', '', plain)
            plain = re.sub(r'\n+', ' ', plain).strip()[:500]
            index.append({
                "title": title,
                "text": plain,
                "url": f"/{md_file.name.replace('.md', '.html')}"
            })
        except Exception:
            pass

    # Also index SOP content
    sop_file = SOP_ROOT / "ROBOT-SOP.md"
    if sop_file.exists():
        try:
            text = sop_file.read_text(encoding="utf-8")
            # Index by chapter sections
            for ch_match in re.finditer(r'^#+\s+(.+)$', text, re.MULTILINE):
                title = ch_match.group(1).strip()[:80]
                pos = ch_match.start()
                snippet = text[pos:pos+300].replace('#', '').replace('\n', ' ').strip()[:200]
                index.append({
                    "title": f"SOP: {title}",
                    "text": snippet,
                    "url": "/sop/full.html"
                })
        except Exception:
            pass

    return index

# ─── Search Index ───────────────────────────────────────────────────────────

def make_page(active_id, title, content, extra_css=""):
    # Prism post-processing: convert codehilite HTML to Prism-compatible
    def _convert_codehilite(html):
        html = re.sub(r'class="codehilite"', 'class="codehilite line-numbers"', html)
        html = re.sub(r'<div class="codehilite"><pre><code class="(\w+)"',
                      r'<div class="codehilite"><pre class="language-\1"><code class="language-\1"', html)
        html = re.sub(r'<div class="codehilite"><pre><code>',
                      '<div class="codehilite"><pre class="language-text"><code class="language-text"', html)
        return html
    content = _convert_codehilite(content)
    nav_html = build_nav_html(NAV_CONFIG, active_id)
    versions = load_versions()
    search_index_json = json.dumps(_build_search_index(), ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — docs.0-1.ai</title>
<style>
:root{{
  --bg:#0a0a0f;--surface:#12121a;--surface2:#1a1a28;--border:#2a2a3a;
  --text:#e0e0e8;--text2:#8888a0;--accent:#ff6b35;--accent2:#70a1ff;
  --green:#2ed573;--yellow:#ffa502;--red:#ff4757;--purple:#a29bfe;
  --sidebar-w:260px;--header-h:56px;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:'DM Sans',system-ui,sans-serif;min-height:100vh}}
a{{color:var(--accent2);text-decoration:none}}
a:hover{{text-decoration:underline}}
blockquote{{border-left:3px solid var(--accent);padding:8px 16px;background:var(--surface2);margin:12px 0;border-radius:0 6px 6px 0;color:var(--text2)}}
code,pre{{font-family:'Fragment Mono','Courier New',monospace}}
pre{{background:#0d0d14;border:1px solid var(--border);padding:16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6}}
code{{background:#1a1a28;padding:2px 6px;border-radius:4px;font-size:0.9em;color:var(--accent2)}}
table{{width:100%;border-collapse:collapse;margin:12px 0}}
th{{background:var(--surface2);padding:10px 14px;text-align:left;border-bottom:2px solid var(--border);font-weight:600}}
td{{padding:8px 14px;border-bottom:1px solid var(--border)}}
tr:hover{{background:#1a1a28}}
.markdown-body h1{{font-size:1.8em;margin:24px 0 16px;padding-bottom:8px;border-bottom:1px solid var(--border);color:var(--accent)}}
.markdown-body h2{{font-size:1.4em;margin:20px 0 12px;color:var(--accent2)}}
.markdown-body h3{{font-size:1.1em;margin:16px 0 8px;color:var(--purple)}}
.markdown-body h4{{font-size:1em;margin:12px 0 6px;color:var(--yellow)}}
.markdown-body p{{margin:8px 0;line-height:1.7}}
.markdown-body ul,.markdown-body ol{{margin:8px 0 8px 20px;line-height:1.7}}
.markdown-body li{{margin:4px 0}}
.markdown-body .task-list-item{{list-style:none;margin-left:-20px}}
.markdown-body .task-list-item input{{margin-right:8px}}
.markdown-body hr{{border:none;border-top:1px solid var(--border);margin:24px 0}}
.header{{position:fixed;top:0;left:0;right:0;height:var(--header-h);background:rgba(10,10,15,0.95);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 20px;z-index:100; backdrop-filter:blur(10px)}}
.header-logo{{font-size:18px;font-weight:700;color:var(--accent);white-space:nowrap}}
.header-version{{margin-left:auto;font-size:12px;color:var(--text2);background:var(--surface2);padding:4px 10px;border-radius:12px;border:1px solid var(--border)}}
.sidebar{{position:fixed;top:var(--header-h);left:0;bottom:0;width:var(--sidebar-w);background:var(--surface);border-right:1px solid var(--border);overflow-y:auto;padding:12px 0}}
.sidebar-section{{padding:6px 0}}
.sidebar-section-title{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--text2);padding:8px 16px 4px;display:flex;align-items:center;gap:6px}}
.sidebar-link{{display:block;padding:6px 16px;font-size:13px;color:var(--text);transition:all .15s;border-left:2px solid transparent}}
.sidebar-link:hover,.sidebar-link.active{{color:var(--accent);border-left-color:var(--accent);background:rgba(255,107,53,.06);text-decoration:none}}
.sidebar-link.sub{{padding-left:28px;font-size:12px}}
.sidebar-children{{margin-left:16px;border-left:1px solid var(--border)}}
.main{{margin-left:var(--sidebar-w);margin-top:var(--header-h);padding:32px 40px;max-width:900px}}
.content-header{{margin-bottom:24px}}
.content-header h1{{font-size:2em;color:var(--accent);margin-bottom:8px}}
.content-meta{{font-size:13px;color:var(--text2)}}
.search-box{{margin-left:24px;position:relative}}
.search-box input{{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:8px;font-size:13px;width:200px;transition:all .2s}}
.search-box input:focus{{outline:none;border-color:var(--accent);width:260px}}
.search-results{{position:absolute;top:100%;right:0;left:0;background:var(--surface);border:1px solid var(--border);border-radius:8px;margin-top:4px;max-height:400px;overflow-y:auto;display:none;z-index:200;box-shadow:0 8px 32px rgba(0,0,0,.4)}}
.search-results.show{{display:block}}
.search-result-item{{padding:10px 14px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--border)}}
.search-result-item:hover{{background:var(--surface2)}}
.search-result-item:last-child{{border-bottom:none}}
.search-highlight{{color:var(--accent);font-weight:600}}
.tag{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;margin-left:6px}}
.tag-approved{{background:rgba(46,213,115,.15);color:var(--green)}}
.tag-pending{{background:rgba(255,165,2,.15);color:var(--yellow)}}
.tag-new{{background:rgba(162,155,254,.15);color:var(--purple)}}
.version-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:12px}}
.version-card-header{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
.version-badge{{background:var(--accent);color:#fff;font-size:12px;font-weight:700;padding:3px 10px;border-radius:10px}}
.version-date{{font-size:12px;color:var(--text2)}}
.version-change{{padding:4px 0;font-size:13px}}
.version-change-add{{color:var(--green)}}
.version-change-mod{{color:var(--yellow)}}
.version-change-del{{color:var(--red)}}
.module-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;margin:16px 0}}
.module-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;transition:all .2s}}
.module-card:hover{{border-color:var(--accent);transform:translateY(-2px)}}
.module-card-icon{{font-size:28px;margin-bottom:8px}}
.module-card-title{{font-weight:600;margin-bottom:4px}}
.module-card-desc{{font-size:12px;color:var(--text2);line-height:1.5}}
.report-item{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:12px}}
.report-item-header{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}
.report-item-title{{font-weight:600;flex:1}}
.report-item-date{{font-size:12px;color:var(--text2)}}
.report-item-meta{{font-size:12px;color:var(--text2)}}
.toc{{background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:24px;font-size:13px}}
.toc-title{{font-weight:600;margin-bottom:10px;color:var(--accent2)}}
.toc a{{color:var(--text2)}}
.toc a:hover{{color:var(--accent)}}
.btn{{display:inline-block;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;transition:all .15s;border:none;margin:2px}}
.btn-primary{{background:var(--accent);color:#fff}}
.btn-primary:hover{{background:#e55a28}}
.btn-outline{{background:transparent;border:1px solid var(--border);color:var(--text)}}
.btn-outline:hover{{border-color:var(--accent);color:var(--accent)}}
.alert{{padding:12px 16px;border-radius:8px;margin:12px 0;font-size:14px}}
.alert-info{{background:rgba(112,161,255,.1);border:1px solid rgba(112,161,255,.3);color:var(--accent2)}}
.alert-success{{background:rgba(46,213,115,.1);border:1px solid rgba(46,213,115,.3);color:var(--green)}}
.alert-warning{{background:rgba(255,165,2,.1);border:1px solid rgba(255,165,2,.3);color:var(--yellow)}}
.alert-danger{{background:rgba(255,71,87,.1);border:1px solid rgba(255,71,87,.3);color:var(--red)}}
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;margin-right:4px}}
.badge-a{{background:rgba(255,71,87,.15);color:#ff4757}}
.badge-b{{background:rgba(255,165,2,.15);color:#ffa502}}
.badge-c{{background:rgba(112,161,255,.15);color:#70a1ff}}
.badge-d{{background:rgba(162,155,254,.15);color:#a29bfe}}
</style>
<<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Fragment+Mono&display=swap" rel="stylesheet">
<!-- Prism.js Code Highlighting -->
<link href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-bash.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-javascript.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-typescript.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-json.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-yaml.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-markdown.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-sql.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-docker.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/line-numbers/prism-line-numbers.min.js"></script>
<!-- Fuse.js Fuzzy Search -->
<script src="https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js"></script>
<link href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/line-numbers/prism-line-numbers.min.css" rel="stylesheet" />
{extra_css}
</head>
<body>
<div class="header">
  <div class="header-logo">🦞 docs.0-1.ai</div>
  <div class="search-box">
    <input type="text" id="searchInput" placeholder="搜索文档..." oninput="handleSearch(this.value)">
    <div class="search-results" id="searchResults"></div>
  </div>
  <div class="header-version">v0.1.0</div>
</div>
<nav class="sidebar">
{nav_html}
</nav>
<main class="main">
{content}
</main>
<script>
// Build search index from localStorage
// Fuse.js search
const searchIndex = {search_index_json};
const fuse = new Fuse(searchIndex, {{
  keys: ['title', 'text'],
  threshold: 0.4,
  includeScore: true,
  minMatchCharLength: 2
}});
function handleSearch(q) {{
  const results = document.getElementById('searchResults');
  if (!q.trim()) {{ results.classList.remove('show'); return; }}
  const found = fuse.search(q, {{ limit: 8 }});
  if (!found.length) {{ results.innerHTML='<div class="search-result-item">无结果</div>'; results.classList.add('show'); return; }}
  results.innerHTML = found.map(r =>
    `<div class="search-result-item" onclick="location.href='${{r.item.url}}'">
      <div>${{r.item.title}}</div>
      <div style="font-size:12px;color:var(--text2);margin-top:2px">${{r.item.text.slice(0,80)}}...</div>
    </div>`
  ).join('');
  results.classList.add('show');
}}
// Keyboard shortcut
document.addEventListener('keydown', e => {{
  if ((e.ctrlKey||e.metaKey) && e.key==='k') {{ e.preventDefault(); document.getElementById('searchInput').focus(); }}
  if (e.key === 'Escape') {{ document.getElementById('searchResults').classList.remove('show'); }}
}});
document.addEventListener('click', e => {{
  if (!e.target.closest('.search-box')) document.getElementById('searchResults').classList.remove('show');
}});
// Highlight active nav
const path = location.pathname;
document.querySelectorAll('.sidebar-link').forEach(l => {{
  if (l.getAttribute('href') === path) l.classList.add('active');
}});
// Prism code highlighting
Prism.highlightAll();
</script>
</body>
</html>"""

def build_nav_html(config, active_id, depth=0):
    html = ""
    for item in config:
        if item.get("children"):
            html += f'<div class="sidebar-section"><div class="sidebar-section-title">{item.get("icon","")} {item["label"]}</div>'
            html += '<div class="sidebar-children">'
            for child in item["children"]:
                cls = "sidebar-link sub" if depth >= 1 else "sidebar-link"
                active = "active" if child.get("id") == active_id else ""
                href = child.get("path","#")
                target = ' target="_blank"' if child.get("external") else ""
                html += f'<a class="{cls} {active}" href="{href}"{target}>{child["label"]}</a>'
            html += '</div></div>'
        else:
            active = "active" if item.get("id") == active_id else ""
            href = item.get("path","#")
            target = ' target="_blank"' if item.get("external") else ""
            html += f'<div class="sidebar-section"><a class="sidebar-link {active}" href="{href}"{target}>{item.get("icon","")} {item["label"]}</a></div>'
    return html

def load_versions():
    if VERSIONS_FILE.exists():
        try:
            return json.loads(VERSIONS_FILE.read_text())
        except:
            pass
    return {}

# ─── Markdown → TOC ──────────────────────────────────────────────────────────

def extract_toc(markdown_text):
    """Extract headings for table of contents"""
    toc = []
    for line in markdown_text.split('\n'):
        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', m.group(2))
            anchor = text.lower().replace(' ', '-').replace('.', '').replace(':', '')
            anchor = re.sub(r'[^\w\-]', '', anchor)
            toc.append({'level': level, 'text': text, 'anchor': anchor})
    return toc

def render_toc(toc):
    if not toc: return ""
    html = '<div class="toc"><div class="toc-title">📑 目录</div>'
    for item in toc[:15]:
        indent = (item['level'] - 1) * 16
        html += f'<div style="padding-left:{indent}px;margin:3px 0"><a href="#{item["anchor"]}">{item["text"]}</a></div>'
    html += '</div>'
    return html

# ─── SOP Content Loader ──────────────────────────────────────────────────────

def load_sop_content():
    """Load and cache SOP content"""
    cache_file = DOCS_ROOT / ".sop_cache.json"
    sop_file = SOP_ROOT / "ROBOT-SOP.md"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text())
        except:
            pass
    if not sop_file.exists():
        return {}
    text = sop_file.read_text()
    chapters = parse_sop_chapters(text)
    # Cache
    cache_file.write_text(json.dumps(chapters, ensure_ascii=False))
    return chapters

def parse_sop_chapters(text):
    """Parse SOP into chapters"""
    lines = text.split('\n')
    chapters = {}
    current = {'title': '', 'content': '', 'subsections': []}
    current_subsection = {'title': '', 'content': ''}
    current_h1 = None
    current_h2 = None

    def save_subsection():
        if current_subsection['title'] or current_subsection['content'].strip():
            current['subsections'].append({
                'title': current_subsection['title'],
                'content': current_subsection['content'].strip()
            })

    for line in lines:
        if line.startswith('# '):
            if current['title']:
                save_subsection()
                chapters[current_h1] = dict(current)
            current = {'title': line[2:].strip(), 'content': '', 'subsections': []}
            current_h1 = current['title']
            current_h2 = None
            current_subsection = {'title': '', 'content': ''}
        elif line.startswith('## '):
            if current_subsection['title'] or current_subsection['content'].strip():
                save_subsection()
            current_subsection = {'title': line[3:].strip(), 'content': ''}
            current_h2 = current_subsection['title']
        elif line.startswith('### '):
            if current_subsection['title'] and current_subsection['content'].strip():
                save_subsection()
            current_subsection = {'title': '— ' + line[4:].strip(), 'content': ''}
        else:
            current_subsection['content'] += line + '\n'

    if current_subsection['title'] or current_subsection['content'].strip():
        save_subsection()
    if current['title']:
        chapters[current_h1] = dict(current)

    # Render each chapter to HTML
    for ch_id, ch in chapters.items():
        ch['html'] = render_markdown(ch['content'])
        for sub in ch['subsections']:
            sub['html'] = render_markdown(sub['content'])

    return chapters

# ─── Report Loader ───────────────────────────────────────────────────────────

def load_reports():
    """Load research reports"""
    reports_dir = SOP_ROOT / "night-build" / "reports"
    reports = []
    if reports_dir.exists():
        for f in sorted(reports_dir.glob("*.md"), reverse=True):
            content = f.read_text()
            # Extract title
            first_line = content.split('\n')[0]
            title = re.sub(r'^#+\s*', '', first_line).strip()
            if not title:
                title = f.stem
            # Extract date
            date_m = re.search(r'(\d{4}-\d{2}-\d{2})', content)
            date = date_m.group(1) if date_m else "未知"
            # Determine sequence
            seq_m = re.match(r'^([A-D])-(\d+)', f.stem)
            seq_type = seq_m.group(1) if seq_m else "?"
            seq_num = seq_m.group(2) if seq_m else "?"
            # Extract status
            status = "pending"
            if "✅" in content[:200] or "已解决" in content[:200] or "已完成" in content[:200]:
                status = "approved"
            # First 200 chars as summary
            summary = re.sub(r'#.*?\n', '', content[:300]).strip()[:150]
            reports.append({
                'id': f.stem,
                'title': title,
                'date': date,
                'seq_type': seq_type,
                'seq_num': seq_num,
                'status': status,
                'summary': summary,
                'url': f'/reports/{f.name}'
            })
    return reports

# ─── Content Generators ─────────────────────────────────────────────────────

def make_home():
    """Home page"""
    versions = load_versions()
    reports = load_reports()
    approved_count = len([r for r in reports if r['status'] == 'approved'])
    pending_count = len([r for r in reports if r['status'] == 'pending'])
    toc_html = render_toc([
        {'level':1,'text':'欢迎使用 docs.0-1.ai','anchor':'welcome'},
        {'level':2,'text':'项目总览','anchor':'overview'},
        {'level':2,'text':'模块状态','anchor':'modules'},
        {'level':2,'text':'调研报告','anchor':'reports'},
        {'level':2,'text':'版本变更','anchor':'changelog'},
    ])
    return make_page("home", "首页", f"""
{toc_html}
<div class="content-header">
  <h1>🦞 欢迎使用 docs.0-1.ai</h1>
  <div class="content-meta">0-1 私人 AI 机器人 · 本地文档站 · v0.1.0</div>
</div>
<div class="alert alert-info">
  📖 <strong>0-1 项目</strong>是一台会跟着 AI 能力一起长大的陪伴机器人。<br>
  本站点托管所有技术文档、调研报告、模块说明和版本变更记录。
</div>
<h2 id="overview">📊 项目总览</h2>
<div class="module-grid">
  <div class="module-card">
    <div class="module-card-icon">🧠</div>
    <div class="module-card-title">贵庚记忆系统</div>
    <div class="module-card-desc">Semantic Cache · Ubuntu 节点 · 8683+ 条索引</div>
  </div>
  <div class="module-card">
    <div class="module-card-icon">🌍</div>
    <div class="module-card-title">LeWM 世界模型</div>
    <div class="module-card-desc">视觉encoder + action decoder · RTX 2060 训练</div>
  </div>
  <div class="module-card">
    <div class="module-card-icon">🦾</div>
    <div class="module-card-title">机械臂模块</div>
    <div class="module-card-desc">Cyber Bricks · MQTT 指令控制</div>
  </div>
  <div class="module-card">
    <div class="module-card-icon">👁️</div>
    <div class="module-card-title">视觉识别</div>
    <div class="module-card-desc">ESP32-Cam · Jetson Nano · RTSP 推流</div>
  </div>
  <div class="module-card">
    <div class="module-card-icon">🔯</div>
    <div class="module-card-title">星闪通信</div>
    <div class="module-card-desc">BearPi H3863 · SLE 20μs 低时延</div>
  </div>
  <div class="module-card">
    <div class="module-card-icon">🖥️</div>
    <div class="module-card-title">OpenClaw</div>
    <div class="module-card-desc">Gateway · MCP 工具 · alsoAllow 配置</div>
  </div>
</div>
<h2 id="reports">📊 调研报告</h2>
<div class="alert">
  已发布：<strong>{approved_count}</strong> 个 &nbsp;|&nbsp; 待审批：<strong>{pending_count}</strong> 个
</div>
<div class="module-grid">
  <div class="module-card" onclick="location.href='/reports/approved.html'" style="cursor:pointer">
    <div class="module-card-icon">✅</div>
    <div class="module-card-title">已发布报告</div>
    <div class="module-card-desc">{approved_count} 个研究报告 · 可阅读</div>
  </div>
  <div class="module-card" onclick="location.href='/reports/pending.html'" style="cursor:pointer">
    <div class="module-card-icon">⏳</div>
    <div class="module-card-title">待审批报告</div>
    <div class="module-card-desc">{pending_count} 个报告 · 需审核后发布</div>
  </div>
  <div class="module-card" onclick="location.href='/changelog/'" style="cursor:pointer">
    <div class="module-card-icon">📝</div>
    <div class="module-card-title">版本变更</div>
    <div class="module-card-desc">OpenClaw + 各模块版本追踪</div>
  </div>
</div>
<h2 id="changelog">📝 版本变更</h2>
""")

def make_sop_chapter(chapter_num, active_id):
    """Render a SOP chapter"""
    chapters = load_sop_content()
    # Map chapter_num to chapter key
    ch_keys = list(chapters.keys())
    if chapter_num == 0:
        return make_page(active_id, f"第{chapter_num}章：启动与配置", "<p>章节内容正在生成中...</p>")

    chapter_names = {
        1: "第一章：概念与愿景",
        2: "第二章：硬件体系",
        3: "第三章：软件架构",
        4: "第四章：实施阶段",
        5: "第五章：安全系统",
        6: "第六章：数据管理",
    }
    ch_name = chapter_names.get(chapter_num, "")
    ch = chapters.get(ch_name, {})

    if not ch:
        return make_page(active_id, f"第{chapter_num}章", "<p>章节未找到。</p>")

    toc = extract_toc(ch['content'])
    toc_html = render_toc(toc) if toc else ""

    subsections_html = ""
    for sub in ch.get('subsections', [])[:20]:  # Limit for performance
        sub_toc = extract_toc(sub['content'])
        anchor = sub['title'].lower().replace(' ', '-').replace('.', '').replace(':', '')
        anchor = re.sub(r'[^\w\-]', '', anchor)
        subsections_html += f'<h2 id="{anchor}">{sub["title"]}</h2>'
        # Only render first part to avoid huge pages
        sub_content = sub['content'][:3000]
        if len(sub['content']) > 3000:
            sub_content += f'\n\n<p style="color:var(--text2);font-size:13px">...（内容过长，详见完整 SOP）</p>'
        subsections_html += render_markdown(sub_content)

    return make_page(active_id, ch.get('title', f"第{chapter_num}章"), f"""
{toc_html}
<div class="content-header">
  <h1>{ch.get('title', f'第{chapter_num}章')}</h1>
  <div class="content-meta">0-1 实施指南 · 章节 {chapter_num}</div>
</div>
<div class="alert alert-info">📖 本章节内容摘录自完整 SOP，完整内容请查看 <a href="/sop/full.html">完整 SOP</a>。</div>
{subsections_html}
""")

def make_sop_full():
    """Full SOP as single page"""
    chapters = load_sop_content()
    ch_keys = list(chapters.keys())
    if not ch_keys:
        return make_page("sop-full", "完整 SOP", "<p>SOP 文件未找到。</p>")

    sections_html = ""
    for ch_name, ch in chapters.items():
        sections_html += f'<h1 id="{ch_name[:20]}">{ch.get("title","")}</h1>\n'
        sections_html += ch.get('html', '')[:10000] + '\n\n'

    return make_page("sop-full", "完整 SOP", f"""
<div class="content-header">
  <h1>📖 0-1 完整实施指南</h1>
  <div class="content-meta">{len(chapters)} 个章节 · 完整内容</div>
</div>
<div class="alert alert-warning">⚠️ 完整 SOP 内容较多，建议使用浏览器 Ctrl+F 搜索。</div>
{sections_html}
""")

def make_reports_list(status_filter="approved"):
    """Research reports list page"""
    reports = load_reports()
    filtered = [r for r in reports if r['status'] == status_filter]

    title = "已发布报告" if status_filter == "approved" else "待审批报告"
    badge_class = "badge-approved" if status_filter == "approved" else "badge-pending"
    icon = "✅" if status_filter == "approved" else "⏳"

    items_html = ""
    for r in filtered:
        badge = f'<span class="badge badge-{r["seq_type"].lower()}">{r["seq_type"]}-{r["seq_num"]}</span>'
        items_html += f"""
        <div class="report-item">
          <div class="report-item-header">
            <span class="report-item-title">{icon} {r['title']}</span>
            {badge}
            <span class="report-item-date">{r['date']}</span>
          </div>
          <div class="report-item-meta">{r['summary']}...</div>
          <div style="margin-top:10px">
            <a href="{r['url']}" class="btn btn-outline" style="font-size:12px;padding:4px 12px">📖 阅读报告</a>
          </div>
        </div>"""

    if not items_html:
        items_html = '<div class="alert alert-info">暂无报告</div>'

    return make_page(f"rep-{status_filter}", title, f"""
<div class="content-header">
  <h1>{icon} {title}</h1>
  <div class="content-meta">共 {len(filtered)} 个报告</div>
</div>
<div style="margin-bottom:20px">
  <a href="/reports/approved.html" class="btn btn-outline {'btn-primary' if status_filter=='approved' else ''}">✅ 已发布</a>
  <a href="/reports/pending.html" class="btn btn-outline {'btn-primary' if status_filter=='pending' else ''}">⏳ 待审批</a>
</div>
{items_html}
""")

def make_report_detail(filename):
    """Single report detail"""
    reports_dir = SOP_ROOT / "night-build" / "reports"
    f = reports_dir / filename
    if not f.exists():
        return make_page("report", "报告", f"<p>报告不存在：{filename}</p>")
    content = f.read_text()
    html = render_markdown(content)
    first_line = content.split('\n')[0]
    title = re.sub(r'^#+\s*', '', first_line).strip() or filename
    return make_page("reports", title, f"""
<div class="content-header">
  <h1>{title}</h1>
  <div class="content-meta">{filename}</div>
</div>
<div style="margin-bottom:16px">
  <a href="/reports/approved.html" class="btn btn-outline" style="font-size:12px">← 返回报告列表</a>
</div>
{html}
""")

def make_changelog_openclaw():
    """OpenClaw changelog page"""
    versions = load_versions()
    oc = versions.get("openclaw", {})
    oc_changes = oc.get("changes", [])

    changes_html = ""
    for c in reversed(oc_changes[:30]):
        ctype_map = {"added": "➕", "modified": "✏️", "fixed": "🔧", "removed": "🗑️"}
        icon = ctype_map.get(c.get("type", ""), "📝")
        cls = f"version-change-{c.get('type','add')}"
        changes_html += f"""
        <div class="version-change">
          <span style="color:var(--text2);font-size:12px;margin-right:8px">{c.get('date','')}</span>
          <span class="{cls}">{icon} {c.get('detail','')}</span>
        </div>"""

    if not changes_html:
        changes_html = '<div class="alert alert-info">暂无变更记录。使用 <code>docs-server.py --add-change</code> 添加。</div>'

    return make_page("cl-openclaw", "OpenClaw 版本变更", f"""
<div class="content-header">
  <h1>📝 OpenClaw 版本变更</h1>
  <div class="content-meta">当前版本：{oc.get('version', '未知')}</div>
</div>
<div class="alert alert-info">
  OpenClaw 版本变更从官方 release log 解析。自定义修改由人工记录。
</div>
{changes_html}
<h2 style="margin-top:24px">📋 添加变更记录</h2>
<pre style="font-size:12px;line-height:1.8">
# 命令行添加变更（待实现）
python3 docs-server.py add-change --module openclaw --type modified --detail "alsoAllow配置修复"

# 或直接编辑版本文件
open {VERSIONS_FILE}
</pre>
""")

# ─── Module Data ───────────────────────────────────────────────────────────────

MODULE_DATA = [
    ("贵庚记忆系统", "gui-geng", "🧠", "Semantic Cache + Ubuntu 32GB RAM，语义索引"),
    ("LeWM 世界模型", "lewm", "🌍", "视觉 encoder + action decoder，RTX 2060 本地训练"),
    ("机械臂模块", "arm", "🦾", "Cyber Bricks ESP32 + MicroPython，MQTT 指令控制"),
    ("视觉识别", "vision", "👁️", "ESP32-Cam OV2640 + Jetson Nano YOLO"),
    ("吸盘抓手", "suction", "🔯", "待定"),
    ("移动模块", "locomotion", "🚗", "待定"),
    ("面部模块", "face", "😊", "待定"),
]

def get_module_by_slug(slug):
    for name, s, icon, desc in MODULE_DATA:
        if s == slug:
            return (name, s, icon, desc)
    return None

def make_modules_index():
    """Modules overview"""
    versions = load_versions()
    cards_html = ""
    for name, slug, icon, desc in MODULE_DATA:
        ver = versions.get(slug, {}).get("version", "v0.0.1")
        cards_html += f"""
        <div class="module-card" onclick="location.href='/modules/{slug}.html'" style="cursor:pointer">
          <div class="module-card-icon">{icon}</div>
          <div class="module-card-title">{name}</div>
          <div class="module-card-desc">{desc}</div>
          <div style="margin-top:8px"><span class="tag tag-new">{ver}</span></div>
        </div>"""

    return make_page("modules", "模块文档", f"""
<div class="content-header">
  <h1>🧩 模块文档</h1>
  <div class="content-meta">0-1 项目的各个功能模块</div>
</div>
<div class="module-grid">
{cards_html}
</div>
""")

def make_module_detail(slug):
    """Individual module detail page"""
    module_info = get_module_by_slug(slug)
    if not module_info:
        return make_page("modules", "模块未找到", """
<div class="content-header"><h1>❌ 模块未找到</h1></div>
<div class="alert alert-danger">请求的模块不存在。</div>
<a href="/modules/" class="btn btn-outline">← 返回模块列表</a>
""")

    name, s, icon, desc = module_info
    versions = load_versions()
    ver_info = versions.get(slug, {})
    current_version = ver_info.get("version", "v0.0.1")
    changes = ver_info.get("changes", [])

    # Try to load Markdown content for this module
    md_file = DOCS_ROOT / "modules" / f"{slug}.md"
    if md_file.exists():
        try:
            md_text = md_file.read_text(encoding="utf-8")
            html_content = render_markdown(md_text)
        except Exception:
            html_content = None
    else:
        html_content = None

    # Build changelog HTML
    changelog_html = ""
    for c in reversed(changes[:10]):
        ctype_map = {"added": "➕", "modified": "✏️", "fixed": "🔧", "removed": "🗑️", "feat": "✨", "config": "⚙️"}
        icon = ctype_map.get(c.get("type", ""), "📝")
        cls = f"version-change-{c.get('type','add')}"
        changelog_html += f'<div class="version-change"><span style="color:var(--text2);font-size:12px;margin-right:8px">{c.get("date","")}</span><span class="{cls}">{icon} {c.get("detail","")}</span></div>'

    # Content section
    if html_content:
        content_section = f"""
<h2 id="content">📖 模块文档</h2>
{html_content}
"""
    else:
        content_section = f"""
<h2 id="content">📖 模块文档</h2>
<div class="alert alert-info">
  文档文件 <code>docs/modules/{slug}.md</code> 尚未创建。
  当前显示基础信息。
</div>
<div class="module-card" style="max-width:500px">
  <div class="module-card-icon" style="font-size:48px">{icon}</div>
  <div class="module-card-title" style="font-size:1.4em;margin:8px 0">{name}</div>
  <div class="module-card-desc">{desc}</div>
</div>
"""

    toc_items = [{"level": 2, "text": "模块文档", "anchor": "content"}]
    if changelog_html:
        toc_items.append({"level": 2, "text": "版本变更", "anchor": "changelog"})
    toc_html = render_toc(toc_items)

    return make_page(f"mod-{slug}", f"{name}", f"""
{toc_html}
<div class="content-header">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
    <span style="font-size:32px">{icon}</span>
    <div>
      <h1 style="border-bottom:none;margin-bottom:4px">{name}</h1>
      <span class="tag tag-new">v{current_version}</span>
    </div>
  </div>
  <div class="content-meta">{desc}</div>
</div>
{content_section}
{'<h2 id="changelog">📝 版本变更</h2>' + changelog_html if changelog_html else ''}
<div style="margin-top:24px">
  <a href="/modules/" class="btn btn-outline">← 返回模块列表</a>
</div>
""")

def make_tool_config():
    """Tools configuration page"""
    try:
        import json as _json
        cfg_file = Path.home() / ".openclaw" / "openclaw.json"
        cfg = _json.loads(cfg_file.read_text())
        also_allow = cfg.get("tools", {}).get("alsoAllow", [])
        profile = cfg.get("tools", {}).get("profile", "coding")
        plugins = cfg.get("plugins", {}).get("entries", {})
    except:
        also_allow, profile, plugins = [], "unknown", {}

    tools_html = ""
    for t in also_allow:
        tools_html += f'<li><code>{t}</code></li>'

    mcp_html = ""
    for name, entry in plugins.items():
        if isinstance(entry, dict):
            cfg_detail = entry.get("config", {})
            if isinstance(cfg_detail, dict):
                srv_name = cfg_detail.get("servers", [{}])[0].get("name", name) if cfg_detail.get("servers") else name
                mcp_html += f'<tr><td><code>{name}</code></td><td>{srv_name}</td><td><span class="tag tag-approved">active</span></td></tr>'

    return make_page("tools", "工具配置", f"""
<div class="content-header">
  <h1>🔧 工具配置</h1>
  <div class="content-meta">当前 Gateway 配置 · openclaw.json</div>
</div>
<h2>MCP 工具 (alsoAllow)</h2>
<div class="alert alert-info">
  当前 profile：<strong>{profile}</strong> &nbsp;|&nbsp; 已授权工具：<strong>{len(also_allow)}</strong> 个
</div>
<ul>{tools_html or '<li>无</li>'}</ul>
<h2 style="margin-top:24px">MCP Server 插件</h2>
<table>
  <th>插件名</th><th>服务器</th><th>状态</th>
  {mcp_html or '<tr><td colspan="3">无</td></tr>'}
</table>
""")

def make_refs():
    """Reference links page"""
    return make_page("refs", "参考链接", f"""
<div class="content-header">
  <h1>🔗 参考链接</h1>
</div>
<h2>本地服务</h2>
<div class="module-grid">
  <div class="module-card" onclick="location.href='http://127.0.0.1:18999/dashboard.html'" style="cursor:pointer">
    <div class="module-card-icon">📊</div>
    <div class="module-card-title">Dashboard</div>
    <div class="module-card-desc">0-1 项目看板 · Night Build 状态</div>
  </div>
  <div class="module-card" onclick="location.href='http://127.0.0.1:18999/world.html'" style="cursor:pointer">
    <div class="module-card-icon">🌍</div>
    <div class="module-card-title">World View</div>
    <div class="module-card-desc">世界视图 · 可视化</div>
  </div>
</div>
<h2 style="margin-top:24px">外部文档</h2>
<div class="module-grid">
  <div class="module-card" onclick="location.href='https://docs.openclaw.ai'" style="cursor:pointer">
    <div class="module-card-icon">📚</div>
    <div class="module-card-title">OpenClaw 官方文档</div>
    <div class="module-card-desc">docs.openclaw.ai</div>
  </div>
  <div class="module-card" onclick="location.href='https://github.com/openclaw/openclaw'" style="cursor:pointer">
    <div class="module-card-icon">⚙️</div>
    <div class="module-card-title">OpenClaw GitHub</div>
    <div class="module-card-desc">源码 · Issue · PR</div>
  </div>
  <div class="module-card" onclick="location.href='https://clawhub.ai'" style="cursor:pointer">
    <div class="module-card-icon">🦞</div>
    <div class="module-card-title">ClawhHub</div>
    <div class="module-card-desc">Skill 市场</div>
  </div>
</div>
""")

# ─── Request Handler ─────────────────────────────────────────────────────────

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS_ROOT), **kwargs)

    def do_GET(self):
        path = unquote(self.path)

        # ── Routes ──────────────────────────────────────────────────
        if path == "/" or path == "/index.html":
            return self.send_html(make_home())

        # SOP chapters
        m = re.match(r'^/sop/chapter-(\d+)\.html$', path)
        if m:
            ch = int(m.group(1))
            return self.send_html(make_sop_chapter(ch, f"sop-ch{ch}"))

        if path == "/sop/full.html":
            return self.send_html(make_sop_full())

        if path.startswith("/sop/"):
            return self.send_html(make_sop_chapter(1, "sop"))

        # Reports
        if path == "/reports/" or path == "/reports/index.html":
            return self.send_html(make_reports_list("approved"))
        if path == "/reports/approved.html":
            return self.send_html(make_reports_list("approved"))
        if path == "/reports/pending.html":
            return self.send_html(make_reports_list("pending"))

        m = re.match(r'^/reports/(.+\.md)$', path)
        if m:
            return self.send_html(make_report_detail(m.group(1)))

        # Changelog
        if path == "/changelog/openclaw.html":
            return self.send_html(make_changelog_openclaw())
        if path == "/changelog/modules.html":
            return self.send_html(make_modules_index())
        if path == "/changelog/timeline.html":
            return self.send_html(make_page("cl-timeline", "完整时间线", "<p>时间线生成中...</p>"))
        if path == "/changelog/":
            return self.send_html(make_changelog_openclaw())

        # Modules
        if path == "/modules/":
            return self.send_html(make_modules_index())

        if path.startswith("/modules/"):
            slug_m = re.match(r'^/modules/([a-z\-]+)\.html$', path)
            if slug_m:
                slug = slug_m.group(1)
                return self.send_html(make_module_detail(slug))

        # Tools
        if path == "/tools/mcp.html" or path == "/tools/":
            return self.send_html(make_tool_config())

        # Refs - proxy to 18999
        if path == "/refs/dashboard/" or path == "/refs/dashboard.html":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:18999/dashboard.html")
            self.end_headers()
            return
        if path == "/refs/world/" or path == "/refs/world.html":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:18999/world.html")
            self.end_headers()
            return

        # Static files
        return super().do_GET()

    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, fmt, *args):
        pass  # Silence logs

# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Ensure directories exist
    (DOCS_ROOT / "reports").mkdir(exist_ok=True)
    (DOCS_ROOT / ".versions").mkdir(exist_ok=True)
    (DOCS_ROOT / "modules").mkdir(exist_ok=True)
    (DOCS_ROOT / "changelog").mkdir(exist_ok=True)

    # Init versions file if missing
    if not VERSIONS_FILE.exists():
        VERSIONS_FILE.write_text(json.dumps({
            "openclaw": {
                "version": "2026.03.31",
                "changes": [
                    {"date": "2026-03-31", "type": "modified",
                     "detail": "alsoAllow移到tools级别，profile改为full，MCP工具可正常通行"}
                ]
            },
            "gui-geng": {"version": "0.1.0", "changes": []},
            "lewm": {"version": "0.1.0", "changes": []},
            "arm": {"version": "0.1.0", "changes": []},
            "vision": {"version": "0.0.1", "changes": []},
            "suction": {"version": "0.0.1", "changes": []},
            "locomotion": {"version": "0.0.1", "changes": []},
            "face": {"version": "0.0.1", "changes": []},
        }, ensure_ascii=False, indent=2))

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🦞 docs.0-1.ai server running at http://127.0.0.1:{PORT}/")
        httpd.serve_forever()
