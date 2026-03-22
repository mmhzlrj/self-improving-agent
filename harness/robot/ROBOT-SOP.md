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

> **调研时间**：2026-03-22
> **调研工具**：zhiku(DeepSeek) + subagent × 2 + web search
> **A18 Pro NPU 基准**：Geekbench AI 量化分数 **44,672**（比 A17 Pro 高 33%）

### 四平台完整对比

| 平台 | iPhone 视觉方案 | 可用性 | 推荐指数 | 备注 |
|------|---------------|--------|---------|------|
| **Apple Vision** | `VNDetectObjectsRequest` | ✅ 最佳 | ⭐⭐⭐⭐⭐ | 免费+极快，120fps+，只支持常见类目 |
| **Core ML + YOLO** | Ultralytics 导出 Core ML | ✅ 最佳 | ⭐⭐⭐⭐⭐ | 通用物体检测，30-60 FPS（A18 Pro）|
| **MediaPipe** | 谷歌全链路框架 | ✅ 推荐 | ⭐⭐⭐⭐ | 跨平台，功能全，编译配置复杂 |
| **FastVLM（苹果官方）** | FastViTHD 视觉编码器 | ✅ 新发现 | ⭐⭐⭐ | iPhone 本地跑 VLM，多模态理解 |

### YOLO 在 Apple Silicon 性能基准（M4 Pro/M4 Max 参考）

| 模型 | 芯片 | FPS | 说明 |
|------|------|-----|------|
| YOLOv11n | M4 Pro | **97.6** | 实时检测首选 |
| YOLOv8n | M4 Pro | **92.6** | 最快，最轻量 |
| YOLOv8s | M4 Pro | 68.8 | 速度精度平衡 |
| YOLOv8m | M4 Pro | 43.7 | 精度更高 |
| YOLOv11m-seg | M4 Max | ~8 | 分割任务 |

*注：A18 Pro 与 M4 同架构（Neural Engine +统一内存），A18 Pro NPU 量化分数比 A17 Pro 高 33%*

### A18 Pro vs A17 Pro

| 指标 | A18 Pro | A17 Pro | 提升 |
|------|---------|---------|------|
| NPU 量化分数 | **44,672** | 33,479 | +33% |
| CPU 单核 | **3376** | 2842 | +19% |
| CPU 多核 | **8219** | 7020 | +17% |

### 三大主力方案详解

**① Apple Vision Framework（原生免费）**

| API | 功能 |
|-----|------|
| `VNDetectHumanRectanglesRequest` | 人体检测 |
| `VNDetectFaceRectanglesRequest` | 人脸检测 |
| `VNDetectBarcodesRequest` | 条码/二维码 |
| `VNRecognizeTextRequest` | 文字识别 OCR |
| `VNRecognizeObjectsRequest` | 通用物体检测（4000+类）|

```swift
// 最简人体检测代码
let request = VNDetectHumanRectanglesRequest()
let handler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer)
try handler.perform([request])
```

**② Core ML + YOLO（通用物体检测首选）**

| 模型 | A18 Pro 预估 FPS | 说明 |
|------|----------------|------|
| YOLOv11n | **40-60 FPS** | 实时检测首选 |
| YOLOv8n | **35-50 FPS** | 成熟稳定 |
| YOLOv8s | **25-40 FPS** | 速度精度平衡 |

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
- MLX 缓存：重复图像延迟从 21.7秒 → 0.78秒（28倍加速）
- Safari 网页版 Demo：实时摄像头画面 + AI 即时描述

### VLM vs YOLO：怎么选

| 维度 | YOLO（目标检测）| VLM（视觉语言模型）|
|------|----------------|------------------|
| 输出 | 边界框 + 类别 | 文字描述 |
| 速度 | ⚡ 毫秒级（40-60 FPS）| 秒级（TTFT 1秒）|
| 精度定位 | ✅ 高精度边界框 | ❌ 无法输出精确坐标 |
| 泛化能力 | 受限训练集 | 理解任意场景 |

**推荐分层架构**：
```
iPhone 摄像头
    ↓
YOLOv11n（Core ML）→ 实时物体检测 → Jetson Nano 运动控制
    ↓
FastVLM 0.5B → 语义理解 → 贵庚大脑
```

---

# 第六部分：AI 软件生态

## 6.1 本地 LLM 推理

> **调研时间**：2026-03-22
> **调研工具**：zhiku(DeepSeek/Kimi/Doubao) + subagent × 2 + web_fetch(OpenClaw docs)

