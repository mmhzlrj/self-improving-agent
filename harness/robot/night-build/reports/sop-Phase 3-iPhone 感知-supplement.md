# Phase 3 iPhone 感知前端 — OpenClaw Bridge 协议补充

> 补充自 `reference/ROBOT-SOP.md` Phase 3 章节及 [OpenClaw Gateway Protocol 官方文档](https://docs.openclaw.ai/gateway/protocol)
> 生成时间：2026-03-30

---

## 摘要

Phase 3 的核心目标是让 iPhone 16 Pro 通过 **OpenClaw Gateway WebSocket 协议**（统一协议，非已废弃的 legacy Bridge）接入 Gateway，成为分布式感知网络的一员。本文档详细定义 iPhone 与 Gateway 之间的通信协议、数据格式、认证机制和延迟预算。

**协议演进说明**：
- ⚠️ **Legacy Bridge Protocol**（TCP JSONL，端口 18790）已被废弃，当前版本不再包含 TCP bridge listener
- ✅ **Gateway WebSocket Protocol**（统一协议）是当前推荐方案，所有平台统一使用 WebSocket + JSON

---

## 1. 协议选择

### 1.1 为什么选 Gateway WebSocket Protocol

| 维度 | Legacy Bridge（TCP JSONL）| Gateway WebSocket（当前）|
|------|--------------------------|--------------------------|
| 传输层 | TCP 直连 | WebSocket（TLS 支持）|
| 端口 | 18790（已废弃）| 与 Gateway 共用端口 |
| 安全性 | 基础 token | challenge-response + device identity + TLS |
| 平台支持 | 需自行实现 TCP JSONL | 所有平台统一，官方 SDK 支持 |
| 双向通信 | 是 | 是（invoke / event）|
| 推荐度 | ❌ 已废弃 | ✅ 推荐 |

**结论**：iPhone 接入必须使用 **Gateway WebSocket Protocol**，不要使用 legacy bridge。

### 1.2 iPhone 作为 OpenClaw Node 的角色定义

iPhone 16 Pro 在 OpenClaw 网络中的角色为 **`node`**，不是 `operator`。

```json
{
  "type": "req",
  "id": "<uuid>",
  "method": "connect",
  "params": {
    "minProtocol": 3,
    "maxProtocol": 3,
    "client": {
      "id": "iphone-16pro",
      "version": "1.0.0",
      "platform": "ios",
      "mode": "node"
    },
    "role": "node",
    "scopes": [],
    "caps": ["camera", "canvas", "screen", "location", "voice", "lidar", "arkit"],
    "commands": ["camera.snap", "camera.stream", "lidar.depth", "arkit.pose", "vision.detect", "mediapipe.gesture"],
    "permissions": {
      "camera.capture": true,
      "camera.stream": true,
      "lidar.depth": true,
      "arkit.pose": true,
      "vision.detect": true,
      "mediapipe.gesture": true
    },
    "auth": { "token": "<node-token>" },
    "locale": "zh-CN",
    "userAgent": "openclaw-ios/1.0.0",
    "device": {
      "id": "<device-fingerprint>",
      "publicKey": "<base64>",
      "signature": "<base64>",
      "signedAt": 1743340800000,
      "nonce": "<challenge-nonce>"
    }
  }
}
```

---

## 2. 握手与认证流程

### 2.1 完整握手序列

```
iPhone                              Gateway
  |----------- TCP / TLS 连接 ------------->|
  |<-------- connect.challenge (nonce) -----|  Gateway 主动下发挑战
  |----------- connect (params) ----------->|  iPhone 带上 token + device identity
  |<----------- hello-ok ------------------|  认证成功，返回 deviceToken
  |                                     |
  |========= 双向 WebSocket 通道建立 ======|
  |                                     |
  |<========= invoke 指令（Gateway→iPhone）=|  Gateway 主动调用 iPhone 能力
  |========= event 事件（iPhone→Gateway）=|  iPhone 主动上报感知数据
```

### 2.2 Challenge-Response 认证细节

**Step 1**: iPhone 收到 `connect.challenge`：

```json
{
  "type": "event",
  "event": "connect.challenge",
  "payload": {
    "nonce": "随机挑战字符串（防止重放攻击）",
    "ts": 1743340800000
  }
}
```

**Step 2**: iPhone 用设备私钥签名以下内容，生成 `v3` 签名 payload：

```
签名内容 = [client.id, client.version, platform, role, scopes, auth.token, device.nonce]
签名算法 = Ed25519 或 ECDSA P-256
```

**Step 3**: Gateway 验证签名和 token：
- ✅ 签名有效 + token 匹配 → 返回 `hello-ok` + `deviceToken`
- ❌ 签名无效 → 返回 `DEVICE_AUTH_SIGNATURE_INVALID`
- ❌ token 不匹配 → 返回 `AUTH_TOKEN_MISMATCH`

**Device Token 有效期**：Gateway 颁发后可持续使用，直到被 revoke。

### 2.3 Token 来源

iPhone Node 的 token 获取方式（与 Jetson Nano / Ubuntu 节点相同）：

1. 在 Mac Gateway 上配对页面批准新设备
2. Gateway 返回配对 token（一次性）
3. iPhone 持久化 token，后续重连使用同一 token

```bash
# Mac Gateway 查看已配对节点
openclaw devices list
```

---

## 3. 数据格式定义

### 3.1 感知数据类型总览

| 数据类型 | 来源 | 大小/帧 | 压缩 | 发送方向 |
|---------|------|---------|------|---------|
| RGB 视频流 | 后置摄像头 | ~1-2 MB/帧 | H.264/RTMP 或 JPEG | iPhone → Gateway |
| 深度图 | LiDAR | 256×192 半浮点 | 原始或 LZ4 | iPhone → Gateway |
| ARKit 位姿 | ARKit | <1 KB | JSON | iPhone → Gateway |
| 物体检测结果 | Vision/YOLO | <10 KB | JSON | iPhone → Gateway |
| 手势关键点 | MediaPipe | <5 KB | JSON | iPhone → Gateway |
| 场景理解 | FastVLM | <20 KB | JSON | iPhone → Gateway |
| 控制指令 | Gateway | <1 KB | JSON | Gateway → iPhone |

### 3.2 ARKit 位姿数据（最核心）

ARKit 每帧（约 30-60 FPS）通过 `event` 帧主动上报：

```json
{
  "type": "event",
  "event": "arkit.pose",
  "payload": {
    "timestamp": 1743340800123,
    "frameId": "iphone-pose-001",
    "camera": {
      "transform": [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.05, 1.2, -0.3, 1.0]
      ],
      "intrinsics": {
        "focalLength": [1500.0, 1500.0],
        "principalPoint": [480.0, 640.0]
      }
    },
    "trackingState": "normal",
    "worldMappingStatus": "mapped"
  }
}
```

> **说明**：`transform` 是 4×4 齐次变换矩阵（列主序），描述 iPhone 相对于 AR 世界原点的位置和朝向。`worldMappingStatus` 指示是否已有足够的特征点进行定位。

### 3.3 LiDAR 深度图数据

深度图通过 `lidar.depth` 事件上报，建议按区域块压缩：

```json
{
  "type": "event",
  "event": "lidar.depth",
  "payload": {
    "timestamp": 1743340800123,
    "frameId": "lidar-frame-001",
    "format": "float16-array",
    "width": 256,
    "height": 192,
    "depthScale": 0.001,
    "maxDepth": 10.0,
    "data": "<base64-encoded Float16Array>",
    "confidence": "<base64-encoded UInt8Array>"
  }
}
```

**传输优化**：
- 全分辨率深度图（256×192 Float16）≈ 98 KB / 帧，传输成本高
- **推荐策略**：每 3-5 帧发送一次完整深度图，期间用 ARKit 位姿内插
- 或者只发送稀疏点云（ARKit `sceneReconstruction` 已有）

### 3.4 物体检测结果（Vision Framework / YOLO Core ML）

```json
{
  "type": "event",
  "event": "vision.detect",
  "payload": {
    "timestamp": 1743340800123,
    "detections": [
      {
        "label": "person",
        "confidence": 0.97,
        "bbox": {"x": 120, "y": 80, "width": 200, "height": 400},
        "depth": 2.5
      },
      {
        "label": "cup",
        "confidence": 0.85,
        "bbox": {"x": 400, "y": 300, "width": 60, "height": 80},
        "depth": 0.8
      }
    ]
  }
}
```

### 3.5 手势识别（MediaPipe on iOS）

```json
{
  "type": "event",
  "event": "mediapipe.gesture",
  "payload": {
    "timestamp": 1743340800123,
    "gesture": "thumbs_up",
    "confidence": 0.92,
    "handedness": "right",
    "landmarks": [
      {"x": 0.5, "y": 0.8, "z": 0.0, "name": "wrist"},
      {"x": 0.52, "y": 0.6, "z": 0.02, "name": "thumb_cmc"}
      // ... 21 个关键点
    ]
  }
}
```

### 3.6 场景理解（FastVLM 0.5B 本地推理）

```json
{
  "type": "event",
  "event": "vision.caption",
  "payload": {
    "timestamp": 1743340800123,
    "caption": "用户在客厅沙发上观看电视，旁边茶几上有一杯咖啡",
    "entities": [
      {"type": "person", "count": 1, "description": "坐在沙发上"},
      {"type": "object", "name": "tv", "location": "前方 3 米"},
      {"type": "object", "name": "coffee_cup", "location": "茶几上"}
    ]
  }
}
```

---

## 4. WebSocket / HTTP 接口设计

### 4.1 连接参数

| 参数 | 值 |
|------|-----|
| 协议 | WSS（推荐）或 WS |
| Gateway 地址 | MacBook 局域网 IP 或 tailnet DNS |
| 端口 | Gateway WebSocket 端口（默认 18789）|
| 路径 | `/ws` 或根路径 |
| 子协议 | 无（OpenClaw 协议在 JSON 内区分）|

### 4.2 iPhone 上的 Invoke 处理（Gateway → iPhone）

当 Gateway 需要调用 iPhone 能力时，发送 `invoke` 帧，iPhone 必须响应：

```json
// Gateway → iPhone
{
  "type": "invoke",
  "id": "invoke-001",
  "command": "camera.snap",
  "params": {
    "resolution": "high",
    "format": "jpeg",
    "quality": 0.9
  }
}

// iPhone → Gateway
{
  "type": "invoke-res",
  "id": "invoke-001",
  "ok": true,
  "payload": {
    "imageData": "<base64>",
    "timestamp": 1743340800123,
    "camera": "back"
  }
}
```

**支持的 invoke 命令**：

| 命令 | 说明 | params |
|------|------|--------|
| `camera.snap` | 拍摄单张照片 | `resolution`, `format`, `quality` |
| `camera.stream` | 开始/停止视频流 | `action: "start" \| "stop"`, `fps` |
| `lidar.depth` | 获取当前深度图 | `format: "full" \| "sparse"` |
| `arkit.pose` | 获取 ARKit 位姿 | 无 |
| `vision.detect` | 触发物体检测 | `threshold`, `labels[]` |
| `location.get` | 获取 GPS 位置 | `accuracy` |

### 4.3 iPhone 主动上报（iPhone → Gateway）

iPhone 通过 `event` 帧主动上报感知数据，**无需 Gateway 邀请**：

```json
{
  "type": "event",
  "event": "感知事件类型",
  "payload": { ... }
}
```

**iPhone 可主动发送的事件类型**：

| 事件 | 触发频率 | 说明 |
|------|---------|------|
| `arkit.pose` | 每帧（30/60 FPS）| ARKit 相机位姿 |
| `lidar.depth` | 每 N 帧（N=3-5）| LiDAR 深度图 |
| `vision.detect` | 检测到新物体时 | Vision Framework 结果 |
| `mediapipe.gesture` | 检测到手势时 | MediaPipe 手势结果 |
| `vision.caption` | 每 1-5 秒 | FastVLM 场景描述 |
| `audio.transcript` | 语音识别结果 | 本地 Whisper 或 ASR |
| `battery.level` | 每分钟 | 电量变化时立即上报 |

### 4.4 Gateway → iPhone 的控制指令

Gateway 可以向 iPhone 发送控制指令，通过 `invoke` 或 `event` 机制：

```json
// 停止当前摄像头流（紧急）
{
  "type": "invoke",
  "id": "ctrl-001",
  "command": "camera.stream",
  "params": { "action": "stop" }
}

// 设置检测灵敏度
{
  "type": "event",
  "event": "config.update",
  "payload": {
    "detectionThreshold": 0.8,
    "depthFrameInterval": 5,
    "captionIntervalSec": 3
  }
}
```

---

## 5. 认证与安全机制

### 5.1 认证层次

| 层次 | 机制 | 说明 |
|------|------|------|
| **网络层** | TLS（WSS）| 加密所有传输内容 |
| **协议层** | Challenge-Response | 防止重放攻击，nonce + timestamp |
| **设备层** | Ed25519 / ECDSA P-256 公私钥对 | 设备身份不可伪造 |
| **应用层** | Gateway Token | 设备授权访问 Gateway |
| **命令层** | 命令白名单（`commands` 字段）| iPhone 只能执行声明的命令 |

### 5.2 Device Identity 签名细节

```
签名 Payload v3 结构：
{
  "client": { "id", "version", "platform", "mode" },
  "role": "node",
  "scopes": [],
  "auth": { "token": "..." },
  "device": {
    "id": "设备指纹（公钥 SHA-256）",
    "publicKey": "base64(公钥)",
    "nonce": "挑战 nonce",
    "signedAt": timestamp
  }
}

签名 = Base64(Ed25519.Sign(私钥, JSON.stringify(payload)))
```

**签名有效窗口**：`signedAt` 与 Gateway 当前时间偏差不得超过 ±5 分钟。

### 5.3 Token 安全

| 项目 | 说明 |
|------|------|
| Node Token 存储 | iOS Keychain（Secure Enclave 保护的区域）|
| Token 有效期 | 长期有效，可 revoke |
| Revoke 方式 | `device.token.revoke`（需 `operator.pairing` scope）|
| Token 轮换 | 支持 `device.token.rotate` |

### 5.4 数据隔离

| 数据类型 | 隔离级别 | 说明 |
|---------|---------|------|
| RGB 视频流 | TLS 加密传输 | 不过云端，直接到 Gateway |
| 深度图/LiDAR | TLS 加密传输 | 同上 |
| ARKit 位姿 | TLS 加密传输 | 同上 |
| 检测结果/场景描述 | TLS 加密传输 | 同上 |
| 原始视频存储 | 本地（iPhone）| Gateway 仅接收处理结果 |

> **隐私保证**：iPhone 的原始视频/图像始终存储在本地设备，只将结构化的感知结果（JSON）上传 Gateway。符合贵庚阶段一的设计原则。

---

## 6. 延迟预算

### 6.1 端到端延迟分解

```
感知链路（iPhone → Gateway → Agent → 控制）：
┌──────────────────────────────────────────────────────────────┐
│ iPhone 摄像头 → ARKit/Vision 处理 → JSON 编码 → WebSocket   │
│                                           → TLS 传输        │
│                                           → Gateway 解码   │
│                                           → OpenClaw Agent  │
│                                           → 响应             │
└──────────────────────────────────────────────────────────────┘
```

| 环节 | 延迟 | 说明 |
|------|------|------|
| ARKit 帧处理 | 5-15 ms | A18 Pro Neural Engine，约 60 FPS |
| Vision / YOLO Core ML | 3-8 ms | YOLOv11n 在 ANE 上极快 |
| MediaPipe 手势 | 5-10 ms | 33 关键点，ANE 加速 |
| FastVLM 0.5B 推理 | 50-200 ms | 本地 VLM，取决于序列长度 |
| JSON 序列化 | <1 ms | 极小数据量 |
| WebSocket 编码/TLS | 1-2 ms | 小帧影响小 |
| **局域网传输（iPhone↔Mac）** | **2-5 ms** | **WiFi 6 局域网，<1ms 如果同 AP** |
| Gateway 解码/分发 | 1-3 ms | Gateway 处理开销 |
| **感知链路总计** | **~20-230 ms** | 取决于是否含 VLM 推理 |

### 6.2 分任务延迟预算

| 任务 | 目标延迟 | 说明 |
|------|---------|------|
| ARKit 位姿上报 | <20 ms | 纯数据，无推理，局域网可达 |
| LiDAR 深度图上报 | <50 ms | 数据量 98KB，建议 3-5fps |
| 物体检测（Vision/YOLO）| <30 ms | Core ML/ANE 推理，极快 |
| 手势识别（MediaPipe）| <30 ms | ANE 加速 |
| 场景描述（FastVLM）| <500 ms | 本地 VLM，可异步 |
| Gateway → iPhone 控制指令 | <50 ms | 局域网延迟 |

### 6.3 带宽需求

| 数据类型 | 带宽需求 | 说明 |
|---------|---------|------|
| ARKit 位姿 | ~2 KB/s（30fps）| 可忽略 |
| LiDAR 深度图 | ~300 KB/s（3fps）| LZ4 压缩后可更低 |
| 物体检测结果 | ~10 KB/s | 事件驱动，非持续 |
| 手势识别结果 | ~5 KB/s | 事件驱动 |
| 场景描述（VLM）| ~20 KB/s（2fps）| 稀疏事件 |
| **合计** | **<500 KB/s** | **极低带宽需求** |

> ⚠️ 注意：以上仅为**感知元数据**的带宽，不含视频流。如需传输原始视频流到 Gateway（不做本地处理），则需要 5-20 Mbps（取决于分辨率/帧率）。

### 6.4 延迟优化建议

1. **异步 VLM**：FastVLM 场景描述不阻塞感知主链路，独立异步上传
2. **帧间稀疏化**：LiDAR 深度图每 3-5 帧传一次，期间用 ARKit 位姿内插
3. **按需检测**：Vision 检测结果只在检测到新物体或物体消失时上报
4. **批处理**：多个感知事件可批量打包在一个 WebSocket 帧中

---

## 7. iOS 原生实现架构

### 7.1 整体模块划分

```
┌─────────────────────────────────────────┐
│           iPhone 16 Pro                 │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌───────┐ │
│  │ ARKit    │  │ Vision   │  │LiDAR  │ │
│  │ (位姿)   │  │ Framework│  │深度图 │ │
│  └────┬─────┘  └────┬─────┘  └───┬───┘ │
│       │              │            │     │
│       └──────┬───────┴────────────┘     │
│              ▼                          │
│       ┌──────────────┐                  │
│       │ 感知融合层     │                  │
│       │ （本地处理）   │                  │
│       └──────┬───────┘                  │
│              ▼                          │
│  ┌──────────────────────────────┐       │
│  │  OpenClaw Node Client (Swift)│       │
│  │  • WebSocket 连接            │       │
│  │  • 协议帧编解码               │       │
│  │  • device identity 签名      │       │
│  │  • 命令分发 / 事件上报        │       │
│  └──────────┬───────────────────┘       │
│             │                            │
│       ┌─────▼─────┐                      │
│       │ Starscream│  (WebSocket 库)       │
│       └───────────┘                      │
└─────────────┬────────────────────────────┘
              │ WSS / TLS
              ▼
┌─────────────────────────────────────────┐
│     OpenClaw Gateway (MacBook)           │
└─────────────────────────────────────────┘
```

### 7.2 第三方依赖（iOS）

| 库 | 用途 | 说明 |
|---|------|------|
| **Starscream** | WebSocket 客户端 | Swift 官方推荐，支持 WSS |
| **ARKit** | AR 位姿追踪 | 系统自带，无需引入 |
| **Vision** | 物体检测/识别 | 系统自带，无需引入 |
| **Core ML** | YOLO 等 ML 模型推理 | 系统自带，需模型转换 |
| **MediaPipe Swift** | 手势关键点检测 | Google 开源，需自行编译 |
| **CryptoKit** | 设备身份签名 | 系统自带（iOS 13+）|
| **Security (Keychain)** | Token 安全存储 | 系统自带 |

### 7.3 与现有 rosbridge 方案的关系

Phase 3 原 SOP 中描述了通过 rosbridge（WebSocket）连接 Jetson Nano 的方案。该方案是**过渡方案**，用于在没有 OpenClaw iOS SDK 时快速验证。

**推荐演进路径**：

```
阶段 A（当前）：rosbridge → Jetson Nano → ROS 2
                iPhone 感知数据经过 Nano 中转

阶段 B（推荐）：OpenClaw WebSocket Protocol → Gateway
                iPhone 直连 Gateway，无需 Nano 中转
                iPhone 成为一等 OpenClaw Node
```

> OpenClaw Gateway WebSocket 协议与 rosbridge 完全独立，iPhone 可以同时支持两种协议，但在有原生 OpenClaw Node Client 后应优先使用原生协议。

---

## 8. 与 Jetson Nano / 其他节点的协同

### 8.1 感知任务分工

| 任务 | iPhone 跑 | Nano 跑 | 说明 |
|------|-----------|---------|------|
| 实时障碍物检测 | ✅ YOLOv11n Core ML | 备用 | iPhone 节省 Nano 算力 |
| 人体检测/跟随 | ✅ Vision | — | 系统级，极快 |
| 手势指令识别 | ✅ MediaPipe | — | 33 关键点 |
| 语义场景理解 | ✅ FastVLM 0.5B | — | 本地 VLM |
| 室内 3D 建模 | ✅ LiDAR + ARKit | 可选 | iPhone 原生 |
| 复杂推理/回答 | — | ✅ | 非实时，延迟可接受 |
| 语音识别 | — | ✅ Whisper | Nano 侧统一处理 |
| 运动控制 | — | ✅ | Nano → Cyber Bricks |

### 8.2 拓扑变化

**Phase 3 前**（iPhone 通过 Nano 中转）：
```
iPhone → rosbridge → Jetson Nano → MQTT → Gateway
```

**Phase 3 后**（iPhone 直连 Gateway）：
```
iPhone ──────────────────→ Gateway → Agent（贵庚）
  ↓（感知结果 JSON，仅几百字节）
Nano ────────────────────→ Gateway
  ↓（控制指令）
Cyber Bricks / ESP32-Cam
```

---

## 9. 已知限制与风险

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| iPhone WiFi 断连 | 中 | 事件缓存， reconnect 后批量上报 |
| ANE 被其他 App 抢占 | 低 | iPhone 作为专用感知机，锁屏后保持 ARKit |
| 电池消耗 | 中 | 降低帧率（15fps 夜间模式），接入电源时全速 |
| Gateway 端口不可达 | 中 | 支持 tailnet 远程连接，或 AP 直连 |
| 协议版本不匹配 | 低 | `minProtocol`/`maxProtocol` 协商，Gateway 会拒绝旧版 |

---

## 10. 参考资料

- [OpenClaw Gateway Protocol](https://docs.openclaw.ai/gateway/protocol)
- [OpenClaw Bridge Protocol（Legacy，已废弃）](https://docs.openclaw.ai/gateway/bridge-protocol)
- `ROBOT-SOP.md` §3.4.4（rosbridge / MCP 方案）
- `ROBOT-SOP.md` §5.2（iPhone 感知前端技术方案）
- `ROBOT-SOP.md` Phase 3 章节
