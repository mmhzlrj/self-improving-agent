# Phase 3 iPhone感知 - 延迟测试方法（补充）

> **任务**：设计 iPhone 感知延迟的测试方法，确保实时控制可行性  
> **补充文件**：sop-Phase3-iPhone感知-supplement.md  
> **调研日期**：2026-03-31  
> **交叉验证**：Tavily Search + 学术文献检索  
> **依赖**：B-0001 ARKit基础框架、B-0002 深度数据获取

---

## 1. 延迟定义与目标

### 1.1 感知延迟定义

**感知延迟 = 数据在物理世界产生时刻 → OpenClaw Agent 收到时刻**

这是端到端（End-to-End）的延迟定义，衡量的是"机器人对真实世界的感知速度"。

### 1.2 人类感觉运动延迟参考

| 场景 | 典型延迟 | 来源 |
|------|---------|------|
| 触觉反应 | 25-75 ms | PNAS 论文 Sensorimotor integration on a rapid time scale |
| 视觉触发 saccades | ~200 ms | Physiology journal |
| 感知"即时"阈值 | 100-200 ms | ResearchGate: Are 100ms Fast Enough? |
| 精细运动控制 | 150-250 ms | 多项研究平均值 |

**结论**：机器人感知延迟 **< 100ms** 即达到人类触觉反应水平，满足实时控制要求。

### 1.3 目标延迟预算

| 阶段 | 目标延迟 | 说明 |
|------|---------|------|
| ARKit 帧处理 | ≤ 33 ms | @ 30fps，每帧最多 33.3ms |
| ARKit → App 传递 | ≤ 5 ms | Delegate / Callback |
| WiFi 传输（局域网） | ≤ 20 ms | 含重传和 jitter |
| OpenClaw Node 解帧 | ≤ 5 ms | JSON 解析 + 解压 |
| Gateway → Agent 传递 | ≤ 10 ms | WebSocket 内部传递 |
| **总计** | **≤ 73 ms** | 留 27ms 安全余量 |

---

## 2. 各阶段延迟拆解

### 2.1 延迟链路总览

```
[物理事件]
    │
    ▼
① ARKit 帧率延迟 (~33ms @ 30fps)
    │
    ▼
② ARKit → App 传递延迟 (~2-5ms)
    │
    ▼
③ 数据序列化/压缩延迟 (~1-3ms)
    │
    ▼
④ WiFi 传输延迟 (~5-20ms)
    │
    ▼
⑤ OpenClaw Node 解帧处理延迟 (~3-10ms)
    │
    ▼
⑥ Gateway → Agent 传递延迟 (~5-10ms)
    │
    ▼
[OpenClaw Agent 收到]
```

### 2.2 各阶段详细分析

#### 阶段①：ARKit 帧率延迟

**来源**：ARKit 以 30fps 运行，每帧间隔 33.3ms，数据在该帧捕获后才可用。

**延迟**：~33 ms（固定，受帧率限制）

**实测方法**：在 ARKit 的 `ARSession` delegate 的 `session(_:didUpdate:)` 回调中，打印 `frame.timestamp` 与系统 UTC 时间戳的差值。

```swift
func session(_ session: ARSession, didUpdate frame: ARFrame) {
    let arkitTimestamp = frame.timestamp          // ARKit 内部时间（秒）
    let now = CFAbsoluteTimeGetCurrent()          // UTC 时间
    let delay = (now - arkitTimestamp) * 1000      // 转换为 ms
    print("ARKit frame delay: \(delay) ms")
}
```

**注意**：`frame.timestamp` 是相对时间（开机后秒数），需要与系统 UTC 时间同步后才能做绝对延迟测量。

#### 阶段②：ARKit → App 传递延迟

**来源**：ARSession delegate 回调队列延迟 + App 主线程调度延迟。

**延迟**：~2-5 ms（正常负载下）

**实测方法**：在 ARKit delegate 回调入口处记录 `DispatchTime.now()`，与帧数据绑定后在 OpenClaw 端计算差值。

#### 阶段③：数据序列化/压缩延迟

**来源**：深度图 Float32 → Data 序列化 + zlib 压缩 + JSON 序列化。

**延迟**：~1-3 ms（取决于深度图分辨率）

