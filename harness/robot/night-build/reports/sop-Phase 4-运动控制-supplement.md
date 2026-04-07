# Phase 4 运动控制模块 · MQTT 主题设计补充

> 补充时间：2026-03-30  
> 对应主文档：harness/robot/ROBOT-SOP.md · Phase 4

---

## §4.1 MQTT Topic 命名规范

### 4.1.1 命名规则总览

| 层级 | 字段 | 说明 | 示例 |
|------|------|------|------|
| Level 1 | 根命名空间 | 系统前缀 | `robot` |
| Level 2 | 机器人编号 | 多机序号（+ 匹配任意） | `0-1`, `0-2`, `+` |
| Level 3 | 设备类型 | 具体设备 | `cyberbrick`, `jetson`, `esp32` |
| Level 4 | 消息方向 | 命令/状态/广播 | `cmd`, `status`, `event` |
| Level 5 | 子类别 | 具体执行器 | `motor`, `servo`, `stop` |

### 4.1.2 标准 Topic 模板

```
robot/{robot_id}/{device_type}/{direction}/{actuator}
```

**命名约束：**
- 仅使用小写字母、数字、`-`、`_`
- 禁止使用中文、空格、特殊符号
- 层级不超过 5 层（超过则用 `_` 下划线合并）
- 单条消息体不超过 256KB（MQTT 协议限制）

### 4.1.3 本项目 Topic 清单

| Topic（发布→订阅） | 方向 | QoS | 说明 |
|---|---|---|---|
| `robot/0-1/cyberbrick/cmd/motor` | OpenClaw → Cyber Brick 1 | 1 | 电机控制 |
| `robot/0-1/cyberbrick/cmd/servo` | OpenClaw → Cyber Brick 1 | 1 | 舵机控制 |
| `robot/0-1/cyberbrick/cmd/stop` | OpenClaw → Cyber Brick 1 | 2 | 紧急停止（最高可靠） |
| `robot/0-1/cyberbrick/status/heartbeat` | Cyber Brick 1 → OpenClaw | 0 | 心跳存活 |
| `robot/0-1/cyberbrick/status/execute` | Cyber Brick 1 → OpenClaw | 1 | 执行结果回传 |
| `robot/0-2/cyberbrick/cmd/motor` | OpenClaw → Cyber Brick 2 | 1 | 备用机电机控制 |
| `robot/+/cyberbrick/cmd/stop` | OpenClaw → 所有 Cyber Brick | 2 | 广播紧急停止 |
| `robot/+/event/estop` | 全设备 → 所有订阅者 | 2 | 全局应急广播 |
| `robot/0-1/jetson/cmd/uart-forward` | OpenClaw → Jetson Nano | 1 | UART 透传指令 |
| `robot/0-1/esp32/cmd/camera` | OpenClaw → ESP32-Cam | 0 | 拍照指令（可丢） |

### 4.1.4 通配符使用场景

| 通配符 | 示例 | 用途 |
|--------|------|------|
| `+` 单级 | `robot/+/cyberbrick/cmd/stop` | 向所有 Cyber Brick 广播急停 |
| `#` 多级 | `robot/0-1/#` | 订阅 0-1 号机器人的所有消息（调试用） |

> ⚠️ **禁止在生产环境订阅 `#`**，会导致客户端收到大量无关消息，增加 CPU/内存压力。

---

## §4.2 订阅 / 发布消息格式（JSON Schema）

### 4.2.1 电机控制指令 `robot/+/cyberbrick/cmd/motor`

**发布方向：** OpenClaw → Cyber Brick  
**QoS：** 1（至少一次送达）

```json
{
  "type": "motor",
  "robot_id": "0-1",
  "timestamp": 1743321600000,
  "payload": {
    "channel": 1,
    "speed": 75,
    "duration_ms": 2000
  }
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定为 `motor` |
| `robot_id` | string | ✅ | 机器人编号，与 Topic 中的 `robot_id` 必须一致 |
| `timestamp` | integer | ✅ | 毫秒级 Unix 时间戳，用于去重 |
| `payload.channel` | integer | ✅ | 电机通道号（1-4） |
| `payload.speed` | integer | ✅ | 速度值 -100 ~ 100（负数=后退） |
| `payload.duration_ms` | integer | ❌ | 执行时长（ms），到达后自动停止。默认 0（持续） |

**JSON Schema：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["type", "robot_id", "timestamp", "payload"],
  "properties": {
    "type": { "const": "motor" },
    "robot_id": { "type": "string", "pattern": "^[0-9]+-[0-9]+$" },
    "timestamp": { "type": "integer", "minimum": 0 },
    "payload": {
      "type": "object",
      "required": ["channel", "speed"],
      "properties": {
        "channel": { "type": "integer", "minimum": 1, "maximum": 4 },
        "speed": { "type": "integer", "minimum": -100, "maximum": 100 },
        "duration_ms": { "type": "integer", "minimum": 0, "maximum": 30000 }
      }
    }
  }
}
```

---

### 4.2.2 舵机控制指令 `robot/+/cyberbrick/cmd/servo`

```json
{
  "type": "servo",
  "robot_id": "0-1",
  "timestamp": 1743321600000,
  "payload": {
    "channel": 1,
    "angle": 90,
    "duration_ms": 1000
  }
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `payload.channel` | integer | ✅ | 舵机通道号（1-4） |
| `payload.angle` | integer | ✅ | 角度 0 ~ 180 |
| `payload.duration_ms` | integer | ❌ | 执行时长（渐变到达），默认 500ms |

**JSON Schema：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["type", "robot_id", "timestamp", "payload"],
  "properties": {
    "type": { "const": "servo" },
    "robot_id": { "type": "string", "pattern": "^[0-9]+-[0-9]+$" },
    "timestamp": { "type": "integer", "minimum": 0 },
    "payload": {
      "type": "object",
      "required": ["channel", "angle"],
      "properties": {
        "channel": { "type": "integer", "minimum": 1, "maximum": 4 },
        "angle": { "type": "integer", "minimum": 0, "maximum": 180 },
        "duration_ms": { "type": "integer", "minimum": 0, "maximum": 10000 }
      }
    }
  }
}
```

---

### 4.2.3 紧急停止指令 `robot/+/cyberbrick/cmd/stop`

**QoS：** 2（恰好一次送达，确保急停不重复不错漏）  
**retained：** `true`（断线重连后仍保持停止状态）

```json
{
  "type": "stop",
  "robot_id": "0-1",
  "timestamp": 1743321600000,
  "payload": {
    "reason": "user_emergency",
    "estop_gpio_triggered": false
  }
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `payload.reason` | string | ✅ | 停止原因：`user_emergency` / `software_watchdog` / `uart_timeout` |
| `payload.estop_gpio_triggered` | boolean | ✅ | 是否由 GPIO 硬件触发（若为 true 说明软件通道已不可靠） |

---

### 4.2.4 执行状态回传 `robot/+/cyberbrick/status/execute`

**发布方向：** Cyber Brick → OpenClaw / Jetson Nano  
**QoS：** 1

```json
{
  "type": "execute_result",
  "robot_id": "0-1",
  "timestamp": 1743321600500,
  "payload": {
    "original_cmd_type": "motor",
    "original_timestamp": 1743321600000,
    "status": "completed",
    "actual_speed": 74,
    "error_code": 0,
    "error_message": null
  }
}
```

**`status` 枚举值：**

| 值 | 说明 |
|----|------|
| `completed` | 执行成功 |
| `aborted` | 被急停中断 |
| `error` | 执行出错（看 `error_code`） |
| `timeout` | UART 超时未响应 |

**`error_code` 枚举值：**

| 值 | 说明 |
|----|------|
| `0` | 无错误 |
| `1001` | 通道号无效 |
| `1002` | 速度超出范围 |
| `1003` | 角度超出范围 |
| `2001` | UART 通信失败 |
| `2002` | UART 校验错误 |
| `9001` | 急停触发中断 |

---

### 4.2.5 心跳消息 `robot/+/cyberbrick/status/heartbeat`

**发布方向：** Cyber Brick → OpenClaw  
**QoS：** 0（可丢，轻量）  
**retained：** `false`

```json
{
  "type": "heartbeat",
  "robot_id": "0-1",
  "timestamp": 1743321600000,
  "payload": {
    "firmware_version": "1.2.3",
    "uptime_seconds": 3600,
    "wifi_rssi": -65,
    "free_heap_kb": 180,
    "motor_status": [0, 0, 0, 0],
    "servo_status": [90, 90, 90, 90]
  }
}
```

> **心跳间隔：** 每 5 秒一次  
> **超时判定：** OpenClaw 超过 15 秒未收到心跳 → 标记为 `offline`，触发重连

---

## §4.3 QoS 等级选择策略

| QoS 等级 | 描述 | 适用场景 | 注意事项 |
|----------|------|----------|----------|
| **QoS 0** | 最多一次（At most once） | 传感器数据流、拍照指令、调试日志 | 可能丢消息，不重试 |
| **QoS 1** | 至少一次（At least once） | 电机/舵机控制指令、执行结果回传 | 可能重复（需业务层去重） |
| **QoS 2** | 恰好一次（Exactly once） | 紧急停止指令、计费数据 | 开销最大，避免滥用 |

### 4.3.1 本项目 QoS 选择依据

```
急停指令  → QoS 2   原因：不允许丢失，也绝对不能重复（重复急停=误操作）
普通指令  → QoS 1   原因：容忍重复（业务层用 timestamp 去重），不允许丢
心跳      → QoS 0   原因：丢了无所谓，下一个心跳会补上
状态回传  → QoS 1   原因：丢了的话下一次执行会覆盖
调试日志  → QoS 0   原因：丢了无所谓
```

### 4.3.2 MicroPython (ESP32) QoS 设置示例

```python
import paho.mqtt.client as mqtt

# QoS 1：普通指令
client.publish("robot/0-1/cyberbrick/cmd/motor",
               payload=str(cmd_dict),
               qos=1)

# QoS 2：急停
client.publish("robot/0-1/cyberbrick/cmd/stop",
               payload=str(stop_dict),
               qos=2,
               retain=True)

# QoS 0：心跳
client.publish("robot/0-1/cyberbrick/status/heartbeat",
               payload=str(heartbeat_dict),
               qos=0)
```

---

## §4.4 Retained 消息使用场景

**Retained 消息**：Broker 会为每个 Topic 保留最新一条消息，新订阅者连接后立即收到该消息。

### 4.4.1 Retained 使用场景

| Topic | retained | 原因 |
|-------|----------|------|
| `robot/+/cyberbrick/cmd/stop` | `true` | 新连接的从机必须知道当前是否处于停止状态 |
| `robot/+/cyberbrick/status/last-will` | `true` | 记录设备最后在线状态 |
| `robot/+/cyberbrick/cmd/motor` | `false` | 普通控制指令不保留 |
| `robot/+/cyberbrick/status/heartbeat` | `false` | 心跳不保留（失效快） |

### 4.4.2 Retained 急停示例

当 OpenClaw 发出急停时，Broker 保留该消息。此后：
1. Cyber Brick 重启 → 连接 → 立即收到 retained 急停 → 保持停止
2. 新的 Cyber Brick 加入网络 → 立即收到急停 → 不会误动作

```python
# Cyber Brick 侧：订阅急停 topic（retained=True）
client.subscribe("robot/+/cyberbrick/cmd/stop", qos=2)
# 新连接后，broker 会立即推送保留的急停消息，防止启动时误动作
```

---

## §4.5 Cyber Bricks ESP32 的 MQTT Client ID 设计

### 4.5.1 Client ID 命名规范

```
cyberbrick_{robot_id}_{device_role}_{mac_last4}
```

**字段说明：**

| 字段 | 格式 | 示例 | 说明 |
|------|------|------|------|
| `cyberbrick` | 固定前缀 | `cyberbrick` | 标识设备类型 |
| `robot_id` | `{n}-{n}` | `0-1` | 机器人编号 |
| `device_role` | `primary` / `backup` | `primary` | 主/备角色 |
| `mac_last4` | 十六进制 | `a1b2` | ESP32 MAC 地址后 4 位（保证唯一性） |

**示例：**
- Cyber Brick 1 主设备：`cyberbrick_0-1_primary_a1b2`
- Cyber Brick 2 备用设备：`cyberbrick_0-1_backup_c3d4`

### 4.5.2 为什么用 MAC 后缀

- ESP32 每次启动 WiFi 重连后，IP 可能变化，但 MAC 地址固定
- 防止 ESP32 重启后 Client ID 冲突导致旧连接被踢下线
- 在多个 ESP32 共存的调试环境中（同一 Broker），每个设备 Client ID 唯一

### 4.5.3 MicroPython Client ID 获取

```python
import network
import ubinascii

sta = network.WLAN(network.STA_IF)
mac = ubinascii.hexlify(sta.config('mac')).decode()  # 如 'b8d61a1b2c3d'
mac_last4 = mac[-4:]  # 如 'a1b2'
client_id = f"cyberbrick_0-1_primary_{mac_last4}"
print(f"Client ID: {client_id}")
```

### 4.5.4 Client ID 与 Clean Session

| 场景 | `clean_session` | 说明 |
|------|-----------------|------|
| 持久连接（生产） | `False` | 保留会话，QoS 1/2 消息不丢 |
| 临时调试连接 | `True` | 每次断开清除会话 |
| ESP32 断电重连 | `False` | 确保离线期间的消息在重连后补发 |

> ⚠️ **ESP32 使用 `clean_session=False`**：因为 ESP32 可能随时断电，必须保证重连后能收到 QoS 1/2 的补发消息。

---

## §4.6 Last Will & Testament (LWT) 配置

### 4.6.1 LWT 的作用

当 Cyber Brick **异常断开**（非主动 DISCONNECT）时，Broker 自动向指定 Topic 推送 LWT 消息，通知其他组件该设备已下线。

**典型触发场景：**
- ESP32 死机/断电
- WiFi 信号中断
- 程序崩溃（未发送 DISCONNECT）

### 4.6.2 LWT Topic 选择

| LWT Topic | retained | 说明 |
|-----------|----------|------|
| `robot/+/event/estop` | `true` | 设备下线本身是一种事件 |

当 Cyber Brick 向 Broker 发送 LWT 消息时，等同于广播"我出问题了"，OpenClaw 立即感知并采取行动。

### 4.6.3 LWT 消息格式

```json
{
  "type": "lwt",
  "robot_id": "0-1",
  "timestamp": 1743321600000,
  "payload": {
    "reason": "unexpected_disconnect",
    "client_id": "cyberbrick_0-1_primary_a1b2",
    "last_seen": 1743321595000,
    "last_cmd_type": "motor",
    "last_cmd_timestamp": 1743321590000
  }
}
```

**`reason` 枚举值：**

| 值 | 说明 |
|----|------|
| `unexpected_disconnect` | 非预期断开（最常见 = 设备故障） |
| `wifi_lost` | WiFi 连接丢失 |
| `mqtt_timeout` | MQTT PING 超时 |
| `oom` | 内存耗尽重启 |
| `watchdog` | 硬件看门狗复位 |

### 4.6.4 MicroPython LWT 配置

```python
import paho.mqtt.client as mqtt
import ujson