### 推理框架对比

| 框架 | RTX 2060 (Turing) | AMD AI Halo (Strix Halo) | OpenClaw 支持 |
|------|-------------------|--------------------------|---------------|
| **vLLM** | ✅ 支持，AWQ/GPTQ 量化 | ✅ ROCm 后端支持 | ✅ OpenAI-compatible API |
| **TensorRT-LLM** | ✅ 支持，INT4/INT8 量化 | ❌ NVIDIA 专有 | ❌ 不支持 |
| **Ollama** | ✅ 原生 CUDA | ✅ ROCm/Vulkan | ✅ 原生集成（推荐）|
| **LM Studio** | ✅ CUDA | ✅ ROCm | ✅ OpenAI-compatible |
| **AMD Quark** | ❌ 不适用 | ✅ 官方量化工具 | ❌ 不支持 |

### CUDA 对 RTX 2060 的支持

| 项目 | 详情 |
|------|------|
| 架构 | Turing (SM 7.5) |
| CUDA 12.x 支持 | ✅ **完全支持** |
| 推荐驱动 | ≥ 525.60.13 (Linux) / ≥ 528.33 (Windows) |
| 推荐 CUDA 版本 | **CUDA 11.8**（图灵最优）/ CUDA 12.4+（可用）|
| FP8 精度 | ❌ 不支持（需要 Ada/Hopper）|
| Tensor Core | ✅ 第一代，支持 FP16/INT8 |

**建议**：RTX 2060 生产环境用 **CUDA 11.8**，开发尝鲜用 **CUDA 12.4+**

### ROCm 对 AMD AI Halo 128GB 的支持

| ROCm 版本 | 支持状态 | 说明 |
|-----------|---------|------|
| ROCm 6.x | ❌ **不支持** | gfx1151 (RDNA 3.5) 不在 6.x 官方支持列表 |
| **ROCm 7.0+** | ✅ **官方支持** | 正式支持 Strix Halo (gfx1151)，集成 rocWMMA |
| **ROCm 7.2.2** | ✅ **推荐版本** | CES 2026 发布，Day-0 优化支持 |
| ROCm 7.9 (nightly) | ✅ 实验性 | 897 tokens/s (Qwen3-30B 提示词处理) |

**性能数据**（llama.cpp, Qwen3-30B, 2048 tokens 上下文）：
- Vulkan 后端：~412 tokens/s
- ROCm 7.0.2 + ROCm 后端：**876.9 tokens/s** (+112%)

### 各硬件能跑的模型

| 硬件 | 能跑的模型 | 量化方案 |
|------|---------|---------|
| RTX 2060 6GB | Qwen3.5-1.5B/4B 4-bit | INT4/INT8 量化 |
| RTX 2060 6GB | YOLO/Gemma 2B | FP16 |
| AMD AI Halo 128GB | Qwen3.5-122B（4-bit 需 ~70GB）| AWQ/GPTQ |
| AMD AI Halo 128GB | LLaMA 70B / Mistral 70B | FP16 直接跑 |
| DGX Spark 128GB | 200B 参数模型（统一内存）| FP16 |

### NemoClaw — NVIDIA 官方 OpenClaw 优化栈

**NemoClaw** 是 NVIDIA GTC 2026 为 OpenClaw 定制的官方软件栈：

| 特性 | 说明 |
|------|------|
| **OpenShell** | 安全沙箱，限制 AI 权限（防恶意操作）|
| **隐私路由器** | 敏感数据本地处理，按需调用云端 |
| **安全护栏** | 企业级合规性，AI 无法同时上网+读写文件+执行代码 |
| **一键安装** | 简化 OpenClaw 部署 |

**对贵庚的影响**：企业级安全护栏 → OpenClaw 可进入生产环境

### DGX Spark 对 OpenClaw 的原生支持

| 特性 | 说明 |
|------|------|
| 硬件 | GB10 芯片，128GB 统一内存，1 PFLOPS |
| OpenClaw | ✅ **官方原生支持**，NVIDIA 官方指南 |
| 推荐后端 | **LM Studio** 或 **Ollama** |
| 可跑模型 | GPT-OSS-120B, MiniMax-M2.5, Qwen3.5-35B |
| 部署方式 | 三行命令完成环境配置+模型下载+网关启动 |

### OpenClaw 本地 LLM 配置推荐