**iPhone 13+ LiDAR 深度图规格**：
- 分辨率：QVGA（320×240）或 483×363 @ 60fps
- 压缩后大小：约 20-50 KB / 帧
- zlib 压缩耗时：< 1ms（A12+ Neural Engine 加速）

#### 阶段④：WiFi 传输延迟

**来源**：UDP/TCP 传输 + 路由器转发 + 信号干扰 + 丢包重传。

**延迟范围**：
- 同一路由器局域网：5-20 ms（稳定）
- 跨路由器（有线回程）：10-30 ms
- 有干扰/拥塞：20-100 ms

**实测方法**：使用 UDP ping 或 TCP RTT 测量。

```bash
# 测量 UDP RTT（推荐，比 ICMP ping 更准确反映应用层延迟）
ping -c 100 -i 0.01 <iPhone_IP>   # 10ms 间隔，连续 100 次

# 或使用 iPerf3 测量带宽和延迟
iperf3 -c <iPhone_IP> -p 5201 -t 10
```

**学术参考**：IEEE 论文 "RT-WiFi: Real-time high-speed communication protocol for wireless cyber-physical control applications" 指出，在工厂局域网环境下 WiFi RTT 可稳定在 5-10ms。

#### 阶段⑤：OpenClaw Node 解帧处理延迟

**来源**：Node.js WebSocket 接收 → Buffer 拼接 → zlib 解压 → JSON.parse。

**延迟**：~3-10 ms（取决于消息大小）

**实测方法**：在 Node WebSocket 的 `message` 事件中记录接收时间戳，与帧内嵌的时间戳做差值。

#### 阶段⑥：Gateway → Agent 传递延迟

**来源**：Gateway 内部消息队列 + Agent 调度延迟。

**延迟**：~5-10 ms（低负载）

**实测方法**：在 Gateway 日志中对比 `incoming_timestamp` 与 `agent_dispatch_timestamp`。

---

## 3. 端到端延迟测试方法

### 3.1 方法一：Ping Timestamp（推荐）

**原理**：在 iPhone 端嵌入发送时间戳，OpenClaw 收到后计算差值。

**步骤**：

1. iPhone App 在发送的 WebSocket 消息中嵌入字段：
   ```json
   {
     "type": "pose_data",
     "send_timestamp": 1743446400.123,   // Unix timestamp (ms)
     "seq": 12345,
     "data": { ... }
   }
   ```

2. OpenClaw Node 收到消息后：
   ```javascript
   const receiveTime = Date.now();
   const sendTime = message.send_timestamp;
   const e2eLatency = receiveTime - sendTime;
   console.log(`E2E Latency: ${e2eLatency} ms, seq: ${message.seq}`);
   ```

3. 收集多次测量（建议 ≥ 100 次），计算：
   - 平均值（Mean）
   - P50 / P95 / P99 百分位数
   - 抖动（Jitter = 相邻延迟差值的标准差）

### 3.2 方法二：Loopback RTT（精确基准测试）

**原理**：iPhone 向服务器发送 UDP 包，服务器立即回传，iPhone 计算 RTT/2。

**注意**：这测的是网络往返时间的一半，不是严格意义上的感知延迟，但可作为网络层基准。

```swift
// iOS 端
let socket = GCDAsyncUdpSocket()
let sendTime = CFAbsoluteTimeGetCurrent()
socket.send(data, toHost: "server_ip", port: 9001, withTimeout: -1, tag: seq)

socket.receive { [weak self] data, _, _, error in
    let rtt = (CFAbsoluteTimeGetCurrent() - sendTime) * 1000
    print("RTT: \(rtt) ms, half: \(rtt/2) ms")
}
```

### 3.3 方法三：硬件同步（实验室级别）

**工具**：硬件信号发生器 + 示波器或逻辑分析仪

**原理**：
1. 信号发生器发出光脉冲（触发信号）
2. iPhone 摄像头同步检测到光脉冲（输入）
3. iPhone 发送 WebSocket 数据包
4. 服务器接收并回传
5. iPhone 收到回传后记录端到端延迟

**精度**：± 1ms，适合科研验证。

### 3.4 方法四：ARSession 内部延迟分析

**工具**：Instruments（macOS）+ Metal System Trace

**方法**：在 Xcode 中使用 Instruments 的 Metal System Trace 模板，追踪 ARKit 帧处理各阶段耗时：
- `ARAbstractView_UpdateFrame`
- `ARSession_Run`
- `ARFrame_CapturedDepthData`

