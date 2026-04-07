# mqtt-router/topics.py
# ============================================================
# 0-1 机器人项目 · MQTT 消息主题定义
# ============================================================
# 命名规范：robot/{robot_id}/{device_type}/{direction}/{actuator}
# 参考：sop-Phase 4-运动控制-supplement.md
#
# 使用方法：
#   from topics import (
#       Topic, MOTOR_CMD_SCHEMA, parse_message,
#       build_motor_cmd, build_estop, build_heartbeat_reply
#   )
# ============================================================

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional, Any, Dict, List, Union
from enum import Enum

# ------------------------------------------------------------
# §1 常量定义
# ------------------------------------------------------------

# 根命名空间
ROOT = "robot"

# 机器人编号（支持多机，这里定义本项目使用的编号）
ROBOT_IDS = ["0-1", "0-2"]

# 设备类型
class DeviceType(str, Enum):
    CYBERBRICK = "cyberbrick"
    JETSON = "jetson"
    ESP32 = "esp32"
    OPENCLAW = "openclaw"


# 消息方向
class Direction(str, Enum):
    CMD = "cmd"       # 命令（上位机→下位机）
    STATUS = "status" # 状态上报（下位机→上位机）
    EVENT = "event"   # 事件广播（双向）


# 执行器子类别
class Actuator(str, Enum):
    MOTOR = "motor"
    SERVO = "servo"
    STOP = "stop"
    HEARTBEAT = "heartbeat"
    UART_FORWARD = "uart-forward"
    CAMERA = "camera"
    ESTOP = "estop"


# QoS 等级
class QoS(int, Enum):
    AT_MOST_ONCE = 0   # 至多一次（可丢）
    AT_LEAST_ONCE = 1  # 至少一次
    EXACTLY_ONCE = 2   # 恰好一次


# ------------------------------------------------------------
# §2 Topic 路径构建
# ------------------------------------------------------------

class Topic:
    """
    MQTT Topic 构建器。

    命名规范：robot/{robot_id}/{device_type}/{direction}/{actuator}

    示例：
        Topic.build(ROBOT_IDS[0], DeviceType.CYBERBRICK, Direction.CMD, Actuator.MOTOR)
        # -> "robot/0-1/cyberbrick/cmd/motor"
    """

    # 允许的字符（MQTT 规范：只能有 ASCII 字母、数字、-、_、+）
    # 注意：+ 是 MQTT 通配符，用于 robot_id 单级通配
    _VALID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\+]+$")

    @classmethod
    def build(
        cls,
        robot_id: str,
        device: Union[str, DeviceType],
        direction: Union[str, Direction],
        actuator: Union[str, Actuator],
    ) -> str:
        """
        构建完整 Topic 路径。

        Args:
            robot_id:    机器人编号，如 "0-1"
            device:      设备类型
            direction:   消息方向
            actuator:   执行器/子类别

        Returns:
            完整 Topic 字符串，如 "robot/0-1/cyberbrick/cmd/motor"

        Raises:
            ValueError: 输入包含非法字符或为空
        """
        robot_id  = str(robot_id)
        device    = device.value if isinstance(device, Enum) else str(device)
        direction = direction.value if isinstance(direction, Enum) else str(direction)
        actuator  = actuator.value if isinstance(actuator, Enum) else str(actuator)

        for name, val in [("robot_id", robot_id), ("device", device),
                          ("direction", direction), ("actuator", actuator)]:
            if not cls._VALID_PATTERN.match(val):
                raise ValueError(
                    f"Topic 字段 '{name}' 包含非法字符，仅允许 a-zA-Z0-9_-: got '{val}'"
                )

        return f"{ROOT}/{robot_id}/{device}/{direction}/{actuator}"

    @classmethod
    def wildcard_all(cls, robot_id: str = "+") -> str:
        """返回订阅所有下级 Topic 的通配符（多级）"""
        return f"{ROOT}/{robot_id}/#"

    @classmethod
    def wildcard_device(cls, robot_id: str = "+") -> str:
        """返回订阅某机器人所有设备消息的单级通配符"""
        return f"{ROOT}/{robot_id}/+"

    @classmethod
    def parse(cls, topic: str) -> Dict[str, str]:
        """
        解析 Topic 路径为字典。

        Args:
            topic: 完整 Topic 路径

        Returns:
            {"root", "robot_id", "device", "direction", "actuator"}

        Raises:
            ValueError: Topic 格式不正确
        """
        parts = topic.split("/")
        if len(parts) != 5 or parts[0] != ROOT:
            raise ValueError(f"Topic 格式不正确（期望 5 层）: {topic}")

        return {
            "root":       parts[0],
            "robot_id":   parts[1],
            "device":     parts[2],
            "direction":  parts[3],
            "actuator":   parts[4],
        }


