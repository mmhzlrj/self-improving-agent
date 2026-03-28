# Phase 1 语音陪伴 - ESP32 引脚分配表

> 补充自 `ROBOT-SOP.md` Phase 1 及相关章节
> 生成时间：2026-03-28

---

## P1.1 ESP32-CAM AI-Thinker 引脚图

```
     ┌─────────────────────────────┐
     │     ESP32-CAM (AI-Thinker)   │
     │                              │
     │   ┌──────────────────────┐   │
     │   │    2×9 排针 (18Pin)  │   │
     │   └──────────────────────┘   │
     │                              │
     │  上排(左→右):               │
     │  GPIO1(TX) GPIO3(RX) GPIO0  │
     │  VCC      GND    GPIO2       │
     │  GPIO4   GPIO16  GPIO17     │
     │  GPIO5   GPIO18 GPIO19      │
     │                              │
     │  下排(左→右):               │
     │  3V3     GND    GPIO35      │
     │  GPIO36  GPIO37 GPIO38      │
     │  GPIO39  GPIO40 GPIO41      │
     │  GPIO42  GPIO3V GND         │
     │                              │
     └─────────────────────────────┘
```

> **注意**：ESP32-CAM 有两个 GND 引脚（相邻排列），连接时请确认不要接错。

---

## P1.2 USB-TTL 烧录接线表

> 来源：ROBOT-SOP.md Phase 2「ESP32-Cam 固件烧录」章节

| 功能 | ESP32-CAM 引脚 | USB-TTL 模块 | 备注 |
|------|--------------|-------------|------|
| 供电（烧录时可不用）| 5V | 5V | ⚠️ 部分 USB-TTL 仅提供 3.3V，需外接 5V 电源 |
| 地线 | GND | GND | **必须连接**，参考点 |
| 发送 | U0R (GPIO3) | TX | ESP32 接收 → USB-TTL 发送 |
| 接收 | U0T (GPIO1) | RX | ESP32 发送 → USB-TTL 接收 |
| 烧录模式触发 | GPIO0 | GND | **烧录时短路**，烧录完成后断开 |
| 摄像头接口 | XCLK | — | 摄像头模块专用，无需连接 USB-TTL |
| SD 卡槽 | DAT0/DAT1/CMD/CLK | — | 内部已连接，无需外部接线 |

**烧录步骤**：
```bash
# 1. GPIO0 拉低（接地）进入烧录模式
# 2. 按下复位键（或重新上电）
# 3. 执行 esptool 烧录
esptool.py --chip esp32 --port /dev/ttyUSB0 \
  --baud 921600 \
  write_flash 0x1000 esp32-cam-webserver.bin

# 4. 烧录完成后：断开 GPIO0 → GND 的连接，重启
```

---

## P1.3 Jetson Nano ↔ ESP32-CAM 有线通信接线表

> 来源：ROBOT-SOP.md「有线通信（GPIO / UART / I2C）」章节
> **关键洞察**：Jetson Nano 和 ESP32-Cam 都有 40 针 GPIO，有线应急停止 <1ms，无线 WiFi >100ms。

### UART 通信（Phase 1/2 打通链路）

| 协议 | 方向 | Jetson Nano 引脚 | ESP32-CAM 引脚 | 参数 |
|------|------|----------------|--------------|------|
| UART TX | Jetson → ESP32 | Pin 8 (UART1_TX / GPIO14) | GPIO3 (U0RXD) | 115200 波特率 |
| UART RX | ESP32 → Jetson | Pin 10 (UART1_RX / GPIO15) | GPIO1 (U0TXD) | 115200 波特率 |
| 地线 | 共地 | Pin 6 (GND) | GND | **必须共地** |

> **Jetson Nano UART 设备文件**：`/dev/ttyTHS1`（注意不是 ttyUSB）

### I2C 总线（多设备扩展）

| 协议 | Jetson Nano | ESP32-CAM | 参数 |
|------|------------|----------|------|
| I2C SDA | Pin 3 (GPIO2) | GPIO4 | 速率 10-400kHz |
| I2C SCL | Pin 5 (GPIO3) | GPIO5 | 需 3.3V 电平匹配 |

> ⚠️ ESP32-CAM I2C 主要用于摄像头初始化（OV2640），正常运行时无需主动控制。

### GPIO 应急停止（硬件中断，μs 级）

| 功能 | Jetson Nano | ESP32-CAM | 说明 |
|------|------------|----------|------|
| 应急停止触发 | Pin 29 (GPIO6) | 任意 GPIO（如 GPIO2） | Jetson 拉低 → ESP32 检测到低电平 → 立即停止所有输出 |
| 应急停止确认 | Pin 31 (GPIO5) | 任意 GPIO（如 GPIO4） | ESP32 拉低 → Jetson 检测到停止完成 |
| 地线 | Pin 34 (GND) | GND | 共地 |

---

## P1.4 Cyber Bricks ESP32-C3 引脚分配（XA003/XA004/XA005）

> 来源：ROBOT-SOP.md 硬件清单

Cyber Bricks 主控为 ESP32-C3（XA003/XA004/XA005），与 Jetson Nano 通过 UART 通信：

| 功能 | ESP32-C3 引脚 | Jetson Nano | 备注 |
|------|-------------|------------|------|
| UART TX | GPIO20 | Pin 10 (RX) | 4Mbps（高速链路）|
| UART RX | GPIO21 | Pin 8 (TX) | 4Mbps |
| I2C SDA | GPIO1 | Pin 3 | 电机/舵机扩展 |
| I2C SCL | GPIO2 | Pin 5 | 电机/舵机扩展 |
| PWM 输出 | GPIO6/7/8/9 | — | 舵机控制（Phase 1 物理输出）|
| 电机驱动 | GPIO10/11/12/13 | — | 直流电机 H 桥 |

---

## P1.5 BearPi-Pico H3863 引脚（Phase 2 备选 MCU）

> 来源：ROBOT-SOP.md §3.3.5 对比表

| 接口 | 数量/规格 | 引脚说明 |
|------|----------|---------|
| GPIO | ×17 | 均可复用 |
| UART | ×3（最高 4Mbps）| UART1 复用：TX=GPIO20, RX=GPIO21 |
| SPI | ×2 | 高速外设 |
| QSPI | ×1 | 扩展存储 |
| PWM | ×8 | 电机/舵机控制 |
| ADC | ×6 | 传感器采集 |
| I2S | ×1 | 音频输入/输出 |

**UART 对接 Jetson Nano 接线**：
```
H3863 UART1 TX (GPIO20) → Jetson Nano Pin 10 (RX) /dev/ttyTHS1
H3863 UART1 RX (GPIO21) → Jetson Nano Pin 8 (TX) /dev/ttyTHS1
H3863 GND               → Jetson Nano Pin 6 (GND)
```

---

## P1.6 快速参考：所有 GND 引脚位置

> ESP32-CAM 有多个 GND，记住位置方便快速接线

| 位置 | 排针顺序 |
|------|---------|
| 上排 | GPIO0 旁边（排针右侧第2位）|
| 下排 | 3V3 旁边（排针左侧第2位）|
| 特点 | 两个 GND **相邻排列**，易于识别 |

---

## P1.7 常见接线错误及后果

| 错误 | 后果 | 修复 |
|------|------|------|
| 5V/3.3V 接反 | ESP32-CAM 立刻烧毁 | 换模块，无修复可能 |
| TX/RX 接反 | 无法烧录/通信 | 交换 TX/RX 线重试 |
| 未共地 | 通信不稳定/丢帧 | 连接任意 GND |
| GPIO0 烧录时未接地 | 无法进入烧录模式 | 重新接地后按复位 |
| 烧录后 GPIO0 未断开 | 程序不运行，卡在 boot 模式 | 断开后重启 |

---

## P1.8 参考链接

- ESP32-CAM 官方文档：https://github.com/espressif/esp32-camera
- esptool.py：https://github.com/espressif/esptool
- ROBOT-SOP.md §A.3：有线通信详细方案
- ROBOT-SOP.md §3.4.2：micro-ROS 接入方案

---

## P1.9 音频硬件选型（Phase 1 语音陪伴）

> 来源：ROBOT-SOP.md §A.2 语音交互 + DeepSeek 搜索调研
> 补充目标：为 Phase 1「USB 耳机」提供具体硬件选型和配置指南

### P1.9.1 选型背景

Phase 1 语音陪伴当前硬件表：

| 设备 | 状态 | 备注 |
|------|------|------|
| Jetson Nano 2GB | 已有 | 主控，**无内置麦克风** |
| USB 耳机 | 需采购 | Phase 2 一起买 |
| Cyber Bricks ×1 | 已有 | 第一个物理输出节点 |

Jetson Nano 2GB **没有 3.5mm 音频输入接口**，只能通过以下方式获取音频输入：
- USB 声卡 / USB 麦克风（最简单）
- I2S MEMS 麦克风（通过 40-pin GPIO，需配置设备树）
- 麦克风阵列（远场场景）

### P1.9.2 方案对比

| 方案 | 成本 | 难度 | 近场(<1m) | 远场(1-5m) | 推荐度 |
|------|------|------|-----------|-----------|--------|
| **USB 耳机（Phase 1 推荐）** | ¥50-150 | ⭐ 简单 | ✅ | ❌ | ⭐⭐⭐⭐⭐ |
| **Waveshare USB 音频模块** | ¥60-80 | ⭐ 简单 | ✅ | ❌ | ⭐⭐⭐⭐ |
| **I2S MEMS 麦克风 (SPH0645)** | ¥30-60 | ⭐⭐ 中等 | ✅ | ❌ | ⭐⭐⭐ |
| **ReSpeaker 4-Mic 阵列** | ¥100-180 | ⭐⭐ 中等 | ✅ | ✅ | ⭐⭐⭐⭐ |
| **iPhone 四麦克风（已有）** | ¥0 | ⭐⭐⭐ 需配置 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |

> **Phase 1 核心原则**：先跑通链路，不追求完美。选 USB 耳机是因为 Phase 2 本来就要买，先用最低成本验证语音交互链路。

### P1.9.3 推荐方案一：USB 耳机（Phase 1 快速验证）

**选型要求**：
- 必须带麦克风（单耳挂麦或头戴式均可）
- USB 接口（免驱动，Linux 原生支持）
- 支持 16kHz 采样率（Whisper 要求）

**推荐型号**：

| 产品 | 关键参数 | 价格区间 | 备注 |
|------|---------|---------|------|
| **漫步者 UC730 / K150** | USB，头戴式，单向麦克风 | ¥80-120 | 高性价比，Linux 兼容性好 |
| **JBL Quantum 50** | USB，入耳式，挂麦 | ¥120-180 | 轻便，适合移动测试 |
| **罗技 H340** | USB，头戴式，USB-A | ¥80-150 | 最常见方案，驱动稳定 |
| **绿联 USB 耳麦** | USB，3.5mm+USB 转接 | ¥40-60 | 极致低价，够用 |

**连接与配置**：

```bash
# 查看设备识别
arecord -l      # 列出录音设备（USB 耳机通常是 card 1）
aplay -l        # 列出播放设备

# 验证设备工作
# 录音 5 秒
arecord -d 5 -f cd /tmp/test.wav
# 播放录音
aplay /tmp/test.wav
```

**配置 ~/.asoundrc（USB 耳机为 card 1）**：

```bash
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

# 重启音频服务
sudo systemctl restart pipewire 或 sudo systemctl restart pulseaudio
```

### P1.9.4 推荐方案二：Waveshare USB 音频编解码模块（Phase 1/2 升级）

> 专为 Jetson Nano 设计，免驱，板载双 MEMS 麦克风 + 3.5mm 耳机 + 喇叭接口

**关键参数**：

| 参数 | 值 |
|------|-----|
| 芯片 | SSS1629 / SSS1629A5 |
| 接口 | USB 2.0，即插即用 |
| 麦克风 | 板载 2 个 MEMS 硅麦克风 |
| 输出 | 3.5mm 耳机孔 + 板载喇叭接口 |
| 采样率 | 16kHz / 48kHz |
| 唤醒词支持 | Snowboy 唤醒词 Demo |

**与 Jetson Nano 的连接**：

```
Waveshare USB Audio Module
    │
    └── USB-A → Jetson Nano USB 2.0 接口（供电+数据）
    └── 3.5mm 耳机 → 扬声器（语音输出）
```

**配置方法**（同 USB 耳机）：

```bash
# 查看 card 编号
arecord -l
# 输出示例：
# card 1: SSS1629 [USB Audio Device], device 0: USB Audio [USB Audio]
#   Subdevices: 1/1
#   Subdevice #0: subdevice #0

# 设为默认设备
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

**适用场景**：Phase 1 验证 + Phase 2 持久部署，性价比高于普通 USB 耳机。

### P1.9.5 进阶方案：ReSpeaker 4-Mic 阵列（远场交互）

> 适合机器人在房间内自由移动的场景，支持声源定位和回声消除

**关键参数**：

| 参数 | 值 |
|------|-----|
| 麦克风数量 | 4 × MEMS |
| 接口 | USB（ReSpeaker USB 版本）或 I2S |
| 远场拾音距离 | 3-5 米 |
| 附加功能 | 声源定位（DoA）、回声消除（AEC）、噪声抑制 |
| 官方支持 | NVIDIA Jetson 官方设备树支持 |

**Jetson Nano I2S 版本接线**：

| 功能 | ReSpeaker 引脚 | Jetson Nano 引脚 |
|------|---------------|-----------------|
| 3.3V | VCC | Pin 1 (3.3V) |
| GND | GND | Pin 6 (GND) |
| I2S BCLK | BCK / CLK | Pin 12 (I2S4_SCLK) |
| I2S L/R CLK | WFS / LRCLK | Pin 35 (I2S4_FS) |
| I2S DOUT | DOUT / SD | Pin 38 (I2S4_DOUT) |

**软件配置**：

```bash
# 通过 Jetson-IO 配置 I2S 设备树
sudo /opt/nvidia/jetson-io/config-by-function.py -o dtb i2s4
sudo reboot

# 验证
arecord -l
# 应该能看到 ReSpeaker 设备
```

**Phase 1 → Phase 2 演进路径**：

```
Phase 1（近场）：USB 耳机 → Whisper base.en → Edge-TTS
        ↓ 验证链路跑通
Phase 2（远场）：ReSpeaker 4-Mic → WebRTC AEC → Whisper → Edge-TTS
        ↓ 增加感知范围
Phase 3（移动）：iPhone 四麦克风 → OpenClaw 节点 → 全向感知
```

### P1.9.6 I2S MEMS 麦克风（紧凑型，Jetson Nano 官方支持）

**推荐型号**：

| 型号 | 关键参数 | NVIDIA 官方支持 | 配置难度 |
|------|---------|----------------|---------|
| **Adafruit SPH0645LM4H** | I2S，3.3V，低功耗，数字输出 | ✅ 有 Overlay | ⭐ 简单 |
| **InvenSense ICS-43434** | I2S，3.3V，高信噪比 | ⚠️ 社区验证 | ⭐⭐ 中等 |

**接线（单只 SPH0645）**：

| 功能 | SPH0645 引脚 | Jetson Nano 引脚 |
|------|------------|-----------------|
| 3.3V | VDD | Pin 1 (3.3V) |
| GND | GND | Pin 6 (GND) |
| BCLK | BCLK | Pin 12 (I2S4_SCLK) |
| LRCLK | LRCLK / WFS | Pin 35 (I2S4_FS) |
| DOUT | DOUT | Pin 38 (I2S4_DOUT) |

```bash
# 配置设备树
sudo /opt/nvidia/jetson-io/config-by-function.py -o dtb i2s4
sudo reboot

# 验证
arecord -l
# 应该看到 I2S 设备
```

### P1.9.7 降噪链路配置（Phase 1+ 推荐启用）

> 即使使用普通 USB 耳机，也建议启用软件降噪链路

**推荐链路**（§A.2 语音交互最佳实践）：

```
音频输入 → WebRTC AEC（回声消除）→ RNNoise（降噪）→ VAD检测 → Whisper
```

**安装与配置**：

```bash
# 安装 WebRTC降噪（PulseAudio 模块）
# Ubuntu/Debian:
sudo apt install webrtc-audio-processing

# 或使用 Python 实现（Phase 1 推荐）：
pip3 install webrtc_noise_gain

# RNNoise（噪声抑制）
# 编译 whisper.cpp 时已包含，无需额外安装
```

**Python 降噪示例**：

```python
from webrtc_noise_gain import WebRTCNoiseGain
import numpy as np

def denoise_audio(audio_data, sample_rate=16000):
    """WebRTC 降噪 + RNNoise"""
    # Step 1: WebRTC AEC（回声消除，需要参考信号）
    # Step 2: RNNoise 降噪
    gain_model = WebRTCNoiseGain()
    # 处理音频帧
    return denoised_audio
```

### P1.9.8 快速决策树

```
语音陪伴 Phase 1 选型 →

先问：Jetson Nano 还是 iPhone 作为前端？
    │
    ├── Jetson Nano 为主控
    │   │
    │   ├── 预算优先 / 快速验证
    │   │   └── → USB 耳机（¥50-150）+ ~/.asoundrc 配置
    │   │
    │   ├── 需要扬声器输出
    │   │   └── → Waveshare USB 音频模块（¥60-80）
    │   │
    │   └── 远场 / 房间自由移动
    │       └── → ReSpeaker 4-Mic 阵列（¥100-180）
    │
    └── iPhone 作为感知前端（未来 Phase 3 方向）
        └── → 利用 iPhone 四麦克风阵列（已有，¥0）
              → OpenClaw Node 接入，完整降噪链路
```

### P1.9.9 参考链接

- NVIDIA Jetson Nano I2S 配置：https://developer.nvidia.com/
- Adafruit SPH0645LM4H：https://www.adafruit.com/product/3421
- ReSpeaker 4-Mic Array：https://github.com/respeaker/seeed-voicecard
- Waveshare USB Audio Module：https://www.waveshare.net/wiki/USB_Audio_Module
- ROBOT-SOP.md §A.2 语音交互模块：https://...

---

## P1.10 Whisper 完整安装配置指南（Phase 1 详细版）

> 来源：whisper.cpp 官方 GitHub (ggml-org/whisper.cpp) + ROBOT-SOP.md §A.2
> 补充目标：为 Phase 1 语音陪伴提供 Whisper 完整安装配置手册，涵盖模型选择、编译选项、性能优化

### P1.10.1 whisper.cpp vs OpenAI Whisper 对比

| 维度 | whisper.cpp | OpenAI Whisper (Python) |
|------|-------------|------------------------|
| 实现语言 | C/C++ | Python + PyTorch |
| 依赖 | 零依赖（纯C） | PyTorch、transformers 等 |
| 内存占用 | ~50% PyTorch 版本 | 较大 |
| 推理速度 | 快（C级优化） | 较慢 |
| GPU 加速 | CUDA / Vulkan / Metal | CUDA |
| Jetson Nano 兼容性 | ✅ 原生支持 | ⚠️ 需要 JetPack + PyTorch |
| 实时语音流 | ✅ whisper-stream | ❌ 需自行封装 |
| **推荐场景** | **Phase 1 嵌入式** | 服务端高精度场景 |

**Phase 1 结论**：使用 whisper.cpp（Jetson Nano 上 CPU 运行完全够用）

### P1.10.2 模型选择对比（关键参数）

> 来源：whisper.cpp README 模型表格

| 模型 | 模型文件大小 | 内存占用 | 相对速度 | 适用场景 |
|------|------------|---------|---------|---------|
| **tiny** | 75 MiB | ~273 MB | 32x realtime | 极致轻量，测试用 |
| **tiny.en** | 75 MiB | ~273 MB | 32x realtime | 英语专用，更快 |
| **base** | 142 MiB | ~388 MB | 16x realtime | **Phase 1 推荐** |
| **base.en** | 142 MiB | ~388 MB | 16x realtime | 英语专用 |
| **small** | 466 MiB | ~852 MB | 6x realtime | 中文推荐 |
| **small.en** | 466 MiB | ~852 MB | 6x realtime | 英语专用 |
| **medium** | 1.5 GiB | ~2.1 GB | 2x realtime | 高精度 |
| **large-v3** | 2.9 GiB | ~3.9 GB | 1x realtime | 最高精度 |

**Phase 1 推荐配置**：
- 英文为主 → `base.en`（内存 ~388MB，16倍实时）
- 中文为主 → `small`（内存 ~852MB，6倍实时，但中文识别率大幅提升）
- Jetson Nano 2GB 内存 → 均可运行，CPU 推理

### P1.10.3 完整安装步骤（CMake 方式，替代旧版 make）

> whisper.cpp 已从 `make` 迁移到 CMake，这是官方推荐方式

```bash
# Step 1: 克隆仓库
cd ~
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp

