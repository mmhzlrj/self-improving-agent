#!/usr/bin/env python3
"""
Monitor script for docs.0-1.ai server (port 18998).
If the service is down, kill any stale processes and restart it.
Logs restart events to /tmp/docs-server-restart.log
"""

import socket
import subprocess
import os
import sys
from datetime import datetime

PORT = 18998
SCRIPT_PATH = os.path.expanduser("~/.openclaw/workspace/tools/docs-server.py")
LOG_FILE = "/tmp/docs-server-restart.log"
PID_FILE = "/tmp/docs-server.pid"


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def is_port_listening(port):
    """Check if port is listening via /dev/tcp (macOS compatible)."""
    try:
        # Use a quick connection test
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def kill_old_process():
    """Kill any existing docs-server.py processes."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "docs-server.py"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), 9)
                        log(f"Killed old process PID {pid}")
                    except ProcessLookupError:
                        pass
    except Exception as e:
        log(f"Error killing old process: {e}")


def start_server():
    """Start docs-server.py in background."""
    try:
        # Get the directory of the script
        script_dir = os.path.dirname(os.path.abspath(SCRIPT_PATH))
        subprocess.Popen(
            [sys.executable, SCRIPT_PATH],
            cwd=script_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        log("Started docs-server.py")
        return True
    except Exception as e:
        log(f"Failed to start docs-server.py: {e}")
        return False


def main():
    if is_port_listening(PORT):
        # Service is healthy — just log check occasionally (not every run to avoid log spam)
        # We'll only log when actually restarting
        pass
    else:
        log("Port 18998 NOT listening — attempting restart...")
        kill_old_process()
        # Brief pause to let the port be released
        import time
        time.sleep(1)
        if start_server():
            log("Restart successful")
        else:
            log("RESTART FAILED")

if __name__ == "__main__":
    main()
