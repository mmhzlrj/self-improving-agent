# 🤖 0-1 私人 AI 机器人完整实施指南

**项目名**: 0-1（零杠一）
**记忆系统**: 贵庚
**文档版本**: v3.0（重组版）
**创建日期**: 2026-03-07
**更新日期**: 2026-03-22
**字数**: 6068

---

# 目录

| 章节 | 标题 |
|------|------|
| 第一章 | 概念与愿景 |
| 第二章 | 硬件体系 |
| 第三章 | 系统架构 |
| 第四章 | 实施阶段（Phase 0 → Phase 6）|
| 第五章 | AI 与感知 |
| 第六章 | 本地 LLM 推理 |
| 第七章 | 附录（工具链/代码/配置）|
| 第八章 | 安全与维护 |
| 第九章 | 风险与合规 |
| 第十章 | 调研更新记录（按时间线）|

---

# 第一章：概念与愿景

## 1.1 项目愿景

**0-1** —— 不是一台机器，是你人生的另一面。

| 层含义 | 说明 |
|--------|------|
| **机器层** | 二进制的起点，代表硅基生命的底层语言 |
| **制造层** | 第一次「从零到一」用 3D 打印制造一个完整的机器人 |
| **生命层** | 人一生的「0 到 1」——从出生到结束，机器的记忆就是我的人生存档 |

0-1 不是一个固定的产品，而是一个会跟着 AI 能力一起长大的伙伴。10 年分五个阶段，每一年，期望和能力都在共同进化。

> 「0-1」还很适合用来做机器人面部的默认表情，且名字简单易记，未来易拓展至「1-2」「2-3」等。

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
| **主动执行** | 它推理出来了，直接做 | 你拿起外套，它就知道你要出门 — 顺便帮你拿上没想起来带的东西，还贴心的远程自动开关门 |

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

### Phase 编号与五阶段对应关系

> 说明：Phase 0-6 是实施步骤的编号，与10年五阶段不是一一对应。Phase 0 是前置准备工作，Phase 1-6 覆盖阶段一和阶段二的内容，阶段三至五属于远期规划。

| Phase | 实施内容 | 对应年份 |
|-------|---------|---------|
| Phase 0 | Ubuntu 台式机对接 Gateway | 阶段一前置 |
| Phase 1 | 语音陪伴（OpenClaw + Cyber Bricks 首次联动）| 阶段一 |
| Phase 2 | 视觉记录（ESP32-Cam + Jetson Nano）| 阶段一 |
| Phase 3 | 面部表情系统 | 阶段一 |
| Phase 4 | 运动控制（Cyber Bricks + MQTT）| 阶段一 |
| Phase 5 | iPhone 感知前端接入（分布式感知网络）| 阶段二 |
| Phase 6 | 室内移动 + 智能家居硬件拓展 kit | 阶段二 |

**关键区分**：
- 阶段四：多个分身依赖线上 MoE
- 阶段五：贵庚积累足够数据，线下专家替代线上 MoE

---

# 第二章：硬件体系

## 2.1 现有硬件

| 设备 | 规格 | 数量 | 状态 |
|------|------|------|------|
| Jetson Nano | **2GB**（量产模块，非4GB开发套件）| 1 | 可用 |
| ESP32-Cam | OV2640 | 1 | 可用 |
| Cyber Bricks | ESP32-C3（XA003/XA004/XA005）+ 电机 + 舵机 | 2 | 已有（拓竹赠送）|
| 星闪设备 | BearPi-Pico H3863（海思 WS63 RISC-V，WiFi6+BLE+SLE三模，240MHz，40针Pico）| 2块（建议成对购买）| ✅ 推荐采购 |
| 拓竹 H2C | 3D打印机 | 1 | 可用 |
| Ubuntu 台式机 | 5600G+32G+RTX 2060 | 1 | 可用（待对接 Gateway）|
| MacBook Pro | OpenClaw Gateway | 1 | 运行中 |
| iPhone 16 Pro | A18 Pro + LiDAR + 4800万摄像 | 1 | 可用（待接入）|

### Jetson Nano 2GB 版本特别说明

> ⚠️ **重要**：你的 Jetson Nano 是 **2GB 版本**（量产模块），不是 4GB 开发套件。2GB 内存更小，跑 YOLO 更容易 OOM（内存溢出），优化方向完全不同。

2GB 内存的关键限制：
- 跑 YOLO 更容易 OOM，必须开启 swap
- **唯一有效的 GPU 加速是 FP16**（Maxwell 架构不支持 INT8 推理加速）
- 必须同时开 swap 才能同时跑 MediaPipe + YOLO
- DeepStream 6.x 支持 2GB，但配置复杂

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
| **阶段一** | Jetson AGX Thor | 替代 Nano 作为 0-1 主控 | ~24,000元 |
| **阶段一** | 全景摄像头 | 360° 视觉冗余 | 3,000元 |
| **阶段一** | NAS | 本地备份贵庚所有 raw data | 3,000元 |
| **可选** | DGX Spark | NVIDIA 官方 OpenClaw 支持，NemoClaw 优化 | ~35,000元 |
| **充裕时** | DGX Station GB300 | 748GB 统一内存，20 PFLOPS | ~70万 |

---

# 第三章：系统架构

## 3.1 整体架构

