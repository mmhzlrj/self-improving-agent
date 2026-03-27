# Jetson Nano 2GB × OpenClaw 部署百科全书

> **文档版本**: 1.0  
> **目标设备**: Jetson Nano 2GB (P3448 量产模块)  
> **系统**: JetPack 4.x / 5.x (Ubuntu 18.04 / 20.04 aarch64)  
> **角色**: OpenClaw 视觉 + 语音处理边缘节点  
> **Gateway 通信**: WebSocket (TCP:18789)

---

## 目录

1. [任务概述](#1-任务概述)
2. [环境确认（环境诊断 SOP）](#2-环境确认环境诊断-sop)
3. [OpenClaw 安装](#3-openclaw-安装)
4. [内存优化（2GB 专用）](#4-内存优化2gb-专用)
5. [Gateway 对接](#5-gateway-对接)
6. [问题与解决方案（9 大类）](#6-问题与解决方案9-大类)
7. [验证方法](#7-验证方法)
8. [架构定位](#8-架构定位)

---

## 1. 任务概述

### 1.1 Jetson Nano 在 0-1 项目中的角色

```
┌─────────────────────────────────────────────────────────┐
│                     OpenClaw Gateway                     │
│                  (MacBook Pro / VPS)                     │
│               WebSocket Port 18789                       │
└──────────────────────┬──────────────────────────────────┘
                       │ LAN / Tailscale / SSH Tunnel
                       │ WebSocket (role: "node")
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 Jetson Nano 2GB (节点)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  YOLO 目标检测 │  │ MediaPipe    │  │ OpenClaw    │ │
│  │  (FP16/TRT)   │  │ 姿态/手势     │  │ Node Host   │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
│            ▲ 提供视觉 AI 算力          ▲ 节点注册       │
└─────────────────────────────────────────────────────────┘
```

**Nano 的核心职责**：
- 充当中控 Gateway 的**视觉推理节点**（YOLO 目标检测）
- 提供**语音/姿态处理**能力（MediaPipe）
- 通过 `openclaw node run` 以 headless 模式接入 Gateway
- 暴露 `system.run` / `system.which` 命令供 Gateway 远程调用
- Gateway 通过 `node.invoke` 调用 Nano 上的 AI 能力

### 1.2 要达成的最终状态

| 检查项 | 目标状态 |
|--------|----------|
| `openclaw node status` | 显示 Nano 为 `connected` + `paired` |
| `openclaw devices list` | Nano 设备状态为 `approved` |
| CUDA 可用 | `nvcc --version` 输出正常 |
| Swap 激活 | `free -h` 显示 swap ≥ 4GB |
| 内存充足 | 空闲 RAM + swap 稳定在 1GB 以上 |
| FP16 推理 | YOLO ONNX 以 FP16 模式加载 |

---

## 2. 环境确认（环境诊断 SOP）

### 2.1 检查 Jetson Nano 型号与系统版本

```bash
# 确认是 2GB 模块（而非 4GB）
cat /etc/nv_tegra_release
# 输出示例：R32 (release), REVISION: 7.4, GC: 131

# 查看模块型号
sudo cat /proc/device-tree/model
# 输出：NVIDIA Jetson Nano 2GB Developer Kit

# 检查 OS 版本
lsb_release -a
# JetPack 4.x = Ubuntu 18.04
# JetPack 5.x = Ubuntu 20.04
```

### 2.2 检查 JetPack 版本（核心依赖）

```bash
# 方法 1：nvcc 路径
/usr/local/cuda/bin/nvcc --version
# JetPack 4.x → CUDA 10.2
# JetPack 5.x → CUDA 11.4

# 方法 2：jetpack conda（若有）
dpkg -l | grep nvidia
# 或
apt list --installed 2>/dev/null | grep cuda

# 方法 3：SDK Manager
# 访问 https://developer.nvidia.com/embedded/jetpack 下载对应版本
```

**版本对照表**：

| JetPack | CUDA | Ubuntu | Python | Node.js 兼容性 |
|---------|------|--------|--------|---------------|
| 4.6.x | CUDA 10.2 | 18.04 | 3.6-3.8 | ✅ 支持 |
| 5.1.x | CUDA 11.4 | 20.04 | 3.8-3.10 | ✅ 推荐 |

> ⚠️ **2GB 特别建议**：优先使用 **JetPack 4.6.x**（CUDA 10.2），兼容性最佳，社区资源最丰富。JetPack 5.x 对 2GB 模块支持较新，部分库可能存在兼容性问题。

### 2.3 检查 GPU 驱动与 CUDA

```bash
# NVIDIA 驱动状态
cat /proc/driver/nvidia/version
# 输出示例：NVRM version: NVIDIA UNIX Driver  32.7.3

# GPU 信息
nvidia-smi
# 检查：GPU 内存使用、GPU 架构（应为 Maxwell）
# 2GB 模块 GPU 型号：NVIDIA Maxwell (128 CUDA cores)

# CUDA 路径确认
echo $CUDA_HOME
# 通常：/usr/local/cuda-10.2 或 /usr/local/cuda-11.4

# 验证 CUDA 库
ldconfig -p | grep libcudart
```

### 2.4 检查存储空间

```bash
# 根分区可用空间（至少需要 8GB+）
df -h /

# 检查 /home 分区
df -h /home

# 查看最大目录
sudo du -sh /var/cache/apt/archives 2>/dev/null || true
sudo du -sh /usr/src 2>/dev/null || true
```

### 2.5 检查内存总量

```bash
# 物理内存（应为 ~1.9GB 可用）
free -h
#               total        used        free      shared  buff/cache   available
# Mem:          1.9Gi       800Mi       300Mi        50Mi       800Mi       1.0Gi

# Swap 状态（初始应为 0）
sudo swapon --show
```

---

## 3. OpenClaw 安装

### 3.1 安装方式选择

OpenClaw 在 Linux 上通过 **npm 全局安装**：

```bash
# 官方推荐（一键安装脚本）
curl -fsSL https://openclaw.ai/install.sh | bash

# 或直接 npm 全局安装
npm i -g openclaw@latest
```

> **注意**：OpenClaw **不提供** deb/rpm 包，也不提供独立二进制。安装依赖 Node.js 运行时。

### 3.2 Jetson Nano 特定注意事项

#### ✅ ARM64 (aarch64) 兼容性

```bash
# 确认架构为 aarch64
uname -m
# 输出必须是：aarch64

# OpenClaw 的 Node.js 运行时完全支持 ARM64
# 但部分第三方 skill 二进制可能只有 x86_64
# 检查方式：
file $(which node)
# 输出：ELF 64-bit LSB executable, ARM aarch64
```

#### ✅ Node.js 版本要求

OpenClaw 要求 **Node.js ≥ 22.14**，**推荐 Node.js 24**。

```bash
# 检查当前 Node.js 版本
node -v

# 如果版本过低或未安装，参考 Raspberry Pi 文档（同样 ARM64）
# 在 Jetson Nano 上安装 Node.js 24：
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证
node -v   # 期望：v24.x.x
npm -v    # 期望：10.x.x 或更高
```

> ⚠️ **JetPack 自带 Python 和部分系统库，不要用 conda 管理 Node.js**。建议用 `nvm` 或直接用 nodesource 官方脚本。

#### ✅ JetPack 兼容性验证

```bash
# CUDA 环境变量（确保添加到 ~/.bashrc）
grep -q 'CUDA_HOME' ~/.bashrc || echo 'export CUDA_HOME=/usr/local/cuda-10.2' >> ~/.bashrc
grep -q 'LD_LIBRARY_PATH' ~/.bashrc || echo 'export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 验证 CUDA 可被 Node.js add-on 调用
# （OpenClaw 内部如使用 CUDA 会检查 nvcc）
nvcc --version
```

### 3.3 早期版本升级

```bash
# 方式 1：openclaw update（推荐）
openclaw update

# 方式 2：npm 升级
npm update -g openclaw

# 方式 3：重跑安装脚本
curl -fsSL https://openclaw.ai/install.sh | bash

# 升级后验证
openclaw --version
openclaw doctor
```

### 3.4 完整安装流程（Step by Step）

```bash
# === 完整 SSH 连接后执行 ===

# Step 1: 更新系统（可选但推荐，JetPack 默认源较旧）
sudo apt update && sudo apt upgrade -y

# Step 2: 安装基础工具
sudo apt install -y git curl build-essential

# Step 3: 确认/安装 Node.js 24
node -v || {
  curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
  sudo apt install -y nodejs
}

# Step 4: 确认 npm 全局路径可用
npm prefix -g
# 如果路径不在 PATH，手动添加：
# echo 'export PATH=$(npm prefix -g)/bin:$PATH' >> ~/.bashrc
# source ~/.bashrc

# Step 5: 安装 OpenClaw
npm i -g openclaw@latest

# Step 6: 确认安装成功
openclaw --version

# Step 7: 跑诊断（检查依赖）
openclaw doctor --non-interactive

# Step 8: 验证 openclaw 可用
openclaw status
```

---

## 4. 内存优化（2GB 专用）

### 4.1 问题背景

Jetson Nano 2GB 只有 **1.9GB 物理内存**，而：
- JetPack 系统占用约 600-800MB
- YOLO 模型加载（FP16）占用约 300-600MB
- MediaPipe 占用约 200-400MB
- OpenClaw Node Host 占用约 100-200MB

**裸机内存严重不足，必须配置 Swap**。

### 4.2 Swap 配置（2GB 专用最优方案）

> **目标**：总可用内存（物理 + swap）≥ 4GB

```bash
# ========== Swap 配置完整脚本 ==========

# Step 1: 检查当前 swap
sudo swapon --show
# 预期：空（无 swap）

# Step 2: 创建 4GB swap 文件（推荐放在 /home 或根分区）
sudo fallocate -l 4G /swapfile
# 如果 fallocate 失败（某些文件系统），用 dd：
# sudo dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress

# Step 3: 设置权限（安全必需）
sudo chmod 600 /swapfile

# Step 4: 格式化为 swap
sudo mkswap /swapfile

# Step 5: 启用 swap
sudo swapon /swapfile

# Step 6: 验证
sudo swapon --show
# 输出示例：
# NAME      SIZE  TYPE   USED PRIO
# /swapfile   4G   file   0B   -1

# Step 7: 永久化（开机自动启用）
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# ========== 优化 swappiness ==========
# 2GB 内存场景建议 swappiness=10（减少对 swap 的依赖）
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# ========== 验证总内存 ==========
free -h
# 预期输出：
#               total        used        free      shared  buff/cache   available
# Mem:          1.9Gi       800Mi       300Mi        50Mi       800Mi       1.0Gi
# Swap:         4.0Gi       0B         4.0Gi
```

### 4.3 减少系统内存占用（为 AI 腾空间）

```bash
# ========== 减少 Jetson Nano 系统内存占用 ==========

# 禁用不需要的服务
sudo systemctl disable bluetooth       # 蓝牙（无外设时）
sudo systemctl disable cups            # 打印服务
sudo systemctl disable avahi-daemon   # 网络发现（可选）

# 停用桌面环境（如果用 JetPack SDK Manager 镜像，默认有 GUI）
# 切换到命令行模式
sudo systemctl set-default multi-user.target
# 或保留 GUI 但降低内存：
# sudo systemctl disable gdm3  # 如果用 GNOME

# 设置 GPU 最小内存（仅给 CUDA 用，桌面用最小显存）
# 编辑 /boot/extlinux/extlinux.conf 或 /boot/config.txt
# Jetson 专用：使用 nvpmodel 限制功率模式
sudo nvpmodel -m 1  # 5W 模式（限制 CPU 频率，省内存）
# m0 = MAXN (10W, 4核全速)
# m1 = 5W (2核, 限制频率)

# 设置 NVIDIA GPU 最小显存（释放给系统）
sudo systemctl restart nvzglconfig || true
# 注：Jetson Nano 2GB 显存是物理内存共享，无需单独配置
```

### 4.4 FP16 配置（TensorRT）

> **核心约束**：Jetson Nano 2GB 的 Maxwell GPU **不支持 INT8**，只能使用 FP16

```bash
# ========== 验证 TensorRT 可用 ==========
python3 -c "import tensorrt; print(tensorrt.__version__)"
# JetPack 4.x → TensorRT 8.x
# JetPack 5.x → TensorRT 8.x / 9.x

# 检查 Python tensorrt
python3 -c "import uff; print('UFF available')" 2>/dev/null || echo "UFF not available"

# ========== YOLO FP16 推理配置 ==========
# 使用 ONNX + TensorRT 加速时，强制 FP16：
# 1. 导出 YOLO 为 ONNX（FP32 导出）
#    yolo export model=yolov8n.pt imgsz=640 format=onnx

# 2. 用 trt conversion 转为 FP16
# 创建转换脚本：trt_convert.py
cat > ~/trt_convert.py << 'EOF'
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit  # noqa: F401

TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

def build_engine(onnx_file, fp16=True):
    """将 ONNX 转为 TensorRT FP16 engine"""
    with trt.Builder(TRT_LOGGER) as builder:
        config = builder.create_builder_config()
        config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1 << 30)  # 1GB
        
        # 关键：启用 FP16（Maxwell 支持）
        if fp16 and builder.platform_has_fast_fp16:
            config.set_flag(trt.BuilderFlag.FP16)
            print("[TRT] FP16 enabled")
        else:
            print("[TRT] FP16 not available, falling back to FP32")
        
        network = builder.create_network(
            flags=1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)  # noqa: E501
        )
        parser = trt.OnnxParser(network, TRT_LOGGER)
        
        with open(onnx_file, 'rb') as f:
            parser.parse(f.read())
        
        engine = builder.build_serialized_network(network, config)
        return engine

if __name__ == '__main__':
    import sys
    onnx_path = sys.argv[1]
    engine = build_engine(onnx_path, fp16=True)
    with open(onnx_path.replace('.onnx', '.trt'), 'wb') as f:
        f.write(engine)
    print(f"[TRT] Engine saved to {onnx_path.replace('.onnx', '.trt')}")
EOF

# 运行转换（注意：转换过程内存消耗大，需要足够 swap）
# python3 ~/trt_convert.py yolov8n.onnx

# ========== Jetson 上 YOLO 模型选择 ==========
# 2GB 内存建议使用最小模型
MODEL_CONFIG="--model yolov8n"        # YOLOv8 nano (3.2M params, ~4MB)
# 备选：yolov8s (11.2M), yolov8n.pt (最小)
# 备选：yolov5s (7.5M params)
```

### 4.5 YOLO + MediaPipe 同时运行最优配置

> **目标**：YOLO（视觉检测）+ MediaPipe（姿态/手势）共存，均衡性能

```bash
# ========== 模型加载策略 ==========

# 策略 1：串行使用（节省内存，推荐）
# 每次只加载一个模型，释放后再加载另一个
# 脚本：~/ai_runner.sh
cat > ~/ai_runner.sh << 'EOF'
#!/bin/bash
# AI 模型串行运行脚本
MODEL_TYPE=$1
IMAGE_PATH=$2

if [ "$MODEL_TYPE" = "yolo" ]; then
    echo "[INFO] Running YOLO detection..."
    python3 ~/run_yolo.py "$IMAGE_PATH"
elif [ "$MODEL_TYPE" = "mediapipe" ]; then
    echo "[INFO] Running MediaPipe pose..."
    python3 ~/run_mediapipe.py "$IMAGE_PATH"
else
    echo "Usage: $0 <yolo|mediapipe> <image_path>"
fi
EOF
chmod +x ~/ai_runner.sh

# 策略 2：共享 GPU 内存池（高级）
# 限制各自最大 GPU 内存使用
# 在 MediaPipe 和 YOLO 代码中同时设置：
#   config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 512 << 20)  # 512MB 上限

# ========== MediaPipe on Jetson ==========
# MediaPipe on Jetson 推荐通过 pip 安装
pip3 install mediapipe
# 或编译 GPU 版本（针对 CUDA）：
#   bazel build --config=cuda //mediapipe/... (需要 CUDA toolkit)

# 验证 MediaPipe
python3 -c "import mediapipe; print('MediaPipe', mediapipe.__version__)"

# ========== OpenClaw Node Host 内存占用最小化 ==========
# 设置 Node.js 堆内存上限（避免 OOM）
echo 'export NODE_OPTIONS="--max-old-space-size=512"' >> ~/.bashrc
source ~/.bashrc
# 这样 openclaw node run 最多使用 512MB Node.js 堆内存

# ========== 内存监控脚本 ==========
cat > ~/monitor_memory.sh << 'EOF'
#!/bin/bash
# 内存监控（配合 crontab 使用）
while true; do
    FREE_RAM=$(free -m | awk 'NR==2{print $7}')
    FREE_SWAP=$(free -m | awk 'NR==3{print $3}')
    echo "$(date): Free RAM=${FREE_RAM}MB, Swap used=${FREE_SWAP}MB"
    
    # 如果空闲 RAM < 200MB，记录警告
    if [ "$FREE_RAM" -lt 200 ]; then
        echo "WARNING: Low memory! RAM=${FREE_RAM}MB"
        logger "OpenClaw Node WARNING: Low memory ${FREE_RAM}MB"
    fi
    sleep 30
done >> /tmp/memory_monitor.log 2>&1
EOF
chmod +x ~/monitor_memory.sh
```

---

## 5. Gateway 对接

### 5.1 Gateway 发现与连接模式

```
Nano 作为节点 → 连接 → Gateway (WebSocket)
```

**Gateway 地址获取**（在 Gateway 主机上执行）：

```bash
# 在 Gateway 机器（MacBook Pro / VPS）上执行：
openclaw config get gateway.bind
# 期望：loopback / lan / tailnet 之一

openclaw config get gateway.port
# 默认为 18789

# 查看 Gateway 绑定地址
openclaw qr --json
# 重要：urlSource 字段告诉你节点应该使用什么地址连接
```

### 5.2 两种 Gateway 部署场景

#### 场景 A：Gateway 在局域网（MacBook Pro 本地）

```bash
# Gateway 主机（MacBook Pro）IP 假设为 192.168.1.100
# 在 Nano 上：
export OPENCLAW_GATEWAY_TOKEN="<your-gateway-token>"
openclaw node run \
  --host 192.168.1.100 \
  --port 18789 \
  --display-name "Jetson-Nano-2GB"
```

#### 场景 B：Gateway 在 VPS（公网可访问）

```bash
# Nano 通过公网地址连接
export OPENCLAW_GATEWAY_TOKEN="<your-gateway-token>"
openclaw node run \
  --host your-vps.example.com \
  --port 18789 \
  --display-name "Jetson-Nano-2GB"
```

#### 场景 C：Gateway 绑定 loopback（默认），Nano 远程连接

**必须通过 SSH 隧道**（因为 Gateway 只监听 127.0.0.1:18789）：

```bash
# 在 Nano 上先建立 SSH 隧道（保持运行）
ssh -N -L 18790:127.0.0.1:18789 user@gateway-host
# 解释：本地 18790 → gateway-host 的 127.0.0.1:18789

# 然后在另一个终端（Nano）执行：
export OPENCLAW_GATEWAY_TOKEN="<your-gateway-token>"
openclaw node run \
  --host 127.0.0.1 \
  --port 18790 \
  --display-name "Jetson-Nano-2GB"
```

### 5.3 获取 Gateway Token

```bash
# 在 Gateway 主机上获取 token
openclaw config get gateway.auth.token
# 或查看 openclaw.json
cat ~/.openclaw/openclaw.json | grep -A2 '"token"'

# 如果未设置，先设置：
openclaw config set gateway.auth.token "your-secure-token"
openclaw gateway restart
```

### 5.4 Node Pairing（配对）— 完整流程

```bash
# ========== Nano 侧（节点）==========
# 设置 token
export OPENCLAW_GATEWAY_TOKEN="your-token-here"

# 运行节点（前台模式，测试用）
openclaw node run \
  --host <gateway-host> \
  --port 18789 \
  --display-name "Jetson-Nano-2GB"

# 预期输出（首次运行）：
# [INFO] Node connecting to ws://<gateway-host>:18789
# [INFO] Device identity: <device-id>
# [INFO] Waiting for pairing approval...

# 保持这个进程运行，在 Gateway 侧审批

# ========== Gateway 侧（主控机器）==========
# 查看待配对设备
openclaw devices list
# 输出示例：
# [
#   {
#     "requestId": "abc123",
#     "deviceId": "nano-device-id",
#     "displayName": "Jetson-Nano-2GB",
#     "role": "node",
#     "status": "pending"
#   }
# ]

# 审批配对
openclaw devices approve abc123

# 验证
openclaw nodes status
# 期望：
# [
#   {
#     "id": "nano-device-id",
#     "displayName": "Jetson-Nano-2GB",
#     "status": "paired",
#     "connected": true
#   }
# ]
```

### 5.5 安装为后台服务（持久化运行）

```bash
# ========== Nano 侧安装为 systemd 服务 ==========
# 先准备好 token 配置
export OPENCLAW_GATEWAY_TOKEN="your-token-here"

# 安装为后台服务
openclaw node install \
  --host <gateway-host> \
  --port 18789 \
  --display-name "Jetson-Nano-2GB"

# 管理服务
openclaw node status
openclaw node stop
openclaw node restart
openclaw node uninstall
```

### 5.6 Exec Approvals（允许节点执行命令）

```bash
# ========== Gateway 侧添加命令白名单 ==========
# 允许 Nano 执行特定命令
openclaw approvals allowlist add --node Jetson-Nano-2GB "/usr/bin/python3"
openclaw approvals allowlist add --node Jetson-Nano-2GB "/usr/local/bin/yolo"
openclaw approvals allowlist add --node Jetson-Nano-2GB "/usr/bin/bash"

# 查看当前白名单
openclaw approvals get --node Jetson-Nano-2GB

# 如果设置为 ask 模式，需要在 Gateway UI 批准每次执行
```

### 5.7 将 Nano 绑定为默认执行节点

```bash
# 在 Gateway 侧（MacBook Pro）：
openclaw config set tools.exec.host node
openclaw config set tools.exec.security allowlist
openclaw config set tools.exec.node "Jetson-Nano-2GB"

# 从 Nano 执行命令示例：
openclaw nodes run --node Jetson-Nano-2GB -- echo "Hello from Nano"
# 期望输出：Hello from Nano
```

---

## 6. 问题与解决方案（9 大类）

### 问题 1：JetPack 版本不兼容

**症状**：
- `nvcc: command not found`
- CUDA 库找不到
- OpenClaw `openclaw doctor` 报 CUDA 警告

**诊断**：
```bash
/usr/local/cuda/bin/nvcc --version
echo $CUDA_HOME
ldconfig -p | grep libcudart
```

**解决方案**：

```bash
# 方案 A：确认 CUDA 在默认路径
ls /usr/local/cuda*/bin/nvcc
# 如果有，创建符号链接：
sudo ln -sf /usr/local/cuda-10.2 /usr/local/cuda

# 方案 B：设置环境变量
cat >> ~/.bashrc << 'EOF'
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
EOF
source ~/.bashrc

# 方案 C：安装缺失的 CUDA Toolkit
sudo apt install cuda-toolkit-10-2
# JetPack 4.x 用户从 NVIDIA 官网下载 CUDA Toolkit 10.2 Runfile
```

---

### 问题 2：内存不足（OOM / Killer）

**症状**：
- `openclaw node run` 突然退出，日志显示 `Killed`
- `dmesg | grep -i "killed process"` 有输出
- Python 报 `MemoryError`
- YOLO 加载时卡死

**诊断**：
```bash
free -h
sudo swapon --show
dmesg | grep -i "out of memory" | tail -5
dmesg | grep -i killed | tail -5
```

**解决方案**：

```bash
# Step 1: 立即启用/增加 swap（如果还没有）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Step 2: 降低 Node.js 堆内存上限
export NODE_OPTIONS="--max-old-space-size=512"

# Step 3: 限制 Python 最大内存
# 在运行 YOLO/MediaPipe 脚本前加：
ulimit -v 1048576  # 1GB 虚拟内存上限

# Step 4: 关闭 GUI 节省内存（如果不用桌面）
sudo systemctl set-default multi-user.target
# 重启后进入纯命令行，节省 ~500MB RAM

# Step 5: 清理缓存
sync && sudo sysctl -w vm.drop_caches=3

# Step 6: 检查是哪个进程最占内存
ps aux --sort=-%mem | head -10
```

---

### 问题 3：GPU 驱动问题

**症状**：
- `nvidia-smi` 报错：`NVIDIA-SMI has failed`
- CUDA 程序报错：`cudaErrorNoDevice`
- `/dev/nvidia0` 不存在

**诊断**：
```bash
ls -la /dev/nvidia*
cat /proc/driver/nvidia/version
nvidia-smi
```

**解决方案**：

```bash
# 方案 A：重新加载 NVIDIA 内核模块
sudo rmmod nvidia
sudo modprobe nvidia
# 或完整重装驱动：
sudo /opt/nvidia/nsight-systems/cli/.../nvidia-smi  # 厂商提供的工具

# 方案 B：检查 Jetson 特定驱动
# Jetson Nano 使用 L4T (Linux for Tegra) 驱动栈
# 驱动在 JetPack 系统镜像中，重刷镜像可能最简单
# 参考：https://developer.nvidia.com/embedded/jetson-nano-2gb-devkit

# 方案 C：验证 GPU 确实被识别
cat /proc/device-tree/nvidia,chip@0/model-name
# 应输出：NVIDIA Tegra X1 或类似
```

---

### 问题 4：OpenClaw 安装失败（依赖问题）

**症状**：
- `npm install -g openclaw` 报错
- `openclaw: command not found`
- `openclaw doctor` 报 Node.js 版本问题

**诊断**：
```bash
node -v
npm -v
npm config get prefix
which node
```

**解决方案**：

```bash
# 方案 A：权限问题（EACCES）
mkdir -p "$HOME/.npm-global"
npm config set prefix "$HOME/.npm-global"
echo 'export PATH=$HOME/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
npm i -g openclaw@latest

# 方案 B：Node.js 版本不兼容
# 卸载旧版本，重新安装 Node 24
# 先卸载：
sudo apt remove nodejs npm -y
# 安装 Node 24：
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt install -y nodejs
node -v  # 确认 v24.x

# 方案 C：PATH 问题
# 找到 openclaw 安装位置
npm prefix -g
# 如果 openclaw 在 /usr/local/bin 但 PATH 没包含，手动添加：
echo 'export PATH=$(npm prefix -g)/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# 方案 D：npm cache 问题
npm cache clean --force
npm i -g openclaw@latest
```

---

### 问题 5：`openclaw node run` 连接失败

**症状**：
- 节点启动后报错：`ECONNREFUSED`
- `WebSocket connection failed`
- 长时间 `Waiting for pairing approval` 但 Gateway 侧没有请求

**诊断**：
```bash
# 测试网络连通性（Nano 侧）
nc -zv <gateway-host> 18789
telnet <gateway-host> 18789

# 检查 Gateway 是否运行（Gateway 侧）
openclaw gateway status
openclaw status

# 检查 token 是否正确
echo $OPENCLAW_GATEWAY_TOKEN

# 检查 Gateway 绑定地址
openclaw qr --json
```

**解决方案**：

```bash
# 方案 A：网络不通 → 防火墙/端口
# 在 Gateway 侧开放端口：
sudo ufw allow 18789/tcp
# 或检查 iptables

# 方案 B：Gateway 只绑定了 loopback → 必须用 SSH 隧道
# 在 Nano 侧：
ssh -N -L 18790:127.0.0.1:18789 user@gateway-host &
# 然后：
openclaw node run --host 127.0.0.1 --port 18790

# 方案 C：token 不匹配
# Gateway 侧重新生成/设置 token：
openclaw config set gateway.auth.token "correct-token"
openclaw gateway restart
# Nano 侧设置环境变量：
export OPENCLAW_GATEWAY_TOKEN="correct-token"

# 方案 D：刷新 pairing（设备 ID 冲突）
# 删除 Nano 上的 node.json，重新发起配对
rm ~/.openclaw/node.json
openclaw node run --host <gateway-host> --port 18789
# 重新配对

# 方案 E：TLS 问题（如果 Gateway 用 wss://）
openclaw node run \
  --host <gateway-host> \
  --port 18789 \
  --tls
```

---

### 问题 6：Swap 配置问题

**症状**：
- `fallocate` 报错：`fallocate failed: Operation not supported`
- swap 文件创建成功但 `swapon` 报错
- 系统启动后 swap 消失

**诊断**：
```bash
df -h /swapfile
ls -la /swapfile
sudo swapon --show
cat /proc/swaps
```

**解决方案**：

```bash
# 方案 A：fallocate 失败 → 用 dd 替代
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 方案 B：文件系统不支持 swap → 换一个目录
# 检查文件系统
df -T /home
# 如果是 FAT32（不支持），创建在 / 根分区：
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress

# 方案 C：启动后 swap 未自动挂载 → 检查 /etc/fstab
# 正确格式：
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
# 验证：
cat /etc/fstab | grep swap

# 方案 D：检查 swap 实际生效
free -h
# 应该看到 Swap 行有 total > 0
```

---

### 问题 7：CUDA 版本不匹配

**症状**：
- `nvcc --version` 显示 CUDA 10.2，但 PyTorch/CuDNN 需要 CUDA 11
- TensorRT import 报错：` libcudart.so.11.0`
- YOLO FP16 推理报错 CUDA 版本不对

**诊断**：
```bash
nvcc --version
python3 -c "import torch; print(torch.version.cuda)"
python3 -c "import tensorrt; print(tensorrt.__version__)"
ldd $(which python3) | grep cuda
```

**解决方案**：

```bash
# 方案 A：统一 CUDA 版本（推荐保持 JetPack 默认版本）
# 不要混用 CUDA 10.2 和 CUDA 11.x
# Jetson Nano 2GB → 保持 CUDA 10.2

# 方案 B：安装匹配 CUDA 版本的 PyTorch
# JetPack 4.6 (CUDA 10.2) 专用 PyTorch：
pip3 install torch==1.13.1+cu116 torchvision==0.14.1+cu116 \
  --extra-index-url https://download.pytorch.org/whl/cu116
# 或使用预编译的 Jetson 专用 wheel：
# 从 NVIDIA NGC 下载对应 JetPack 版本的 PyTorch

# 方案 C：设置正确的 LD_LIBRARY_PATH
cat >> ~/.bashrc << 'EOF'
export CUDA_HOME=/usr/local/cuda-10.2
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
EOF
source ~/.bashrc

# 方案 D：TensorRT 版本确认
dpkg -l | grep TensorRT
# JetPack 4.x 通常带 TensorRT 8.x
# 如果需要更新：
# wget https://developer.nvidia.com/tensorrt/download
```

---

### 问题 8：存储空间不足

**症状**：
- `apt install` 报错：`E: You don't have enough free space`
- `npm install` 报错：`ENOSPC`
- 系统日志：`Disk full`

**诊断**：
```bash
df -h /
df -h /home
df -h /tmp
```

**解决方案**：

```bash
# 方案 A：清理 apt 缓存（最有效）
sudo apt clean
sudo apt autoremove -y
sudo rm -rf /var/cache/apt/archives/*
du -sh /var/cache/apt/archives

# 方案 B：清理旧内核（释放 /boot 分区）
dpkg --list | grep linux-image
sudo apt remove --purge linux-image-unsigned-*  # 保留最新内核
sudo apt autoremove -y
sudo update-grub

# 方案 C：清理 pip 缓存和旧包
pip3 cache purge
rm -rf ~/.cache/pip

# 方案 D：清理 Jetson SDK Manager 缓存
sudo rm -rf ~/nvidia/nvidia_sdk_download/
rm -rf ~/.local/share/Trash/*

# 方案 E：扩展存储（SD 卡 / USB SSD）
# 检测外置存储
lsblk
# 格式化并挂载到 /opt（存放大文件）
sudo mkfs.ext4 /dev/sda1
sudo mkdir -p /opt
sudo mount /dev/sda1 /opt
# 将大文件移到 /opt
sudo mv ~/models /opt/
sudo ln -s /opt/models ~/models

# 方案 F：Docker 镜像清理（如果用了 Docker）
sudo docker system prune -a -f
```

---

### 问题 9：YOLO / MediaPipe 运行不稳定

**症状**：
- YOLO 推理卡顿（>10s/帧）
- MediaPipe 报错 `GpuNotAvailable`
- 两个同时运行时系统崩溃

**诊断**：
```bash
# GPU 利用率
nvidia-smi dmon -s u
# 查看哪个进程占 GPU
nvidia-smi

# 内存使用
free -h
# 实时监控
watch -n 1 free -h
```

**解决方案**：

```bash
# 方案 A：降低 YOLO 分辨率
# 在 YOLO 推理时用更小的输入尺寸：
yolo detect predict model=yolov8n.pt source=camera.jpg imgsz=320
# imgsz=320 比 imgsz=640 减少约 75% GPU 内存

# 方案 B：GPU 进程隔离（YOLO 和 MediaPipe 不同时用 GPU）
# 方案 1：串行执行（推荐）
python3 run_yolo.py && python3 run_mediapipe.py

# 方案 2：错峰执行
# 每 5 分钟 YOLO 检测，之间执行 MediaPipe

# 方案 C：限制 MediaPipe GPU 内存
# 在 MediaPipe 代码中设置：
#   base_options.delegate = BaseOptions.DELEGATE_CPU  # 强制用 CPU
# 或仅在 CPU 不足时才用 GPU

# 方案 D：NVIDIA 功率模式限制
# 切换到低功率模式（限制性能但省内存）
sudo nvpmodel -m 1  # 5W 模式（推荐用于 2GB）
# 恢复：
# sudo nvpmodel -m 0  # 10W 模式

# 方案 E：cgroup 内存限制（高级）
# 编辑 /etc/systemd/system.conf：
# DefaultLimitMEMLOCK=infinity
# 然后重启
```

---

## 7. 验证方法

### 7.1 节点连接状态验证

```bash
# ========== Nano 侧验证 ==========
# 确认节点正在运行
openclaw node status
# 期望：status=running, connected=true

# 查看节点日志
journalctl --user -u openclaw-node -f
# 或
cat ~/.openclaw/logs/node.log

# ========== Gateway 侧验证 ==========
# 查看节点列表
openclaw nodes status
# 期望：
# ID        | Name              | Status  | Capabilities
# ---------|-------------------|---------|-------------------
# nano-xxx | Jetson-Nano-2GB   | paired  | system.run, system.which

# 查看节点详情
openclaw nodes describe --node Jetson-Nano-2GB
# 期望：显示 connected=true, role=node

# ========== 端到端命令测试 ==========
# 从 Gateway 向 Nano 发送命令
openclaw nodes run --node Jetson-Nano-2GB -- uname -a
# 期望：返回 Nano 的内核信息（Linux aarch64）

openclaw nodes run --node Jetson-Nano-2GB -- free -h
# 期望：显示 Nano 的内存状态

openclaw nodes run --node Jetson-Nano-2GB -- nvidia-smi
# 期望：返回 Nano 的 GPU 信息
```

### 7.2 Gateway Token 验证

```bash
# ========== Gateway 侧 ==========
# 查看当前 token
openclaw config get gateway.auth.token
# 确认非空

# 测试 Gateway 健康状态
openclaw health
# 期望：gateway=status: ok

# ========== Nano 侧 ==========
# 测试 token 认证
OPENCLAW_GATEWAY_TOKEN="your-token" openclaw nodes status
# 如果 token 正确，应返回节点信息
# 如果错误，报 AUTH_ERROR
```

### 7.3 视觉 AI 能力验证

```bash
# ========== YOLO 推理测试 ==========
# 在 Nano 上：
python3 -c "
import cv2
print('OpenCV:', cv2.__version__)
"

# YOLO ONNX FP16 测试
# python3 ~/test_yolo_fp16.py  # 自定义测试脚本
# 期望：FPS > 10（640x640 输入）

# ========== MediaPipe 测试 ==========
python3 -c "
import mediapipe as mp
print('MediaPipe:', mp.__version__)
mp_pose = mp.solutions.pose.Pose()
print('Pose model loaded OK')
"

# ========== 节点 invoke 测试（从 Gateway 调用 Nano AI）==========
# 在 Gateway 侧：
openclaw nodes invoke \
  --node Jetson-Nano-2GB \
  --command system.run \
  --params '{"command": "python3 -c \"import cv2; print(cv2.__version__)\""}'
```

### 7.4 完整链路验证检查单

| 检查项 | 命令 | 期望结果 |
|--------|------|----------|
| Node 进程运行 | `openclaw node status` | `status=running` |
| Gateway 收到连接 | `openclaw nodes status` | Nano 显示 `connected=true` |
| 设备已配对 | `openclaw devices list` | Nano 状态 `approved` |
| Token 有效 | `openclaw health` | `status: ok` |
| 节点可执行命令 | `openclaw nodes run --node Jetson-Nano-2GB -- echo hi` | 返回 `hi` |
| GPU 可用 | `openclaw nodes run --node Jetson-Nano-2GB -- nvidia-smi` | GPU 信息 |
| Swap 正常 | `openclaw nodes run --node Jetson-Nano-2GB -- free -h` | Swap 显示 > 0 |
| CUDA 可用 | `openclaw nodes run --node Jetson-Nano-2GB -- nvcc --version` | 版本号 |

---

## 8. 架构定位

### 8.1 Nano 和 Gateway 的通信方式

```
┌─────────────────────────────────────────────────────────┐
│                      Gateway (WebSocket Server)            │
│                    监听: 0.0.0.0:18789                    │
│                  协议: WebSocket + JSON                   │
│               认证: Token / Password                       │
└──────────────────────────┬──────────────────────────────┘
                           │
                    WebSocket (wss:// 或 ws://)
                    加密: TLS (可选) / 明文 (内网)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                   │
        ▼                  ▼                   ▼
┌──────────────┐  ┌────────────────┐  ┌──────────────────┐
│  MacBook Pro  │  │   VPS 节点    │  │  Jetson Nano 2GB │
│  (Operator)   │  │   (Node)      │  │    (Node)        │
└──────────────┘  └────────────────┘  └──────────────────┘
```

**通信协议**：`WebSocket` + JSON over TCP (port 18789)

**关键点**：
- Gateway 是唯一的 WebSocket 服务器
- 节点（Nano）是 WebSocket **客户端**
- 节点声明 `role: "node"`，Gateway 声明 `role: "operator"`
- 节点通过 `node.invoke` 暴露能力（`system.run`, `camera.*`, `canvas.*`）
- Gateway 通过 `exec host=node` 路由命令到 Nano

### 8.2 数据流

```
用户消息 (Telegram/Discord/WebChat)
    │
    ▼
Gateway (接收消息，路由给 Agent)
    │
    ▼
Agent 决定调用 AI 能力
    │
    ├─► 直接响应（Cloud LLM）
    │
    └─► node.invoke (YOLO/MediaPipe 推理请求)
            │
            ▼
        Nano (执行推理)
            │
            ▼
        结果返回 Gateway
            │
            ▼
        Gateway 响应用户
```

### 8.3 Node Host 配置文件

```bash
# Nano 上的节点配置存储
cat ~/.openclaw/node.json
# 格式：
{
  "id": "nano-device-fingerprint",
  "displayName": "Jetson-Nano-2GB",
  "gateway": {
    "host": "192.168.1.100",
    "port": 18789
  },
  "token": "device-pairing-token",
  "nodeApiToken": "..."
}

# Exec approvals 存储
cat ~/.openclaw/exec-approvals.json
# 格式：
{
  "mode": "allowlist",  // 或 "ask"
  "allowlist": [
    "/usr/bin/python3",
    "/usr/local/bin/yolo"
  ]
}
```

### 8.4 与其他节点类型的对比

| 特性 | iOS/Android 节点 | macOS 节点 | Jetson Nano 节点 |
|------|-----------------|------------|-----------------|
| 运行模式 | App 前台 | 菜单栏 App | Headless (`node run`) |
| GPU 加速 | 有限 | 有限 | **完整 CUDA/TensorRT** |
| YOLO 推理 | ❌ 困难 | ❌ 困难 | ✅ **推荐** |
| MediaPipe | 部分支持 | 部分支持 | ✅ **完整** |
| 节点安装 | App 内扫码 | 菜单栏设置 | CLI `node install` |
| 配对方式 | QR 码 | 自动发现 | CLI `devices approve` |

---

## 附录：完整一键部署脚本

```bash
#!/bin/bash
# deploy_openclaw_nano.sh
# 用途：在 Jetson Nano 2GB 上一键部署 OpenClaw Node

set -e

echo "[1/8] 检查系统环境..."
uname -m | grep -q aarch64 || { echo "ERROR: Not ARM64"; exit 1; }
free -h | grep Mem

echo "[2/8] 安装 Node.js 24..."
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt install -y nodejs
node -v

echo "[3/8] 安装 OpenClaw..."
npm i -g openclaw@latest
openclaw --version

echo "[4/8] 配置 Swap 4GB..."
if ! sudo swapon --show | grep -q /swapfile; then
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
free -h

echo "[5/8] 优化内存（关闭不需要的服务）..."
sudo systemctl disable bluetooth 2>/dev/null || true
sudo systemctl disable cups 2>/dev/null || true
sudo nvpmodel -m 1  # 5W 模式

echo "[6/8] 设置 Node 堆内存限制..."
echo 'export NODE_OPTIONS="--max-old-space-size=512"' >> ~/.bashrc

echo "[7/8] 验证 OpenClaw..."
export PATH=$(npm prefix -g)/bin:$PATH
openclaw doctor --non-interactive

echo "[8/8] 等待 Gateway 配对..."
echo "请在 Gateway 机器上执行："
echo "  openclaw devices list"
echo "  openclaw devices approve <requestId>"
echo ""
echo "然后在 Nano 上运行："
echo "  export OPENCLAW_GATEWAY_TOKEN='your-token'"
echo "  openclaw node install --host <gateway-ip> --port 18789 --display-name 'Jetson-Nano-2GB'"
echo ""
echo "[DONE] 部署完成！"
```

---

## 补充内容（基于映射报告 v2）

### 补充 1：多 Agent 并行感知处理（Phase 2 优化）

映射报告 v2 描述了多 Agent 协作架构，Jetson Nano 作为视觉节点可参与并行处理：

```
主 Agent（贵庚大脑）
  ├── Sub-agent 1（视觉分析）→ ESP32-Cam RTSP → Nano YOLO 推理
  ├── Sub-agent 2（语音合成）→ Edge-TTS
  └── Sub-agent 3（运动控制）→ MQTT Cyber Bricks
```

**配置方式**：
```json5
{
  agents: {
    defaults: {
      subagents: {
        maxSpawnDepth: 2,          // 允许嵌套
        maxConcurrent: 8,          // 并行数量
        runTimeoutSeconds: 900,    // 15 分钟超时
      },
    },
  },
}
```

**对 Nano 的意义**：Nano 上的 YOLO 推理可以作为独立 sub-agent 并行运行，不阻塞主 Agent。

### 补充 2：OpenClaw Skill 模板（可直接复用）

映射报告 v2 提供了可直接创建的 Skill 配置：

**jetson-nano skill**（在 Nano 上执行 Python/SSH）：
```markdown
---
name: jetson-nano
description: 在 Jetson Nano 上执行 AI 推理任务
metadata: {
  "openclaw": {
    "requires": { "bins": ["python3"], "env": ["NANO_HOST"] },
    "primaryEnv": "NANO_HOST",
  }
}
---
```

**esp32-cam skill**（控制 ESP32-Cam）：
```markdown
---
name: esp32-cam
description: 控制 ESP32-Cam 获取图像
metadata: {
  "openclaw": {
    "requires": { "env": ["ESP32_CAM_URL"] },
    "primaryEnv": "ESP32_CAM_URL",
  }
}
---
```

Skill 存放路径：`~/.openclaw/workspace/skills/`

### 补充 3：⚠️ 禁止使用 Bun 安装 OpenClaw（重要警告）

**映射报告 v2 实测警告**：

> 近期 OpenClaw 加强了插件验证机制，**Bun 全局安装路径会触发 "unsafe plugin manifest" 错误**，导致 OpenClaw 无法启动。

**✅ 正确方式**（npm）：
```bash
npm install -g openclaw@latest
```

**❌ 错误方式**：
```bash
bun install -g openclaw   # 会导致启动失败！
```

---

*文档生成时间：2026-03-26*
*补充时间：2026-03-27（基于映射报告 v2）*
*维护建议：每 3 个月检查 OpenClaw 更新和 JetPack 新版本兼容性*

---

## 补充：自定义镜像方案调研（pythops/jetson-image）

> **调研时间**: 2026-03-26  
> **目标**: 评估 https://github.com/pythops/jetson-image 能否解决 Jetson Nano 2GB 安装 Node.js 22+ / OpenClaw 的问题

### 9.1 项目概况

| 指标 | 数据 |
|------|------|
| Stars / Forks | 546 / 143 |
| 最近更新 | 2026-03-24（极活跃） |
| 许可证 | AGPLv3 |
| 支持 Nano 2GB | ✅ 明确支持 |

### 9.2 核心发现

**好消息**：
- pythops/jetson-image **确实支持 Jetson Nano 2GB**
- 可构建 **Ubuntu 22.04** 镜像（比官方 JetPack 4.6.1 的 Ubuntu 18.04 新）
- 提供 **L4T 32.x 和 35.x** 两个选择
- 极简镜像，RAM 占用极低

**坏消息**：
- ❌ Nano 2GB **最高只能用 Ubuntu 22.04**，无法用 24.04
- ❌ Ubuntu 22.04 ≠ Node.js 22+ 直接可用
- ⚠️ **预编译 Node.js 22 ARM64 二进制因 MTE（Memory Tagging Extension）问题无法在 Nano 上运行**
- ⚠️ **仍需从源码编译 Node.js 22**（约27小时，MTE 补丁）

### 9.3 pythops/jetson-image vs 官方 JetPack 4.6.1

| 对比项 | JetPack 4.6.1 | pythops/jetson-image (Nano 2GB + Ubuntu 22.04) |
|--------|--------------|----------------------------------------------|
| Ubuntu 版本 | 18.04 | 22.04 ✅ |
| 构建复杂度 | 低（直接烧录） | 中（需 Linux 主机构建） |
| 预装 CUDA | ✅ | ❌ 需手动 apt install |
| 官方支持 | ✅ | ❌ |
| Node.js 22 编译 | 需编译（~27小时） | 需编译（但系统库更新，略有优势） |
| 硬件稳定性 | 完美 | ⚠️ 可能有问题 |

### 9.4 最终结论

**pythops/jetson-image 对 OpenClaw 部署的价值：有限**

1. Ubuntu 22.04 比 18.04 新，但**仍解决不了 MTE 问题**
2. 即使换了 Ubuntu 22.04，仍需从源码编译 Node.js 22（~27小时）
3. 如果有 Linux 构建主机，可以尝试；否则不必专门为此搭环境
4. **最务实的方案仍是**：官方 JetPack 4.6.1 + NVM 源码编译 Node 22 + npm 安装 OpenClaw

### 9.5 重要警告（2026-03 实测）

**不要用 Bun 安装 OpenClaw！**

近期 OpenClaw 加强了插件验证机制，Bun 全局安装路径会触发"unsafe plugin manifest"错误，导致无法启动。

✅ **正确方式**：
```bash
# 编译好 Node.js 22 后，用 npm 全局安装
npm install -g openclaw@latest
```

### 9.6 参考文档

- 项目主页：https://github.com/pythops/jetson-image
- 详细调研报告：`Jetson-Nano-Custom-Image-Research.md`（同目录）
- NVIDIA 官方 L4T 归档：https://developer.nvidia.com/embedded/jetson-linux-archive
