#!/bin/bash
# Tailscale userspace 安装脚本（完全不需要root）

set -e
TARBALL=/tmp/tailscale.tar.gz
STATE_FILE=/home/jet/tailscale.state
BIN_DIR=/home/jet/bin
TS_BIN=${BIN_DIR}/tailscaled
TS=${BIN_DIR}/tailscale

echo "[1/6] 创建bin目录..."
mkdir -p $BIN_DIR

echo "[2/6] 检查tailscale二进制..."
if [ ! -f $TS_BIN ] || [ ! -f $TS ]; then
    echo "[3/6] 解压到$BIN_DIR..."
    mkdir -p /tmp/ts_extract
    tar -xzf $TARBALL -C $BIN_DIR --strip-components=1 -C $BIN_DIR
    ls $BIN_DIR/
else
    echo "[3/6] 二进制已存在，跳过解压"
fi

echo "[4/6] 添加Mac公钥到authorized_keys..."
MAC_PUB="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHcFla5/ii1T7Env4GCelZIpzkCchQcPanNg27QQcimw MacBook-LR"
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
if ! grep -q "$MAC_PUB" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "$MAC_PUB" >> ~/.ssh/authorized_keys
    echo "公钥已添加"
else
    echo "公钥已存在"
fi
chmod 600 ~/.ssh/authorized_keys

echo "[5/6] 启动tailscaled（userspace模式）..."
pkill tailscaled 2>/dev/null || true
$TS_BIN --tun=userspace-networking --state=$STATE_FILE &
sleep 3
if ps aux | grep tailscaled | grep -v grep > /dev/null; then
    echo "tailscaled 启动成功！PID=$(pgrep tailscaled)"
else
    echo "tailscaled 启动失败"
    exit 1
fi

echo "[6/6] 等待tailscale up（会打印登录链接）..."
$TS up
echo "完成！Tailnet IP: $($TS ip -4)"