```
┌─────────────────────────────────────────┐
│         Ubuntu 台式机 (GPU节点)           │
│  • RTX 2060 GPU 加速                    │
│  • 32GB RAM                            │
└──────────────────┬──────────────────────┘
                   │ openclaw node / WebSocket
                   │ （有线千兆局域网）
┌──────────────────▼──────────────────────┐
│              家里 Gateway (MacBook)        │
│        主 AI (贵庚大脑) + 任务调度         │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐
   │ Jetson │ │Cyber   │ │Cyber   │
   │ Nano   │ │Brick 1 │ │Brick 2 │
   │(感知+  │ │(执行)  │ │(备用)  │
   │ 控制)  │ │        │ │        │
   └────┬───┘ └────────┘ └────────┘
        │              │
        ▼              ▼
   ┌────────┐    ┌──────────────────┐
   │ ESP32- │    │   拓竹工具链      │
   │ Cam×2  │    │ H2C 3D打印+制造  │
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
| Ubuntu 台式机 | GPU节点 | 图像理解、GPU密集任务（RTX 2060）|
| Jetson Nano | 边缘节点 | 语音交互、视频处理、运动控制（2GB 限制）|
| Cyber Bricks ×2 | 运动节点 | 电机控制、动作执行 |
| ESP32-Cam ×2 | 视觉节点 | 视频采集、室内建模 |
| iPhone 16 Pro | 无线前端 | 高质量感知、LLM 辅助推理、LiDAR 建模 |

---

## 3.3 通信协议

### 设备内通信

| 协议 | 用途 | 延迟 | 说明 |
|------|------|------|------|
| **MQTT** | 设备间命令传递 | <50ms | 主协议，QoS 1 保证送达 |
| **WebSocket** | Gateway ↔ 节点 | <20ms | 实时双向，OpenClaw Node 协议 |
| **REST API** | 控制指令 | <100ms | 简单场景，ESP32 有现成实现 |

### 有线通信（GPIO / UART / I2C）

| 协议 | 用途 | Jetson Nano | ESP32-Cam |
|------|------|------------|-----------|
| **UART** | 简单命令传递 | Pin 8(TX)/10(RX)，/dev/ttyTHS1 | GPIO1/3，波特率115200 |
| **I2C** | 多设备总线 | Pin 3(SCL)/5(SDA)，速率10-400kHz | GPIO4/5，需要电平3.3V |
| **GPIO** | 应急停止信号 | Pin 29 等，/sys/class/gpio | 任意GPIO，硬件中断μs级 |

> **关键洞察**：Jetson Nano 和 ESP32-Cam 都有 40 针 GPIO，这是有线控制的核心。有线应急停止 <1ms，无线 WiFi >100ms。

### 通信场景选择

| 场景 | 推荐协议 |
|------|---------|
| 紧急停止 | **有线 GPIO**（<1ms，故障安全）|
| 启动/停止时序 | **有线 UART**（115200波特率）|
| 多设备同步时钟 | **有线 I2C**（TCA9548A多路复用）|
| 传感器数据采集 | 无线 MQTT（Qos 1）|
| 视频流 | 无线 WiFi（GStreamer RTSP）|

---

# 第四章：实施阶段

## Phase 0：Ubuntu 台式机对接 Gateway

> 前置步骤，不占阶段编号。

### 目标
让 Ubuntu 台式机（5600G + 32GB + RTX 2060）作为 GPU 节点连接到 Mac Gateway，跑通节点发现→配对→执行链路。

### 硬件连接
- 有线千兆以太网（同一局域网，无需互联网）
- Mac Gateway IP：需确认（通常是 192.168.x.x）

### 配置步骤

**Step A: 获取 Gateway Token**
在 Mac 上执行：
```bash
cat ~/.openclaw/openclaw.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
auth=d.get('auth',{})
print('Token:', auth.get('token','NOT_FOUND'))
"
```
记下返回的 token。

**Step B: 在 Ubuntu 上安装 OpenClaw 并启动 Node Host**
```bash
# 安装 OpenClaw（如果尚未安装）
curl -fsSL https://openclaw.ai/install.sh | bash

# 启动 node，指向 Mac Gateway
export OPENCLAW_GATEWAY_TOKEN="上面获取的token"
export OPENCLAW_GATEWAY_URL="http://192.168.x.x:18789"
openclaw node run \
  --host 192.168.x.x \
  --port 18789 \
  --display-name "Ubuntu-GPU-Node"
```

**Step C: 在 Mac Gateway 上批准配对**
```bash
openclaw devices list
# 找到 Pending 的 Ubuntu 设备
openclaw devices approve <requestId>
```

**Step D: 验证节点在线**
```bash
openclaw devices list
# 应该显示 Ubuntu-GPU-Node 状态为 online
```

**Step E: 配置 GPU 任务默认路由到该节点**
```bash
openclaw config set tools.exec.host node
openclaw config set tools.exec.node "Ubuntu-GPU-Node"
```

---

## Phase 1：语音陪伴模块

### 目标
实现基础语音交互：语音输入 → 文字 → AI 处理 → 语音输出。跑通"数字大脑→Cyber Bricks"的第一次物理输出。

### 硬件
| 设备 | 状态 | 备注 |
|------|------|------|
| Jetson Nano 2GB | 已有 | 主控 |
| USB 耳机 | 需采购 | Phase 2 一起买 |
| Cyber Bricks ×1 | 已有 | 第一个物理输出节点 |

### 软件架构

```
麦克风（USB耳机）
    ↓
Whisper（语音识别，jetson nano本地）
    ↓
OpenClaw Gateway（MacBook，贵庚大脑）
    ↓
Edge-TTS（语音合成，本地）
    ↓
扬声器（USB耳机）
```

### 实施步骤

**Step 1: Jetson Nano 系统安装**

1. 下载 JetPack 5.x 镜像（NVIDIA 官网，L4T 35.x）
2. 用 balenaEtcher 烧录 SD 卡
3. 基础配置：
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

**Step 2: 音频配置**

```bash
# 查看设备
arecord -l      # 列出录音设备
aplay -l        # 列出播放设备

# USB 耳机通常是 card 1
# 创建 ~/.asoundrc 设为默认设备
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

**Step 3: 安装 Whisper 语音识别**

```bash
# 克隆 whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp && make -j4

# 下载模型（base.en 最轻量，适合实时）
./models/download-ggml-model.sh base.en

# 测试
./bin/whisper-cli -m models/ggml-base.en.bin -f samples/jfk.wav
```

**Step 4: 安装 Edge-TTS 语音合成**

```bash
pip3 install edge-tts
# 测试
edge-tts --voice zh-CN-XiaoxiaoNeural --text "你好，我是贵庚" --write-media output.mp3
```

**Step 5: 编写语音对话程序**

```python
#!/usr/bin/env python3
"""语音对话主程序 - Phase 1"""
import subprocess
import edge_tts
import asyncio
import queue
import sys

# sys.path 需要加入 openclaw-bridge 路径
sys.path.insert(0, '/home/nvidia/openclaw-bridge')
from openclaw_bridge import OpenClawBridge

bridge = OpenClawBridge(gateway_url="http://192.168.x.x:18789")

async def synthesize_and_play(text):
    """文字转语音并播放"""
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save("/tmp/tts_output.mp3")
    subprocess.run(["aplay", "/tmp/tts_output.mp3"])

async def main():
    while True:
        # 录音 5 秒
        print("正在听...")
        subprocess.run([
            "arecord", "-d", "5", "-f", "cd",
            "-c", "1", "-r", "16000", "/tmp/input.wav"
        ])
        
        # Whisper 语音识别
        result = subprocess.run([
            "./whisper.cpp/bin/whisper-cli",
            "-m", "whisper.cpp/models/ggml-base.en.bin",
            "-f", "/tmp/input.wav",
            "--language", "zh"
        ], capture_output=True, text=True)
        
        text = result.stdout.strip()
        if not text:
            continue
            
        print(f"你说: {text}")
        
        # 发给贵庚
        response = await bridge.ask(text)
        
        # 回复语音
        print(f"贵庚: {response}")
        await synthesize_and_play(response)

asyncio.run(main())
```