LWT_TOPIC = "robot/0-1/event/estop"
LWT_PAYLOAD = ujson.dumps({
    "type": "lwt",
    "robot_id": "0-1",
    "timestamp": 0,  # 占位，运行时更新
    "payload": {
        "reason": "unexpected_disconnect",
        "client_id": f"cyberbrick_0-1_primary_{mac_last4}",
        "last_seen": 0,
        "last_cmd_type": None,
        "last_cmd_timestamp": None
    }
})

mqtt_client = mqtt.Client(
    client_id=f"cyberbrick_0-1_primary_{mac_last4}",
    clean_session=False
)

# 设置 LWT（关键！）
mqtt_client.will_set(
    topic=LWT_TOPIC,
    payload=LWT_PAYLOAD,
    qos=2,
    retain=True
)

mqtt_client.on_message = on_message
mqtt_client.connect("192.168.x.x", 1883, keepalive=30)
mqtt_client.subscribe("robot/0-1/cyberbrick/cmd/#", qos=1)
mqtt_client.loop_start()
```

### 4.6.5 OpenClaw 端 LWT 监听处理

```python
import paho.mqtt.client as mqtt
import ujson

def on_lwt(client, userdata, msg):
    try:
        lwt = ujson.loads(msg.payload)
        robot_id = lwt.get("robot_id", "unknown")
        reason = lwt["payload"]["reason"]
        print(f"[LWT] Robot {robot_id} disconnected: {reason}")
        # 触发应急处理：
        # 1. 记录日志
        # 2. 通知上层（网关/SOP）
        # 3. 尝试通过 GPIO 硬件急停
    except Exception as e:
        print(f"[LWT] Parse error: {e}")

mqtt_client = mqtt.Client()
mqtt_client.on_message = on_lwt
mqtt_client.connect("192.168.x.x", 1883)
mqtt_client.subscribe("robot/+/event/estop", qos=2)
mqtt_client.loop_start()
```

### 4.6.6 LWT 与 Keepalive

- **Keepalive：** Cyber Brick 每 30 秒向 Broker 发送一次 PING。超过 1.5× keepalive（45 秒）无响应，Broker 判定为离线并发送 LWT。
- **建议值：** `keepalive=30`（30 秒），适合 ESP32 低功耗场景。

---

## §4.7 消息去重策略（业务层）

由于 QoS 1 可能导致消息重复到达，业务层需要去重。

### 4.7.1 去重方案：时间戳 + 滑动窗口

```python
import time

class Deduplicator:
    """基于时间戳的滑动窗口去重"""
    def __init__(self, window_seconds=5):
        self.window_seconds = window_seconds
        self.seen = {}  # {timestamp: True}

    def is_duplicate(self, timestamp):
        now = time.time()
        # 清理过期条目
        self.seen = {t: v for t, v in self.seen.items() if now - t < self.window_seconds}
        if timestamp in self.seen:
            return True
        self.seen[timestamp] = True
        return False

dedup = Deduplicator(window_seconds=5)

def on_message(topic, msg):
    cmd = ujson.loads(msg)
    ts = cmd.get("timestamp", 0)
    if dedup.is_duplicate(ts):
        print(f"[DEDUP] Discard duplicate: {cmd}")
        return
    execute_command(cmd)
```

---

## §4.8 完整订阅 / 发布矩阵

| Topic | Publisher | Subscriber(s) | QoS | retained |
|-------|-----------|----------------|-----|----------|
| `robot/0-1/cyberbrick/cmd/motor` | OpenClaw | Cyber Brick 1 | 1 | false |
| `robot/0-1/cyberbrick/cmd/servo` | OpenClaw | Cyber Brick 1 | 1 | false |
| `robot/0-1/cyberbrick/cmd/stop` | OpenClaw | Cyber Brick 1, Cyber Brick 2 | 2 | **true** |
| `robot/0-2/cyberbrick/cmd/motor` | OpenClaw | Cyber Brick 2 | 1 | false |
| `robot/+/cyberbrick/cmd/stop` | OpenClaw | All Cyber Bricks | 2 | **true** |
| `robot/0-1/cyberbrick/status/execute` | Cyber Brick 1 | OpenClaw, Jetson Nano | 1 | false |
| `robot/0-1/cyberbrick/status/heartbeat` | Cyber Brick 1 | OpenClaw | 0 | false |
| `robot/0-2/cyberbrick/status/execute` | Cyber Brick 2 | OpenClaw | 1 | false |
| `robot/+/event/estop` | Broker (LWT) | OpenClaw, Jetson Nano | 2 | **true** |
| `robot/0-1/jetson/cmd/uart-forward` | OpenClaw | Jetson Nano | 1 | false |
| `robot/+/cyberbrick/cmd/camera` | OpenClaw | ESP32-Cam | 0 | false |

---

*本文档为 ROBOT-SOP.md Phase 4 的补充内容，与主文档配套使用。*

---

## §4.9 UART 有线协议格式（Wire-level Serial Protocol）

### 4.9.1 为什么需要 UART 层

MQTT 是 OpenClaw ↔ Jetson Nano 之间的协议，而 **Jetson Nano ↔ Cyber Bricks** 之间使用 UART 有线连接作为第二跳。Jetson Nano 充当 MQTT-UART 网关，将 MQTT 消息转换为 UART 字节流。

```
OpenClaw → MQTT → Jetson Nano → UART → Cyber Brick
```

### 4.9.2 UART 参数

| 参数 | 值 |
|------|------|
| 波特率 | 115200 bps |
| 数据位 | 8 |
| 停止位 | 1 |
| 校验位 | 无 |
| 流控制 | 无 |

### 4.9.3 UART 帧格式

每帧格式：`[STX][CMD][LEN][DATA...][CRC8][ETX]`

| 字段 | 长度 | 说明 |
|------|------|------|
| `STX` | 1 byte | 帧起始标志，`0xAA` |
| `CMD` | 1 byte | 命令类型 |
| `LEN` | 1 byte | DATA 长度（不含头尾） |
| `DATA` | N bytes | 数据负载 |
| `CRC8` | 1 byte | CRC-8/ITU 校验（覆盖 CMD+LEN+DATA） |
| `ETX` | 1 byte | 帧结束标志，`0x55` |

### 4.9.4 CMD 指令码定义

| CMD (hex) | 名称 | 说明 | DATA 格式 |
|-----------|------|------|-----------|
| `0x01` | `MOTOR_SET` | 设置单通道电机速度 | `[ch(1)][speed(1)]` |
| `0x02` | `SERVO_SET` | 设置单通道舵机角度 | `[ch(1)][angle(1)]` |
| `0x03` | `MOTOR_ALL` | 同时设置 4 通道电机 | `[spd1][spd2][spd3][spd4]` |
| `0x04` | `SERVO_ALL` | 同时设置 4 通道舵机 | `[ang1][ang2][ang3][ang4]` |
| `0x05` | `STOP_ALL` | 停止所有电机和舵机 | 无 |
| `0x06` | `SEQ_RUN` | 执行预设动作序列 | `[seq_id(1)]` |
| `0x07` | `STATUS_QUERY` | 查询当前状态 | 无 |
| `0x08` | `FW_VERSION` | 查询固件版本 | 无 |
| `0xFE` | `SYNC_STOP` | 同步停止（带确认） | 无 |
| `0xFF` | `RESET` | 软件复位 | 无 |

### 4.9.5 DATA 字段编码

**电机速度 (1 byte signed):**
```
0x00       = 停止（0）
0x01~0x64  = 正转 1~100 (1%=1, 100%=100)
0x65~0xC8  = 保留
0xC9~0xFF  = 反转 195~255 (-100=-55, -1=-1)
```
换算公式：
- 正转：`speed = raw`
- 反转：`speed = raw - 256`（即 raw = 256 + speed）

**舵机角度 (1 byte):**
```
0x00~0xB4  = 角度 0°~180°（直接映射）
```

### 4.9.6 CRC-8/ITU 计算（Python 示例）

```python
def crc8_itu(data: bytes) -> int:
    """CRC-8/ITU 多项式: x^8 + x^2 + x + 1 (0x07)"""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x07
            else:
                crc <<= 1
        crc &= 0xFF
    return crc

def build_frame(cmd: int, data: bytes) -> bytes:
    """构建完整 UART 帧"""
    payload = bytes([cmd, len(data)]) + data
    crc = crc8_itu(payload)
    return bytes([0xAA]) + payload + bytes([crc, 0x55])
```

### 4.9.7 指令示例

**例1：电机1 正转 50%**
```
Frame: AA 01 02 01 32 7D 55
       |  |  |  |  |   |  |
       STX CMD LEN CH SPEED CRC ETX
```
计算：CMD=0x01, LEN=0x02, DATA=`[0x01, 0x32]`, payload=`[0x01, 0x02, 0x01, 0x32]`, CRC=0x7D

**例2：舵机2 转到 90°**
```
Frame: AA 02 02 02 5A 19 55
       |  |  |  |  |   |  |
       STX CMD LEN CH ANGLE CRC ETX
```
`0x5A` = 90（十进制）

**例3：同步停止（带 CRC 确认）**
```
Frame: AA FE 00 00 FE 55
       |  |  |  |  |  |
       STX CMD LEN CRC CRC ETX
```
`CMD=0xFE`（SYNC_STOP），LEN=0x00，`CRC=crc8_itu([0xFE, 0x00])=0xFE`

### 4.9.8 Jetson Nano UART 网关示例

```python
import serial
import paho.mqtt.client as mqtt
import ujson

SERIAL_PORT = "/dev/ttyTHS1"  # Jetson Nano UART
BAUD_RATE = 115200

def uart_send(cmd: int, data: bytes = b""):
    """通过 UART 发送帧到 Cyber Brick"""
    frame = build_frame(cmd, data)
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        ser.write(frame)
        # 等待响应（SYNC_STOP 需要确认）
        if cmd == 0xFE:
            resp = ser.read(6)
            if resp[1] == 0xFE:
                print("[UART] STOP acknowledged")

def mqtt_to_uart(topic: str, payload: dict):
    """将 MQTT JSON 指令转换为 UART 帧"""
    cmd_type = payload.get("type")
    p = payload.get("payload", {})

    if cmd_type == "motor":
        ch = p.get("channel", 1)
        speed = p.get("speed", 0)
        uart_send(0x01, bytes([ch, speed if speed >= 0 else 256 + speed]))
    elif cmd_type == "servo":
        ch = p.get("channel", 1)
        angle = p.get("angle", 90)
        uart_send(0x02, bytes([ch, angle]))
    elif cmd_type == "stop":
        uart_send(0xFE)  # SYNC_STOP
    elif cmd_type == "motor_all":
        speeds = p.get("speeds", [0, 0, 0, 0])
        data = bytes([s if s >= 0 else 256 + s for s in speeds])
        uart_send(0x03, data)
    elif cmd_type == "seq_run":
        uart_send(0x06, bytes([p.get("seq_id", 0)]))

def on_mqtt_message(client, userdata, msg):
    try:
        payload = ujson.loads(msg.payload)
        mqtt_to_uart(msg.topic, payload)
    except Exception as e:
        print(f"[Gateway] Error: {e}")

mqtt_client = mqtt.Client()
mqtt_client.on_message = on_mqtt_message
mqtt_client.connect("192.168.x.x", 1883)
mqtt_client.subscribe("robot/0-1/cyberbrick/cmd/#", qos=1)
mqtt_client.loop_start()
```

---

## §4.10 运动指令序列（Motion Sequence）

### 4.10.1 序列指令用途

运动序列（Sequence）是预设的多步动作组合，通过一个 `SEQ_RUN` 指令触发，适用于：
- 复杂动作（"前进 1 米 → 右转 45° → 抓取"）
- 固定流程（开机动作、复位动作）
- 实时性要求高的场景（减少 MQTT 往返延迟）

### 4.10.2 预设序列清单

| seq_id | 名称 | 描述 | 动作步骤 |
|--------|------|------|---------|
| `0` | `IDLE` | 空闲待机 | 电机停止，舵机归中 90° |
| `1` | `STARTUP` | 开机仪式 | 舵机全摆动 0→180→90，电机轻震 |
| `2` | `FORWARD_1M` | 前进 1 米 | 电机 speed=60, duration=2000ms → stop |
| `3` | `TURN_RIGHT_45` | 右转 45° | 右舵打到 45°，左舵不动，duration=500ms → 归中 |
| `4` | `TURN_LEFT_45` | 左转 45° | 左舵打到 135°，右舵不动，duration=500ms → 归中 |
| `5` | `REVERSE_0.5M` | 后退 0.5 米 | 电机 speed=-60, duration=1000ms → stop |
| `6` | `WAVE_HELLO` | 招手动作 | 舵机2 摆动 60°↔120° ×3 次 |
| `7` | `BOW` | 鞠躬 | 舵机2 从 90° → 150° → 90°，duration=1500ms |
| `8` | `ESTOP_RECOVERY` | 急停恢复 | STOP_ALL → IDLE → 等待人工确认 |
| `9` | `SHUTDOWN` | 关机 | 舵机归中 → 电机停止 → 延迟 500ms → RESET |

### 4.10.3 序列触发方式

**通过 MQTT 触发序列：**
```json
// Topic: robot/0-1/cyberbrick/cmd/seq
// QoS: 1
{
  "type": "seq_run",
  "robot_id": "0-1",
  "timestamp": 1743321600000,
  "payload": {
    "seq_id": 6
  }
}
```

**通过 UART 直接触发：**
```
Frame: AA 06 01 06 XX 55
              |  |
              SEQ_ID CRC