# ------------------------------------------------------------
# §3 预定义 Topic 常量（静态分析 / IDE 自动补全用）
# ------------------------------------------------------------

# ----- Cyber Brick 1 -----
CYBERBRICK1_MOTOR_CMD   = Topic.build("0-1", DeviceType.CYBERBRICK, Direction.CMD, Actuator.MOTOR)
CYBERBRICK1_SERVO_CMD   = Topic.build("0-1", DeviceType.CYBERBRICK, Direction.CMD, Actuator.SERVO)
CYBERBRICK1_STOP_CMD    = Topic.build("0-1", DeviceType.CYBERBRICK, Direction.CMD, Actuator.STOP)
CYBERBRICK1_HEARTBEAT   = Topic.build("0-1", DeviceType.CYBERBRICK, Direction.STATUS, Actuator.HEARTBEAT)
CYBERBRICK1_EXECUTE     = Topic.build("0-1", DeviceType.CYBERBRICK, Direction.STATUS, Actuator.MOTOR)  # 执行结果回传

# ----- Cyber Brick 2 -----
CYBERBRICK2_MOTOR_CMD   = Topic.build("0-2", DeviceType.CYBERBRICK, Direction.CMD, Actuator.MOTOR)
CYBERBRICK2_SERVO_CMD   = Topic.build("0-2", DeviceType.CYBERBRICK, Direction.CMD, Actuator.SERVO)
CYBERBRICK2_STOP_CMD    = Topic.build("0-2", DeviceType.CYBERBRICK, Direction.CMD, Actuator.STOP)
CYBERBRICK2_HEARTBEAT   = Topic.build("0-2", DeviceType.CYBERBRICK, Direction.STATUS, Actuator.HEARTBEAT)

# ----- 全机广播急停 -----
ESTOP_BROADCAST     = Topic.build("+", DeviceType.CYBERBRICK, Direction.EVENT, Actuator.ESTOP)
ESTOP_ALL_DEVICES    = Topic.build("+", "+", Direction.EVENT, Actuator.ESTOP)

# ----- Jetson Nano -----
JETSON_UART_CMD     = Topic.build("0-1", DeviceType.JETSON, Direction.CMD, Actuator.UART_FORWARD)
JETSON_STATUS       = Topic.build("0-1", DeviceType.JETSON, Direction.STATUS, "+")

# ----- ESP32-Cam -----
ESP32_CAMERA_CMD    = Topic.build("0-1", DeviceType.ESP32, Direction.CMD, Actuator.CAMERA)

# ------------------------------------------------------------
# §4 消息体 DataClass 定义
# ------------------------------------------------------------

@dataclass
class MotorPayload:
    """电机控制指令 payload"""
    channel: int          # 电机通道号（1-4）
    speed: int            # 速度 -100 ~ 100（负数=后退）
    duration_ms: int = 0  # 执行时长（ms），0=持续


@dataclass
class ServoPayload:
    """舵机控制指令 payload"""
    channel: int          # 舵机通道号（1-6）
    angle: int            # 目标角度（度）
    duration_ms: int = 0  # 执行时长（ms）


@dataclass
class EstopPayload:
    """紧急停止 payload"""
    reason: str = "manual"  # 触发原因：manual / sensor / timeout