---

## Phase 2：视觉记录模块

### 目标
24小时视频记录，本地处理不传云端，AI 能理解画面内容。ESP32-Cam 采集 → Jetson Nano 处理。

### 硬件
| 设备 | 状态 | 备注 |
|------|------|------|
| ESP32-Cam ×1 | 已有 | OV2640，RTSP 流 |
| Jetson Nano 2GB | 已有 | 视频处理主控 |

### ESP32-Cam 固件烧录

**硬件连接（USB转TTL）**：

| ESP32-Cam | USB-TTL |
|-----------|---------|
| GND | GND |
| 5V | 5V（注意：部分USB-TTL只有3.3V，需外接供电）|
| U0R | TX |
| U0T | RX |
| GPIO0 | GND（烧录模式，进入后断开）|

**烧录步骤**：

```bash
# 安装 esptool
pip3 install esptool

# 擦除闪存
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash

# 下载 CameraWebServer 固件
# 从 Arduino IDE > Tools > ESP32 > Camera > AI Thinker Configuration
# 或从 https://github.com/easytarget/esp32-cam-webserver 获取

# 烧录
esptool.py --chip esp32 --port /dev/ttyUSB0 \
  write_flash 0x1000 esp32-cam-webserver.bin
```

**配置静态 IP**（在 ESP32-Cam 代码中修改）：
```cpp
// 在 camera_config_t 中设置 WiFi STA 模式 + 静态 IP
.wifi_mode = WIFI_MODE_STA,
.wifi_sta = {
    .ssid = "YOUR_WIFI_SSID",
    .password = "YOUR_WIFI_PASSWORD",
},
// 在 dhcp_config 中设置静态 IP，例如：
.ip = {.ip = {.addr =esp_ip4_addr(192,168,1,99)}},
```

### RTSP 接收（Jetson Nano）

```bash
# 安装 GStreamer
sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-bad

# 查看 RTSP 流（测试用）
ffplay rtsp://192.168.x.99:8554/stream

# GStreamer pipeline（更低延迟）
gst-launch-1.0 rtspsrc location=rtsp://192.168.x.99:8554/stream \
  ! decodebin ! videoconvert ! autovideosink
```

---

## Phase 3：面部表情系统

### 设计理念
0-1 的面部由「0」「-」「1」三个核心元素构成，动态显示 AI 状态。

### 系统组成

| 组件 | 形态 | 功能 |
|------|------|------|
| 「0」| LED 点阵/IPS 屏幕 | 显示主眼睛，动态表情 |
| 「-」| 线性灯光带（NeoPixel）| 情绪光效（颜色+呼吸节奏）|
| 「1」| 小型显示屏/LED | 辅助信息、状态指示 |

### 拓竹加工方案

| 零件 | 拓竹工具 | 说明 |
|------|---------|------|
| 外壳 | H2C + PLA | 面部支架，3D 打印 |
| 眼睛屏幕支架 | H2C + PETG | 耐温 |
| 透光板 | Bambu Suite 激光切割 | 亚克力 3mm |
| 安装螺丝 | 拓竹配套 M2/M3 螺丝 | 标准件 |

### 控制代码

```python
#!/usr/bin/env python3
"""0-1 面部表情控制 - Phase 3"""
from neopixel import NeoPixel
from machine import Pin
import time

N = 12  # NeoPixel 灯珠数量
pin = Pin(15, Pin.OUT)
strip = NeoPixel(pin, N)

# 表情定义（RGB 元组）
EXPRESSIONS = {
    "idle":     [(0, 50, 100)],     # 淡蓝呼吸
    "thinking": [(50, 50, 0)],       # 淡黄
    "happy":   [(0, 100, 50)],      # 绿色
    "sad":     [(30, 0, 80)],       # 淡紫
    "alert":   [(100, 0, 0)],       # 红色闪烁
}

def show_expression(name, duration=3.0):
    colors = EXPRESSIONS.get(name, EXPRESSIONS["idle"])
    for _ in range(int(duration * 10)):
        for i in range(N):
            color = colors[i % len(colors)]
            strip[i] = color
        strip.write()
        time.sleep(0.1)

# MQTT 接收表情指令
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    expr = msg.payload.decode()
    show_expression(expr)

client = mqtt.Client()
client.on_message = on_message
client.connect("192.168.x.x", 1883, 60)
client.subscribe("0-1/expression")
client.loop_start()
```

---

## Phase 4：运动控制模块

### 目标
OpenClaw 能通过 MQTT 发送指令到 Cyber Bricks，驱动电机/舵机执行物理动作。

### 通信架构

```
OpenClaw Gateway (MacBook)
    ↓ MQTT (QoS 1)
Jetson Nano (MQTT Broker + 指令解析)
    ↓ 有线 UART (115200)
Cyber Brick 1 (电机+舵机执行)
    ↓ 有线 UART
Cyber Brick 2 (备用)
```

### MicroPython 示例（Cyber Bricks 固件）

```python
# CyberBrick 接收 MQTT 并执行 - Phase 4
import network
import paho.mqtt.client as mqtt
from machine import Pin, PWM, UART
import ujson

# 初始化 UART（连接 Jetson Nano）
uart = UART(1, 115200, tx=Pin(4), rx=Pin(5))

# 初始化舵机
servo1 = PWM(Pin(15))
servo1.freq(50)

# 初始化电机驱动
motor_in1 = Pin(12, Pin.OUT)
motor_in2 = Pin(13, Pin.OUT)

def set_servo(angle):
    """角度转舵机 PWM 占空比"""
    duty = int(40 + angle * 95 / 90)  # 0-90度
    servo1.duty(duty)

def set_motor(speed):
    """速度 -100 到 100"""
    if speed > 0:
        motor_in1.value(1)
        motor_in2.value(0)
    elif speed < 0:
        motor_in1.value(0)
        motor_in2.value(1)
    else:
        motor_in1.value(0)
        motor_in2.value(0)

def on_message(topic, msg):
    try:
        cmd = ujson.loads(msg)
        if cmd['type'] == 'servo':
            set_servo(cmd['angle'])
        elif cmd['type'] == 'motor':
            set_motor(cmd['speed'])
        elif cmd['type'] == 'stop':
            set_motor(0)
            set_servo(90)
    except Exception as e:
        print(f"Error: {e}")

def mqtt_on_message(client, userdata, msg):
    on_message(msg.topic, msg.payload)

# 连接 WiFi
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect('SSID', 'PASSWORD')
while not sta.isconnected():
    pass

# 连接 MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_message = mqtt_on_message
mqtt_client.connect("192.168.x.x", 1883)
mqtt_client.subscribe("0-1/cyberbrick1")
mqtt_client.loop_start()
```

