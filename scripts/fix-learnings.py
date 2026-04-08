#!/usr/bin/env python3
"""Remove duplicate content in LEARNINGS.md after the 2026-04-07 section."""
path = '/Users/lr/.openclaw/workspace/.learnings/LEARNINGS.md'
with open(path) as f:
    content = f.read()

# Find the problematic duplicate area - after "添加新路径前必须先..."
# Remove the duplicate commands and orphaned "**错误的命令**：" line
marker = '添加新路径前必须先 `ls /usr/bin/xxx /sbin/xxx` 确认存在'
if marker in content:
    # Find where the duplicate starts and ends
    idx = content.index(marker) + len(marker)
    rest = content[idx:]
    # Remove duplicate content until "**避免 SSL 问题**"
    if rest.startswith('\n- ✅ `gh release list'):
        # Remove everything until "**避免 SSL 问题**"
        ssl_marker = '**避免 SSL 问题**'
        ssl_idx = rest.index(ssl_marker)
        content = content[:idx] + rest[ssl_idx:]
        print("Cleaned duplicate content")
    else:
        print("Marker found but no duplicate")
else:
    print("Marker not found")

with open(path, 'w') as f:
    f.write(content)
print("Done")
