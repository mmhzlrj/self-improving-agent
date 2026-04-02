# 视觉识别模块

> ESP32-Cam OV2640 采集视频流，Jetson Nano 2GB 运行 YOLO + MediaPipe，FP16 加速推理

## 概述

视觉识别模块是 0-1 机器人的感知核心，负责 24 小时视频采集和本地 AI 理解。ESP32-Cam（OV2640 摄像头）通过 RTSP 协议将视频流推送至 Jetson Nano 2GB，后者运行 YOLOv8n/v11n（TensorRT FP16 加速）和 MediaPipe（人体姿态/手势），完成目标检测、人体感知等任务。所有处理完全本地，不传云端。Phase 2 阶段目标为打通 ESP32-Cam → Jetson Nano 的完整视频流和 AI 推理链路。

## 硬件参数

| 参数 | 规格 |
|------|------|
| 摄像头 | ESP32-Cam，OV2640 传感器 |
| 处理器 | ESP32（Xtensa LX6，520KB SRAM，4MB Flash）|
| 视频输出 | RTSP 流（MJPEG 压缩）|
| 接收处理 | Jetson Nano 2GB（Maxwell 128-core，2GB LPDDR4）|
| 推荐分辨率 | QVGA 320×240 @ 5-10 FPS（避免 ESP32 内存溢出）|
| 通信 | WiFi STA（静态 IP）+ UART（与 Jetson Nano 通信）|

## 技术方案

**整体数据流**：
```
ESP32-Cam（采集）
    ↓ RTSP WiFi 流（192.168.x.99:8554/stream）
Jetson Nano 2GB
    ├─ GStreamer / FFmpeg 接收 RTSP
    ├─ YOLOv8n TensorRT FP16 → 目标检测（13-16 FPS @ 640×640）
    └─ MediaPipe Pose → 人体姿态估计（约 10-15 FPS，需开 swap）
    ↓
OpenClaw Gateway (MacBook)
```

**Jetson Nano 2GB 关键约束**：
- 2GB 内存必须开启 swap 才能同时跑 YOLO + MediaPipe
- 唯一有效 GPU 加速：**FP16**（Maxwell 架构不支持 INT8）
- 推荐输入分辨率：320×320 或 416×416（牺牲精度换 FPS）

**实测 FPS（完整 pipeline）**：

| 模型 | 输入分辨率 | FPS（含前后处理）|
|------|----------|----------------|
| YOLOv8n | 640×640 | ~13-16 |
| YOLOv8n | 416×416 | ~20-25 |
| YOLOv11n | 416×416 | ~25-35 |
| YOLOv4-tiny | 416×416 | ~20-30 |
| YOLOv11n | 320×320 | ~50+（极限值）|

**YOLO + MediaPipe 共存配置**（需开 swap）：
```
YOLOv8n + TensorRT FP16：~15-20 FPS，占用 ~1-1.5 GB
MediaPipe Pose（CPU）：~10-15 FPS，占用 ~500-800 MB
两者同时跑：约 10-15 FPS，内存 ~2.5 GB
```

**RTSP 接收命令**：
```bash
# GStreamer pipeline（低延迟）
gst-launch-1.0 rtspsrc location=rtsp://192.168.x.99:8554/stream \
  ! decodebin ! videoconvert ! autovideosink

# FFplay 测试
ffplay rtsp://192.168.x.99:8554/stream
```

## 当前状态

| 项目 | 状态 |
|------|------|
| ESP32-Cam 固件烧录 | ✅ 已烧录，待实测 |
| ESP32-Cam 静态 IP 配置 | ✅ 已配置 |
| RTSP 推流 | 🔄 待打通（Jetson Nano 接收测试）|
| Jetson Nano YOLO + TensorRT FP16 | ✅ 可用 |
| Jetson Nano MediaPipe | ⚠️ GPU 加速不成熟，建议用 TensorRT 替代 |
| YOLO + MediaPipe 共存 | 🔄 需开 swap，实测稳定性 |
| RynnBrain 接入（阶段二）| 🔄 阶段二任务 |

**Phase 2 里程碑**：
- [ ] ESP32-Cam 连接到 WiFi，验证 RTSP 流可访问
- [ ] Jetson Nano 安装 GStreamer，测试 RTSP 接收
- [ ] YOLOv8n 转换为 TensorRT FP16 模型
- [ ] 完整 pipeline 实测（ESP32-Cam → Nano → 检测结果）
- [ ] 与 OpenClaw 感知模块对接

## 问题记录

**花屏问题**
- **现象**：ESP32-Cam 视频流出现彩色条纹/花屏
- **原因**：ESP32-Cam 供电不足（部分 USB-TTL 仅供 3.3V，电流不够）
- **解决方案**：
  1. 使用独立 5V/2A 电源给 ESP32-Cam 供电（不要依赖 USB-TTL 取电）
  2. 确认 GND 共地连接正常
  3. 降低分辨率或帧率（减少瞬时电流峰值）

**IP 变更问题**
- **现象**：ESP32-Cam 重启后 IP 变化，导致 RTSP URL 失效
- **原因**：DHCP 分配地址不固定
- **解决方案**：
  1. 在 `camera_config_t` 中设置静态 IP（烧录前修改固件）
  2. 将 ESP32-Cam 分配为 DHCP 静态租约（路由器端）
  3. 推荐静态 IP：192.168.1.99

**ESP32-Cam 内存溢出**
- **现象**：高分辨率（如 800×600）时 ESP32 复位/重启
- **原因**：520KB SRAM 无法支撑高分辨率 JPEG 编码
- **解决方案**：使用 QVGA 320×240 或 CIF 400×296，分辨率越高越容易 OOM

## 参考链接

- [ROBOT-SOP.md - Phase 2 视觉记录模块](../harness/robot/ROBOT-SOP.md#phase-2视觉记录模块)
- [ROBOT-SOP.md - Jetson Nano 视觉感知](../harness/robot/ROBOT-SOP.md#jetson-nano-视觉感知)
- [ROBOT-SOP.md - ESP32-Cam 固件与通信](../harness/robot/ROBOT-SOP.md#esp32-cam-有线通信)
- [ROBOT-SOP.md - ESP32-Cam 问题排查](../harness/robot/ROBOT-SOP.md#esp32-cam-问题)
