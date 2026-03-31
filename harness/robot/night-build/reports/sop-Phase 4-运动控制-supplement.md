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