```
`CMD=0x06 (SEQ_RUN)`, LEN=1, DATA=`[seq_id]`, CRC=XX, ETX=0x55

### 4.10.4 自定义序列写入（Cyber Brick 固件侧）

Cyber Bricks 支持在固件中预定义序列，格式为：

```python
# Cyber Brick 固件中的序列定义
from machine import Timer

sequences = {
    0: [],  # IDLE
    1: [  # STARTUP
        {"type": "servo_all", "data": [0, 0, 0, 0], "delay": 500},
        {"type": "servo_all", "data": [180, 180, 180, 180], "delay": 500},
        {"type": "servo_all", "data": [90, 90, 90, 90], "delay": 300},
    ],
    6: [  # WAVE_HELLO
        {"type": "servo", "ch": 2, "angle": 60, "delay": 200},
        {"type": "servo", "ch": 2, "angle": 120, "delay": 200},
        {"type": "servo", "ch": 2, "angle": 60, "delay": 200},
        {"type": "servo", "ch": 2, "angle": 120, "delay": 200},
        {"type": "servo", "ch": 2, "angle": 90, "delay": 100},
    ],
}

def run_sequence(seq_id):
    seq = sequences.get(seq_id, [])
    for step in seq:
        if step["type"] == "servo":
            set_servo(step["ch"], step["angle"])
        elif step["type"] == "motor":
            set_motor(step["ch"], step["speed"])
        elif step["type"] == "servo_all":
            for i, ang in enumerate(step["data"]):
                set_servo(i+1, ang)
        utime.sleep_ms(step.get("delay", 0))
```

---

## §4.11 运动指令完整参考（Quick Reference Card）

### 4.11.1 MQTT 高层指令汇总

| 动作 | Topic | QoS | 最小 Payload |
|------|-------|-----|-------------|
| 电机正转 | `robot/0-1/cyberbrick/cmd/motor` | 1 | `{"type":"motor","robot_id":"0-1","timestamp":0,"payload":{"channel":1,"speed":50}}` |
| 电机反转 | `robot/0-1/cyberbrick/cmd/motor` | 1 | `{"type":"motor","robot_id":"0-1","timestamp":0,"payload":{"channel":1,"speed":-50}}` |
| 电机停止 | `robot/+/cyberbrick/cmd/motor` | 1 | `{"type":"motor","robot_id":"0-1","timestamp":0,"payload":{"channel":1,"speed":0}}` |
| 舵机角度 | `robot/0-1/cyberbrick/cmd/servo` | 1 | `{"type":"servo","robot_id":"0-1","timestamp":0,"payload":{"channel":1,"angle":90}}` |
| 急停 | `robot/+/cyberbrick/cmd/stop` | 2 | `{"type":"stop","robot_id":"0-1","timestamp":0,"payload":{"reason":"user_emergency","estop_gpio_triggered":false}}` |
| 序列触发 | `robot/0-1/cyberbrick/cmd/seq` | 1 | `{"type":"seq_run","robot_id":"0-1","timestamp":0,"payload":{"seq_id":1}}` |

### 4.11.2 UART 字节指令卡

| 动作 | 帧（hex） | 说明 |
|------|----------|------|
| 电机1 速50 | `AA 01 02 01 32 [CRC] 55` | ch=1, speed=50(0x32) |
| 电机2 速-30 | `AA 01 02 02 DA [CRC] 55` | ch=2, speed=-30(0xDA=218=256-38) |
| 舵机1 90° | `AA 02 02 01 5A [CRC] 55` | ch=1, angle=90(0x5A) |
| 舵机3 180° | `AA 02 02 03 B4 [CRC] 55` | ch=3, angle=180(0xB4) |
| 四电机全停 | `AA 03 04 00 00 00 00 [CRC] 55` | all speed=0 |
| 四舵归中 | `AA 04 04 5A 5A 5A 5A [CRC] 55` | all angle=90(0x5A) |
| 同步急停 | `AA FE 00 [CRC] 55` | CMD=0xFE, 需确认 |
| 软复位 | `AA FF 00 [CRC] 55` | CMD=0xFF, 无确认 |

### 4.11.3 OpenClaw Skill 指令模板

```python
#!/usr/bin/env python3
"""Cyber Bricks 运动控制 - OpenClaw Skill 封装"""
import paho.mqtt.client as mqtt
import time
import sys

MQTT_BROKER = "192.168.x.x"   # Jetson Nano (MQTT Broker)
TOPIC_MOTOR  = "robot/0-1/cyberbrick/cmd/motor"
TOPIC_SERVO  = "robot/0-1/cyberbrick/cmd/servo"
TOPIC_STOP   = "robot/+/cyberbrick/cmd/stop"
TOPIC_SEQ    = "robot/0-1/cyberbrick/cmd/seq"

def get_ts():
    return int(time.time() * 1000)

def motor(channel: int, speed: int, duration_ms: int = 0):
    """驱动电机
    channel: 1-4
    speed: -100 ~ 100（负数=反转）
    duration_ms: 0=持续, >0=执行后自动停止
    """
    payload = {
        "type": "motor",
        "robot_id": "0-1",
        "timestamp": get_ts(),
        "payload": {
            "channel": channel,
            "speed": speed,
            "duration_ms": duration_ms
        }
    }
    _publish(TOPIC_MOTOR, payload, qos=1)

def servo(channel: int, angle: int, duration_ms: int = 500):
    """驱动舵机
    channel: 1-4
    angle: 0 ~ 180
    duration_ms: 渐变到达时长，默认 500ms
    """
    payload = {
        "type": "servo",
        "robot_id": "0-1",
        "timestamp": get_ts(),
        "payload": {
            "channel": channel,
            "angle": angle,
            "duration_ms": duration_ms
        }
    }
    _publish(TOPIC_SERVO, payload, qos=1)

def stop(reason: str = "user_emergency"):
    """急停所有电机和舵机"""
    payload = {
        "type": "stop",
        "robot_id": "0-1",
        "timestamp": get_ts(),
        "payload": {
            "reason": reason,
            "estop_gpio_triggered": False
        }
    }
    _publish(TOPIC_STOP, payload, qos=2, retain=True)

def seq(seq_id: int):
    """触发预设动作序列"""
    payload = {
        "type": "seq_run",
        "robot_id": "0-1",
        "timestamp": get_ts(),
        "payload": {"seq_id": seq_id}
    }
    _publish(TOPIC_SEQ, payload, qos=1)

def _publish(topic: str, payload: dict, qos: int = 0, retain: bool = False):
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883, keepalive=30)
    import ujson
    client.publish(topic, ujson.dumps(payload), qos=qos, retain=retain)
    client.disconnect()

# CLI 入口
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "stop"
    params = sys.argv[2:] if len(sys.argv) > 2 else []

    if action == "forward":
        motor(1, 60, 2000)
    elif action == "backward":
        motor(1, -60, 2000)
    elif action == "left":
        servo(1, 45)
    elif action == "right":
        servo(1, 135)
    elif action == "wave":
        seq(6)
    elif action == "bow":
        seq(7)
    elif action == "stop":
        stop()
    else:
        print(f"Unknown action: {action}")
        print("Usage: cyberbrick_control.py [forward|backward|left|right|wave|bow|stop]")
```

**OpenClaw 调用示例（exec 方式）：**
```
用户："让机器人招手"
→ exec → python3 /path/to/cyberbrick_control.py wave

用户："往前走2秒"
→ exec → python3 /path/to/cyberbrick_control.py forward
```
（修改 `duration_ms` 参数以调整时长）

---

*补充内容：§4.9 UART 有线协议格式 · §4.10 运动指令序列 · §4.11 完整参考*

---

## §4.9 Cyber Bricks 固件结构详解

> 本节补充官方 CyberBrick Multi-Function Core Board（ESP32-C3）的固件架构信息。
> 数据来源：Bambu Lab 官方 Wiki + GitHub（CyberBrick-Official/CyberBrick_Controller_Core）+ 社区论坛逆向分析。

---

### §4.9.1 硬件规格总览

| 参数 | 规格 |
|------|------|
| 主控芯片 | ESP32-C3FH4X（RISC-V 32-bit @ 160MHz）|
| 无线通信 | Bluetooth 5.0 LE + WiFi 802.11 b/g/n（2.4GHz）|
| 固件升级 | 支持蓝牙 OTA 升级（出厂内置 Bootloader）|
| 编程方式 | MicroPython 应用层（推荐）/ 原生 ESP-IDF C/C++ |
| 官方文档 | [Bambu Lab Wiki - CyberBrick](https://wiki.bambulab.com/en/cyberbrick/components/component-list) |
| 代码仓库 | [CyberBrick-Official/CyberBrick_Controller_Core](https://github.com/CyberBrick-Official/CyberBrick_Controller_Core) |

---

### §4.9.2 模块化硬件架构

CyberBrick 采用「核心板 + 功能扩展板」的分层设计：

```
┌─────────────────────────────────────────────────────────┐
│              CyberBrick 系统架构                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐   ┌────────────────────────────┐  │
│  │ Controller Core  │   │   Multi-Function Core      │  │
│  │ (ESP32-C3FH4X)   │   │   Board -XA003             │  │
│  │  核心板           │◄──│   Type-C / 电池输入 / 用户按键  │  │
│  │  WiFi + BT       │   └────────────────────────────┘  │
│  └────────┬────────┘                                    │
│           │ UART / GPIO / PWM / I2C                      │
│           ▼                                              │
│  ┌──────────────────────────────────────────────────┐    │
│  │          Functional Shields（功能扩展板）          │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐          │    │
│  │  │ Motor    │ │ Servo   │ │ LED      │          │    │
│  │  │ Shield   │ │ Shield  │ │ Shield   │          │    │
│  │  │ XH2.54   │ │ 3-pin   │ │ WS2812   │          │    │
│  │  │ 7.4-12.6V│ │ Header  │ │ 3-pin    │          │    │
│  │  │ 2x DC    │ │ 4x Servo│ │ 2x LED   │          │    │
│  │  └─────────┘ └─────────┘ └─────────┘          │    │
│  └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

#### 核心板接口（Controller Core）

| 接口 | 规格 |
|------|------|
| Type-C | 5V 编程/供电（连接 PC） |
| 电池输入 | 3.7V–12.6V（锂电/干电池盒）|
| 复位按键 | 重启主控程序 |
| 用户按键 | 可编程自定义功能 |
| GPIO 引脚 | 详见官方 Pinout 图（GPIO 0–21）|

#### Motor Shield（电机驱动板）

| 参数 | 规格 |
|------|------|
| 电机端口 | M1、M2（2-pin SH1.0 母头）|
| 电机类型 | 有刷直流电机 |
| 驱动芯片 | Heroic HTD8811（双 H 桥）|
| 控制方式 | 每路电机 2 个 GPIO（PWM + 方向）|
| 输入电压 | 7.4V–12.6V（XH2.54 供电口）|
| 最大电流 | 3A（持续）|
| PWM 调速 | 支持正转/反转/刹车 |

#### Servo Shield（舵机驱动板）

| 参数 | 规格 |
|------|------|
| 舵机端口 | S1–S4（3-pin 标准舵机接口）|
| 供电电压 | 5V（核心板供电）|
| 控制信号 | PWM（50Hz，0.5–2.5ms 脉宽）|
| 角度范围 | 0°–180°（标准舵机）|

#### LED Shield

| 参数 | 规格 |
|------|------|
| LED 端口 | D1、D2（3-pin SH1.0 母头）|
| 协议支持 | WS2812（单线串行 RGB）|
| 单端口灯数 | 可接整条 LED 灯带 |

---

### §4.9.3 官方固件架构（MicroPython）

CyberBrick 官方固件基于 MicroPython，分为两种应用模式：

#### 应用目录结构

```
CyberBrick_Controller_Core/
├── src/
│   ├── app_rc/              # 遥控器（RC）应用
│   │   ├── boot.py          # 启动入口
│   │   ├── app/
│   │   │   ├── rc_main.py   # RC 主程序（开机自动加载）
│   │   │   ├── rc_config.py # 配置文件
│   │   │   ├── control.py   # 控制逻辑
│   │   │   └── parse.py     # 遥控信号解析
│   │   └── bbl/             # Basic Battery Library（基础驱动）
│   │       ├── motors.py    # 电机驱动（HTD8811）
│   │       ├── parser.py    # 协议解析
│   │       └── ...
│   └── app_timelapse/       # 延时摄影套件应用
└── requirements.txt
```

#### 启动流程

```
上电 / 复位
    │
    ▼
boot.py  （固化在 Flash，勿修改）
    │
    ▼
app/rc_main.py  （用户自定义应用入口）
    │
    ▼
rc_config.py  （加载用户配置）
    │
    ├── 初始化 GPIO / UART / PWM
    ├── 连接 WiFi / Bluetooth
    └── 进入主循环（监听遥控信号 or MQTT）
```

#### 关键驱动文件

**bbl/motors.py**（官方电机驱动）

```python
# CyberBrick_Controller_Core/src/app_rc/bbl/motors.py
# 驱动 Heroic HTD8811 双 H 桥驱动芯片
# 每路电机需要 2 个 GPIO：
#   - PWM 引脚：控制速度（0-100%）
#   - DIR 引脚：控制方向（正/反/刹车）
#
# ESP32-C3 GPIO 映射（Motor Shield XH2.54）：
#   M1: GPIO_X (PWM) + GPIO_Y (DIR)
#   M2: GPIO_Z (PWM) + GPIO_W (DIR)

from machine import Pin, PWM

class DCMotor:
    def __init__(self, pwm_pin, dir_pin, freq=1000):
        self.pwm = PWM(Pin(pwm_pin), freq=freq)
        self.dir = Pin(dir_pin, Pin.OUT)

    def set_speed(self, speed):
        """speed: -100 ~ 100，负数=反转"""
        if speed > 0:
            self.dir.value(1)
            self.pwm.duty(abs(speed))
        elif speed < 0:
            self.dir.value(0)
            self.pwm.duty(abs(speed))
        else:
            self.pwm.duty(0)  # 刹车

    def brake(self):
        self.pwm.duty(0)
```

---

### §4.9.4 通信机制

#### 无线通信协议栈

