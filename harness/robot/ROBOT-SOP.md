# 🤖 0-1 私人 AI 机器人完整实施指南

**项目名**: 0-1（零杠一）
**记忆系统**: 贵庚
**文档版本**: v2.0（重组版）
**创建日期**: 2026-03-07
**更新日期**: 2026-03-21

---

# 第一部分：概念与愿景

## 1.1 项目愿景

**0-1** —— 不是一台机器，是你人生的另一面。

| 层含义 | 说明 |
|--------|------|
| **机器层** | 二进制的起点，代表硅基生命的底层语言 |
| **制造层** | 第一次「从零到一」用 3D 打印制造一个完整的机器人 |
| **生命层** | 人一生的「0 到 1」——从出生到结束，机器的记忆就是我的人生存档 |

0-1 不是一个固定的产品，而是一个会跟着 AI 能力一起长大的伙伴。10 年分五个阶段，每一年，期望和能力都在共同进化。

> 「0-1」还很适合用来做机器人面部的默认表情，且名字简单易记，未来易拓展到「1-2」、「2-3」等。

---

## 1.2 核心系统：贵庚

**贵庚** 是 0-1 的记忆系统，专为保存一个人完整的一生而设计。

- **贵** = 粤语里对他人的敬称，也暗含「珍贵」
- **庚** = 天干第七位，对应时间、年龄、周期——记忆本质上就是时间的切片
- **贵庚** 在粤语里是问老人家年龄的敬语，带着一种对岁月沉淀的敬畏

> 贵庚存的不是数据，是一个人的年龄和尊严。

### 核心价值主张

| 价值 | 说明 | 优先级 |
|------|------|--------|
| **记忆延续（贵庚）** | 帮你记录身边发生的事情，随时回顾 | P0 |
| **陪伴对话** | 随时语音交流，有问必答 | P0 |
| **执行任务** | 帮你完成简单的物理任务 | P1 |
| **安全守护** | 身份认证、防抢防盗、紧急响应 | P1 |
| **数据隐私** | 所有数据本地处理，不传云端 | P0 |

---

## 1.3 核心陪伴理念：从「响应」到「懂你」

0-1 的终极目标不是执行指令，而是**观察你、推理你、主动介入**。

```
观察层（摄像头/传感器）
    ↓
行为模式识别（贵庚）
    ↓
意图推理引擎
    ↓
主动执行 / 主动询问
    ↓
你的反馈 → 微调模型
```

### 三个层次

| 层次 | 表现 | 举例 |
|------|------|------|
| **被动响应** | 你说/做，它执行 | "帮我回复微信" |
| **主动提醒** | 它观察到了，提示你 | "你今天还没喝水" |
| **主动执行** | 它推理出来了，直接做 | 你拿起外套，它就知道你要出门 — 顺便帮你拿上没想起来带的东西 |

**最难的其实是「不打扰」**：主动推理最难的不是判断你要什么，而是**判断什么时候不该出声**。

> 贵庚需要学的第一件事不是预测，是**什么时候闭嘴**。

---

## 1.4 10年五阶段路线图

### 最终确认的五阶段

| 阶段 | 时间 | 核心目标 |
|------|------|---------|
| **阶段一** | 1-2年 | OpenClaw + Cyber Bricks 第一次结合，跑通"数字大脑→物理身体"链路 |
| **阶段二** | 3-4年 | 贵庚 MVP + 本地小模型控制物理身体；数字孪生环境训练→现实校验 |
| **阶段三** | 5-6年 | 身体+大脑进化，走出家门进入开放世界，互相守护 |
| **阶段四** | 7-8年 | 多个专家分身融合（线上MoE），各司其职，有摩擦期 |
| **阶段五** | 9-10年 | 线下专家替代线上MoE，经过长期磨合离线也能做好事情 |

**关键区分**：
- 阶段四：多个分身依赖线上 MoE
- 阶段五：贵庚积累足够数据，线下专家替代线上 MoE

---

# 第二部分：硬件体系

## 2.1 现有硬件

