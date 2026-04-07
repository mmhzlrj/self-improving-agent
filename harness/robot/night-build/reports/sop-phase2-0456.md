# Phase 2 §3 Jetson环境配置 - CUDA/cuDNN

> 整理自 ROBOT-SOP.md Phase 2 视觉记录模块相关章节
> 涉及内容：系统安装、ROS 2、TensorRT、YOLO 部署、MediaPipe、RTSP

## 前提条件

| 项目 | 要求 |
|------|------|
| 硬件 | Jetson Nano 2GB（B01 量产模块，非 4GB 开发套件） |
| 系统 | JetPack 5.x（L4T 35.x） |
| 存储 | ≥32GB SD 卡 |
| 网络 | 与 Mac 同一局域网 |

> ⚠️ **重要**：2GB 版本内存更小，跑 YOLO 更容易 OOM（内存溢出），优化方向与 4GB 版本完全不同。2GB 必须开启 swap 才能同时跑 YOLO + MediaPipe，且 GPU 加速仅支持 FP16（Maxwell 不支持 INT8）。

---

## 步骤

### Step A: 系统安装与基础配置

**A.1 下载并烧录 JetPack 镜像**

```bash
# 1. 下载 JetPack 5.x 镜像
# 官方: https://developer.nvidia.com/embedded/jetpack
# 社区: https://github.com/pythops/jetson-image
# 讨论: https://github.com/topics/jetson-nano-2gb

# 2. 用 balenaEtcher 烧录 SD 卡
```

**A.2 基础系统配置**

```bash
# 换阿里云源（加速）
sudo sed -i 's/cn.archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list
sudo apt update

# 开启 SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# 记录 IP
hostname -I
```

**A.3 从 Mac 连接 Jetson Nano**

```bash
# 默认用户名 jetson，密码 jetson（首次启动需先通过 HDMI+键盘设置）
ssh jetson@<Jetson_IP>

# 或使用密钥认证（推荐）：
ssh-copy-id jetson@<Jetson_IP>
```

**A.4 开启 SWAP（2GB 版本必做）**

```bash
# 方法1: 使用 dphys-swapfile
sudo apt install -y dphys-swapfile
sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=4096/' /etc/dphys-swapfile
sudo systemctl enable dphys-swapfile
sudo systemctl start dphys-swapfile

# 方法2: 手动创建
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

### Step B: ROS 2 Foxy 安装（精简版）

**B.1 添加 ROS 2 源**

```bash
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
export LANG=en_US.UTF-8

sudo apt install -y curl gnupg2 lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -

# 添加源（注意版本对应）
# Jetson Nano 2GB + JetPack 5.x → Ubuntu 20.04 → ROS 2 Foxy
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu focal main" > /etc/apt/sources.list.d/ros-latest.list'
sudo apt update
```

**B.2 安装 ros-base（仅核心，无 GUI）**

```bash
sudo apt install -y ros-foxy-ros-base python3-argcomplete
sudo apt install -y python3-rosdep
sudo rosdep init
rosdep update

echo "source /opt/ros/foxy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

**资源占用**：

| 组件 | 内存占用 | 说明 |
|------|---------|------|
| ROS 2 Foxy core | ~300-400MB | 仅核心，无 GUI |
| 完整 ros-base | ~600-800MB | 包含 rclcpp / rclpy / msgs |

**优化建议**：永远只装 `ros-foxy-ros-base`，用远程 rviz2 或手机/平板做可视化。

---

### Step C: CUDA/cuDNN 环境验证与 TensorRT 安装

**C.1 验证 CUDA 已预装**

```bash
# 检查 CUDA 版本（JetPack 已包含）
nvcc --version

# 检查 cuDNN
cat /usr/include/cudnn_version.h | grep CUDNN_MAJOR -A 2

# 检查 TensorRT
dpkg -l | grep TensorRT
# 或
python3 -c "import tensorrt; print(tensorrt.__version__)"
```

**C.2 安装 GStreamer（视频pipeline）**

```bash
sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-bad
```

**C.3 安装 Python AI 依赖**

```bash
# 安装 PyTorch（ Jetson 专用版本）
# 参考: https://forums.developer.nvidia.com/t/pytorch-for-jetson/72050
# 下载对应 JetPack 版本的 wheel 文件
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu102

# 安装 ONNX Runtime
pip3 install onnxruntime

# 安装 transformers（用于 Gemma Embedding）
pip3 install transformers sentence-transformers
```

---

### Step D: YOLO + TensorRT FP16 部署（Nano 2GB 必读）

> ⚠️ **关键**：2GB 版本 GPU 加速仅支持 FP16，Maxwell 架构不支持 INT8

**D.1 安装 TensorRT**

```bash
# TensorRT 通常随 JetPack 预装
# 如需手动安装：
# 下载 TensorRT GA: https://developer.nvidia.com/tensorrt/download
sudo dpkg -i nv-tensorrt-repo-*_amd64.deb
sudo apt update
sudo apt install -y tensorrt
python3 -c "import tensorrt; print(tensorrt.__version__)"
```