| 层级 | 协议 | 说明 |
|------|------|------|
| 应用层 | 自定义 RC 协议 | 遥控器→CoreBoard |
| 传输层 | ESP-NOW（疑似）| 2.4GHz 短距离，低延迟 |
| 或 | Bluetooth 5.0 LE | 配置/OTA 升级 |
| 底层 | WiFi 802.11 b/g/n | MQTT 上行/固件下载 |

> ⚠️ 根据社区逆向分析，CyberBrick 模块间通信可能使用 ESP-NOW（2.4GHz 随机信道），而非标准 WiFi。但官方未公开确认此细节。

#### 蓝牙配置接口

- 开机时长按用户按键 → 进入蓝牙配对模式
- 指示灯：蓝色常亮 = 蓝牙已连接
- 固件升级可通过蓝牙 OTA 完成

#### UART 有线通信（与 Jetson Nano 对接）

| 参数 | 值 |
|------|---|
| 默认波特率 | 115200 |
| 数据位 | 8 |
| 停止位 | 1 |
| 流控制 | 无 |
| TX/RX 引脚 | 核心板 Pin 4/5（可自定义）|

---

### §4.9.5 本项目中的 CyberBrick 固件改造方案

#### 方案 A：保留官方 RC 固件（推荐快速原型）

直接使用官方 `app_rc` 固件，通过 UART 接收 Jetson Nano 的 MQTT→UART 桥接指令。

```
OpenClaw → MQTT → Jetson Nano → UART → CyberBrick（官方固件）
```

优点：开箱即用，官方固件稳定
缺点：UART 指令有限，无 MQTT 原生支持

#### 方案 B：自定义 MicroPython 固件（推荐生产环境）

替换 `app/rc_main.py` 为自定义 MQTT Client 程序，实现 OpenClaw 直接控制：

```python
# CyberBrick 自定义固件 - Phase 4 适配版
# 文件：app/rc_main.py（上传到 /app/rc_main.py）

import network
import paho.mqtt.client as mqtt
from machine import Pin, PWM, UART
import ujson
import time

# ===== UART 初始化（Jetson Nano 通信）=====
uart = UART(1, 115200, tx=Pin(4), rx=Pin(5))

# ===== 电机驱动初始化（HTD8811）=====
class HTD8811:
    def __init__(self, pwm_pin, dir_pin, freq=1000):
        self.pwm = PWM(Pin(pwm_pin), freq=freq)
        self.dir = Pin(dir_pin, Pin.OUT)

    def set_speed(self, speed):
        """speed: -100 ~ 100"""
        if speed > 0:
            self.dir.value(1)
        elif speed < 0:
            self.dir.value(0)
        self.pwm.duty(abs(int(speed * 10.23)))  # 0-1023

    def brake(self):
        self.pwm.duty(0)

# M1: GPIO12(PWM) + GPIO13(DIR)
# M2: GPIO14(PWM) + GPIO15(DIR)
motor1 = HTD8811(12, 13)
motor2 = HTD8811(14, 15)

# ===== 舵机初始化（SG90 等标准舵机）=====
# S1-S4: GPIO 16/17/18/19
servos = []
for pin_num in [16, 17, 18, 19]:
    pwm = PWM(Pin(pin_num), freq=50)  # 50Hz
    servos.append(pwm)

def set_servo(index, angle):
    """angle: 0 ~ 180，映射到 0.5~2.5ms 脉宽"""
    duty = int(26 + angle * 1023 / 180)  # 0.5ms~2.5ms @ 65535 @ 50Hz
    servos[index].duty(duty)

# ===== MQTT 初始化（连接 Jetson Nano Broker）=====
MQTT_BROKER = "192.168.x.x"  # Jetson Nano IP
MQTT_TOPIC_CMD = "robot/0-1/cyberbrick/cmd/#"
MQTT_TOPIC_STATUS = "robot/0-1/cyberbrick/status"

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect('SSID', 'PASSWORD')
while not sta.isconnected():
    pass
print(f"WiFi connected: {sta.ifconfig()}")

def on_mqtt_message(client, userdata, msg):
    try:
        cmd = ujson.loads(msg.payload)
        action = msg.topic.split('/')[-1]  # motor / servo / stop

        if action == 'motor':
            channel = cmd['payload']['channel']
            speed = cmd['payload']['speed']
            if channel == 1:
                motor1.set_speed(speed)
            elif channel == 2:
                motor2.set_speed(speed)

        elif action == 'servo':
            channel = cmd['payload']['channel']
            angle = cmd['payload']['angle']
            set_servo(channel - 1, angle)

        elif action == 'stop':
            motor1.brake()
            motor2.brake()
            for s in servos:
                s.duty(0)

        # 回传执行结果
        client.publish(MQTT_TOPIC_STATUS + "/execute", ujson.dumps({
            "type": "execute_result",
            "status": "completed"
        }))

    except Exception as e:
        print(f"Error: {e}")

mqtt_client = mqtt.Client()
mqtt_client.on_message = on_mqtt_message
mqtt_client.connect(MQTT_BROKER, 1883, keepalive=30)
mqtt_client.subscribe(MQTT_TOPIC_CMD, qos=1)
mqtt_client.loop_start()

print("CyberBrick Phase 4 Firmware Ready")
```

---

### §4.9.6 固件上传方式

| 方式 | 工具 | 适用场景 |
|------|------|---------|
| **Type-C USB** | Thonny / esptool.py | 初次烧录 / 恢复官方固件 |
| **蓝牙 OTA** | Bambu Lab App | 无线升级（官方固件）|
| **WiFi OTA** | `ampy` / `rshell` | 自定义 MicroPython 代码 |
| **Jupyter** | `%send` magic | 运行时调试 |

#### 通过 ampy 上传文件

```bash
# 安装 ampy
pip install adafruit-ampy

# 上传自定义 rc_main.py（通过 Jetson Nano USB 连接）
ampy -p /dev/ttyACM0 put app/rc_main.py /app/rc_main.py

# 重启 CyberBrick
ampy -p /dev/ttyACM0 run boot.py
```

#### 使用 mpy-cross 优化 RAM 占用

当 RAM 不足时，将 `.py` 编译为 `.mpy` 字节码：

```bash
# 安装 mpy-cross
pip install mpy-cross

# 编译 control.py → control.mpy
mpy-cross app/control.py

# 上传 .mpy 文件（与 .py 同名）
ampy -p /dev/ttyACM0 put app/control.mpy /app/control.py
```

---

### §4.9.7 指示灯状态参考

| 状态 | 颜色/节奏 | 含义 |
|------|----------|------|
| 常亮绿 | 绿色 | 上电（未连接无线）|
| 常亮蓝 | 蓝色 | 蓝牙已连接 |
| 常亮黄 | 黄色 | 2.4GHz 主从连接中 |
| 交替闪烁蓝黄 | 蓝+黄 | 蓝牙 + 2.4GHz 均已连接 |
| 每秒闪绿×1 | 绿色 | ID 指示灯（持续5秒）|
| 每2秒闪绿×1 | 绿色 | 设置传输中 |
| 快闪绿×2/秒 | 绿色 | 设置更新中 |
| 常亮白 | 白色 | 固件更新待处理 |
| 闪烁白 | 白色 | 固件正在更新 |
| 常亮红 | 红色 | 固件更新失败 |

---

### §4.9.8 参考链接

| 资源 | URL |
|------|-----|
| 官方组件列表 Wiki | https://wiki.bambulab.com/en/cyberbrick/components/component-list |
| 官方 GitHub 源码 | https://github.com/CyberBrick-Official/CyberBrick_Controller_Core |
| 官方论坛（应用开发）| https://forum.bambulab.com/t/where-is-documentation-on-building-applications-for-cyberbrick/172330 |
| MicroPython 固件文档 | Quick reference for CyberBrick Multi-Function Core Board (ESP32-C3) — MicroPython V01.00.00.02 |
| 社区 ESP-NOW 逆向分析 | https://github-wiki-see.page/m/rotorman/CyberBrick_ESPNOW/wiki |

---

## §4.12 速度/方向控制详解（Speed & Direction Control）

> 本节补充 Phase 4 中电机速度控制和方向控制的完整技术细节，包含PID闭环控制、梯形曲线规划、差速转向模型及实际标定方法。

---

### §4.12.1 速度控制原理

#### 4.12.1.1 PWM 占空比 → 电机转速映射

CyberBrick 电机驱动芯片 HTD8811 通过 PWM 信号控制电机转速：

```
电机转速 ∝ PWM 占空比
```

| PWM 占空比 | 电机行为 |
|-----------|---------|
| 0% | 停止（刹车模式）|
| 1%~49% | 正转，速度递增 |
| 50% | 理论中点（实际死区）|
| 51%~100% | 反转，速度递增 |

> ⚠️ **死区问题**：HTD8811 在 50% 附近存在控制死区（不转或抖动）。建议使用 0% 刹车，1%~100% 调速，或专门做 45%~55% 死区跳过处理。

**Python 实现（MicroPython on ESP32-C3）：**

```python
from machine import PWM, Pin

class MotorController:
    """CyberBrick 电机速度控制器"""
    DEAD_ZONE_LOW = 2    # 低于此值视为停止（克服静摩擦）
    DEAD_ZONE_HIGH = 98  # 高于此值视为反转启动

    def __init__(self, pwm_pin, dir_pin, freq=1000):
        self.pwm = PWM(Pin(pwm_pin), freq=freq)
        self.dir = Pin(dir_pin, Pin.OUT)
        self._speed = 0

    def set_speed(self, speed):
        """speed: -100 ~ 100
        -100 ~ -1 : 反转（速度 = |speed|）
         0        : 刹车停止
         1 ~ 100  : 正转
        """
        self._speed = speed
        if speed > 0:
            self.dir.value(1)
            duty = self._apply_dead_zone(speed, direction=1)
            self.pwm.duty(duty)
        elif speed < 0:
            self.dir.value(0)
            duty = self._apply_dead_zone(abs(speed), direction=-1)
            self.pwm.duty(duty)
        else:
            self.pwm.duty(0)  # 刹车

    def _apply_dead_zone(self, speed, direction):
        """应用静摩擦力补偿和死区跳过"""
        if direction == 1:
            # 正转：从 0 开始需要克服静摩擦
            duty = int(self.DEAD_ZONE_LOW * 10.23)  # 静摩擦补偿
            extra = int((speed - self.DEAD_ZONE_LOW) * 10.23)
            duty = max(duty, extra) if speed > self.DEAD_ZONE_LOW else 0
            if speed < self.DEAD_ZONE_LOW:
                duty = 0  # 静摩擦区间直接刹车
            else:
                duty = int(self.DEAD_ZONE_LOW * 10.23 + (speed - self.DEAD_ZONE_LOW) / (100 - self.DEAD_ZONE_LOW) * (1023 - self.DEAD_ZONE_LOW * 10.23))
            return min(duty, 1023)
        else:
            # 反转：类似处理
            duty = int(self.DEAD_ZONE_LOW * 10.23)
            if speed < self.DEAD_ZONE_LOW:
                return 0
            duty = int(self.DEAD_ZONE_LOW * 10.23 + (speed - self.DEAD_ZONE_LOW) / (100 - self.DEAD_ZONE_LOW) * (1023 - self.DEAD_ZONE_LOW * 10.23))
            return min(duty, 1023)

    def brake(self):
        """硬件刹车（快速停止）"""
        self.pwm.duty(0)
        self._speed = 0

    def get_speed(self):
        return self._speed
```

#### 4.12.1.2 速度档位定义

| 档位 | 速度值 | 适用场景 |
|------|--------|---------|
| `STOP` | 0 | 停止/刹车 |
| `CREEP` | 10~20 | 蠕动模式（精细移动）|
| `SLOW` | 30~40 | 室内低速巡逻 |
| `NORMAL` | 50~60 | 默认速度 |
| `FAST` | 70~80 | 室外/快速移动 |
| `MAX` | 90~100 | 极速（电量充足时）|

---

### §4.12.2 方向控制模型

#### 4.12.2.1 差速转向模型（Tank / Skid Steering）

0-1 为两轮差速底盘（类似坦克），转向通过左右轮速度差实现：

```
前进（直行）：左轮速度 = 右轮速度 > 0
后退（直行）：左轮速度 = 右轮速度 < 0
原地左转：  左轮速度 < 0，右轮速度 > 0
原地右转：  左轮速度 > 0，右轮速度 < 0
左偏转：    左轮速度 < 右轮速度
右偏转：    左轮速度 > 右轮速度
```

**数学模型：**

```
v_l = base_speed × turn_factor_left
v_r = base_speed × turn_factor_right

# turn_factor 范围：
#   1.0  = 全速
#   0.0  = 停止
#  -1.0  = 全速反转
```

**Python 实现：**

```python
class DifferentialDrive:
    """差速底盘方向控制器"""

    def __init__(self, left_motor, right_motor):
        self.left = left_motor    # MotorController
        self.right = right_motor  # MotorController
        self.base_speed = 50       # 默认基础速度

    def set_base_speed(self, speed):
        self.base_speed = max(-100, min(100, speed))

    def forward(self, speed=None):
        s = speed or self.base_speed
        self.left.set_speed(s)
        self.right.set_speed(s)

    def backward(self, speed=None):
        s = speed or self.base_speed
        self.left.set_speed(-s)
        self.right.set_speed(-s)

    def turn_left(self, radius=0.5, speed=None):
        """左转
        radius: 0.0=原地左转, 0.5=正常左转, 1.0=直行（无转向）
        """
        s = speed or self.base_speed
        v_l = int(s * (1 - radius))
        v_r = s
        self.left.set_speed(v_l)
        self.right.set_speed(v_r)

    def turn_right(self, radius=0.5, speed=None):
        """右转
        radius: 0.0=原地右转, 0.5=正常右转, 1.0=直行（无转向）
        """
        s = speed or self.base_speed
        v_l = s
        v_r = int(s * (1 - radius))
        self.left.set_speed(v_l)
        self.right.set_speed(v_r)

    def spin_left(self, speed=None):
        """原地左转（原地自转）"""
        s = speed or self.base_speed
        self.left.set_speed(-s)
        self.right.set_speed(s)

    def spin_right(self, speed=None):
        """原地右转"""
        s = speed or self.base_speed
        self.left.set_speed(s)
        self.right.set_speed(-s)

    def stop(self):
        self.left.brake()
        self.right.brake()
```

