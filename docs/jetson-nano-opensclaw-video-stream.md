# Jetson Nano + OpenClaw 视频流接入方案

> 创建时间：2026-03-07
> 更新：2026-03-07 新增 NVIDIA DeepStream 方案

---

## 背景

目标：将 Jetson Nano 2GB 的 CSI 摄像头视频流接入 OpenClaw，实现实时视频分析。

限制条件：
- Jetson Nano 2GB 无法安装 Node.js 22（方案一不可行）
- 需要低延迟（20-30fps）

---

## 一、数据流架构

```
Jetson Nano CSI摄像头
    ↓ GStreamer RTSP 推流 (20-30fps)
Mac 接收 RTSP 流
    ↓ Python 脚本截帧 → HTTP 接口
OpenClaw exec 调用 → 本地/云端模型分析
```

---

## 二、Jetson Nano 推流方案

### 2.1 GStreamer RTSP 推流命令

```bash
# 安装依赖
sudo apt install libgstrtspserver-1.0-dev gstreamer1.0-tools

# 推流命令 (RTSP)
gst-launch-1.0 nvarguscamerasrc sensor_id=0 ! \
'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! \
nvvidconv ! video/x-raw ! \
x264enc speed-preset=ultrafast tune=zerolatency ! \
rtph264pay name=pay0 pt=96 ! \
udpsink host=<Mac-IP> port=5000
```

### 2.2 推荐参数

| 参数 | 推荐值 |
|------|--------|
| 分辨率 | 1280x720 |
| 帧率 | 30fps |
| 编码 | x264 ultrafast + zerolatency |
| 传输协议 | UDP |
| 码率 | 2000-4000 kbps |
| 延迟 | < 100ms |

---

## 三、Mac 接收端方案

### 3.1 GStreamer 接收

```bash
brew install gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly

# 接收命令
gst-launch-1.0 rtspsrc location=rtsp://<jetson-ip>:8554/stream latency=100 ! \
rtph264depay ! h264parse ! avdec_h264 ! autovideosink
```

### 3.2 Python OpenCV 接收 + HTTP 服务

```python
# rtsp_receiver.py
import cv2
from flask import Flask, send_file
import io
import threading

app = Flask(__name__)
rtsp_url = "rtsp://<jetson-ip>:8554/stream"

def keep_stream_alive():
    cap = cv2.VideoCapture(rtsp_url)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream lost, reconnecting...")
            cap = cv2.VideoCapture(rtsp_url)

# 启动保活线程
threading.Thread(target=keep_stream_alive, daemon=True).start()

@app.route('/frame')
def get_frame():
    cap = cv2.VideoCapture(rtsp_url)
    ret, frame = cap.read()
    cap.release()
    if ret:
        _, img_encoded = cv2.imencode('.jpg', frame)
        return send_file(io.BytesIO(img_encoded.tobytes()), mimetype='image/jpeg')
    return "No frame", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### 3.3 FFmpeg 截帧命令

```bash
# 从 RTSP 流截取单帧
ffmpeg -i rtsp://<jetson-ip>:8554/stream -vframes 1 -q:v 2 /tmp/jetson_frame.jpg

