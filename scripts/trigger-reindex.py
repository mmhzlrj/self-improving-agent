#!/usr/bin/env python3
"""Trigger reindex via SSH tunnel."""
import subprocess, time

# Start SSH tunnel in background
tunnel = subprocess.Popen([
    'ssh', '-L', '5050:localhost:5050',
    'jet@192.168.1.18',
    'curl -s http://localhost:5050/reindex'
], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

try:
    out, err = tunnel.communicate(timeout=10)
    print(out)
    print(err)
except subprocess.TimeoutExpired:
    tunnel.kill()
    out, err = tunnel.communicate()
    print('TIMEOUT')
    print(out[-500:] if out else '')