**D.2 YOLO 模型转换为 TensorRT FP16**

```bash
# 1. 安装 ultralytics
pip3 install ultralytics

# 2. 转换 YOLOv5n 为 TensorRT FP16
python3 << 'EOF'
import torch
from ultralytics import YOLO

# 加载模型
model = YOLO('yolov5nu.pt')

# 导出为 TensorRT FP16
# 注意：2GB 版本建议用 yolov5n/yolov8n，不要用 larger 模型
model.export(format='engine', half=True, imgsz=640)
EOF

# 或使用 trtexec 命令行
# /usr/src/tensorrt/bin/trtexec --onnx=yolov5n.onnx --engine=yolov5n.engine --fp16
```

**D.3 性能参考（Jetson Nano 2GB 实测）**

| 模型 | FPS | 内存 |
|------|-----|------|
| YOLOv5n + TensorRT FP16 | ~15-20 FPS | ~1-1.5 GB |
| YOLOv8n + TensorRT FP16 | ~10-15 FPS | ~1.5-2 GB |

**D.4 替代方案：ONNX + ncnn（如果 TensorRT 失败）**

```bash
# 导出为 ONNX
model.export(format='onnx')

# ncnn 推理（CPU，不依赖 GPU）
# 适合 2GB 内存紧张场景
```

---

## 验证

### 1. CUDA 环境验证

```bash
# CUDA 版本
nvcc --version
# 预期输出: cuda_11.8.r11.8

# cuDNN 版本
cat /usr/include/cudnn_version.h | grep CUDNN_MAJOR -A 2
# 预期输出: CUDNN_MAJOR 8, CUDNN_MINOR 6, CUDNN_PATCHLEVEL 0

# TensorRT 版本
python3 -c "import tensorrt; print(tensorrt.__version__)"
# 预期输出: 8.x.x
```

### 2. ROS 2 验证

```bash
source /opt/ros/foxy/setup.bash
ros2 run rclcpp_components component_container &
ros2 component list
# 预期输出包含 component_container
```

### 3. YOLO TensorRT 推理验证

```bash
python3 << 'EOF'
import cv2
from ultralytics import YOLO

# 加载 TensorRT engine
model = YOLO('yolov5n.engine')

# 测试推理
results = model.predict(source=0, verbose=False)
print(f"推理成功，检测到 {len(results[0].boxes)} 个目标")
EOF
```

### 4. RTSP 流接收验证

```bash
# 测试接收 ESP32-Cam RTSP 流
ffplay rtsp://192.168.x.99:8554/stream

# 或用 GStreamer
gst-launch-1.0 rtspsrc location=rtsp://192.168.x.99:8554/stream \
  ! decodebin ! videoconvert ! autovideosink
```

---

## 常见问题

### Q1: Jetson Nano 2GB 跑 YOLO 内存溢出 OOM

**原因**：2GB 内存太小，同时跑模型 + 视频解码 + ROS 会爆内存

**解决方案**：
1. 开启 4GB SWAP（见 Step A.4）
2. 只跑 YOLO，不同时开 ROS
3. 使用 yolov5n/yolov8n，不要用 yolov5s/yolov8s
4.降低分辨率：`imgsz=320`

### Q2: TensorRT FP16 转换失败

**原因**：Maxwell 架构不支持 INT8

**解决方案**：
1. 确认导出时使用 `--fp16`，不是 `--int8`
2. 检查模型大小，2GB 版本只能跑最小的模型
3. 备选方案：用 ONNX + ncnn（CPU 推理）

### Q3: MediaPipe 在 Jetson Nano 2GB 上性能差

**原因**：MediaPipe GPU 加速不成熟

**解决方案**：
1. 用 TensorRT + MobileNet 替代 MediaPipe Pose/手势
2. 或用 ncnn + Vulkan 后端

### Q4: USB 耳机无法录音

**原因**：默认音频设备是板载 MIC

**解决方案**：
```bash
# 查看设备
arecord -l      # 列出录音设备
aplay -l        # 列出播放设备

# USB 耳机通常是 card 1，创建 ~/.asoundrc
cat > ~/.asoundrc << 'EOF'
pcm.!default {
  type hw
  card 1
}
ctl.!default {
  type hw
  card 1
}
EOF
```

### Q5: WiFi 断开连不上

**原因**：驱动问题

**解决方案**：
```bash
sudo apt install linux-firmware
sudo reboot
```

### Q6: ROS 2 节点无法通信

**检查步骤**：
```bash
# 1. 检查环境变量
source /opt/ros/foxy/setup.bash
echo $ROS_DOMAIN_ID

# 2. 测试通信
ros2 topic list

# 3. 检查防火墙
sudo ufw allow 11811/udp
```
