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
import datetime as dt
from pathlib import Path
from urllib.parse import unquote

PORT = 18998
SCRIPT_PREFIX = "/docs.0-1.ai"
DOCS_ROOT = Path(__file__).parent.parent / "docs"
VERSIONS_FILE = DOCS_ROOT / ".versions" / "versions.json"
REPORTS_STATUS = DOCS_ROOT / "reports" / "status.json"
SOP_ROOT = Path.home() / ".openclaw" / "workspace" / "harness" / "robot"

# ─── Backlinks: Page Name → URL Map ──────────────────────────────────────────

BACKLINK_MAP = {
    # Modules
    "贵庚":        f"{SCRIPT_PREFIX}/modules/gui-geng.html",
    "gui-geng":   f"{SCRIPT_PREFIX}/modules/gui-geng.html",
    "gui_geng":   f"{SCRIPT_PREFIX}/modules/gui-geng.html",
    "LeWM":       f"{SCRIPT_PREFIX}/modules/lewm.html",
    "lewm":       f"{SCRIPT_PREFIX}/modules/lewm.html",
    "世界模型":    f"{SCRIPT_PREFIX}/modules/lewm.html",
    "机械臂":      f"{SCRIPT_PREFIX}/modules/arm.html",
    "arm":        f"{SCRIPT_PREFIX}/modules/arm.html",
    "vision":     f"{SCRIPT_PREFIX}/modules/vision.html",
    "视觉":       f"{SCRIPT_PREFIX}/modules/vision.html",
    "suction":    f"{SCRIPT_PREFIX}/modules/suction.html",
    "吸盘":       f"{SCRIPT_PREFIX}/modules/suction.html",
    "locomotion": f"{SCRIPT_PREFIX}/modules/locomotion.html",
    "移动":       f"{SCRIPT_PREFIX}/modules/locomotion.html",
    "face":       f"{SCRIPT_PREFIX}/modules/face.html",
    "面部":       f"{SCRIPT_PREFIX}/modules/face.html",
    # SOP
    "ROBOT-SOP":  f"{SCRIPT_PREFIX}/sop/full.html",
    "robot-sop":  f"{SCRIPT_PREFIX}/sop/full.html",
    "robot_sop":  f"{SCRIPT_PREFIX}/sop/full.html",
    "SOP":        f"{SCRIPT_PREFIX}/sop/full.html",
    # Reports
    "reports":    f"{SCRIPT_PREFIX}/reports/approved.html",
    "报告":       f"{SCRIPT_PREFIX}/reports/approved.html",
}

# Regex for [[wiki-links]] — matches [[text]] and [[text|display]]
WIKI_LINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')

# ─── Search Cache (5-min TTL) ─────────────────────────────────────────────────
_SEARCH_CACHE = {}
_SEARCH_CACHE_TIME = {}

def _get_cache(key):
    import time
    if key in _SEARCH_CACHE:
        if time.time() - _SEARCH_CACHE_TIME[key] < 300:
            return _SEARCH_CACHE[key]
    return None

def _set_cache(key, value):
    import time
    _SEARCH_CACHE[key] = value
    _SEARCH_CACHE_TIME[key] = time.time()

def _extract_snippet(content, query, context=100):
    """Extract snippet around first match of query (case-insensitive)."""
    idx = content.lower().find(query.lower())
    if idx == -1:
        return content[:200]
    start = max(0, idx - context)
    end = min(len(content), idx + len(query) + context)
    snippet = content[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(content):
        snippet = snippet + "…"
    return snippet

def _score_text(text, query):
    """Simple scoring: title match = 2.0, content match = 1.0"""
    q = query.lower()
    t = text.lower()
    score = 0.0
    # Count occurrences in content
    pos = 0
    while True:
        pos = t.find(q, pos)
        if pos == -1:
            break
        score += 1.0
        pos += len(q)
    return score

def search_docs(query):
    """Search across SOP, modules, and reports. Returns dict with results."""
    import time
    cache_key = query.strip().lower()
    cached = _get_cache(cache_key)
    if cached is not None:
        return cached

    results = []
    q = query.strip()
    if not q:
        return {"query": query, "results": [], "total": 0}

    # ── 1. SOP chapters (ROBOT-SOP.md) ────────────────────────────
    sop_file = SOP_ROOT / "ROBOT-SOP.md"
    if sop_file.exists():
        try:
            sop_text = sop_file.read_text(encoding='utf-8')
            sop_chapters = parse_sop_chapters(sop_text)
            for ch_key, ch in sop_chapters.items():
                title_match = q.lower() in ch_key.lower()
                content_score = _score_text(ch.get('content', ''), q)
                sub_scores = [_score_text(sub.get('content', ''), q) for sub in ch.get('subsections', [])]
                total_score = (2.0 if title_match else 0) + content_score + sum(sub_scores)
                if total_score > 0:
                    # Find snippet from chapter content or subsections
                    full_content = ch.get('content', '') + '\n' + '\n'.join(
                        sub.get('content', '') for sub in ch.get('subsections', [])
                    )
                    snippet = _extract_snippet(full_content, q)
                    results.append({
                        "title": ch_key,
                        "url": f"{SCRIPT_PREFIX}/sop/full.html",
                        "snippet": snippet,
                        "score": min(total_score / 10.0, 1.0)
                    })
        except Exception as e:
            pass

    # ── 2. Module docs (docs/modules/*.md) ──────────────────────────
    modules_dir = DOCS_ROOT / "modules"
    if modules_dir.exists():
        for md_file in modules_dir.glob("*.md"):
            try:
                text = md_file.read_text(encoding='utf-8')
                title_m = re.match(r'^#\s+(.+)$', text)
                title = title_m.group(1).strip() if title_m else md_file.stem
                title_match = q.lower() in title.lower()
                content_score = _score_text(text, q)
                total_score = (2.0 if title_match else 0) + content_score
                if total_score > 0:
                    snippet = _extract_snippet(text, q)
                    url = f"{SCRIPT_PREFIX}/modules/{md_file.stem}.html"
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                        "score": min(total_score / 5.0, 1.0)
                    })
            except Exception:
                pass

    # ── 3. Reports (SOP_ROOT/night-build/reports/*.md) ─────────────
    reports_dir = SOP_ROOT / "night-build" / "reports"
    if reports_dir.exists():
        for md_file in reports_dir.glob("*.md"):
            if md_file.name in ("INDEX.md",):
                continue
            try:
                text = md_file.read_text(encoding='utf-8')
                title_m = re.match(r'^#\s+(.+)$', text)
                title = title_m.group(1).strip() if title_m else md_file.stem
                title_match = q.lower() in title.lower()
                content_score = _score_text(text, q)
                total_score = (2.0 if title_match else 0) + content_score
                if total_score > 0:
                    snippet = _extract_snippet(text, q)
                    url = f"{SCRIPT_PREFIX}/reports/{md_file.name.replace('.md','.html')}"
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                        "score": min(total_score / 5.0, 1.0)
                    })
            except Exception:
                pass

    # Sort by score descending
    results.sort(key=lambda r: r['score'], reverse=True)
    # Normalize scores to 0-1 range
    max_score = results[0]['score'] if results else 1.0
    for r in results:
        r['score'] = round(r['score'] / max_score, 2) if max_score > 0 else 0.0

    output = {
        "query": query,
        "results": results[:20],
        "total": len(results)
    }
    _set_cache(cache_key, output)
    return output

# Global backlinks index: target_url → list of {source_url, source_title}
_BACKLINKS_INDEX = None