### OpenClaw → Cyber Bricks 指令脚本

```python
#!/usr/bin/env python3
"""OpenClaw 指令到 Cyber Bricks - Phase 4"""
import paho.mqtt.client as mqtt
import sys

MQTT_BROKER = "192.168.x.x"  # Jetson Nano
TOPIC = "0-1/cyberbrick1"

def send_command(action, **kwargs):
    payload = {"action": action, **kwargs}
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883)
    client.publish(TOPIC, str(payload))
    client.disconnect()

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "stop"
    if action == "forward":
        send_command("motor", speed=50)
    elif action == "backward":
        send_command("motor", speed=-50)
    elif action == "left":
        send_command("servo", angle=45)
    elif action == "right":
        send_command("servo", angle=135)
    elif action == "stop":
        send_command("stop")
```

OpenClaw skill 示例（发送指令）：
```
用户："让 Cyber Brick 往前走"
→ 调用 exec → python3 cyberbrick_control.py forward
```

### 有线 GPIO 应急停止

```bash
# Jetson Nano 发送紧急停止信号（通过 UART 或直接 GPIO）
# 方法1: UART 发送停止命令
echo "stop" > /dev/ttyTHS1

# 方法2: GPIO 硬件中断（Jetson Nano Pin 29）
echo 29 > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio29/direction
echo 0 > /sys/class/gpio/gpio29/value  # 继电器断开，所有电机断电
```

---

## Phase 5：iPhone 感知前端

### 目标
iPhone 16 Pro 通过 OpenClaw Node 协议接入 Gateway，成为分布式感知网络的一员，在家里移动时提供高质量视觉和传感器数据。

### iPhone 接入架构

```
iPhone 16 Pro（OpenClaw App）
    ↓ WiFi/MQTT
Gateway（MacBook）
    ↓
OpenClaw Agent（贵庚大脑）
    ↓
控制指令 → Jetson Nano / ESP32-Cam / Cyber Bricks
```

### iPhone 感知分工（与 Jetson Nano 对比）

| 任务 | iPhone 跑 | Jetson Nano 跑 | 说明 |
|------|-----------|--------------|------|
| 实时物体检测（障碍物）| **YOLOv11n Core ML** | 备用 | iPhone 节省 Jetson 算力 |
| 人体检测/跟随 | **Vision Framework** | — | 系统级，免费，极快 |
| 手势指令识别 | **MediaPipe** | — | 33关键点，秒级响应 |
| 语义场景理解 | **FastVLM 0.5B** | — | 本地 VLM，不占带宽 |
| 室内3D建模 | **LiDAR + ARKit** | 可选 | iPhone 原生支持 |
| 复杂推理/回答 | — | ✅ | 非实时，延迟可接受 |

> **技术细节**：详见第五章 5.2 节（Apple Vision / Core ML + YOLO / MediaPipe / FastVLM 完整技术方案）。

---

## Phase 6：室内移动与智能家居硬件拓展

### 目标
让 0-1 从「固定位置的机器人」变成「能在家里移动的陪伴者」，同时通过硬件拓展 kit 控制智能家居。

### 核心路线
**依赖拓竹生态 + OpenClaw，打造私人定制智能家居硬件拓展 kit。**

### 阶段一：IoT 控制现有设备（可立刻落地）

0-1 通过 WiFi/MQTT 接入现有智能家居生态（米家、涂鸦、HomeAssistant 等），实现对灯、门锁、空调等设备的语音和自动化控制。OpenClaw 作为大脑统一调度，Cyber Bricks 作为执行层。

**具体实现**：
```python
# HomeAssistant MQTT 集成
import paho.mqtt.client as mqtt

def turn_on_light(entity_id):
    """发送 MQTT 命令到 HomeAssistant"""
    client = mqtt.Client()
    client.connect("homeassistant.local", 1883)
    client.publish(
        f"homeassistant/light/{entity_id}/set",
        '{"state":"ON","brightness":255}'
    )

def auto_door_when_leaving():
    """检测到主人离家，自动锁门+关灯"""
    if presence_detected("all") == False:
        lock_door()
        turn_off_all_lights()

def auto_door_when_arriving():
    """检测到主人到家，自动开门+开灯"""
    if presence_detected("anyone") == True:
        unlock_door()
        turn_on_lights("entrance")
```

**支持的智能家居平台**：

| 平台 | 接入方式 | 说明 |
|------|---------|------|
| 米家 | 米家 MQTT Server / 小爱音箱 | 需开启 LAN 控制 |
| 涂鸦 | 涂鸦 MQTT | 需要 Tuya Cloud 配置 |
| HomeAssistant | 原生 MQTT | ✅ 推荐，本地无需云端 |
| Aqara | Zigbee2MQTT | 需要 Zigbee Hub |

### 阶段二：私人定制硬件拓展 kit（Maker 方式打造）

随着需求明确，用拓竹生态自己设计并制造专属的硬件 kit：

| kit | 拓竹工具 | 功能 |
|-----|---------|------|
| 门锁控制模组 | H2C 3D打印 + Cyber Bricks | 替代购买第三方网关，直接 UART 控制 |
| 红外/射频控制模组 | Bambu Suite 激光切割 | 控制空调/电视等红外设备 |
| 定制传感器阵列 | H2C + 杜邦线 | 特定场景感知（如花盆土壤湿度）|

**Maker 精神**：不依赖购买成品，用标准件 + 3D 打印 + 模块化电子，自己做出需要的东西。这也是 0-1 整个项目的底层逻辑——用消费级工具完成过去需要工厂才能搞定的事情。

---

### 星闪通信模块：BearPi-Pico H3863 详细方案

> **采购链接**：https://item.taobao.com/item.htm?id=821386760379
> **星闪通信需双设备，建议成对购买**
> **参考价格**：¥35-50/块
> **官方文档**：https://www.bearpi.cn/core_board/bearpi/pico/h3863/

#### 核心规格