#### 4.12.2.2 舵机转向（Steering Servo）

如果 0-1 使用前轮舵机布局（前轮转向 + 后轮驱动），则方向控制通过前轮舵机实现：

```
转向角度 = f(前轮舵机角度)
前轮角度 0°   = 直行
前轮角度 < 0° = 左转
前轮角度 > 0° = 右转
转弯半径 ∝ 1 / 前轮角度
```

> **注意**：根据现有 ROBOT-SOP.md，0-1 使用的是 CyberBrick 舵机控制（多轴机械臂风格），具体是差速地盘还是舵机地盘需根据实际硬件确认。

---

### §4.12.3 梯形速度曲线（Trapezoidal Speed Profile）

为避免电机突加/突减速度造成的机械冲击，使用梯形速度曲线进行加减速规划：

```
速度
  ^
100%|     ┌────────────┐
    |    /            \
    |   /              \
  0%|──┘                └──────
    └────────────────────────→ 时间
    t0   t1          t2   t3
```

| 阶段 | 时间段 | 说明 |
|------|--------|------|
| 加速段 | t0 → t1 | 匀加速（斜率恒定）|
| 匀速段 | t1 → t2 | 恒定速度（占运行时间最长）|
| 减速段 | t2 → t3 | 匀减速（斜率恒定）|
| 停止段 | t3 后 | 速度 = 0 |

**Python 实现（梯形曲线规划器）：**

```python
import time

class TrapezoidalSpeedProfile:
    """梯形速度曲线规划器"""

    def __init__(self,
                 max_speed=100,
                 accel=200,     # 加速度 %/s（每秒速度变化量）
                 decel=200,     # 减速度 %/s
                 min_speed=5):  # 蠕动速度（下限，防止低速抖动）
        self.max_speed = max_speed
        self.accel = accel        # %/s
        self.decel = decel
        self.min_speed = min_speed

    def get_target_speed(self, current_speed, target_speed, dt):
        """根据梯形曲线计算下一步目标速度
        current_speed: 当前速度（-100~100）
        target_speed:  目标速度（-100~100）
        dt:            时间步长（秒）
        返回: 下一步速度
        """
        diff = target_speed - current_speed

        if abs(diff) < self.min_speed:
            return target_speed  # 接近目标，直接到位

        if diff > 0:
            # 加速
            delta = self.accel * dt
        else:
            # 减速（或反向加速）
            delta = -self.decel * dt

        new_speed = current_speed + delta

        # 限幅
        if diff > 0:
            new_speed = min(new_speed, target_speed)
        else:
            new_speed = max(new_speed, target_speed)

        return max(-self.max_speed, min(self.max_speed, new_speed))


class MotionController:
    """带梯形曲线的运动控制器"""

    def __init__(self, left_motor, right_motor):
        self.drive = DifferentialDrive(left_motor, right_motor)
        self.profile = TrapezoidalSpeedProfile(
            max_speed=80,
            accel=150,   # 每秒加速 150%
            decel=200    # 每秒减速 200%（可更急）
        )
        self.current_speed = 0
        self.target_speed = 0
        self.running = False

    def move_forward(self, speed=50, duration_ms=None):
        self.target_speed = speed
        self.running = True
        # 注意：实际调速需要定时循环调用 step()

    def move_backward(self, speed=50, duration_ms=None):
        self.target_speed = -speed
        self.running = True

    def stop(self):
        self.target_speed = 0
        self.running = False

    def step(self, dt):
        """定时调用（建议 50ms 周期），驱动电机"""
        if not self.running and self.current_speed == 0:
            return

        new_speed = self.profile.get_target_speed(
            self.current_speed,
            self.target_speed if self.running else 0,
            dt
        )
        self.current_speed = new_speed
        self.drive.forward(int(abs(new_speed))) if new_speed > 0 else \
            self.drive.backward(int(abs(new_speed))) if new_speed < 0 else \
                self.drive.stop()
```

---

### §4.12.4 PID 闭环速度控制

为保证速度稳定性（克服电池电压下降、地面摩擦力变化等），引入 PID 闭环控制：

```
error = target_speed - actual_speed
output = Kp × error + Ki × ∫error·dt + Kd × d(error)/dt
motor_speed += output（限幅）
```

**MicroPython 实现（针对 ESP32 资源受限环境）：**

```python
class PIDSpeedController:
    """简化 PID 速度控制器（定点数版本，减少浮点开销）"""

    def __init__(self, kp=1.5, ki=0.1, kd=0.05,
                 out_min=-100, out_max=100):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.out_min = out_min
        self.out_max = out_max
        self.integral = 0
        self.prev_error = 0
        self.prev_time = None

    def compute(self, target, measurement, dt_ms):
        """计算 PID 输出
        target:     目标速度（0~100）
        measurement: 实际速度（从编码器反馈）
        dt_ms:      时间步长（毫秒）
        返回: 电机 PWM 占空比调整量
        """
        if self.prev_time is None:
            self.prev_time = dt_ms
            return 0

        dt = (dt_ms - self.prev_time) / 1000.0  # 转为秒
        self.prev_time = dt_ms

        error = target - measurement

        # 积分项（带积分饱和，防止 windup）
        self.integral += error * dt
        self.integral = max(-50, min(50, self.integral))  # 积分限幅

        # 微分项
        if dt > 0:
            derivative = (error - self.prev_error) / dt
        else:
            derivative = 0
        self.prev_error = error

        # PID 输出
        output = self.kp * error + self.ki * self.integral + self.kd * derivative

        # 限幅到电机有效范围
        return max(self.out_min, min(self.out_max, output))


class EncoderFeedback:
    """霍尔编码器速度反馈（简化版）"""

    def __init__(self, pin_a, pin_b, pulses_per_revolution=12,
                 wheel_circumference_cm=21):
        """
        pin_a, pin_b: 霍尔编码器 A/B 相引脚
        pulses_per_revolution: 电机每转脉冲数（霍尔传感器通常 12 PPR）
        wheel_circumference_cm: 轮子周长（cm）
        """
        from machine import Pin, Timer
        self.pulses = 0
        self.pin_a = Pin(pin_a, Pin.IN)
        self.pin_b = Pin(pin_b, Pin.IN)
        self.ppr = pulses_per_revolution
        self.circumference = wheel_circumference_cm  # cm

        # 外部中断计数 A 相
        self.pin_a.irq(trigger=Pin.IRQ_RISING, handler=self._count)

        # 定时器计算速度（每秒清零计数）
        self.speed_timer = Timer()
        self.speed_timer.init(period=100, mode=Timer.PERIODIC,
                              callback=lambda t: self._calc_speed())

        self.rpm = 0

    def _count(self, pin):
        self.pulses += 1

    def _calc_speed(self):
        """每 100ms 计算一次速度（RPM 和 cm/s）"""
        self.rpm = (self.pulses / self.ppr) * 600  # pulses/100ms → rpm
        self.pulses = 0

    def get_speed(self):
        """返回当前速度（cm/s）"""
        # rpm → cm/s: rpm / 60 × circumference
        return self.rpm / 60 * self.circumference
```

> ⚠️ **ESP32-C3 无硬件编码器接口**（与 ESP32 不同），需要用 `Pin.irq()` 外部中断计数，或者选购带硬件 quadrature encoder 接口的扩展板。

---

### §4.12.5 速度标定（Calibration）

#### 4.12.5.1 标定目的

由于电机个体差异、电池电压、地面摩擦力等因素，同样的 PWM 占空比在不同条件下实际转速不同。需要标定「速度等级 → 实际运动速度」的映射。

#### 4.12.5.2 标定方法

**方法一：固定距离计时（推荐）**

```python
import time

def calibrate_speed(motor, distance_cm=100):
    """在固定距离（100cm）上测试各速度档位的时间
    结果：speed_level → actual_velocity (cm/s)
    """
    results = {}

    for target_speed in [20, 40, 60, 80, 100]:
        # 记录出发时间
        start_time = time.time()

        # 发送固定速度指令
        motor.set_speed(target_speed)

        # 等待走完 distance_cm（需要外部光电开关或超声传感器检测）
        # 这里简化为固定时长演示
        time.sleep(2.0)  # 假设 2 秒恰好走完 100cm

        motor.brake()
        elapsed = time.time() - start_time
        velocity = distance_cm / elapsed  # cm/s
        results[target_speed] = velocity

    return results


def build_speed_lookup(calibration_data, max_velocity_cm_s=30.0):
    """根据标定数据构建速度查找表
    max_velocity_cm_s: 速度 100 时对应的最大实际速度
    """
    lookup = {}
    for speed_level, velocity in calibration_data.items():
        lookup[speed_level] = velocity

    # 反向查找：给定期望速度 → 需要的 speed_level
    # 可用线性插值
    def velocity_to_level(desired_velocity):
        for i, (level, vel) in enumerate(sorted(lookup.items())):
            if vel >= desired_velocity:
                if i == 0:
                    return level
                prev_level, prev_vel = list(lookup.items())[i-1]
                # 线性插值
                ratio = (desired_velocity - prev_vel) / (vel - prev_vel + 0.001)
                return int(prev_level + ratio * (level - prev_level))
        return 100  # 上限

    return lookup, velocity_to_level
```

**方法二：电池电压补偿**

电池电压下降时，相同 PWM 占空比下电机实际转速下降。可加入电压补偿：

```python
import machine

class VoltageCompensatedMotor:
    """带电池电压补偿的电机控制器"""

    def __init__(self, motor, nominal_voltage=7.4):
        self.motor = motor
        self.nominal_v = nominal_voltage
        self.adc = machine.ADC(1)  # ESP32-C3 GPIO 1 作为电池电压检测

    def _read_voltage(self):
        """读取电池电压（ADC 分压后）"""
        raw = self.adc.read()
        # 根据分压比计算实际电压
        return raw / 4095 * 3.3 * (10 + 10) / 10  # 假设 10k+10k 分压

    def set_speed(self, speed):
        v = self._read_voltage()
        if v < self.nominal_v * 0.8:
            print("[WARN] Battery low, speed may be reduced")
        # 电压补偿系数
        compensation = min(1.0, self.nominal_v / max(v, 3.0))
        compensated_speed = int(speed * compensation)
        self.motor.set_speed(compensated_speed)
```

---

### §4.12.6 方向控制决策表（Direction Control Decision Table）

| 场景 | 左侧电机 | 右侧电机 | 备注 |
|------|---------|---------|------|
| 直线前进 | +speed | +speed | 两轮同速 |
| 直线后退 | -speed | -speed | 两轮同速 |
| 小左转 | +speed | +speed × 0.5 | 右轮降速 |
| 小右转 | +speed × 0.5 | +speed | 左轮降速 |
| 大左转 | 0 | +speed | 右轮驱动 |
| 大右转 | +speed | 0 | 左轮驱动 |
| 原地左旋 | -speed | +speed | 差速最大 |
| 原地右旋 | +speed | -speed | 差速最大 |
| 急刹 | 0 | 0 | 惯性滑行刹车 |

---

### §4.12.7 OpenClaw 速度/方向控制 Skill 封装

```python
#!/usr/bin/env python3
"""CyberBrick 速度/方向控制 - OpenClaw Skill 封装
文件：~/.openclaw/workspace/harness/robot/cyberbrick_speed_dir.py
用法：
  python3 cyberbrick_speed_dir.py forward 60      # 前进，速度60
  python3 cyberbrick_speed_dir.py back 40         # 后退，速度40
  python3 cyberbrick_speed_dir.py left 50 0.5     # 左转，速度50，半径0.5
  python3 cyberbrick_speed_dir.py spin_left 70    # 原地左旋，速度70
  python3 cyberbrick_speed_dir.py stop            # 停止
"""

import paho.mqtt.client as mqtt
import time
import sys
import ujson

MQTT_BROKER = "192.168.x.x"
TOPIC_MOTOR = "robot/0-1/cyberbrick/cmd/motor"
TOPIC_STOP  = "robot/+/cyberbrick/cmd/stop"

def get_ts():
    return int(time.time() * 1000)

def publish_motor(channel, speed, duration_ms=0, qos=1):
    payload = {
        "type": "motor",
        "robot_id": "0-1",
        "timestamp": get_ts(),
        "payload": {
            "channel": channel,
            "speed": speed,
            "duration_ms": duration_ms
        }
    }
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883, keepalive=30)
    client.publish(TOPIC_MOTOR, ujson.dumps(payload), qos=qos)
    client.disconnect()

def publish_stop(reason="user_command"):
    payload = {
        "type": "stop",
        "robot_id": "0-1",
        "timestamp": get_ts(),
        "payload": {"reason": reason, "estop_gpio_triggered": False}
    }
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883, keepalive=30)
    client.publish(TOPIC_STOP, ujson.dumps(payload), qos=2, retain=True)
    client.disconnect()

# 差速转向控制
def differential_move(v_l, v_r, duration_ms=None):
    """差速控制：左右轮速度单独设定"""
    if duration_ms and duration_ms > 0:
        # 异步发送后等待（实际应用中用线程/Timer）
        publish_motor(1, v_l, duration_ms)
        publish_motor(2, v_r, duration_ms)
        time.sleep(duration_ms / 1000)
        publish_stop("auto_stop")
    else:
        publish_motor(1, v_l)
        publish_motor(2, v_r)

def forward(speed=60, duration_ms=0):
    differential_move(speed, speed, duration_ms)

def backward(speed=60, duration_ms=0):
    differential_move(-speed, -speed, duration_ms)

def turn_left(radius=0.5, speed=60, duration_ms=0):
    v_l = int(speed * (1 - radius))
    v_r = speed
    differential_move(v_l, v_r, duration_ms)

def turn_right(radius=0.5, speed=60, duration_ms=0):
    v_l = speed
    v_r = int(speed * (1 - radius))
    differential_move(v_l, v_r, duration_ms)

def spin_left(speed=60, duration_ms=0):
    differential_move(-speed, speed, duration_ms)

def spin_right(speed=60, duration_ms=0):
    differential_move(speed, -speed, duration_ms)

# CLI 入口
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: cyberbrick_speed_dir.py [forward|back|left|right|spin_left|spin_right|stop] [speed] [extra]")
        sys.exit(1)

    action = sys.argv[1]
    speed = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    extra = sys.argv[3] if len(sys.argv) > 3 else None

    {
        "forward":   lambda: forward(speed),
        "back":      lambda: backward(speed),
        "backward":  lambda: backward(speed),
        "left":      lambda: turn_left(float(extra or 0.5), speed),
        "right":     lambda: turn_right(float(extra or 0.5), speed),
        "spin_left": lambda: spin_left(speed),
        "spin_right":lambda: spin_right(speed),
        "stop":      lambda: publish_stop(),
    }.get(action, lambda: print(f"Unknown: {action}"))()

    print(f"[OK] {action}" + (f" speed={speed}" if action not in ("stop",) else ""))
```

