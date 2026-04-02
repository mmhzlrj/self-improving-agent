#!/usr/bin/env python3
"""把 /var/run/tailscale/tailscaled.sock 的请求转发到实际 socket"""
import socket
import threading
import os
import signal

REAL_SOCKET = "/home/jet/tailscaled.sock"
FAKE_SOCKET = "/var/run/tailscale/tailscaled.sock"

def handle_client(src, dst_addr):
    """一个人走过来，帮我把信送到对面的信箱"""
    try:
        dst = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        dst.connect(REAL_SOCKET)
        # 双向转发
        def forward(src, dst):
            try:
                while True:
                    data = src.recv(4096)
                    if not data:
                        break
                    dst.sendall(data)
            except:
                pass
            finally:
                try:
                    src.close()
                except:
                    pass
                try:
                    dst.close()
                except:
                    pass
        t1 = threading.Thread(target=forward, args=(src, dst))
        t2 = threading.Thread(target=forward, args=(dst, src))
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()
    except Exception as e:
        src.close()

def main():
    # 创建目录
    os.makedirs("/var/run/tailscale", exist_ok=True)
    # 清理旧socket
    if os.path.exists(FAKE_SOCKET):
        os.unlink(FAKE_SOCKET)
    # 监听
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(FAKE_SOCKET)
    server.listen(50)
    os.chmod(FAKE_SOCKET, 0o666)
    print(f"代理启动: {FAKE_SOCKET} -> {REAL_SOCKET}")
    while True:
        src, _ = server.accept()
        threading.Thread(target=handle_client, args=(src, None), daemon=True).start()

if __name__ == "__main__":
    main()