| 设备 | 规格 | 数量 | 状态 |
|------|------|------|------|
| Jetson Nano | **2GB**（量产模块，非4GB开发套件）| 1 | 可用 |
| ESP32-Cam | OV2640 | 1 | 可用 |
| Cyber Bricks | ESP32-C3（XA003/XA004/XA005）+ 电机 + 舵机 | 2 | 已有（拓竹赠送）|
| 星闪设备 | 未知型号 | ? | 测试中 |
| 拓竹 H2C | 3D打印机 | 1 | 可用 |
| Ubuntu 台式机 | 5600G+32G+2060 | 1 | 可用（待对接 Gateway）|
| MacBook | OpenClaw Gateway | 1 | 运行中 |

---

## 2.2 需要采购（阶段一 MVP）

| 类别 | 配件 | 预算 |
|------|------|------|
| 语音套件 | 蓝牙耳麦（ESP32-Cam 蓝牙音频）| ¥80~150 |
| 运动套件 | 舵机、电机、轮子等 | ¥229 |
| 传感器 | 超声波、红外、蜂鸣器 | ¥22 |
| 其他 | 杜邦线、面包板、螺丝 | ¥60 |
| **合计** | | **¥391** |

---

## 2.3 电源方案

| 电源 | 规格 | 说明 |
|------|------|------|
| **拓竹 Cyber Tanks 内置电池** | 未知 | 随 Cyber Tanks 套件赠送，优先使用 |
| **小米 20000mAh 充电宝** | 74Wh | 便携，支持快充，可作为移动供电 |

> ⚠️ 扫地机器人电池已报废：进水腐蚀，无修复价值。

**长期目标**：固态户外移动电源，满电支持 ≥24 小时续航（覆盖白天+黑夜完整周期）。

---

## 2.4 梯度采购路线图

| 时间 | 设备 | 理由 | 价格 |
|------|------|------|------|
| **2026-06** | RTX 5050 9GB GDDR7 | 插入现有台式机，跑 Qwen3.5-4B/9B 4-bit | ~2,000元 |
| **Q2** | AMD AI Halo 128GB | 跑 Qwen3.5-122B，本地训练贵庚，618 可能低于1万 | ~10,000-15,000元 |
| **阶段一** | Jetson AGX Thor | 替代 Nano 作为 0-1 主控 | 24,000元 |
| **阶段一** | 全景摄像头 | 360° 视觉冗余 | 3,000元 |
| **阶段一** | NAS | 本地备份贵庚所有 raw data | 3,000元 |
| **可选** | DGX Spark | NVIDIA 官方 OpenClaw 支持，NemoClaw 优化 | ~35,000元 |
| **充裕时** | DGX Station GB300 | 748GB 统一内存，20 PFLOPS | ~70万 |

---

# 第三部分：系统架构

## 3.1 整体架构

```
┌─────────────────────────────────────────┐
│         Ubuntu 台式机 (GPU节点)           │
│  • RTX 2060 GPU 加速                    │
│  • 32GB RAM                            │
└──────────────────┬──────────────────────┘
                   │ openclaw node
                   │ WebSocket
┌──────────────────▼──────────────────────┐
│              家里 Gateway (Mac)          │
│        主 AI (我) + 贵庚 + 任务调度       │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐
   │ Jetson │ │Cyber   │ │Cyber   │
   │ Nano   │ │Brick 1 │ │Brick 2 │
   │(感知)  │ │(执行)  │ │(备用)  │
   └────────┘ └────────┘ └────────┘
        │              │
        ▼              ▼
   ┌────────┐    ┌──────────────────┐
   │ ESP32- │    │   拓竹工具链      │
   │ Cam    │    │ H2C/H2D+Studio   │
   └────────┘    └──────────────────┘
```

### iPhone 接入后的完整拓扑

```
Gateway(MacBook)
    ↓ WiFi/MQTT
iPhone 16 Pro(感知前端) ← OpenClaw Node 协议
    ↓ 有线 UART/I2C/GPIO
Jetson Nano(控制) → ESP32-Cam × 2 + Cyber Bricks
```

---

## 3.2 节点说明

