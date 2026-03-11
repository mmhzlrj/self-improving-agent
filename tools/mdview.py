#!/usr/bin/env python3
"""
Markdown 文件预览器
用浏览器打开 Markdown 文件，支持代码高亮
"""

import sys
import os
import tempfile
import webbrowser
import markdown

# 扩展
MD_EXTENSIONS = [
    'extra', 'codehilite', 'tables', 'fenced_code', 'nl2br'
]

# CSS 样式（类似 GitHub）
CSS = """
<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    line-height: 1.6;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
    background: #fff;
}
pre {
    background: #f6f8fa;
    padding: 16px;
    border-radius: 6px;
    overflow-x: auto;
}
code {
    background: #f6f8fa;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'SF Mono', Monaco, Consolas, monospace;
    font-size: 85%;
}
pre code {
    background: none;
    padding: 0;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
}
th, td {
    border: 1px solid #d0d7de;
    padding: 8px 12px;
}
th {
    background: #f6f8fa;
}
blockquote {
    border-left: 4px solid #d0d7de;
    margin: 0;
    padding-left: 16px;
    color: #57606a;
}
img {
    max-width: 100%;
    height: auto;
}
a {
    color: #0969da;
}
h1, h2, h3, h4, h5, h6 {
    border-bottom: 1px solid #d0d7de;
    padding-bottom: 0.3em;
}
</style>
"""

def view_markdown(filepath):
    """用浏览器打开 Markdown 文件"""
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return False
    
    # 读取 Markdown 文件
    with open(filepath, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 转换为 HTML
    html_content = markdown.markdown(md_content, extensions=MD_EXTENSIONS)
    
    # 添加标题
    filename = os.path.basename(filepath)
    title = os.path.splitext(filename)[0]
    
    # 完整 HTML
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    {CSS}
</head>
<body>
{html_content}
</body>
</html>"""
    
    # 写入临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(full_html)
        temp_path = f.name
    
    # 用浏览器打开
    webbrowser.open(f'file://{temp_path}')
    print(f"✅ 已打开: {filename}")
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: mdview <文件路径>")
        print("示例: mdview ~/.openclaw/workspace/harness/aigc-workflow/README.md")
        sys.exit(1)
    
    filepath = sys.argv[1]
    # 展开 ~
    filepath = os.path.expanduser(filepath)
    
    view_markdown(filepath)

if __name__ == "__main__":
    main()