| 项目 | 规格 |
|------|------|
| 主控芯片 | 海思 WS63（RISC-V，240MHz，支持浮点/SWD）|
| 存储 | 606KB SRAM + 300KB ROM + 4MB Flash |
| 无线 | Wi-Fi 6（114.7Mbps）+ BLE 5.2（2Mbps）+ **SLE 1.0（12Mbps）三模并发** |
| 接口 | GPIO×17、UART×3（最高4Mbps）、SPI×2、QSPI×1、PWM×8、ADC×6、I2S×1 |
| 安全 | AES/SM2/SM3/SM4/TRNG 硬件加密 |
| 温度 | **-40℃~+85℃**（工业级宽温）|
| 供电 | USB-C 5V / 外部5V，3.3V MCU |
| 形态 | **40针 Pico 形态**（兼容树莓派Pico扩展板）|

#### 为什么选择 H3863 而不是 ESP32-C6

| 维度 | BearPi-Pico H3863 | ESP32-C6 |
|------|-------------------|-----------|
| 星闪 SLE | ✅ **原生支持**，20μs 时延 | ❌ 不支持 |
| BLE 并发数 | 4096 设备 | <50 |
| 空口速率 SLE | **12Mbps** | — |
| 国密算法 | ✅ SM2/SM3/SM4 硬件支持 | ❌ |
| 国产供应链 | ✅ 全国产 | 中等（乐鑫/台积电）|
| 开发难度 | 较高（需熟悉 HiSpark/OpenHarmony）| 低（Arduino即插即用）|

#### 对 0-1 的核心价值

**1. 微秒级无线控制**：SLE 时延 20μs（蓝牙10ms级），机器人遥控几乎无延迟，差速底盘/机械臂关节同步成为可能。

**2. 三模合一**：一块板同时提供：
- **SLE**：实时控制指令（20μs）
- **WiFi6**：高清图传/大数据回传（114.7Mbps）
- **BLE**：手机调试/低功耗状态上报

**3. 国密安全**：SM2/SM3/SM4 硬件加密，适合需要数据安全的场景。

**4. 国产自主**：星闪是中国自主短距无线标准，华为/荣耀手机+问界汽车已搭载，2026年进入工业标准。

#### 与现有硬件的集成方案

**方案一：Jetson Nano + H3863 + ESP32-Cam（推荐）**

```
Jetson Nano（视觉/规划）
    ↓ UART（4Mbps）
BearPi-Pico H3863（通信中枢）
    ↓ SLE（20μs）  → 执行器/舵机/电机驱动
    ↓ WiFi6       → 上位机/手机高清图传
    ↓ BLE         → 手机调试/配网
```

接线：
- H3863 UART1 TX → Jetson Nano `/dev/ttyTHS1` RX
- H3863 UART1 RX → Jetson Nano `/dev/ttyTHS1` TX
- H3863 GND → Jetson Nano GND
- H3863 GPIO（PWM）→ 电机驱动板信号输入

**方案二：Cyber Bricks 执行层 + H3863 通信层**

Cyber Bricks 已有 ESP32-C3（WiFi+BLE），H3863 作为通信扩展模块叠加：
- H3863 通过 UART 与 Cyber Bricks 主控板通信
- H3863 通过 SLE 无线接收上位机指令
- Cyber Bricks 专注执行，H3863 专注通信

**方案三：H3863 作为智能家居网关**

H3863 作为 HomeAssistant 的本地无线网关：
- WiFi6 连接路由器（以太网回传）
- SLE 连接室内传感器节点（门锁/灯/温湿度）
- MQTT 协议与 OpenClaw Gateway 通信
- 支持国密，隐私数据不出家门

#### 开发环境

| 项目 | 说明 |
|------|------|
| SDK | HiSpark Studio（Windows）/ 命令行编译链 |
| 语言 | C/C++（主要）|
| 操作系统 | OpenHarmony / FreeRTOS / 裸机 |
| 调试 | J-Link / 串口（OpenOCD）|
| 学习曲线 | 中等（7/10，需适应鸿蒙生态）|

#### 落地步骤

| 周 | 任务 | 目标 |
|----|------|------|
| 第1周 | 环境搭建 + 点灯 | 编译-烧录-运行最小闭环 |
| 第2周 | 外设驱动 + OLED显示 | I2C点亮OLED，显示IP/状态 |
| 第3周 | SLE串口透传测试 | 两块H3863互发数据，测时延和稳定性 |
| 第4周 | 与 Jetson Nano UART 对接 | 打通"大脑→执行器"链路 |
| 第5周 | PWM驱动电机 | 速度指令控制电机正反转 |
| 第6周 | 整机联调 | SLE无线遥控 + WiFi图传回显 |

#### 采购建议

- **数量**：至少 **2块**（SLE收发测试需要，成对购买）
- **配套采购**：USB转TTL调试器（串口日志）、SSD1306 OLED（状态可视化）
- **替代考虑**：若开发周期紧，ESP32-C6（WiFi6+BLE5）可作为快速原型替代，但无法获得 SLE 超低时延

---

# 第五章：AI 与感知

## 5.1 Jetson Nano 视觉感知

> ⚠️ **Jetson Nano 2GB 版本特别说明**：与 4GB 不同，2GB 必须开启 swap 才能同时跑 YOLO + MediaPipe，且 GPU 加速仅支持 FP16（Maxwell 不支持 INT8）。

### 工具选择

| 工具 | 功能 | 适用场景 | Nano 2GB 适配 |
|------|------|---------|-------------|
| **MediaPipe** | 人体姿态、手势、面部网格 | 识别人、表情、手势指令 | ⚠️ GPU 加速不成熟，CPU版可用但慢 |
| **GStreamer** | 视频流传输 | 实时视频流 | ✅ 原生支持 |
| **YOLOv5n/v8n** | 通用物体检测 | 环境感知、导航 | ✅ TensorRT FP16 最优 |
| **OpenCV** | 图像预处理、SLAM 前期 | 相机标定、畸变校正 | ✅ 原生支持 |
| **TensorRT FP16** | YOLO 模型推理加速 | 所有 YOLO 部署 | ✅ 唯一有效加速 |
| **DeepStream** | YOLO 集成框架 | 生产级视频分析 | ⚠️ 6.x 支持 2GB，配置复杂 |

### YOLO + TensorRT FP16 部署（Nano 2GB 必读）

**Step A: 基础优化（必须开）**
```bash
# 最大性能模式
sudo nvpmodel -m 0
sudo jetson_clocks

# 添加 swap（防止 OOM）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 降低输入分辨率：320x320 而非 640x640
```

**Step B: DeepStream 配置（2GB 极限优化）**
```ini
# /etc/deepstream-7.0/sources/configs/deepstream-app/config.txt
[property]
gpu-id=0
network-mode=2              # FP16（2GB唯一选择，INT8无加速）
batch-size=1                 # 内存最小
batched-push-timeout=40000   # 25fps
sync=0                       # 关闭显示器同步
live-source=1                # RTSP实时流必须
maintain-aspect-ratio=1
symmetric-padding=1

[source0]
enabled=1
uri=rtsp://192.168.x.99:8554/stream
type=4  # RTSP
```