| 节点 | 角色 | 功能 |
|------|------|------|
| Mac Gateway | 主控 | AI大脑、贵庚记忆、任务调度 |
| Ubuntu 台式机 | GPU节点 | 图像理解、GPU密集任务 |
| Jetson Nano | 边缘节点 | 语音交互、视频处理、运动控制 |
| Cyber Bricks ×2 | 运动节点 | 电机控制、动作执行 |
| ESP32-Cam | 视觉节点 | 视频采集、室内建模 |
| iPhone 16 Pro | 无线前端 | 高质量感知、LLM 辅助推理 |

---

## 3.3 通信协议

### 设备内通信

| 协议 | 用途 | 延迟 | 说明 |
|------|------|------|------|
| **MQTT** | 设备间命令传递 | <50ms | 主协议 |
| **WebSocket** | Gateway ↔ 节点 | <20ms | 实时双向 |
| **REST API** | 控制指令 | <100ms | 简单场景 |

### 有线通信（GPIO 层面）

| 协议 | 用途 | Jetson Nano | ESP32-Cam |
|------|------|------------|-----------|
| **UART** | 简单命令传递 | Pin 8(TX)/10(RX) | GPIO1/3 |
| **I2C** | 多设备总线 | Pin 3(SCL)/5(SDA) | GPIO4/5 |
| **GPIO** | 应急停止信号 | Pin 29 等 | 任意 GPIO |

> **关键洞察**：Jetson Nano 和 ESP32-Cam 都有 40 针 GPIO，这是有线控制的核心。有线应急停止 <1ms，无线 WiFi >100ms。

### 选择原则

| 场景 | 推荐协议 |
|------|---------|
| 紧急停止 | **有线 GPIO**（<1ms）|
| 启动/停止时序 | **有线 UART** |
| 多设备同步时钟 | **有线 I2C** |
| 传感器数据采集 | 无线 MQTT |
| 视频流 | 无线 WiFi（GStreamer）|

---

# 第四部分：实施阶段

## Phase 0：Ubuntu 台式机对接 Gateway

### 目标
让 Ubuntu 台式机（5600G + 32GB + RTX 2060）作为 GPU 节点连接到 Mac Gateway。

### 配置步骤

**Step 1**: 获取 Gateway Token
```bash
cat ~/.openclaw/openclaw.json | grep -A5 '"auth"'
```

**Step 2**: 在 Ubuntu 上启动 Node Host
```bash
export OPENCLAW_GATEWAY_TOKEN="your-token-here"
openclaw node run --host 192.168.1.x --port 18789 --display-name "Ubuntu-GPU-Node"
```

**Step 3**: 在 Mac Gateway 上批准配对
```bash
openclaw devices list
openclaw devices approve <requestId>
```

**Step 4**: 配置 Exec 默认使用该节点
```bash
openclaw config set tools.exec.host node
openclaw config set tools.exec.node "Ubuntu-GPU-Node"
```

---

## Phase 1：语音陪伴模块

### 目标
实现基础语音交互：语音输入 → 文字 → AI 处理 → 语音输出。

### 硬件
- Jetson Nano（已有）
- USB 耳机（需采购）

### 实施步骤

**Step 1**: Jetson Nano 系统安装
1. 下载 JetPack 镜像（NVIDIA 官网）
2. 用 balenaEtcher 烧录 SD 卡
3. 基础配置：换阿里云源、开启 SSH

**Step 2**: 音频配置
```bash
# 查看设备
arecord -l
aplay -l

# 设置默认设备（USB耳机card 1）
nano ~/.asoundrc
```

**Step 3**: 安装 Whisper 语音识别
```bash
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp && make -j4
./models/download-ggml-model.sh tiny
```

**Step 4**: 安装 Edge-TTS 语音合成
```bash
pip3 install edge-tts
```

**Step 5**: 运行语音对话程序（详见附录 A.1）

---

## Phase 2：视觉记录模块

### 目标
24小时视频记录，本地处理不传云端，AI 能理解画面内容。

### 硬件
- ESP32-Cam（已有）

### 实施步骤

**Step 1**: ESP32-Cam 固件烧录
```bash
# 硬件连接：GND/5V/U0R/U0T/IO0(烧录模式)
pip3 install esptool
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash \
  0x1000 esp32-cam-webserver.bin
```

**Step 2**: Jetson Nano 接收视频
```bash
ffplay rtsp://<ESP32-CAM-IP>/stream
```

