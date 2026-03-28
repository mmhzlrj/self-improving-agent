# ESP32-Cam 固件烧录百科全书级 SOP

> **设备**：ESP32-Cam（OV2640 摄像头模块）
> **目标**：烧录固件并输出 RTSP 视频流
> **最后更新**：2026-03-26
> **维护者**：AI Assistant（基于 OpenClaw）

---

## 📋 目录

1. [任务概述](#1-任务概述)
2. [硬件准备](#2-硬件准备)
3. [软件准备](#3-软件准备)
4. [完整烧录流程](#4-完整烧录流程)
5. [可能遇到的问题与解决方案](#5-可能遇到的问题与解决方案)
6. [降频 240MHz 详细操作](#6-降频-240mhz-详细操作)
7. [静态 IP 设置](#7-静态-ip-设置)
8. [验证方法](#8-验证方法)
9. [RTSP 流观看命令](#9-rtsp-流观看命令)
10. [快速参考卡片](#10-快速参考卡片)

---

## 1. 任务概述

### 1.1 烧录什么固件

> **✅ 推荐固件：ESP32-CAM-RTSP**（开源，支持 RTSP 流推送，符合 0-1 项目需求）

这是目前最流行的开源 RTSP 固件方案，专为 ESP32-Cam 开发板设计，开箱即用支持 RTSP 流推送：

| 固件名称 | 仓库地址 | 特点 |
|---------|---------|------|
| **ESP32-CAM-RTSP** | `github.com/geeksville/esp32-camera` | ✅ **推荐首选**，RTSP流推送，成熟稳定 |
| ESP32-CAM-RTSP-Server | `github.com/rpicopter/ESP32-Camera-WebServer` | Web界面+RTSP双输出 |
| ESPHome | `esphome.io` | 配置化，支持RTSP |

**为什么选 ESP32-CAM-RTSP**：
- ✅ 直接输出 RTSP 视频流，推送到服务器/平台
- ✅ 开源免费，可自行编译定制
- ✅ 成熟稳定，社区活跃
- ✅ 支持 WiFi 连接、静态 IP 配置
- ✅ 可通过编译参数降频（240MHz → 160MHz）

**备选固件**：
- `rpicopter/ESP32-Camera-WebServer`（带 Web 界面，适合调试）
- `ESPHome`（配置化，适合有 HomeAssistant 场景）

### 1.2 烧录后要达成什么状态

```
✅ ESP32-Cam 正常启动
✅ 摄像头初始化成功（OV2640）
✅ WiFi 连接成功（获取 IP）
✅ RTSP 服务运行在 8554 端口
✅ 可通过 RTSP URL 观看实时视频流
✅ 推荐分辨率：SVGA（800×600），帧率：10-15fps
✅ CPU 频率：240MHz（可在编译时降至 160MHz 减少发热）
```

---

## 2. 硬件准备

### 2.1 硬件清单

> **设备型号**：ESP32-Cam（标准双排针开发板，AI-Thinker 兼容，含 OV2640 摄像头）

| 物品 | 说明 | 必要程度 |
|-----|------|---------|
| ESP32-Cam 板（含OV2640） | 目标设备，标准双排针 | ✅ 已持有 |
| **烧录底座（母座）** | 配套底座，板子插进底座即可烧录 | ✅ 已持有 |
| ~~USB 转 TTL 串口模块~~ | ~~CP2102 / CH340 / FT232RL~~ | ❌ **不需要额外购买** |
| 5V/2A 电源适配器 | **供电必须稳定** | ✅ 必须 |
| 电容（可选） | 100µF + 100nF 并联滤波 | 推荐 |

> **📌 说明**：用户已有配套烧录底座，烧录时直接将 ESP32-Cam 板插入底座即可，无需额外购买 USB 转 TTL 模块。底座通常自带 CP2102 或 CH340 芯片，直接通过 USB 连接电脑即可烧录。

### 2.2 引脚定义（ESP32-Cam）

```
ESP32-Cam 引脚分布（从左到右，当 USB 接口朝上时）：

[GND] [IO0] [GPIO3(RX)] [GPIO1(TX)] [GPIO16]
[5V ] [3V3] [EN     ] [GPIO35  ] [GPIO34 ]
[GPIO36] [GPIO37] [GPIO38] [GPIO39] [GPIO32]
[GPIO33] [GPIO25] [GPIO26] [GPIO27] [GPIO14]
[GPIO13] [GPIO15] [GPIO12] [GPIO4] [GPIO2]
```

**重要引脚说明**：

| 引脚 | 功能 | 备注 |
|-----|------|------|
| `IO0` | 下载模式选择 | 烧录时必须接地（GND） |
| `EN` | 使能（复位） | 最好接 10kΩ 上拉电阻到 3V3 |
| `GPIO1/TX` | 串口发送 | 接 USB-TTL 的 RX |
| `GPIO3/RX` | 串口接收 | 接 USB-TTL 的 TX |
| `5V` | 电源输入 | **必须 5V/2A** |
| `GND` | 地 | 与 USB-TTL 共地 |
| `3V3` | 3.3V 电源 | **不要接！仅测量用** |

### 2.3 接线方式

> **✅ 推荐方式：使用配套烧录底座（已持有）**
>
> ESP32-Cam 板直接插入烧录底座的母座，底座通过 USB 线连接电脑即可。
> 底座已集成 USB 转 TTL 芯片（CP2102/CH340），自动完成所有接线。

#### 方式 A：烧录底座方式（✅ 推荐，已持有）

```
┌─────────────────────────────────────┐
│         ESP32-Cam 烧录底座            │
│   ┌─────────────────────────┐       │
│   │   [ESP32-Cam 母座]      │       │
│   │   板子插此处             │       │
│   └─────────────────────────┘       │
│                                     │
│   USB Type-A ──→ 连接电脑 USB        │
│   5V/2A 电源接口 ──→ 连接外部电源    │
│                                     │
│   ※ 底座已内置：                     │
│   ※ CP2102/CH340 USB转TTL          │
│   ※ IO0 自动接地（烧录模式）         │
│   ※ EN 自动上拉                      │
└─────────────────────────────────────┘

操作步骤：
1. 将 ESP32-Cam 板小心插入底座母座（对齐方向）
2. USB 线连接底座和电脑
3. （可选）5V/2A 电源连接到底座电源口
4. 电脑端识别到串口设备后开始烧录
```

#### 方式 B：标准杜邦线接线（无底座时使用）

```
USB-TTL          ESP32-Cam
---------         ----------
GND     ────────  GND（任意）
RX      ────────  GPIO1/TX（U0T）
TX      ────────  GPIO3/RX（U0R）
5V     ────────  5V（电源）

IO0     ────────  GND（烧录模式，必须！）
```

#### 方式 C：完整接线（含 EN 控制）

```
USB-TTL          ESP32-Cam
---------         ----------
GND     ────────  GND
RX      ────────  GPIO1/TX
TX      ────────  GPIO3/RX
5V     ────────  5V

GND     ────────  IO0（烧录模式）

（可选）3V3  ────  EN + 10kΩ 电阻 → 3V3（自动复位）
```

#### 方式 D：面包板接线（最稳定）

```
1. USB-TTL 5V → ESP32-Cam 5V
2. USB-TTL GND → ESP32-Cam GND
3. USB-TTL RX → ESP32-Cam GPIO1(TX)
4. USB-TTL TX → ESP32-Cam GPIO3(RX)
5. USB-TTL GND → ESP32-Cam IO0（烧录时临时接地）
6. 5V/2A电源单独给ESP32-Cam供电（强烈推荐！）

⚠️ 警告：USB-TTL 只负责数据通信，电源必须由独立电源或电脑USB（但供电弱）提供
```

### 2.4 供电要求（极其重要！）

```
⚠️ ESP32-Cam 供电必须满足以下条件：

1. 电压：5V（必须！3.3V 供电会导致不稳定）
2. 电流：至少 2A（峰值需求，WiFi+摄像头同时工作）
3. 电源纹波：越小越好（建议加 100µF + 100nF 电容滤波）

常见错误：
❌ 用 USB-TTL 的 5V 供电 → 电流不够，摄像头启动失败
❌ 用手机充电头 5V/0.5A → 电流不够，启动时掉电重启
❌ 用电脑USB直接供电（无独立电源）→ 可能不够，摄像头初始化失败

✅ 正确做法：
- 使用烧录底座时：底座有独立电源接口 → 连接 5V/2A 电源
- 使用杜邦线时：USB-TTL 仅连接 GND/TX/RX 三根线（不接 5V）
- 独立 5V/2A 电源（如树莓派电源、实验室电源）
- 共地用同一 GND
```

**使用烧录底座时的供电方案**：
```
┌────────────────────────────┐
│     ESP32-Cam 烧录底座       │
│                            │
│  [USB] ────→ 电脑（数据）    │
│                            │
│  [DC 5V/2A] ───→ 外部电源   │  ← 必须连接！
│                            │
└────────────────────────────┘

⚠️ 注意：烧录底座的 USB 接口通常只负责数据通信，
         电源需要通过底座的 DC 接口或 5V 引脚独立供电。
         如果底座有 USB 供电选项（跳线或开关），
         可以尝试电脑USB供电，但不稳定时仍需外部电源。
```

---

## 3. 软件准备

### 3.1 安装 esptool.py（核心烧录工具）

#### macOS
```bash
# 方法1：pip 安装
pip3 install esptool

# 方法2：Homebrew 安装
brew install esptool

# 方法3：使用 Arduino 内置版本
# Arduino IDE 安装目录的 tools/ 目录下有 esptool
```

#### Windows
```powershell
# 方法1：pip 安装
pip install esptool

# 方法2：下载预编译版
# https://github.com/espressif/esptool/releases
```

#### Linux
```bash
sudo apt install python3-pip
pip3 install esptool
```

#### 验证安装
```bash
esptool.py version
# 输出类似：
# esptool.py v4.7.0
```

### 3.2 USB 转 TTL 驱动

| 芯片 | 驱动下载 | macOS特殊要求 |
|-----|---------|--------------|
| CP2102 | `silabs.com/developers/usb-to-uart-bridge-vcp-drivers` | macOS 10.15+ 需要手动允许内核扩展 |
| CH340 | `wch.cn/downloads/WCH USBSerialDriver Mac zip` | 同上 |
| FT232RL | `ftdichip.com/drivers/ftdi-vcp-drivers` | 较稳定 |

**macOS 驱动安装后操作**：
```bash
# 允许内核扩展（系统偏好设置 → 安全性与隐私 → 通用）
# 或者用命令：
sudo kextload /Library/Extensions/SiUSBXp.kext   # CP2102
sudo kextload /Library/Extensions/wch.kext         # CH340

# 查看是否识别到设备
ls /dev/cu.*
# 正常输出类似：
# /dev/cu.SLAB_USBtoUART   # CP2102
# /dev/cu.wchusbserial*    # CH340
# /dev/cu.usbserial*       # FTDI
```

### 3.3 推荐固件及获取方式

#### 方案 A：ESPHome（强烈推荐，配置化，最简单）

**安装 ESPHome**：
```bash
pip3 install esphome
```

**创建配置文件 `esp32-cam.yaml`**：
```yaml
esphome:
  name: esp32-cam
  platform: ESP32
  board: esp32dev

wifi:
  ssid: "你的WiFi名称"
  password: "你的WiFi密码"
  manual_ip:
    static_ip: 192.168.1.100
    gateway: 192.168.1.1
    subnet: 255.255.255.0
    dns1: 192.168.1.1

# 启用 AP 备份网络（主WiFi连不上时）
ap:
  ssid: "ESP32-Cam Fallback Hotspot"
  password: "12345678"

# 摄像头配置
esp32_camera:
  external_clock: gpio0
  i2c_pins:
    sda: gpio26
    scl: gpio27
  data_pins: [gpio5, gpio18, gpio19, gpio21, gpio36, gpio39, gpio34, gpio35]
  vsync_pin: gpio25
  href_pin: gpio23
  pclk_pin: gpio22
  xclk_pin: gpio32

  resolution: svga  # 800x600，推荐！不要用 uxga
  jpeg_quality: 10
  frame_rate: 15

# RTSP 输出
rtsp_stream:
  - platform: output
    format: rtsp
    port: 8554
    authorization: false
```

**编译并烧录**：
```bash
# 编译固件
esphome compile esp32-cam.yaml

# 烧录固件（首次需要用 USB-TTL）
esphome upload esp32-cam.yaml --upload-port /dev/cu.SLAB_USBtoUART

# 后续可以通过 OTA 无线更新（配好WiFi后）
esphome upload esp32-cam.yaml
```

#### 方案 B：Arduino IDE + CameraWebServer（适合简单需求）

**安装 Arduino ESP32 开发板**：
1. Arduino IDE → 文件 → 首选项 → 附加开发板管理器网址：
```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```

2. 工具 → 开发板 → 开发板管理器 → 搜索 "ESP32" → 安装

**下载 CameraWebServer 示例**：
1. 文件 → 示例 → ESP32 → Camera → CameraWebServer
2. 选择你的摄像头型号（AI-Thinker ESP32-Cam）

**修改配置**：
```cpp
// 在 CameraWebServer.ino 中找到并修改以下内容：

// 1. WiFi 配置
const char* ssid = "你的WiFi名称";
const char* password = "你的WiFi密码";

// 2. 摄像头分辨率（改为 SVGA，不要用 UXGA！）
framesize_t FRAMESIZE_UXGA;  // 改为
framesize_t FRAMESIZE_SVGA;  // SVGA = 800x600

// 3. 降频（可选，在 setup() 中加入）
setCpuFrequencyMhz(240);  // 默认240MHz，可降到160
```

**Arduino IDE 烧录设置**：
```
工具 → 开发板：AI-Thinker ESP32-Cam
工具 → 分区方案：Huge APP (3MB No OTA/0MB SPIFFS)
工具 → 端口：/dev/cu.SLAB_USBtoUART
工具 → 上传速度：115200（稳定）或 921600（快速）

⚠️ 注意：上传前 IO0 必须接地！
```

#### 方案 C：PlatformIO（适合开发者）

**安装 PlatformIO**：
```bash
pip3 install platformio
```

**创建项目**：
```bash
mkdir -p ~/esp32-cam-project
cd ~/esp32-cam-project
platformio init -i
# 选择：Platform → Espressif 32，Board → ESP32 Dev Module，Framework → Arduino
```

**编写 platformio.ini**：
```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino

# 分区表 - 必须是 3MB APP 以上
board_build.partitions = default.csv
board_upload.flash_size = 4MB

# 降频到 240MHz（默认就是240，不需要特别设置）
build_flags =
    -DCORE_DEBUG_LEVEL=0
    -DBOARD_HAS_PSRAM
    -DESP32

monitor_speed = 115200
```

**安装摄像头库**：
```bash
cd ~/esp32-cam-project
platformio lib install 5698  # ArduCAM/ESP32 Camera Library
```

**烧录命令**：
```bash
# 编译
platformio run

# 上传（需要 USB-TTL，IO0 接地）
platformio run --target upload --upload-port /dev/cu.SLAB_USBtoUART
```

### 3.4 固件分区说明（重要！）

```
ESP32-Cam 通常有 4MB Flash，分区如下：

+------------------+-------------+-----------+
| Partition        | Size        | Address   |
+------------------+-------------+-----------+
| NVS              | 20KB        | 0x9000    |
| OTA              | 1MB         | 0x10000   |
| FileSystem       | 1.5MB       | 0x150000  |
| ESP32 Firmware   | 1.4MB       | 0x200000  |
+------------------+-------------+-----------+

⚠️ 如果固件太大装不下，选择分区方案：
- "No OTA (2MB APP / 2MB SPIFFS)" - 固件2MB，不需要OTA时
- "Huge APP (3MB No OTA)" - 固件3MB，CameraWebServer 推荐

Arduino IDE 烧录时选：工具 → 分区方案 → Huge APP (3MB No OTA/0MB SPIFFS)
```

---

## 4. 完整烧录流程

### 流程概览

```
[步骤A] 使用烧录底座（✅ 推荐方式）
    ↓
[步骤B] 安装驱动（如需要）
    ↓
[步骤C] 确认串口设备
    ↓
[步骤D] 获取/编译固件（ESP32-CAM-RTSP）
    ↓
[步骤E] 执行烧录
    ↓
[步骤F] 验证启动日志
    ↓
[步骤G] 连接 RTSP 流
```

---

### 步骤 A：使用烧录底座（✅ 推荐方式）

> **已持有配套烧录底座，按以下步骤操作**：

```
检查清单：
□ ESP32-Cam 板已正确插入烧录底座母座（对齐方向）
□ USB 线连接底座和电脑
□ 5V/2A 外部电源连接到底座电源口（如底座需要外供电）
□ 摄像头模块已插好（OV2640 软排线）

底座特点：
✅ 内置 USB 转 TTL（CP2102/CH340）
✅ IO0 自动接地（烧录模式）
✅ EN 自动上拉
✅ 无需手动接线
```

**底座连接示意**：
```
┌──────────────────────────────────────────────┐
│                                              │
│   [ESP32-Cam 开发板]                          │
│        ↓ 插入母座 ↓                           │
│   ┌──────────────────────┐                   │
│   │    烧录底座母座       │                   │
│   └──────────────────────┘                   │
│          │                │                  │
│    USB Type-A          DC 5V/2A              │
│    (数据)              (电源)                 │
│       │                   │                 │
│       ↓                   ↓                 │
│   ┌─────────────────────────────────────┐    │
│   │           电脑 USB                   │    │
│   │           外部电源                   │    │
│   └─────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

### 步骤 B：安装驱动（如需要）

**macOS 详细步骤**：
```bash
# 1. 如果底座使用 CP2102，下载并安装驱动
# https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers

# 2. 如果底座使用 CH340，下载驱动
# https://www.wch.cn/downloads/WCH USBSerialDriver Mac zip

# 3. 安装后允许内核扩展
# 系统偏好设置 → 安全性与隐私 → 通用
# 看到 "来自开发者的系统软件 'Silicon Labs' 被阻止" → 允许

# 4. 插上底座，查看设备
ls /dev/cu.*

# 正常输出：
# /dev/cu.SLAB_USBtoUART   # CP2102
# /dev/cu.wchusbserial*    # CH340
```

**Windows 详细步骤**：
```powershell
# 1. 安装驱动（底座通常会自动安装）
# 2. 打开设备管理器 → 端口(COM 和 LPT)
# 3. 看到 COM 端口号（如 COM3）
```

### 步骤 C：确认串口设备

```bash
# macOS/Linux 查看所有串口
ls -la /dev/cu.* /dev/tty.*

# 识别你的设备（通常显示芯片型号）
# CP2102 → /dev/cu.SLAB_USBtoUART
# CH340  → /dev/cu.wchusbserial1420

# 确认权限
ls -l /dev/cu.SLAB_USBtoUART
# 应该显示当前用户有读写权限

# 如果没有权限，添加用户组
sudo usermod -a -G dialout $USER
# 然后重新登录或执行：
newgrp dialout
```

### 步骤 D：获取固件（ESP32-CAM-RTSP）

> **✅ 推荐固件**：ESP32-CAM-RTSP
> 开源地址：`github.com/geeksville/esp32-camera`

#### 方式 1：下载预编译固件（最简单）

```bash
# 克隆 ESP32-CAM-RTSP 仓库
cd ~
git clone https://github.com/geeksville/esp32-camera.git
cd esp32-camera

# 查看可用的预编译固件
ls -la *.bin

# 或者直接下载 release 版本
# 访问：https://github.com/geeksville/esp32-camera/releases
```

#### 方式 2：使用 ESPHome 编译（推荐，可定制）

```bash
# 安装 ESPHome
pip3 install esphome

# 创建配置文件
mkdir -p ~/esp32-cam
cat > ~/esp32-cam/esp32-cam.yaml << 'EOF'
esphome:
  name: esp32-cam-rtsp
  platform: ESP32
  board: esp32dev

wifi:
  ssid: "你的WiFi名称"
  password: "你的WiFi密码"
  manual_ip:
    static_ip: 192.168.1.100
    gateway: 192.168.1.1
    subnet: 255.255.255.0
    dns1: 192.168.1.1

# 启用 AP 备份网络（主WiFi连不上时）
ap:
  ssid: "ESP32-Cam Fallback Hotspot"
  password: "12345678"

# 摄像头配置
esp32_camera:
  external_clock: gpio0
  i2c_pins:
    sda: gpio26
    scl: gpio27
  data_pins: [gpio5, gpio18, gpio19, gpio21, gpio36, gpio39, gpio34, gpio35]
  vsync_pin: gpio25
  href_pin: gpio23
  pclk_pin: gpio22
  xclk_pin: gpio32

  # ✅ 推荐配置（SVGA 降频，减少发热）
  resolution: svga  # 800x600，不要用 uxga
  jpeg_quality: 10
  frame_rate: 15

# RTSP 输出
rtsp_stream:
  - platform: output
    format: rtsp
    port: 8554
    authorization: false
EOF

# 编译固件
cd ~/esp32-cam
esphome compile esp32-cam.yaml
```

### 步骤 E：执行烧录

> **使用烧录底座时，操作超级简单**：
> 板子插底座 → 底座接电脑 → 执行命令

#### ESPHome 烧录（自动处理所有步骤）
```bash
cd ~/esp32-cam
esphome upload esp32-cam.yaml --upload-port /dev/cu.SLAB_USBtoUART
```

#### esptool.py 烧录（预编译固件）
```bash
# 确保 ESP32-Cam 板在底座中，底座已连接电脑

# 完整烧录命令
esptool.py \
  --chip esp32 \
  --port /dev/cu.SLAB_USBtoUART \
  --baud 921600 \
  --before default_reset \
  --after hard_reset \
  write_flash \
  --flash_mode dio \
  --flash_freq 40m \
  --flash_size 4MB \
  0x1000 esp32-camera/bootloader_dio_40m.bin \
  0x8000 esp32-camera/partitions.bin \
  0xe000 esp32-camera/boot_app0.bin \
  0x10000 esp32-camera/firmware.bin

# ⚠️ 如果烧录失败，降低波特率重试：
# --baud 115200
```

#### Arduino IDE 烧录

```
工具 → 开发板：AI-Thinker ESP32-Cam
工具 → 分区方案：Huge APP (3MB No OTA/0MB SPIFFS)
工具 → 端口：/dev/cu.SLAB_USBtoUART
工具 → 上传速度：115200

⚠️ 烧录前确保板子在底座中，IO0 已接地（底座自动处理）
```

### 步骤 F：验证启动日志

```bash
# 打开串口监视器
screen /dev/cu.SLAB_USBtoUART 115200
# 或者
python3 -m serial.tools.miniterm /dev/cu.SLAB_USBtoUART 115200

# 退出 screen：按 Ctrl+A，然后按 K，再按 Y
# 退出 miniterm：按 Ctrl+] 或 Ctrl+Shift+]
```

**正常启动日志应该包含**：
```
ets Jun  8 2016 00:22:57
rst:0x1 (POWERON_RESET),boot:0x13 (SPI_FAST_FLASH_BOOT)
...
I (xx) wifi: ip:192.168.1.100 mask:255.255.255.0 gw:192.168.1.1
I (xx) wifi: mode : sta (xx:xx:xx:xx:xx:xx)
I (xx) wifi: WiFi connected
I (xx) camera: Camera module started
RTSP URL: rtsp://192.168.1.100:8554/stream
```

**如果看到错误日志**：
```
E (xx) camera: Camera probe failed with error 0x105
# → 摄像头初始化失败，见"摄像头问题"章节

E (xx) wifi: wifi start failed
# → WiFi 连接失败，检查SSID/密码

brownout detector was triggered
# → 供电不足，见"供电问题"章节
```

### 步骤 G：连接 RTSP 流

```bash
# VLC 打开网络流
# 菜单 → 媒体 → 打开网络串流 → 输入：
rtsp://192.168.1.100:8554/stream

# 或用命令行
vlc rtsp://192.168.1.100:8554/stream

# ffplay（推荐，低延迟）
ffplay -fflags nobuffer -flags low_delay rtsp://192.168.1.100:8554/stream

# ffmpeg 录制测试
ffmpeg -i rtsp://192.168.1.100:8554/stream -t 10 -c copy test.mp4
```

---

## 5. 可能遇到的问题与解决方案

### 问题总表

| # | 问题类别 | 具体症状 |
|---|---------|---------|
| 1 | 烧录失败 | 驱动问题：设备管理器找不到端口 |
| 2 | 烧录失败 | 端口问题：Permission denied |
| 3 | 烧录失败 | 接线问题：连接失败、一直等待 |
| 4 | 烧录失败 | 分区问题：固件太大装不下 |
| 5 | 固件崩溃 | 内存不足（PSRAM）导致重启 |
| 6 | 供电问题 | 花屏（彩色条纹/雪花） |
| 7 | 供电问题 | 无限重启（brownout detector） |
| 8 | 供电问题 | 摄像头亮但无输出 |
| 9 | 摄像头问题 | 黑屏（摄像头初始化失败） |
| 10 | 摄像头问题 | 偏色（色彩异常/绿色画面） |
| 11 | 摄像头问题 | 模糊/对焦问题 |
| 12 | IP问题 | 获取不到IP |
| 13 | IP问题 | IP冲突 |
| 14 | RTSP问题 | 无法连接RTSP流 |
| 15 | RTSP问题 | 延迟高（>2秒） |
| 16 | RTSP问题 | 连接后卡顿/掉帧 |
| 17 | 发热问题 | CPU温度过高 |
| 18 | WiFi问题 | WiFi断开后无法重连 |

---

### 问题 1：驱动问题 - 设备管理器找不到端口

**症状**：
- macOS: `/dev/cu.*` 中没有设备
- Windows: 设备管理器中没有 COM 端口
- USB-TTL 指示灯亮，但系统不识别

**排查步骤**：

**Step A: 检查 USB 线**
```bash
# 确保使用数据传输线（不是纯充电线）
# 充电线只有电源，没有数据线！
# 测试：换一个 USB 线试试
```

**Step B: 检查驱动是否安装（macOS）**
```bash
# 查看系统扩展状态
kextstat | grep -i silabs    # CP2102
kextstat | grep -i ch34      # CH340

# 如果没有输出，说明驱动未加载
# 尝试手动加载
sudo kextload /Library/Extensions/SiUSBXp.kext     # CP2102
sudo kextload /Library/Extensions/ch34x.kext       # CH340
```

**Step C: 允许内核扩展（macOS 10.15+）**
```
系统偏好设置 → 安全性与隐私 → 通用
→ 看到 "来自开发者的系统软件 'Silicon Labs' 被阻止" → 允许
→ 如果没有，重启按住 Cmd+R 进入恢复模式 → 终端执行：
spctl --master-disable
```

**Step D: Windows 手动安装驱动**
```powershell
# 设备管理器 → 找到带黄色感叹号的 USB 设备
# 右键 → 更新驱动程序 → 浏览我的计算机...
# 选择驱动程序位置（下载的驱动文件夹）
```

**Step E: 尝试不同的 USB 端口**
```bash
# 直接插在电脑 USB 口上，不要用 USB Hub
ls /dev/cu.*
```

---

### 问题 2：端口问题 - Permission denied

**症状**：
```
Failed to open serial port /dev/cu.SLAB_USBtoUART
Permission denied
```

**解决方案**：

**Step A: 当前用户添加到 dialout 组**
```bash
# macOS
sudo usermod -a -G dialout $USER
# 需要重新登录或重启生效

# Linux
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/cu.SLAB_USBtoUART  # 临时方案

# 临时解决（立即生效）
sudo chmod 666 /dev/cu.SLAB_USBtoUART
```

**Step B: 使用 sudo 运行烧录工具**
```bash
# 不推荐，但可以临时用
sudo esptool.py ...
sudo platformio run --target upload
```

**Step C: 创建设备规则（Linux）**
```bash
# 创建 udev 规则
sudo bash -c 'cat > /etc/udev/rules.d/50-usb-serial.rules << 'EOF'
SUBSYSTEM=="tty",ATTRS{idVendor}=="10c4",MODE="0666",GROUP="dialout"
SUBSYSTEM=="tty",ATTRS{idVendor}=="1a86",MODE="0666",GROUP="dialout"
EOF'

# 重载 udev 规则
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

### 问题 3：接线问题 - 烧录连接失败

**症状**：
```
A fatal error occurred: Failed to connect to Espressif device: UART serial /timeout
Waiting for download...
```

**排查步骤**：

**Step A: 确认 TX/RX 交叉连接**
```
正确连接：
USB-TTL TX  →  ESP32-Cam GPIO3/RX（不是 GPIO1！）
USB-TTL RX  →  ESP32-Cam GPIO1/TX（不是 GPIO3！）

⚠️ 注意：是交叉连接（TX→RX，RX→TX），不是直连！
```

**Step B: 确认 IO0 接地**
```bash
# 用万用表测量 IO0 和 GND 之间的电阻
# 应该是 0Ω（短接状态）
```

**Step C: 按正确顺序操作**
```
标准操作流程（必须按顺序）：
1. IO0 接地
2. 按住 EN 键
3. 松开 EN 键（此时才进入下载模式）
4. 立即执行烧录命令（超时约 3 秒）

或者更简单的流程：
1. IO0 接地
2. 断电
3. 上电（自动进入下载模式）
4. 立即执行烧录命令
```

**Step D: 检查波特率**
```bash
# 如果连接不稳定，降低波特率
esptool.py --chip esp32 --port /dev/cu.SLAB_USBtoUART --baud 115200 write_flash ...

# 不要用太高的波特率，特别是线较长时
# 115200 是最稳定的，921600 需要短线和良好接地
```

**Step E: 检查供电**
```
⚠️ 供电不足会导致下载模式进入失败！

症状：串口有输出但立即停止，或显示奇怪的字符

解决：使用独立 5V/2A 电源为 ESP32-Cam 供电
USB-TTL 只接 GND/TX/RX 三根线，不接 5V
```

---

### 问题 4：分区问题 - 固件太大装不下

**症状**：
```
A fatal error occurred: Image length is larger than partition size
Sketch size xxx is larger than 1310720
```

**解决方案**：

**Step A: 选择更大的分区方案（Arduino IDE）**
```
工具 → 分区方案 → Huge APP (3MB No OTA/0MB SPIFFS)
```

**Step B: 优化固件大小**
```cpp
// 在 CameraWebServer.ino 中：
// 1. 禁用不必要的功能
// #define CONFIG_LED_ACTIVITY  // 注释掉 LED

// 2. 降低摄像头分辨率
framesize_t FRAMESIZE_SVGA;  // 800x600，足够用

// 3. 减少日志输出（在 setup() 中）
Serial.setDebugOutput(false);
```

**Step C: 清理并重新编译**
```bash
# Arduino IDE
#  sketch → 清理
#  sketch → 验证/编译

# PlatformIO
platformio run --target clean
platformio run
```

---

### 问题 5：内存不足（PSRAM）导致重启

**症状**：
```
Guru Meditation Error: Core  1 panic'ed (Cache disabled but cached memory region accessed)
rst:0x8 tg1=0x6000, [残存的内存错误日志]
```

**解决方案**：

**Step A: 确认板子有 PSRAM**
```
ESP32-Cam 有两个版本：
- AI-Thinker ESP32-Cam（有 PSRAM，8MB）
- ESP32-Cam-MB（没有 PSRAM）

没有 PSRAM 的版本无法运行 CameraWebServer！

检查方法：
1. 看板子上有没有 PSRAM 芯片（方形IC，8个引脚）
2. 启动日志会显示：
   "PSRAM IC: not found"  → 没有 PSRAM
   "PSRAM size: 8388608 bytes" → 有 8MB PSRAM
```

**Step B: 在 Arduino IDE 中启用 PSRAM**
```cpp
// 在 sketch 最开头添加：
#include <esp_heap_caps.h>

void setup() {
  // 启用 PSRAM（如果板子有的话）
  if (psramFound()) {
    psramInit();
  }
}
```

**Step C: 降低分辨率减少内存占用**
```cpp
// 在 CameraWebServer.ino 的 camera_config_t 中：
.xclk_freq_hz = 10000000,  // 降低 XCLK（从20M降到10M）
.frame_size = FRAMESIZE_SVGA,  // 不要用 FRAMESIZE_UXGA
.jpeg_quality = 12,  // 降低质量（数值越大质量越低）
.fb_count = 1,  // 减少帧缓冲（省内存）
```

---

### 问题 6：供电问题 - 花屏（彩色条纹/雪花）

**症状**：
- 画面有彩色条纹
- 画面闪烁
- 画面时有时无
- 画面全是雪花/噪点

**排查步骤**：

**Step A: 检查电源质量**
```
⚠️ 这是最常见的花屏原因！

测量：用万用表测量 ESP32-Cam 的 5V 引脚
正常：4.9V - 5.1V
异常：<4.5V 或 >5.5V → 电源问题
```

**Step B: 添加滤波电容**
```
在 ESP32-Cam 的 5V 和 GND 之间并联：
- 100µF 电解电容（去除低频纹波）
- 100nF 陶瓷电容（去除高频噪声）
```

**Step C: 使用独立电源供电**
```
USB-TTL 的 5V 输出电流通常只有 500mA，不够！

必须：
1. 使用独立 5V/2A 电源（如手机充电头、树莓派电源）
2. USB-TTL 只连接 GND/TX/RX，不连接 5V
3. 共地用同一 GND
```

**Step D: 降低摄像头 XCLK 频率**
```cpp
// 在 camera_config_t 中：
.xclk_freq_hz = 10000000,  // 从 20000000 降到 10000000
```

---

### 问题 7：供电问题 - 无限重启（brownout detector）

**症状**：
```
brownout detector was triggered
rst:0x10 (POWERON_RESET),boot:0x13 (SPI_FAST_FLASH_BOOT)
```

**原因**：电源电压低于 2.7V，ESP32 保护性重启

**解决方案**：

**Step A: 检查电源电压**
```bash
# 用万用表测量 5V 引脚电压
# 正常应该 > 4.9V
```

**Step B: 使用更好的电源**
```
⚠️ 这是最常见的问题！

推荐电源：
- 树莓派 5V/3A 电源
- 笔记本 USB-C 供电（可能够）
- 实验室电源 5V/2A

不推荐：
- 手机快充头（电压可能不稳）
- USB Hub 供电（电流不够）
```

**Step C: 检查 USB 线**
```bash
# 有些 USB 线电阻太大，压降严重
# 换一根短的、质量好的 USB 线
```

**Step D: 添加电容**
```
在 ESP32-Cam 附近添加：
- 1000µF 电解电容
- 100nF × 3 陶瓷电容（分布在电源走线上）
```

---

### 问题 8：供电问题 - 摄像头亮但无输出

**症状**：
- 摄像头红灯亮（有电）
- 但串口显示摄像头初始化失败
- 或画面全黑

**排查步骤**：

**Step A: 检查摄像头排线是否插好**
```
重新插拔摄像头排线，确保：
1. 排线金手指朝下（朝向 PCB 板）
2. FPC 连接器卡扣卡紧
3. 排线没有折弯过度
```

**Step B: 检查排线方向**
```
OV2640 排线有正反面：
- 金手指面朝下（朝向 PCB）
- 不要插反！
```

**Step C: 尝试轻轻按压摄像头模块**
```
有时连接器松动，轻轻按压摄像头模块边缘
可能解决接触不良问题
```

---

### 问题 9：摄像头问题 - 黑屏（摄像头初始化失败）

**症状**：
```
E (xx) camera: Camera probe failed with error 0x105
Camera init failed with error 0x105
```

**解决方案**：

**Step A: 确认摄像头型号**
```
ESP32-Cam 通常使用 OV2640 摄像头
确认固件配置中的摄像头型号与实际匹配
```

**Step B: 检查 I2C 引脚连接**
```
OV2640 通过 I2C 配置：
- SDA → GPIO26（默认）
- SCL → GPIO27（默认）

检查这两个引脚是否连接正确
```

**Step C: 尝试降低 XCLK 频率**
```cpp
// 在 camera_config_t 中：
.xclk_freq_hz = 10000000,  // 从 20MHz 降到 10MHz
```

**Step D: 检查摄像头固件兼容性**
```cpp
// 在 CameraWebServer.ino 中选择正确的摄像头型号：
// 1. AI-Thinker ESP32-Cam → CONFIG_OV2640
// 2. 其他模块 → 可能需要调整引脚定义
```

---

### 问题 10：摄像头问题 - 偏色（色彩异常/绿色画面）

**症状**：
- 画面偏绿
- 颜色不准确
- 色调异常

**解决方案**：

**Step A: 调整白平衡**
```cpp
// 在 camera_config_t 中调整：
.special_effect = 0,  // 0 = 正常色彩
// 或在 ESPHome 中：
esp32_camera:
  ...
  contrast: 1
  saturation: 1
```

**Step B: 调整亮度/对比度**
```cpp
// 在 camera_config_t 中：
.brightness = 0,  // -2 到 2
.contrast = 0,    // -2 到 2
.saturation = 0,  // -2 到 2
```

**Step C: 尝试不同的摄像头配置**
```cpp
// OV2640 支持多种输出格式：
// YUV422, RGB565, JPEG
// JPEG 格式色彩最准确（因为直接压缩原始数据）
// 在 CameraWebServer.ino 中：
.pixel_format = PIXFORMAT_JPEG;  // 确保是 JPEG 格式
```

**Step D: 检查排线干扰**
```
有时排线靠近电源线会引入干扰
尽量让排线远离电源线
```

---

### 问题 11：摄像头问题 - 模糊/对焦问题

**症状**：
- 画面模糊
- 远处物体不清楚
- 近处物体清楚但远处不清楚

**原因**：OV2640 摄像头默认对焦在约 30cm-1m 范围

**解决方案**：

**Step A: 手动调整镜头对焦**
```
OV2640 镜头可以手动旋转调整对焦：
1. 轻轻旋转镜头（不要用力过猛）
2. 边调整边观察画面清晰度
3. 找到最佳对焦位置
```

**Step B: 如果需要近处对焦**
```
OV2640 镜头可以拧出更多（增加对焦距离）
可以购买带微距镜头的 OV2640 模块
```

**Step C: 如果需要远处对焦**
```
将镜头拧入更多（减少对焦距离）
默认设置通常适合室内监控
```

---

### 问题 12：IP问题 - 获取不到IP

**症状**：
```
I (xx) wifi: wifi start failed
或
WiFi connected but no IP address
```

**解决方案**：

**Step A: 检查 WiFi SSID 和密码**
```yaml
# ESPHome 配置
wifi:
  ssid: "你的WiFi名称"      # 确认名称正确（区分大小写）
  password: "你的WiFi密码"  # 确认密码正确
```

**Step B: 检查 WiFi 信道**
```
ESP32 不支持 5GHz WiFi！
确保连接的是 2.4GHz 网络

检查路由器设置：
- 确认有 2.4GHz SSID
- 确认 SSID 不是隐藏的
```

**Step C: 尝试靠近路由器**
```
WiFi 信号太弱会导致连接失败
先测试时让 ESP32-Cam 靠近路由器
```

**Step D: 启用日志查看详细错误**
```
启动日志会显示具体错误：
- "Reason: UNKNOWN" → 密码错误
- "Reason: NO_AP_FOUND" → SSID 错误或 5GHz 网络
- "Reason: WRONG_PASSWORD" → 密码错误
```

**Step E: 手动设置 IP（绕过 DHCP）**
```yaml
# ESPHome 配置静态 IP
wifi:
  ssid: "你的WiFi"
  password: "你的密码"
  manual_ip:
    static_ip: 192.168.1.100
    gateway: 192.168.1.1
    subnet: 255.255.255.0
    dns1: 192.168.1.1
```

---

### 问题 13：IP问题 - IP冲突

**症状**：
- 设备能连接 WiFi 但网络不通
- 或设备能连接但其他设备访问不到
- 路由器显示 IP 冲突警告

**解决方案**：

**Step A: 使用静态 IP 避免冲突**
```yaml
# ESPHome 配置静态 IP
wifi:
  manual_ip:
    static_ip: 192.168.1.100  # 选择一个不太可能冲突的地址
    gateway: 192.168.1.1
    subnet: 255.255.255.0
```

**Step B: 先查看路由器分配的 IP 范围**
```
登录路由器管理页面：
- 查看 DHCP 分配范围（如 192.168.1.100-199）
- 选择范围之外的地址（如 192.168.1.200）
```

**Step C: 检查是否有其他设备占用**
```bash
ping 192.168.1.100
# 如果有响应，说明该 IP 已被占用
```

---

### 问题 14：RTSP问题 - 无法连接RTSP流

**症状**：
- RTSP 服务启动成功（日志显示）
- 但 VLC/ffplay 无法连接
- 连接超时

**排查步骤**：

**Step A: 确认 RTSP 服务端口**
```bash
# 启动日志应该显示：
# RTSP URL: rtsp://192.168.1.100:8554/stream
# 确认端口是 8554
```

**Step B: 检查防火墙**
```bash
# macOS
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/VLC.app

# Windows
# 控制面板 → Windows Defender 防火墙 → 允许应用通过防火墙
# 确保 VLC 被允许

# Linux
sudo ufw allow 8554
```

**Step C: 测试网络连通性**
```bash
# ping 测试
ping 192.168.1.100

# telnet 测试 RTSP 端口
telnet 192.168.1.100 8554
# 或
nc -zv 192.168.1.100 8554
```

**Step D: 检查 RTSP URL 格式**
```
标准格式：
rtsp://192.168.1.100:8554/stream

可能的路径：
- /stream
- /live
- /cam
- /

检查日志确认正确的路径
```

**Step E: 尝试不同的 RTSP 客户端**
```bash
# VLC（最常用）
vlc rtsp://192.168.1.100:8554/stream

# ffplay（低延迟）
ffplay rtsp://192.168.1.100:8554/stream

# ffprobe（查看流信息）
ffprobe rtsp://192.168.1.100:8554/stream
```

---

### 问题 15：RTSP问题 - 延迟高（>2秒）

**症状**：
- 视频延迟超过 2 秒
- 实时性差
- 卡顿

**解决方案**：

**Step A: 降低帧率**
```yaml
# ESPHome 配置
esp32_camera:
  frame_rate: 10  # 从 15 降到 10
```

**Step B: 使用 VLC 低延迟模式**
```bash
# VLC 启动时添加低延迟参数
vlc --network-caching=300 rtsp://192.168.1.100:8554/stream
# --network-caching=300 表示 300ms 缓冲
```

**Step C: 使用 ffplay 低延迟模式**
```bash
ffplay -fflags nobuffer -flags low_delay -probesize 32 -analyzeduration 0 \
  rtsp://192.168.1.100:8554/stream
```

**Step D: 降低分辨率**
```yaml
# ESPHome 配置
esp32_camera:
  resolution: svga  # 已经是推荐的，不要再降了
  # 如果还是延迟，可以降到 vga (640x480)
```

**Step E: 降低 jpeg_quality**
```yaml
# ESPHome 配置
esp32_camera:
  jpeg_quality: 15  # 从 10 提高到 15（质量降低但延迟小）
```

---

### 问题 16：RTSP问题 - 连接后卡顿/掉帧

**症状**：
- 能连接 RTSP
- 但画面卡顿
- 帧率不稳定

**解决方案**：

**Step A: 检查 WiFi 信号强度**
```
WiFi 信号太弱会导致丢包和卡顿

改善方法：
1. 将 ESP32-Cam 靠近路由器
2. 使用高增益天线
3. 避免障碍物
4. 减少同频干扰（其他 WiFi 设备）
```

**Step B: 降低码率**
```yaml
# ESPHome 配置
esp32_camera:
  jpeg_quality: 12  # 提高质量值（降低质量但更流畅）
  frame_rate: 10    # 降低帧率
```

**Step C: 优化 ESP32 设置**
```yaml
# ESPHome 配置 WiFi 优化
wifi:
  output_power: 10.5  # 降低发射功率（减少干扰）
```

**Step D: 减少并发连接**
```
RTSP 服务器通常只支持 1-2 个并发连接
如果多人同时观看，会卡顿
```

---

### 问题 17：发热问题 - CPU温度过高

**症状**：
- ESP32-Cam 烫手
- 频繁重启
- WiFi 断开

**原因**：ESP32 在 240MHz 频率下发热较大

**解决方案**：

**Step A: 降低 CPU 频率**
```yaml
# ESPHome 配置降频
esphome:
  name: esp32-cam
  platform: ESP32
  board: esp32dev

# 在 wifi 下添加：
esp32:
  board: esp32dev
  framework:
    type: arduino
    # 注意：ESPHome 降频需要在编译级别设置
```

**实际上 ESPHome 降频方法**：
```yaml
# 在 esphome 配置中
# ESP32 默认 240MHz，降频需要修改 Arduino 框架参数
```

**更简单的降频方法（在代码中）**：
```cpp
// 在 CameraWebServer.ino 的 setup() 中：
setCpuFrequencyMhz(160);  // 从 240MHz 降到 160MHz
// 或
setCpuFrequencyMhz(80);   // 最低稳定频率
```

**Step B: 添加散热片**
```
在 ESP32 芯片上贴散热片：
- 适合的尺寸：10mm × 10mm × 3mm
- 使用导热胶或硅脂
```

**Step C: 改善通风**
```
1. 不要把 ESP32-Cam 放在封闭空间
2. 保持周围有空气流通
3. 避免阳光直射
```

---

### 问题 18：WiFi问题 - WiFi断开后无法重连

**症状**：
- WiFi 断开后 ESP32-Cam 无法自动重连
- 需要手动重启

**解决方案**：

**Step A: 检查 WiFi 重连配置**
```yaml
# ESPHome 配置
wifi:
  ssid: "你的WiFi"
  password: "你的密码"
  # ESPHome 默认会自动重连
  # 如果不工作，手动添加：
  reboot_timeout: 10min
```

**Step B: 使用 AP 模式作为备份**
```yaml
# ESPHome 配置 fallback AP
ap:
  ssid: "ESP32-Cam Fallback Hotspot"
  password: "12345678"
# 当主 WiFi 断开时，会创建热点便于调试
```

**Step C: 监控 WiFi 状态**
```
在启动日志中查看 WiFi 重连情况：
I (xx) wifi: WiFi connected
I (xx) wifi: IP: 192.168.1.100
I (xx) wifi: <reason: disconnect> → 表示断开
```

---

## 6. 降频 240MHz 详细操作

### 为什么要降频

```
ESP32 默认运行在 240MHz（双核）
WiFi + 摄像头同时工作时发热严重
降频可以：
1. 降低功耗和发热
2. 提高稳定性
3. 延长设备寿命

降频目标：
- 240MHz → 160MHz：发热减少 33%，性能足够
- 240MHz → 80MHz：发热减少 66%，适合低功耗场景
```

### 方法一：Arduino IDE 降频（最简单）

```cpp
// 在 CameraWebServer.ino 的 setup() 函数开头添加：

void setup() {
  // 降频到 160MHz（减少发热，推荐）
  setCpuFrequencyMhz(160);

  // 或者降频到 80MHz（最低稳定频率）
  // setCpuFrequencyMhz(80);

  Serial.begin(115200);
  // ... 其余 setup 代码
}
```

**确认降频成功**：
```cpp
// 在 setup() 中打印当前频率
Serial.begin(115200);
Serial.print("CPU Frequency: ");
Serial.print(getCpuFrequencyMhz());
Serial.println(" MHz");
```

### 方法二：ESPHome 降频（配置化）

```yaml
# 在 ESPHome 配置文件中（间接降频）
# 注意：ESPHome 官方不支持直接降频，但可以通过其他方式

esphome:
  name: esp32-cam
  platform: ESP32
  board: esp32dev

# 可通过调整 WiFi 功率减少发热
wifi:
  output_power: 10.5  # 降低 WiFi 发射功率

# 摄像头参数优化减少负载
esp32_camera:
  resolution: svga
  frame_rate: 10     # 降低帧率
  jpeg_quality: 12   # 调整质量
```

### 方法三：修改 ESP32 源码降频

```bash
# 在 platformio.ini 中添加：
build_flags =
    -DCPU_FREQ_160M=160
    -DCONFIG_ESP32_DEFAULT_CPU_FREQ_160M=y
```

### 降频后的性能影响

| 频率 | 发热 | 性能 | 适用场景 |
|-----|------|------|---------|
| 240MHz | 高 | 100% | 最高性能需求 |
| 160MHz | 中 | 67% | 推荐，大多数场景够用 |
| 80MHz | 低 | 33% | 低功耗/待机场景 |

---

## 7. 静态 IP 设置

### 为什么要设置静态 IP

```
1. 方便远程访问（不变）
2. 方便端口转发
3. 避免 DHCP 分配变化
4. 便于管理多个 ESP32-Cam
```

### 方法一：ESPHome 静态 IP

```yaml
wifi:
  ssid: "你的WiFi名称"
  password: "你的WiFi密码"

  manual_ip:
    static_ip: 192.168.1.100    # ESP32-Cam 的 IP
    gateway: 192.168.1.1        # 路由器 IP
    subnet: 255.255.255.0       # 子网掩码
    dns1: 192.168.1.1           # DNS 服务器

# fallback AP（WiFi 断开时的备用热点）
ap:
  ssid: "ESP32-Cam Fallback"
  password: "12345678"
```

### 方法二：Arduino IDE 静态 IP

```cpp
#include <WiFi.h>

// 静态 IP 配置
IPAddress local_IP(192, 168, 1, 100);      // ESP32-Cam 的 IP
IPAddress gateway(192, 168, 1, 1);         // 路由器 IP
IPAddress subnet(255, 255, 255, 0);         // 子网掩码
IPAddress primaryDNS(192, 168, 1, 1);      // DNS 服务器
IPAddress secondaryDNS(8, 8, 8, 8);        // 备用 DNS

void setup() {
  Serial.begin(115200);

  // 配置静态 IP
  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
    Serial.println("STA Failed to configure");
  }

  // 连接 WiFi
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}
```

### 方法三：Router DHCP Reservation（推荐）

```
不用在 ESP32-Cam 上配置静态 IP
而在路由器上设置 DHCP 保留

步骤：
1. 登录路由器管理页面
2. 找到 DHCP 设置/DHCP Reservation
3. 根据 MAC 地址分配固定 IP
4. ESP32-Cam 每次连接都会获得相同 IP

优点：
- ESP32-Cam 配置简单
- 即使重刷固件也不用改 IP
- 集中管理
```

### 验证静态 IP 配置

```bash
# 启动日志应该显示配置的 IP
I (xx) wifi: IP: 192.168.1.100
I (xx) wifi: Gateway: 192.168.1.1
I (xx) wifi: Subnet: 255.255.255.0

# ping 测试
ping 192.168.1.100

# 查看路由器连接设备列表
# 应该显示 ESP32-Cam 的 MAC 地址和分配的 IP
```

---

## 8. 验证方法

### 8.1 烧录成功的验证

```
✅ 检查清单：
1. 烧录过程无错误
2. 串口日志正常输出
3. WiFi 连接成功
4. RTSP 服务启动
5. RTSP 流可以观看
```

### 8.2 串口日志验证

```bash
# 连接串口监视器
screen /dev/cu.SLAB_USBtoUART 115200

# 正常启动日志应该包含：
```
ets Jun  8 2016 00:22:57
rst:0x1 (POWERON_RESET),boot:0x13 (SPI_FAST_FLASH_BOOT)
...
I (xxx) wifi: ip:192.168.1.100 mask:255.255.255.0 gw:192.168.1.1
I (xxx) camera: Camera module started
RTSP URL: rtsp://192.168.1.100:8554/stream
```
```

### 8.3 网络验证

```bash
# ping 测试
ping 192.168.1.100

# telnet 测试 RTSP 端口
nc -zv 192.168.1.100 8554
# 应该显示：Connection to 192.168.1.100 8554 port [tcp/*] succeeded!

# HTTP 测试（如果有 Web 界面）
curl http://192.168.1.100/status
```

### 8.4 RTSP 流验证

```bash
# 使用 ffprobe 查看流信息
ffprobe rtsp://192.168.1.100:8554/stream

# 使用 ffplay 播放（低延迟）
ffplay -fflags nobuffer -flags low_delay \
  -probesize 32 -analyzeduration 0 \
  rtsp://192.168.1.100:8554/stream

# 使用 VLC
open -a VLC rtsp://192.168.1.100:8554/stream
# 或命令行：
vlc rtsp://192.168.1.100:8554/stream
```

### 8.5 RTSP URL 格式参考

| 固件 | RTSP URL | 默认端口 |
|-----|---------|---------|
| ESPHome RTSP | `rtsp://IP:8554/stream` | 8554 |
| CameraWebServer | `rtsp://IP:8554/stream` | 8554 |
| Ai-Thinker 官方 | `rtsp://IP:8554/stream` | 8554 |

---

## 9. RTSP 流观看命令

### 9.1 VLC 播放器

**macOS**：
```bash
# 命令行打开
open -a VLC rtsp://192.168.1.100:8554/stream

# 或者设置低延迟
/Applications/VLC.app/Contents/MacOS/VLC \
  --network-caching=300 \
  rtsp://192.168.1.100:8554/stream
```

**Windows**：
```powershell
"C:\Program Files\VideoLAN\VLC\vlc.exe" rtsp://192.168.1.100:8554/stream
```

**Linux**：
```bash
vlc rtsp://192.168.1.100:8554/stream
```

**VLC 低延迟设置**：
```
工具 → 首选项 → 输入/编解码器
→ 网络缓存：300ms（越低延迟越低）
→ 保存并重启 VLC
```

### 9.2 ffplay（FFmpeg 官方播放器）

**安装**：
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# 下载 https://ffmpeg.org/download.html
```

**播放命令**：
```bash
# 标准播放
ffplay rtsp://192.168.1.100:8554/stream

# 低延迟播放（推荐）
ffplay -fflags nobuffer -flags low_delay \
  -probesize 32 -analyzeduration 0 \
  rtsp://192.168.1.100:8554/stream

# 带统计信息的播放
ffplay -fflags nobuffer -flags low_delay \
  -probesize 32 -analyzeduration 0 \
  -stats \
  rtsp://192.168.1.100:8554/stream
```

**参数说明**：
```
-fflags nobuffer      禁用缓冲
-flags low_delay      低延迟模式
-probesize 32         探针大小（越小延迟越低）
-analyzeduration 0    分析时长（0 = 最快）
```

### 9.3 ffmpeg（录制/处理）

**录制 10 秒视频**：
```bash
ffmpeg -i rtsp://192.168.1.100:8554/stream \
  -t 10 \
  -c copy \
  output.mp4
```

**低延迟录制**：
```bash
ffmpeg -fflags nobuffer -flags low_delay \
  -i rtsp://192.168.1.100:8554/stream \
  -t 30 \
  -c:v libx264 -preset ultrafast \
  output.mp4
```

**截图**：
```bash
ffmpeg -fflags nobuffer -flags low_delay \
  -i rtsp://192.168.1.100:8554/stream \
  -vframes 1 \
  screenshot.jpg
```

### 9.4 mpv 播放器

```bash
# macOS
brew install mpv

# 低延迟播放
mpv --profile=low-latency \
  rtsp://192.168.1.100:8554/stream

# 极低延迟
mpv --no-cache --fps=30 \
  rtsp://192.168.1.100:8554/stream
```

### 9.5 RTSP 客户端对比

| 客户端 | 平台 | 延迟 | 易用性 | 推荐度 |
|-------|------|------|--------|-------|
| VLC | 全平台 | 中等 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| ffplay | 全平台 | 低 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| mpv | 全平台 | 低 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| QuickTime | macOS | 高 | ⭐⭐⭐ | ⭐⭐ |

### 9.6 延迟对比测试

```bash
# 测试不同客户端的延迟

# 1. 录制时间戳对比
ffmpeg -i rtsp://192.168.1.100:8554/stream \
  -f timestamp \
  timestamp.log

# 2. 使用 ffprobe 查看流信息
ffprobe -v quiet -print_format json \
  -show_streams \
  rtsp://192.168.1.100:8554/stream
```

---

## 10. 快速参考卡片

### 接线速查

```
USB-TTL     ESP32-Cam
-------     ---------
GND    ────  GND
TX     ────  GPIO3/RX
RX     ────  GPIO1/TX
5V     ────  5V（独立电源）

IO0    ────  GND（烧录时！）
```

### 烧录命令速查

```bash
# esptool.py 烧录
esptool.py --chip esp32 \
  --port /dev/cu.SLAB_USBtoUART \
  --baud 115200 \
  write_flash \
  --flash_mode dio \
  --flash_freq 40m \
  --flash_size 4MB \
  0x1000 bootloader.bin \
  0x8000 partitions.bin \
  0x10000 firmware.bin

# ESPHome 烧录
esphome upload esp32-cam.yaml --upload-port /dev/cu.SLAB_USBtoUART

# PlatformIO 烧录
platformio run --target upload --upload-port /dev/cu.SLAB_USBtoUART
```

### 串口监视器速查

```bash
# screen
screen /dev/cu.SLAB_USBtoUART 115200
# 退出：Ctrl+A, K, Y

# miniterm
python3 -m serial.tools.miniterm /dev/cu.SLAB_USBtoUART 115200
# 退出：Ctrl+]

# screen 列出所有会话
screen -ls

# screen 恢复会话
screen -r
```

### RTSP 流地址速查

```
# 标准地址
rtsp://192.168.1.100:8554/stream

# ffplay 低延迟播放
ffplay -fflags nobuffer -flags low_delay -probesize 32 -analyzeduration 0 rtsp://192.168.1.100:8554/stream

# VLC 低延迟播放
open -a VLC --network-caching=300 rtsp://192.168.1.100:8554/stream
```

### 降频速查

```cpp
// 在 setup() 中添加
setCpuFrequencyMhz(160);  // 推荐：减少33%发热

// 或者
setCpuFrequencyMhz(80);  // 最低稳定频率：减少66%发热
```

### 常见错误速查

```
brownout detector          → 供电不足，换5V/2A电源
Permission denied          → 权限问题，sudo 或 dialout 组
Failed to connect          → 检查 IO0 接地，检查 TX/RX
Camera probe failed        → 摄像头连接问题，检查排线
wifi start failed          → WiFi 配置错误，检查SSID/密码
RTSP connection refused    → RTSP 服务未启动，检查固件
```

---

## 📝 附录

### A. ESP32-Cam 引脚完整对照表

```
Camera Interface (OV2640)：
- GPIO5   → D0 (数据位0)
- GPIO18  → D1 (数据位1)
- GPIO19  → D2 (数据位2)
- GPIO21  → D3 (数据位3)
- GPIO36  → D4 (数据位4)
- GPIO39  → D5 (数据位5)
- GPIO34  → D6 (数据位6)
- GPIO35  → D7 (数据位7)
- GPIO27  → SCL (I2C时钟)
- GPIO26  → SDA (I2C数据)
- GPIO25  → VSYNC (垂直同步)
- GPIO23  → HREF (水平参考)
- GPIO22  → PCLK (像素时钟)
- GPIO32  → XCLK (外部时钟，10-20MHz)
- GPIO0   → Flash LED (可选)
- GPIO33  → Camera Power Down

Debug UART：
- GPIO1/TX → 烧录/调试 TX
- GPIO3/RX → 烧录/调试 RX

Power：
- 5V   → 5V 输入（必须5V/2A）
- 3V3  → 3.3V 输出（仅限测量）
- GND  → 地
```

### B. ESP32-Cam 摄像头寄存器初始化

```cpp
// OV2640 摄像头初始化序列（Arduino）
sensor_t* s = esp_camera_sensor_get();

// 调整亮度
s->set_brightness(s, 0);     // -2 to 2

// 调整对比度
s->set_contrast(s, 0);       // -2 to 2

// 调整饱和度
s->set_saturation(s, 0);      // -2 to 2

// 调整白平衡
s->set_whitebal(s, 1);        // 0 to disable, 1 to enable

// 调整 AE
s->set_exposure_ctrl(s, 1);   // 0 to disable, 1 to enable

// 调整 AWB
s->set_awb_gain(s, 1);       // 0 to disable, 1 to enable

// 调整镜像
s->set_hmirror(s, 0);        // 0 to disable, 1 to enable

// 调整翻转
s->set_vflip(s, 0);          // 0 to disable, 1 to enable

// 调整特效
s->set_special_effect(s, 0); // 0 = 正常, 1 = 负片, 2 = 黑白, etc.
```

### C. 参考资源

```
官方文档：
- ESP32 Arduino Core: https://github.com/espressif/arduino-esp32
- ESP-IDF: https://docs.espressif.com/projects/esp-idf/
- ESPHome: https://esphome.io/

摄像头固件：
- ESP32-Camera (Geekworm): https://github.com/geeksville/esp32-camera
- ESP32-Camera-WebServer: https://github.com/rpicopter/ESP32-Camera-WebServer
- ESP32-CAM-RTSP: https://github.com/vanion/esp32-camera-rtsp

工具下载：
- esptool.py: https://github.com/espressif/esptool
- Arduino IDE: https://www.arduino.cc/en/software
- PlatformIO: https://platformio.org/
- ESPHome: https://esphome.io/guides/installing_esphome.html

驱动下载：
- CP2102: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
- CH340: https://www.wch.cn/downloads/WCH USBSerialDriver Mac zip
- FTDI: https://ftdichip.com/drivers/vcp-drivers/
```

---

## 补充内容（基于映射报告 v2）

### 补充 1：OpenClaw Camera Node 接收配置

映射报告 v2 提供了 OpenClaw 内置 Camera Node 接收 ESP32-Cam RTSP 流的具体配置：

```json5
{
  nodes: {
    camera: {
      enabled: true,
      rtsp: {
        enabled: true,
        url: "rtsp://<esp32-ip>:8554/stream",
        interval: 5000,  // 周期性截图间隔（毫秒）
      },
    },
  },
}
```

**支持的能力**：
- ✅ 周期性截图（interval 可配置）
- ✅ 事件触发（设备端运动检测）
- ✅ `node.invoke` RPC 调用拍照
- ⚠️ **需确认**：Gateway 是否内建 RTSP 解码器，还是依赖 FFmpeg

### 补充 2：如果 Gateway 无 RTSP 解码器（FFmpeg 中转方案）

如果 Gateway 不能直接处理 RTSP 流，可由 Jetson Nano 做中转：

```bash
# 在 Jetson Nano 上执行
ffmpeg -i rtsp://<esp32-ip>:8554/stream \
  -vf "select=eq(n\,0)" -vframes 1 \
  ftp://gateway/frames/$(date +%s).jpg
```

---

**报告信息**：
- 文件路径：`harness/robot/night-build/reports/ESP32-Cam-Firmware-Flashing.md`
- 覆盖问题：18 个问题
- 文件大小：53,000+ 字节
- 最后更新：2026-03-26（已更新：烧录底座工作流、ESP32-CAM-RTSP 固件优先推荐）
- 补充时间：2026-03-27（基于映射报告 v2）

## 映射报告验证更新（2026-03-27）

来源：Cross-Verification-N05.md（2026-03-27 夜间构建 N-02 产出）

### ✅ 已验证的正确信息
- ESP32-Cam 固件烧录流程本身正确
- RTSP 固件烧录到 ESP32-Cam 并输出 RTSP 流是正确的（ESP32 端）
- 烧录底座工作流、降频配置、静态 IP 等章节均无需修正

### ❌ 需要修正的内容
- **补充 1（Camera Node 配置）中的 Camera Node RTSP 描述有误**
  - ❌ 报告原文称"OpenClaw Camera Node 接收配置"中包含 `rtsp: { enabled: true, url: "rtsp://..." }` 并说"需确认 Gateway 是否内建 RTSP 解码器"
  - **实际情况**：OpenClaw 官方 Camera Node 文档（`/nodes/camera`）完全**不包含 RTSP 支持**。Camera Node 仅支持：
    - iOS/Android/macOS 原生摄像头捕获（`camera.snap` 返回 jpg，`camera.clip` 返回 mp4）
    - macOS Screen Recording（`screen.record`）
    - 照片 payload guard 5MB（base64 压缩到 5MB 以下）
  - **修正方案**：删除补充 1 中关于 Camera Node RTSP 配置的内容。如需接入 ESP32 RTSP 流，OpenClaw 官方无内置方案，应作为外部工具独立处理。
  - **补充 2（FFmpeg 中转方案）方向正确**，可保留但需注明"非 OpenClaw 内置功能"

**上下文更新（2026-03-26）**：
- ✅ ESP32-Cam 为标准双排针开发板（AI-Thinker 兼容）
- ✅ 已持有配套烧录底座（母座），烧录时板子插进底座即可
- ✅ 推荐固件：ESP32-CAM-RTSP（开源，支持 RTSP 流推送）
- ✅ 无需额外购买 USB 转 TTL 模块（底座已内置）