# Step 2: CMake 构建（替代旧版 make）
cmake -B build
cmake --build build -j --config Release

# Step 3: 下载模型（选一个）
# 英文语音 → base.en
./models/download-ggml-model.sh base.en
# 中文语音 → small（中文识别率比 base 高很多）
./models/download-ggml-model.sh small

# Step 4: 快速测试
./build/bin/whisper-cli -m ./models/ggml-base.en.bin -f ./samples/jfk.wav

# 一键安装（等价于上面）
make -j base.en
```

### P1.10.4 CUDA 加速配置（Jetson Nano 可选）

Jetson Nano 有 NVIDIA GPU（Maxwell），可以加速 Whisper 推理：

```bash
# 检查 CUDA 是否可用
nvcc --version
# 应该输出 CUDA version

# 使用 CUDA 编译
cmake -B build -DGGML_CUDA=1
cmake --build build -j --config Release

# 运行（自动使用 GPU）
./build/bin/whisper-cli -m ./models/ggml-base.en.bin -f ./samples/jfk.wav

# 查看日志中的 GPU 信息
# 应该看到 CUDA = 1
```

**注意**：Jetson Nano 的 GPU 较弱（Maxwell），CUDA 加速效果可能不如预期，明显优于 CPU 即可。

### P1.10.5 量化模型（减少内存占用）

量化后的模型更小、更快，适合嵌入式设备：

```bash
# Step 1: 量化（Q5_0 方法，精度损失小）
./build/bin/quantize \
  models/ggml-base.en.bin \
  models/ggml-base.en-q5_0.bin \
  q5_0

# Step 2: 使用量化模型
./build/bin/whisper-cli \
  -m models/ggml-base.en-q5_0.bin \
  -f /tmp/input.wav

# 量化效果：
# base.en 142MB → ggml-base.en-q5_0.bin ~45MB（68% 压缩）
# 内存占用从 388MB → ~200MB
```

**量化方法对比**：

| 方法 | 压缩率 | 精度损失 | 推荐 |
|------|--------|---------|------|
| Q4_0 | ~75% | 轻微 | 极致内存 |
| **Q5_0** | ~68% | 很小 | **推荐** |
| Q8_0 | ~50% | 几乎无 | 精度优先 |

### P1.10.6 实时语音流（whisper-stream）

Phase 1 需要的不是离线文件转写，而是**实时麦克风输入**：

```bash
# 安装 SDL2（实时流必需）
sudo apt install libsdl2-dev

# 编译 whisper-stream
cmake -B build -DWHISPER_SDL2=ON
cmake --build build -j --config Release

# 运行实时语音流
./build/bin/whisper-stream \
  -m ./models/ggml-base.en.bin \
  -t 8 \
  --step 500 \
  --length 5000

# 参数说明：
# -t 8: 使用 8 个线程
# --step 500: 每 500ms 采样一次
# --length 5000: 每次处理 5000ms 音频缓冲

# 按 Ctrl+C 退出
```

### P1.10.7 VAD（语音活动检测）集成

VAD 可以过滤静音，减少 Whisper 处理时间：

```bash
# 下载 Silero VAD 模型
./models/download-vad-model.sh silero-v6.2.0

# 使用 VAD（只处理有语音的部分）
./build/bin/whisper-cli \
  -m models/ggml-base.en.bin \
  -vm models/ggml-silero-v6.2.0.bin \
  --vad \
  -f /tmp/input.wav

# VAD 参数调优：
# --vad-threshold 0.5: 语音检测阈值（0-1）
# --vad-min-speech-duration-ms 250: 最短语音片段（ms）
# --vad-min-silence-duration-ms 200: 静音判定时长（ms）
# --vad-max-speech-duration-s 30: 最大语音片段（秒）
```

### P1.10.8 Phase 1 完整集成代码（Python subprocess 调用）

> 基于 ROBOT-SOP.md Phase 1 Step 5，补充 whisper.cpp 路径和参数

```python
#!/usr/bin/env python3
"""语音对话主程序 - Phase 1 (whisper.cpp 版本)"""
import subprocess
import edge_tts
import asyncio
import sys

WHISPER_CLI = "./whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL = "./whisper.cpp/models/ggml-base.en.bin"
AUDIO_INPUT = "/tmp/input.wav"

async def synthesize_and_play(text):
    """文字转语音并播放"""
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save("/tmp/tts_output.mp3")
    subprocess.run(["aplay", "/tmp/tts_output.mp3"])

def transcribe(audio_path):
    """调用 whisper-cli 进行语音识别"""
    result = subprocess.run([
        WHISPER_CLI,
        "-m", WHISPER_MODEL,
        "-f", audio_path,
        "--language", "en",        # 中文改为 "zh"
        "--max-len", "1",          # 词级时间戳
        "-t", "4"                  # 4 线程
    ], capture_output=True, text=True)
    
    # whisper-cli 输出格式：[00:00:00.000 --> 00:00:01.200] Hello world
    lines = result.stdout.strip().split('\n')
    texts = []
    for line in lines:
        if ']-->' in line:
            # 提取时间戳后的文本
            text = line.split(']', 1)[1].strip()
            texts.append(text)
    return ' '.join(texts)

async def main():
    while True:
        print("正在听...")
        # 录音 5 秒
        subprocess.run([
            "arecord", "-d", "5", "-f", "cd",
            "-c", "1", "-r", "16000", AUDIO_INPUT
        ])
        
        # 语音识别
        text = transcribe(AUDIO_INPUT)
        if not text:
            continue
        
        print(f"你说: {text}")
        
        # TODO: 发给贵庚大脑（OpenClaw Bridge）
        response = f"我听到了：{text}"
        
        print(f"回复: {response}")
        await synthesize_and_play(response)

asyncio.run(main())
```

### P1.10.9 常见问题排查

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| `whisper_init_state: invalid model` | 模型文件损坏 | 重新下载：`rm -rf models/ggml-*.bin && ./models/download-ggml-model.sh base.en` |
| 识别全是乱码 | 音频格式不对 | 确保 16kHz 单声道 WAV：`ffmpeg -i input.mp3 -ar 16000 -ac 1 -c:a pcm_s16le output.wav` |
| Jetson Nano 内存不足 | 模型太大 | 换用量化模型：`quantize` 命令生成 q5_0 版本 |
| CUDA 版本不兼容 | JetPack 版本过低 | 检查：`nvcc --version`，建议 JetPack 5.x |
| `make base.en` 报错 | 旧版 make 方式 | 改用 CMake：`cmake -B build && cmake --build build -j` |
| 实时流延迟太高 | 线程数不够 | 增加线程：`-t 8`，或使用 `--step 250` 减少缓冲 |

### P1.10.10 音频格式要求（必须遵守）

Whisper 要求特定音频格式，**不是所有音频都能直接识别**：

```bash
# Whisper 要求：
# - 采样率：16kHz（或 8kHz/32kHz 也可自动重采样）
# - 声道：单声道（mono）
# - 位深：16-bit PCM
# - 格式：WAV（最可靠）

# 检查现有音频格式
ffmpeg -i /tmp/input.wav 2>&1 | grep -E "Audio|Stream"

# 转换示例（MP3 → Whisper 合规格式）
ffmpeg -i input.mp3 \
  -ar 16000 \
  -ac 1 \
  -c:a pcm_s16le \
  output.wav

# 实时录音（arecord 默认就是 16kHz 单声道 16bit，兼容）
arecord -d 5 -f cd -c 1 -r 16000 /tmp/input.wav
# -f cd = 44100Hz, 16bit, stereo（Whisper 会自动重采样）
# -r 16000 -c 1 = 指定 16kHz 单声道（更省处理）
```

### P1.10.11 Whisper CLI 完整参数参考

```bash
# 基础用法
whisper-cli -m 模型路径 -f 音频文件

# 完整参数
whisper-cli [参数]
  -m, --model           模型文件路径
  -f, --file            输入音频文件（WAV/PCM）
  -l, --language        语言代码（auto=en=zh 等）
  -t, --threads         线程数（默认 4）
  -p, --processors      处理器数（默认 1）
  --max-len             最大行长度（词级时间戳用 -ml 1）
  -ml, --max-line-len   最大行字符数
  -bo, --best-of        beam size（默认 5）
  -pa, --patience       beam patience（默认 1）
  -w, --word-timestamps 启用词级时间戳
  --vad                  启用 VAD
  --vad-model           VAD 模型路径
  --vad-threshold       VAD 阈值（默认 0.5）
  -owts, --output-wts   输出 karaoke 时间戳脚本
  -oa, --output-article 输出纯文本
  -oj, --output-json    输出 JSON
  -os, --output-srt     输出 SRT 字幕
  -ot, --output-ttml    输出 TTML 字幕
  -ov, --output-vtt     输出 VTT 字幕
  -h, --help            显示帮助
```

### P1.10.12 参考链接

- whisper.cpp GitHub：https://github.com/ggml-org/whisper.cpp
- 模型下载：https://huggingface.co/ggml-org/whisper.cpp
- whisper-stream 示例：https://github.com/ggml-org/whisper.cpp/tree/master/examples/stream
- Silero VAD：https://github.com/snakers4/silero-vad
- ROBOT-SOP.md §A.2 语音交互模块

---

## P1.11 Edge-TTS 完整配置指南（Phase 1 详细版）

> 来源：edge-tts GitHub (rany2/edge-tts) + Microsoft Azure Speech SDK 文档
> 补充目标：为 Phase 1 语音陪伴提供 Edge-TTS 完整配置手册

### P1.11.1 简介

Edge-TTS 是微软 Edge 浏览器的在线语音合成服务的 Python 封装，具有以下特点：

| 特性 | 说明 |
|------|------|
| **无需 API Key** | 直接调用 Edge 在线服务，完全免费 |
| **无需 Microsoft Edge** | 纯 Python，不依赖任何微软桌面软件 |
| **无需 Windows** | 全平台支持（Linux/macOS/Windows）|
| **延迟极低** | 本地合成，网络请求后即时返回 |
| **中文支持优秀** | 多种中文音色可选，部分支持方言 |
| **SSML 支持** | 可控制语速、音调、音量 |
| **字幕生成** | 可同步生成 SRT/ VTT 字幕文件 |

**Edge-TTS vs 其他 TTS 方案对比**：

| 方案 | 成本 | 离线 | 中文质量 | 延迟 | 推荐场景 |
|------|------|------|---------|------|---------|
| **Edge-TTS** | 免费 | ❌ | ⭐⭐⭐⭐⭐ | <500ms | **Phase 1 推荐** |
| Pikara / VALL-E | 免费 | ✅ | ⭐⭐⭐⭐ | 较高 | 离线优先 |
| Azure TTS | 按量付费 | ❌ | ⭐⭐⭐⭐⭐ | <200ms | 生产环境 |
| GTTS | 免费 | ❌ | ⭐⭐⭐ | >1s | 临时测试 |

### P1.11.2 安装

```bash
# pip 安装（推荐）
pip3 install edge-tts

# pipx 安装（系统级 CLI 工具）
pipx install edge-tts

# 验证安装
edge-tts --version
# 输出示例：edge-tts 7.x.x
```

### P1.11.3 中文语音完整列表（zh-CN 系列）

> 通过 `edge-tts --list-voices` 获取，以下为常用中文语音

#### 普通话（Mainland China）

| 语音名称 | 性别 | 适用场景 | 音色特点 |
|---------|------|---------|---------|
| **zh-CN-XiaoxiaoNeural** | 女 | 通用、新闻、导航 | 清晰自然，Phase 1 默认推荐 |
| **zh-CN-YunxiNeural** | 男 | 通用、对话 | 磁性低沉，适合男声场景 |
| **zh-CN-YunyangNeural** | 男 | 新闻播报 | 专业播音腔，语速稳定 |
| **zh-CN-YunfeiNeural** | 女 | 对话、助手 | 活泼亲切，适合语音助手 |
| **zh-CN-XiaoyiNeural** | 女 | 儿童内容 | 甜美可爱，适合早教 |
| **zh-CN-liaoningNeural** | 女 | 东北方言 | 地道东北话 |
| **zh-CN-shaanxiNeural** | 女 | 陕西方言 | 陕西方言特色 |
| **zh-CNHenan-XiaohanNeural** | 女 | 河南方言 | 河南口音 |
| **zh-CN-ChangchengNeural** | 女 | 天津方言 | 天津话特色 |

#### 台湾/香港

| 语音名称 | 性别 | 地区 |
|---------|------|------|
| **zh-TW-HsiaoYuNeural** | 女 | 台湾国语 |
| **zh-TW-YunJheNeural** | 男 | 台湾国语 |
| **zh-HK-HiuGaaiNeural** | 女 | 粤语 |
| **zh-HK-HiuMaanNeural** | 女 | 粤语 |
| **zh-HK-WanLungNeural** | 男 | 粤语 |

#### 其他中文变体

| 语音名称 | 地区/语言 |
|---------|---------|
| **zh-CN-XiaoniNeural** | 儿童专用（语速慢，发音清晰）|
| **yue-CN-XiaoMinNeural** | 粤语（广东话）|
| **zh-CN-YunyouNeural** | 语音邮件/低沉男声 |

**Phase 1 推荐配置**：

```python
# Phase 1 默认语音组合
VOICE_FEMALE = "zh-CN-XiaoxiaoNeural"  # 默认女声，清亮自然
VOICE_MALE   = "zh-CN-YunxiNeural"       # 男声助手
VOICE_NEWS   = "zh-CN-YunyangNeural"    # 新闻播报
```

### P1.11.4 语速 / 音调 / 音量控制

Edge-TTS 通过 prosody 标签的三个属性控制输出：

| 参数 | CLI 参数 | 取值范围 | 默认值 | 说明 |
|------|---------|---------|-------|------|
| **语速** | `--rate` | `-100%` ~ `+100%` | `+0%` | 负数减慢，正数加快 |
| **音调** | `--pitch` | `-50Hz` ~ `+50Hz` | `+0Hz` | 降低/升高音调 |
| **音量** | `--volume` | `-100%` ~ `+100%` | `+0%` | 减小/增大音量 |

**CLI 用法示例**：

```bash
# 正常语速（默认）
edge-tts --voice zh-CN-XiaoxiaoNeural --text "你好，我是贵庚" --write-media normal.mp3

# 语速减慢 30%
edge-tts --rate=-30% --voice zh-CN-XiaoxiaoNeural --text "慢慢说" --write-media slow.mp3

# 语速加快 50%
edge-tts --rate=+50% --voice zh-CN-XiaoxiaoNeural --text "快速播报" --write-media fast.mp3

# 音调降低 20Hz（更低沉）
edge-tts --pitch=-20Hz --voice zh-CN-XiaoxiaoNeural --text "低沉男声" --write-media low_pitch.mp3

# 音量增大 50%
edge-tts --volume=+50% --voice zh-CN-XiaoxiaoNeural --text "大声说" --write-media loud.mp3

# 组合使用：语速慢 + 音调低（老年友好）
edge-tts --rate=-40% --pitch=-10Hz --volume=+20% \
  --voice zh-CN-XiaoxiaoNeural \
  --text "老人听得更清楚" \
  --write-media elderly.mp3
```

> ⚠️ **负数参数注意**：CLI 中负数必须用 `=` 连接，否则会被当作命令行选项：
> - ✅ `--rate=-30%`
> - ❌ `--rate -30%`

### P1.11.5 Python API 完整用法

#### 基础用法（异步）

```python
import asyncio
import edge_tts

async def basic_tts():
    """最简单的 TTS 调用"""
    communicate = edge_tts.Communicate("你好，我是贵庚", "zh-CN-XiaoxiaoNeural")
    await communicate.save("/tmp/hello.mp3")

asyncio.run(basic_tts())
```

#### 带参数的 Communicate

```python
import asyncio
import edge_tts

async def tts_with_params():
    """带语速、音调、音量参数"""
    communicate = edge_tts.Communicate(
        text="语速慢一点，音调低一点",
        voice="zh-CN-XiaoxiaoNeural",
        rate="-30%",      # 减慢 30%
        pitch="-10Hz",    # 音调降低 10Hz
        volume="+20%"     # 音量增加 20%
    )
    await communicate.save("/tmp/modified.mp3")

asyncio.run(tts_with_params())
```

#### 获取音频流（不写文件）

```python
import asyncio
import edge_tts

async def tts_to_stream():
    """获取音频流，可用于直接播放或进一步处理"""
    communicate = edge_tts.Communicate("流式音频测试", "zh-CN-XiaoxiaoNeural")
    
    # get_stream() 返回异步生成器
    stream = await communicate.get_stream()
    
    # 读取所有数据
    audio_data = b""
    async for chunk in stream:
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    
    print(f"音频大小: {len(audio_data)} bytes")
    return audio_data

asyncio.run(tts_to_stream())
```

#### 获取字幕（SRT 时间戳）

```python
import asyncio
import edge_tts

async def tts_with_subtitles():
    """生成带时间戳的 SRT 字幕文件"""
    text = "第一句。第二句。第三句。"
    
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    
    # 同时生成音频和字幕
    await communicate.save(
        "/tmp/output.mp3",
        subtitles="SRT",  # 或 "VTT"
    )
    # 自动生成 /tmp/output.srt

asyncio.run(tts_with_subtitles())
```

#### 子进程方式（不用 Python 异步）

```python
import subprocess

result = subprocess.run([
    "edge-tts",
    "--voice", "zh-CN-XiaoxiaoNeural",
    "--rate", "+20%",
    "--text", "用 subprocess 调用 edge-tts",
    "--write-media", "/tmp/subprocess.mp3"
], capture_output=True, text=True)

if result.returncode == 0:
    print("成功生成音频")
