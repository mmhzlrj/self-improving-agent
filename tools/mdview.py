#!/usr/bin/env python3
"""
Markdown 文件预览器
用浏览器打开 Markdown 文件，支持代码高亮和审批模式

用法:
  mdview <文件路径>              # 普通预览
  mdview --review <文件路径>     # 审批模式（带采纳/不采纳/备注按钮）
"""

import sys
import os
import json
import datetime
import argparse
import re
import markdown
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import webbrowser
import time

# 扩展
MD_EXTENSIONS = [
    'extra', 'codehilite', 'tables', 'fenced_code', 'nl2br'
]

PORT = 18999

# ============ 通用 CSS ============
BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    line-height: 1.7;
    color: #1f2937;
    background: #f3f4f6;
}
.container {
    max-width: 960px;
    margin: 0 auto;
    padding: 24px;
}
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
code {
    background: #f3f4f6;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', Consolas, monospace;
    font-size: 0.85em;
    color: #e11d48;
}
pre {
    background: #1e293b;
    color: #e2e8f0;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 12px 0;
    font-size: 14px;
}
pre code {
    background: none;
    padding: 0;
    color: inherit;
    font-size: inherit;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
    font-size: 14px;
}
th, td {
    border: 1px solid #e5e7eb;
    padding: 10px 14px;
    text-align: left;
}
th {
    background: #f9fafb;
    font-weight: 600;
    color: #374151;
}
blockquote {
    border-left: 4px solid #3b82f6;
    margin: 12px 0;
    padding: 8px 16px;
    color: #6b7280;
    background: #eff6ff;
    border-radius: 0 6px 6px 0;
}
img { max-width: 100%; height: auto; border-radius: 8px; }
h1 { font-size: 1.8em; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin-bottom: 16px; }
h2 { font-size: 1.4em; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin: 24px 0 12px; }
h3 { font-size: 1.2em; margin: 20px 0 10px; }
hr { border: none; border-top: 1px solid #e5e7eb; margin: 24px 0; }
ul, ol { padding-left: 24px; margin: 8px 0; }
li { margin: 4px 0; }
p { margin: 8px 0; }
strong { color: #111827; }
"""

# ============ 审批模式 CSS ============
REVIEW_CSS = """
.review-item {
    background: #fff;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    padding: 20px;
    margin: 16px 0;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.review-item:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.review-item.approved {
    border-color: #22c55e;
    background: #f0fdf4;
}
.review-item.rejected {
    border-color: #ef4444;
    background: #fef2f2;
}
.review-item.pending {
    border-color: #f59e0b;
    background: #fffbeb;
}
.review-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    flex-wrap: wrap;
    gap: 10px;
}
.review-title {
    font-size: 16px;
    font-weight: 700;
    color: #111827;
    display: flex;
    align-items: center;
    gap: 8px;
}
.review-actions {
    display: flex;
    gap: 8px;
}
.review-actions button {
    padding: 7px 18px;
    border-radius: 8px;
    border: 1px solid transparent;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 4px;
}
.btn-approve {
    background: #dcfce7;
    color: #166534;
    border-color: #bbf7d0;
}
.btn-approve:hover { background: #bbf7d0; }
.btn-reject {
    background: #fee2e2;
    color: #991b1b;
    border-color: #fecaca;
}
.btn-reject:hover { background: #fecaca; }
.review-note {
    width: 100%;
    margin-top: 10px;
    padding: 10px 14px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    font-size: 13px;
    resize: vertical;
    min-height: 40px;
    font-family: inherit;
    color: #374151;
    background: #f9fafb;
    transition: border-color 0.15s;
}
.review-note:focus {
    outline: none;
    border-color: #3b82f6;
    background: #fff;
}
.review-note::placeholder { color: #9ca3af; }
.review-diff { margin: 10px 0; }
.diff-label {
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
    color: #6b7280;
}
.diff-old {
    background: #fef2f2;
    border-left: 3px solid #ef4444;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin: 6px 0;
    font-size: 14px;
    color: #7f1d1d;
}
.diff-new {
    background: #f0fdf4;
    border-left: 3px solid #22c55e;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin: 6px 0;
    font-size: 14px;
    color: #14532d;
}
.review-status {
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 700;
    letter-spacing: 0.02em;
}
.review-status.pending { background: #fef3c7; color: #92400e; }
.review-status.approved { background: #dcfce7; color: #166534; }
.review-status.rejected { background: #fee2e2; color: #991b1b; }
.review-priority {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
}

/* Toolbar */
.review-toolbar {
    position: sticky;
    top: 0;
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid #e5e7eb;
    padding: 14px 24px;
    margin: -24px -24px 24px -24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 100;
    flex-wrap: wrap;
    gap: 10px;
}
.review-stats {
    display: flex;
    gap: 16px;
    font-size: 13px;
    font-weight: 600;
}
.toolbar-actions {
    display: flex;
    gap: 8px;
}
.toolbar-btn {
    padding: 7px 16px;
    border-radius: 8px;
    border: 1px solid #d1d5db;
    background: #fff;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 4px;
}
.toolbar-btn:hover { background: #f3f4f6; border-color: #9ca3af; }
.toolbar-btn.primary { background: #2563eb; border-color: #2563eb; color: #fff; }
.toolbar-btn.primary:hover { background: #1d4ed8; }
.toolbar-btn.success { background: #16a34a; border-color: #16a34a; color: #fff; }
.toolbar-btn.success:hover { background: #15803d; }

/* Bottom bar */
.review-bottom {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(8px);
    border-top: 1px solid #e5e7eb;
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 100;
}
body.review-mode { padding-bottom: 70px; }

/* Verified section */
.verified-section {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 16px 0;
}
.verified-section h3 { color: #166534; margin-bottom: 8px; }
"""

# ============ JavaScript ============
REVIEW_JS = """
<script>
const STORAGE_KEY = 'mdview_review_' + document.title;
function getRS() { try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch { return {}; } }
function saveRS(s) { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); }
function updateStats() {
    const state = getRS();
    const items = document.querySelectorAll('.review-item');
    let total=items.length, approved=0, rejected=0, pending=0;
    items.forEach(item => {
        const id = item.dataset.id;
        const s = state[id] || { status: 'pending' };
        item.className = 'review-item ' + s.status;
        const badge = item.querySelector('.review-status');
        if (badge) { badge.className = 'review-status ' + s.status; badge.textContent = {pending:'\\u23f3 \\u5f85\\u5ba1\\u6279',approved:'\\u2705 \\u5df2\\u91c7\\u7eb3',rejected:'\\u274c \\u5df2\\u62d2\\u7edd'}[s.status]||'\\u23f3 \\u5f85\\u5ba1\\u6279'; }
        const note = item.querySelector('.review-note');
        if (note && s.note) note.value = s.note;
        if (s.status==='approved') approved++; else if (s.status==='rejected') rejected++; else pending++;
    });
    const el = document.getElementById('review-stats');
    if (el) el.innerHTML = '<span>\\ud83d\\udccb \\u603b\\u8ba1: '+total+'</span><span style="color:#16a34a">\\u2705 \\u91c7\\u7eb3: '+approved+'</span><span style="color:#ef4444">\\u274c \\u62d2\\u7edd: '+rejected+'</span><span style="color:#d97706">\\u23f3 \\u5f85\\u5ba1: '+pending+'</span>';
}
function setReview(id, status) {
    const state = getRS();
    const note = document.querySelector('[data-id="'+id+'"] .review-note');
    state[id] = { status, note: note?note.value:'', time: new Date().toISOString() };
    saveRS(state); updateStats();
}
function saveNote(id) {
    const state = getRS();
    const note = document.querySelector('[data-id="'+id+'"] .review-note');
    if (state[id]) state[id].note = note?note.value:''; else state[id] = {status:'pending',note:note?note.value:'',time:new Date().toISOString()};
    saveRS(state);
}
function approveAll() { if (!confirm('\\u786e\\u5b9a\\u5168\\u90e8\\u91c7\\u7eb3\\uff1f')) return; const s=getRS(); document.querySelectorAll('.review-item').forEach(item=>{const id=item.dataset.id;const n=item.querySelector('.review-note');s[id]={status:'approved',note:n?n.value:'',time:new Date().toISOString()};}); saveRS(s); updateStats(); }
function exportResults() {
    const s=getRS();const r=[];document.querySelectorAll('.review-item').forEach(item=>{const id=item.dataset.id;const t=item.querySelector('.review-title')?.textContent||'';const st=s[id]||{status:'pending',note:''};r.push({id,title:t,status:st.status,note:st.note,time:st.time});});
    const blob=new Blob([JSON.stringify(r,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='review-results-'+new Date().toISOString().slice(0,10)+'.json';a.click();URL.revokeObjectURL(url);
}
function clearAll() { if (!confirm('\\u786e\\u5b9a\\u6e05\\u7a7a\\u6240\\u6709\\u5ba1\\u6279\\u72b6\\u6001\\uff1f')) return; localStorage.removeItem(STORAGE_KEY); updateStats(); }
document.addEventListener('input', function(e){if(e.target.classList.contains('review-note')){const item=e.target.closest('.review-item');if(item)saveNote(item.dataset.id);}});
document.addEventListener('DOMContentLoaded', updateStats);
</script>
"""


class UTF8HTTPRequestHandler(SimpleHTTPRequestHandler):
    """确保 HTML 文件以 UTF-8 编码提供"""
    def end_headers(self):
        path = self.translate_path(self.path)
        if path.endswith('.html') or path.endswith('.htm'):
            self.send_header('Content-Type', 'text/html; charset=utf-8')
        super().end_headers()

    def log_message(self, format, *args):
        pass  # 静默日志


def start_server(directory):
    """启动 HTTP 服务器"""
    os.chdir(directory)
    server = HTTPServer(('127.0.0.1', PORT), UTF8HTTPRequestHandler)
    server.serve_forever()


def generate_normal_html(filepath):
    """普通预览模式"""
    with open(filepath, 'r', encoding='utf-8') as f:
        md_content = f.read()

    html_body = markdown.markdown(md_content, extensions=MD_EXTENSIONS)
    filename = os.path.basename(filepath)
    title = os.path.splitext(filename)[0]

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>{BASE_CSS}</style>
</head>
<body>
<div class="container">
{html_body}
</div>
</body>
</html>"""


def generate_review_html(filepath):
    """审批模式"""
    with open(filepath, 'r', encoding='utf-8') as f:
        md_content = f.read()

    filename = os.path.basename(filepath)
    title = os.path.splitext(filename)[0]

    # 解析修改意见条目
    sections = re.split(r'\n###\s*(\d+)\.\s*', md_content)
    header_html = markdown.markdown(sections[0], extensions=MD_EXTENSIONS)

    items = []
    for i in range(1, len(sections), 2):
        if i + 1 >= len(sections):
            break
        item_num = sections[i]
        item_content = sections[i + 1]
        item_id = f"item-{item_num}"
        lines = item_content.strip().split('\n')
        item_title = f"#{item_num} {lines[0]}" if lines else f"#{item_num}"

        old_text = new_text = source = ""
        priority = "\U0001f7e1\u4e2d"

        for line in lines:
            if '\u539f\u6587' in line and '\u5efa\u8bae\u6539\u4e3a' not in line:
                old_text = re.sub(r'^\*\*\u539f\u6587\*\*[：:]\s*', '', line)
            elif '\u5efa\u8bae\u6539\u4e3a' in line:
                new_text = re.sub(r'^\*\*\u5efa\u8bae\u6539\u4e3a\*\*[：:]\s*', '', line)
            elif '\u6765\u6e90' in line:
                source = re.sub(r'^\*\*\u6765\u6e90\*\*[：:]\s*', '', line)
            elif '\u4f18\u5148\u7ea7' in line:
                priority = re.sub(r'^\*\*\u4f18\u5148\u7ea7\*\*[：:]\s*', '', line)

        rest_html = markdown.markdown('\n'.join(lines), extensions=MD_EXTENSIONS)
        items.append({
            'id': item_id, 'num': item_num, 'title': item_title,
            'old_text': old_text, 'new_text': new_text,
            'priority': priority, 'content_html': rest_html,
        })

    items_html = ""
    for item in items:
        diff_html = ""
        if item['old_text']:
            diff_html += f'<div class="diff-old"><div class="diff-label">\U0001f4c4 \u539f\u6587</div>{item["old_text"]}</div>\n'
        if item['new_text']:
            diff_html += f'<div class="diff-new"><div class="diff-label">\u270f\ufe0f \u5efa\u8bae</div>{item["new_text"]}</div>\n'

        items_html += f"""
<div class="review-item pending" data-id="{item['id']}">
    <div class="review-header">
        <div style="display:flex;align-items:center;gap:10px;">
            <h3 class="review-title">{item['title']}</h3>
            <span class="review-status pending">\u23f3 \u5f85\u5ba1\u6279</span>
        </div>
        <div class="review-actions">
            <button class="btn-approve" onclick="setReview('{item['id']}', 'approved')">\u2705 \u91c7\u7eb3</button>
            <button class="btn-reject" onclick="setReview('{item['id']}', 'rejected')">\u274c \u62d2\u7edd</button>
        </div>
    </div>
    <div class="review-diff">{diff_html}</div>
    {item['content_html'] if item['old_text'] or item['new_text'] else ''}
    <textarea class="review-note" placeholder="\U0001f4dd \u5907\u6ce8\u8bf4\u660e\uff08\u53ef\u9009\uff09..." oninput="saveNote('{item['id']}')"></textarea>
</div>
"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <title>\U0001f4cb {title}</title>
    <style>{BASE_CSS}\n{REVIEW_CSS}</style>
    {REVIEW_JS}
</head>
<body class="review-mode">
<div class="review-toolbar">
    <div class="review-stats" id="review-stats">
        <span>\U0001f4cb \u603b\u8ba1: {len(items)}</span>
        <span style="color:#d97706">\u23f3 \u5f85\u5ba1: {len(items)}</span>
    </div>
    <div class="toolbar-actions">
        <button class="toolbar-btn success" onclick="approveAll()">\u2705 \u5168\u90e8\u91c7\u7eb3</button>
        <button class="toolbar-btn" onclick="clearAll()">\U0001f504 \u91cd\u7f6e</button>
        <button class="toolbar-btn primary" onclick="exportResults()">\U0001f4e4 \u5bfc\u51fa\u7ed3\u679c</button>
    </div>
</div>
<div class="container">
{header_html}
{items_html}
</div>
<div class="review-bottom">
    <div style="font-size:12px;color:#6b7280;">
        \U0001f4a1 \u5ba1\u6279\u7ed3\u679c\u81ea\u52a8\u4fdd\u5b58\u5230\u6d4f\u89c8\u5668\u672c\u5730\u5b58\u50a8
    </div>
    <div class="toolbar-actions">
        <button class="toolbar-btn primary" onclick="exportResults()">\U0001f4e4 \u5bfc\u51fa JSON \u7ed3\u679c</button>
    </div>
</div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description='Markdown \u6587\u4ef6\u9884\u89c8\u5668')
    parser.add_argument('filepath', help='Markdown \u6587\u4ef6\u8def\u5f84')
    parser.add_argument('--review', '-r', action='store_true', help='\u5ba1\u6279\u6a21\u5f04\uff08\u5e26\u91c7\u7eb3/\u4e0d\u91c7\u7eb3\u6309\u94ae\uff09')
    args = parser.parse_args()

    filepath = os.path.expanduser(args.filepath)
    if not os.path.exists(filepath):
        print(f"\u274c \u6587\u4ef6\u4e0d\u5b58\u5728: {filepath}")
        sys.exit(1)

    # Output directory
    out_dir = os.path.expanduser('~/.openclaw/workspace/.review/html')
    os.makedirs(out_dir, exist_ok=True)

    # Generate HTML
    if args.review:
        html_content = generate_review_html(filepath)
        mode_label = '\u5ba1\u6279\u6a21\u5f0f'
    else:
        html_content = generate_normal_html(filepath)
        mode_label = '\u666e\u901a\u9884\u89c8'

    out_path = os.path.join(out_dir, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Start HTTP server in background thread
    server_thread = threading.Thread(target=start_server, args=(out_dir,), daemon=True)
    server_thread.start()
    time.sleep(0.5)

    # Open browser
    webbrowser.open(f'http://127.0.0.1:{PORT}/index.html')

    filename = os.path.basename(filepath)
    print(f"\u2705 \u5df2\u6253\u5f00\uff08{mode_label}\uff09: {filename}")
    print(f"   URL: http://127.0.0.1:{PORT}/index.html")

    # Keep server alive
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