**推荐栈**：LM Studio + MiniMax M2.5（Responses API）

```json5
{
  models: {
    mode: "merge",
    providers: {
      lmstudio: {
        baseUrl: "http://127.0.0.1:1234/v1",
        apiKey: "lmstudio",
        api: "openai-responses",
        models: [{
          id: "minimax-m2.5-gs32",
          name: "MiniMax M2.5 GS32",
          contextWindow: 196608,
        }]
      }
    }
  }
}
```

**备选**：Ollama（更简单，`openclaw onboard` 自动配置）

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

---

# 第十三部分：调研更新（2026-03-21 深夜调研补充）

> 调研方式：deepseek_deepseek_chat + 4x sessions_spawn 子Agent + web_fetch，覆盖 Genesis/Jetson/YOLO/iPhone/语音/OpenClaw 全部章节。

---

## 13.1 Genesis 物理引擎最新动态（深度调研）

### 官方最新数据（2026-03-21 调研确认）

| 指标 | 数值 |
|------|------|
| GitHub Stars | **28,318** |
| 最近更新 | **2026-03-21 13:48（今天！）** |
| License | Apache 2.0 |
| 版本策略 | **无语义版本号**，按时间节点发版 |

### Genesis vs Isaac Sim 完整对比

| 对比维度 | Genesis | Isaac Sim |
|----------|---------|-----------|
| 定位 | 通用具身智能/生成式仿真 | 工业级数字孪生 |
| 物理引擎 | 自研多求解器（刚体/MPM/SPH/FEM/PBD）| PhysX 5.1 (GPU) |
| 渲染 | 光线追踪 + 光栅化 | RTX 光线追踪（Omniverse USD）|
| GPU要求 | **GTX 1080 6GB 起**，支持 AMD/Apple Metal/CPU | 必须 NVIDIA RTX 8GB+ |
| ROS支持 | ❌ 无原生集成 | ✅ ROS2 Bridge 开箱即用 |
| USD支持 | 基础导入 | ✅ 完整 Omniverse USD |
| 学习曲线 | **低**（pip 安装，Gym 风格 API）| 高（需掌握 USD/Omniverse）|
| 速度 | **43M FPS**（RTX 4090）| 100+ 智能体并行 |
| 擅长场景 | 机器人学习、策略生成、数据合成 | 工厂数字孪生 |

### Genesis 最新功能（2026年以来）

| 日期 | 新增功能 |
|------|---------|
| 2026-03-16 | ProximitySensor、TemperatureGridSensor、GPU碰撞检测提速30% |
| 2026-03-13 | FOTS触觉传感器、异构机器人并行仿真、noslip性能大幅提升 |
| 2026-03-06 | Avatar实体重引入、IPC coupler改进、Apple Metal动态数组支持 |
| 2026-02-18 | **Quadrants编译器**正式迁移、AMD ROCm实验性支持 |
| 2026-02-10 | 交互查看器插件机制、glTF/USD支持、碰撞场景提速30% |

### ⚠️ 重要发现：v0.4.3 版本号不存在

调研确认：`v0.4.3` 不是官方 release tag，PyPI 包版本和 GitHub tag 策略不一致。**请以 GitHub Releases 页面为准**，最新功能请查看 GitHub 最新 commit。

### 竞品动态：Newton（2025年最强竞争者）

| 维度 | Genesis | Newton |
|------|---------|--------|
| 背景 | Genesis AI（Stanford系）| **Disney Research + Google DeepMind + NVIDIA 三巨头** |
| 时间 | 2023-10 | 2025-09 |
| 生态 | Apache 2.0，快速崛起 | 已贡献给 **Linux Foundation** |
| 核心 | 速度最快、多材料统一 | 专注复杂接触场景（雪地、碎石等非结构化地形）|
| 融资 | 1.05亿美元种子轮 | 未公开 |

**结论**：Genesis 仍是机器人学习的最佳开源选择，Newton 需要关注但为时尚早。

---

## 13.2 Jetson Nano 2GB + YOLO 极限优化（实测数据）

### DeepStream-Yolo 最新支持版本

✅ 全面支持：YOLOv13 / YOLOv12 / YOLO11 / YOLO26 / YOLO-Master

### 极限优化配置（Jetson Nano 2GB 极限方案）