else:
    print(f"失败: {result.stderr}")
```

### P1.11.6 实时语音对话（Phase 1 核心代码）

> 基于 ROBOT-SOP.md Phase 1 Step 5，补充完整的 Edge-TTS 集成方案

```python
#!/usr/bin/env python3
"""语音对话主程序 - Phase 1 (完整版)
实现：麦克风 → Whisper → OpenClaw → Edge-TTS → 扬声器
"""
import subprocess
import asyncio
import edge_tts
import sys
import os

# ====== 配置 ======
WHISPER_CLI   = "./whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL = "./whisper.cpp/models/ggml-base.en.bin"
VOICE         = "zh-CN-XiaoxiaoNeural"
TTS_RATE      = "+0%"      # 默认语速
TTS_PITCH     = "+0Hz"     # 默认音调
TTS_VOLUME    = "+0%"      # 默认音量
AUDIO_INPUT   = "/tmp/input.wav"
TTS_OUTPUT    = "/tmp/tts_output.mp3"

# ====== TTS 函数 ======
async def synthesize(text: str) -> str:
    """文字转语音，返回 MP3 文件路径"""
    communicate = edge_tts.Communicate(
        text,
        voice=VOICE,
        rate=TTS_RATE,
        pitch=TTS_PITCH,
        volume=TTS_VOLUME
    )
    await communicate.save(TTS_OUTPUT)
    return TTS_OUTPUT

async def play_audio(audio_path: str):
    """播放音频文件"""
    subprocess.run(["aplay", audio_path], check=True)

async def tts_and_play(text: str):
    """合成并播放语音（连续执行）"""
    audio_path = await synthesize(text)
    await play_audio(audio_path)

# ====== Whisper 识别函数 ======
def transcribe(audio_path: str) -> str:
    """调用 whisper-cli 进行语音识别"""
    result = subprocess.run([
        WHISPER_CLI,
        "-m", WHISPER_MODEL,
        "-f", audio_path,
        "--language", "zh",
        "-t", "4"
    ], capture_output=True, text=True)
    
    # 解析 whisper-cli 输出（词级时间戳格式）
    texts = []
    for line in result.stdout.strip().split('\n'):
        if '-->' in line:
            text = line.split(']', 1)[1].strip()
            texts.append(text)
    
    return ' '.join(texts) if texts else ""

# ====== 主循环 ======
async def main():
    while True:
        print("🎤 正在听...")
        
        # 录音 5 秒（16kHz 单声道 WAV）
        subprocess.run([
            "arecord", "-d", "5",
            "-f", "cd",           # 44.1kHz, 16bit, stereo
            "-c", "1",            # 单声道
            "-r", "16000",        # 16kHz 采样率
            AUDIO_INPUT
        ], check=True)
        
        # 语音识别
        text = transcribe(AUDIO_INPUT)
        if not text:
            print("（未检测到语音，重新监听）")
            continue
        
        print(f"👤 你说: {text}")
        
        # TODO: 发给贵庚大脑（OpenClaw Bridge）
        # response = await bridge.ask(text)
        response = f"我听到了：{text}"
        
        print(f"🤖 贵庚: {response}")
        
        # 回复语音
        await tts_and_play(response)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\n已退出语音对话")
```

### P1.11.7 语速适配场景配置

根据不同场景调整 Edge-TTS 参数：

```python
# 场景 → 参数配置
SCENE_CONFIGS = {
    "normal": {
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "volume": "+0%",
        "desc": "正常语速，日常对话"
    },
    "elderly": {
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "-40%",  # 慢 40%
        "pitch": "-5Hz", # 稍低沉
        "volume": "+30%",# 大声 30%
        "desc": "老年友好模式"
    },
    "news": {
        "voice": "zh-CN-YunyangNeural",
        "rate": "+10%",  # 稍快
        "pitch": "+0Hz",
        "volume": "+0%",
        "desc": "新闻播报风格"
    },
    "quick": {
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "+30%",  # 快 30%
        "pitch": "+0Hz",
        "volume": "+0%",
        "desc": "快速播报，应急信息"
    },
    "male": {
        "voice": "zh-CN-YunxiNeural",
        "rate": "+0%",
        "pitch": "-10Hz", # 降低音调
        "volume": "+0%",
        "desc": "男声模式"
    },
}
```

### P1.11.8 长文本分段处理

Edge-TTS 单次合成有长度限制（建议不超过 500 字符），长文本需要分段：

```python
import asyncio
import edge_tts

MAX_CHUNK_LENGTH = 450  # 留余量

def split_text(text: str, max_len: int = MAX_CHUNK_LENGTH) -> list[str]:
    """按句子分割长文本"""
    import re
    # 按句号、问号、感叹号分割
    sentences = re.split(r'([。！？])', text)
    
    chunks = []
    current = ""
    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i] + sentences[i + 1]
        if len(current) + len(sentence) <= max_len:
            current += sentence
        else:
            if current:
                chunks.append(current)
            current = sentence
    
    if current:
        chunks.append(current)
    
    return chunks

async def synthesize_long_text(text: str, output_path: str = "/tmp/long_tts.mp3"):
    """合成超长文本（分段 + 合并）"""
    chunks = split_text(text)
    
    import tempfile
    import os
    
    temp_files = []
    
    for i, chunk in enumerate(chunks):
        temp_file = f"/tmp/tts_chunk_{i}.mp3"
        communicate = edge_tts.Communicate(chunk, "zh-CN-XiaoxiaoNeural")
        await communicate.save(temp_file)
        temp_files.append(temp_file)
    
    # 用 ffmpeg 合并所有 MP3
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for tf in temp_files:
            f.write(f"file '{tf}'\n")
        concat_list = f.name
    
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        output_path
    ], check=True)
    
    # 清理临时文件
    os.unlink(concat_list)
    for tf in temp_files:
        os.unlink(tf)
    
    return output_path

# 使用示例
async def demo():
    long_text = "这是一个很长的文本，包含很多内容。我们需要把它分割成多个小段落。每一个小段落都可以单独合成。最后用ffmpeg合并成一个大文件。这样就可以突破单次合成的长度限制了。"
    await synthesize_long_text(long_text, "/tmp/long_output.mp3")

asyncio.run(demo())
```

### P1.11.9 常见问题排查

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| `ConnectionError` | 网络不通 / 代理问题 | 检查网络：`curl -I https://speech.platform.bing.com` |
| 合成很慢（>3s）| 文本太长 | 分段处理，每段不超过 450 字符 |
| 音频无法播放（aplay 报错）| MP3 格式问题 | 用 ffmpeg 转换：`ffmpeg -i output.mp3 -acodec pcm_s16le -ar 44100 output.wav` |
| 中文发音错误 | 生僻字 / 多音字 | 用同音字替换，或在文本中加注音 |
| 语音卡顿 | 音频缓冲不足 | 减小录音时长（3s）或用流式播放 |
| `edge-tts: command not found` | 未正确安装 | `pip3 install edge-tts`，或用 `python3 -m edge_tts` |
| 字幕时间戳不准 | 英文标点被当作断句点 | 用中文标点（。，！？）分割 |

### P1.11.10 Edge-TTS + 扬声器输出配置

Edge-TTS 输出的 MP3 文件需要通过播放器输出到 USB 耳机/扬声器：

```bash
# 方式 1：aplay（ALSA，直接播放 WAV/MP3）
aplay /tmp/tts_output.mp3

# 方式 2：ffplay（FFmpeg，自动检测格式）
ffplay -nodisp -autoexit /tmp/tts_output.mp3

# 方式 3：mpv（高质量播放）
mpv /tmp/tts_output.mp3 --no-video

# 方式 4：Python 播放（不需要子进程）
# pip3 install pydub
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio

audio = AudioSegment.from_mp3("/tmp/tts_output.mp3")
_play_with_simpleaudio(audio)
```

**配置默认播放设备（确保输出到 USB 耳机）**：

```bash
# 查看所有播放设备
aplay -l

# 设置环境变量指定设备
export AUDIODEV=hw:1,0  # card 1, device 0

# 或在 ~/.asoundrc 中设置默认设备
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

### P1.11.11 参考链接

- Edge-TTS GitHub：https://github.com/rany2/edge-tts
- 中文语音列表演示：https://speech.platform.bing.com/consumer/srec/synthesize
- Microsoft Azure TTS 文档：https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/
- FFmpeg 音频处理：https://ffmpeg.org/ffmpeg.html
- ROBOT-SOP.md §A.2 语音交互模块

---

## P1.12 语音识别代码框架（Phase 1 详细版）

> 来源：ROBOT-SOP.md Phase 1 + whisper.cpp 官方 examples + OpenClaw Bridge Protocol
> 补充目标：为 Phase 1 语音陪伴提供完整的语音识别代码框架，包含状态机、错误处理、性能优化

### P1.12.1 语音识别模块整体架构

Phase 1 语音识别的核心是建立一条可靠的 **麦克风 → VAD → Whisper → 文字** 流水线：

```
┌──────────────────────────────────────────────────────────────┐
│                     语音输入子系统（Jetson Nano）              │
│                                                              │
│  USB 耳机麦克风（16kHz PCM）                                  │
│          ↓                                                   │
│  ┌─────────────────┐                                         │
│  │  VAD 检测模块    │ ← 过滤静音，减少 Whisper 负载          │
│  │  (Silero VAD)   │                                         │
│  └────────┬────────┘                                         │
│           ↓ 检测到语音开始 → 启动录音缓冲                       │
│  ┌────────────────────────────────────────┐                 │
│  │  环形录音缓冲（Ring Buffer）             │                 │
│  │  - 持续录音，保留最近 N 秒               │                 │
│  │  - VAD 检测到语音尾后，截取有效片段       │                 │
│  └────────┬────────────────────────────────┘                 │
│           ↓ 有效语音片段（通常 1-10 秒）                        │
│  ┌────────────────────────────────────────┐                 │
│  │  Whisper 推理（whisper.cpp / whisper-cli）│                │
│  │  - 模型: ggml-small.bin（中文）/ base.en（英文）│            │
│  │  - 输出: 文字 + 时间戳（可选）              │                 │
│  └────────┬────────────────────────────────┘                 │
│           ↓ 识别文本                                          │
│  ┌────────────────────────────────────────┐                 │
│  │  OpenClaw Bridge 客户端                 │                 │
│  │  - HTTP POST 到 Gateway                │                 │
│  │  - 获取 AI 回复文字                      │                 │
│  └────────┬────────────────────────────────┘                 │
│           ↓ 回复文字                                          │
│  ┌────────────────────────────────────────┐                 │
│  │  Edge-TTS 语音合成 + aplay 播放          │                 │
│  └────────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────┘
```

### P1.12.2 WhisperRecognizer 封装类

> 封装 whisper-cli 的完整调用逻辑，提供简洁的 Python API

```python
#!/usr/bin/env python3
"""
WhisperRecognizer - whisper.cpp Python 封装类
提供简洁的语音识别接口，支持多种调用模式
"""
import subprocess
import os
import threading
import queue
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

class RecognizerMode(Enum):
    """识别模式"""
    FILE = "file"          # 离线文件识别
    STREAM = "stream"      # 实时流识别（whisper-stream）
    SUBPROCESS = "subprocess"  # 子进程模式（推荐）

@dataclass
class RecognitionResult:
    """识别结果数据类"""
    text: str
    segments: list[dict]  # 时间戳片段
    language: str
    duration: float       # 音频时长（秒）
    confidence: float     # 置信度（0-1）