**OpenClaw 指令示例：**
```
用户："让机器人以速度60左转"
→ exec → python3 ~/.openclaw/workspace/harness/robot/cyberbrick_speed_dir.py left 60

用户："原地右转，速度80，持续2秒"
→ exec → python3 ~/.openclaw/workspace/harness/robot/cyberbrick_speed_dir.py spin_right 80

用户："停止"
→ exec → python3 ~/.openclaw/workspace/harness/robot/cyberbrick_speed_dir.py stop
```

---

### §4.12.8 速度/方向控制调试检查清单

| 检查项 | 方法 | 判定标准 |
|--------|------|---------|
| 电机方向正确 | 手动 `motor(1, 50)` 观察轮子 | 轮子向前转 |
| 正反转对称 | 对比 `motor(1,50)` 和 `motor(1,-50)` 速度 | 转速接近 |
| 差速转向正确 | `turn_left()` 后机器人向左转 | 与预期一致 |
| 急停响应 < 50ms | 示波器测量 UART/GPIO 响应时间 | < 50ms |
| 低速稳定性 | 速度=10 观察抖动 | 无抖动/无异响 |
| 电池电压补偿 | 低电量时速度是否自动提升 PWM | 速度维持 |

---

*§4.12 速度/方向控制详解 · 完 · 补充时间：2026-04-01*

---

## §4.12 安全停止机制（Safety Stop Mechanism）

> 补充时间：2026-04-01  
> 对应主文档：harness/robot/ROBOT-SOP.md · Phase 4 · 「有线 GPIO 应急停止」  
> 补充级别：核心功能 · 必须实现

---

### §4.12.1 安全架构总览

