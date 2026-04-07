# mqtt-router

MQTT 消息路由器 — 0-1 机器人项目的 MQTT 中间件，负责消息路由、协议桥接和 Topic 管理。

## 项目结构

```
mqtt-router/
├── mqtt_router.py   # MQTT 连接管理 + 消息路由主逻辑（paho-mqtt）
├── bridge.py        # MQTT ↔ OpenClaw HTTP 双向桥接（标准库实现）
├── topics.py        # Topic 路径定义、消息体 Schema、JSON 验证工具
├── config.yaml      # 配置文件模板（支持所有组件）
├── requirements.txt # Python 依赖（仅 paho-mqtt）
├── Dockerfile       # 容器化部署
└── README.md        # 本文件
```

## 组件说明

### 1. mqtt_router.py — MQTT 路由器

MQTT Broker 连接管理、消息订阅与路由分发。支持 MQTT 标准通配符（`#`/`+`）、多回调注册、自动重连。

**核心类：`MQTTRouter`**

- 连接管理：`connect()` / `disconnect()` / `is_connected()`
- 订阅：`subscribe(topic, callback)` / `unsubscribe(topic, callback)`
- 发布：`publish(topic, payload, qos, retain)`
- 自动重连：指数退避（5s → 10s → 20s → ...，上限 300s）

**依赖：** `paho-mqtt`

```python
from mqtt_router import MQTTRouter

def on_message(topic, payload):
    print(f"[{topic}] {payload}")

router = MQTTRouter(broker_host="localhost", broker_port=1883)
router.subscribe("robot/#", on_message)
router.connect()

import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    router.disconnect()
```

### 2. bridge.py — MQTT ↔ OpenClaw HTTP 桥接

将 MQTT 消息转发到 OpenClaw Gateway（HTTP Webhook），同时允许通过 HTTP POST 将消息发布到 MQTT。标准库实现，无需 paho-mqtt。

**HTTP 端点：**

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 服务健康检查 |
| `/status` | GET | 详细状态（MQTT/OpenClaw 连通性 + 统计） |
| `/publish` | POST | HTTP → MQTT（发布消息） |
| `/subscribe` | POST | HTTP → MQTT（订阅 topic，当前返回 501） |

**依赖：** 仅标准库（`http.server`, `socket`, `json`, `urllib`）

```bash
# 启动桥接服务
python bridge.py \
    --mqtt-host localhost \
    --mqtt-port 1883 \
    --openclaw-url http://127.0.0.1:18789 \
    --port 8080

# 健康检查
curl http://localhost:8080/health

# 发布 MQTT 消息（HTTP → MQTT）
curl -X POST http://localhost:8080/publish \
    -H "Content-Type: application/json" \
    -d '{"topic": "robot/cmd/move", "payload": "forward", "qos": 0}'
```

### 3. topics.py — Topic 定义与 Schema 验证

定义 0-1 机器人项目的 MQTT Topic 规范，包含消息体 DataClass、JSON Schema 和验证工具。

**Topic 命名规范：**

```
robot/{robot_id}/{device_type}/{direction}/{actuator}
```

| 层级 | 说明 | 示例 |
|------|------|------|
| `robot` | 根命名空间 | 固定 |
| `{robot_id}` | 机器人编号 | `0-1`、`0-2`、`+`（广播） |
| `{device_type}` | 设备类型 | `cyberbrick`、`jetson`、`esp32`、`openclaw` |
| `{direction}` | 消息方向 | `cmd`（命令）、`status`（状态）、`event`（事件） |
| `{actuator}` | 执行器 | `motor`、`servo`、`estop`、`heartbeat` |

**消息类型：**

| type | 方向 | 说明 |
|------|------|------|
| `motor` | cmd → 下位机 | 电机控制（channel 1-4, speed -100~100） |
| `servo` | cmd → 下位机 | 舵机控制（channel 1-6, angle 0-180°） |
| `stop` | event | 紧急停止 |
| `heartbeat` | status → 上位机 | 心跳状态（电池电压、堆内存、运行时间） |
| `execute` | status → 上位机 | 执行结果回传 |

