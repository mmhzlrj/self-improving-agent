#!/usr/bin/env python3
"""Deduplicate command-log.md"""
path = '/Users/lr/.openclaw/workspace/docs/command-log.md'
with open(path) as f:
    lines = f.readlines()

# Find the 2026-04-07 section and deduplicate
seen = set()
output = []
skip = False
for line in lines:
    # Skip duplicate "openclaw update run" entries
    if 'openclaw update run' in line and line in seen:
        continue
    seen.add(line)
    output.append(line)

with open(path, 'w') as f:
    f.writelines(output)
print(f"Done, removed duplicates. Total lines: {len(output)}")
