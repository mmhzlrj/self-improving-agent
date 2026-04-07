# ESP32-CAM RTSP Streaming Server

> 将 AI-Thinker ESP32-CAM 变成一个支持标准 RTSP 协议的 MJPEG 流媒体服务器，可被 VLC、FFplay、Qt 等任何 RTSP 客户端直接拉流。

## 目录

- [特性](#特性)
- [硬件要求](#硬件要求)
- [快速开始](#快速开始)
  - [1. 安装 PlatformIO](#1-安装-platformio)
  - [2. 连接硬件](#2-连接硬件)
  - [3. 编译并烧录](#3-编译并烧录)
  - [4. 查看串口输出](#4-查看串口输出)
- [WiFi 配置](#wifi-配置)
  - [AP 模式（默认）](#ap-模式默认)
  - [STA 模式（连接路由器）](#sta-模式连接路由器)
- [RTSP 流地址](#rtsp-流地址)
- [播放器推荐](#播放器推荐)
- [配置参数参考](#配置参数参考)
- [LED 状态指示](#led-状态指示)
- [文件结构](#文件结构)
- [常见问题](#常见问题)
- [性能参考](#性能参考)
- [License](#license)

---

## 特性

- **标准 RTSP 协议**：使用 RTSP 1.0 + RTP over TCP，支持任何兼容客户端
- **MJPEG 编码**：无需额外转码，带宽占用低（@800x600 约 1-3 Mbps）
- **AP + STA 双模式**：默认 AP 热点，也支持连接现有路由器
- **LED 状态指示**：板载 LED 直观显示 WiFi / 摄像头 / 流媒体状态
- **最多 4 路并发客户端**：可同时被多个播放器拉流
- **PSRAM 优化**：自动检测并利用 ESP32 PSRAM，提升帧率稳定性

---

## 硬件要求

| 组件 | 说明 |
|------|------|
| AI-Thinker ESP32-CAM | 板载 OV2640 摄像头，集成 ESP32 + 2MP sensor |
| USB 转 TTL 模块 | CP2102 / CH340G，用于烧录和串口调试（如 ESP32-CAM 上有 USB 口可省略） |
| 5V 电源 or USB 供电 | 建议 5V/2A，防止供电不足导致重启 |
| 跳线帽（可选） | IO0 与 GND 短接进入烧录模式 |

> **注意**：部分 ESP32-CAM 板卡没有自带 USB 接口，需要通过外接 USB-UART 模块连接。
> 接线方式见[常见问题 - 烧录失败](#烧录失败)。

---

## 快速开始

### 1. 安装 PlatformIO

推荐使用 PlatformIO CLI 或 VSCode 插件：

```bash
# macOS
brew install platformio
# Linux
pip install platformio
# Windows: 下载 https://platformio.org/install/cli
```

或直接安装 **PlatformIO IDE for VSCode** 插件。

### 2. 连接硬件

使用 USB-UART 模块连接 ESP32-CAM：

| USB-UART 模块 | ESP32-CAM |
|--------------|-----------|
| TX | GPIO 3 (U0RXD) |
| RX | GPIO 1 (U0TXD) |
| GND | GND |
| 5V | 5V（或 VIN） |

> ⚠️ **接线时 ESP32-CAM 断电操作**，避免损坏。

如果需要进入烧录模式，还需将 IO0 拉低（GND），或按住板上的 **BOOT** 按钮再复位。

### 3. 编译并烧录

```bash
# 进入项目目录
cd esp32-cam-rtsp

# 编译
pio run

# 上传（需要进入烧录模式）
pio run --target upload

# 上传后自动打开串口监视器
pio device monitor
```

或者在 VSCode 中点击 PlatformIO 插件的 **Upload** 按钮。

### 4. 查看串口输出

连接成功后，串口（115200 baud）会输出：

```
╔════════════════════════════════════════════╗
║      ESP32-CAM RTSP Streaming Server       ║
║           Version 1.0.0                    ║
╚════════════════════════════════════════════╝

[WiFi] AP 模式，启动热点: ESP32_CAM_AP
[WiFi] AP 启动成功！
[WiFi] IP 地址: 192.168.4.1
[WiFi] RTSP 完整地址: rtsp://192.168.4.1:8554/mjpeg/1

[Camera] 摄像头初始化成功！
[Camera] 分辨率: 800x600
[Camera] JPEG 质量: 12

[RTSP] RTSP 服务器启动，端口: 8554
[RTSP] RTSP 服务器启动成功！
```

---

## WiFi 配置

### AP 模式（默认）

设备会创建名为 `ESP32_CAM_AP` 的热点，密码 `12345678`。直接连接即可。

**适用场景**：没有路由器、临时部署、现场配置。

```
设备 IP: 192.168.4.1（默认）
RTSP 端口: 8554
完整流地址: rtsp://192.168.4.1:8554/mjpeg/1
```

### STA 模式（连接路由器）

修改 `platformio.ini` 中的 `build_flags`，或直接在代码中定义：

```ini
build_flags =
    -DWIFI_AP_MODE=false
    -DSTA_SSID="YourRouterSSID"
    -DSTA_PASSWORD="YourRouterPassword"
```

编译烧录后，设备会连接指定路由器，串口打印获取到的 IP：

```
[WiFi] STA 连接成功！
[WiFi] IP 地址: 192.168.1.100
[WiFi] RSSI: -45 dBm
[WiFi] RTSP 完整地址: rtsp://192.168.1.100:8554/mjpeg/1
```

> **提示**：如果 STA 连接失败（30 秒超时），设备会自动回退到 AP 模式，确保始终可以连接。

---

## RTSP 流地址

```
rtsp://<设备IP>:8554/mjpeg/1
```

| 参数 | 值 |
|------|-----|
| 协议 | RTSP 1.0 over TCP (interleaved) |
| 视频格式 | MJPEG (RTP payload type 26) |
| 分辨率 | 默认 800x600（可在 platformio.ini 中修改） |
| 帧率 | 约 20-30 FPS（取决于场景和 WiFi 质量） |
| 并发客户端 | 最多 4 路 |

---

## 播放器推荐

### VLC（推荐，跨平台）

```
1. 打开 VLC → 媒体 → 打开网络串流
2. 输入: rtsp://192.168.4.1:8554/mjpeg/1
3. 点击播放
```

或命令行：
```bash
vlc rtsp://192.168.4.1:8554/mjpeg/1
```

### FFplay（命令行）

```bash
ffplay rtsp://192.168.4.1:8554/mjpeg/1
```

### ffplay 进阶参数

```bash
# 指定缓冲区大小（降低延迟）
ffplay -fflags nobuffer -flags low_delay rtsp://192.168.4.1:8554/mjpeg/1

# 录制到文件
ffmpeg -i rtsp://192.168.4.1:8554/mjpeg/1 -c copy output.mp4
```

### 其他兼容客户端

- **Qt VLC Media Player**：Windows / Linux
- **iOS / Android**：IP Camera、tinyCam Monitor 等 App
- **Web**：通过 FFmpeg 转发为 HLS 或 MSE 流
- **Python**：opencv-python (`cv2.VideoCapture("rtsp://...")`)

---

## 配置参数参考

在 `platformio.ini` 的 `build_flags` 中覆盖：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `WIFI_SSID` | `ESP32_CAM_AP` | AP 热点名称 |
| `WIFI_PASSWORD` | `12345678` | AP 热点密码（至少 8 位） |
| `WIFI_AP_MODE` | `true` | `true`=AP 模式，`false`=STA 模式 |
| `STA_SSID` | `YourRouterSSID` | STA 模式下的路由器名称 |
| `STA_PASSWORD` | `YourRouterPassword` | STA 模式下的路由器密码 |
| `RTSP_PORT` | `8554` | RTSP 服务端口 |
| `VIDEO_FRAME_SIZE` | `SVGA` | 分辨率，可选 UXGA/SXGA/HD/SVGA/VGA |
| `JPEG_QUALITY` | `12` | JPEG 质量 10-63，越小质量越高 |
| `ENABLE_PSRAM` | `enabled` | 自动检测 PSRAM，禁用可设置 `false` |

分辨率对照：

| 名称 | 宽度 | 高度 |
|------|------|------|
| `FRAMESIZE_UXGA` | 1600 | 1200 |
| `FRAMESIZE_SXGA` | 1280 | 1024 |
| `FRAMESIZE_HD` | 1280 | 720 |
| `FRAMESIZE_SVGA` | 800 | 600 |
| `FRAMESIZE_VGA` | 640 | 480 |

> ⚠️ 分辨率越高，需要的 PSRAM 越大。无 PSRAM 的 ESP32-CAM 建议使用 VGA 或 SVGA。

---

## LED 状态指示

板载蓝色 LED（ GPIO 33，active-LOW）指示系统运行状态：

| 状态 | 闪烁模式 | 含义 |
|------|----------|------|
| `LED_OFF` | 熄灭 | 系统空闲 / 关机 |
| `LED_WIFI_CONNECTING` | 慢闪（500ms 周期） | 正在连接 WiFi |
| `LED_WIFI_OK` | 双闪（200ms x2） | WiFi 已连接 |
| `LED_STREAMING` | 常亮 | 正在推流 |
| `LED_CAMERA_ERROR` | 快闪（100ms 周期） | 摄像头错误 |
| `LED_RTSP_ERROR` | 三闪（200ms x3） | RTSP 服务器错误 |
| `LED_WIFI_ERROR` | 长闪（1000ms 灭） | WiFi 连接失败 |

LED 在 `loop()` 中由 `led_update()` 驱动，调用周期 50-100ms。

---

## 文件结构

```
esp32-cam-rtsp/
├── README.md              # 本文件
├── platformio.ini         # PlatformIO 项目配置
├── main.cpp               # 主入口：WiFi、摄像头、RTSP 初始化
├── camera.h / camera.cpp  # 摄像头驱动封装
├── RTSP.h / rtsp_server.cpp # RTSP 服务器实现
└── led_status.h           # LED 状态指示器
```

### 核心模块

| 文件 | 职责 |
|------|------|
| `main.cpp` | 系统初始化、WiFi 连接、FreeRTOS 摄像头任务 |
| `camera.cpp` | esp32-camera 驱动封装，提供 `camera_init/capture/frame` 接口 |
| `rtsp_server.cpp` | RTSP 协议栈实现（RTSP OPTIONS/DESCRIBE/SETUP/PLAY/TEARDOWN），RTP over TCP 打包发送 |
| `led_status.h` | LED 状态机，根据系统状态自动切换闪烁模式 |

---

## 常见问题

### 烧录失败

**症状**：`Connecting..........` 后超时。

**排查步骤**：
1. 检查 TX/RX 是否接反（UART 交叉连接）
2. 确认 IO0 已接地（按住 BOOT 按钮，或烧录前短接 IO0-GND）
3. 复位板卡（在串口监视器出现乱码时按一次 RST）
4. 尝试降低 `upload_speed`（`platformio.ini` 中设为 115200）

### 摄像头初始化失败（0xFFFFFFFF 或 0x10501）

**常见原因**：
- 摄像头排线接触不良（重新插拔摄像头 FPC 排线）
- XCLK 频率过高（部分 OV2640 不支持 20MHz，可降至 8MHz）
- PSRAM 容量不足（关闭 PSRAM 使用更小分辨率）

### 串口只显示乱码

- 确认波特率设为 **115200**（`platformio.ini` 中 `monitor_speed`）
- 检查是否选了正确的串口

### WiFi 已连接但无法拉流

- 确认防火墙未阻止 **8554** 端口
- 检查设备 IP 是否在同一网段
- 尝试 ping 设备 IP，确认网络连通

### VLC 播放卡顿 / 延迟高

- 降低分辨率（SVGA → VGA）和 JPEG 质量（12 → 20）
- 在 VLC 中关闭"所有接口"（工具 → 偏好设置 → 全部 → 串流输出）
- 使用 FFplay 并加低延迟参数：`ffplay -fflags nobuffer -flags low_delay rtsp://...`

---

## 性能参考

| 分辨率 | JPEG 质量 | 典型码率 | 推荐场景 |
|--------|-----------|----------|----------|
| 800x600 (SVGA) | 12 | 1-3 Mbps | 默认，平衡质量与带宽 |
| 640x480 (VGA) | 15 | 0.5-1.5 Mbps | 网络较差、移动设备 |
| 1280x720 (HD) | 10 | 2-5 Mbps | 高画质需求，需 PSRAM |

> 数据基于室内普通光照环境，WiFi 802.11n 直连。单客户端、无干扰环境下实测帧率约 20-30 FPS。

---

## License

MIT License

---

## 参考资料

- [esphome/esp32-camera](https://github.com/espressif/esp32-camera) — 官方 ESP32 Camera 驱动
- [airjournals/ESP32-RTSP](https://github.com/airicism/esp32-rtsp) — RTSP 协议参考
- [ESP32 RTSP 协议规范 (RFC 2326)](https://datatracker.ietf.org/doc/html/rfc2326)
- [RTP 协议规范 (RFC 3550)](https://datatracker.ietf.org/doc/html/rfc3550)