# 从 HTTP 接口获取
curl -s http://localhost:8080/frame > /tmp/jetson_frame.jpg
```

---

## 四、OpenClaw 集成

### 4.1 当前方案（云端模型）

- 使用 MiniMax M2.5 的 imageModel 进行分析
- 通过 exec 调用 FFmpeg 截帧

### 4.2 本地方案（RTX 2060）

详见第五章

---

## 五、RTX 2060 本地模型方案

### 5.1 推荐模型

| 模型 | 参数量 | 显存需求 | 推荐度 |
|------|--------|----------|--------|
| **Moondream** | 1.8B | ~2GB | ⭐⭐⭐ 最小最省 |
| **MiniMind-V** | 26M-104M | 0.6-1.1GB | ⭐⭐⭐ 极致轻量 |
| **MiniCPM-V** | 8B | ~4GB | ⭐⭐ 高效 |
| **LLaVA 7B (4-bit)** | 7B | ~6GB | ⭐⭐ 主流 |
| **Qwen2.5-VL-7B** | 7B | ~6GB | ⭐⭐ 阿里最强 |

### 5.2 Ollama 部署（推荐）

**安装：**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**运行模型：**
```bash
ollama run llava
ollama run qwen2.5vl
ollama run moondream
ollama run minicpm-v
```

### 5.3 OpenClaw 配置

```json5
{
  agents: {
    defaults: {
      imageModel: { primary: "ollama/llava" }
    }
  }
}
```

**环境变量：**
```bash
export OLLAMA_API_KEY="ollama-local"
```

**API 地址：** `http://localhost:11434`

---

## 六、NVIDIA DeepStream 方案（边缘 AI 推理）

### 6.1 DeepStream SDK 简介

NVIDIA DeepStream 是基于 GStreamer 的实时视频分析工具包，专为边缘 AI 设计：

- **40+ 硬件加速插件**
- **支持 Jetson 全系列**（Nano, Xavier NX, AGX Orin）
- **支持模型**：YOLO、RT-DETR、PeopleNet、DINOv2 等

### 6.2 核心插件

| 插件 | 用途 |
|------|------|
| `gst-nvinference` | TensorRT AI 推理 |
| `nvtracker` | 多摄像头追踪 |
| `nvdsosd` | 屏幕标注（框选、文字） |
| `nvdsasr` | 音频/语音识别 |

### 6.3 jetson-inference 库

```python
import jetson.inference
import jetson.utils

# 目标检测
net = jetson.inference.detectNet("ssd-mobilenet-v2")
camera = jetson.utils.gstCamera(1280, 720, "0")
img, width, height = camera.CaptureRGBA()
detections = net.Detect(img, width, height)
```

### 6.4 推荐模型（Jetson Nano 2GB）

| 模型 | 任务 | 帧率 |
|------|------|------|
| MobileNet-V2-SSD | 目标检测 | ~20-30 FPS |
| ResNet-18 | 图像分类 | ~25-30 FPS |
| FCN-ResNet18 | 语义分割 | ~10-15 FPS |
| PoseNet | 姿态估计 | ~15-20 FPS |

### 6.5 入门资源

- **Hello AI World**：https://github.com/dusty-nv/jetson-inference
- **JetPack 版本**：最后支持 Jetson Nano 的是 JetPack 4.6.4

---

## 七、双视频流输出方案

### 7.1 GStreamer Tee 分支

使用 `tee` 元素同时输出两个视频流：

```bash
gst-launch-1.0 \
  nvarguscamerasrc sensor_id=0 ! \
  video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1 ! \
  tee name=t \
  t. ! queue ! rtph264pay ! udpsink host=<Mac-IP> port=5000 \
  t. ! queue ! nvdsosd display-text=1 ! nvvideoconvert ! rtph264pay ! udpsink host=<Mac-IP> port=5001
```

| 端口 | 视频流 |
|------|--------|
| 5000 | 原始视频流 |
| 5001 | AI 标注后视频流 |

### 7.2 关键元素

- `tee` - 分支 pipeline
- `queue` - 隔离数据流，防止阻塞
- `nvdsosd` - AI 标注（画框、文字）
- `nvvidconv` - NVIDIA 硬件加速转换

---

## 八、最终架构（更新版）