**Step 3**: 编写视频处理程序（详见附录 A.2）

---

## Phase 3：面部表情系统

### 设计理念
0-1 的面部由「0」「-」「1」三个核心元素构成，动态显示 AI 状态。

### 系统组成

| 组件 | 形态 | 功能 |
|------|------|------|
| 「0」| LED 点阵/IPS 屏幕 | 显示主眼睛，动态表情 |
| 「-」| 线性灯光带 | 情绪光效（颜色+呼吸节奏）|
| 「1」| 小型显示屏/LED | 辅助信息、状态指示 |

详见附录 A.3 精密加工工作流。

---

## Phase 4：运动控制模块

### 目标
OpenClaw 能通过 WiFi/MQTT 发送指令到 Cyber Bricks，驱动电机/舵机执行物理动作。

### 硬件
- Jetson Nano（主控）
- Cyber Bricks ×2（执行器）
- ESP32-Cam（传感器）

### 通信架构

```
OpenClaw Gateway
    ↓ MQTT
Jetson Nano（接收指令）
    ↓ UART/I2C 有线
Cyber Bricks（驱动电机/舵机）
```

### MicroPython 示例（Cyber Bricks）

```python
# CyberBrick 接收 HTTP 请求并执行
import network
import urequests
from machine import Pin, PWM

# 初始化舵机
servo = PWM(Pin(15))
servo.freq(50)

def set_angle(angle):
    duty = int(40 + angle * 95 / 90)
    servo.duty(duty)

# HTTP 服务器
def web_server():
    import socket
    s = socket.socket()
    s.bind(('', 80))
    s.listen(5)
    while True:
        conn, addr = s.accept()
        request = conn.recv(1024)
        if b'/servo?' in request:
            angle = int(request.decode().split('angle=')[1].split()[0][0])
            set_angle(angle)
        conn.send('HTTP/1.1 200 OK\n\nOK')
        conn.close()
```

### 有线 GPIO 应急停止

```bash
# Jetson Nano 发送紧急停止信号
echo 29 > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio29/direction
echo 0 > /sys/class/gpio/gpio29/value  # 继电器断开，所有电机断电
```

---

## Phase 5：iPhone 感知前端

### 目标
iPhone 16 Pro 通过 OpenClaw Node 协议接入 Gateway，成为分布式感知网络的一员。

### iPhone 作为 OpenClaw Node 的能力

| iPhone 能力 | 通过 OpenClaw 暴露为 | 说明 |
|------------|-------------------|------|
| 摄像头（4800万主摄）| `camera` 节点 | 实时视频流 |
| LiDAR 深度数据 | `camera.depth` 节点 | 室内3D建模、避障 |
| 四麦克风阵列 | `audio` 节点 | 远场语音采集 |
| A18 Pro NPU | 本地 LLM 推理节点 | Core ML 模型 |
| IMU 姿态 | `sensor.imu` 节点 | 6轴惯性测量 |
| UWB 定位 | `sensor.position` 节点 | 室内10-30cm精度 |

### 接入方式

```
iPhone 16 Pro（OpenClaw App）
    ↓ WiFi/MQTT
Gateway（MacBook）
    ↓
OpenClaw Agent（贵庚大脑）
    ↓
控制指令 → Jetson Nano / ESP32-Cam / Cyber Bricks
```

### iPhone 托管时的感知分工

| 任务 | 在哪个设备跑 | 说明 |
|------|------------|------|
| 实时物体检测（障碍物）| **iPhone YOLOv11n** | Core ML，节省 Jetson 算力 |
| 人体检测/跟随 | **iPhone Vision** | 免费，系统级 |
| 手势指令识别 | **iPhone MediaPipe** | 33关键点，极快 |
| 语义场景理解 | **iPhone FastVLM** | 本地 VLM，不占带宽 |
| 复杂推理/回答 | **Jetson Nano / 云端** | 非实时，延迟可接受 |

---

# 第五部分：AI 与感知

## 5.1 Jetson Nano 视觉感知

### 工具选择