def build_backlinks_index():
    """Scan all .md files and build a backlinks index.
    Returns: { target_url: [ {title, url}, ... ], ... }
    """
    global _BACKLINKS_INDEX
    if _BACKLINKS_INDEX is not None:
        return _BACKLINKS_INDEX

    index = {}  # target_url → list of (source_title, source_url)

    def _add_ref(target_url, source_url, source_title):
        if target_url not in index:
            index[target_url] = []
        if not any(s['url'] == source_url for s in index[target_url]):
            index[target_url].append({'title': source_title, 'url': source_url})

    def _scan_file(md_path, source_url):
        try:
            text = md_path.read_text(encoding='utf-8')
        except Exception:
            return
        for m in WIKI_LINK_RE.finditer(text):
            name = m.group(1).strip()
            disp = (m.group(2) or name).strip()
            # Look up in BACKLINK_MAP (case-insensitive)
            target = None
            for key, url in BACKLINK_MAP.items():
                if key.lower() == name.lower():
                    target = url
                    break
            if target:
                _add_ref(target, source_url, disp)

    # Scan DOCS_ROOT/*.md
    for md_file in DOCS_ROOT.glob("*.md"):
        if md_file.name.startswith("."):
            continue
        source_url = f"{SCRIPT_PREFIX}/{md_file.name.replace('.md', '.html')}"
        title = md_file.stem
        try:
            first = md_file.read_text(encoding='utf-8').split('\n')[0]
            tm = re.match(r'^#\s+(.+)$', first)
            if tm:
                title = tm.group(1).strip()[:60]
        except Exception:
            pass
        _scan_file(md_file, source_url)

    # Scan DOCS_ROOT/modules/*.md
    modules_dir = DOCS_ROOT / "modules"
    if modules_dir.exists():
        for md_file in sorted(modules_dir.glob("*.md")):
            source_url = f"{SCRIPT_PREFIX}/modules/{md_file.stem}.html"
            title = md_file.stem
            try:
                first = md_file.read_text(encoding='utf-8').split('\n')[0]
                tm = re.match(r'^#\s+(.+)$', first)
                if tm:
                    title = tm.group(1).strip()[:60]
            except Exception:
                pass
            _scan_file(md_file, source_url)

    # Scan SOP files
    sop_md = SOP_ROOT / "ROBOT-SOP.md"
    if sop_md.exists():
        source_url = f"{SCRIPT_PREFIX}/sop/full.html"
        _scan_file(sop_md, source_url)
        # Also scan individual chapter pages as sources
        for i in range(12):
            ch_url = f"{SCRIPT_PREFIX}/sop/chapter-{i}.html"
            for md_file in DOCS_ROOT.glob("*.md"):
                _scan_file(md_file, ch_url)

    # Scan report files
    reports_dir = SOP_ROOT / "night-build" / "reports"
    if reports_dir.exists():
        for md_file in sorted(reports_dir.glob("*.md")):
            source_url = f"{SCRIPT_PREFIX}/reports/{md_file.name}"
            title = md_file.stem
            try:
                first = md_file.read_text(encoding='utf-8').split('\n')[0]
                tm = re.match(r'^#\s+(.+)$', first)
                if tm:
                    title = tm.group(1).strip()[:60]
            except Exception:
                pass
            _scan_file(md_file, source_url)

    _BACKLINKS_INDEX = index
    return index

def render_backlinks(current_url):
    """Render the backlinks section for a given page URL."""
    index = build_backlinks_index()
    refs = index.get(current_url, [])
    if not refs:
        return ""
    items_html = ""
    for ref in refs[:20]:  # Limit to 20
        items_html += f'''
        <div class="backlink-item">
            <span class="backlink-icon">↩</span>
            <a href="{ref['url']}" class="backlink-link">{ref['title']}</a>
        </div>'''
    return f'''
<div class="backlinks-section">
    <div class="backlinks-title">🔗 被以下页面引用</div>
    {items_html}
</div>'''

def _preprocess_wiki_links(text):
    """Convert [[xxx]] and [[xxx|display]] to markdown links."""
    def _replace(m):
        name = m.group(1).strip()
        display = (m.group(2) or name).strip()
        # Find URL in BACKLINK_MAP
        for key, url in BACKLINK_MAP.items():
            if key.lower() == name.lower():
                return f'[{display}]({url})'
        # Unknown link — render as span with tooltip
        return f'<span class="wiki-link-unresolved" title="未找到页面: {name}">{display}</span>'
    return WIKI_LINK_RE.sub(_replace, text)

# ─── Markdown Renderer ────────────────────────────────────────────────────────

try:
    import markdown
    MD = markdown.Markdown(extensions=['tables', 'fenced_code', 'codehilite', 'toc'])
    def render_markdown(text):
        MD.reset()
        text = _preprocess_wiki_links(text)
        return MD.convert(text)
except ImportError:
    def render_markdown(text):
        text = _preprocess_wiki_links(text)
        return "<pre>" + text.replace("&","&amp;").replace("<","&lt;") + "</pre>"

# ─── Navigation ──────────────────────────────────────────────────────────────