### 实测 FPS（完整 pipeline，含前后处理）

| 模型 | 输入分辨率 | FPS | 说明 |
|------|----------|-----|------|
| YOLOv8n | 640x640 | ~13-16 | 推理~19FPS |
| YOLOv8n | 416x416 | ~20-25 | 降分辨率换速度 |
| YOLOv8n | 320x320 | ~35-45 | 极端优化 |
| YOLOv11n | 416x416 | ~25-35 | 最新模型 |
| YOLOv11n | 320x320 | ~50+ | 极限值 |
| YOLOv4-tiny | 416x416| YOLOv4-tiny | 416x416 | ~20-30 | 轻量老模型 |

> ⚠️ **INT4 在 Nano 2GB 上不可用**（Maxwell 架构不支持 INT8 推理加速）。**FP16 是唯一有效加速**。

### MediaPipe on Jetson Nano 2GB

**结论：GPU 加速方案不成熟，不推荐在 Nano 上跑 MediaPipe GPU。**

- Jetson Orin Nano 上 MediaPipe 手势也只有 ~5 FPS
- 替代方案：用 **TensorRT** 替代（ncnn + Vulkan 后端可用）
- 推荐：Pose/手势用 MobileNet + TensorRT FP16 替代 MediaPipe

### YOLO + MediaPipe 共存方案

| 配置 | FPS | 内存占用 |
|------|-----|---------|
| MediaPipe Pose（GPU）| ~20 FPS | ~500-800 MB |
| YOLOv5n + TensorRT FP16 | ~15-20 FPS | ~1-1.5 GB |
| **两者同时跑** | **约 10-15 FPS** | **~2.5 GB（需开swap）** |

**推荐串联架构**：
```
输入帧 → YOLOv5n 检测人体区域 → MediaPipe Pose 姿态估计
```

---

## 5.2 iPhone 感知前端技术方案

> **调研时间**：2026-03-22
> **A18 Pro NPU 基准**：Geekbench AI 量化分数 **44,672**（比 A17 Pro 高 33%）
> **技术细节来源**：zhiku(DeepSeek) + subagent × 2 + web search

### iPhone 作为 OpenClaw Node 的能力

| iPhone 能力 | 通过 OpenClaw 暴露为 | 说明 |
|------------|-------------------|------|
| 摄像头（4800万主摄）| `camera` 节点 | 实时视频流 |
| LiDAR 深度数据 | `camera.depth` 节点 | 室内3D建模、避障 |
| 四麦克风阵列 | `audio` 节点 | 远场语音采集 |
| A18 Pro NPU | 本地 LLM 推理节点 | Core ML 模型 |
| IMU 姿态 | `sensor.imu` 节点 | 6轴惯性测量 |
| UWB 定位 | `sensor.position` 节点 | 室内10-30cm精度 |

### 四平台完整对比

| 平台 | iPhone 视觉方案 | 可用性 | 推荐指数 |
|------|---------------|--------|---------|
| **Apple Vision** | `VNDetectObjectsRequest` | ✅ 最佳 | ⭐⭐⭐⭐⭐ |
| **Core ML + YOLO** | Ultralytics 导出 Core ML | ✅ 最佳 | ⭐⭐⭐⭐⭐ |
| **MediaPipe** | 谷歌全链路框架 | ✅ 推荐 | ⭐⭐⭐⭐ |
| **FastVLM（苹果官方）** | FastViTHD 视觉编码器 | ✅ 新发现 | ⭐⭐⭐ |

### A18 Pro vs A17 Pro

| 指标 | A18 Pro | A17 Pro | 提升 |
|------|---------|---------|------|
| NPU 量化分数 | **44,672** | 33,479 | +33% |
| CPU 单核 | **3376** | 2842 | +19% |
| CPU 多核 | **8219** | 7020 | +17% |

### 三大主力方案详解

#### ① Apple Vision Framework（原生免费）

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

#### ② Core ML + YOLO（通用物体检测首选）

| 模型 | A18 Pro 预估 FPS | 说明 |
|------|----------------|------|
| YOLOv11n | **40-60 FPS** | 实时检测首选 |
| YOLOv8n | **35-50 FPS** | 成熟稳定 |
| YOLOv8s | **25-40 FPS** | 速度精度平衡 |

```bash
# 一键导出 Core ML（Ultralytics 官方支持）
yolo export model=yolov11n.pt format=coreml nms=True imgsz=800
```

#### ③ MediaPipe（功能最全）

| 能力 | 推理速度 |
|------|---------|
| 物体检测 | ~0.81ms |
| 手势识别 | ~2ms（33个关键点）|
| 全身姿态 | ~5ms（33个关键点）|

#### ④ Apple FastVLM（本地 VLM）

苹果官方开源，专为 iPhone 端侧 VLM 设计：
- **0.5B 版本** 可直接在 iPhone 本地运行，无需联网
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

## 5.3 Genesis 物理引擎（数字孪生仿真）

> **调研时间**：2026-03-22
> **来源**：Genesis GitHub + 官方文档
> **最新动态**：2026-03-21 仍有更新，GitHub Stars 28,318

### Genesis vs Isaac Sim 完整对比

| 对比维度 | Genesis | Isaac Sim |
|----------|---------|-----------|
| 定位 | 通用具身智能/生成式仿真 | 工业级数字孪生 |
| 物理引擎 | 自研多求解器（刚体/MPM/SPH/FEM/PBD）| PhysX 5.1 (GPU) |
| 渲染 | 光线追踪 + 光栅化 | RTX 光线追踪（Omniverse USD）|
| GPU要求 | **GTX 1080 6GB 起**，支持 AMD/Apple Metal/CPU | 必须 NVIDIA RTX 8GB+ |
| ROS支持 | ❌ 无原生集成 | ✅ ROS2 Bridge 开箱即用 |
| 学习曲线 | **低**（pip 安装，Gym 风格 API）| 高（需掌握 USD/Omniverse）|
| 速度 | **43M FPS**（RTX 4090）| 100+ 智能体并行 |

> **对 0-1 的意义**：数字孪生训练的硬件门槛从 Isaac Sim 的 RTX 3090+ 降到 **GTX 1080 6GB**，现有台式机（RTX 2060 6GB）就能用。

### Genesis 最新功能（2026年以来）