**主要 API：**

```python
from topics import (
    Topic,                   # Topic 路径构建器
    build_motor_cmd,         # 构建电机指令 JSON
    build_estop,             # 构建急停指令
    build_heartbeat_reply,   # 构建心跳上报
    parse_message,           # 解析 MQTT 消息 JSON
    validate_message,        # Schema 验证
    get_qos,                 # 获取 Topic QoS 等级
    is_retained,             # 判断是否 retained 消息
    MOTOR_CMD_SCHEMA,       # 电机指令 JSON Schema
)

# 构建电机指令
payload = build_motor_cmd(robot_id="0-1", channel=1, speed=80, duration_ms=500)
# {"type":"motor","robot_id":"0-1","timestamp":1234567890,"payload":{"channel":1,"speed":80,"duration_ms":500}}

# 验证消息
is_valid, err = validate_message(raw_json)
if not is_valid:
    print(f"验证失败: {err}")

# 获取 QoS
qos = get_qos("robot/0-1/cyberbrick/cmd/motor")  # -> 1 (AT_LEAST_ONCE)
```

## Topic 一览

| Topic 常量 | 说明 | QoS |
|-----------|------|-----|
| `CYBERBRICK1_MOTOR_CMD` | Cyber Brick 1 电机控制 | 1 |
| `CYBERBRICK1_SERVO_CMD` | Cyber Brick 1 舵机控制 | 1 |
| `CYBERBRICK1_STOP_CMD` | Cyber Brick 1 急停 | 2 |
| `CYBERBRICK1_HEARTBEAT` | Cyber Brick 1 心跳 | 0 |
| `CYBERBRICK1_EXECUTE` | Cyber Brick 1 执行结果 | 1 |
| `CYBERBRICK2_*` | Cyber Brick 2 同上一组 | 同上 |
| `ESTOP_BROADCAST` | 全机急停广播 | 2 |
| `JETSON_UART_CMD` | Jetson Nano UART 透传 | 1 |
| `ESP32_CAMERA_CMD` | ESP32-Cam 拍照 | 0 |

## 配置（config.yaml）

所有组件均支持通过 `config.yaml` 配置，也支持环境变量覆盖。详见 `config.yaml` 内的注释。

**环境变量优先级高于文件配置**（适合容器化部署）：

```bash
MQTT_HOST=192.168.1.100 \
MQTT_PORT=1883 \
OPENCLAW_URL=http://openclaw:18789 \
python bridge.py
```

## Docker 部署

```bash
# 构建镜像
docker build -t mqtt-router .

# 运行（使用环境变量）
docker run -d \
    -e MQTT_HOST=192.168.1.100 \
    -e MQTT_PORT=1883 \
    -e OPENCLAW_URL=http://openclaw:18789 \
    -p 8080:8080 \
    mqtt-router

# docker-compose 参考
# 见 docker-compose.yml（项目根目录）
```

**容器内入口：** 默认启动 `bridge.py`（桥接服务）。如需单独运行路由器：
```bash
docker run ... mqtt-router python -u mqtt_router.py --help
```

## 依赖

```
paho-mqtt>=1.6.0
```

仅 `mqtt_router.py` 需要 paho-mqtt；`bridge.py` 使用标准库 socket 实现，无需第三方依赖。

## 错误处理

- **连接失败**：指数退避重连（5s → 最大 300s），可配置最大重试次数
- **订阅失败**：`SubscriptionError` 异常
- **消息路由失败**：单个回调异常不会影响其他回调（`swallow_errors=True`）
- **MQTT 协议错误**：映射到友好错误描述（`CONNACK_REFUSED_USERNAME` 等）

## 线程安全

`MQTTRouter` 内部使用 `threading.Lock` 保护共享状态，可在多线程环境中安全使用。

## 许可

内部项目，保留所有权利。
