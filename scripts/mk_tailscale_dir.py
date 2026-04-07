#!/usr/bin/env python3
import subprocess
import sys

password = "13572468"

# 用 sshpass 方式：通过pty自动响应sudo密码
cmd = [
    'ssh', '-tt', '-o', 'StrictHostKeyChecking=no',
    'jet@192.168.1.18',
    f'echo {password} | sudo -S mkdir -p /var/run/tailscale && sudo chown jet:jet /var/run/tailscale && ls -la /var/run/tailscale/'
]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out, _ = proc.communicate(input=(password + '\n').encode(), timeout=15)
print(out.decode())