```
┌─────────────────────────────────────────────────────────────┐
│                    Jetson Nano 2GB                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  JetPack 4.6.4 + DeepStream + GStreamer            │   │
│  │                                                     │   │
│  │  CSI 摄像头 → MiniMind-V / SSD-MobileNet            │   │
│  │              → 双流输出 (tee)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│            原始流 (5000)        AI标注流 (5001)            │
└─────────────────────────────────────────────────────────────┘
            ↓                              ↓
┌─────────────────────┐    ┌─────────────────────┐
│     Mac 接收端      │    │   Ubuntu + RTX 2060 │
│  OpenCV/GStreamer  │    │     Ollama/LLaVA    │
│   转发到 OpenClaw  │    │    深度分析 + 判断  │
└─────────────────────┘    └─────────────────────┘
```

### 分工：

1. **Jetson Nano** - 边缘预处理，轻量级 AI 识别（MiniMind-V / SSD-MobileNet）
2. **Mac** - 接收转发，FFmpeg 截帧
3. **RTX 2060** - 深度分析（LLaVA / Qwen2.5-VL）
4. **OpenClaw** - 协调控制，最终决策

---

## 九、MiniMind-V 边缘部署

**MiniMind-V 仅需 0.6-1.1GB 显存**，可以在 Jetson Nano 2GB 上运行做初步识别：

| 模型 | 参数量 | 推理显存 |
|------|--------|----------|
| MiniMind2-Small-V | 26M | 0.6-1.1 GB |
| MiniMind2-V | 104M | 0.6 GB |

---

## 十、待验证事项

- [ ] Jetson Nano 安装 JetPack 4.6.4
- [ ] DeepStream 环境配置
- [ ] MiniMind-V 在 Jetson 上运行
- [ ] 双流输出实际测试
- [ ] 与 OpenClaw 集成测试

---

## 十一、升级计划（后期）

### 11.1 硬件升级

- **Jetson Thor Nano** - 预计 2026 年底上市，将是升级选择
- 性能比 Orin Nano 更强

### 11.2 视频协议

- **WebRTC** - 延迟更低（~100ms）
- **MediaMTX** - 可做 RTSP → WebRTC 协议转换

> ⚠️ **注意**：前期不需要传输视频到让我看到画面。主要目标是让边缘终端有智能能力（具身智能），而非远程监控。

### 11.3 本地模型

- 直接在 OpenClaw 上运行 Ollama
- 不需要额外的服务器

---

## 十二、当前优先级

### 第一阶段：边缘智能（具身智能）

- [ ] Jetson Nano 部署 MiniMind-V
- [ ] DeepStream 环境配置
- [ ] AI 识别结果通过消息传递（不需要视频流）
- [ ] OpenClaw 接收识别结果并决策

### 第二阶段：视频监控（可选）

- [ ] WebRTC 推流
- [ ] Mac 接收转发
- [ ] RTX 2060 深度分析

---

## 相关链接

- 飞书文档：https://feishu.cn/docx/FB1Zd9dnZoTlt3xn9YWcbacHnPe
- OpenClaw 文档：https://docs.openclaw.ai
- GStreamer 文档：https://gstreamer.freedesktop.org
- Ollama：https://ollama.com
- LLaVA：https://github.com/haotian-liu/LLaVA
- jetson-inference：https://github.com/dusty-nv/jetson-inference

---

## 十三、调研工作流 Skill

已创建调研专用 Skill：`~/.openclaw/workspace/skills/deep-research/SKILL.md`

### 两种模式

1. **用户参与模式**：用户给方向，我执行调研
2. **自主模式**：我主动举一反三，多轮深入搜索

### 关键点

- 用户补充信息很重要（他们有我不知道的专业知识）
- 及时文档沉淀（飞书 + 本地）
- 用中文总结结果
- 说明盲区待验证

---

## 十四、Jetson Thor Nano 预测调研（2026-03-07）

### 14.1 调研背景

基于 Orin 系列和 AGX Thor 的规格对比，预测即将发布的 Jetson Thor Nano 规格。

### 14.2 Jetson 历代产品规格