| 工具 | 功能 | 适用场景 | 阶段 |
|------|------|---------|------|
| **MediaPipe** | 人体姿态、手势、面部网格 | 识别人、表情、手势指令 | 阶段一 |
| **GStreamer** | 视频流传输（20-30fps实测）| 实时视频流 | 阶段一 |
| **YOLOv5n/v8n** | 通用物体检测 | 环境感知、导航 | 阶段一 |
| **OpenCV** | 图像预处理、SLAM 前期 | 相机标定 | 阶段一 |
| **TensorRT FP16** | YOLO 模型推理加速 | 所有 YOLO 部署 | 阶段一 |
| **DeepStream 5.0/5.1** | YOLO 集成框架 | 生产级视频分析 | 阶段一 |

> **注意**：你的 Jetson Nano 是 **2GB 版本**（量产模块），不是 4GB 开发套件。2GB 内存更小，跑 YOLO 更容易 OOM。

### YOLO 在 Nano 2GB 上的实测 FPS（TensorRT FP16）

| 模型 | Nano 4GB | Nano 2GB（预估）| 说明 |
|------|---------|---------------|------|
| YOLOv8n | 13-16 FPS | 5-10 FPS | 速度最快，但 2GB 容易 OOM |
| YOLOv5n | 15-25 FPS | 8-15 FPS | 最稳妥，DeepStream-Yolo 适配最好 |
| YOLOv11n | 10.6 FPS | 3-7 FPS | 精度最高但最慢，2GB 风险大 |

### Nano 2GB 必开优化

```bash
# 最大性能模式
sudo nvpmodel -m 0 && sudo jetson_clocks

# 添加 swap（防止 OOM）
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile

# 降低输入分辨率：320x320 而非 640x640
```

### YOLO + MediaPipe 共存方案

| 配置 | FPS | 内存占用 |
|------|-----|---------|
| MediaPipe Pose（GPU）| ~20 FPS | ~500-800 MB |
| YOLOv5n + TensorRT FP16 | ~15-20 FPS | ~1-1.5 GB |
| **两者同时跑** | **约 10-15 FPS** | **~2.5 GB（需开 swap）** |

**推荐串联架构**：
```
输入帧 → YOLOv5n 检测人体区域 → MediaPipe Pose 姿态估计
```

---

## 5.2 iPhone AI 目标检测方案

### 五平台完整对比

| 平台 | iPhone 视觉方案 | 可用性 | 备注 |
|------|---------------|--------|------|
| **Apple Vision** | `VNDetectObjectsRequest` | ✅ 最佳 | 免费+极快，只支持人脸/人体/条码/文字/矩形 |
| **Core ML + YOLO** | Ultralytics 导出 Core ML | ✅ 最佳 | 通用物体检测，30-60 FPS（A18 Pro）|
| **MediaPipe** | 谷歌全链路框架 | ✅ 推荐 | 人脸/手势/姿态/物体一条龙，0.81ms |
| **FastVLM（苹果官方）** | FastViTHD 视觉编码器 | ✅ 新发现 | iPhone 本地跑 VLM，0.5B 版本专为手机优化 |
| **豆包/字节** | 云端 API | ❌ 不适用 | 无端侧 SDK |
| **千问/Qwen** | GGUF + llama.cpp | ⚠️ 可行但慢 | 不适合实时检测 |
| **Kimi/Moonshot** | k1 iOS App 有视觉 | ❌ 手机跑不了 | Kimi-VL 开源需 24GB GPU |
| **智谱/GLM** | 云端架构 | ❌ 不适用 | GLM-4.5V 太大 |

### 三大主力方案详解

**① Apple Vision Framework（原生免费）**

| API | 功能 |
|-----|------|
| `VNDetectHumanRectanglesRequest` | 人体检测 |
| `VNDetectFaceRectanglesRequest` | 人脸检测 |
| `VNDetectBarcodesRequest` | 条码/二维码 |
| `VNRecognizeTextRequest` | 文字识别 OCR |

```swift
// 最简人体检测代码
let request = VNDetectHumanRectanglesRequest()
let handler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer)
try handler.perform([request])
```

**② Core ML + YOLO（通用物体检测首选）**

| 模型 | A18 Pro FPS | 说明 |
|------|------------|------|
| YOLOv11n | **30-60 FPS** | 实时检测首选 |
| YOLOv8n | **25-50 FPS** | 成熟稳定 |

