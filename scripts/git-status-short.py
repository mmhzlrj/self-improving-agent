#!/usr/bin/env python3
"""Git status short, limited without head."""
import subprocess
r = subprocess.run(['git', '-C', '/Users/lr/.openclaw/workspace', 'status', '--short'], capture_output=True, text=True)
lines = r.stdout.splitlines()
for l in lines[:20]:
    print(l)