安全停止机制采用 **三层保护** 架构，从软件到硬件逐级兜底：

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 · 软件层（Software）                               │
│  MQTT 急停指令 + 命令超时 + 心跳检测                         │
│  触发条件：软件异常、通信断开、指令错误                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 2 · 固件层（Firmware）                                │
│  ESP32 看门狗（Watchdog）+ 运动超时 + 异常指令过滤            │
│  触发条件：固件跑飞、指令卡死、单片机失联                     │
├─────────────────────────────────────────────────────────────┤
│  Layer 3 · 硬件层（Hardware）                                │
│  物理急停按钮 + 继电器断电 + 过流保护                         │
│  触发条件：所有软件失效时的最后防线                           │
└─────────────────────────────────────────────────────────────┘
```

**设计原则：**
- 每一层独立生效，任意一层触发均可停止运动
- 硬件层不依赖任何软件，天然免疫软件崩溃
- 软件层响应最快（< 10ms），硬件层最可靠（< 5ms 继电器响应）

---

### §4.12.2 Layer 1 · 软件层安全停止

#### 4.12.2.1 MQTT 急停指令（最高优先级）

所有急停相关 Topic（见 §4.1.3）均使用 **QoS 2**（ Exactly Once），确保指令必达且不重复：

| Topic | QoS | 说明 |
|-------|-----|------|
| `robot/0-1/cyberbrick/cmd/stop` | 2 | 单机急停 |
| `robot/+/cyberbrick/cmd/stop` | 2 | 广播所有 Cyber Brick |
| `robot/+/event/estop` | 2 | 全局应急广播 |

**急停指令格式：**

```json
{
  "type": "estop",
  "robot_id": "0-1",
  "timestamp": 1743321600000,
  "reason": "user_button",
  "payload": {
    "stop_motors": true,
    "release_servos": false,
    "reset_after_sec": 0
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定为 `estop` |
| `robot_id` | string | ✅ | 机器人编号 |
| `reason` | string | ✅ | 触发原因代码（见 §4.12.5）|
| `payload.stop_motors` | boolean | ✅ | 是否停止所有电机 |
| `payload.release_servos` | boolean | ❌ | 舵机是否释放（false=保持当前位置）|
| `payload.reset_after_sec` | integer | ❌ | 自动恢复延时（秒），0=手动恢复 |

#### 4.12.2.2 命令超时机制（OpenClaw 侧）

OpenClaw 发送运动指令后，自动启动超时计时器：

```python
#!/usr/bin/env python3
"""OpenClaw 运动指令超时控制器"""
import paho.mqtt.client as mqtt
import time
import threading

class MotionController:
    def __init__(self, broker="192.168.x.x"):
        self.broker = broker
        self.client = mqtt.Client()
        self.active_commands = {}  # command_id -> start_time
        self.default_timeout = 5.0  # 秒
        
    def send_motor(self, robot_id, channel, speed, duration_ms=0):
        """发送电机指令，自动注册超时"""
        cmd_id = f"motor_{robot_id}_{channel}_{int(time.time()*1000)}"
        topic = f"robot/{robot_id}/cyberbrick/cmd/motor"
        payload = {
            "type": "motor",
            "robot_id": robot_id,
            "timestamp": int(time.time() * 1000),
            "command_id": cmd_id,
            "payload": {"channel": channel, "speed": speed, "duration_ms": duration_ms}
        }
        self.client.connect(self.broker, 1883)
        self.client.publish(topic, str(payload), qos=2)
        self.client.disconnect()
        
        # 注册超时监控
        if duration_ms == 0:
            # 持续运动指令：启动超时计时器
            timeout = self.default_timeout
        else:
            timeout = duration_ms / 1000.0 + 1.0  # duration + 1s buffer
            
        t = threading.Timer(timeout, self._timeout_handler, args=[cmd_id, robot_id])
        t.start()
        self.active_commands[cmd_id] = t
        
    def _timeout_handler(self, cmd_id, robot_id):
        """超时后自动发送急停"""
        print(f"[WARN] Command {cmd_id} timeout, sending E-STOP to {robot_id}")
        self.send_estop(robot_id, reason="command_timeout")
        if cmd_id in self.active_commands:
            del self.active_commands[cmd_id]
            
    def send_estop(self, robot_id, reason="software"):
        """发送急停指令"""
        topic = f"robot/{robot_id}/event/estop"
        payload = {
            "type": "estop",
            "robot_id": robot_id,
            "timestamp": int(time.time() * 1000),
            "reason": reason,
            "payload": {"stop_motors": True, "release_servos": False, "reset_after_sec": 0}
        }
        self.client.connect(self.broker, 1883)
        self.client.publish(topic, str(payload), qos=2)
        self.client.disconnect()
```

#### 4.12.2.3 心跳检测与自动急停

当 Jetson Nano 或 Cyber Brick 心跳中断超过阈值，OpenClaw 自动触发急停：

```python
#!/usr/bin/env python3
"""心跳检测器 - 超过阈值自动急停"""
import paho.mqtt.client as mqtt
import time

HEARTBEAT_TIMEOUT = 3.0  # 秒，超过此值未收到心跳则急停
last_heartbeat = {}

def on_heartbeat(client, userdata, msg):
    """处理心跳消息"""
    try:
        import ujson
        payload = ujson.loads(msg.payload)
        robot_id = payload.get("robot_id", "unknown")
        last_heartbeat[robot_id] = time.time()
    except:
        pass

def heartbeat_monitor_loop(controller):
    """定期检查心跳，超时则急停"""
    while True:
        now = time.time()
        for robot_id, last_ts in list(last_heartbeat.items()):
            if now - last_ts > HEARTBEAT_TIMEOUT:
                print(f"[CRITICAL] {robot_id} heartbeat timeout ({now-last_ts:.1f}s), E-STOP!")
                controller.send_estop(robot_id, reason="heartbeat_timeout")
                del last_heartbeat[robot_id]
        time.sleep(0.5)
```

---

### §4.12.3 Layer 2 · 固件层安全保护

#### 4.12.3.1 ESP32 看门狗（Watchdog Timer）

Cyber Bricks ESP32 启用硬件看门狗，防止固件死锁：

```python
# CyberBrick 固件 - 看门狗配置
from machine import WDT
import machine

# 启用看门狗（超时时间约 8 秒）
wdt = WDT(timeout=8000)

def main_loop():
    while True:
        wdt.feed()  # 定期喂狗，8秒内必须调用一次
        # 正常业务逻辑
        process_mqtt_messages()
        update_motors()
        send_heartbeat()
```

> ⚠️ **注意**：喂狗操作必须在 8 秒内执行一次，否则 ESP32 自动复位，所有输出归零（电机停止）。

#### 4.12.3.2 固件层运动超时保护

即使没有外部超时触发，固件自身也限制单次运动最大时长：

```python
# CyberBrick 固件 - 运动超时保护
MAX_MOTOR_RUN_TIME = 10.0  # 秒，单次运动最大时长
motor_start_time = None
current_speed = 0

def set_motor(speed):
    global motor_start_time, current_speed
    if speed != 0:
        motor_start_time = time.time()
        current_speed = speed
    _apply_motor(speed)

def check_motor_timeout():
    """定时任务检查运动超时"""
    global motor_start_time, current_speed
    if current_speed != 0 and motor_start_time is not None:
        if time.time() - motor_start_time > MAX_MOTOR_RUN_TIME:
            print("[WARN] Motor timeout, stopping")
            _apply_motor(0)
            current_speed = 0
            motor_start_time = None

# 定时器：每 100ms 检查一次
import uasyncio as asyncio

async def safety_task():
    while True:
        check_motor_timeout()
        await asyncio.sleep(0.1)
```

#### 4.12.3.3 异常指令过滤

固件层对指令进行安全校验，拒绝非法参数：

```python
def validate_motor_command(channel, speed):
    """校验电机指令合法性"""
    if not (1 <= channel <= 4):
        raise ValueError(f"Invalid channel: {channel}")
    if not isinstance(speed, int) or not (-100 <= speed <= 100):
        raise ValueError(f"Invalid speed: {speed} (must be -100 to 100)")

def validate_servo_command(angle):
    """校验舵机指令合法性"""
    if not isinstance(angle, (int, float)) or not (0 <= angle <= 180):
        raise ValueError(f"Invalid angle: {angle} (must be 0 to 180)")

def on_message(topic, msg):
    try:
        cmd = ujson.loads(msg)
        cmd_type = cmd.get('type')
        
        if cmd_type == 'motor':
            validate_motor_command(cmd['payload']['channel'], cmd['payload']['speed'])
            set_motor(cmd['payload']['speed'])
            
        elif cmd_type == 'servo':
            validate_servo_command(cmd['payload']['angle'])
            set_servo(cmd['payload']['angle'])
            
        elif cmd_type == 'estop':
            # 急停指令无条件执行，不校验
            do_emergency_stop(cmd.get('reason', 'unknown'))
            
    except ValueError as e:
        print(f"[SECURITY] Rejected invalid command: {e}")
    except Exception as e:
        print(f"[ERROR] Command processing error: {e}")
```

---

### §4.12.4 Layer 3 · 硬件层安全保护

#### 4.12.4.1 物理急停按钮（E-Stop Button）

物理急停按钮是 **唯一不依赖软件的停止手段**，应安装在机器人外壳显眼位置：

**硬件选型：**

| 型号 | 类型 | 触发电流 | 说明 |
|------|------|---------|------|
| Omron A22E | 按钮+灯 | 5A/250V AC | 带灯，可复位 |
| Schneider XB7 | 急停蘑菇头 | 3A/240V AC | 标准工业级 |
| 国产 LA38 | 经济型 | 5A/380V AC | 性价比高 |

**接线原理（继电器控制法）：**

```
  [急停按钮] ──┬── 常闭触点 ──→ [继电器线圈] ──→ GND
               │
  [复位按钮] ──┘（并联继电器常开触点）

  继电器触点（NC）→ 控制电机驱动供电
                   当继电器失电 → 触点断开 → 电机断电
```

**Cyber Bricks 接线：**
- Cyber Brick 的电机驱动使能引脚（如 ENA）连接到继电器的 NC（常闭）触点
- 正常状态：继电器吸合 → ENA 正常 → 电机可运转
- 急停触发：继电器失电（按钮断开或软件断开）→ NC 触点断开 → ENA=0 → 电机立即停止

#### 4.12.4.2 Jetson Nano GPIO 硬件急停

```bash
# Jetson Nano 硬件急停（通过 GPIO 触发继电器）
# 继电器连接在 Pin 29 (GPIO12)

# 初始化急停 GPIO
echo 12 > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio12/direction

# 正常状态：输出 HIGH（继电器吸合）
echo 1 > /sys/class/gpio/gpio12/value

# 急停：输出 LOW（继电器断开，电机断电）
echo 0 > /sys/class/gpio/gpio12/value
```

#### 4.12.4.3 Cyber Bricks 继电器保护电路

```python
# CyberBrick 固件 - 继电器控制
# 使用 GPIO 控制继电器，继电器控制电机驱动电源

relay_pin = Pin(27, Pin.OUT)  # GPIO27 控制继电器

RELAY_ENGAGED = True   # 继电器吸合 = 电机供电正常
RELAY_RELEASED = False  # 继电器断开 = 电机断电

def relay_engage():
    """恢复电机供电"""
    relay_pin.value(1)

def relay_release():
    """断开电机供电（即时急停）"""
    relay_pin.value(0)

def do_emergency_stop(reason):
    """执行急停：继电器断开 + 电机停止 + 舵机保持"""
    relay_release()       # 硬件级断电
    _apply_motor(0)       # 软件级停止
    print(f"[E-STOP] Triggered by {reason}, relay released")
```

---

### §4.12.5 急停原因代码（Reason Codes）

| 代码 | 含义 | 来源 |
|------|------|------|
| `user_button` | 用户按下物理急停按钮 | 硬件层 |
| `software` | OpenClaw 软件触发 | 软件层 |
| `command_timeout` | 运动指令超时无响应 | 软件层 |
| `heartbeat_timeout` | 心跳检测超时 | 软件层 |
| `invalid_command` | 收到非法指令 | 固件层 |
| `overcurrent` | 电机过流检测 | 固件层 |
| `overtemperature` | 温度超限 | 固件层 |
| `watchdog_reset` | 看门狗复位 | 固件层 |
| `manual_reset` | 人工手动复位 | 用户操作 |

---

### §4.12.6 恢复流程（Recovery Procedure）

急停触发后的标准恢复流程：

```
急停触发
    ↓
1. 排查急停原因（检查 reason 字段）
    ↓
2. 确认安全状态（机器人周围无障碍物、无人员靠近）
    ↓
3. 清除急停条件
    - 软件急停 → 无需操作，等待自动恢复或发送 reset
    - 物理按钮 → 旋转按钮复位
    ↓
4. 发送恢复指令（MQTT）
    Topic: robot/0-1/cyberbrick/cmd/reset
    {
        "type": "reset",
        "robot_id": "0-1",
        "timestamp": 1743321600000,
        "reason": "manual_reset"
    }
    ↓
5. 继电器重新吸合（motor_enable=true）
    ↓
6. 恢复运动控制
```

**恢复指令格式：**

```json
{
  "type": "reset",
  "robot_id": "0-1",
  "timestamp": 1743321600000,
  "reason": "manual_reset",
  "payload": {
    "motor_enable": true,
    "servo_enable": true
  }
}
```

---

### §4.12.7 安全停止测试流程（出厂前必测）

| 步骤 | 测试内容 | 预期结果 |
|------|---------|---------|
| T-01 | 软件急停：发送 `estop` MQTT 指令 | 电机立即停止，继电器保持断开 |
| T-02 | 指令超时：发送 `duration_ms=0` 电机指令，等待 5 秒 | OpenClaw 自动发送急停 |
| T-03 | 心跳超时：断开 Jetson Nano 网络，等待 3 秒 | OpenClaw 自动发送急停 |
| T-04 | 物理按钮：按下急停按钮 | 继电器立即断开，电机断电 |
| T-05 | 看门狗：固件中注释掉 `wdt.feed()`，等待 8 秒 | ESP32 复位，电机停止 |
| T-06 | 恢复流程：复位后发送 `reset` 指令 | 电机恢复正常控制 |

> ⚠️ **出厂前必须完成 T-01 到 T-06 全部测试**，任一项失败则不允许机器人上线运行。


---

## §4.12 避障逻辑（Obstacle Avoidance Logic）

> 补充时间：2026-04-01  
> 对应主文档：harness/robot/ROBOT-SOP.md · Phase 4 · §4.12  
> 数据来源：iPhone LiDAR + 后置深度传感器 + Jetson Nano 视觉融合

---

### §4.12.1 避障系统架构

避障逻辑位于 **感知层** 与 **运动控制层** 之间，充当安全决策中枢：

```
┌──────────────────────────────────────────────────────────────────┐
│                      避障系统数据流                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   iPhone 摄像头/LiDAR        Jetson Nano            Cyber Bricks│
│   ┌──────────────┐        ┌──────────────────┐   ┌───────────┐ │
│   │ 后置 LiDAR    │───────▶│  深度数据处理     │──▶│  运动指令  │ │
│   │ 深度点云       │        │  障碍物检测       │   │  STOP/YAW │ │
│   │ (>30cm)       │        │  路径规划         │   └───────────┘ │
│   ├──────────────┤        │                  │        ▲          │
│   │ 前置TrueDepth │──────▶│  近距离精密检测   │        │          │
│   │ (15-100cm)   │        │  (Cyber Bricks   │        │          │
│   │              │        │   关节区域)       │   UART有线      │
│   └──────────────┘        └──────────────────┘        │          │
│                                                          │          │
│   ┌──────────────┐        ┌──────────────────┐          │          │
│   │ 摄像头 (RGB) │───────▶│  YOLOv11 视觉检测 │──────────┘          │
│   │             │        │  (Apple Vision)  │                      │
│   └──────────────┘        └──────────────────┘                      │
│                                                                  │
│   OpenClaw (MacBook) ── MQTT QoS2 ──▶ 急停广播                    │
└──────────────────────────────────────────────────────────────────┘
```

**避障优先级**：急停（QoS 2）> 避障决策 > 正常运动指令

---

### §4.12.2 传感器方案与分工

#### 传感器覆盖范围

| 传感器 | 检测范围 | 分辨率 | 精度 | 主要用途 |
|--------|---------|--------|------|---------|
| **后置 LiDAR**（iPhone）| 30cm - 500cm | Apple 未公布 | ~1cm | 室内导航避障（>100cm）|
| **前置 TrueDepth** | 15cm - 100cm | 640×480 | ~1mm | 近距离精密避障（<100cm）|
| **后置摄像头 YOLOv11n** | 实时画面 | 800×600 | 目标级 | 语义障碍物（人/宠物/家具）|

#### 传感器融合策略

```
障碍物检测 = LiDAR 距离阈值判定 OR 视觉检测结果

if (LiDAR distance < SAFE_DISTANCE) OR (Vision detected object in path):
    trigger_avoidance()
```

| 障碍物距离 | 响应策略 | 动作 |
|-----------|---------|------|
| < 15cm | **立即急停** | QoS 2 急停 + GPIO 断电 |
| 15-50cm | **减速绕行** | 速度降至 20%，向远离障碍物方向转向 |
| 50-100cm | **绕行** | 正常速度，动态路径规划 |
| > 100cm | **正常行驶** | 无干预 |

---

### §4.12.3 避障 MQTT Topic 设计

#### Topic 命名规范（避障专用）

```
robot/{robot_id}/obstacle/{direction}/{type}
```

| Topic | 方向 | QoS | 说明 |
|-------|------|-----|------|
| `robot/0-1/obstacle/detect/前方` | 传感器 → OpenClaw | 1 | 前方检测到障碍物 |
| `robot/0-1/obstacle/detect/后方` | 传感器 → OpenClaw | 1 | 后方检测到障碍物 |
| `robot/0-1/obstacle/status/scan` | Jetson Nano → OpenClaw | 0 | 实时扫描数据（周期性）|
| `robot/0-1/obstacle/cmd/pause` | OpenClaw → Cyber Bricks | 2 | 暂停运动（避障决策）|
| `robot/0-1/obstacle/cmd/resume` | OpenClaw → Cyber Bricks | 1 | 恢复运动 |
| `robot/+/obstacle/event/collision` | 全设备 → 所有订阅者 | 2 | 碰撞预警（已触及）|

#### 障碍物检测消息格式

**Topic:** `robot/0-1/obstacle/detect/前方`  
**QoS:** 1

```json
{
  "type": "obstacle_detect",
  "robot_id": "0-1",
  "timestamp": 1743321600000,
  "payload": {
    "direction": "前方",
    "sensor": "lidar_rear",
    "distance_cm": 45,
    "confidence": 0.95,
    "action": "slowdown",
    "avoid_direction": "右转",
    "path_clearance_cm": 30
  }
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `direction` | string | ✅ | `前方` / `后方` / `左侧` / `右侧` |
| `sensor` | string | ✅ | `lidar_rear` / `truedepth_front` / `vision_yolo` |
| `distance_cm` | integer | ✅ | 障碍物距离（厘米）|
| `confidence` | float | ✅ | 检测置信度 0.0 ~ 1.0 |
| `action` | string | ✅ | `stop` / `slowdown` / `redirect` / `none` |
| `avoid_direction` | string | ❌ | 建议避让方向：`左转` / `右转` / `后退` |
| `path_clearance_cm` | integer | ❌ | 绕行所需最小通道宽度 |

**action 枚举值：**

| 值 | 触发条件 | 对应运动指令 |
|----|---------|------------|
| `stop` | distance < 15cm | QoS 2 STOP_ALL |
| `slowdown` | 15cm ≤ distance < 50cm | speed → 20% |
| `redirect` | 50cm ≤ distance < 100cm | yaw ± 45° 绕行 |
| `none` | distance ≥ 100cm | 无干预 |

#### 碰撞预警消息格式

**Topic:** `robot/+/obstacle/event/collision`  
**QoS:** 2（恰好一次）

```json
{
  "type": "collision_warning",
  "robot_id": "0-1",
  "timestamp": 1743321600000,
  "payload": {
    "direction": "前方",
    "distance_cm": 8,
    "force_N": 3,
    "immediate_stop": true,
    "damage_check": false
  }
}
```

---

### §4.12.4 Jetson Nano 避障处理程序

#### 完整避障逻辑流程

```
接收 LiDAR/深度数据
    │
    ▼
解析点云/深度帧
    │
    ▼
计算最近障碍物距离（扇形扫描，角度 ±60°）
    │
    ├── distance < 15cm ──▶ 立即急停 + 广播 collision_warning
    │
    ├── 15cm ≤ d < 50cm ──▶ 减速 + 启动绕行决策
    │                          │
    │                          ├── 左侧畅通 ──▶ 左转 45°
    │                          ├── 右侧畅通 ──▶ 右转 45°
    │                          └── 两侧均堵 ──▶ 后退 0.5m
    │
    ├── 50cm ≤ d < 100cm ──▶ 绕行（yaw ± 30°）
    │
    └── distance ≥ 100cm ──▶ 无干预，继续正常运动
```

#### Jetson Nano 避障主程序

```python
#!/usr/bin/env python3
"""
Jetson Nano - 避障决策引擎
接收 iPhone 传感器数据，执行避障逻辑，发送运动指令到 Cyber Bricks
"""
import paho.mqtt.client as mqtt
import ujson
import time
import math

# ===== 避障参数 =====
SAFE_DISTANCE_STOP = 15      # cm - 立即急停
SAFE_DISTANCE_SLOW = 50       # cm - 减速
SAFE_DISTANCE_AVOID = 100     # cm - 绕行
SCAN_ANGLE = 60               # 度 - 前方扇形扫描角度
TURN_ANGLE_SLOW = 45          # 度 - 减速时转向角度
TURN_ANGLE_AVOID = 30         # 度 - 绕行时转向角度
SAFE_CLEARANCE = 30           # cm - 绕行所需通道宽度

# ===== 状态 =====
last_obstacle_time = 0
is_avoiding = False
current_action = "none"
mqtt_client = None

# MQTT 配置
MQTT_BROKER = "192.168.x.x"  # Jetson Nano 本地 Broker
MQTT_TOPIC_OBSTACLE_IN = "robot/0-1/iphone/sensor/depth"
MQTT_TOPIC_OBSTACLE_OUT = "robot/0-1/obstacle/detect"
MQTT_TOPIC_MOTOR_CMD = "robot/0-1/cyberbrick/cmd/motor"
MQTT_TOPIC_SERVO_CMD = "robot/0-1/cyberbrick/cmd/servo"
MQTT_TOPIC_STOP = "robot/+/cyberbrick/cmd/stop"

def get_ts():
    return int(time.time() * 1000)

def publish_motor(speed: int, duration_ms: int = 0):
    payload = {
        "type": "motor",
        "robot_id": "0-1",
        "timestamp": get_ts(),
        "payload": {"channel": 1, "speed": speed, "duration_ms": duration_ms}
    }
    mqtt_client.publish(MQTT_TOPIC_MOTOR_CMD, ujson.dumps(payload), qos=1)

def publish_servo(angle: int, duration_ms: int = 500):
    payload = {
        "type": "servo",
        "robot_id": "0-1",
        "timestamp": get_ts(),
        "payload": {"channel": 1, "angle": angle, "duration_ms": duration_ms}
    }
    mqtt_client.publish(MQTT_TOPIC_SERVO_CMD, ujson.dumps(payload), qos=1)

def emergency_stop(reason: str):
    """发送 QoS 2 急停"""
    payload = {
        "type": "stop",
        "robot_id": "0-1",
        "timestamp": get_ts(),
        "payload": {"reason": reason, "estop_gpio_triggered": False}
    }
    mqtt_client.publish(MQTT_TOPIC_STOP, ujson.dumps(payload), qos=2, retain=True)
    print(f"[AVOID] EMERGENCY STOP: {reason}")

def publish_obstacle_detect(direction: str, sensor: str, distance: int,
                            action: str, avoid_direction: str = None):
    """发布障碍物检测消息"""
    payload = {
        "type": "obstacle_detect",
        "robot_id": "0-1",
        "timestamp": get_ts(),
        "payload": {
            "direction": direction,
            "sensor": sensor,
            "distance_cm": distance,
            "confidence": 0.95,
            "action": action,
            "avoid_direction": avoid_direction,
            "path_clearance_cm": SAFE_CLEARANCE
        }
    }
    mqtt_client.publish(
        f"robot/0-1/obstacle/detect/{direction}",
        ujson.dumps(payload), qos=1
    )

def turn(direction: str, angle: int):
    """
    通过舵机转向
    direction: 'left' / 'right'
    angle: 转向角度（45 / 30）
    """
    center = 90
    if direction == "left":
        target = center - angle  # 例：90-45=45
    else:
        target = center + angle  # 例：90+45=135

    publish_servo(target, duration_ms=500)
    print(f"[AVOID] Turn {direction} to {target}°")

def avoid_obstacle(direction: str):
    """
    执行避障动作
    direction: '左转' / '右转' / '后退'
    """
    global is_avoiding, current_action

    if direction == "左转":
        turn("left", TURN_ANGLE_AVOID)
        # 短暂前进（带方向）
        time.sleep(0.5)
        publish_motor(40, duration_ms=800)
        # 回正
        time.sleep(0.8)
        publish_servo(90, duration_ms=300)
        current_action = "avoid_left"

    elif direction == "右转":
        turn("right", TURN_ANGLE_AVOID)
        time.sleep(0.5)
        publish_motor(40, duration_ms=800)
        time.sleep(0.8)
        publish_servo(90, duration_ms=300)
        current_action = "avoid_right"

    elif direction == "后退":
        publish_motor(-30, duration_ms=1000)  # 后退 1 秒
        current_action = "reverse"

    is_avoiding = False
    current_action = "none"

def process_depth_data(data: dict):
    """
    处理 iPhone 深度传感器数据
    data: 包含 distance_cm, sensor, direction 等字段
    """
    global last_obstacle_time, is_avoiding, current_action

    distance = data.get("distance_cm", 999)
    sensor = data.get("sensor", "lidar_rear")
    direction = data.get("direction", "前方")
    confidence = data.get("confidence", 1.0)

    # 置信度过低则忽略
    if confidence < 0.7:
        return

    # 防抖：100ms 内不重复触发
    if time.time() - last_obstacle_time < 0.1:
        return

    print(f"[DEPTH] sensor={sensor} dist={distance}cm dir={direction}")

    if distance < SAFE_DISTANCE_STOP:
        # ===== 立即急停 =====
        emergency_stop("obstacle_avoidance")
        publish_obstacle_detect(direction, sensor, distance, "stop")
        publish_motor(0)
        is_avoiding = True
        current_action = "stop"
        last_obstacle_time = time.time()

    elif distance < SAFE_DISTANCE_SLOW:
        # ===== 减速 + 绕行决策 =====
        if not is_avoiding:
            print(f"[AVOID] Slowdown triggered: {distance}cm")
            # 降速到 20%
            publish_motor(15)
            is_avoiding = True
            # 决策绕行方向（这里简化处理：随机选择）
            # 实际可结合侧面 LiDAR 数据判断哪侧更空
            avoid_dir = "左转" if direction == "右方" else "右转"
            avoid_obstacle(avoid_dir)
            publish_obstacle_detect(direction, sensor, distance, "slowdown", avoid_dir)
            last_obstacle_time = time.time()

    elif distance < SAFE_DISTANCE_AVOID:
        # ===== 绕行（不减速）=====
        if not is_avoiding:
            print(f"[AVOID] Redirect triggered: {distance}cm")
            avoid_dir = "左转" if direction == "右方" else "右转"
            avoid_obstacle(avoid_dir)
            publish_obstacle_detect(direction, sensor, distance, "redirect", avoid_dir)
            last_obstacle_time = time.time()

    else:
        # ===== 无障碍，正常行驶 =====
        if is_avoiding and current_action != "stop":
            print("[AVOID] Path clear, resuming normal speed")
            publish_motor(60)  # 恢复正常速度
            is_avoiding = False
            current_action = "none"

def on_mqtt_message(client, userdata, msg):
    try:
        payload = ujson.loads(msg.payload)
        topic = msg.topic

        if topic.startswith("robot/0-1/iphone/sensor/depth"):
            process_depth_data(payload)
        elif topic == "robot/0-1/obstacle/cmd/resume":
            # 收到恢复指令
            print("[AVOID] Resume command received")
            publish_motor(60)
            is_avoiding = False
            current_action = "none"

    except Exception as e:
        print(f"[AVOID] Error processing message: {e}")

# ===== MQTT 初始化 =====
mqtt_client = mqtt.Client(client_id="jetson_nano_obstacle")
mqtt_client.on_message = on_mqtt_message
mqtt_client.connect(MQTT_BROKER, 1883, keepalive=30)
mqtt_client.subscribe("robot/0-1/iphone/sensor/depth", qos=1)
mqtt_client.subscribe("robot/0-1/obstacle/cmd/resume", qos=1)
mqtt_client.loop_start()

print("[AVOID] Obstacle Avoidance Engine started")
print(f"[AVOID] SAFE_DISTANCE_STOP={SAFE_DISTANCE_STOP}cm")
print(f"[AVOID] SAFE_DISTANCE_SLOW={SAFE_DISTANCE_SLOW}cm")
print(f"[AVOID] SAFE_DISTANCE_AVOID={SAFE_DISTANCE_AVOID}cm")
```

#### iPhone 深度数据采集（Swift → MQTT）

```swift
// iPhone 侧：采集 LiDAR 深度数据，通过 OpenClaw Node 发送到 Jetson Nano
import AVFoundation
import NetworkExtension

// 通过 OpenClaw 暴露的 camera.depth 节点读取数据
// 深度数据格式：[[Float]] 每帧HxW 深度值（米）

class DepthMonitor {
    func readDistance() -> [String: Any] {
        // 通过 OpenClaw Node 获取后置 LiDAR 数据
        // 简化：返回模拟数据（实际使用 camera.depth API）
        let distanceMeters = readDepthFromLiDAR()
        let distanceCm = Int(distanceMeters * 100)

        return [
            "type": "depth_data",
            "timestamp": Int(Date().timeIntervalSince1970 * 1000),
            "payload": [
                "distance_cm": distanceCm,
                "sensor": "lidar_rear",
                "direction": "前方",
                "confidence": 0.95
            ]
        ]
    }

    // 扇形扫描：返回最近障碍物距离
    func scanForwardSector() -> Int {
        // 读取深度图
        // 在 ±60° 扇形区域内取最小值
        // （具体实现依赖 OpenClaw Node API）
        let depthMap = getDepthMap()  // HxW Float 数组
        let minDist = findMinInSector(depthMap, angleRange: 60)
        return Int(minDist * 100)  // 转换为 cm
    }
}
```

---

### §4.12.5 视觉障碍物检测（YOLOv11 + Apple Vision）

除了 LiDAR 距离检测，还需结合视觉识别语义障碍物（人、宠物、家具）：

```python
#!/usr/bin/env python3
"""
Jetson Nano - 视觉障碍物检测
使用 YOLOv11n (Core ML) 实时检测并触发避障
"""
import cv2
import numpy as np
import paho.mqtt.client as mqtt
import ujson
import time
from pathlib import Path

# YOLO 检测类别（仅保留需要避障的类别）
AVOID_CLASSES = {
    0: "person",    # 人
    15: "cat",      # 猫
    16: "dog",      # 狗
    56: "chair",    # 椅子（可移动障碍）
    57: "couch",    # 沙发
    60: "dining table",  # 餐桌
    17: "bird",     # 宠物鸟
}

# 避障区域：图像下半部分（机器人高度以上的区域）
ROI_Y_START = 0.4  # 图像下方 40% 起为有效障碍区

def detect_obstacles_yolo(frame) -> list:
    """
    使用 YOLOv11n 检测画面中的障碍物
    返回：[(class_name, confidence, bbox), ...]
    """
    # 加载模型（首次调用慢，后续使用模型缓存）
    # 使用 OpenCV DNN 后端（支持 Core ML / ONNX）
    net = cv2.dnn.readNet("/path/to/yolov11n.onnx")

    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (640, 640))
    net.setInput(blob)

    outputs = net.forward(net.getUnconnectedOutLayersNames())
    # 解析输出（YOLOv11 输出格式：[1, 84, 8400]）
    # 84 = 4(bbox) + 80(classes)

    detections = []
    h, w = frame.shape[:2]

    # 简化解析（实际参考 YOLOv11 后处理逻辑）
    for detection in outputs[0].T:
        # confidence, class_id, bbox...
        conf = detection[4]
        if conf > 0.5:
            class_id = np.argmax(detection[5:])
            if class_id in AVOID_CLASSES:
                cx, cy, bw, bh = detection[:4]
                # 转换为像素坐标
                x1 = int((cx - bw/2) * w)
                y1 = int((cy - bh/2) * h)
                x2 = int((cx + bw/2) * w)
                y2 = int((cy + bh/2) * h)
                # 判断是否在下半区（机器人视野）
                if y1 > h * ROI_Y_START:
                    detections.append((AVOID_CLASSES[class_id], conf, (x1,y1,x2,y2)))

    return detections

def on_frame_received(frame):
    """
    处理每一帧画面
    frame: cv2 BGR 图像
    """
    detections = detect_obstacles_yolo(frame)

    if detections:
        # 取置信度最高的障碍物
        best = max(detections, key=lambda x: x[1])
        class_name, conf, bbox = best

        # 计算大致距离（基于 bbox 大小，简化估计）
        x1, y1, x2, y2 = bbox
        obj_height_pixels = y2 - y1
        # 假设图像中人是 1.7m 高，估算距离
        estimated_distance_m = 1.7 * h / obj_height_pixels

        print(f"[VISION] Detected {class_name} conf={conf:.2f} dist≈{estimated_distance_m:.1f}m")

        # 超过安全距离则触发避障
        if estimated_distance_m < 1.0:  # < 1m
            trigger_vision_avoidance(class_name, estimated_distance_m)
    else:
        clear_vision_avoidance()

def trigger_vision_avoidance(class_name: str, distance_m: float):
    """视觉检测到障碍物，触发避障"""
    # 发送 MQTT 避障消息
    payload = {
        "type": "obstacle_detect",
        "robot_id": "0-1",
        "timestamp": int(time.time() * 1000),
        "payload": {
            "direction": "前方",
            "sensor": "vision_yolo",
            "distance_cm": int(distance_m * 100),
            "confidence": 0.9,
            "action": "slowdown" if distance_m > 0.5 else "stop",
            "avoid_direction": "右转",
            "object_class": class_name
        }
    }
    mqtt_client.publish(
        "robot/0-1/obstacle/detect/前方",
        ujson.dumps(payload), qos=1
    )

def clear_vision_avoidance():
    """视觉确认无障碍"""
    pass  # 依赖 LiDAR 数据做最终判断
```

---

### §4.12.6 避障与急停的优先级设计

#### 紧急程度分级

| 级别 | 触发条件 | 响应时间 | 动作 |
|------|---------|---------|------|
| **P0 急停** | LiDAR < 15cm / GPIO 触发 / 用户按钮 | < 10ms | QoS 2 STOP_ALL + GPIO 断电 |
| **P1 紧急避障** | LiDAR 15-50cm / 视觉检测人 < 50cm | < 100ms | 减速 + 立即绕行 |
| **P2 预防性避障** | LiDAR 50-100cm / 视觉检测物体 < 1m | < 500ms | 绕行 |
| **P3 正常导航** | 无障碍物 | 实时 | 正常运动 |

#### 竞态处理原则

```
急停 vs 避障：
- P0 急停：最高优先级，覆盖所有避障决策
- P1/P2 避障：运动中实时生效，不阻止 P0 急停
- 避障执行中收到 P0：立即中断，执行急停

避障 vs 正常运动指令：
- OpenClaw 发送正常运动指令时，避障引擎同时运行
- 避障引擎拥有运动否决权（可覆盖正在执行的运动指令）
- 避障完成后，发 QoS 1 resume 恢复运动
```

#### 双重保障：软件急停 + 硬件急停

```python
# ===== 软件层：MQTT QoS 2 急停 =====
def software_estop():
    payload = {
        "type": "stop",
        "robot_id": "0-1",
        "timestamp": get_ts(),
        "payload": {"reason": "obstacle_emergency", "estop_gpio_triggered": False}
    }
    mqtt_client.publish(MQTT_TOPIC_STOP, ujson.dumps(payload), qos=2, retain=True)

# ===== 硬件层：GPIO 继电器断电（Jetson Nano）=====
# 当检测到严重碰撞或软件通道失效时，触发 GPIO 硬件急停
def hardware_estop():
    """
    Jetson Nano GPIO Pin 29 → 继电器控制 → 所有电机断电
    这是最后的物理保障，不依赖任何软件协议
    """
    GPIO_PATH = "/sys/class/gpio/gpio29"
    try:
        with open(f"{GPIO_PATH}/value", "w") as f:
            f.write("0")  # 继电器断开，电机断电
        print("[HARDWARE ESTOP] Motors disconnected via GPIO")
    except Exception as e:
        print(f"[HARDWARE ESTOP] Failed: {e}")

# 阈值判断
if distance < 8:  # 极端危险距离（8cm）
    software_estop()
    hardware_estop()  # 双重保险
```

---

### §4.12.7 避障系统调试与验证

#### 调试 Topic（临时订阅）

```bash
# 订阅所有避障相关消息（调试用）
mosquitto_sub -t "robot/0-1/obstacle/#" -v

# 订阅 Jetson Nano 摄像头帧（测试 YOLO）
mosquitto_sub -t "robot/0-1/jetson/vision/detections" -v

# 手动发送障碍物测试数据
mosquitto_pub -t "robot/0-1/iphone/sensor/depth" -m '{
    "type":"depth_data","timestamp":0,
    "payload":{"distance_cm":35,"sensor":"lidar_rear","direction":"前方","confidence":0.95}
}'
```

#### 单元测试：避障逻辑验证

```python
def test_obstacle_avoidance():
    """避障逻辑单元测试"""
    test_cases = [
        # (distance_cm, expected_action)
        (8,    "stop"),       # P0 急停
        (14,   "stop"),       # P0 急停
        (15,   "slowdown"),   # P1 减速
        (35,   "slowdown"),   # P1 减速
        (50,   "redirect"),   # P2 绕行
        (75,   "redirect"),   # P2 绕行
        (100,  "none"),       # P3 正常
        (150,  "none"),       # P3 正常
    ]

    for distance, expected in test_cases:
        data = {"distance_cm": distance, "sensor": "lidar_rear",
                "direction": "前方", "confidence": 1.0}
        action = get_action_from_distance(distance)
        status = "✅" if action == expected else "❌"
        print(f"{status} dist={distance}cm → {action} (expected {expected})")