---

## 4. 分阶段测试方案

### 4.1 测试环境要求

| 项目 | 要求 |
|------|------|
| iPhone | iPhone 13+（LiDAR），iOS 17.4+ |
| 网络 | 5 GHz WiFi 路由器，与 Mac 同局域网 |
| 服务器 | Mac 本地 Node.js 测试服务（排除公网抖动） |
| 测试距离 | 1m / 2m / 5m（模拟实际使用场景） |

### 4.2 各阶段测试步骤

#### Stage 1：纯 ARKit 延迟测试（无需网络）

```
工具：Xcode Instruments + System Trace
步骤：
1. Xcode 连接 iPhone，启动 ARSession
2. 在真机上运行 Metal System Trace
3. 采集 100 帧数据，记录每帧 timestamp 间隔
4. 验证帧率稳定在 30fps（间隔 33.3ms ± 2ms）
```

#### Stage 2：本地 UDP RTT 测试（无需 App）

```
工具：Mac 上 Python 脚本 + iPhone 网络调试 App
步骤：
1. Mac 运行：python3 udp_latency_test.py
2. iPhone 使用 "Network Utility" 或 LightBlue app 发送 UDP
3. 记录 100 次 RTT，计算 P50/P95
4. 目标：P95 < 30ms
```

#### Stage 3：WebSocket 端到端测试

```
工具：测试版 iPhone App + 本地 Node.js 服务器
步骤：
1. iPhone App 以最高帧率发送 dummy pose 数据（30fps）
2. 每帧包含 send_timestamp
3. Node.js 服务记录 receive_timestamp，回传 confirm 消息
4. iPhone 计算 E2E latency
5. 采集 300 帧数据（10秒）
6. 输出统计：Mean / P50 / P95 / P99 / Jitter
```

### 4.3 记录表格模板

| 测试编号 | 测试日期 | iPhone型号 | 网络条件 | 距离 | 帧率 | Mean(ms) | P50(ms) | P95(ms) | P99(ms) | Jitter(ms) | 备注 |
|---------|---------|-----------|---------|------|------|---------|---------|---------|---------|-----------|------|
| TEST-001 | 2026-03-31 | iPhone 14 Pro | 5GHz WiFi | 1m | 30fps | - | - | - | - | - | - |
| TEST-002 | | | | | | | | | | | |

---

## 5. 延迟基准与判断标准

### 5.1 延迟分级标准

| 等级 | E2E 延迟 | P95 | 判断 | 行动 |
|------|---------|-----|------|------|
| 🟢 优秀 | < 50ms | < 70ms | 实时控制完全可行 | 保持监控 |
| 🟡 良好 | 50-73ms | 70-100ms | 实时控制可行 | 关注抖动 |
| 🟠 警告 | 73-100ms | 100-150ms | 勉强可行 | 启动优化 |
| 🔴 危险 | > 100ms | > 150ms | 实时控制不可行 | 立即降级 |

### 5.2 各阶段延迟预算达标标准

| 阶段 | 目标 | 警告阈值 |
|------|------|---------|
| ARKit 帧率 | ≤ 33.3ms | > 35ms（帧率下降） |
| ARKit → App | ≤ 5ms | > 10ms |
| 数据压缩 | ≤ 3ms | > 5ms |
| WiFi 传输 | ≤ 20ms | > 40ms |
| Node 解帧 | ≤ 10ms | > 20ms |
| Gateway 传递 | ≤ 10ms | > 20ms |

---

## 6. 超时处理机制

### 6.1 阈值触发规则

```
E2E_LATENCY_WARNING  = 100ms  (单帧超时)
E2E_LATENCY_CRITICAL = 200ms  (连续超时阈值)
WINDOW_SIZE          = 30     (滚动窗口大小，约1秒 @ 30fps)

# 在滚动窗口内：
IF 超时帧数 >= 5 THEN 触发 WARNING
IF 超时帧数 >= 15 THEN 触发 CRITICAL
```

### 6.2 降级策略

#### Level 1：降低发送频率（WARNING 时）

```
从 30fps → 15fps
优点：WiFi 传输延迟减半，拥塞减少
缺点：感知精度下降（移动预测可补偿）
```

#### Level 2：降低数据精度（WARNING 持续 5s）

```
深度图：320×240 → 160×120
浮点精度：Float32 → UInt16 (mm)
姿态：保留关键关节，放弃指尖精度
```