| 产品 | AI性能 | 架构 | 内存 | 功耗 | 价格 |
|------|--------|------|------|------|------|
| Jetson Nano 2GB | ~0.5 TOPS | Maxwell | 2GB | 5-10W | $99 |
| Orin Nano Super | 67 TOPS | Ampere | 8GB | 7-25W | $199 |
| Orin NX 16GB | 117 TOPS | Ampere | 16GB | 10-40W | $399 |
| AGX Orin 64GB | 275 TOPS | Ampere | 64GB | 15-60W | $999 |
| AGX Thor T4000 | 1200 TFLOPS | Blackwell | 64GB | 40-70W | $2,999 |
| AGX Thor T5000 | 2070 TFLOPS | Blackwell | 128GB | 40-130W | $2,999+ |

### 14.3 规律分析

1. **性能阶梯**：Nano → NX → AGX 分别是 67 → 117 → 275 TOPS（约 2x 阶梯）
2. **架构升级**：Orin (Ampere) → Thor (Blackwell) 性能提升 7.5x
3. **Orin Nano Super**：通过提升功耗上限（7W → 25W）实现性能提升 67%

### 14.4 Thor Nano 预测规格

| 规格 | 预测值 | 依据 |
|------|--------|------|
| **AI 性能** | 200-300 TOPS (INT8) | Nano 67 → NX 117 → AGX 275 阶梯，Thor 版预计 3-4x Nano |
| **GPU** | 256-512 核 Blackwell | T4000 1536核 → 按比例缩减 |
| **CPU** | 8核 Neoverse-V3AE | T4000 12核 → 精简版 |
| **内存** | 8-16GB LPDDR5X | 对应 Nano 定位 |
| **功耗** | 15-40W | Orin Nano 7-25W → 升级版 |
| **价格** | $299-499 | Orin Nano Super $199 升级版 |
| **发布时间** | 2026 年底 | 用户消息 |

### 14.5 待验证

- [ ] Thor Nano 实际发布规格
- [ ] 与预测对比

> ⚠️ **注意**：截至调研时（2026-03-07），网上无 Thor Nano 具体爆料，以上为基于规律的预测。

---

## 十五、LTX Studio / LTX 2.3 模型调研（2026-03-07）

### 15.1 简介

LTX Studio 是 AI 视频生成平台，LTX-2 是其开源的多模态 AI 模型。

### 15.2 LTX 2.3 新功能

| 功能 | 说明 |
|------|------|
| 原生 4K 竖屏 | 最高 1080×1920，TikTok/Ins 优化 |
| 关键帧控制 | 定义起点帧到终点帧的运动 |
| 图像转视频改进 | 减少 60% 不可用输出 |
| 音频管道 | 全新声码器，伪影减少 3 倍 |
| 更清晰输出 | VAE 架构重建，细节更好 |
| 提示词理解 | 比前一版本好 4 倍 |

### 15.3 技术规格

| 模式 | 分辨率 | 帧率 | 时长 |
|------|--------|------|------|
| Fast | 1080p/1440p/4K | 24/25/48/50 fps | 最长 20 秒 |
| Pro | 1080p/1440p/4K | 24/25/48/50 fps | 最长 20 秒 |

### 15.4 API 能力

- Text-to-Video：文本生成视频
- Image-to-Video：图像动画化
- Audio-to-Video：音频驱动视频
- Retake：重新生成片段
- Extend：延长视频

### 15.5 部署选项

1. **开源**：模型权重公开，年收入<$1000万免费
2. **API**：托管 API 端点
3. **本地部署**：LTX Desktop / LTX CLI / LTX MCP
4. **商业许可**：年收入>$1000万需付费

### 15.6 OpenClaw 接入方案

1. **通过 exec 调用 CLI**：直接运行 ltx 命令
2. **通过 API**：调用 LTX API
3. **通过 MCP**：如果支持 MCP 协议

### 15.7 待测试

- [ ] LTX 本地部署测试
- [ ] OpenClaw 接入测试

---

*本文档由 AI 助手维护更新*