```bash
# 一键导出 Core ML（Ultralytics 官方支持）
yolo export model=yolov11n.pt format=coreml nms=True imgsz=800
```

**③ MediaPipe（功能最全）**

| 能力 | 推理速度 |
|------|---------|
| 物体检测 | ~0.81ms |
| 手势识别 | ~2ms（33个关键点）|
| 全身姿态 | ~5ms（33个关键点）|

### Apple FastVLM（新发现）

苹果官方开源，专为 iPhone 端侧 VLM 设计：
- **0.5B 版本**可直接在 iPhone 本地运行，无需联网
- 首字延迟比 LLaVA-OneVision **快 85 倍**（FastViTHD 视觉编码器）
- Safari 网页版 Demo：实时摄像头画面 + AI 即时描述

### VLM vs YOLO：怎么选

| 维度 | YOLO（目标检测）| VLM（视觉语言模型）|
|------|----------------|------------------|
| 输出 | 边界框 + 类别 | 文字描述 |
| 速度 | ⚡ 毫秒级（30-60 FPS）| 秒级 |
| 精度定位 | ✅ 高精度边界框 | ❌ 无法输出精确坐标 |
| 泛化能力 | 受限训练集 | 理解任意场景 |

**推荐分层架构**：
```
iPhone 摄像头
    ↓
YOLO11n（Core ML）→ 实时物体检测 → Jetson Nano 运动控制
    ↓
FastVLM 0.5B → 语义理解 → 贵庚大脑
```

---

# 第六部分：AI 软件生态

## 6.1 本地 LLM 推理

| 工具 | 作用 | 适用阶段 |
|------|------|---------|
| **NIM** | NVIDIA 推理微服务容器，API 兼容 OpenAI | 阶段一 |
| **TensorRT-LLM** | NIM 底层引擎，FP8/INT4 量化 | 阶段一 |
| **vLLM** | 开源 LLM 推理引擎 | 阶段一 |
| **AMD Quark** | AMD 推理量化工具 | AI Halo |

### 各硬件能跑的模型

| 硬件 | 能跑的模型 |
|------|---------|
| RTX 5050 9GB GDDR7 | Qwen3.5-4B/9B 4-bit |
| AMD AI Halo 128GB | Qwen3.5-122B（4-bit 量化需 ~70GB）|
| DGX Spark | 200B 参数模型 |

---

## 6.2 机器人仿真与数字孪生

### Genesis（开源物理引擎）— 首选

华人团队开源，GitHub 2.5万+ Star，比 Isaac Sim 快 10-80 倍：

| 对比 | Isaac Sim | Genesis |
|------|-----------|---------|
| 速度 | 快 | **快 10-80 倍** |
| GPU 要求 | RTX 3090+（8GB+）| **GTX 1080 6GB 起**（RTX 4060 8GB 验证可跑）|
| GPU 范围 | 仅限 NVIDIA | **NVIDIA + AMD + Apple Metal + 纯 CPU** |
| 费用 | 免费但封闭 | **MIT 开源，完全免费** |

**真实门槛**：最低 **GTX 1080 6GB** 就能跑，**RTX 4060 8GB** 已验证流畅运行。RTX 4090 可达 4300 万 FPS，比实时快 43 万倍。

**对 0-1 的意义**：数字孪生训练的硬件门槛从 Isaac Sim 的 RTX 3090+ 降到 GTX 1080 6GB，现有台式机（RTX 2060 6GB）就能用。

### Isaac Lab（可选）

NVIDIA 官方机器人强化学习训练框架，基于 Isaac Sim。阶段三以后用于训练复杂操作技能。

### DLSS 5（渲染加速）

2026 年秋发布，AI 真正理解场景后生成像素，不只是补帧。消费级 RTX 4090 也能跑真实感虚拟环境训练贵庚。

---

# 第七部分：安全与维护

## 7.1 安全功能

详见第十章。

## 7.2 日常维护

详见第十一章。

## 7.3 常见问题排查

详见第十一章。

---

# 第八部分：附录

## A.1 语音对话程序完整代码

详见第五章 Phase 1。