```bash
# 基础必开
sudo nvpmodel -m 0 && sudo jetson_clocks

# DeepStream config 关键参数
network-mode=2              # FP16（2GB唯一选择，INT8无加速）
batch-size=1                  # 内存最小
batched-push-timeout=40000   # 25fps
sync=0                       # 关闭显示器同步
live-source=1                # RTSP实时流必须
maintain-aspect-ratio=1
symmetric-padding=1
```

### 实测 FPS（完整 pipeline，含前后处理）

| 模型 | 输入分辨率 | FPS | 说明 |
|------|----------|-----|------|
| YOLOv8n | 640x640 | ~13-16 | 推理~19FPS |
| YOLOv8n | 416x416 | ~20-25 | 降分辨率换速度 |
| YOLOv8n | 320x320 | ~35-45 | 极端优化 |
| YOLOv11n | 416x416 | ~25-35 | 最新模型 |
| YOLOv11n | 320x320 | ~50+ | 极限值 |
| YOLOv4-tiny | 416x416 | ~20-30 | 轻量老模型 |

> ⚠️ INT4 在 Nano 2GB 上不可用（Maxwell 架构不支持 INT8 推理加速）。**FP16 是唯一有效加速。**

### MediaPipe on Jetson Nano 2GB

**结论：GPU 加速方案不成熟，不推荐在 Nano 上跑 MediaPipe GPU。**

- Jetson Orin Nano 上 MediaPipe 手势也只有 ~5 FPS
- 替代方案：用 **TensorRT** 替代（ncnn + Vulkan 后端可用）
- 推荐：Pose/手势用 MobileNet + TensorRT FP16 替代 MediaPipe

---

## 13.3 iPhone 感知前端最新方案

### Apple FastVLM（最新验证）

| 指标 | 数据 |
|------|------|
| GitHub | apple/ml-fastvlm，CVPR 2025 |
| 速度 | 比 LLaVA-OneVision 快 **85倍 TTFT** |
| iPhone 16 Pro Max 实测 | TTFT 低至 **0.3秒** |
| 模型规格 | 0.5B / 1.5B / 7B |

### iPhone Core ML + YOLO 最新工具链

- `model.export(format='coreml')` 一键导出，Ultralytics 官方支持
- iPhone 15 Pro 跑 YOLOv8n：**约 28 FPS**（1080p）
- iPhone 16 Pro（A18 Pro）预计高 15-20%

### Camera Control 按钮可行性

| 交互 | 可行性 | 说明 |
|------|--------|------|
| 短按触发拍照 | ✅ 可行 | 通过 AssistiveTouch 映射 |
| 长按持续录制 | ✅ 可行 | BLE 通知触发 |
| 滑动调节速度 | ✅ 可行 | 电容感应可区分按压面积 |
| 深度 API 控制 | ❌ 受限 | Apple 未开放硬件级 API |

### LiDAR 导航：ARKit vs 传统 SLAM

| 方案 | 适合场景 | iPhone 接口 |
|------|---------|------------|
| ARKit 路径记忆 | 室内固定路线 | 直接用 |
| RoomPlan API | 自动生成 3D 房间模型 | CAD 导出 |
| RTAB-Map | 室内建图+导航 | iOS 端口可用 |
| ORB-SLAM3 | 室外/室内通用 | 有 iOS 版本 |

**最佳实践**：iPhone 做感知前端（摄像头/LiDAR/IMU）→ WiFi 传输数据 → Jetson 跑 SLAM 算法。

---

## 13.4 语音交互模块升级方案

### TTS 推荐（本地离线）

| 方案 | 优势 | 适合场景 |
|------|------|---------|
| **VITS** | ~0.83 RTF（1.2倍实时），最轻量 | ✅ 机器人首选 |
| **CosyVoice2-0.5B** | 阿里出品，高自然度，多语言 | 产品级，稳定优先 |
| **GPT-SoVITS v4** | 5秒音频克隆，1分钟微调 | 个性化声音 |
| ~~Edge-TTS~~ | ❌ 需要云服务，不符合离线要求 | — |

### 语音唤醒方案

| 方案 | 推荐度 | 说明 |
|------|--------|------|
| **OpenWakeWord** | ⭐⭐⭐⭐⭐ | 完全开源，可自定义唤醒词 |
| Porcupine | ⭐⭐⭐ | 轻量，25-50ms 延迟 |
| Picovoice | ⭐⭐⭐ | 可考虑，商业友好 |

### 降噪链路（最佳实践）

```
音频输入 → WebRTC AEC（回声消除）→ RNNoise（降噪）→ VAD检测 → 唤醒词引擎
```