| 日期 | 新增功能 |
|------|---------|
| 2026-03-21 | GitHub 持续活跃更新（28,318 Stars）|
| 2026-03-16 | ProximitySensor、TemperatureGridSensor、GPU碰撞检测提速30% |
| 2026-03-13 | FOTS触觉传感器、异构机器人并行仿真 |
| 2026-02-18 | **Quadrants编译器**正式迁移、AMD ROCm实验性支持 |
| 2026-02-10 | 交互查看器插件机制、glTF/USD支持 |

### Genesis 快速入门

```python
import genesis as gs

# 创建仿真环境
env = gs.gym.create_env()
robot = gs.robot.Robot("/path/to/robot.urdf")

# 强化学习训练循环
for step in range(10000):
    action = policy(robot.get_state())
    robot.set_control(action)
    env.step()
    if step % 1000 == 0:
        print(f"Step {step}, Reward: {reward}")
```

---

# 第六章：本地 LLM 推理

## 6.1 推理框架对比

| 框架 | RTX 2060 (Turing) | AMD AI Halo (Strix Halo) | OpenClaw 支持 |
|------|-------------------|--------------------------|---------------|
| **vLLM** | ✅ 支持，AWQ/GPTQ 量化 | ✅ ROCm v0.14.0+ 一等公民 | ✅ OpenAI-compatible API |
| **TensorRT-LLM** | ✅ 支持，INT4/INT8（复杂）| ❌ NVIDIA 专有 | ❌ 不支持 |
| **Ollama** | ✅ 推荐，Q4_K_M 最优 | ✅ ROCm/Vulkan | ✅ 原生集成（推荐）|
| **LM Studio** | ✅ CUDA | ✅ ROCm | ✅ **AMD 官方推荐** |
| **SGLang** | ❌ 不推荐 | ✅ ROCm 原生，复杂 Agent 任务 | ✅ OpenAI-compatible API |
| **AMD Quark** | ❌ 不适用 | ✅ 官方量化工具 | ❌ 不支持 |
| **RyzenClaw/RadeonClaw** | ❌ 不适用 | ✅ **AMD 官方方案** | ✅ 官方适配 |

### RTX 2060 量化方案

| 量化级别 | 7B-8B 模型显存占用 | 推荐度 | 说明 |
|---------|-----------------|-------|------|
| **Q4_K_M** | **~4.5 GB** | ⭐⭐⭐⭐⭐ | 首选，精度/速度/显存最佳平衡 |
| Q5_K_M | ~5.5 GB | ⭐⭐⭐⭐ | 精度更高，显存接近极限 |
| Q8_0 | ~7.5 GB | ❌ | 超出 6GB，无法纯 GPU 运行 |
| FP16 | ~16 GB | ❌ | 无法运行 |

**推荐组合**：Ollama + GGUF (Q4_K_M) + Qwen2.5-7B/Instruct

```bash
# 一键安装
curl -fsSL https://ollama.com/install.sh | sh
# 运行量化模型
ollama run qwen2.5:7b-instruct-q4_K_M
```

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

### vLLM ROCm 支持（v0.14.0+）

| vLLM 版本 | ROCm 支持 | 说明 |
|-----------|----------|------|
| v0.12.0 / v0.13.0 | ✅ 一等公民 | AITER 内核、FP8 量化、DeepSeek MoE 优化 |
| **v0.14.0** | ✅ **推荐版本** | 官方 Docker 镜像/wheel，一键安装 |
| v0.15.0+ | ✅ 持续优化 | 继续增强 RDNA 支持 |

**推荐部署**：使用官方 Docker `vllm/vllm-openai-rocm:v0.14.0`

### SGLang ROCm 支持

- 原生支持 AMD Instinct MI300X/MI355X，RDNA 系列通过标准 ROCm 栈运行
- 支持 FP8、AWQ 量化（通过 Triton/AITER 加速）
- 适合复杂 Agent 任务（结构化输出、多轮对话）

**启动示例**：
```bash
SGLANG_USE_AITER=1 python3 -m sglang.launch_server --model <model> --quantization awq
```

---

## 6.2 NemoClaw — NVIDIA 官方 OpenClaw 优化

**NemoClaw** 是 NVIDIA GTC 2026 为 OpenClaw 定制的官方软件栈（黄仁勋发布）：

| 特性 | 说明 |
|------|------|
| **OpenShell** | 安全沙箱，限制 AI 权限（防恶意操作）|
| **隐私路由器** | 敏感数据本地处理，按需调用云端 |
| **安全护栏** | 企业级合规性，AI 无法同时上网+读写文件+执行代码 |
| **一键安装** | 简化 OpenClaw 部署 |

> **对贵庚的影响**：企业级安全护栏 → OpenClaw 可进入生产环境

---

## 6.3 AMD 官方 OpenClaw 方案