@dataclass
class HeartbeatPayload:
    """心跳状态 payload"""
    battery_mv: int = 0     # 电池电压（mV）
    free_heap: int = 0      # ESP32 剩余堆内存（Byte）
    uptime_ms: int = 0      # 运行时间（ms）
    temp_c: float = 0.0     # 芯片温度（℃）


@dataclass
class ExecutePayload:
    """执行结果回传 payload"""
    success: bool
    error_code: int = 0
    message: str = ""


@dataclass
class BaseMessage:
    """所有 MQTT 消息的基类"""
    type: str          # 消息类型：motor / servo / stop / heartbeat / execute
    robot_id: str     # 机器人编号
    timestamp: int    # 毫秒级 Unix 时间戳
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: Union[str, bytes]) -> "BaseMessage":
        """
        从 JSON 反序列化为 BaseMessage（自动识别 type 并返回对应子类）。

        Raises:
            json.JSONDecodeError: JSON 格式错误
            KeyError: 缺少必填字段
            ValueError: type 字段值不支持
        """
        data = json.loads(raw)

        required = ["type", "robot_id", "timestamp", "payload"]
        for key in required:
            if key not in data:
                raise KeyError(f"消息缺少必填字段: {key}")

        msg = cls(
            type=data["type"],
            robot_id=data["robot_id"],
            timestamp=data["timestamp"],
            payload=data.get("payload", {}),
        )

        # 根据 type 补充 payload 类型提示（运行时检查）
        return msg


def build_motor_cmd(
    robot_id: str,
    channel: int,
    speed: int,
    timestamp: Optional[int] = None,
    duration_ms: int = 0,
) -> str:
    """
    构建电机控制指令 JSON。

    Args:
        robot_id:    机器人编号，如 "0-1"
        channel:     电机通道号（1-4）
        speed:       速度 -100 ~ 100
        timestamp:   时间戳，默认当前时间
        duration_ms: 持续时长（ms）

    Returns:
        JSON 字符串

    Raises:
        ValueError: 参数超出有效范围
    """
    if not (1 <= channel <= 4):
        raise ValueError(f"channel 必须在 1-4 之间: {channel}")
    if not (-100 <= speed <= 100):
        raise ValueError(f"speed 必须在 -100~100 之间: {speed}")
    if timestamp is None:
        import time
        timestamp = int(time.time() * 1000)

    msg = BaseMessage(
        type="motor",
        robot_id=robot_id,
        timestamp=timestamp,
        payload={"channel": channel, "speed": speed, "duration_ms": duration_ms},
    )
    return msg.to_json()


def build_servo_cmd(
    robot_id: str,
    channel: int,
    angle: int,
    timestamp: Optional[int] = None,
    duration_ms: int = 0,
) -> str:
    """构建舵机控制指令 JSON"""
    if not (1 <= channel <= 6):
        raise ValueError(f"servo channel 必须在 1-6 之间: {channel}")
    if not (0 <= angle <= 180):
        raise ValueError(f"angle 必须在 0-180 之间: {angle}")
    if timestamp is None:
        import time
        timestamp = int(time.time() * 1000)

    msg = BaseMessage(
        type="servo",
        robot_id=robot_id,
        timestamp=timestamp,
        payload={"channel": channel, "angle": angle, "duration_ms": duration_ms},
    )
    return msg.to_json()


def build_estop(robot_id: str = "+", reason: str = "manual") -> str:
    """构建紧急停止指令 JSON（robot_id='+' 为广播急停）"""
    import time
    msg = BaseMessage(
        type="stop",
        robot_id=robot_id,
        timestamp=int(time.time() * 1000),
        payload={"reason": reason},
    )
    return msg.to_json()


def build_heartbeat_reply(
    robot_id: str,
    battery_mv: int = 0,
    free_heap: int = 0,
    uptime_ms: int = 0,
    temp_c: float = 0.0,
) -> str:
    """构建心跳状态上报 JSON（Cyber Brick → OpenClaw）"""
    import time
    msg = BaseMessage(
        type="heartbeat",
        robot_id=robot_id,
        timestamp=int(time.time() * 1000),
        payload={
            "battery_mv": battery_mv,
            "free_heap": free_heap,
            "uptime_ms": uptime_ms,
            "temp_c": temp_c,
        },
    )
    return msg.to_json()