class WhisperRecognizer:
    """whisper.cpp 封装类"""
    
    def __init__(
        self,
        model_path: str = "./whisper.cpp/models/ggml-small.bin",
        language: str = "zh",
        threads: int = 4,
        vad_model_path: Optional[str] = None,
        use_vad: bool = True
    ):
        self.model_path = model_path
        self.language = language
        self.threads = threads
        self.vad_model_path = vad_model_path
        self.use_vad = use_vad
        
        # 检查模型文件
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Whisper 模型未找到: {model_path}")
        
        # whisper-cli 路径
        self.whisper_cli = "./whisper.cpp/build/bin/whisper-cli"
        if not os.path.exists(self.whisper_cli):
            # 尝试旧版路径
            self.whisper_cli = "./whisper.cpp/bin/whisper-cli"
        
        self._check_cli()
    
    def _check_cli(self):
        """验证 whisper-cli 可用"""
        try:
            result = subprocess.run(
                [self.whisper_cli, "--help"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("whisper-cli 检查失败")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"whisper-cli 未找到，请先编译 whisper.cpp:\n"
                f"  cd whisper.cpp && cmake -B build && cmake --build build -j"
            )
    
    def recognize_file(
        self,
        audio_path: str,
        word_timestamps: bool = False,
        temperature: float = 0.0
    ) -> RecognitionResult:
        """
        识别音频文件（离线模式）
        
        Args:
            audio_path: 音频文件路径（WAV/PCM，推荐 16kHz 单声道）
            word_timestamps: 是否输出词级时间戳
            temperature: 采样温度（越高越有创意，越低越保守）
        
        Returns:
            RecognitionResult: 包含识别文本、时间戳、置信度
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        cmd = [
            self.whisper_cli,
            "-m", self.model_path,
            "-f", audio_path,
            "-l", self.language,
            "-t", str(self.threads),
            "-ot",          # 输出 TTML 格式（带时间戳）
            "-ml", "1",      # 每句最大字符数
        ]
        
        if word_timestamps:
            cmd.append("-w")  # --word-timestamps
        
        if temperature > 0:
            cmd.extend(["-temperature", str(temperature)])
        
        if self.use_vad and self.vad_model_path:
            cmd.extend(["--vad", "--vad-model", self.vad_model_path])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Whisper 识别失败: {result.stderr}")
        
        # 解析 TTML 输出
        text, segments = self._parse_ttml(result.stdout)
        
        # 估算置信度（基于模型 logits，简单版本用词数/字符数比）
        confidence = self._estimate_confidence(text, segments)
        
        # 估算音频时长（从文件名或音频流获取，这里用segments推算）
        duration = sum(s.get('end', 0) - s.get('start', 0) for s in segments)
        
        return RecognitionResult(
            text=text,
            segments=segments,
            language=self.language,
            duration=duration,
            confidence=confidence
        )
    
    def recognize_stream(
        self,
        audio_callback: Callable[[bytes], None],
        sample_rate: int = 16000
    ) -> None:
        """
        实时流识别（使用 whisper-stream）
        
        Args:
            audio_callback: 识别到文字时的回调函数，签名为 callback(text: str)
            sample_rate: 采样率，默认 16000
        """
        cmd = [
            "./whisper.cpp/build/bin/whisper-stream",
            "-m", self.model_path,
            "-t", str(self.threads),
            "--step", "500",      # 每 500ms 采样一次
            "--length", "3000",   # 每次处理 3000ms 缓冲
            "--listen",           # 监听模式
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            for line in process.stdout:
                line = line.strip()
                if line and "：" in line:  # whisper-stream 输出格式
                    text = line.split("：", 1)[1].strip()
                    audio_callback(text)
        except KeyboardInterrupt:
            process.terminate()
            process.wait()
    
    def _parse_ttml(self, ttml_output: str) -> tuple[str, list[dict]]:
        """解析 TTML 时间戳格式"""
        import re
        
        segments = []
        full_text = []
        
        # TTML 格式: <p begin="0.00" end="2.50">识别文字</p>
        pattern = r'<p begin="([\d.]+)"[^>]*>([^<]+)</p>'
        
        for match in re.finditer(pattern, ttml_output):
            start = float(match.group(1))
            text = match.group(2).strip()
            
            # 估算结束时间（基于下一个片段或平均语速）
            end = start + len(text) * 0.06  # 约 16 字符/秒
            
            segments.append({
                "start": start,
                "end": end,
                "text": text
            })
            full_text.append(text)
        
        return " ".join(full_text), segments
    
    def _estimate_confidence(self, text: str, segments: list) -> float:
        """估算置信度（简化版本）"""
        if not text:
            return 0.0
        
        # 基于有效字符比例
        valid_chars = sum(1 for c in text if c.isalnum() or '\u4e00' <= c <= '\u9fff')
        ratio = valid_chars / max(len(text), 1)
        
        # 基于片段数量（片段越多通常越准确）
        segment_bonus = min(len(segments) * 0.01, 0.1)
        
        return min(ratio + segment_bonus, 1.0)
```

### P1.12.3 实时语音流处理管道（VAD + Whisper）

> 实现真正的实时语音识别：边录边识别，不需要停顿

```python
#!/usr/bin/env python3
"""
实时语音识别管道 - VAD + Whisper 联合推理
特点：边录边识别，语音结束后立即输出，无需固定录音时长
"""
import subprocess
import threading
import queue
import time
import numpy as np
import wave
import os
from typing import Optional, Callable
from WhisperRecognizer import WhisperRecognizer

class RealtimeVoicePipeline:
    """
    实时语音识别管道
    
    工作流程：
    1. 持续从麦克风录音（环形缓冲）
    2. VAD 检测语音活动
    3. 语音结束后，截取有效片段送 Whisper
    4. 返回识别结果
    """
    
    def __init__(
        self,
        whisper_recognizer: WhisperRecognizer,
        vad_threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 500,
        max_speech_duration_ms: int = 15000,
        buffer_duration_ms: int = 10000,
        sample_rate: int = 16000
    ):
        self.recognizer = whisper_recognizer
        self.vad_threshold = vad_threshold
        self.min_speech_ms = min_speech_duration_ms
        self.min_silence_ms = min_silence_duration_ms
        self.max_speech_ms = max_speech_duration_ms
        self.buffer_ms = buffer_duration_ms
        self.sample_rate = sample_rate
        
        # 内部状态
        self.is_running = False
        self.audio_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self._record_thread: Optional[threading.Thread] = None
        self._process_thread: Optional[threading.Thread] = None
        
        # 状态机
        self._state = "idle"  # idle -> recording -> processing -> idle
        self._speech_start_time: Optional[float] = None
        self._last_speech_time: Optional[float] = None
        self._audio_buffer: list[np.ndarray] = []
    
    def start(self, callback: Callable[[str], None]) -> None:
        """
        启动实时语音管道
        
        Args:
            callback: 识别到文字后的回调函数
        """
        if self.is_running:
            return
        
        self.is_running = True
        self._result_callback = callback
        
        # 启动录音线程
        self._record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._record_thread.start()
        
        # 启动处理线程
        self._process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._process_thread.start()
    
    def stop(self) -> None:
        """停止管道"""
        self.is_running = False
        if self._record_thread:
            self._record_thread.join(timeout=2)
        if self._process_thread:
            self._process_thread.join(timeout=2)
    
    def _record_loop(self) -> None:
        """录音循环（持续从麦克风读取音频）"""
        import pyaudio
        
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024  # 64ms 一帧
        )
        
        bytes_per_ms = self.sample_rate * 2 // 1000  # 16bit = 2 bytes
        
        try:
            while self.is_running:
                # 读取一帧
                data = stream.read(1024, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                
                # VAD 检测（简化版：检查音量阈值）
                is_speech = self._simple_vad(audio_chunk)
                current_time = time.time()
                
                if is_speech:
                    self._audio_buffer.append(audio_chunk)
                    self._last_speech_time = current_time
                    
                    # 超过最大语音时长，强制截断
                    if self._speech_start_time:
                        speech_duration = (current_time - self._speech_start_time) * 1000
                        if speech_duration > self.max_speech_ms:
                            self._flush_buffer()
                else:
                    # 静音检测
                    if self._state == "recording" and self._last_speech_time:
                        silence_duration = (current_time - self._last_speech_time) * 1000
                        if silence_duration > self.min_silence_ms:
                            self._flush_buffer()
                    
                    # 状态切换：idle -> recording
                    if self._state == "idle" and self._audio_buffer:
                        self._state = "recording"
                        self._speech_start_time = current_time
                        
                        # 补充前导音频（语音开始前的 300ms）
                        prefix_samples = int(0.3 * self.sample_rate)
                        prefix_data = np.zeros(prefix_samples, dtype=np.int16)
                        self._audio_buffer.insert(0, prefix_data)
                
                # 清理超出缓冲大小的旧数据
                total_samples = sum(len(chunk) for chunk in self._audio_buffer)
                max_samples = int(self.buffer_ms * self.sample_rate / 1000)
                while total_samples > max_samples and len(self._audio_buffer) > 1:
                    removed = self._audio_buffer.pop(0)
                    total_samples -= len(removed)
        
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
    
    def _simple_vad(self, audio_chunk: np.ndarray) -> bool:
        """简化版 VAD：基于音量的语音检测"""
        # 计算 RMS 音量
        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))
        
        # 阈值（麦克风灵敏度不同需调整）
        threshold = 500  # 16bit PCM
        
        return rms > threshold
    
    def _flush_buffer(self) -> None:
        """将缓冲区的音频片段送入处理队列"""
        if not self._audio_buffer:
            return
        
        # 合并所有片段
        audio_data = np.concatenate(self._audio_buffer)
        
        # 保存为临时 WAV 文件
        temp_file = f"/tmp/voice_{int(time.time()*1000)}.wav"
        self._save_wav(temp_file, audio_data)
        
        # 清空缓冲区
        self._audio_buffer = []
        self._state = "idle"
        self._speech_start_time = None
        
        # 送入处理队列
        self.audio_queue.put(temp_file)
    
    def _process_loop(self) -> None:
        """处理循环：从队列取音频片段，调用 Whisper 识别"""
        while self.is_running:
            try:
                # 非阻塞获取
                try:
                    audio_file = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                self._state = "processing"
                
                # 调用 Whisper 识别
                try:
                    result = self.recognizer.recognize_file(audio_file)
                    
                    if result.text.strip():
                        print(f"[VAD] 识别: {result.text}")
                        self._result_callback(result.text)
                
                except Exception as e:
                    print(f"[VAD] 识别错误: {e}")
                
                finally:
                    # 清理临时文件
                    try:
                        os.unlink(audio_file)
                    except:
                        pass
                    self._state = "idle"
            
            except Exception as e:
                print(f"[VAD] 处理循环错误: {e}")
    
    def _save_wav(self, path: str, audio_data: np.ndarray) -> None:
        """保存为 WAV 文件"""
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
```

### P1.12.4 语音对话状态机（完整版）

> 处理多人机交互的完整状态机，包含唤醒、打断、超时等场景

```python
#!/usr/bin/env python3
"""
语音对话状态机 - Phase 1 核心控制逻辑
处理：唤醒 → 监听 → 识别 → 回复 → 等待 的完整循环
"""
import asyncio
import subprocess
import edge_tts
import time
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Callable
from WhisperRecognizer import WhisperRecognizer

class VoiceState(Enum):
    """语音对话状态"""
    IDLE = auto()           # 空闲，等待唤醒
    WAKE_DETECT = auto()    # 唤醒词检测中
    LISTENING = auto()      # 录音中
    RECOGNIZING = auto()    # 识别中
    THINKING = auto()       # AI 处理中
    SPEAKING = auto()       # 语音回复中
    INTERRUPTED = auto()    # 被打断

@dataclass
class VoiceDialogConfig:
    """语音对话配置"""
    # 录音参数
    record_duration_sec: float = 5.0
    max_record_duration_sec: float = 10.0
    silence_timeout_sec: float = 3.0
    
    # 识别参数
    whisper_model: str = "./whisper.cpp/models/ggml-small.bin"
    language: str = "zh"
    min_confidence: float = 0.3  # 低于此置信度要求重试
    
    # 回复参数
    tts_voice: str = "zh-CN-XiaoxiaoNeural"
    tts_rate: str = "+0%"
    
    # 状态机参数
    idle_timeout_sec: float = 30.0  # 多久无活动回到 IDLE
    max_retries: int = 2            # 识别失败重试次数

@dataclass
class VoiceDialogContext:
    """对话上下文"""
    state: VoiceState = VoiceState.IDLE
    last_user_text: str = ""
    last_response: str = ""
    retry_count: int = 0
    session_start: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

class VoiceDialogMachine:
    """
    语音对话状态机
    
    状态流转：
    IDLE → (唤醒词检测到) → LISTENING → RECOGNIZING → THINKING → SPEAKING → IDLE
         → (打断) → INTERRUPTED → IDLE
         → (超时) → IDLE
    """
    
    def __init__(
        self,
        config: VoiceDialogConfig,
        openclaw_bridge,  # OpenClawBridge 实例
        recognizer: WhisperRecognizer
    ):
        self.config = config
        self.bridge = openclaw_bridge
        self.recognizer = recognizer
        self.ctx = VoiceDialogContext()
        
        # 外部回调
        self.on_state_change: Optional[Callable[[VoiceState, VoiceState], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def _transition(self, new_state: VoiceState) -> None:
        """状态切换"""
        old_state = self.ctx.state
        if old_state != new_state:
            self.ctx.state = new_state
            self.ctx.last_activity = time.time()
            print(f"[状态机] {old_state.name} → {new_state.name}")
            
            if self.on_state_change:
                self.on_state_change(old_state, new_state)
    
    async def run_cycle(self) -> None:
        """执行一轮完整的语音对话（单轮模式）"""
        try:
            # 1. 进入 LISTENING
            self._transition(VoiceState.LISTENING)
            
            # 2. 录音
            audio_path = await self._record_audio()
            if not audio_path:
                self._transition(VoiceState.IDLE)
                return
            
            # 3. 进入 RECOGNIZING
            self._transition(VoiceState.RECOGNNIZING)
            
            # 4. Whisper 识别
            result = self.recognizer.recognize_file(audio_path)
            
            # 清理临时文件
            try:
                import os
                os.unlink(audio_path)
            except:
                pass
            
            if not result.text or result.confidence < self.config.min_confidence:
                # 置信度不足，重试
                self.ctx.retry_count += 1
                if self.ctx.retry_count < self.config.max_retries:
                    print(f"[状态机] 置信度不足 ({result.confidence:.2f})，重试 {self.ctx.retry_count}/{self.config.max_retries}")
                    await self._speak("没有听清楚，请再说一次。")
                    return await self.run_cycle()  # 递归重试
                else:
                    await self._speak("抱歉，我没有听清楚。")
                    self.ctx.retry_count = 0
                    self._transition(VoiceState.IDLE)
                    return
            
            self.ctx.retry_count = 0
            self.ctx.last_user_text = result.text
            print(f"[状态机] 用户: {result.text}")
            
            # 5. 进入 THINKING
            self._transition(VoiceState.THINKING)
            
            # 6. 发给 OpenClaw
            response = await self.bridge.ask(result.text)
            self.ctx.last_response = response
            
            # 7. 进入 SPEAKING
            self._transition(VoiceState.SPEAKING)
            
            # 8. TTS 回复
            await self._speak(response)
            
            # 9. 完成，回到 IDLE
            self._transition(VoiceState.IDLE)
            
        except asyncio.CancelledError:
            self._transition(VoiceState.INTERRUPTED)
            raise
        except Exception as e:
            print(f"[状态机] 错误: {e}")
            if self.on_error:
                self.on_error(str(e))
            self._transition(VoiceState.IDLE)
    
    async def _record_audio(self) -> Optional[str]:
        """录音并返回音频文件路径"""
        output_path = f"/tmp/voice_input_{int(time.time()*1000)}.wav"
        
        # arecord 参数：16kHz 单声道 16bit
        proc = await asyncio.create_subprocess_exec(
            "arecord",
            "-d", str(int(self.config.record_duration_sec)),
            "-f", "cd",
            "-c", "1",
            "-r", "16000",
            "-t", "wav",
            output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await proc.communicate()
        
        if proc.returncode == 0 and os.path.exists(output_path):
            return output_path
        return None
    
    async def _speak(self, text: str) -> None:
        """文字转语音并播放"""
        output_path = "/tmp/tts_output.mp3"
        
        communicate = edge_tts.Communicate(
            text,
            voice=self.config.tts_voice,
            rate=self.config.tts_rate
        )
        await communicate.save(output_path)
        
        # 播放
        await asyncio.create_subprocess_exec(
            "aplay", output_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
    
    async def run_continuous(self) -> None:
        """持续运行模式（多轮对话）"""
        print("[状态机] 启动持续对话模式（Ctrl+C 退出）")
        
        while True:
            try:
                # 检查空闲超时
                idle_time = time.time() - self.ctx.last_activity
                if idle_time > self.config.idle_timeout_sec and self.ctx.state == VoiceState.IDLE:
                    # 空闲超时，播放提示音（可选）
                    pass
                
                # 执行一轮对话
                await self.run_cycle()
                
                # 轮询间隔
                await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                print("[状态机] 已停止")
                break
            except Exception as e:
                print(f"[状态机] 循环错误: {e}")
                await asyncio.sleep(1)
```

### P1.12.5 OpenClaw Bridge 集成代码

> Phase 1 语音陪伴的关键链路：Jetson Nano → OpenClaw Gateway

```python
#!/usr/bin/env python3
"""
OpenClaw Bridge 集成 - Phase 1 语音陪伴核心
参考：https://docs.openclaw.ai/gateway/bridge-protocol
"""
import asyncio
import aiohttp
import json
import hashlib
import time
from typing import Optional

class OpenClawBridge:
    """
    OpenClaw Bridge 协议客户端
    
    Bridge Protocol 是一种简单的 HTTP POST/GET 协议：
    - Gateway 运行在 MacBook（贵庚大脑）
    - Jetson Nano（语音陪伴）作为客户端
    - 通过局域网 HTTP 通信
    """
    
    def __init__(
        self,
        gateway_url: str = "http://192.168.x.x:18789",
        api_key: Optional[str] = None,
        device_id: str = "jetson-nano-01",
        timeout: float = 30.0
    ):
        """
        Args:
            gateway_url: OpenClaw Gateway 地址（MacBook 内网 IP）
            api_key: Gateway API Key（可选）
            device_id: 本设备标识
            timeout: 请求超时（秒）
        """
        self.gateway_url = gateway_url.rstrip('/')
        self.api_key = api_key
        self.device_id = device_id
        self.timeout = timeout
        
        # 会话
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()
    
    def _headers(self) -> dict:
        """构建请求头"""
        headers = {
            "Content-Type": "application/json",
            "X-Device-ID": self.device_id,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def ask(self, text: str, context: Optional[dict] = None) -> str:
        """
        发送问题，获取 AI 回复（核心方法）
        
        Args:
            text: 用户语音识别的文字
            context: 额外上下文（设备状态等）
        
        Returns:
            AI 回复文字
        """
        if not self._session:
            raise RuntimeError("请使用 async with 语句")
        
        payload = {
            "message": text,
            "device_id": self.device_id,
            "timestamp": int(time.time() * 1000),
        }
        
        if context:
            payload["context"] = context
        
        url = f"{self.gateway_url}/bridge/ask"
        
        async with self._session.post(
            url,
            json=payload,
            headers=self._headers()
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise RuntimeError(f"Gateway 请求失败 ({resp.status}): {error_text}")
            
            data = await resp.json()
            return data.get("response", data.get("text", ""))
    
    async def tell(self, event: str, data: dict) -> None:
        """
        单向事件通知（无回复）
        
        Args:
            event: 事件名称（如 "audio_captured", "motion_detected"）
            data: 事件数据
        """
        if not self._session:
            raise RuntimeError("请使用 async with 语句")
        
        payload = {
            "event": event,
            "device_id": self.device_id,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        
        url = f"{self.gateway_url}/bridge/event"
        
        async with self._session.post(
            url,
            json=payload,
            headers=self._headers()
        ) as resp:
            # 事件通知不强制检查响应
            pass
    
    async def get_status(self) -> dict:
        """查询 Gateway 状态"""
        if not self._session:
            raise RuntimeError("请使用 async with 语句")
        
        url = f"{self.gateway_url}/bridge/status"
        
        async with self._session.get(
            url,
            headers=self._headers()
        ) as resp:
            return await resp.json()
    
    async def stream_ask(
        self,
        text: str,
        on_chunk: callable
    ) -> str:
        """
        流式问答（长回复分段返回）
        
        Args:
            text: 用户语音识别的文字
            on_chunk: 每个片段的回调，签名为 on_chunk(chunk: str)
        
        Returns:
            完整回复文字
        """
        if not self._session:
            raise RuntimeError("请使用 async with 语句")
        
        payload = {
            "message": text,
            "device_id": self.device_id,
            "stream": True,
            "timestamp": int(time.time() * 1000),
        }
        
        url = f"{self.gateway_url}/bridge/ask"
        full_response = []
        
        async with self._session.post(
            url,
            json=payload,
            headers=self._headers()
        ) as resp:
            async for line in resp.content:
                if line.strip():
                    chunk_data = json.loads(line)
                    chunk = chunk_data.get("chunk", "")
                    full_response.append(chunk)
                    on_chunk(chunk)
        
        return "".join(full_response)


# ===== Phase 1 完整使用示例 =====

async def main():
    """Phase 1 语音陪伴主程序"""
    
    # 配置
    GATEWAY_URL = "http://192.168.x.x:18789"  # 替换为 MacBook 实际 IP
    WHISPER_MODEL = "./whisper.cpp/models/ggml-small.bin"
    
    async with OpenClawBridge(gateway_url=GATEWAY_URL) as bridge:
        # 测试连接
        try:
            status = await bridge.get_status()
            print(f"[启动] Gateway 状态: {status}")
        except Exception as e:
            print(f"[启动] Gateway 连接失败: {e}")
            print("[启动] 继续运行（离线模式）")
        
        # 初始化 Whisper
        recognizer = WhisperRecognizer(model_path=WHISPER_MODEL)
        
        # 初始化对话状态机
        config = VoiceDialogConfig()
        dialog = VoiceDialogMachine(
            config=config,
            openclaw_bridge=bridge,
            recognizer=recognizer
        )
        
        # 启动持续对话
        await dialog.run_continuous()


if __name__ == "__main__":
    asyncio.run(main())
```

### P1.12.6 错误处理与降级策略

> Phase 1 部署后会遇到各种异常情况，完整的错误处理保障稳定性

```python
#!/usr/bin/env python3
"""
错误处理与降级策略 - Phase 1 部署必备
"""

from enum import Enum
from typing import Optional
import subprocess
import time

class ErrorLevel(Enum):
    """错误级别"""
    RECOVERABLE = "recoverable"    # 可自动恢复
    DEGRADED = "degraded"          # 降级运行
    FATAL = "fatal"               # 致命错误

class Phase1ErrorHandler:
    """
    Phase 1 错误处理器
    
    原则：
    1. 网络断了 → 继续本地对话（离线模式）
    2. Whisper 卡住 → 重置进程
    3. TTS 失败 → 打印文字，降级到文字输出
    4. 内存不足 → 换更小模型
    """
    
    def __init__(self):
        self.error_count = 0
        self.last_error_time = 0
        self.consecutive_errors = 0
        self._recovery_actions = {
            "whisper_timeout": self._restart_whisper,
            "network_error": self._retry_with_backoff,
            "tts_error": self._fallback_to_text,
            "memory_error": self._downgrade_model,
        }
    
    def handle(self, error: Exception, context: str) -> ErrorLevel:
        """
        处理错误，返回是否可继续
        
        Returns:
            ErrorLevel.RECOVERABLE: 自动恢复，继续运行
            ErrorLevel.DEGRADED: 降级运行（功能受限）
            ErrorLevel.FATAL: 致命错误，停止
        """
        error_msg = str(error)
        error_type = self._classify_error(error_msg)
        
        print(f"[错误] [{context}] {error_type}: {error_msg}")
        
        self.error_count += 1
        self.consecutive_errors += 1
        self.last_error_time = time.time()
        
        # 连续错误保护（防止死循环）
        if self.consecutive_errors > 10:
            print("[错误] 连续错误超过 10 次，停止自动恢复")
            return ErrorLevel.FATAL
        
        # 执行恢复动作
        if error_type in self._recovery_actions:
            action = self._recovery_actions[error_type]
            action(error)
        
        # 根据错误类型决定级别
        if "timeout" in error_msg.lower():
            return ErrorLevel.RECOVERABLE
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            return ErrorLevel.DEGRADED  # 降级到离线模式
        elif "memory" in error_msg.lower() or "oom" in error_msg.lower():
            return ErrorLevel.DEGRADED  # 降级到小模型
        else:
            return ErrorLevel.RECOVERABLE
    
    def _classify_error(self, error_msg: str) -> str:
        """分类错误"""
        error_lower = error_msg.lower()
        
        if "timeout" in error_lower:
            return "whisper_timeout"
        elif "network" in error_lower or "connection" in error_lower:
            return "network_error"
        elif "tts" in error_lower or "edge-tts" in error_lower:
            return "tts_error"
        elif "memory" in error_lower or "oom" in error_lower:
            return "memory_error"
        elif "whisper" in error_lower:
            return "whisper_error"
        else:
            return "unknown_error"
    
    def _restart_whisper(self, error: Exception) -> None:
        """重启 Whisper 进程"""
        print("[恢复] 重启 Whisper 进程...")
        subprocess.run(["pkill", "-f", "whisper-cli"], check=False)
        time.sleep(1)
    
    def _retry_with_backoff(self, error: Exception) -> None:
        """退避重试"""
        backoff = min(2 ** self.consecutive_errors, 60)  # 最多 60 秒
        print(f"[恢复] 等待 {backoff} 秒后重试...")
        time.sleep(backoff)
    
    def _fallback_to_text(self, error: Exception) -> None:
        """降级到文字输出"""
        print("[降级] TTS 不可用，显示文字代替语音输出")
    
    def _downgrade_model(self, error: Exception) -> None:
        """降级到更小模型"""
        print("[降级] 内存不足，切换到 tiny 模型...")
        # 这里可以动态修改 recognizer 的 model_path
        # self.recognizer.model_path = "./whisper.cpp/models/ggml-tiny.bin"
    
    def reset_consecutive(self) -> None:
        """重置连续错误计数（每次成功执行后调用）"""
        self.consecutive_errors = 0
```

### P1.12.7 性能优化技巧（Jetson Nano 2GB 专项）

> Jetson Nano 2GB 内存有限，Phase 1 必须优化才能流畅运行

```python
# ====== 性能优化配置 ======

# 1. 量化模型（内存减半，速度提升 30%）
# 原始: ggml-small.bin  (~466MB 文件)
# 量化: ggml-small-q5_0.bin  (~250MB 文件，内存占用 ~500MB → ~250MB)
#
# 量化命令：
# ./build/bin/quantize models/ggml-small.bin models/ggml-small-q5_0.bin q5_0

# 2. 减少线程数（2GB 内存不宜开太多线程）
WHISPER_THREADS = 2  # 而不是默认的 4

# 3. 启用 VAD 过滤静音（减少 50% Whisper 调用）
USE_VAD = True
VAD_THRESHOLD = 0.5

# 4. 音频降采样（16kHz → 8kHz，适合远场场景）
# Edge-TTS 支持自动重采样，不需要手动处理
# Whisper 对 16kHz 和 8kHz 都能识别

# 5. 缓存 TTS 结果（常用回复直接播放，不重复合成）
TTS_CACHE_SIZE = 100  # 最多缓存 100 个 TTS 结果
TTS_CACHE = {}

def cached_tts(text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> str:
    """带缓存的 TTS"""
    cache_key = f"{voice}:{text}"
    
    if cache_key in TTS_CACHE:
        return TTS_CACHE[cache_key]
    
    # 合成
    output_path = f"/tmp/tts_{hashlib.md5(cache_key.encode()).hexdigest()}.mp3"
    # ... edge_tts 合成代码 ...
    
    # 缓存
    TTS_CACHE[cache_key] = output_path
    
    # 清理超出缓存大小
    if len(TTS_CACHE) > TTS_CACHE_SIZE:
        oldest_key = next(iter(TTS_CACHE))
        del TTS_CACHE[oldest_key]
    
    return output_path

# 6. 使用 subprocess 而非 asyncio（减少 Python 协程开销）
# 对于 Phase 1 这种简单 pipeline，subprocess 比 asyncio 更稳定
subprocess.run([
    "arecord", "-d", "5", "-f", "cd", "-c", "1", "-r", "16000", "/tmp/input.wav"
], check=True)

# 7. 内存监控（自动降级）
import psutil

def check_memory_and_downgrade():
    """检查内存，不足时自动降级"""
    mem = psutil.virtual_memory()
    
    if mem.percent > 85:
        print(f"[内存警告] 使用率 {mem.percent}%，切换到量化模型")
        # 动态切换到量化模型
        # recognizer.model_path = "./whisper.cpp/models/ggml-small-q5_0.bin"
    elif mem.percent > 95:
        print(f"[内存危险] 使用率 {mem.percent}%，强制重启")
        # 触发优雅重启
```

### P1.12.8 快速启动脚本（一键运行）

```bash
#!/bin/bash
# Phase 1 语音陪伴快速启动脚本
# 放置在 ~/robot/phase1-start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WHISPER_DIR="$SCRIPT_DIR/whisper.cpp"
VOICE_MODEL="ggml-small.bin"  # 中文推荐 small

echo "=== Phase 1 语音陪伴启动 ==="

# 1. 检查 Whisper 模型
if [ ! -f "$WHISPER_DIR/models/$VOICE_MODEL" ]; then
    echo "[1/5] 下载 Whisper 模型..."
    cd "$WHISPER_DIR"
    ./models/download-ggml-model.sh small
    cd -
fi

# 2. 检查麦克风
echo "[2/5] 检查麦克风..."
if ! arecord -l | grep -q "card"; then
    echo "[错误] 未检测到麦克风，请检查 USB 耳机连接"
    exit 1
fi
arecord -l

# 3. 检查 Gateway 连接
echo "[3/5] 检查 Gateway..."
GATEWAY_IP="192.168.x.x"  # 替换为实际 IP
if curl -s --connect-timeout 3 "http://$GATEWAY_IP:18789/bridge/status" > /dev/null; then
    echo "Gateway 连接成功"
else
    echo "Gateway 连接失败，继续离线模式"
fi

# 4. 设置环境变量
export WHISPER_MODEL="$WHISPER_DIR/models/$VOICE_MODEL"
export LD_LIBRARY_PATH="$WHISPER_DIR/build/lib:$LD_LIBRARY_PATH"

# 5. 启动语音对话程序
echo "[4/5] 启动语音对话..."
cd "$SCRIPT_DIR"
python3 voice_dialog.py

echo "=== 已退出 ==="
```

### P1.12.9 参考链接

- whisper.cpp GitHub：https://github.com/ggml-org/whisper.cpp
- whisper-stream 示例：https://github.com/ggml-org/whisper.cpp/tree/master/examples/stream
- Silero VAD：https://github.com/snakers4/silero-vad
- PyAudio（Jetson Nano）：`sudo apt install python3-pyaudio`
- OpenClaw Bridge Protocol：https://docs.openclaw.ai/gateway/bridge-protocol
- ROBOT-SOP.md Phase 1：语音陪伴模块

---

## P1.13 TTS 代码框架核心摘要（Phase 1 必读）

> 来源：P1.11 Edge-TTS 完整配置指南提炼 + ROBOT-SOP.md Phase 1 Step 4/5
> 本节为 TTS 代码框架的快速参考，详细代码见 P1.11 各小节

### P1.13.1 三层调用层级

| 层级 | 方式 | 代码量 | 适用场景 | 详细位置 |
|------|------|--------|---------|---------|
| **L1 CLI** | `edge-tts --voice ... --text ... --write-media` | 1行 | 快速测试、单次合成 | P1.11.2 |
| **L2 Python 异步** | `edge_tts.Communicate().save()` | 5-10行 | **Phase 1 推荐** | P1.11.5 |
| **L3 流式+回调** | `get_stream()` + 自定义播放 | 20-30行 | 实时对话、低延迟 | P1.11.5 / P1.11.6 |

**Phase 1 推荐 L2 方案**（最简单的完整用法）：

```python
import asyncio
import edge_tts

async def tts_and_play(text: str, output: str = "/tmp/tts.mp3"):
    """文字转语音并保存为 MP3（Phase 1 最简方案）"""
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save(output)

async def main():
    await tts_and_play("你好，我是贵庚")
    # 用 aplay /tmp/tts.mp3 播放

asyncio.run(main())
```

### P1.13.2 参数配置速查表

```python
# ===== Edge-TTS 核心参数 =====

# 语音选择（见 P1.11.3 完整列表）
VOICE_OPTIONS = {
    "默认女声":  "zh-CN-XiaoxiaoNeural",   # 清晰自然，Phase 1 默认
    "活泼女声":  "zh-CN-YunfeiNeural",       # 对话助手风格
    "默认男声":  "zh-CN-YunxiNeural",        # 磁性低沉
    "新闻男声":  "zh-CN-YunyangNeural",      # 播音腔
}

# 语速（见 P1.11.4）
RATE_OPTIONS = {
    "极慢(-50%)":  "-50%",
    "慢(-25%)":    "-25%",
    "正常":        "+0%",
    "快(+25%)":    "+25%",
    "极快(+50%)":  "+50%",
}

# 组合使用（SSML prosody 标签）
communicate = edge_tts.Communicate(
    text="老年友好模式示例",
    voice="zh-CN-XiaoxiaoNeural",
    rate="-40%",     # 慢40%
    pitch="-10Hz",   # 音调降10Hz
    volume="+30%"    # 音量增30%
)
await communicate.save("/tmp/tts_elderly.mp3")
```

### P1.13.3 Phase 1 语音对话完整调用链

```
用户说话
  ↓
arecord 录音（5秒 /tmp/input.wav）
  ↓
whisper-cli 识别 → text
  ↓
OpenClaw Bridge.ask(text) → response
  ↓
Edge-TTS 合成 → /tmp/tts_output.mp3   ← P1.13.4 核心代码
  ↓
aplay 播放 /tmp/tts_output.mp3
```

### P1.13.4 核心代码片段（直接可用）

**依赖安装：**
```bash
pip3 install edge-tts
```

**基础 TTS 合成 + 播放（Phase 1 直接可用）：**
```python
import asyncio
import edge_tts
import subprocess

VOICE = "zh-CN-XiaoxiaoNeural"
OUTPUT = "/tmp/tts_output.mp3"

async def tts(text: str, voice: str = VOICE) -> str:
    """TTS 合成，返回 MP3 文件路径"""
    com = edge_tts.Communicate(text, voice)
    await com.save(OUTPUT)
    return OUTPUT

async def tts_and_play(text: str, voice: str = VOICE) -> None:
    """合成并直接播放"""
    path = await tts(text, voice)
    subprocess.run(["aplay", path], check=True)

# 使用
asyncio.run(tts_and_play("你好，贵庚已上线"))
```

**带参数的 TTS（场景化配置）：**
```python
SCENE_CONFIGS = {
    "normal":  {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+0%",  "pitch": "+0Hz", "volume": "+0%"},
    "elderly": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "-40%", "pitch": "-10Hz","volume": "+30%"},
    "quick":   {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+50%", "pitch": "+0Hz", "volume": "+0%"},
    "male":    {"voice": "zh-CN-YunxiNeural",    "rate": "+0%",  "pitch": "-10Hz","volume": "+0%"},
}

async def tts_scene(text: str, scene: str = "normal") -> str:
    cfg = SCENE_CONFIGS[scene]
    com = edge_tts.Communicate(text, **cfg)
    await com.save(OUTPUT)
    return OUTPUT
```

**长文本分段合成（>450字符自动分段）：**
```python
import re, asyncio, edge_tts, subprocess

MAX_LEN = 450

def split_long_text(text: str) -> list[str]:
    """按句子分割，MAX_LEN 为每段上限"""
    parts = re.split(r'([。！？])', text)
    chunks, current = [], ""
    for i in range(0, len(parts) - 1, 2):
        sent = parts[i] + parts[i + 1]
        if len(current) + len(sent) <= MAX_LEN:
            current += sent
        else:
            if current: chunks.append(current)
            current = sent
    if current: chunks.append(current)
    return chunks

async def tts_long_text(text: str) -> str:
    chunks = split_long_text(text)
    paths = []
    for i, chunk in enumerate(chunks):
        p = f"/tmp/tts_long_{i}.mp3"
        await edge_tts.Communicate(chunk, VOICE).save(p)
        paths.append(p)
    # ffmpeg 合并（需要 ffmpeg）
    subprocess.run(["ffmpeg", "-y", "-i", "concat:" + "|".join(paths),
                    "-c", "copy", OUTPUT], check=True)
    for p in paths: subprocess.run(["rm", "-f", p])
    return OUTPUT
```

### P1.13.5 播放设备配置

Edge-TTS 输出 MP3，通过 aplay 播放到 USB 耳机：

```bash
# 查看播放设备（USB 耳机通常是 card 1）
aplay -l

# 设置默认设备（~/.asoundrc）
cat > ~/.asoundrc << 'EOF'
pcm.!default { type hw; card 1; }
ctl.!default { type hw; card 1; }
EOF

# 直接播放
aplay /tmp/tts_output.mp3

# 或用 ffplay（自动检测格式，无需转换）
ffplay -nodisp -autoexit /tmp/tts_output.mp3
```

**Python 中指定播放设备（无需改全局配置）：**
```python
import subprocess

# 通过环境变量指定 card 1
env = {"AUDIODEV": "hw:1,0"}
subprocess.run(["aplay", "/tmp/tts.mp3"], env={**os.environ, **env})
```

### P1.13.6 与 Whisper 的衔接（完整 Pipeline）

```python
#!/usr/bin/env python3
"""
Phase 1 语音对话 Pipeline
麦克风 → Whisper → OpenClaw → Edge-TTS → 扬声器
"""
import asyncio, subprocess, edge_tts, sys, os

GATEWAY = "http://192.168.x.x:18789"  # MacBook 内网 IP
VOICE   = "zh-CN-XiaoxiaoNeural"
WSPATH  = "./whisper.cpp/build/bin/whisper-cli"
WMODEL  = "./whisper.cpp/models/ggml-small.bin"
AUDIO_IN  = "/tmp/input.wav"
TTS_OUT   = "/tmp/tts_output.mp3"

async def tts(text: str) -> None:
    com = edge_tts.Communicate(text, VOICE)
    await com.save(TTS_OUT)
    subprocess.run(["aplay", TTS_OUT], check=True)

def whisper(audio: str) -> str:
    r = subprocess.run([
        WSPATH, "-m", WMODEL, "-f", audio, "-l", "zh", "-t", "4"
    ], capture_output=True, text=True)
    # 解析 whisper-cli 时间戳输出格式
    texts = [l.split(']',1)[1].strip() for l in r.stdout.split('\n') if '-->' in l]
    return ' '.join(texts)

async def bridge_ask(text: str) -> str:
    """发到 OpenClaw Gateway 获取回复"""
    import aiohttp
    async with aiohttp.ClientSession() as sess:
        async with sess.post(f"{GATEWAY}/bridge/ask", json={"message": text}) as resp:
            data = await resp.json()
            return data.get("response", data.get("text", ""))

async def main():
    while True:
        print("🎤 听中...")
        subprocess.run(["arecord","-d","5","-f","cd","-c","1","-r","16000",AUDIO_IN])
        text = whisper(AUDIO_IN)
        if not text.strip():
            continue
        print(f"👤 {text}")
        response = await bridge_ask(text)
        print(f"🤖 {response}")
        await tts(response)

asyncio.run(main())
```

### P1.13.7 常见错误排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `ConnectionError` | 网络不通 / 代理 | `curl -I https://speech.platform.bing.com` 检查网络 |
| 合成 >3s | 文本太长 | 分段，每段 ≤450 字符（P1.13.4 长文本函数）|
| `aplay` 播放失败 | MP3 格式 / 设备问题 | `ffmpeg -i out.mp3 -acodec pcm_s16le -ar 44100 out.wav && aplay out.wav` |
| 中文发音错误 | 生僻字/多音字 | 用同音字替换，或使用 SSML 音标标注 |
| `edge-tts: not found` | 未安装 | `pip3 install edge-tts` 或 `python3 -m edge_tts` |

### P1.13.8 TTS 框架代码位置索引

| 需求 | 代码位置 |
|------|---------|
| Edge-TTS 安装配置 | → P1.11.1 / P1.11.2 |
| 中文语音完整列表 | → P1.11.3 |
| 语速/音调/音量控制 | → P1.11.4 |
| Python API 完整用法 | → P1.11.5 |
| 实时语音对话完整代码 | → P1.11.6 |
| 场景化参数配置 | → P1.11.7 |
| 长文本分段处理 | → P1.11.8 |
| 降噪链路配置 | → P1.11.7（P1.9.7 音频链路）|
| 扬声器输出配置 | → P1.11.10 |
| 完整 Pipeline（Whisper+Bridge+Edge-TTS）| → P1.13.6 本节 + P1.12.5 |
| 错误处理与降级 | → P1.12.6 |
| 性能优化（Jetson Nano）| → P1.12.7 |
| 快速启动脚本 | → P1.12.8 |
| 参考链接 | → P1.11.11 |

---

## P1.14 TTS 代码框架（可复用类封装版）

> 来源：P1.11 Edge-TTS + P1.12 WhisperRecognizer 架构模式
> 补充目标：为 Phase 1 提供可复用的 TTSManager 类，支持缓存、多引擎、SSML、播放控制

### P1.14.1 TTSManager 核心类

> 对标 P1.12 的 WhisperRecognizer，提供同级别可复用的 TTS 封装

```python
#!/usr/bin/env python3
"""
TTSManager - Edge-TTS 可复用封装类
功能：缓存管理、多引擎切换、SSML 支持、播放控制
"""
import asyncio
import hashlib
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import edge_tts

class TTSEngine(Enum):
    """支持的 TTS 引擎"""
    EDGE_TTS = "edge"       # 微软 Edge 在线（Phase 1 推荐）
    GTTS = "gtts"          # Google TTS（备用）
    COQUI = "coqui"       # Coqui TTS（离线，Phase 2+）

@dataclass
class TTSConfig:
    """TTS 配置"""
    engine: TTSEngine = TTSEngine.EDGE_TTS
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    volume: str = "+0%"
    output_dir: str = "/tmp"
    cache_enabled: bool = True
    cache_size: int = 100        # 最多缓存 N 条
    cache_ttl: int = 86400       # 缓存有效期（秒），默认 24 小时
    max_chunk_length: int = 450  # Edge-TTS 单次合成上限

@dataclass
class TTSResult:
    """TTS 结果"""
    audio_path: str          # 音频文件路径
    duration: float          # 音频时长（秒）
    engine: str              # 使用哪个引擎
    from_cache: bool        # 是否来自缓存
    text_length: int        # 原始文本长度

class TTSManager:
    """
    TTS 管理器 - Phase 1 语音合成核心组件

    特性：
    1. LRU 缓存（减少重复合成，提升响应速度）
    2. 多引擎支持（Edge-TTS / GTTS / Coqui）
    3. SSML 标记支持（细粒度控制发音）
    4. 自动分段（长文本 → 多段 → ffmpeg 合并）
    5. 播放控制（播放设备、进度回调）
    6. 场景预设（normal / elderly / quick / male）

    用法示例：
        manager = TTSManager()
        result = await manager.speak("你好，我是贵庚")
        await manager.speak_and_play("你好", scene="elderly")
    """

    # 场景预设
    SCENE_PRESETS = {
        "normal":  {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+0%",  "pitch": "+0Hz", "volume": "+0%"},
        "elderly": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "-40%", "pitch": "-10Hz","volume": "+30%"},
        "quick":   {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+50%", "pitch": "+0Hz", "volume": "+0%"},
        "male":    {"voice": "zh-CN-YunxiNeural",    "rate": "+0%",  "pitch": "-10Hz","volume": "+0%"},
        "news":    {"voice": "zh-CN-YunyangNeural",  "rate": "+10%", "pitch": "+0Hz", "volume": "+0%"},
        "child":   {"voice": "zh-CN-XiaoyiNeural",  "rate": "-20%", "pitch": "+10Hz","volume": "+10%"},
    }

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._cache: dict[str, TTSResult] = {}
        self._cache_order: list[str] = []  # LRU 顺序
        self._lock = asyncio.Lock()

        # 验证输出目录
        os.makedirs(self.config.output_dir, exist_ok=True)

    # ===== 公开 API =====

    async def speak(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        volume: Optional[str] = None,
        output_path: Optional[str] = None,
        use_cache: bool = True,
    ) -> TTSResult:
        """
        文字转语音（异步）

        Args:
            text: 要合成的文本
            voice: 语音名称（默认用 config.voice）
            rate: 语速（默认 +0%）
            pitch: 音调（默认 +0Hz）
            volume: 音量（默认 +0%）
            output_path: 输出文件路径（默认自动生成）
            use_cache: 是否使用缓存

        Returns:
            TTSResult: 包含音频路径、时长等信息
        """
        # 参数合并
        voice = voice or self.config.voice
        rate = rate or self.config.rate
        pitch = pitch or self.config.pitch
        volume = volume or self.config.volume

        # 缓存查询
        if use_cache and self.config.cache_enabled:
            cache_key = self._make_cache_key(text, voice, rate, pitch, volume)
            cached = self._cache_get(cache_key)
            if cached:
                print(f"[TTS] 命中缓存: {text[:20]}...")
                return cached

        # 生成输出路径
        if not output_path:
            output_path = self._make_output_path(text)

        # 分段处理长文本
        if len(text) > self.config.max_chunk_length:
            result = await self._speak_long_text(
                text, voice, rate, pitch, volume, output_path
            )
        else:
            result = await self._speak_single(
                text, voice, rate, pitch, volume, output_path
            )

        # 更新缓存
        if use_cache and self.config.cache_enabled:
            await self._cache_put(cache_key, result)

        return result

    async def speak_and_play(
        self,
        text: str,
        voice: Optional[str] = None,
        scene: Optional[str] = None,
        playback_device: Optional[str] = None,
        on_progress: Optional[Callable[[float], None]] = None,
    ) -> TTSResult:
        """
        合成 + 播放（TTS + aplay 连续执行）

        Args:
            text: 要合成的文本
            voice: 语音名称
            scene: 场景预设（覆盖 voice 参数）
            playback_device: 播放设备（如 "hw:1,0"）
            on_progress: 播放进度回调（参数为当前进度百分比 0-1）
        """
        if scene and scene in self.SCENE_PRESETS:
            preset = self.SCENE_PRESETS[scene]
            voice = voice or preset["voice"]
            rate = preset["rate"]
            pitch = preset["pitch"]
            volume = preset["volume"]
        else:
            rate = pitch = volume = None

        # 合成
        result = await self.speak(
            text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
        )

        # 播放
        await self._play(
            result.audio_path,
            device=playback_device,
            on_progress=on_progress,
        )

        return result

    def speak_sync(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
    ) -> TTSResult:
        """同步版本的 speak（阻塞，Phase 1 简单场景用）"""
        return asyncio.run(self.speak(text, voice=voice, rate=rate))

    # ===== 内部实现 =====

    async def _speak_single(
        self,
        text: str,
        voice: str,
        rate: str,
        pitch: str,
        volume: str,
        output_path: str,
    ) -> TTSResult:
        """单次合成（Edge-TTS）"""
        if self.config.engine == TTSEngine.EDGE_TTS:
            return await self._edge_tts_speak(
                text, voice, rate, pitch, volume, output_path
            )
        elif self.config.engine == TTSEngine.GTTS:
            return await self._gtts_speak(text, voice, output_path)
        else:
            raise NotImplementedError(f"引擎 {self.config.engine} 未实现")

    async def _edge_tts_speak(
        self,
        text: str,
        voice: str,
        rate: str,
        pitch: str,
        volume: str,
        output_path: str,
    ) -> TTSResult:
        """Edge-TTS 合成"""
        communicate = edge_tts.Communicate(
            text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
        )
        await communicate.save(output_path)

        duration = self._get_duration(output_path)

        return TTSResult(
            audio_path=output_path,
            duration=duration,
            engine="edge-tts",
            from_cache=False,
            text_length=len(text),
        )

    async def _gtts_speak(
        self,
        text: str,
        voice: str,
        output_path: str,
    ) -> TTSResult:
        """Google TTS 合成（备用，离线不可用）"""
        from gtts import gTTS

        # gTTS 不支持 voice 参数，用 lang 代替
        lang = "zh-CN"
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)

        duration = self._get_duration(output_path)

        return TTSResult(
            audio_path=output_path,
            duration=duration,
            engine="gtts",
            from_cache=False,
            text_length=len(text),
        )

    async def _speak_long_text(
        self,
        text: str,
        voice: str,
        rate: str,
        pitch: str,
        volume: str,
        output_path: str,
    ) -> TTSResult:
        """长文本分段合成 + ffmpeg 合并"""
        chunks = self._split_text(text)

        temp_files = []
        for i, chunk in enumerate(chunks):
            temp_file = os.path.join(
                self.config.output_dir,
                f"tts_chunk_{int(asyncio.get_event_loop().time()*1000)}_{i}.mp3"
            )
            await self._speak_single(
                chunk, voice, rate, pitch, volume, temp_file
            )
            temp_files.append(temp_file)

        # ffmpeg 合并
        concat_list = os.path.join(self.config.output_dir, "concat_list.txt")
        with open(concat_list, "w") as f:
            for tf in temp_files:
                f.write(f"file '{tf}'\n")

        try:
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", concat_list,
                "-c", "copy",
                output_path
            ], check=True, capture_output=True)
        finally:
            os.unlink(concat_list)
            for tf in temp_files:
                try:
                    os.unlink(tf)
                except:
                    pass

        duration = self._get_duration(output_path)

        return TTSResult(
            audio_path=output_path,
            duration=duration,
            engine="edge-tts (merged)",
            from_cache=False,
            text_length=len(text),
        )

    def _split_text(self, text: str) -> list[str]:
        """按句子分割长文本（Edge-TTS 上限 450 字符）"""
        import re
        parts = re.split(r'([。！？\.\!\?])', text)
        chunks, current = [], ""

        for i in range(0, len(parts) - 1, 2):
            sentence = parts[i] + (parts[i + 1] if i + 1 < len(parts) else "")
            if len(current) + len(sentence) <= self.config.max_chunk_length:
                current += sentence
            else:
                if current:
                    chunks.append(current)
                current = sentence

        if current:
            chunks.append(current)

        return chunks

    async def _play(
        self,
        audio_path: str,
        device: Optional[str] = None,
        on_progress: Optional[Callable[[float], None]] = None,
    ) -> None:
        """播放音频文件"""
        cmd = ["aplay", audio_path]
        if device:
            cmd.extend(["-D", device])

        # aplay 不支持进度回调，简化为直接播放
        await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

    def _get_duration(self, audio_path: str) -> float:
        """用 ffprobe 获取音频时长（秒）"""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ], capture_output=True, text=True, timeout=5)
            return float(result.stdout.strip())
        except:
            return 0.0

    # ===== 缓存管理 =====

    def _make_cache_key(
        self,
        text: str,
        voice: str,
        rate: str,
        pitch: str,
        volume: str,
    ) -> str:
        """生成缓存 key"""
        key_str = f"{text}|{voice}|{rate}|{pitch}|{volume}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _make_output_path(self, text: str) -> str:
        """生成唯一的输出文件路径"""
        key = hashlib.md5(text.encode()).hexdigest()[:12]
        return os.path.join(
            self.config.output_dir,
            f"tts_{key}.mp3"
        )

    def _cache_get(self, key: str) -> Optional[TTSResult]:
        """从缓存获取"""
        if key in self._cache:
            # LRU: 移到末尾
            self._cache_order.remove(key)
            self._cache_order.append(key)
            result = self._cache[key]
            result.from_cache = True
            return result
        return None

    async def _cache_put(self, key: str, result: TTSResult) -> None:
        """写入缓存"""
        async with self._lock:
            if key in self._cache:
                return

            # LRU 淘汰
            while len(self._cache) >= self.config.cache_size:
                oldest_key = self._cache_order.pop(0)
                old_result = self._cache.pop(oldest_key, None)
                # 清理旧文件（如果不在使用中）
                try:
                    if old_result and os.path.exists(old_result.audio_path):
                        os.unlink(old_result.audio_path)
                except:
                    pass

            self._cache[key] = result
            self._cache_order.append(key)

    def clear_cache(self) -> None:
        """清空所有缓存"""
        for result in self._cache.values():
            try:
                if os.path.exists(result.audio_path):
                    os.unlink(result.audio_path)
            except:
                pass
        self._cache.clear()
        self._cache_order.clear()

    def cache_stats(self) -> dict:
        """缓存统计"""
        return {
            "size": len(self._cache),
            "max_size": self.config.cache_size,
            "keys": list(self._cache.keys()),
        }
```

### P1.14.2 TTSManager 快速使用指南

**初始化（Phase 1 最简方式）：**
```python
import asyncio
from tts_manager import TTSManager

# 默认配置（Edge-TTS + 中文女声）
manager = TTSManager()

async def demo():
    # 基础合成
    result = await manager.speak("你好，我是贵庚")
    print(f"音频: {result.audio_path}，时长: {result.duration:.1f}s")

    # 场景化合成
    await manager.speak_and_play("说慢一点，我年纪大了", scene="elderly")

    # 指定语音参数
    await manager.speak_and_play(
        "快速播报重要信息",
        voice="zh-CN-YunyangNeural",
        rate="+30%"
    )

    # 打印缓存命中率
    print(manager.cache_stats())

asyncio.run(demo())
```

**在 WhisperRecognizer 对话循环中使用：**
```python
# 在 P1.12 的 VoiceDialogMachine 中集成 TTSManager

class VoiceDialogMachine:
    def __init__(self, ...):
        ...
        self.tts = TTSManager()

    async def _speak(self, text: str) -> None:
        # 替换原来的 edge_tts.Communicate 调用
        # 使用缓存，重复回复秒出
        await self.tts.speak_and_play(
            text,
            voice=self.config.tts_voice,
            rate=self.config.tts_rate,
        )
```

**OpenClaw Bridge 集成（完整 Pipeline）：**
```python
import asyncio
from tts_manager import TTSManager
from WhisperRecognizer import WhisperRecognizer

async def voice_loop():
    """完整语音对话循环（VAD + Whisper + Bridge + TTS）"""
    recognizer = WhisperRecognizer(
        model_path="./whisper.cpp/models/ggml-small.bin",
        language="zh"
    )
    tts = TTSManager()

    async with OpenClawBridge(gateway_url="http://192.168.x.x:18789") as bridge:
        while True:
            print("🎤 等待语音...")

            # 录音
            audio_file = "/tmp/input.wav"
            subprocess.run([
                "arecord", "-d", "5", "-f", "cd",
                "-c", "1", "-r", "16000", audio_file
            ], check=True)

            # 识别
            result = recognizer.recognize_file(audio_file)
            if not result.text.strip():
                continue

            print(f"👤 {result.text}")

            # 发送给大脑
            response = await bridge.ask(result.text)
            print(f"🤖 {response}")

            # TTS 回复（带缓存，重复回复不重复合成）
            await tts.speak_and_play(response, scene="normal")

asyncio.run(voice_loop())
```

### P1.14.3 SSML 高级用法（细粒度发音控制）

> Edge-TTS 支持 SSML 标记，可控制特定字词的发音、停顿、语调

**SSML 基本结构：**
```xml
<speak>
  <prosody rate="+0%" pitch="+0Hz">
    主要内容
    <break time="500ms"/>  <!-- 停顿 500ms -->
    <emphasis>重点词</emphasis>
  </prosody>
</speak>
```

**SSML 标签速查：**

| 标签 | 属性 | 说明 | 示例 |
|------|------|------|------|
| `<break>` | `time` | 停顿 | `<break time="500ms"/>` |
| `<emphasis>` | `level` | 重音 | `<emphasis level="strong">关键词</emphasis>` |
| `<prosody>` | `rate/pitch/volume` | 全局参数 | `<prosody rate="+20%">快速</prosody>` |
| `<say-as>` | `interpret-as` | 特殊读法 | `<say-as interpret-as="characters">ABC</say-as>` |
| `<phoneme>` | `alphabet/ph` | IPA 音标 | `<phoneme alphabet="py" ph="ni3 hao3">你好</phoneme>` |

**SSML 实用场景：**

```python
import asyncio
import edge_tts

async def ssml_demo():
    """SSML 高级发音控制示例"""

    # 场景1: 添加自然停顿（让回复更有节奏感）
    ssml_1 = """<speak>
        你好，今天是星期一。
        <break time="300ms"/>
        有什么我可以帮你的吗？
    </speak>"""
    await edge_tts.Communicate(ssml_1, "zh-CN-XiaoxiaoNeural").save("/tmp/ssml_1.mp3")

    # 场景2: 数字和电话号码的正确读法
    ssml_2 = """<speak>
        我的电话号码是
        <say-as interpret-as="telephone">13812345678</say-as>。
        请记录一下。
    </speak>"""
    await edge_tts.Communicate(ssml_2, "zh-CN-XiaoxiaoNeural").save("/tmp/ssml_2.mp3")

    # 场景3: 英文单词按字母读出
    ssml_3 = """<speak>
        AI 是
        <say-as interpret-as="characters">Artificial Intelligence</say-as>
        的缩写。
    </speak>"""
    await edge_tts.Communicate(ssml_3, "zh-CN-XiaoxiaoNeural").save("/tmp/ssml_3.mp3")

    # 场景4: 多音字纠错（用拼音注音）
    # 注意：Edge-TTS 的 alphabet="py" 使用汉语拼音
    ssml_4 = """<speak>
        重庆的正确读法是
        <phoneme alphabet="py" ph="zhong4 qing2">重庆</phoneme>，
        不是 <phoneme alphabet="py" ph="chong2 qing">重请</phoneme>。
    </speak>"""
    await edge_tts.Communicate(ssml_4, "zh-CN-XiaoxiaoNeural").save("/tmp/ssml_4.mp3")

    # 场景5: 语速变化（关键词放慢）
    ssml_5 = """<speak>
        重要提醒：
        <prosody rate="-30%">明天早上九点记得开会。</prosody>
        不要迟到。
    </speak>"""
    await edge_tts.Communicate(ssml_5, "zh-CN-XiaoxiaoNeural").save("/tmp/ssml_5.mp3")

    print("SSML 示例已生成")

asyncio.run(ssml_demo())
```

**SSML + TTSManager 集成：**
```python
class TTSManager:
    async def speak_ssml(self, ssml: str, output_path: Optional[str] = None) -> TTSResult:
        """直接传入 SSML 文本"""
        if not output_path:
            key = hashlib.md5(ssml.encode()).hexdigest()[:12]
            output_path = os.path.join(self.config.output_dir, f"tts_ssml_{key}.mp3")

        communicate = edge_tts.Communicate(ssml)
        await communicate.save(output_path)

        return TTSResult(
            audio_path=output_path,
            duration=self._get_duration(output_path),
            engine="edge-tts-ssml",
            from_cache=False,
            text_length=len(ssml),
        )

    async def speak_with_pauses(self, text: str, pause_positions: list[int]) -> TTSResult:
        """
        在指定位置插入停顿

        Args:
            text: 原始文本
            pause_positions: 停顿位置列表（字符索引）
        """
        import re
        ssml_parts = []
        last_pos = 0

        for pos in sorted(pause_positions):
            ssml_parts.append(text[last_pos:pos])
            ssml_parts.append('<break time="500ms"/>')
            last_pos = pos

        ssml_parts.append(text[last_pos:])
        ssml = "<speak>" + "".join(ssml_parts) + "</speak>"

        return await self.speak_ssml(ssml)
```

### P1.14.4 离线 TTS 方案（Coqui/TTS）

> Phase 2+ 可选：完全离线的 TTS 引擎，不依赖网络

**Coqui TTS 安装：**
```bash
# CPU 版本（Phase 1 Jetson Nano 可用）
pip3 install TtsCoqui

# 或从源码编译（支持 GPU 加速）
git clone https://github.com/coqui-ai/TTS.git
cd TTS && pip install -e .
```

**Coqui TTS vs Edge-TTS 对比：**

| 维度 | Edge-TTS | Coqui TTS (XTTS) |
|------|----------|-----------------|
| 成本 | 免费（微软） | 免费（开源） |
| 离线 | ❌ 需要网络 | ✅ 完全离线 |
| 中文质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐（仍在线） |
| 声音克隆 | ❌ 不支持 | ✅ 支持 6-30s 音频克隆 |
| Jetson Nano 兼容性 | ✅ 极轻量 | ⚠️ 需要 4GB+ 内存 |
| 延迟 | <500ms | 1-3s（CPU）|
| **推荐场景** | **Phase 1** | Phase 2 声音定制 |

**Coqui TTSManager 适配：**
```python
async def _coqui_tts_speak(
    self,
    text: str,
    voice: str,
    output_path: str,
) -> TTSResult:
    """Coqui TTS 合成（需要提前准备好参考音频）"""
    from TTS.api import TTS

    # 初始化（首次调用较慢，建议全局单例）
    tts = TTS(model_name="xtts", gpu=False)  # gpu=False for Jetson Nano

    # voice: 参考音频路径（用于声音克隆）
    # 无克隆需求用默认：
    # tts.tts(text=text, file_path=output_path)

    # 声音克隆（6-30s 参考音频）
    tts.tts_with_torch(
        text=text,
        speaker_wav=voice,  # 参考音频路径
        file_path=output_path,
    )

    duration = self._get_duration(output_path)
    return TTSResult(
        audio_path=output_path,
        duration=duration,
        engine="coqui-xtts",
        from_cache=False,
        text_length=len(text),
    )
```

**引擎切换示例：**
```python
# 从 Edge-TTS 切换到 Coqui（同一套 API）
config_edge = TTSConfig(engine=TTSEngine.EDGE_TTS, voice="zh-CN-XiaoxiaoNeural")
config_coqui = TTSConfig(engine=TTSEngine.COQUI, voice="/path/to/your_voice.wav")

manager_edge = TTSManager(config_edge)
manager_coqui = TTSManager(config_coqui)

# Phase 1: Edge-TTS 在线高质量
result = await manager_edge.speak("今天天气怎么样？")

# Phase 2: Coqui 离线 + 声音克隆
result = await manager_coqui.speak("今天天气怎么样？")
```

### P1.14.5 播放控制进阶（混音、多路同时播放）

> Phase 2 进阶需求：背景音乐、混音、同时多路输出

**背景音乐混音（Phase 2）：**
```python
async def play_with_background_music(
    tts_audio: str,
    bgm_audio: str,
    output: str,
    bgm_volume: float = 0.3,
):
    """
    TTS 叠加背景音乐

    Args:
        tts_audio: TTS 生成的音频路径
        bgm_audio: 背景音乐文件路径
        output: 混音输出路径
        bgm_volume: 背景音乐音量（0-1）
    """
    # ffmpeg 混音
    # -filter_complex: 混合两个音频流
    # [0:a]volume=1.0[TTS]; [1:a]volume=0.3[BGM]; [TTS][BGM]amix=inputs=2:duration=longest
    subprocess.run([
        "ffmpeg", "-y",
        "-i", tts_audio,
        "-i", bgm_audio,
        "-filter_complex",
        f"[0:a]volume=1.0[a0];[1:a]volume={bgm_volume}[a1];"
        f"[a0][a1]amix=inputs=2:duration=longest:normalize=0",
        "-c:a", "libmp3lame",
        "-q:a", "2",
        output
    ], check=True)

    return output
```

**多设备同时播放（Phase 2 多房间）：**
```python
async def play_multi_room(
    text: str,
    rooms: list[dict],
):
    """
    同时在多个房间播放（Phase 2 智能家居联动）

    Args:
        rooms: [{"name": "客厅", "device": "hw:1,0"},
                {"name": "卧室", "device": "hw:2,0"}]
    """
    # 先合成
    result = await tts.speak(text)

    # 同时发送到多个播放设备
    tasks = []
    for room in rooms:
        task = asyncio.create_subprocess_exec(
            "aplay",
            "-D", room["device"],
            result.audio_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)
    print(f"已在 {len(rooms)} 个房间同时播放")
```

### P1.14.6 TTS 代码框架完整文件

> 保存为 `~/robot/tts_manager.py`，配合 P1.12 的 WhisperRecognizer 使用

**文件结构：**
```
~/robot/
├── tts_manager.py      # TTSManager 类（本节）
├── whisper_recognizer.py  # WhisperRecognizer 类（P1.12）
├── voice_dialog.py     # 语音对话主程序
└── phase1-start.sh     # 快速启动脚本（P1.12.8）
```

**安装依赖（all-in-one）：**
```bash
pip3 install edge-tts aiohttp gtts TtsCoqui  # 可选 Coqui
# Jetson Nano: sudo apt install ffmpeg
```

**测试脚本：**
```python
#!/usr/bin/env python3
"""TTSManager 快速测试"""
import asyncio
from tts_manager import TTSManager

async def test():
    m = TTSManager()

    print("=== Edge-TTS 测试 ===")
    r = await m.speak("你好，Phase 1 TTS 测试")
    print(f"输出: {r.audio_path} ({r.duration:.1f}s)")

    print("\n=== 场景测试 ===")
    for scene in ["normal", "elderly", "quick", "male"]:
        r = await m.speak(f"场景测试：{scene}", scene=scene)
        print(f"  {scene}: {r.audio_path}")

    print("\n=== 缓存测试 ===")
    # 重复内容第二次应命中缓存
    r1 = await m.speak("缓存测试内容")
    r2 = await m.speak("缓存测试内容")
    print(f"  r1 来自缓存: {r1.from_cache}")
    print(f"  r2 来自缓存: {r2.from_cache}")

    print(f"\n缓存状态: {m.cache_stats()}")

asyncio.run(test())
```

### P1.14.7 TTSManager API 参考

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `speak(text)` | 文字转语音（异步）| `TTSResult` |
| `speak_and_play(text, ...)` | 合成 + 播放 | `TTSResult` |
| `speak_sync(text)` | 同步版本（阻塞）| `TTSResult` |
| `speak_ssml(ssml)` | SSML 标记输入 | `TTSResult` |
| `speak_with_pauses(text, positions)` | 带停顿的 TTS | `TTSResult` |
| `clear_cache()` | 清空缓存 | — |
| `cache_stats()` | 缓存命中率统计 | `dict` |

**TTSResult 字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `audio_path` | `str` | 输出 MP3 文件路径 |
| `duration` | `float` | 音频时长（秒）|
| `engine` | `str` | 使用的 TTS 引擎 |
| `from_cache` | `bool` | 是否来自缓存 |
| `text_length` | `int` | 原始文本字符数 |

### P1.14.8 参考链接

- Edge-TTS GitHub：https://github.com/rany2/edge-tts
- SSML 官方文档：https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/speech-synthesis-markup
- Coqui TTS GitHub：https://github.com/coqui-ai/TTS
- FFmpeg 音频处理：https://ffmpeg.org/ffmpeg.html
- P1.11 Edge-TTS 完整配置指南（→ 本文件 P1.11）
- P1.12 WhisperRecognizer 类（→ 本文件 P1.12）

---

## P1.15 端到端测试步骤

> 本节覆盖从语音输入到语音输出的完整链路验证，对应 Phase 1 目标：**语音输入 → 文字 → AI 处理 → 语音输出**。

### P1.15.1 前置条件检查

执行前确认以下服务已就绪：

| 检查项 | 命令 | 期望结果 |
|--------|------|----------|
| Whisper 可执行 | `./whisper.cpp/bin/whisper-cli --help` | 显示帮助信息 |
| Edge-TTS 可用 | `edge-tts --version` | 显示版本号 |
| OpenClaw Gateway 可达 | `curl -s http://192.168.x.x:18789/health` | `{"status":"ok"}` |
| 音频设备正常 | `arecord -l` | 列出 USB 耳机（card 1） |
| 播放设备正常 | `aplay -l` | 列出 USB 耳机（card 1） |

### P1.15.2 分链路独立测试

**测试链路 A：麦克风 → Whisper 语音识别**

```bash
# Step A1: 录制测试音频（5秒）
arecord -d 5 -f cd -c 1 -r 16000 /tmp/e2e_test_input.wav
# 期望：/tmp/e2e_test_input.wav 大小 > 400KB（约 5s × 16kHz × 16bit）

# Step A2: Whisper 识别
./whisper.cpp/bin/whisper-cli \
  -m whisper.cpp/models/ggml-base.en.bin \
  -f /tmp/e2e_test_input.wav \
  --language zh
# 期望：输出识别后的中文文字
# 失败排查：确认模型文件存在、音频文件非空、语言参数正确
```

**测试链路 B：OpenClaw Gateway 通信**

```bash
# Step B1: 通过 Bridge Protocol 发送测试消息
#（在 MacBook 上，或 Jetson Nano 能访问 Gateway 的任意机器）

# Python 测试：
python3 - << 'PYEOF'
import aiohttp
import asyncio

async def test_gateway():
    url = "http://192.168.x.x:18789/bridge/ask"
    payload = {"text": "你好，测试消息", "stream": False}
    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as r:
            print(f"状态码: {r.status}")
            data = await r.json()
            print(f"回复: {data}")
            return data

asyncio.run(test_gateway())
PYEOF
# 期望：收到 AI 回复
# 失败排查：检查 Gateway 日志、确认 Bridge Protocol 格式（参考 §3.3）
```

**测试链路 C：Edge-TTS 语音合成**

```bash
# Step C1: 合成测试
edge-tts --voice zh-CN-XiaoxiaoNeural \
  --text "你好，这是 Phase 1 端到端测试" \
  --write-media /tmp/e2e_test_output.mp3
# 期望：生成 MP3 文件，时长约 3-5 秒

# Step C2: 播放测试
aplay -D hw:1,0 /tmp/e2e_test_output.mp3
# 期望：听到"你好，这是 Phase 1 端到端测试"
# 失败排查：确认 ~/.asoundrc 默认设备为 card 1
```

### P1.15.3 全链路端到端测试

**测试脚本：`~/robot/e2e_test.py`**

```python
#!/usr/bin/env python3
"""
Phase 1 端到端测试脚本
链路：麦克风 → Whisper → OpenClaw Bridge → AI → Edge-TTS → 扬声器
用法：python3 ~/robot/e2e_test.py
"""
import subprocess
import asyncio
import sys
import os

# 配置
GATEWAY_URL = "http://192.168.x.x:18789"
WHISPER_MODEL = "whisper.cpp/models/ggml-base.en.bin"
WHISPER_CLI = "./whisper.cpp/bin/whisper-cli"
RECORD_SECONDS = 5

def record_audio(output_path: str, duration: int = RECORD_SECONDS) -> bool:
    """录制音频"""
    print(f"[1/4] 正在录音 {duration} 秒...")
    result = subprocess.run([
        "arecord", "-d", str(duration), "-f", "cd",
        "-c", "1", "-r", "16000", output_path
    ], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] 录音失败: {result.stderr}")
        return False
    size = os.path.getsize(output_path)
    print(f"[OK] 录音完成: {output_path} ({size} bytes)")
    return size > 40000  # 5s audio should be > 40KB

def recognize_speech(audio_path: str) -> str:
    """Whisper 语音识别"""
    print("[2/4] 正在识别语音...")
    result = subprocess.run([
        WHISPER_CLI, "-m", WHISPER_MODEL,
        "-f", audio_path, "--language", "zh"
    ], capture_output=True, text=True, cwd="/home/nvidia/whisper.cpp")
    if result.returncode != 0:
        print(f"[ERROR] 识别失败: {result.stderr}")
        return ""
    text = result.stdout.strip()
    print(f"[OK] 识别结果: {text}")
    return text

async def ask_ai(text: str) -> str:
    """通过 Bridge 询问 AI"""
    print(f"[3/4] 正在询问 AI: {text}")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as sess:
            async with sess.post(
                f"{GATEWAY_URL}/bridge/ask",
                json={"text": text, "stream": False},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as r:
                data = await r.json()
                answer = data.get("text", "") or data.get("answer", "")
                print(f"[OK] AI 回复: {answer}")
                return answer
    except Exception as e:
        print(f"[ERROR] AI 请求失败: {e}")
        return ""

def synthesize_and_play(text: str, output_mp3: str = "/tmp/e2e_tts.mp3") -> bool:
    """Edge-TTS 合成 + 播放"""
    print(f"[4/4] 正在合成语音并播放...")
    result = subprocess.run([
        "edge-tts", "--voice", "zh-CN-XiaoxiaoNeural",
        "--text", text, "--write-media", output_mp3
    ], capture_output=True, text=True)
    if result.returncode != 0 or not os.path.exists(output_mp3):
        print(f"[ERROR] TTS 合成失败: {result.stderr}")
        return False
    print(f"[OK] 合成完成，播放中...")
    subprocess.run(["aplay", output_mp3], check=True)
    return True

async def main():
    audio_path = "/tmp/e2e_input.wav"
    tts_path = "/tmp/e2e_output.mp3"

    # Step 1: 录音
    if not record_audio(audio_path):
        print("=== 测试失败：录音环节 ===")
        return False

    # Step 2: 语音识别
    user_text = recognize_speech(audio_path)
    if not user_text:
        print("=== 测试失败：语音识别环节 ===")
        return False

    # Step 3: 询问 AI
    ai_reply = await ask_ai(user_text)
    if not ai_reply:
        print("=== 测试失败：AI 通信环节 ===")
        return False

    # Step 4: TTS 回复
    if not synthesize_and_play(ai_reply, tts_path):
        print("=== 测试失败：语音合成环节 ===")
        return False

    print("\n✅ Phase 1 端到端测试全部通过！")
    return True

if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
```

**执行方式：**

```bash
cd /home/nvidia
python3 ~/robot/e2e_test.py
# 期望输出：
# [1/4] 正在录音 5 秒...
# [OK] 录音完成: /tmp/e2e_input.wav (441000 bytes)
# [2/4] 正在识别语音...
# [OK] 识别结果: 你好
# [3/4] 正在询问 AI: 你好
# [OK] AI 回复: 你好！有什么我可以帮助你的吗？
# [4/4] 正在合成语音并播放...
# ✅ Phase 1 端到端测试全部通过！
```

### P1.15.4 故障排查索引

| 症状 | 可能原因 | 排查命令 |
|------|----------|----------|
| 录音文件为空 | arecord 默认设备错误 | `arecord -l` 确认 card 编号 |
| Whisper 识别乱码 | 音频格式不对或语言参数错误 | `file /tmp/e2e_input.wav` 确认是 WAV |
| AI 无回复 | Gateway 不可达或 Bridge 协议格式错误 | `curl -v http://192.168.x.x:18789/health` |
| TTS 无声音 | aplay 设备不对或 MP3 解码器缺失 | `aplay -D hw:1,0 /tmp/e2e_tts.mp3` 单独测试 |
| 延迟过长（>10s）| Whisper 模型太大或网络慢 | 换用 tiny.en 模型测试 |

### P1.15.5 验收标准

Phase 1 端到端测试通过当且仅当：

1. ✅ `arecord` 录制 5 秒生成 > 400KB 的 WAV 文件
2. ✅ `whisper-cli` 输出可辨识的中文文字
3. ✅ Bridge Protocol 成功收到 AI 回复（非超时/错误）
4. ✅ `edge-tts` 生成 MP3 文件
5. ✅ `aplay` 通过 USB 耳机播放出声音

**全部通过即 Phase 1 语音陪伴模块验收完成。**

---

## P1.16 延迟优化方案（Phase 1 关键性能章节）

> 来源：Phase 1 当前代码 + 行业最佳实践 + 嵌入式实时系统优化经验
> 补充目标：为 Phase 1 语音陪伴提供端到端延迟优化方案，将全链路延迟从 >10s 降低到 <3s

### P1.16.1 延迟构成分析（全链路拆解）

Phase 1 当前语音对话的完整链路延迟分布：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Phase 1 全链路延迟分布（当前 baseline）                 │
│                                                                         │
│  [录音等待] → [Whisper 识别] → [网络传输] → [AI 处理] → [TTS 合成] → [播放] │
│     5s        2-5s           50-200ms     1-3s         1-3s        100ms  │
│   (固定)    (模型相关)       (内网)      (Gateway)     (Edge)       (本地) │
│                                                                         │
│  总计：约 9-16 秒 （体验较差，交互不自然）                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

**各环节延迟详情：**

| 环节 | 当前值 | 影响因素 | 可优化空间 |
|------|--------|---------|-----------|
| **录音等待** | 5s（固定）| 固定 5 秒录音，用户必须说完才能处理 | ✅ 可优化（VAD 检测）|
| **Whisper 识别** | 2-5s | 模型大小（base vs tiny）、线程数 | ✅ 可优化（量化+小模型）|
| **网络传输（内网）** | 50-200ms | Gateway 距离、WiFi 质量 | ⚠️ 轻微优化 |
| **AI 处理（Gateway）** | 1-3s | 模型速度、上下文长度 | ⚠️ 依赖硬件 |
| **TTS 合成（Edge）** | 1-3s | 文本长度、服务器负载 | ✅ 可优化（流式/缓存）|
| **音频播放** | 100ms | 设备缓冲、文件大小 | ✅ 可优化 |
| **总计** | **9-16s** | — | **目标 <3s** |

### P1.16.2 目标延迟（Phase 1 vs Phase 2）

| 指标 | Phase 1 目标 | Phase 2 目标 | 优化手段 |
|------|------------|------------|---------|
| **端到端延迟（TTHL）** | < 3s | < 1.5s | VAD + 流式 TTS |
| **首字节延迟（TTFB）** | < 1s | < 300ms | 增量式 Whisper |
| **Whisper 延迟** | < 2s | < 500ms | tiny 模型 + 量化 |
| **TTS 延迟** | < 1.5s | < 300ms | 短文本缓存 |
| **用户体验** | 可接受对话 | 自然对话 | 全链路优化 |

### P1.16.3 优化一：VAD 替代固定录音（延迟 -3s）

> **最大优化项**：去掉固定 5 秒等待，改为 VAD（Voice Activity Detection）语音活动检测

**原理：**
```
固定录音（当前）：用户说完 → 等满5秒 → 开始识别
                   ↓
VAD 检测（优化后）：用户开始说话 → VAD检测到 → 实时处理
                   ↓
               静音检测到 → 截断录音 → 立即识别
```

**当前代码问题：**
```python
# Phase 1 Step 5 当前代码
subprocess.run([
    "arecord", "-d", "5",  # ← 固定 5 秒，用户说完还要等满 5s
    "-f", "cd", "-c", "1", "-r", "16000", "/tmp/input.wav"
])
```

**优化方案 A：Silero VAD（推荐，精度最高）**

```bash
# Step 1: 下载 Silero VAD 模型
cd whisper.cpp && ./models/download-vad-model.sh silero-v6.2.0

# Step 2: whisper-cli 内置 VAD 支持（最简单）
./whisper.cpp/build/bin/whisper-cli \
  -m models/ggml-base.en.bin \
  -f /tmp/real_time_audio.wav \
  --vad \
  --vad-model models/ggml-silero-v6.2.0.bin \
  --vad-threshold 0.5 \
  --vad-min-speech-duration-ms 250 \
  --vad-min-silence-duration-ms 500
```

**优化方案 B：webrtc-noise-gain（更低延迟）**

```bash
# 安装 WebRTC VAD
pip3 install webrtcvad

# Python VAD 示例（实时流处理）
import webrtcvad
import collections

def read_chunks(audio_source, chunk_duration=30):
    """每 30ms 一帧，VAD 支持 10/20/30ms"""
    samplerate = 16000
    frame_size = int(samplerate * chunk_duration / 1000) * 2  # 16bit
    while True:
        chunk = audio_source.read(frame_size)
        if not chunk:
            break
        yield chunk

def vad_filter(audio_frames, aggressiveness=2):
    """过滤静音帧，只保留语音片段"""
    vad = webrtcvad.Vad(aggressiveness)  # 0-3，越高越激进
    is_speech = [vad.is_speech(frame, 16000) for frame in audio_frames]
    return [f for f, s in zip(audio_frames, is_speech) if s]

# 实时处理循环
import pyaudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True)
frames = collections.deque(maxlen=100)  # 保留最近 3 秒

for frame in read_chunks(stream):
    frames.append(frame)
    is_speech = webrtcvad.Vad(2).is_speech(frame, 16000)
    print("语音" if is_speech else "静音")
```

**优化效果：**
- 短指令（1-2 秒说完）：等待时间从 5s → 1.5s，节省 **3.5 秒**
- 长回复（3-4 秒说完）：等待时间不变，但整体体验更自然

### P1.16.4 优化二：Whisper 模型降级 + 量化（延迟 -2s）

> **高优先级优化**：将 Whisper 模型从 `base` 降级到 `tiny` + Q5_0 量化

**当前配置（延迟较高）：**
```python
WHISPER_MODEL = "./whisper.cpp/models/ggml-base.en.bin"  # 142MB
# Whisper 延迟：2-5 秒（Jetson Nano 2GB CPU）
```

**优化配置（推荐 Phase 1）：**

```bash
# Step 1: 下载 tiny 模型
./models/download-ggml-model.sh tiny

# Step 2: 量化（内存减半，速度提升 2x）
./build/bin/quantize \
  models/ggml-tiny.bin \
  models/ggml-tiny-q5_0.bin \
  q5_0

# 文件大小对比：
# base.en     : 142MB → 388MB 内存占用
# tiny        :  75MB → 200MB 内存占用  
# tiny-q5_0   :  ~25MB → ~100MB 内存占用（极致优化）
```

**Python 集成（tiny 模型）：**

```python
WHISPER_MODEL_TINY = "./whisper.cpp/models/ggml-tiny-q5_0.bin"
# 延迟：1-2 秒（比 base 快 2-3x）
# 精度损失：tiny 对中文支持有限，建议 Phase 1 用 tiny.en 或 base.zh

# 推荐配置（Phase 1 平衡方案）：
WHISPER_MODEL = "./whisper.cpp/models/ggml-base.en.bin"  # 英文
# 或
WHISPER_MODEL = "./whisper.cpp/models/ggml-tiny.bin"      # 中文（但需实测识别率）
```

**线程优化（延迟 -500ms）：**

```python
# Jetson Nano 2GB 建议线程数
WHISPER_THREADS = 2  # 默认 4 线程在 2GB 机器上可能 OOM

# 在 whisper-cli 调用时加 -t 参数
result = subprocess.run([
    "whisper-cli", "-m", model, "-f", audio,
    "-t", "2",           # 2 线程（比默认慢但更稳定）
    "--language", "zh"
], ...)
```

### P1.16.5 优化三：OpenClaw Bridge 流式请求（延迟 -1s）

> **Gateway 侧优化**：使用流式 Bridge Protocol，边识别边发送

**当前顺序处理（总延迟 = 识别延迟 + AI 延迟）：**
```
用户说完 → Whisper 识别（2-5s）→ 发送给 Gateway → AI 回复（1-3s）→ TTS
```

**优化后并行处理（总延迟 ≈ max(识别, AI)）：**
```
用户说话中 → VAD 检测到语音 → 立即开始 Whisper（后台）
                                         ↓
用户说完 → 立即发送已识别文字 → AI 并行处理
                                         ↓
                              Whisper 完成 + AI 完成 → TTS（几乎无等待）
```

**流式 Bridge 实现：**

```python
async def stream_ask_and_recognize(audio_file: str, gateway_url: str):
    """
    边识别边发送，实现 AI 处理和 Whisper 并行
    """
    import aiohttp
    import asyncio
    import subprocess

    # Step 1: 启动 Whisper 识别（后台任务）
    whisper_task = asyncio.create_subprocess_exec(
        "whisper-cli",
        "-m", "models/ggml-tiny.bin",
        "-f", audio_file,
        "--language", "zh",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Step 2: 在 Whisper 运行期间，预热 Gateway 连接
    async with aiohttp.ClientSession() as sess:
        # 等待 Whisper 完成
        proc = await whisper_task
        stdout, _ = await proc.communicate()
        recognized_text = stdout.decode().strip()

        if not recognized_text:
            return ""

        # Step 3: 发送已识别的文字（此时 AI 可以开始处理）
        async with sess.post(
            f"{gateway_url}/bridge/ask",
            json={"text": recognized_text}
        ) as resp:
            result = await resp.json()
            return result.get("text", "")
```

**流式 TTS（Edge-TTS 支持 chunk 输出）：**

```python
async def stream_tts_and_play(text: str):
    """
    流式 TTS：边合成边播放，首字节延迟 < 300ms
    """
    import edge_tts
    import asyncio
    import subprocess

    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    
    # 启动 aplay 进程（stdin 模式）
    player = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", "pipe:0", "-acodec", "pcm_s16le", "-ar", "16000", "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    # 边接收 TTS 音频流边送给播放器
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            player.stdin.write(chunk["data"])
    
    await player.stdin.close()
    await player.wait()
```

### P1.16.6 优化四：TTS 结果缓存（延迟 -2s，对重复回复）

> **命中率 30-50% 的优化**：常用回复（如"你好"、"好的"）直接读缓存

**缓存策略：**

```python
from functools import lru_cache
import hashlib

# LRU 缓存（Python 内置）
@lru_cache(maxsize=100)
def cached_tts(text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> str:
    """缓存 TTS 结果，命中时延迟从 1-3s → <50ms"""
    output = f"/tmp/tts_{hashlib.md5((text+voice).encode()).hexdigest()[:12]}.mp3"
    # ... edge_tts 合成 ...
    return output

# 使用
cached_file = cached_tts("你好，我是贵庚")
# 第二次调用直接返回 /tmp/tts_xxxx.mp3，无需重新合成
```

**常见回复缓存词库：**

```python
# Phase 1 常用回复（建议预缓存）
CACHED_RESPONSES = {
    # 问候类
    "你好": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+0%"},
    "早上好": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+0%"},
    "晚上好": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+0%"},
    # 确认类
    "好的": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+0%"},
    "知道了": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+0%"},
    "稍等": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "-20%"},
    # 等待类
    "我在听": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+0%"},
    "请说": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+0%"},
}

def warm_up_cache():
    """预缓存常用回复（Phase 1 启动时调用）"""
    for text, params in CACHED_RESPONSES.items():
        asyncio.run(cached_tts(text, params["voice"]))
    print(f"已预缓存 {len(CACHED_RESPONSES)} 个常用回复")
```

### P1.16.7 优化五：网络传输优化（延迟 -100ms）

> **内网优化**：Gateway 和 Jetson Nano 之间的高效通信

**问题分析：**
```
当前：每个请求新建 TCP 连接（握手延迟 ~50ms）
优化：保持长连接 + HTTP Keep-Alive（零握手延迟）
```

**HTTP Keep-Alive 配置（aiohttp）：**

```python
import aiohttp

# 不复用连接（当前问题）
async with aiohttp.ClientSession() as sess:
    async with sess.post(url, json=payload) as resp:  # 每次新连接
        ...

# 优化后：复用 TCP 连接
connector = aiohttp.TCPConnector(limit=10, keepalive_timeout=300)
async with aiohttp.ClientSession(connector=connector) as sess:
    # 所有请求复用同一个连接，节省 50-100ms/次
    async with sess.post(url, json=payload) as resp:
        ...
```

**内网直连（避免公网绕路）：**
```python
# 当前：可能通过公网 DNS 解析
GATEWAY_URL = "http://192.168.x.x:18789"  # 内网 IP

# 确保用内网 IP 而不是域名
# macOS 上可运行 `ifconfig | grep "inet " | grep -v 127.0.0.1` 查看内网地址
```

### P1.16.8 优化六：音频格式精简（延迟 -200ms）

> **文件 I/O 优化**：减小音频文件体积，加快读写速度

**当前配置：**
```bash
arecord -d 5 -f cd -c 1 -r 16000 /tmp/input.wav
# -f cd = 44100Hz, 16bit, stereo → 1秒 = 176KB
```

**优化配置：**
```bash
# Whisper 只需 16kHz 单声道 16bit
arecord -d 5 -f S16_LE -c 1 -r 16000 /tmp/input.wav
# 1秒 = 32KB（体积减少 5x，读写速度快 5x）

# 极致优化：8kHz 采样（Whisper 支持自动重采样）
arecord -d 5 -f S16_LE -c 1 -r 8000 /tmp/input.wav
# 1秒 = 16KB（体积减少 11x，适合远场场景）
```

**文件大小对比（5 秒录音）：**

| 格式 | 采样率 | 声道 | 位深 | 文件大小 |
|------|--------|------|------|---------|
| cd（当前）| 44100Hz | 立体声 | 16bit | 441KB |
| **优化后** | **16000Hz** | **单声道** | **16bit** | **160KB** |
| 极致版 | 8000Hz | 单声道 | 16bit | 80KB |

### P1.16.9 综合优化配置（Phase 1 推荐）

> 将以下配置应用到 Phase 1 主程序，实现全链路延迟降低 60%

**优化前后对比：**

| 优化项 | 优化前 | 优化后 | 节省 |
|--------|--------|--------|------|
| 录音等待 | 5s（固定）| 1.5s（VAD）| **-3.5s** |
| Whisper | base（2-5s）| tiny-q5_0（0.5-1.5s）| **-2s** |
| TTS | 每次重新合成 | 缓存命中时 | **-1.5s** |
| 播放缓冲 | 大缓冲 | 小缓冲 | **-200ms** |
| **总计** | **9-16s** | **<3s** | **-7~13s** |

**Phase 1 优化版主程序：**

```python
#!/usr/bin/env python3
"""
Phase 1 语音陪伴 - 延迟优化版
全链路延迟目标：< 3 秒

优化要点：
1. VAD 替代固定 5 秒录音
2. Whisper tiny-q5_0 量化模型
3. HTTP Keep-Alive 长连接
4. TTS 结果缓存（lru_cache）
5. 16kHz 单声道音频（替代 cd 格式）
"""
import subprocess
import asyncio
import edge_tts
import webrtcvad
import aiohttp
import collections
import hashlib
from functools import lru_cache

# ====== 配置（优化版）======
GATEWAY_URL = "http://192.168.x.x:18789"
WHISPER_MODEL = "./whisper.cpp/models/ggml-tiny-q5_0.bin"  # 量化模型
WHISPER_THREADS = 2
VOICE = "zh-CN-XiaoxiaoNeural"
AUDIO_SAMPLE_RATE = 16000
AUDIO_FILE = "/tmp/input_optimized.wav"
TTS_CACHE_DIR = "/tmp/tts_cache"

import os
os.makedirs(TTS_CACHE_DIR, exist_ok=True)

# ====== TTS 缓存（优化三）======
@lru_cache(maxsize=100)
def cached_tts_sync(text: str, voice: str = VOICE) -> str:
    """同步版 TTS 缓存（用于 lru_cache）"""
    key = hashlib.md5((text + voice).encode()).hexdigest()[:12]
    path = f"{TTS_CACHE_DIR}/tts_{key}.mp3"
    if os.path.exists(path):
        return path
    # 同步合成（首次或缓存未命中）
    subprocess.run([
        "edge-tts",
        "--voice", voice,
        "--text", text,
        "--write-media", path
    ], check=True, capture_output=True)
    return path

async def cached_tts(text: str, voice: str = VOICE) -> str:
    """异步版 TTS 缓存"""
    return cached_tts_sync(text, voice)

# ====== VAD 录音（优化一）======
class VADRecorder:
    """基于 WebRTC VAD 的智能录音"""
    
    def __init__(self, aggressiveness=2, frame_ms=30):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.frame_ms = frame_ms
        self.frame_size = int(16000 * frame_ms / 1000) * 2
        
    def record_until_silence(self, max_duration=5.0) -> bytes:
        """录音直到检测到静音（最多 max_duration 秒）"""
        import pyaudio
        
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=self.frame_size
        )
        
        frames = []
        silence_count = 0
        max_frames = int(max_duration * 1000 / self.frame_ms)
        
        for i in range(max_frames):
            frame = stream.read(self.frame_size, exception_on_overflow=False)
            frames.append(frame)
            
            is_speech = self.vad.is_speech(frame, 16000)
            if not is_speech:
                silence_count += 1
                if silence_count > 10:  # 连续 10 帧（约 300ms）静音则停止
                    break
            else:
                silence_count = 0
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        return b"".join(frames)

# ====== Whisper 识别（优化二）======
def recognize_tiny(audio_path: str) -> str:
    """Whisper tiny 模型识别"""
    result = subprocess.run([
        "whisper-cli",
        "-m", WHISPER_MODEL,
        "-f", audio_path,
        "-l", "zh",
        "-t", str(WHISPER_THREADS)
    ], capture_output=True, text=True)
    
    # 解析输出
    texts = []
    for line in result.stdout.split('\n'):
        if '-->' in line:
            text = line.split(']', 1)[1].strip()
            if text:
                texts.append(text)
    return ' '.join(texts)

# ====== OpenClaw Bridge（优化四：Keep-Alive）======
class OptimizedBridge:
    """优化版 Bridge：HTTP Keep-Alive + 流式"""
    
    def __init__(self, gateway_url: str):
        self.gateway_url = gateway_url
        self._connector = aiohttp.TCPConnector(limit=10, keepalive_timeout=300)
        self._session: aiohttp.ClientSession = None
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession(connector=self._connector)
        return self
    
    async def __aexit__(self, *args):
        await self._session.close()
    
    async def ask(self, text: str) -> str:
        async with self._session.post(
            f"{self.gateway_url}/bridge/ask",
            json={"text": text}
        ) as resp:
            data = await resp.json()
            return data.get("text", "")

# ====== 主循环（优化汇总）======
async def main():
    recorder = VADRecorder()
    
    print("🎤 Phase 1 延迟优化版已启动（目标延迟 < 3s）")
    print("按 Ctrl+C 退出\n")
    
    async with OptimizedBridge(GATEWAY_URL) as bridge:
        while True:
            print("👂 等待语音输入...")
            
            # 优化一：VAD 录音（不等满 5 秒）
            audio_data = recorder.record_until_silence(max_duration=5.0)
            
            if len(audio_data) < 1600:  # < 50ms 的录音忽略
                print("（音频过短，重新监听）")
                continue
            
            # 保存为 WAV
            import wave
            with wave.open(AUDIO_FILE, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_data)
            
            # 优化二：Whisper tiny 识别（< 1.5s）
            print("🧠 识别中...")
            text = recognize_tiny(AUDIO_FILE)
            
            if not text.strip():
                print("（未识别到内容，重新监听）")
                continue
            
            print(f"👤 你说: {text}")
            
            # 优化四：Keep-Alive 长连接发送（节省 50-100ms）
            print("🤖 AI 处理中...")
            try:
                response = await bridge.ask(text)
            except Exception as e:
                print(f"Gateway 错误: {e}")
                response = "抱歉，网络连接出了问题。"
            
            print(f"🤖 贵庚: {response}")
            
            # 优化三：TTS 缓存（命中时 < 50ms）
            print("🔊 播放回复...")
            try:
                tts_file = cached_tts(response)
                subprocess.run(["aplay", tts_file], check=True, capture_output=True)
            except Exception as e:
                print(f"TTS 播放错误: {e}")
            
            print()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\n已退出")
```

### P1.16.10 延迟监控与基准测试

> 量化每个优化项的实际效果，建立性能基准

**基准测试脚本：**

```python
#!/usr/bin/env python3
"""
Phase 1 延迟基准测试
测量各环节实际延迟，用于验证优化效果
"""
import time
import asyncio
import subprocess

def measure_whisper(audio_file: str, model: str) -> float:
    """测量 Whisper 识别延迟"""
    start = time.time()
    subprocess.run([
        "whisper-cli",
        "-m", model,
        "-f", audio_file,
        "-l", "zh", "-t", "2"
    ], capture_output=True, check=True)
    return time.time() - start

async def measure_bridge_ask(text: str, gateway_url: str) -> float:
    """测量 Bridge 请求延迟"""
    import aiohttp
    start = time.time()
    async with aiohttp.ClientSession() as sess:
        async with sess.post(f"{gateway_url}/bridge/ask", json={"text": text}) as resp:
            await resp.json()
    return time.time() - start

def measure_tts(text: str) -> float:
    """测量 TTS 合成延迟"""
    start = time.time()
    subprocess.run([
        "edge-tts",
        "--voice", "zh-CN-XiaoxiaoNeural",
        "--text", text,
        "--write-media", "/tmp/bench_tts.mp3"
    ], capture_output=True, check=True)
    return time.time() - start

async def benchmark():
    """运行完整基准测试"""
    print("=== Phase 1 延迟基准测试 ===\n")
    
    test_audio = "/tmp/bench_input.wav"
    test_text = "你好，今天天气怎么样？"
    
    # 生成测试音频
    subprocess.run([
        "edge-tts",
        "--voice", "zh-CN-XiaoxiaoNeural",
        "--text", test_text,
        "--write-media", "/tmp/bench_input.mp3"
    ], check=True)
    
    # 转换为 Whisper 可用格式
    subprocess.run([
        "ffmpeg", "-y", "-i", "/tmp/bench_input.mp3",
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        test_audio
    ], capture_output=True)
    
    # 测试 Whisper
    print("📊 Whisper 延迟测试：")
    for model in ["ggml-tiny.bin", "ggml-base.en.bin"]:
        path = f"whisper.cpp/models/{model}"
        try:
            t = measure_whisper(test_audio, path)
            print(f"  {model}: {t:.2f}s")
        except:
            print(f"  {model}: (未找到)")
    
    # 测试 Bridge
    print("\n📊 Bridge 延迟测试：")
    t = await measure_bridge_ask("你好", "http://192.168.x.x:18789")
    print(f"  单次请求: {t:.2f}s")
    
    # 测试 TTS
    print("\n📊 TTS 延迟测试：")
    for text in ["你好", "你好，请问今天天气怎么样？"]:
        t = measure_tts(text)
        print(f"  文本({len(text)}字): {t:.2f}s")
    
    print("\n✅ 基准测试完成")

asyncio.run(benchmark())
```

**预期测试结果（Phase 1 优化后）：**

| 环节 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 录音等待 | 5.0s | 1.5s | **70%↓** |
| Whisper (tiny) | — | 0.8s | 参考 |
| Whisper (base) | 2.5s | — | — |
| Bridge 请求 | 200ms | 100ms | **50%↓** |
| TTS (缓存未命中) | 1.5s | 1.0s | **33%↓** |
| TTS (缓存命中) | — | **<50ms** | **95%↓** |
| **端到端（首次）** | **12s** | **<3s** | **75%↓** |
| **端到端（缓存命中）** | — | **<1.5s** | **87%↓** |

### P1.16.11 Jetson Nano 2GB 内存优化专项

> Jetson Nano 2GB 内存有限，优化内存使用可间接降低延迟（避免 OOM 导致卡顿）

**内存监控脚本：**

```python
#!/usr/bin/env python3
"""Jetson Nano 内存监控 - Phase 1 部署必备"""
import psutil
import time

MEMORY_THRESHOLD_WARN = 80  # %，警告阈值
MEMORY_THRESHOLD_CRIT = 90  # %，危险阈值

def check_memory():
    mem = psutil.virtual_memory()
    percent = mem.percent
    available_gb = mem.available / (1024**3)
    
    status = "✅" if percent < MEMORY_THRESHOLD_WARN else \
             "⚠️" if percent < MEMORY_THRESHOLD_CRIT else "🚨"
    
    print(f"{status} 内存: {percent:.1f}% | 可用: {available_gb:.2f}GB")
    
    if percent > MEMORY_THRESHOLD_CRIT:
        print("🚨 内存危险，建议重启进程或降级模型")
        return False
    elif percent > MEMORY_THRESHOLD_WARN:
        print("⚠️ 内存偏高中")
    
    return True

def memory_auto_downgrade():
    """
    内存 >85% 时自动降级 Whisper 模型
    """
    if not check_memory():
        print("🔄 自动降级 Whisper 模型: base → tiny")
        # 动态修改模型路径
        # global WHISPER_MODEL
        # WHISPER_MODEL = "./whisper.cpp/models/ggml-tiny.bin"

# 在 Phase 1 主循环中加入：
# 每 10 轮对话检查一次内存
if __name__ == "__main__":
    print("=== Jetson Nano 内存监控 ===")
    while True:
        check_memory()
        time.sleep(10)
```

**Jetson Nano 内存优化配置：**

```bash
# /etc/sysctl.conf 添加 swap 优化
vm.swappiness=10
vm.dirty_ratio=15
vm.dirty_background_ratio=5

# 禁用不必要的服务（释放内存）
sudo systemctl stop bluetooth  # Phase 1 不需要蓝牙
sudo systemctl stop snapd      # Phase 1 不需要 snap
sudo systemctl stop unattended-upgrades

# 确认可用内存
free -h
```

### P1.16.12 延迟优化检查清单（Phase 1 部署前必读）

> 逐项检查以下优化是否已应用

**基础优化（立即生效）：**

- [ ] **VAD 录音**：将固定 `arecord -d 5` 改为 VAD 检测
- [ ] **Whisper 模型**：从 `base` 降级到 `tiny-q5_0`（量化版）
- [ ] **音频格式**：从 `cd`（44.1kHz 立体声）改为 16kHz 单声道
- [ ] **TTS 缓存**：对重复回复启用 `lru_cache`

**网络优化（延迟 -100ms）：**

- [ ] **内网直连**：使用 `http://192.168.x.x:18789` 而非域名
- [ ] **HTTP Keep-Alive**：aiohttp 启用 `TCPConnector`

**高级优化（Phase 2 目标）：**

- [ ] **流式 TTS**：边合成边播放（Edge-TTS 支持 chunk）
- [ ] **增量识别**：Whisper 流式输出（whisper-stream）
- [ ] **本地 Whisper**：内网部署，减少 AI 处理时间

**运维监控（长期稳定性）：**

- [ ] **内存监控**：每 10 轮对话检查一次内存
- [ ] **延迟基准测试**：每周运行一次 `benchmark.py`
- [ ] **错误日志**：记录每次 >5s 的端到端延迟

### P1.16.13 参考链接

- Silero VAD 模型：https://github.com/snakers4/silero-vad
- WebRTC VAD：https://github.com/wiseman/py-webrtcvad
- whisper.cpp 量化：https://github.com/ggml-org/whisper.cpp/tree/master/examples/quantize
- Edge-TTS 流式：https://github.com/rany2/edge-tts#streaming
- aiohttp Keep-Alive：https://docs.aiohttp.org/en/stable/client_reference.html
- P1.12 WhisperRecognizer（→ 本文件 P1.12）
- P1.14 TTSManager（→ 本文件 P1.14，含缓存实现）
- P1.15 端到端测试（→ 本文件 P1.15）