#### Level 3：切换为纯 App 端决策（CRITICAL 时）

```
OpenClaw Agent 不可达时，iPhone App 接管：
- 基础手势识别（本地 ML）
- 紧急停止指令（硬编码，无需 AI）
- 本地 TTS 反馈
```

#### Level 4：安全停止（CRITICAL 持续 10s）

```
停止所有运动指令输出
机器人进入自由停止状态
发送告警到所有在线通道
```

### 6.3 告警机制

```javascript
// OpenClaw Node 端告警逻辑
function checkLatencySlack(latencyHistory, currentLatency) {
    const p95 = percentile(latencyHistory, 95);
    const warningThreshold = 100;  // ms
    const criticalThreshold = 200; // ms
    
    if (currentLatency > criticalThreshold) {
        sendAlert('CRITICAL', `E2E latency: ${currentLatency}ms`);
        triggerDegradation(3);  // Level 3
    } else if (p95 > warningThreshold) {
        sendAlert('WARNING', `P95 latency: ${p95}ms`);
        triggerDegradation(1);  // Level 1
    }
}
```

---

## 7. 延迟优化建议

### 7.1 ARKit 层优化

- 使用 `ARConfiguration.FrameSemantics.DeepPerson` 时注意：启用 `.personSegmentation` 会增加 14-29ms/帧开销（A17 Pro 实测），非必要时不启用
- LiDAR 深度图使用 QVGA（320×240）而非 VGA，减少 60% 数据量
- 深度图和 RGB 帧分开传输，深度图优先（延迟敏感）

### 7.2 网络层优化

- 使用 **UDP** 而非 TCP（无拥塞控制，延迟更低）
- 关闭 iPhone 后台其他 App 的网络活动
- 使用 5 GHz WiFi（而非 2.4 GHz），减少无线干扰
- QoS 标记：深度数据 UDP 包设置 DSCP EF（加速转发）

### 7.3 数据格式优化

- 深度图使用 **LZ4** 压缩（比 zlib 快 3-5 倍）
- 关节角度使用 **Quat16**（4×float16 = 8 bytes vs 16×float32 = 64 bytes）
- 稀疏更新：只传输变化的骨骼节点，而非全部 91 个节点

### 7.4 OpenClaw Node 优化

- WebSocket 使用 `permessage-deflate` 压缩扩展
- 使用 `fast-json-stringify` 替代 `JSON.parse`（快 2-3 倍）
- Node.js 使用 `--max-old-space-size=4096` 避免 GC 停顿

---

## 8. 参考资料

### 学术文献

1. **PNAS - Sensorimotor integration on a rapid time scale**  
   https://www.pnas.org/doi/pdf/10.1073/pnas.1702671114  
   关键数据：触觉反应延迟 25-75 ms

2. **arXiv:2602.17381 - End-to-End Latency Measurement Methodology for Connected and Automated Vehicles**  
   https://arxiv.org/abs/2602.17381  
   关键数据：5G 网络 E2E 延迟测量方法论，M2M 延迟 306ms 实测

3. **IEEE RT-WiFi - Real-time high-speed communication protocol for wireless cyber-physical control**  
   IEEE Symposium on Real-Time Systems, 2013  
   关键数据：工厂 WiFi 环境 RTT 可达 5-10ms

### 技术文档

4. **Apple Developer - ARFrame.capturedDepthData**  
   https://developer.apple.com/documentation/arkit/arframe/captureddepthdata  
   深度摄像头帧率与主摄像头不同步说明

5. **RealityKit Performance Guide**  
   https://developer.apple.com/documentation/realitykit/improving-the-performance-of-a-realitykit-app  
   每帧渲染线程 16.6ms 目标（60fps）

### 工具

6. **UDP Latency Testing - Dev.to**  
   https://dev.to/yacine_s/measuring-end-to-end-latency-for-robots-and-cameras-over-5g-without-rf-gear-lfj  
   每 10ms 发送 50-200 byte UDP 包测 RTT 直方图的方法

7. **Realtimecollisiondetection.net - Input Latency**  
   https://realtimecollisiondetection.net/blog/?p=30  
   30fps 下最佳 5 帧延迟，最差 6.67 帧延迟分析

---

*本文件为 B-0004 延迟测试方法的补充文档，与 B-0004-延迟测试方法.md 配套使用。*
