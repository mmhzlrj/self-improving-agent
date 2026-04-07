#!/usr/bin/env python3
"""Fix ZeroDivisionError in HEARTBEAT.md MiniMax check script."""

path = '/Users/lr/.openclaw/workspace/HEARTBEAT.md'
old = 'pct_used = (used / total) * 100'
new = 'pct_used = (used / total * 100) if total > 0 else 0.0'

with open(path, 'r') as f:
    content = f.read()

if old in content:
    content = content.replace(old, new, 1)  # Only replace first occurrence
    with open(path, 'w') as f:
        f.write(content)
    print('✅ Fixed: pct_used division by zero guard added.')
    print(f'Changed: {old}')
    print(f'To:      {new}')
else:
    print('⚠️  Pattern not found — already fixed or different text.')