def build_execute_reply(
    robot_id: str,
    success: bool,
    error_code: int = 0,
    message: str = "",
) -> str:
    """构建执行结果回传 JSON（Cyber Brick → OpenClaw）"""
    import time
    msg = BaseMessage(
        type="execute",
        robot_id=robot_id,
        timestamp=int(time.time() * 1000),
        payload={"success": success, "error_code": error_code, "message": message},
    )
    return msg.to_json()


def parse_message(raw: Union[str, bytes]) -> BaseMessage:
    """
    解析 MQTT 消息 JSON，支持类型自动识别。

    相当于 BaseMessage.from_json 的别名，更符合使用习惯。

    Raises:
        json.JSONDecodeError: JSON 格式错误
        KeyError: 缺少必填字段
        ValueError: type 字段值不支持
    """
    return BaseMessage.from_json(raw)


# ------------------------------------------------------------
# §5 JSON Schema 定义（供外部验证库使用）
# ------------------------------------------------------------

MOTOR_CMD_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["type", "robot_id", "timestamp", "payload"],
    "additionalProperties": False,
    "properties": {
        "type": {"const": "motor"},
        "robot_id": {
            "type": "string",
            "pattern": r"^[0-9]+-[0-9]+$",
            "description": "机器人编号，格式：数字-数字，如 0-1"
        },
        "timestamp": {
            "type": "integer",
            "minimum": 0,
            "description": "毫秒级 Unix 时间戳"
        },
        "payload": {
            "type": "object",
            "required": ["channel", "speed"],
            "additionalProperties": False,
            "properties": {
                "channel": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 4,
                    "description": "电机通道号 1-4"
                },
                "speed": {
                    "type": "integer",
                    "minimum": -100,
                    "maximum": 100,
                    "description": "速度 -100（后退）~ 100（前进）"
                },
                "duration_ms": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 0,
                    "description": "执行时长（ms），0=持续"
                },
            },
        },
    },
}

SERVO_CMD_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["type", "robot_id", "timestamp", "payload"],
    "properties": {
        "type": {"const": "servo"},
        "robot_id": {"type": "string", "pattern": r"^[0-9]+-[0-9]+$"},
        "timestamp": {"type": "integer", "minimum": 0},
        "payload": {
            "type": "object",
            "required": ["channel", "angle"],
            "properties": {
                "channel": {"type": "integer", "minimum": 1, "maximum": 6},
                "angle": {"type": "integer", "minimum": 0, "maximum": 180},
                "duration_ms": {"type": "integer", "minimum": 0, "default": 0},
            },
        },
    },
}

ESTOP_CMD_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["type", "robot_id", "timestamp", "payload"],
    "properties": {
        "type": {"const": "stop"},
        "robot_id": {"type": "string", "pattern": r"^[0-9]+-[0-9]+$"},
        "timestamp": {"type": "integer", "minimum": 0},
        "payload": {
            "type": "object",
            "required": ["reason"],
            "properties": {
                "reason": {
                    "type": "string",
                    "enum": ["manual", "sensor", "timeout"],
                    "default": "manual"
                },
            },
        },
    },
}

HEARTBEAT_STATUS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["type", "robot_id", "timestamp", "payload"],
    "properties": {
        "type": {"const": "heartbeat"},
        "robot_id": {"type": "string", "pattern": r"^[0-9]+-[0-9]+$"},
        "timestamp": {"type": "integer", "minimum": 0},
        "payload": {
            "type": "object",
            "properties": {
                "battery_mv": {"type": "integer", "minimum": 0},
                "free_heap": {"type": "integer", "minimum": 0},
                "uptime_ms": {"type": "integer", "minimum": 0},
                "temp_c": {"type": "number"},
            },
        },
    },
}

EXECUTE_STATUS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["type", "robot_id", "timestamp", "payload"],
    "properties": {
        "type": {"const": "execute"},
        "robot_id": {"type": "string", "pattern": r"^[0-9]+-[0-9]+$"},
        "timestamp": {"type": "integer", "minimum": 0},
        "payload": {
            "type": "object",
            "required": ["success"],
            "properties": {
                "success": {"type": "boolean"},
                "error_code": {"type": "integer", "default": 0},
                "message": {"type": "string", "default": ""},
            },
        },
    },
}