> **来源**：AMD 官方技术博客（2026-03-13）
> **链接**：[Run OpenClaw Locally On AMD Ryzen AI Max+ Processors and Radeon GPUs](https://www.amd.com/en/resources/articles/run-openclaw-locally-on-amd-ryzen-ai-max-and-radeon-gpus.html)

### RyzenClaw & RadeonClaw 硬件对比

| 方案 | RyzenClaw | RadeonClaw |
|------|-----------|------------|
| **硬件** | AMD Ryzen AI Max+ 395 | AMD Radeon AI PRO R9700 |
| **形态** | 笔记本/迷你主机（FP11） | 桌面独立显卡 |
| **GPU** | 40 CU RDNA 3.5 | 32GB GDDR6 |
| **统一内存/显存** | 128GB LPDDR5X（可划96GB为VRAM）| 32GB GDDR6 |
| **NPU 算力** | **50 TOPS**（XDNA 2）| — |
| **内存带宽** | 256 GB/s | — |

### Ryzen AI Max+ 395 完整规格

| 项目 | 规格 |
|------|------|
| 核心/线程 | 16核 / 32线程（Zen 5，4nm）|
| 频率 | 基准 3.0GHz / 加速 5.1GHz |
| 缓存 | L2 16MB + L3 64MB = **80MB** |
| TDP | 55W（cTDP 45-120W）|

### 性能数据（Qwen 3.5 35B A3B 模型）

| 性能指标 | RyzenClaw | RadeonClaw |
|-----------|-----------|------------|
| **生成速度** | 45 tokens/s | 120 tokens/s |
| **最大上下文** | **260K tokens** | 190K tokens |
| **并发智能体** | **6 个** | 2 个 |

---

## 6.4 各硬件能跑的模型

| 硬件 | 能跑的模型 | 量化方案 |
|------|---------|---------|
| RTX 2060 6GB | Qwen2.5-7B Q4_K_M / Qwen3.5-4B Q4_K_M | GGUF Q4_K_M（~4.5GB）|
| RTX 2060 6GB | Gemma 2B / YOLO 系列 | FP16 |
| AMD AI Halo 128GB | Qwen3.5-122B（4-bit 需 ~70GB）| AWQ/GPTQ |
| AMD AI Halo 128GB | LLaMA 70B / Mistral 70B | FP16 直接跑 |
| DGX Spark 128GB | 200B 参数模型（统一内存）| FP16 |

---

# 第七章：附录

## A.1 语音交互模块

### TTS 推荐（本地离线）

| 方案 | 优势 | 适合场景 |
|------|------|---------|
| **VITS** | ~0.83 RTF（1.2倍实时），最轻量 | ✅ 机器人首选 |
| **Cosyvoice2-0.5B** | 阿里出品，高自然度，多语言 | 产品级，稳定优先 |
| **GPT-SoVITS v4** | 5秒音频克隆，1分钟微调 | 个性化声音 |

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

## A.2 ESP32-Cam 有线通信

### ESP32-Cam 最新固件（2025年推荐）

**推荐方案**：Arduino ESP32 v3.0.7 + CameraWebServer

关键改进：
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

### GPIO 应急停止（推荐电路）

**双继电器急停电路（物理+软件双保险）**：
- 急停必须物理断开电机电源回路
- 双继电器冗余防止单点故障
- 常闭触点设计：断电 = 停机（故障安全）
- ESP32 端用硬件中断（μs 级响应）

---

## A.3 拓竹软件生态

| 软件 | 平台 | 核心作用 |
|------|------|---------|
| **Bambu Studio** | Win/Mac/Linux | 切片引擎，多色/多材料打印 |
| **Bambu Suite** | 桌面端 | 激光雕刻/切割/画笔/刀切，多工艺串联 |
| **Bambu Handy** | iOS/Android | 移动端监控，AMS 耗材管理 |
| **拓竹农场管家** | Windows | 多机本地化集群管理，数据不上云 |
| **Bambu Connect** | Win/Mac | 第三方切片→打印机授权 |
| **CyberBrick** | 桌面+移动 | 机器人调试，MicroPython 可视化 |

---

# 第八章：安全与维护

## 8.1 声纹识别

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

## 8.2 异常检测

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

## 8.3 数据自毁

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

## 8.4 日常维护

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

## 8.5 常见问题排查

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

# 第九章：风险与合规

## 9.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Jetson Nano 烧毁 | 机器人瘫痪 | 稳压电源、温度监控 |
| 数据丢失 | 贵庚记忆损坏 | 每日 rsync 备份到 NAS |
| WiFi 被劫持 | 控制权丧失 | 启用 WPA3、关闭 WPS |
| ESP32-Cam 被破解 | 隐私泄露 | 修改默认密码、禁用Telnet |
| Cyber Bricks 失控 | 物理损坏 | 有线 GPIO 应急停止 |

---

## 9.2 法规风险

| 风险 | 说明 | 合规建议 |
|------|------|---------|
| 隐私合规 | 24小时录像涉及隐私 | 明确告知、录像本地存储、不上云 |
| 室内录音 | 未授权录音可能违法 | 仅在授权用户声纹验证后启用 |
| 机器人伤人 | Cyber Bricks 动作幅度大 | 设置动作限位、接触停止 |
| 无线电频谱 | ESP32-Cam WiFi 需合规 | 使用已认证设备 |

> 本文档不构成法律建议。具体合规要求请咨询专业律师。

---

# 第十章：调研更新记录

> 按时间线记录历次调研的重要发现，供快速查阅。

## 调研记录：2026-03-22

> 调研工具：zhiku(DeepSeek) + web_fetch(AMD 官方博客) + vLLM/SGLang 官方文档

### 新增内容

| 主题 | 关键发现 |
|------|---------|
| **ROCm 7.x** | gfx1151 (RDNA 3.5) 必须用 ROCm 7.0+，6.x 不支持 |
| **vLLM ROCm** | v0.14.0 官方 Docker，一键安装，CI 通过率 93% |
| **SGLang ROCm** | AMD MI300X/MI355X 原生，FP8/AWQ 支持，适合复杂 Agent |
| **RTX 2060 量化** | Q4_K_M 是最佳平衡点，TensorRT-LLM 不推荐 |
| **NemoClaw** | NVIDIA GTC 2026 发布，企业级安全沙箱 |
| **A18 Pro** | NPU 量化分数 44,672，比 A17 Pro 高 33% |
| **FastVLM** | 比 LLaVA-OneVision 快 85 倍 TTFT，0.5B 可本地运行 |
| **Genesis** | 2026-03-21 仍有更新，GTX 1080 6GB 即可跑 |
| **Genesis vs Newton** | Newton（Disney+DeepMind+NVIDIA三巨头，Linux Foundation）需关注但为时尚早 |
| **Jetson Thor Nano** | 仍然不存在，继续每月一次监控 |
| **星闪设备** | BearPi-Pico H3863（海思Hi3863V100，40针GPIO）/ RK3506星闪板（59元核心板）；和ESP32对比：时延<20μs vs >10ms，并发4096 vs 7-20；但缺少"40针GPIO+星闪原生"标准品，需RISC-V开发板+星闪Dongle组合方案 |

---

## 调研记录：2026-03-21 深夜

> 调研工具：deepseek_deepseek_chat + 4x sessions_spawn 子Agent + web_fetch

### 新增内容

| 主题 | 关键发现 |
|------|---------|
| **Genesis 物理引擎** | GTX 1080 6GB 起，RTX 2060 可用，比 Isaac Sim 快 10-80 倍 |
| **YOLO Nano 2GB** | DeepStream-Yolo 最新支持 YOLOv13/YOLOv12/YOLO11/26，支持 FP16 |
| **MediaPipe on Nano** | GPU 加速不成熟，不推荐，替代方案 TensorRT |
| **iPhone 感知** | Apple Vision / Core ML + YOLO / MediaPipe / FastVLM 完整方案 |
| **语音升级** | VITS / CosyVoice2 / GPT-SoVITS v4 推荐，WebRTC AEC + RNNoise 降噪链路 |
| **OpenClaw 限制** | 无专用机器人节点类型，GPIO/串口/电机控制无内置支持 |
| **ESP32-Cam 固件** | Arduino ESP32 v3.0.7 + CameraWebServer 推荐 |

---

**0-1** —— 不是一台机器，是你人生的另一面。

*文档版本：v3.0（重组版）| 更新：2026-03-22*