## A.2 视频处理程序完整代码

详见第六章 Phase 2。

## A.3 拓竹软件生态

| 软件 | 平台 | 核心作用 |
|------|------|---------|
| **Bambu Studio** | Win/Mac/Linux | 切片引擎，多色/多材料打印 |
| **Bambu Suite** | 桌面端 | 激光雕刻/切割/画笔/刀切，多工艺串联 |
| **Bambu Handy** | iOS/Android | 移动端监控，AMS 耗材管理 |
| **拓竹农场管家** | Windows | 多机本地化集群管理，数据不上云 |
| **Bambu Connect** | Win/Mac | 第三方切片→打印机授权 |
| **CyberBrick** | 桌面+移动 | 机器人调试，MicroPython 可视化 |

## A.4 技术风险与法规

详见第十二章。

---

# 第九部分：安全功能

## 9.1 声纹识别

### 目标
通过声纹识别确认用户身份，只有授权用户的声音才能触发关键操作。

### 实现方式

```python
import librosa
import numpy as np

def extract_voice_embedding(audio_path):
    y, sr = librosa.load(audio_path, sr=16000)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    return np.mean(mfccs.T, axis=0)

def verify_speaker(test_audio, enrolled_audio, threshold=0.85):
    test_emb = extract_voice_embedding(test_audio)
    enrolled_emb = extract_voice_embedding(enrolled_audio)
    similarity = np.dot(test_emb, enrolled_emb) / (
        np.linalg.norm(test_emb) * np.linalg.norm(enrolled_emb)
    )
    return similarity > threshold
```

### 声纹注册流程

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 用户说3-5个不同句子 | 收集多样本 |
| 2 | 提取每句的声纹向量 | 10-15秒音频 |
| 3 | 平均后存储 | 存入本地数据库 |
| 4 | 验证时比对 | 余弦相似度 >0.85 通过 |

---

## 9.2 异常检测

### 目标
实时监控 Jetson Nano / ESP32-Cam 运行状态，发现异常立即告警。

### 监控指标

| 指标 | 正常范围 | 异常阈值 | 处理 |
|------|---------|---------|------|
| CPU 温度 | < 80C | > 85C | 降频/停机 |
| CPU 使用率 | < 90% | > 95% 持续5分钟 | 重启进程 |
| 内存使用 | < 80% | > 90% | 清理缓存 |
| 网络延迟 | < 100ms | > 500ms | 切换网络 |
| ESP32-Cam FPS | > 15 FPS | < 10 FPS | 重启固件 |

### 监控脚本

```python
#!/usr/bin/env python3
import psutil, subprocess, time, requests

def get_cpu_temp():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            return int(f.read()) / 1000
    except: return 0

def check_system():
    warnings = []
    temp = get_cpu_temp()
    if temp > 85: warnings.append(f"CPU温度过高: {temp}C")
    mem = psutil.virtual_memory()
    if mem.percent > 90: warnings.append(f"内存不足: {mem.percent}%")
    cpu = psutil.cpu_percent(interval=5)
    if cpu > 95: warnings.append(f"CPU过载: {cpu}%")
    return warnings

def send_alert(message):
    try:
        requests.post("http://192.168.1.x:3000/api/alert",
            json={"type": "system_warning", "message": message}, timeout=5)
    except: pass

while True:
    warnings = check_system()
    for w in warnings:
        print(f"WARNING: {w}")
        send_alert(w)
    time.sleep(60)
```

---

## 9.3 数据自毁

### 目标
在物理被盗或被强制夺取时，自动销毁贵庚的核心数据。

### 触发条件

| 触发方式 | 说明 |
|---------|------|
| 物理按钮 | 机器人被夺走时按下 |
| 遥控指令 | 发送销毁信号 |
| 异常检测 | 检测到被拆解（加速度计异常）|
| 超时未认证 | 超过设定时间未声纹验证 |

### 销毁流程

