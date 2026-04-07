#!/bin/bash
#
# node-setup/uninstall.sh - Node setup 卸载脚本
# 用途: 清理 node-setup 安装的所有组件
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${SCRIPT_DIR}"

echo "=== Node Setup Uninstall ==="
echo "安装目录: ${INSTALL_DIR}"

# 检查是否有安装记录
if [ ! -f "${INSTALL_DIR}/.install_manifest" ]; then
    echo "[INFO] 未找到安装记录，尝试清理默认安装位置..."
fi

# 停止服务
echo "[Step 1/4] 停止 node-setup 服务..."
if [ -f "${INSTALL_DIR}/stop.sh" ]; then
    bash "${INSTALL_DIR}/stop.sh" 2>/dev/null || true
fi

# 杀死相关进程
echo "[Step 2/4] 清理相关进程..."
pkill -f "node-setup" 2>/dev/null || true
pkill -f "node_manager" 2>/dev/null || true

# 清理配置文件
echo "[Step 3/4] 清理配置文件..."
rm -f ~/.node_setup_config 2>/dev/null || true
rm -f ~/.config/node-setup/*.json 2>/dev/null || true
rm -rf ~/.node-setup 2>/dev/null || true

# 清理安装目录
echo "[Step 4/4] 清理安装目录..."
if [ -d "${INSTALL_DIR}" ]; then
    # 只删除 node-setup 特有的文件，保留目录结构
    rm -f "${INSTALL_DIR}"/*.sh 2>/dev/null || true
    rm -f "${INSTALL_DIR}"/*.py 2>/dev/null || true
    rm -f "${INSTALL_DIR}"/*.json 2>/dev/null || true
    rm -f "${INSTALL_DIR}"/.install_manifest 2>/dev/null || true
fi

echo ""
echo "=== 卸载完成 ==="
echo "注意: 如需完全删除，请手动移除整个目录: ${INSTALL_DIR}"
echo ""