| 方案 | 延迟 | CPU占用 | 核心能力 |
|------|------|---------|---------|
| RNNoise | **10ms** | **3.2%** | 降噪（PESQ 3.8）|
| WebRTC AEC3 | 20-60ms | 8.7% | 回声消除 |
| 顺序 | 先 AEC 后 RNNoise | — | 互补非替代 |

### Whisper 优化（Jetson Nano）

- 模型：`base.en`（139MB），可达 1倍实时
- TensorRT INT8 量化：速度提升 40%+，内存减半
- 推荐路径：`whisper-edge` + ONNX 导出 + TensorRT

---

## 13.5 OpenClaw 作为机器人大脑的深度评估

### 核心发现：没有专用"机器人节点"类型

OpenClaw 官方支持以下节点类型：

| 节点类型 | 暴露命令 |
|----------|---------|
| macOS | canvas/camera/screen/system/device/notifications |
| iOS | camera/canvas/screen/location/voice |
| Android | camera/canvas/sms/device/notifications/motion |
| Headless Linux | **只有 system.run / system.which** |

⚠️ **没有 GPIO、串口、CAN 总线、电机控制、传感器读取的内置支持。**

### OpenClaw 的真实定位

| 适合场景 | 不适合场景 |
|---------|-----------|
| 自然语言交互高层任务 | 毫秒级实时运动控制 |
| 多 channel 控制（微信/Telegram）| 精密工业机械臂 |
| 高层任务规划和异常处理 | 自动驾驶 |
| 服务机器人对话系统 | 硬实时操作系统 |

### 推荐架构：OpenClaw + ROS 2 混合

```
OpenClaw Gateway（AI 大脑）
    ↓ exec / Skill
Robot Bridge（Python 脚本）
    ↓
ROS 2 生态系统（运动控制层）
    ↓
MoveIt（运动规划）/ Navigation（路径规划）/ 传感器驱动
    ↓
机器人硬件
```

### OpenClaw 多节点限制

| 能力 | 状态 |
|------|------|
| 多 Node Host 连接 | ✅ 支持 |
| Exec 节点绑定 | ✅ 支持 |
| 节点分组/tag | ❌ 不支持 |
| 跨节点直接通信 | ❌ 不支持 |
| 分布式执行 | ❌ 不支持 |

---

## 13.6 Jetson Nano + ESP32-Cam 有线通信最新方案

### ESP32-Cam 最新固件（2025年推荐）

**推荐方案**：Arduino ESP32 v3.0.7 + CameraWebServer

关键改进（相比旧版）：
- Wi-Fi 自动重连机制完善
- 看门狗复位大幅减少
- 分区表优化支持更大 ota_0

```cpp
// 稳定初始化（2025年推荐）
rtc_clk_cpu_freq_set(RTC_CPU_FREQ_240M); // 降频减少发热
// 使用 SVGA 而非 UXGA，减少内存压力
```

### UART 通信（Jetson Nano ↔ ESP32-Cam）

- 电平：双方都是 3.3V TTL，**直接互连不需要电平转换**
- 端口：Jetson Nano 用 `/dev/ttyTHS1`（40-pin GPIO 8/10）
- 波特率：115200（最佳性价比）

### I2C 总线注意事项

| 问题 | 解决方案 |
|------|---------|
| 地址检测不到 | 降低频率至 10-50kHz |
| 地址冲突 | 使用 TCA9548A I2C 多路复用器 |
| 数据错误 | 绞线+屏蔽或换用 UART |

### 协议选择

| 协议 | 推荐度 | 适用场景 |
|------|--------|---------|
| **MQTT** | ⭐⭐⭐⭐⭐ | ESP32 控制指令下发+状态上报 |
| **ROS 2 Humble** | ⭐⭐⭐⭐ | Jetson Nano 与上位机/多节点 |
| ZeroMQ | ⭐⭐⭐ | 极低延迟实时控制 |
| gRPC | ⭐ | 太重，ESP32 资源不足 |

### GPIO 应急停止（推荐电路）

**双继电器急停电路（物理+软件双保险）**：
- 急停必须物理断开电机电源回路
- 双继电器冗余防止单点故障
- 常闭触点设计：断电 = 停机（故障安全）
- ESP32 端用硬件中断（μs 级响应）

---

**0-1** —— 不是一台机器，是你人生的另一面。

*调研更新：2026-03-22 凌晨*