NAV_CONFIG = [
    {"id": "home",     "label": "首页",       "icon": "🏠", "path": "/"},
    {"id": "sop",      "label": "实施指南",   "icon": "📖", "path": "/sop/",
     "children": [
        {"id": "sop-ch1", "label": "目录",            "path": "/sop/chapter-1.html"},
        {"id": "sop-ch2", "label": "第一章：概念与愿景", "path": "/sop/chapter-2.html",
         "subsections": [
             {"label": "1.1 项目愿景", "path": "/sop/chapter-2.html"},
             {"label": "1.2 核心系统：贵庚", "path": "/sop/chapter-2.html"},
             {"label": "1.3 核心陪伴理念", "path": "/sop/chapter-2.html"},
             {"label": "1.4 10年五阶段路线图", "path": "/sop/chapter-2.html"},
         ]},
        {"id": "sop-ch3", "label": "第二章：硬件体系",   "path": "/sop/chapter-3.html",
         "subsections": [
             {"label": "2.1 现有硬件", "path": "/sop/chapter-3.html"},
             {"label": "2.2 需要采购", "path": "/sop/chapter-3.html"},
             {"label": "2.3 电源方案", "path": "/sop/chapter-3.html"},
             {"label": "2.4 梯度采购路线图", "path": "/sop/chapter-3.html"},
             {"label": "2.5 星闪通信模块", "path": "/sop/chapter-3.html"},
             {"label": "2.6 Medusa Halo", "path": "/sop/chapter-3.html"},
             {"label": "2.7 手部与执行器设计", "path": "/sop/chapter-3.html"},
             {"label": "2.8 技术可行性", "path": "/sop/chapter-3.html"},
         ]},
        {"id": "sop-ch4", "label": "第三章：系统架构",   "path": "/sop/chapter-4.html",
         "subsections": [
             {"label": "3.1 整体架构", "path": "/sop/chapter-4.html"},
             {"label": "3.2 节点说明", "path": "/sop/chapter-4.html"},
             {"label": "3.3 通信协议", "path": "/sop/chapter-4.html"},
             {"label": "3.4 ROS 2 支持", "path": "/sop/chapter-4.html"},
         ]},
        {"id": "sop-ch5", "label": "第四章：实施阶段",   "path": "/sop/chapter-5.html",
         "subsections": [
             {"label": "Phase 0：Ubuntu对接", "path": "/sop/chapter-5.html"},
             {"label": "Phase 1：语音陪伴", "path": "/sop/chapter-5.html"},
             {"label": "Phase 2：视觉记录", "path": "/sop/chapter-5.html"},
             {"label": "Phase 3：iPhone感知", "path": "/sop/chapter-5.html"},
             {"label": "Phase 4：运动控制", "path": "/sop/chapter-5.html"},
             {"label": "Phase 5：面部表情", "path": "/sop/chapter-5.html"},
             {"label": "Phase 6：室内移动", "path": "/sop/chapter-5.html"},
         ]},
        {"id": "sop-ch6", "label": "第五章：AI 与感知",  "path": "/sop/chapter-6.html",
         "subsections": [
             {"label": "5.1 Jetson Nano 视觉感知", "path": "/sop/chapter-6.html"},
             {"label": "5.2 iPhone 感知前端", "path": "/sop/chapter-6.html"},
             {"label": "5.3 物理仿真引擎", "path": "/sop/chapter-6.html"},
             {"label": "5.4 具身大脑基模", "path": "/sop/chapter-6.html"},
             {"label": "5.5 机器人技能训练", "path": "/sop/chapter-6.html"},
         ]},
        {"id": "sop-ch7", "label": "第六章：本地 LLM 推理","path": "/sop/chapter-7.html",
         "subsections": [
             {"label": "6.1 推理框架对比", "path": "/sop/chapter-7.html"},
             {"label": "6.2 NemoClaw", "path": "/sop/chapter-7.html"},
             {"label": "6.3 AMD OpenClaw", "path": "/sop/chapter-7.html"},
             {"label": "6.4 各硬件能跑的模型", "path": "/sop/chapter-7.html"},
         ]},
        {"id": "sop-ch8", "label": "第七章：附录",        "path": "/sop/chapter-8.html",
         "subsections": [
             {"label": "A.1 关键开源项目", "path": "/sop/chapter-8.html"},
             {"label": "A.2 语音交互模块", "path": "/sop/chapter-8.html"},
             {"label": "A.3 ESP32-Cam 有线通信", "path": "/sop/chapter-8.html"},
             {"label": "A.4 拓竹软件生态", "path": "/sop/chapter-8.html"},
         ]},
        {"id": "sop-ch9", "label": "第八章：安全与维护",  "path": "/sop/chapter-9.html",
         "subsections": [
             {"label": "8.1 声纹识别", "path": "/sop/chapter-9.html"},
             {"label": "8.2 异常检测", "path": "/sop/chapter-9.html"},
             {"label": "8.3 数据自毁", "path": "/sop/chapter-9.html"},
             {"label": "8.4 日常维护", "path": "/sop/chapter-9.html"},
             {"label": "8.5 常见问题排查", "path": "/sop/chapter-9.html"},
         ]},
        {"id": "sop-ch10", "label": "第九章：风险与合规",  "path": "/sop/chapter-10.html",
         "subsections": [
             {"label": "9.1 技术风险", "path": "/sop/chapter-10.html"},
             {"label": "9.2 法规风险", "path": "/sop/chapter-10.html"},
         ]},
        {"id": "sop-ch11", "label": "第十章·术语表",     "path": "/sop/chapter-11.html"},
        {"id": "sop-full", "label": "完整 SOP",          "path": "/sop/full.html"},
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
    {"id": "techref",  "label": "技术参考",   "icon": "📚", "path": "/techref/",
     "children": [
        {"id": "tr-browser", "label": "Browser Relay",   "path": "/techref/browser-relay.html"},
        {"id": "tr-openclaw", "label": "OpenClaw 更新",   "path": "/techref/openclaw-updates.html"},
        {"id": "tr-hardware", "label": "硬件参考",        "path": "/techref/hardware.html"},
        {"id": "tr-research", "label": "调研资料",        "path": "/techref/research.html"},
        {"id": "tr-misc",     "label": "其他文档",        "path": "/techref/misc.html"},
     ]},
    {"id": "refs",     "label": "参考链接",   "icon": "🔗", "path": "/refs/",
     "children": [
        {"id": "ref-dashboard", "label": "Dashboard",    "path": "/refs/dashboard/"},
        {"id": "ref-world",     "label": "World View",  "path": "/refs/world/"},
        {"id": "ref-openclaw",  "label": "OpenClaw 官方文档", "external": "https://docs.openclaw.ai"},
     ]},
    {"id": "board",    "label": "任务看板",   "icon": "📋", "path": "/board/"},
]

# ─── Template ────────────────────────────────────────────────────────────────

# ─── Search Index ───────────────────────────────────────────────────────────

def _build_search_index():
    """Build search index from all Markdown files (used by Fuse.js).

    Optimization: Only index titles (no body text) to keep the embedded
    JSON index small (~45 KB vs ~288 KB). The Python /api/search endpoint
    still does full-text search via search_docs().
    """
    index = []
    docs_dir = DOCS_ROOT

    for md_file in docs_dir.glob("*.md"):
        if md_file.name.startswith("."):
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
            title_m = re.match(r'^#\s+(.+)$', text)
            title = title_m.group(1).strip() if title_m else md_file.stem
            index.append({
                "title": title,
                "url": f"{SCRIPT_PREFIX}/{md_file.name.replace('.md', '.html')}"
            })
        except Exception:
            pass

    # Also index SOP content (by heading sections)
    sop_file = SOP_ROOT / "ROBOT-SOP.md"
    if sop_file.exists():
        try:
            text = sop_file.read_text(encoding="utf-8")
            for ch_match in re.finditer(r'^#+\s+(.+)$', text, re.MULTILINE):
                title = ch_match.group(1).strip()[:80]
                index.append({
                    "title": f"SOP: {title}",
                    "url": f"{SCRIPT_PREFIX}/sop/full.html"
                })
        except Exception:
            pass

    # Also index module docs
    modules_dir = DOCS_ROOT.parent / "docs" / "modules"
    if modules_dir.exists():
        for md_file in sorted(modules_dir.glob("*.md")):
            try:
                text = md_file.read_text(encoding="utf-8")
                title_m = re.match(r'^#\s+(.+)$', text)
                title = title_m.group(1).strip() if title_m else md_file.stem
                index.append({
                    "title": f"[模块] {title}",
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
                index.append({
                    "title": f"[报告] {title}",
                    "url": f"{SCRIPT_PREFIX}/reports/{md_file.name}"
                })
            except Exception:
                pass

    return index

# ─── Search Index ───────────────────────────────────────────────────────────

def make_page(active_id, title, content, extra_css="", backlinks=""):
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
:root[data-theme="light"]{{
  --bg:#ffffff;--surface:#f8f9fa;--surface2:#e9ecef;--border:#dee2e6;
  --text:#212529;--text2:#6c757d;--accent:#e85d04;--accent2:#1971c2;
  --green:#2f9e44;--yellow:#f08f00;--red:#e03131;--purple:#7048e8;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
html{{overflow-x:hidden;overflow-y:auto;height:100%;scrollbar-width:none}}
html::-webkit-scrollbar{{display:none}}
body{{background:var(--bg);color:var(--text);font-family:'DM Sans',system-ui,sans-serif;min-height:100vh;scrollbar-width:none}}
body::-webkit-scrollbar{{display:none}}
a{{color:var(--accent2);text-decoration:none}}
a:hover{{text-decoration:underline}}
blockquote{{border-left:3px solid var(--accent);padding:8px 16px;background:var(--surface2);margin:12px 0;border-radius:0 6px 6px 0;color:var(--text2)}}
code,pre{{font-family:'Fragment Mono','Courier New',monospace}}
pre{{background:var(--surface);border:1px solid var(--border);padding:16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6}}
code{{background:var(--surface2);padding:2px 6px;border-radius:4px;font-size:0.9em;color:var(--accent2)}}
table{{width:100%;border-collapse:collapse;margin:12px 0}}
th{{background:var(--surface2);padding:10px 14px;text-align:left;border-bottom:2px solid var(--border);font-weight:600}}
td{{padding:8px 14px;border-bottom:1px solid var(--border)}}
tr:hover{{background:var(--surface2)}}
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
.header{{position:fixed;top:0;left:0;right:0;height:var(--header-h);background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 20px;z-index:100; backdrop-filter:blur(10px)}}
.header-logo{{font-size:18px;font-weight:700;color:var(--accent);white-space:nowrap}}
.header-version{{margin-left:auto;font-size:12px;color:var(--text2);background:var(--surface2);padding:4px 10px;border-radius:12px;border:1px solid var(--border)}}
.sidebar{{position:fixed;top:var(--header-h);left:0;bottom:0;width:var(--sidebar-w);background:var(--surface);border-right:1px solid var(--border);overflow-y:auto;padding:12px 0;scrollbar-width:none}}
.sidebar::-webkit-scrollbar{{display:none}}
.sidebar-section{{padding:6px 0}}
.sidebar-section-title{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--text2);padding:8px 16px 4px;display:flex;align-items:center;gap:6px}}
.sidebar-link{{display:block;padding:6px 16px;font-size:13px;color:var(--text);transition:all .15s;border-left:2px solid transparent}}
.sidebar-link:hover,.sidebar-link.active{{color:var(--accent);border-left-color:var(--accent);background:rgba(255,107,53,.06);text-decoration:none}}
.sidebar-link.sub{{padding-left:28px;font-size:12px}}
.sidebar-children{{margin-left:16px;border-left:1px solid var(--border)}}
.sidebar-toggle{{margin-left:auto;font-size:10px;color:var(--text2);transition:transform .2s}}
.sidebar-section.collapsed .sidebar-children{{display:none}}
.sidebar-section.collapsed .sidebar-toggle{{transform:rotate(-90deg)}}
.sidebar-chapter{{margin:0}}
.sidebar-subsections{{display:none;padding:2px 0 2px 8px}}
.sidebar-arrow{{font-size:9px;color:var(--text2);margin-left:4px;transition:transform .15s;display:inline-block}}
.sidebar-link.sub-sub{{padding-left:44px;font-size:11px;color:var(--text2);opacity:.8}}
.sidebar-link.sub-sub:hover{{color:var(--accent);opacity:1}}
.main{{margin-left:var(--sidebar-w);margin-top:var(--header-h);padding:32px 40px;max-width:900px}}
.content-header{{margin-bottom:24px}}
.content-header h1{{font-size:2em;color:var(--accent);margin-bottom:8px}}
.content-meta{{font-size:13px;color:var(--text2)}}
.search-box{{margin-left:24px;position:relative}}
.search-box input{{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:8px;font-size:13px;width:200px;transition:all .2s}}
.search-box input:focus{{outline:none;border-color:var(--accent);width:260px}}
.search-results{{position:absolute;top:100%;right:0;left:0;background:var(--surface);border:1px solid var(--border);border-radius:8px;margin-top:4px;max-height:400px;overflow-y:auto;display:none;z-index:200;box-shadow:0 8px 32px rgba(0,0,0,.4);scrollbar-width:none}}
.search-results::-webkit-scrollbar{{display:none}}
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
/* ── Backlinks ─────────────────────────────────────────────────── */
.backlinks-section{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin-top:40px}}
.backlinks-title{{font-size:14px;font-weight:600;color:var(--accent2);margin-bottom:12px;display:flex;align-items:center;gap:6px}}
.backlink-item{{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--border);font-size:13px}}
.backlink-item:last-child{{border-bottom:none}}
.backlink-icon{{color:var(--accent2);font-size:12px}}
.backlink-link{{color:var(--text);transition:color .15s}}
.backlink-link:hover{{color:var(--accent);text-decoration:none}}
.wiki-link-unresolved{{color:var(--yellow);border-bottom:1px dashed var(--yellow);cursor:help}}
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
  <button id="themeToggle" onclick="toggleTheme()" style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:6px 12px;cursor:pointer;font-size:12px;margin-left:16px;color:var(--text)">🌙</button>
  <button id="scrollBottomBtn" onclick="scrollToBottom()" title="滑到底部" style="position:fixed;bottom:24px;right:24px;width:40px;height:40px;background:var(--accent);color:#fff;border:none;border-radius:50%;cursor:pointer;font-size:18px;z-index:999;box-shadow:0 4px 12px rgba(0,0,0,.3);display:none;align-items:center;justify-content:center">↓</button>
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
{backlinks}
</main>
<script>
// Sidebar chapter accordion
function toggleChapter(link) {{
  const chapter = link.closest('.sidebar-chapter');
  const subs = chapter.querySelector('.sidebar-subsections');
  const arrow = link.querySelector('.sidebar-arrow');
  const isOpen = subs.style.display !== 'none';
  // Close all other chapters first
  document.querySelectorAll('.sidebar-chapter').forEach(ch => {{
    if (ch !== chapter) {{
      ch.querySelector('.sidebar-subsections').style.display = 'none';
      ch.querySelector('.sidebar-arrow').textContent = '▸';
    }}
  }});
  // Toggle current
  subs.style.display = isOpen ? 'none' : 'block';
  arrow.textContent = isOpen ? '▸' : '▾';
}}
// Build search index from localStorage
// Fuse.js search
const searchIndex = {search_index_json};
const fuse = new Fuse(searchIndex, {{
  keys: ['title'],
  threshold: 0.3,
  includeScore: true,
  minMatchCharLength: 1
}});
function handleSearch(q) {{
  const results = document.getElementById('searchResults');
  if (!q.trim()) {{ results.classList.remove('show'); return; }}
  const found = fuse.search(q, {{ limit: 8 }});
  if (!found.length) {{ results.innerHTML='<div class="search-result-item">无结果</div>'; results.classList.add('show'); return; }}
  results.innerHTML = found.map(r =>
    `<div class="search-result-item" onclick="location.href='${{r.item.url}}'">
      <div>${{r.item.title}}</div>
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
{{Prism.highlightAll();}}
// Theme toggle
const THEMES = {{ dark: '🌙', light: '☀️' }};
function toggleTheme() {{
    const root = document.documentElement;
    const current = root.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    document.getElementById('themeToggle').textContent = THEMES[next];
    localStorage.setItem('theme', next);
}}
function scrollToBottom() {{
    window.scrollTo({{top: document.body.scrollHeight, behavior: 'smooth'}});
}}
function updateScrollBtn() {{
    const btn = document.getElementById('scrollBottomBtn');
    if (!btn) return;
    const nearBottom = window.innerHeight + window.scrollY >= document.body.offsetHeight - 200;
    btn.style.display = nearBottom ? 'none' : 'flex';
}}
window.addEventListener('scroll', updateScrollBtn);
(function() {{
    const saved = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    document.getElementById('themeToggle').textContent = THEMES[saved] || '🌙';
}})();
</script>
</body>
</html>"""

def build_nav_html(config, active_id, depth=0):
    html = ""
    for item in config:
        if item.get("children"):
            html += f'<div class="sidebar-section"><div class="sidebar-section-title" onclick="this.parentElement.classList.toggle(\'collapsed\')">{item.get("icon","")} {item["label"]} <span class="sidebar-toggle">▾</span></div>'
            html += '<div class="sidebar-children">'
            for child in item["children"]:
                # Check if this child has subsections (collapsible)
                if child.get("subsections"):
                    child_active = "active" if child.get("id") == active_id else ""
                    href = SCRIPT_PREFIX + child["path"] if not child["path"].startswith(SCRIPT_PREFIX) and not child["path"].startswith("http") else child["path"]
                    html += f'<div class="sidebar-chapter" data-chapter="{child.get("id","")}">'
                    html += f'<a class="sidebar-link sub {child_active}" href="{href}" onclick="event.preventDefault();toggleChapter(this)">{child["label"]} <span class="sidebar-arrow">▸</span></a>'
                    html += '<div class="sidebar-subsections">'
                    for sub in child["subsections"]:
                        sub_href = SCRIPT_PREFIX + sub.get("path", child["path"]) if not sub.get("path","").startswith("http") else sub.get("path","")
                        html += f'<a class="sidebar-link sub-sub" href="{sub_href}">{sub["label"]}</a>'
                    html += '</div></div>'
                else:
                    cls = "sidebar-link sub" if depth >= 1 else "sidebar-link"
                    active = "active" if child.get("id") == active_id else ""
                    href = child.get("path","#")
                    target = ' target="_blank"' if child.get("external") else ""
                    if not child.get("external") and not href.startswith("http"):
                        href = SCRIPT_PREFIX + href if not href.startswith(SCRIPT_PREFIX) else href
                    html += f'<a class="{cls} {active}" href="{href}"{target}>{child["label"]}</a>'
            html += '</div></div>'
        else:
            active = "active" if item.get("id") == active_id else ""
            href = item.get("path","#")
            target = ' target="_blank"' if item.get("external") else ""
            if not item.get("external") and not href.startswith("http"):
                href = SCRIPT_PREFIX + href if not href.startswith(SCRIPT_PREFIX) else href
            html += f'<div class="sidebar-section"><a class="sidebar-link {active}" href="{href}"{target}>{item.get("icon","")} {item["label"]}</a></div>'
    return html

def load_versions():
    if VERSIONS_FILE.exists():
        try:
            return json.loads(VERSIONS_FILE.read_text())
        except:
            pass
    return {}

def bump_module_version(slug, change_type, description):
    """更新模块版本号（需要重启 docs-server）"""
    versions = load_versions()
    if slug not in versions:
        versions[slug] = {"version": "v0.0.1", "changes": []}
    ver = versions[slug]["version"]
    major, minor, patch = map(int, ver.lstrip("v").split("."))
    if change_type == "major": major += 1; minor = patch = 0
    elif change_type == "minor": minor += 1; patch = 0
    else: patch += 1
    new_ver = f"v{major}.{minor}.{patch}"
    versions[slug]["version"] = new_ver
    versions[slug]["changes"].insert(0, {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": change_type,
        "detail": description
    })
    VERSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSIONS_FILE.write_text(json.dumps(versions, ensure_ascii=False, indent=2))
    return new_ver

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
        if line.startswith('# ') and not re.match(r'^# \d+\.', line):
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

# ─── Task Board Loader ───────────────────────────────────────────────────────

def load_tasks():
    """Load tasks from night-build/tasks/ directory.
    Status detection:
    - done: output directory exists for the task
    - in-progress: task file contains 'running' or 'processing' in content
    - pending: otherwise
    Returns: list of task dicts with id, group, type, status, title
    """
    tasks_dir = SOP_ROOT / "night-build" / "tasks"
    output_base = SOP_ROOT / "night-build" / "output"
    tasks = []

    # Known task sequences
    seq_config = {
        "A": {"label": "A序列", "priority": "high", "color": "#ff4757"},
        "B": {"label": "B序列", "priority": "high", "color": "#ffa502"},
        "F": {"label": "F序列", "priority": "medium", "color": "#70a1ff"},
        "R": {"label": "R序列", "priority": "low", "color": "#a29bfe"},
        "H": {"label": "H序列", "priority": "medium", "color": "#2ed573"},
        "E": {"label": "E序列", "priority": "low", "color": "#5352ed"},
    }

    if not tasks_dir.exists():
        return [], seq_config

    for f in sorted(tasks_dir.glob("T-*.md")):
        if f.name == "README.md":
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        # Parse JSON header
        status = "pending"
        task_id = f.stem
        group = "?"
        task_type = "unknown"

        # Extract JSON block at top
        json_m = re.match(r'^#.*?\n(\{.*?\n\})', content, re.DOTALL)
        if json_m:
            try:
                meta = json.loads(json_m.group(1))
                task_id = meta.get("id", f.stem)
                group_raw = meta.get("group", "?")
                # Handle group like "A", "B", or "AR" (A sequence research)
                group = group_raw.strip()
                task_type = meta.get("type", "unknown")
            except Exception:
                pass

        # Also try to detect group from filename: T-01-A01 → A, T-01-B01 → B
        fname_m = re.match(r'T-\d+-([A-Z]+)\d+', f.stem)
        if fname_m and group == "?":
            group = fname_m.group(1)

        # Detect status: check output directory
        output_dir = output_base / "2026-03-26" / f.stem
        if not output_dir.exists():
            output_dir = output_base / "2026-03-27" / f.stem
        if not output_dir.exists():
            # Check any date subdir
            for date_dir in sorted(output_base.glob("*")):
                if date_dir.is_dir():
                    check = date_dir / f.stem
                    if check.exists():
                        output_dir = check
                        break

        if output_dir.exists() and output_dir.is_dir():
            status = "done"
        elif "running" in content[:200].lower() or "processing" in content[:200].lower():
            status = "in-progress"

        # Extract title from first heading or prompt
        title = task_id
        prompt_m = re.search(r'^##?\s+Prompt.*?\n(.*)', content, re.MULTILINE)
        if prompt_m:
            first_line = prompt_m.group(1).strip()[:60]
            if first_line:
                title = first_line[:50] + ("..." if len(first_line) > 50 else "")

        seq_info = seq_config.get(group, {"label": f"{group}序列", "priority": "low", "color": "#888"})

        tasks.append({
            "id": task_id,
            "group": group,
            "group_label": seq_info["label"],
            "priority": seq_info["priority"],
            "color": seq_info["color"],
            "type": task_type,
            "status": status,
            "title": title,
            "filename": f.name,
        })

    return tasks, seq_config

def make_board():
    """Task Board page — three-column kanban: pending | in-progress | done"""
    tasks, seq_config = load_tasks()

    # Compute stats
    total = len(tasks)
    done = len([t for t in tasks if t["status"] == "done"])
    in_progress = len([t for t in tasks if t["status"] == "in-progress"])
    pending = len([t for t in tasks if t["status"] == "pending"])
    rate = f"{done/total*100:.0f}%" if total > 0 else "—"

    # Group by sequence
    seq_stats_html = ""
    for seq_key, info in seq_config.items():
        seq_tasks = [t for t in tasks if t["group"] == seq_key]
        if seq_tasks:
            seq_done = len([t for t in seq_tasks if t["status"] == "done"])
            seq_total = len(seq_tasks)
            seq_rate = f"{seq_done/seq_total*100:.0f}%" if seq_total > 0 else "—"
            seq_stats_html += f"""
            <div class="board-stat-chip" style="--chip-color:{info['color']}">
                <span class="board-stat-chip-label">{info['label']}</span>
                <span class="board-stat-chip-val">{seq_done}/{seq_total}</span>
            </div>"""

    # Build columns
    columns = {
        "pending": {"label": "📋 待办", "tasks": [], "class": "board-col-pending"},
        "in-progress": {"label": "🔄 进行中", "tasks": [], "class": "board-col-progress"},
        "done": {"label": "✅ 已完成", "tasks": [], "class": "board-col-done"},
    }

    for t in tasks:
        status = t["status"]
        priority_cls = {
            "high": "priority-high",
            "medium": "priority-medium",
            "low": "priority-low",
        }.get(t["priority"], "priority-low")

        card = f"""
        <div class="task-card">
            <div class="task-card-header">
                <span class="task-card-id" style="color:{t['color']}">{t['id']}</span>
                <span class="task-card-seq" style="background:{t['color']}22;color:{t['color']};border:1px solid {t['color']}44">{t['group_label']}</span>
            </div>
            <div class="task-card-title">{t['title']}</div>
            <div class="task-card-footer">
                <span class="task-card-type">{t['type']}</span>
            </div>
        </div>"""
        columns[status]["tasks"].append(card)

    col_html = {}
    for col_id, col in columns.items():
        inner = "".join(col["tasks"]) if col["tasks"] else '<div class="board-empty">暂无任务</div>'
        col_html[col_id] = f"""
        <div class="board-column {col['class']}">
            <div class="board-col-header" onclick="toggleBoardCol(this)">
                <span>{col['label']}</span>
                <span class="board-col-count">{len(col['tasks'])}</span>
                <span class="board-col-toggle">▾</span>
            </div>
            <div class="board-col-body">
                {inner}
            </div>
        </div>"""

    return make_page("board", "任务看板", f"""
<style>
.board-stats{{display:flex;align-items:center;gap:12px;margin-bottom:24px;flex-wrap:wrap}}
.board-total{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center}}
.board-total-num{{font-size:28px;font-weight:700;color:var(--accent)}}
.board-total-label{{font-size:12px;color:var(--text2);margin-top:2px}}
.board-stat-chip{{display:flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 16px}}
.board-stat-chip-label{{font-size:12px;font-weight:600}}
.board-stat-chip-val{{font-size:13px;color:var(--text2)}}
.board-rate{{margin-left:auto;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center;}}
.board-rate-num{{font-size:28px;font-weight:700;color:var(--green)}}
.board-rate-label{{font-size:12px;color:var(--text2);margin-top:2px}}
.board-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;align-items:start}}
.board-column{{background:var(--surface);border:1px solid var(--border);border-radius:12px;overflow:hidden}}
.board-col-pending{{border-color:var(--yellow)44;}}
.board-col-progress{{border-color:var(--accent2)44;}}
.board-col-done{{border-color:var(--green)44;}}
.board-col-header{{display:flex;align-items:center;gap:8px;padding:12px 16px;font-weight:600;font-size:14px;cursor:pointer;user-select:none;background:var(--surface2)}}
.board-col-count{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:1px 8px;font-size:12px;color:var(--text2)}}
.board-col-toggle{{margin-left:auto;font-size:10px;color:var(--text2);transition:transform .2s}}
.board-col-toggle.collapsed{{transform:rotate(-90deg);}}
.board-col-body{{padding:12px;display:flex;flex-direction:column;gap:10px;max-height:600px;overflow-y:auto;scrollbar-width:none}}
.board-col-body::-webkit-scrollbar{{display:none}}
.board-col-body.collapsed{{display:none;}}
.task-card{{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:12px;transition:all .15s}}
.task-card:hover{{border-color:var(--accent);transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,.2)}}
.task-card-header{{display:flex;align-items:center;gap:8px;margin-bottom:8px}}
.task-card-id{{font-size:12px;font-weight:700;font-family:monospace}}
.task-card-seq{{font-size:10px;font-weight:600;padding:2px 6px;border-radius:6px}}
.task-card-title{{font-size:13px;line-height:1.4;margin-bottom:8px;color:var(--text)}}
.task-card-footer{{display:flex;align-items:center;gap:6px}}
.task-card-type{{font-size:11px;color:var(--text2);background:var(--surface2);padding:2px 6px;border-radius:4px}}
.board-empty{{text-align:center;padding:24px;color:var(--text2);font-size:13px}}
@media(max-width:800px){{.board-grid{{grid-template-columns:1fr;}}}}
</style>

<div class="content-header">
  <h1>📋 任务看板</h1>
  <div class="content-meta">Night Build 任务池 · 实时状态</div>
</div>

<!-- Stats row -->
<div class="board-stats">
    <div class="board-total">
        <div class="board-total-num">{total}</div>
        <div class="board-total-label">总任务数</div>
    </div>
    {seq_stats_html}
    <div class="board-rate">
        <div class="board-rate-num">{rate}</div>
        <div class="board-rate-label">完成率</div>
    </div>
</div>

<!-- Kanban board -->
<div class="board-grid">
    {col_html['pending']}
    {col_html['in-progress']}
    {col_html['done']}
</div>

<script>
function toggleBoardCol(header) {{
    var body = header.nextElementSibling;
    var toggle = header.querySelector('.board-col-toggle');
    body.classList.toggle('collapsed');
    toggle.classList.toggle('collapsed');
}}
</script>
""")

def load_reports():
    """Load research reports"""
    reports_dir = SOP_ROOT / "night-build" / "reports"
    reports = []
    if reports_dir.exists():
        # Load status file
        statuses = {}
        if REPORTS_STATUS.exists():
            statuses = json.loads(REPORTS_STATUS.read_text())
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
            # Extract status from status.json if present, otherwise from content
            if f.name in statuses:
                status = statuses[f.name]["status"]
            elif "✅" in content[:200] or "已解决" in content[:200] or "已完成" in content[:200]:
                status = "approved"
            else:
                status = "pending"
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
                'url': f'{SCRIPT_PREFIX}/reports/{f.name}'
            })
    return reports

# ─── Content Generators ─────────────────────────────────────────────────────

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

def make_sop_chapter(chapter_num, active_id):
    """Render a SOP chapter — 显示完整章节内容，无截断"""
    chapters = load_sop_content()
    # 按文件出现顺序排序章节标题（跳过非章节标题）
    chapter_order = [
        "🤖 0-1 私人 AI 机器人完整实施指南",
        "目录",
        "第一章：概念与愿景",
        "第二章：硬件体系",
        "第三章：系统架构",
        "第四章：实施阶段",
        "第五章：AI 与感知",
        "第六章：本地 LLM 推理",
        "第七章：附录",
        "第八章：安全与维护",
        "第九章：风险与合规",
        "术语表（Glossary）",
    ]
    # 尝试用列表中的标题匹配，也尝试匹配已解析的章节 key
    ch_key = chapter_order[chapter_num] if chapter_num < len(chapter_order) else ""
    ch = chapters.get(ch_key, {})
    # 如果精确匹配失败，用模糊匹配（章节号）
    if not ch:
        import re as _re
        pat = _re.compile(r'第([一二三四五六七八九十\d]+)章')
        for k, v in chapters.items():
            m = pat.search(k)
            if m:
                cn = m.group(1)
                num_map = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
                if num_map.get(cn, int(cn) if cn.isdigit() else -1) == chapter_num:
                    ch = v
                    ch_key = k
                    break
    # chapter_num=0 对应前言/目录
    if chapter_num == 0 and not ch:
        # 取前两个 H1 合并（标题+目录）
        keys = list(chapters.keys())
        if len(keys) >= 2:
            ch = dict(chapters[keys[0]])
            ch['content'] = chapters[keys[0]].get('content','') + '\n' + chapters[keys[1]].get('content','')
            ch['subsections'] = chapters[keys[0]].get('subsections',[]) + chapters[keys[1]].get('subsections',[])
            ch['title'] = "前言与目录"

    if not ch:
        avail = ''.join(f'<li><a href="{SCRIPT_PREFIX}/sop/chapter-{i}.html">{chapter_order[i] if i < len(chapter_order) else "?"}</a></li>' for i in range(len(chapter_order)))
        return make_page(active_id, f"第{chapter_num}章", f"<p>章节未找到。可用章节：</p><ul>{avail}</ul>")

    # ── Chapter 1 (目录): render as card layout instead of table ──
    if chapter_num == 1:
        # Build card-based TOC from all chapters
        card_chapters = [
            ("第一章：概念与愿景", 2, ["1.1 项目愿景","1.2 核心系统：贵庚","1.3 核心陪伴理念：从「响应」到「懂你」","1.4 10年五阶段路线图"]),
            ("第二章：硬件体系", 3, ["2.1 现有硬件","2.2 需要采购（阶段一 MVP）","2.3 电源方案","2.4 梯度采购路线图","2.5 星闪通信模块：BearPi-Pico H3863","2.6 Medusa Halo：移动 AI 工作站","2.7 手部与执行器设计","2.8 技术可行性：五条技术路线"]),
            ("第三章：系统架构", 4, ["3.1 整体架构","3.2 节点说明","3.3 通信协议","3.4 ROS 2 支持情况与替代框架"]),
            ("第四章：实施阶段", 5, ["Phase 0：Ubuntu 台式机对接 Gateway","Phase 1：语音陪伴模块","Phase 2：视觉记录模块","Phase 3：iPhone 感知前端","Phase 4：运动控制模块","Phase 5：面部表情系统","Phase 6：室内移动与智能家居硬件拓展"]),
            ("第五章：AI 与感知", 6, ["5.1 Jetson Nano 视觉感知","5.2 iPhone 感知前端技术方案","5.3 物理仿真引擎：Genesis 与 Newton","5.4 具身大脑基模：RynnBrain 与空间智能","5.5 机器人技能训练：从模仿学习到自主泛化"]),
            ("第六章：本地 LLM 推理", 7, ["6.1 推理框架对比","6.2 NemoClaw — NVIDIA 官方 OpenClaw 优化","6.3 AMD 官方 OpenClaw 方案","6.4 各硬件能跑的模型"]),
            ("第七章：附录", 8, ["A.1 关键开源项目参考","A.2 语音交互模块","A.3 ESP32-Cam 有线通信","A.4 拓竹软件生态"]),
            ("第八章：安全与维护", 9, ["8.1 声纹识别","8.2 异常检测","8.3 数据自毁","8.4 日常维护","8.5 常见问题排查"]),
            ("第九章：风险与合规", 10, ["9.1 技术风险","9.2 法规风险"]),
            ("第十章·术语表", 11, ["术语表"]),
        ]
        toc_css = """.toc-card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;margin-top:20px}
.toc-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 20px;transition:border-color .2s,box-shadow .2s;cursor:pointer}
.toc-card:hover{border-color:var(--accent);box-shadow:0 4px 20px rgba(255,107,53,.1)}
.toc-card-title{font-size:15px;font-weight:700;color:var(--accent);margin-bottom:10px}
.toc-card-subs{list-style:none;padding:0;margin:0}
.toc-card-subs li{padding:5px 0;font-size:12px;color:var(--text2);border-bottom:1px solid rgba(42,42,58,.5);display:flex;align-items:center;gap:6px}
.toc-card-subs li:last-child{border-bottom:none}
.toc-card-subs li::before{content:"›";color:var(--accent);font-weight:700;font-size:13px;flex-shrink:0}
.toc-card-subs a{color:var(--text2);text-decoration:none}
.toc-card-subs a:hover{color:var(--accent)}"""
        cards_html = ""
        for title, ch_pg, subs in card_chapters:
            subs_li = "".join(f'<li><a href="{SCRIPT_PREFIX}/sop/chapter-{ch_pg}.html">{s}</a></li>' for s in subs)
            cards_html += f"""<div class="toc-card" onclick="location.href='{SCRIPT_PREFIX}/sop/chapter-{ch_pg}.html'">
  <div class="toc-card-title">{title}</div>
  {f'<ul class="toc-card-subs">{subs_li}</ul>' if subs else ''}
</div>"""
        sop_file = SOP_ROOT / "ROBOT-SOP.md"
        export_buttons = ""
        if sop_file.exists():
            export_buttons = f"""<div style="margin:16px 0;display:flex;gap:8px;flex-wrap:wrap">
  <a href="{SCRIPT_PREFIX}/raw/ROBOT-SOP.md" class="btn btn-outline" style="font-size:12px" target="_blank">📄 导出 Markdown 源文件</a>
  <a href="{SCRIPT_PREFIX}/api/export/sop-pdf" class="btn btn-primary" style="font-size:12px">📑 导出 PDF 版</a>
</div>"""
        return make_page(active_id, "目录", f"""
<div class="content-header">
  <h1>📖 0-1 实施指南 · 目录</h1>
  <div class="content-meta">共 {len(card_chapters)} 个章节</div>
</div>
{export_buttons}
<div class="toc-card-grid">{cards_html}</div>
""", extra_css=f"<style>{toc_css}</style>")

    # Extract TOC from full chapter content
    toc = extract_toc(ch['content'])
    toc_html = render_toc(toc) if toc else ""

    # Render ALL subsections without any truncation
    subsections_html = ""
    for sub in ch.get('subsections', []):
        anchor = sub['title'].lower().replace(' ', '-').replace('.', '').replace(':', '')
        anchor = re.sub(r'[^\w\-]', '', anchor)
        subsections_html += f'<h2 id="{anchor}">{sub["title"]}</h2>\n'
        subsections_html += render_markdown(sub['content']) + '\n'

    sop_file = SOP_ROOT / "ROBOT-SOP.md"
    export_buttons = ""
    if sop_file.exists():
        export_buttons = f"""
<div style="margin:16px 0;display:flex;gap:8px;flex-wrap:wrap">
  <a href="{SCRIPT_PREFIX}/raw/ROBOT-SOP.md" class="btn btn-outline" style="font-size:12px" target="_blank">📄 导出 Markdown 源文件</a>
  <a href="{SCRIPT_PREFIX}/api/export/sop-pdf" class="btn btn-primary" style="font-size:12px">📑 导出 PDF 版</a>
</div>"""

    return make_page(active_id, ch.get('title', f"第{chapter_num}章"), f"""
{toc_html}
<div class="content-header">
  <h1>{ch.get('title', f'第{chapter_num}章')}</h1>
  <div class="content-meta">0-1 实施指南 · 章节 {chapter_num} · 共 {len(ch.get('subsections',[]))} 节</div>
</div>
{export_buttons}
{subsections_html}
<div style="margin-top:32px;padding-top:16px;border-top:1px solid var(--border)">
  <a href="{SCRIPT_PREFIX}/sop/" class="btn btn-outline">← 实施指南目录</a>
</div>
""")

def make_sop_full():
    """Full SOP as single page — 完整内容，无截断"""
    chapters = load_sop_content()
    if not chapters:
        return make_page("sop-full", "完整 SOP", "<p>SOP 文件未找到。</p>")

    sections_html = ""
    for ch_name, ch in chapters.items():
        sections_html += f'<h1 id="{ch_name[:20]}">{ch.get("title","")}</h1>\n'
        # 渲染完整 HTML，无截断
        sections_html += ch.get('html', '') + '\n\n'

    sop_file = SOP_ROOT / "ROBOT-SOP.md"
    export_buttons = ""
    if sop_file.exists():
        export_buttons = f"""
<div class="content-header" style="margin-bottom:24px">
  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
    <h1 style="margin:0;border:none">📖 0-1 完整实施指南</h1>
    <span class="badge badge-c">{len(chapters)} 个章节</span>
  </div>
</div>
<div style="margin:16px 0;display:flex;gap:8px;flex-wrap:wrap">
  <a href="{SCRIPT_PREFIX}/raw/ROBOT-SOP.md" class="btn btn-outline" style="font-size:13px" target="_blank">📄 导出 Markdown 源文件</a>
  <a href="{SCRIPT_PREFIX}/api/export/sop-pdf" class="btn btn-primary" style="font-size:13px">📑 导出 PDF 版</a>
</div>"""

    return make_page("sop-full", "完整 SOP", f"""
{export_buttons}
<div class="alert alert-info" style="margin-bottom:24px">
  本页面显示完整 SOP 内容。按 <kbd>Ctrl+F</kbd> 搜索关键词。
</div>
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
  <a href="{SCRIPT_PREFIX}/reports/approved.html" class="btn btn-outline {'btn-primary' if status_filter=='approved' else ''}">✅ 已发布</a>
  <a href="{SCRIPT_PREFIX}/reports/pending.html" class="btn btn-outline {'btn-primary' if status_filter=='pending' else ''}">⏳ 待审批</a>
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
    # Load review status
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
        reviewer_note_html = f'<div style="margin-top:8px;font-size:13px;color:var(--text2)">备注：{current.get("reviewer_note", "无")}</div>' if current.get('reviewer_note') else ''
        review_ui = f"""
    <div style="margin-top:24px;padding:16px;background:var(--surface);border:1px solid var(--border);border-radius:12px">
      <div style="display:flex;align-items:center;gap:8px">
        <span style="font-size:18px">{'✅' if current_status == 'approved' else '❌'}</span>
        <span style="font-weight:600">{'已采纳' if current_status == 'approved' else '已拒绝'}</span>
        <span style="color:var(--text2);font-size:12px">{current.get('reviewed_at', '')}</span>
      </div>
      {reviewer_note_html}
    </div>"""
    return make_page("reports", title, f"""
<div class="content-header">
  <h1>{title}</h1>
  <div class="content-meta">{filename}</div>
</div>
<div style="margin-bottom:16px">
  <a href="{SCRIPT_PREFIX}/reports/approved.html" class="btn btn-outline" style="font-size:12px">← 返回报告列表</a>
</div>
{html}
{review_ui}
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
        <div class="module-card" onclick="location.href='{SCRIPT_PREFIX}/modules/{slug}.html'" style="cursor:pointer">
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
<a href="{SCRIPT_PREFIX}/modules/" class="btn btn-outline">← 返回模块列表</a>
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
  <a href="{SCRIPT_PREFIX}/modules/" class="btn btn-outline">← 返回模块列表</a>
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
        # Strip script prefix
        if path.startswith(SCRIPT_PREFIX):
            path = path[len(SCRIPT_PREFIX):]
        if not path:
            path = "/"

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

        # Board / task kanban
        if path == "/board/" or path == "/board/index.html":
            return self.send_html(make_board())

        # Tech reference pages
        if path.startswith("/techref/"):
            techref_dir = path[len("/techref/"):]
            category_map = {
                "browser-relay.html": ["browser-relay-config.md", "browser-relay-full-guide.md", "browser-relay-keepalive.md", "browser-background-open.md"],
                "openclaw-updates.html": ["openclaw-builtin-skills.md", "openclaw-release-log.md", "openclaw-update-analysis-for-01.md", "openclaw-update-analysis-for-01-detailed.md", "post-upgrade-20260329.md", "docs.openclaw.ai-sop.md"],
                "hardware.html": ["jetson-nano-opensclaw-video-stream.md", "node-pairing-sop.md"],
                "research.html": ["comfyui-6gb-research.md", "video-generation-research.md"],
                "misc.html": ["SPEC.md", "before_tool_call-example.md", "blender-robot-test.md", "chat-export-for-rl.md"],
            }

            if techref_dir in category_map:
                files = category_map[techref_dir]
                category_title = {
                    "browser-relay.html": "Browser Relay",
                    "openclaw-updates.html": "OpenClaw 更新",
                    "hardware.html": "硬件参考",
                    "research.html": "调研资料",
                    "misc.html": "其他文档",
                }.get(techref_dir, "技术参考")

                items_html = ""
                for fname in files:
                    f = DOCS_ROOT / fname
                    if f.exists():
                        text = f.read_text(encoding='utf-8')
                        title_m = re.match(r'^#\s+(.+)$', text)
                        title = title_m.group(1).strip() if title_m else fname
                        size_kb = len(text) / 1024
                        items_html += f"""
                        <div class="report-item">
                            <div class="report-item-title">📄 {title}</div>
                            <div class="report-item-meta">{fname} · {size_kb:.1f} KB</div>
                            <div style="margin-top:8px">
                                <a href="{SCRIPT_PREFIX}/{fname.replace('.md','.html')}" class="btn btn-outline" style="font-size:12px;padding:4px 12px">📖 查看</a>
                            </div>
                        </div>"""

                page_title = f"📚 {category_title}"
                return self.send_html(make_page("techref", page_title, f"""
                <div class="content-header">
                    <h1>{page_title}</h1>
                    <div class="content-meta">{len(files)} 个文档</div>
                </div>
                {items_html}
                """))
            elif techref_dir == "" or techref_dir == "index.html":
                # Tech reference index
                return self.send_html(make_page("techref", "📚 技术参考", "<p>请从左侧导航选择分类。</p>"))
            else:
                # Try to serve as individual doc
                doc_name = techref_dir.replace('.html', '.md')
                f = DOCS_ROOT / doc_name
                if f.exists():
                    content = f.read_text(encoding='utf-8')
                    html = render_markdown(content)
                    title_m = re.match(r'^#\s+(.+)$', content)
                    title = title_m.group(1).strip() if title_m else doc_name
                    return self.send_html(make_page("techref", title, f"""
                    <div class="content-header"><h1>{title}</h1><div class="content-meta">{doc_name}</div></div>
                    {html}
                    """))

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

        # Raw file download (e.g. /raw/ROBOT-SOP.md)
        if path.startswith("/raw/"):
            filename = path[len("/raw/"):]
            return self.send_file(filename)

        # PDF export of SOP
        if path == "/api/export/sop-pdf":
            return self.export_sop_pdf()

        # API: get document content for AI reading
        if path.startswith("/api/docs/get"):
            from urllib.parse import parse_qs as _parse_qs
            # Parse query string from path directly
            if '?' in path:
                qs = path.split('?', 1)[1]
            else:
                qs = ''
            params = _parse_qs(qs)
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

        # API: search docs
        if path.startswith("/api/search"):
            from urllib.parse import parse_qs as _parse_qs
            if '?' in path:
                qs = path.split('?', 1)[1]
            else:
                qs = ''
            params = _parse_qs(qs)
            q = params.get('q', [''])[0].strip()

            result = search_docs(q)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            return

        # Static files
        return super().do_GET()

    def do_POST(self):
        path = unquote(self.path)
        # Strip script prefix
        if path.startswith(SCRIPT_PREFIX):
            path = path[len(SCRIPT_PREFIX):]

        # Review API: update report status
        if path == "/api/review":
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))
            filename = body.get('filename', '')
            action = body.get('action', '')  # 'approve' or 'reject'
            note = body.get('note', '')

            # Verify file exists
            reports_dir = SOP_ROOT / "night-build" / "reports"
            if not (reports_dir / filename).exists():
                self.send_error(404)
                return

            # Load/create status.json
            status_file = REPORTS_STATUS
            if status_file.exists():
                statuses = json.loads(status_file.read_text())
            else:
                statuses = {}

            # Update status
            statuses[filename] = {
                "status": "approved" if action == "approve" else "rejected",
                "reviewed_at": dt.datetime.now().isoformat(),
                "reviewer_note": note
            }
            status_file.parent.mkdir(parents=True, exist_ok=True)
            status_file.write_text(json.dumps(statuses, indent=2, ensure_ascii=False))

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            return

        # ── AI Write APIs ────────────────────────────────────────────

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

        # Update module document
        if path == "/api/modules/update":
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))
            slug = body.get('slug', '')
            content = body.get('content', '')

            if not slug:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "slug is required"}).encode())
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

        self.send_error(404)

    def send_file(self, filename):
        """Serve raw file download"""
        # Try SOP_ROOT first, then DOCS_ROOT
        for root_dir in [SOP_ROOT, DOCS_ROOT]:
            file_path = root_dir / filename
            if file_path.exists() and file_path.is_file():
                content = file_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", len(content))
                self.end_headers()
                self.wfile.write(content)
                return
        self.send_error(404)

    def export_sop_pdf(self):
        """Export SOP as PDF. Serves cached PDF if available, falls back to redirect.
        To regenerate: use the browser tool (`browser(action=pdf)`) and copy to docs/.cache/
        Chrome subprocess does not work reliably in daemon context on macOS.
        """
        sop_file = SOP_ROOT / "ROBOT-SOP.md"
        if not sop_file.exists():
            return self.send_error(404)
        pdf_file = DOCS_ROOT / ".cache" / "sop-export.pdf"

        # Serve cached PDF if it exists and is valid (>1KB)
        if pdf_file.exists():
            size = pdf_file.stat().st_size
            if size > 1000:
                content = pdf_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", 'attachment; filename="ROBOT-SOP.pdf"')
                self.send_header("Content-Length", len(content))
                self.end_headers()
                self.wfile.write(content)
                return

        # No cached PDF: redirect to HTML page for browser print-to-PDF
        self.send_response(302)
        self.send_header("Location", "/docs.0-1.ai/sop/full.html")
        self.end_headers()

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
