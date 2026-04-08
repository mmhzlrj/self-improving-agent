#!/usr/bin/env python3
import subprocess, sys
r = subprocess.run(['/usr/bin/rsync', '-avz', '--ignore-existing',
    '/Users/lr/.openclaw/agents/main/sessions/',
    'jet@192.168.1.18:/home/jet/.openclaw/agents/main/sessions/'],
    capture_output=True, text=True)
print(r.stdout[-2000:] if r.stdout else '(no stdout)')
print(r.stderr[-500:] if r.stderr else '(no stderr)')
print('exit:', r.returncode)