```python
#!/usr/bin/env python3
def destroy_all_data():
    import os, subprocess
    DATA_DIRS = [
        "/home/nvidia/guigeng/memory",
        "/home/nvidia/guigeng/videos",
        "/home/nvidia/guigeng/audio",
    ]
    print("WARNING: 触发数据自毁程序")
    subprocess.run(["pkill", "-f", "robot-voice"])
    subprocess.run(["pkill", "-f", "robot-video"])
    for dir_path in DATA_DIRS:
        if os.path.exists(dir_path):
            subprocess.run(["shred", "-n", "3", "-ruv", dir_path])
    print("OK: 数据自毁完成")
```

> WARNING: 数据自毁后不可恢复。重要数据应定期备份到 NAS。

---

# 第十部分：日常维护与排查

## 10.1 日常维护

### 每日检查

```bash
# 1. 检查节点在线状态
openclaw devices list

# 2. 检查 Jetson Nano 温度
ssh nvidia@192.168.1.x "cat /sys/class/thermal/thermal_zone0/temp"

# 3. 检查 ESP32-Cam 视频流
ffplay rtsp://192.168.1.y/stream

# 4. 检查 Cyber Bricks 电池
curl http://192.168.1.z/battery
```

### 每周维护

| 任务 | 操作 | 说明 |
|------|------|------|
| 日志清理 | journalctl --vacuum-time=7d | 删除7天前日志 |
| 缓存清理 | rm -rf ~/.cache/* | 清理临时文件 |
| 固件检查 | 检查 ESP32-Cam 新固件 | 提升稳定性 |
| 备份 | rsync 到 NAS | 贵庚数据双备份 |

### 每月维护

| 任务 | 操作 |
|------|------|
| 系统更新 | sudo apt update && sudo apt upgrade -y |
| 磁盘检查 | df -h 确认存储充足 |
| 证书更新 | 检查 OpenClaw Gateway 证书 |
| 硬件检查 | 检查所有接线、供电、散热 |

---

## 10.2 常见问题排查

### Jetson Nano 问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 开机黑屏 | 电源不足 | 使用 5V/4A 电源适配器 |
| WiFi 断开 | 驱动问题 | sudo apt install linux-firmware |
| USB 不识别 | 供电不足 | 接外接供电 USB Hub |
| 温度过高 | 散热不足 | 清理风扇、安装散热片 |

### ESP32-Cam 问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 无法连接 | IP 变更 | 重新扫描或设置静态 IP |
| 视频花屏 | 供电不足 | 使用 5V/2A 电源 |
| RTSP 延迟大 | WiFi 信号弱 | 靠近路由器或用有线 |
| 固件崩溃 | 内存泄漏 | 重刷固件 |

### Cyber Bricks 问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 电机不转 | 电池没电 | 充电或换电池 |
| 舵机抖转 | 信号干扰 | 检查接线、加屏蔽 |
| WiFi 断开 | 信号弱 | 调整天线位置 |

### OpenClaw 问题

| 问题 | 原因 | 解决 |
|------|------|------|
| Node 不在线 | 网络不通 | ping 192.168.1.x 检查 |
| exec 超时 | 节点负载高 | 等几秒重试 |
| 配对失败 | Token 错误 | 重新获取 Token |

---

# 第十一部分：风险与合规

## 11.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Jetson Nano 烧毁 | 机器人瘫痪 | 稳压电源、温度监控 |
| 数据丢失 | 贵庚记忆损坏 | 每日 rsync 备份到 NAS |
| WiFi 被劫持 | 控制权丧失 | 启用 WPA3、关闭 WPS |
| ESP32-Cam 被破解 | 隐私泄露 | 修改默认密码、禁用Telnet |
| Cyber Bricks 失控 | 物理损坏 | 有线 GPIO 应急停止 |

---

## 11.2 法规风险

| 风险 | 说明 | 合规建议 |
|------|------|---------|
| 隐私合规 | 24小时录像涉及隐私 | 明确告知、录像本地存储、不上云 |
| 室内录音 | 未授权录音可能违法 | 仅在授权用户声纹验证后启用 |
| 机器人伤人 | Cyber Bricks 动作幅度大 | 设置动作限位、接触停止 |
| 无线电频谱 | ESP32-Cam WiFi 需合规 | 使用已认证设备 |

> 本文档不构成法律建议。具体合规要求请咨询专业律师。

---

**0-1** —— 不是一台机器，是你人生的另一面。

*本文档将持续更新完善*