def get_action_from_distance(distance: int) -> str:
    if distance < SAFE_DISTANCE_STOP:
        return "stop"
    elif distance < SAFE_DISTANCE_SLOW:
        return "slowdown"
    elif distance < SAFE_DISTANCE_AVOID:
        return "redirect"
    else:
        return "none"
```

---

### §4.12.8 避障参数配置清单

| 参数 | 值 | 说明 |
|------|---|------|
| `SAFE_DISTANCE_STOP` | 15 cm | 立即急停阈值 |
| `SAFE_DISTANCE_SLOW` | 50 cm | 减速阈值 |
| `SAFE_DISTANCE_AVOID` | 100 cm | 绕行阈值 |
| `SCAN_ANGLE` | 60° | 扇形扫描角度 |
| `TURN_ANGLE_SLOW` | 45° | 减速时转向角度 |
| `TURN_ANGLE_AVOID` | 30° | 绕行时转向角度 |
| `SAFE_CLEARANCE` | 30 cm | 绕行所需通道宽度 |
| `DEBOUNCE_MS` | 100 ms | 避障触发防抖间隔 |
| `VISION_CONFIDENCE_THRESHOLD` | 0.7 | 视觉检测置信度阈值 |
| `VISION_ROI_Y_START` | 0.4 | 视觉有效障碍区域（图像比例）|

---

*补充内容：§4.12 避障逻辑（Obstacle Avoidance Logic）*

*本文档为 ROBOT-SOP.md Phase 4 的补充内容，与主文档配套使用。*