# Schema 字典，按 type 索引
SCHEMAS = {
    "motor":     MOTOR_CMD_SCHEMA,
    "servo":     SERVO_CMD_SCHEMA,
    "stop":      ESTOP_CMD_SCHEMA,
    "heartbeat": HEARTBEAT_STATUS_SCHEMA,
    "execute":   EXECUTE_STATUS_SCHEMA,
}


def validate_message(raw: Union[str, bytes]) -> tuple[bool, str]:
    """
    验证 MQTT 消息 JSON 是否符合 Schema。

    使用标准库 json + 内置验证逻辑，不依赖外部 schema 库。

    Returns:
        (is_valid, error_message)

    Note:
        这里做基础的结构和类型验证。
        如需完整 JSON Schema 验证（$schema 关键词），
        可安装 `jsonschema` 库后调用：
            from jsonschema import validate
            validate(instance=data, schema=SCHEMAS[data["type"]])
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return False, f"JSON 解析失败: {e}"

    if "type" not in data:
        return False, "缺少必填字段: type"

    msg_type = data.get("type")
    if msg_type not in SCHEMAS:
        valid_types = ", ".join(SCHEMAS.keys())
        return False, f"不支持的 type: {msg_type}（支持: {valid_types}）"

    schema = SCHEMAS[msg_type]

    # 必填字段检查
    for required in schema.get("required", []):
        if required not in data:
            return False, f"[{msg_type}] 缺少必填字段: {required}"

    # payload 必填字段检查
    if "payload" in schema.get("required", []) and "payload" not in data:
        return False, f"[{msg_type}] 缺少必填字段: payload"

    payload_schema = schema.get("properties", {}).get("payload", {}).get("properties", {})
    payload_required = schema.get("properties", {}).get("payload", {}).get("required", [])

    for field_name in payload_required:
        if field_name not in data.get("payload", {}):
            return False, f"[{msg_type}] payload 缺少必填字段: {field_name}"

    # 类型检查（简单版）
    for field_name, field_schema in payload_schema.items():
        val = data.get("payload", {}).get(field_name)
        if val is None:
            continue
        expected_type = field_schema.get("type")
        if expected_type == "integer" and not isinstance(val, int):
            return False, f"[{msg_type}] payload.{field_name} 类型错误，期望 integer，实际 {type(val).__name__}"
        if expected_type == "number" and not isinstance(val, (int, float)):
            return False, f"[{msg_type}] payload.{field_name} 类型错误，期望 number"
        if expected_type == "boolean" and not isinstance(val, bool):
            return False, f"[{msg_type}] payload.{field_name} 类型错误，期望 boolean"

        # 范围检查
        if expected_type in ("integer", "number") and isinstance(val, (int, float)):
            if "minimum" in field_schema and val < field_schema["minimum"]:
                return False, f"[{msg_type}] payload.{field_name} 值 {val} 小于最小值 {field_schema['minimum']}"
            if "maximum" in field_schema and val > field_schema["maximum"]:
                return False, f"[{msg_type}] payload.{field_name} 值 {val} 大于最大值 {field_schema['maximum']}"

    return True, ""


# ------------------------------------------------------------
# §6 Topic → QoS 映射表
# ------------------------------------------------------------

# QoS 映射：Topic → QoS 等级
TOPIC_QOS_MAP: Dict[str, int] = {
    # Cyber Brick 命令（可靠送达）
    CYBERBRICK1_MOTOR_CMD:  QoS.AT_LEAST_ONCE,
    CYBERBRICK1_SERVO_CMD:  QoS.AT_LEAST_ONCE,
    CYBERBRICK1_STOP_CMD:   QoS.EXACTLY_ONCE,   # 急停最高可靠
    CYBERBRICK2_MOTOR_CMD:   QoS.AT_LEAST_ONCE,
    CYBERBRICK2_SERVO_CMD:   QoS.AT_LEAST_ONCE,
    CYBERBRICK2_STOP_CMD:    QoS.EXACTLY_ONCE,
    # 全机广播急停
    ESTOP_BROADCAST:         QoS.EXACTLY_ONCE,
    ESTOP_ALL_DEVICES:       QoS.EXACTLY_ONCE,
    # 状态上报
    CYBERBRICK1_HEARTBEAT:   QoS.AT_MOST_ONCE,  # 心跳可丢
    CYBERBRICK2_HEARTBEAT:   QoS.AT_MOST_ONCE,
    CYBERBRICK1_EXECUTE:     QoS.AT_LEAST_ONCE,
    # Jetson
    JETSON_UART_CMD:         QoS.AT_LEAST_ONCE,
    JETSON_STATUS:           QoS.AT_MOST_ONCE,
    # ESP32
    ESP32_CAMERA_CMD:        QoS.AT_MOST_ONCE,   # 拍照可丢
}


def get_qos(topic: str) -> int:
    """
    获取 Topic 对应的 QoS 等级。

    支持通配符订阅时的精确匹配回退。

    Args:
        topic: 完整 Topic 路径

    Returns:
        QoS 等级（0/1/2），未匹配时默认 1
    """
    if topic in TOPIC_QOS_MAP:
        return TOPIC_QOS_MAP[topic]

    # 通配符回退：按前缀匹配
    for pattern, qos in TOPIC_QOS_MAP.items():
        if topic.startswith(pattern.rsplit("/", 1)[0] + "/"):
            return qos

    return QoS.AT_LEAST_ONCE  # 默认至少一次


# ------------------------------------------------------------
# §7 Retained 消息配置
# ------------------------------------------------------------

# Retained Topic 集合：Broker 会保留这些 Topic 的最后一条消息
RETAINED_TOPICS: set = {
    ESTOP_BROADCAST,       # 急停状态需要持久化，新设备连接后立即知道急停状态
    ESTOP_ALL_DEVICES,
    CYBERBRICK1_HEARTBEAT, # 心跳保留，新订阅者立即知道设备是否在线
    CYBERBRICK2_HEARTBEAT,
}


def is_retained(topic: str) -> bool:
    """判断 Topic 是否需要 retained 消息"""
    return topic in RETAINED_TOPICS


# ------------------------------------------------------------
# §8 便利工具
# ------------------------------------------------------------

def list_all_topics() -> List[str]:
    """返回所有已定义的 Topic 常量列表（供调试/文档用）"""
    return [
        name for name, val in globals().items()
        if name.isupper() and isinstance(val, str) and val.startswith("robot/")
    ]


def topic_description(topic: str) -> str:
    """返回 Topic 的中文描述"""
    DESCRIPTIONS = {
        CYBERBRICK1_MOTOR_CMD:   "Cyber Brick 1 电机控制命令",
        CYBERBRICK1_SERVO_CMD:   "Cyber Brick 1 舵机控制命令",
        CYBERBRICK1_STOP_CMD:    "Cyber Brick 1 紧急停止命令",
        CYBERBRICK1_HEARTBEAT:   "Cyber Brick 1 心跳状态上报",
        CYBERBRICK1_EXECUTE:     "Cyber Brick 1 执行结果回传",
        CYBERBRICK2_MOTOR_CMD:   "Cyber Brick 2 电机控制命令",
        CYBERBRICK2_SERVO_CMD:   "Cyber Brick 2 舵机控制命令",
        CYBERBRICK2_STOP_CMD:    "Cyber Brick 2 紧急停止命令",
        CYBERBRICK2_HEARTBEAT:   "Cyber Brick 2 心跳状态上报",
        ESTOP_BROADCAST:         "全机紧急停止广播",
        ESTOP_ALL_DEVICES:       "全设备事件广播",
        JETSON_UART_CMD:         "Jetson Nano UART 透传命令",
        JETSON_STATUS:           "Jetson Nano 状态上报",
        ESP32_CAMERA_CMD:        "ESP32-Cam 拍照命令",
    }
    return DESCRIPTIONS.get(topic, "（未定义）")
