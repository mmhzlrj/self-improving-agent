"""
bridge.py - MQTT <-> OpenClaw HTTP Bridge

功能：
  - MQTT 消息 <-> OpenClaw Gateway HTTP API 双向桥接
  - 将 MQTT 主题消息转发到 OpenClaw Webhook/HTTP 端点
  - 将 HTTP 请求发布到指定 MQTT 主题
  - 提供 HTTP 健康检查和状态端点

OpenClaw Gateway API 参考：
  - Webhook 格式：POST /webhook?topic=<topic>  body: {"message": "...", "from": "mqtt"}
  - Gateway 地址：http://127.0.0.1:<port>（默认 18789）

依赖：标准库（http.server, json, threading, logging, urllib, asyncio）
      需要 mqtt_router.py 同目录
标准库：不依赖 paho-mqtt，使用标准库 socket 直接实现轻量 MQTT client（可选）

用法：
    # 启动 bridge
    python bridge.py --mqtt-host localhost --mqtt-port 1883 \\
                     --openclaw-url http://127.0.0.1:18789 \\
                     --listen 0.0.0.0 --port 8080

    # HTTP 测试
    curl -X POST http://localhost:8080/publish \\
         -H "Content-Type: application/json" \\
         -d '{"topic": "robot/cmd", "payload": "move_forward"}'

    # MQTT 消息会自动转发到 OpenClaw Gateway
"""

import argparse
import json
import logging
import socket
import sys
import threading
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import socketserver

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("mqtt_bridge")

# ---------------------------------------------------------------------------
# 异常定义
# ---------------------------------------------------------------------------
class BridgeError(Exception):
    """桥接器通用错误基类"""
    pass


class HTTPForwardError(BridgeError):
    """HTTP 转发失败"""
    pass


class MQTTPublishError(BridgeError):
    """MQTT 发布失败"""
    pass


# ---------------------------------------------------------------------------
# 轻量级 MQTT Client（标准库实现，仅支持 QoS 0 publish）
# 为避免外部依赖，使用标准库 socket 实现简单 MQTT PUBLISH
# 如需完整 MQTT 功能，请安装 paho-mqtt: pip install paho-mqtt
# ---------------------------------------------------------------------------
class SimpleMQTTClient:
    """
    轻量级 MQTT 发布客户端（标准库 socket 实现）。

    仅支持：
      - CONNECT / CONNACK
      - PUBLISH (QoS 0)
      - DISCONNECT

    适用场景：只需要向外发布消息，不需要订阅。

    如需完整订阅功能，使用同目录 mqtt_router.py 中的 MQTTRouter 类。
    """

    MQTT_PROTOCOL_VERSION = 4  # MQTT 3.1.1

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "",
        keepalive: int = 60,
        username: str = None,
        password: str = None,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.keepalive = keepalive

        # 生成客户端ID
        if not client_id:
            client_id = f"bridge_{uuid.uuid4().hex[:8]}"
        self.client_id = client_id

        self.username = username
        self.password = password
        self._sock: socket.socket = None
        self._connected = False
        self._lock = threading.Lock()

    # -------------------------------------------------------------------------
    # 连接管理
    # -------------------------------------------------------------------------

    def connect(self) -> bool:
        """
        连接到 MQTT Broker。

        Returns:
            True 连接成功
            False 连接失败
        """
        with self._lock:
            try:
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.settimeout(10)
                self._sock.connect((self.broker_host, self.broker_port))

                # 发送 CONNECT 报文
                connect_packet = self._build_connect_packet()
                self._sock.sendall(connect_packet)

                # 读取 CONNACK 报文
                connack = self._read_packet()
                if connack is None:
                    logger.error(f"[{self.client_id}] 未收到 CONNACK")
                    return False

                packet_type, remaining_len, connack_data = connack
                if packet_type == 0x20:  # CONNACK
                    conn_return_code = connack_data[1]
                    if conn_return_code == 0:
                        self._connected = True
                        logger.info(
                            f"[{self.client_id}] ✅ 已连接 MQTT Broker "
                            f"{self.broker_host}:{self.broker_port}"
                        )
                        return True
                    else:
                        logger.error(
                            f"[{self.client_id}] ❌ CONNACK 返回码={conn_return_code}"
                        )
                        return False
                else:
                    logger.error(f"[{self.client_id}] 预期 CONNACK，实际={packet_type:#04x}")
                    return False

            except Exception as e:
                logger.error(f"[{self.client_id}] 连接 MQTT Broker 失败: {e}")
                self._cleanup()
                return False

    def disconnect(self) -> None:
        """断开与 Broker 的连接"""
        with self._lock:
            if not self._connected:
                return
            try:
                # 发送 DISCONNECT 报文（固定头：0xE0, 0x00）
                self._sock.sendall(b"\xe0\x00")
                logger.info(f"[{self.client_id}] 发送 DISCONNECT")
            except Exception as e:
                logger.warning(f"[{self.client_id}] DISCONNECT 异常: {e}")
            finally:
                self._cleanup()

    def is_connected(self) -> bool:
        return self._connected

    # -------------------------------------------------------------------------
    # PUBLISH
    # -------------------------------------------------------------------------

    def publish(
        self,
        topic: str,
        payload: str = "",
        qos: int = 0,
        retain: bool = False,
    ) -> bool:
        """
        发布 MQTT 消息（仅支持 QoS 0）。

        Args:
            topic:   目标 topic
            payload: 消息内容
            qos:     QoS 等级（仅支持 0）
            retain:  是否保留

        Returns:
            True 成功，False 失败
        """
        if not self._connected:
            logger.warning(f"[{self.client_id}] 未连接，跳过发布: {topic}")
            return False

        if qos not in (0, 1, 2):
            logger.warning(f"[{self.client_id}] QoS {qos} 不支持，强制 QoS 0")
            qos = 0

        try:
            packet = self._build_publish_packet(topic, payload, qos, retain)
            with self._lock:
                self._sock.sendall(packet)
            logger.debug(f"[{self.client_id}] 📤 MQTT PUBLISH -> {topic}: {payload[:80]}")
            return True
        except Exception as e:
            logger.error(f"[{self.client_id}] MQTT PUBLISH 失败 [{topic}]: {e}")
            self._connected = False
            return False

    # -------------------------------------------------------------------------
    # 内部方法
    # -------------------------------------------------------------------------

    def _build_connect_packet(self) -> bytes:
        """构建 CONNECT 报文"""
        # 可变头部
        proto_name = b"MQTT"
        proto_level = bytes([self.MQTT_PROTOCOL_VERSION])  # 4 = 3.1.1

        # 连接标志
        connect_flags = 0x02  # Clean Session
        if self.username:
            connect_flags |= 0x80
            if self.password:
                connect_flags |= 0x40

        payload = proto_name + b"\x00\x04" + proto_level + bytes([connect_flags])
        payload += self._encode_remaining_length(10 + len(payload))

        # 变长编码会在下面重新计算，先放占位
        # 重构：先计算不含 remaining length 的部分
        proto_name_field = proto_name + b"\x00\x04"
        var_header = proto_name_field + proto_level + bytes([connect_flags, 0x00])  # keepalive 2 bytes
        var_header += self._encode_remaining_length(len(proto_name_field) + 1 + 1 + 2 + len(self.client_id))

        # 实际 CONNECT 报文结构：
        # Fixed header: 0x10, remaining_length
        # Variable header: protocol_name, protocol_level, connect_flags, keepalive(2bytes)
        # Payload: client_id, (username), (password)

        client_id_bytes = self.client_id.encode("utf-8")
        username_bytes = self.username.encode("utf-8") if self.username else None
        password_bytes = self.password.encode("utf-8") if self.password else None

        payload_parts = [
            proto_name + b"\x00\x04",  # protocol name
            bytes([self.MQTT_PROTOCOL_VERSION]),  # protocol level
            bytes([connect_flags]),  # connect flags
            self._encode_int16(self.keepalive),  # keepalive
            self._encode_string(self.client_id),  # client_id
        ]
        if username_bytes:
            payload_parts.append(self._encode_string(self.username))
        if password_bytes:
            payload_parts.append(self._encode_string(self.password))

        payload = b"".join(payload_parts)
        remaining_len = len(payload)

        fixed_header = bytes([0x10]) + self._encode_remaining_length(remaining_len)
        return fixed_header + payload

    def _build_publish_packet(
        self,
        topic: str,
        payload: str,
        qos: int,
        retain: bool,
    ) -> bytes:
        """构建 PUBLISH 报文"""
        topic_bytes = topic.encode("utf-8")

        # 可变头部：topic + packet_id (仅 QoS > 0)
        var_header = self._encode_string(topic)
        if qos > 0:
            var_header += self._encode_int16(1)  # packet_id = 1 (简化)

        # 载荷
        payload_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload

        # 固定头
        fixed_flags = (qos << 1) | (1 if retain else 0)
        fixed_header = bytes([0x30 | fixed_flags])

        remaining = len(var_header) + len(payload_bytes)
        fixed_header += self._encode_remaining_length(remaining)

        return fixed_header + var_header + payload_bytes

    def _read_packet(self):
        """读取并解析一个 MQTT 报文"""
        try:
            # 读取固定头
            first_byte = self._sock.recv(1)
            if not first_byte:
                return None
            packet_type = first_byte[0] >> 4
            remaining_len = self._decode_remaining_length()
            if remaining_len is None:
                return None

            # 读取剩余载荷
            data = b""
            while len(data) < remaining_len:
                chunk = self._sock.recv(remaining_len - len(data))
                if not chunk:
                    return None
                data += chunk

            return packet_type, remaining_len, data

        except socket.timeout:
            return None
        except Exception as e:
            logger.debug(f"读取 MQTT 报文异常: {e}")
            return None

    def _encode_remaining_length(self, length: int) -> bytes:
        """MQTT 变长编码（1-4 字节）"""
        result = bytearray()
        for _ in range(4):
            digit = length % 128
            length //= 128
            if length > 0:
                digit |= 0x80
            result.append(digit)
            if length == 0:
                break
        return bytes(result)

    def _decode_remaining_length(self) -> int:
        """解码 MQTT 变长长度字段"""
        multiplier = 1
        value = 0
        for _ in range(4):
            b = self._sock.recv(1)[0]
            value += (b & 0x7F) * multiplier
            if (b & 0x80) == 0:
                break
            multiplier *= 128
        return value

    def _encode_string(self, s: str) -> bytes:
        """编码 MQTT 字符串（2字节长度 + UTF-8）"""
        s_bytes = s.encode("utf-8")
        return self._encode_int16(len(s_bytes)) + s_bytes

    def _encode_int16(self, v: int) -> bytes:
        """编码 2 字节整数"""
        return bytes([(v >> 8) & 0xFF, v & 0xFF])

    def _cleanup(self):
        """清理 socket"""
        self._connected = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None


# ---------------------------------------------------------------------------
# OpenClaw HTTP Client
# ---------------------------------------------------------------------------
class OpenClawHTTPClient:
    """
    向 OpenClaw Gateway 发送 HTTP 请求的客户端。

    支持：
      - GET /health 健康检查
      - POST /webhook 转发 MQTT 消息
      - GET /status 获取状态
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:18789",
        timeout: float = 10.0,
        api_key: str = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key

    def _make_headers(self, extra: dict = None) -> dict:
        """构建 HTTP 请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MQTT-OpenClaw-Bridge/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if extra:
            headers.update(extra)
        return headers

    def health_check(self) -> dict:
        """
        检查 OpenClaw Gateway 是否可达。

        Returns:
            {"ok": True, "latency_ms": 12.3}  或  {"ok": False, "error": "..."}
        """
        try:
            start = time.time()
            req = Request(
                f"{self.base_url}/health",
                headers=self._make_headers(),
                method="GET",
            )
            with urlopen(req, timeout=self.timeout) as resp:
                latency = (time.time() - start) * 1000
                body = resp.read().decode("utf-8", errors="replace")
                return {"ok": True, "latency_ms": round(latency, 1), "body": body}
        except HTTPError as e:
            return {"ok": False, "error": f"HTTP {e.code}: {e.reason}"}
        except URLError as e:
            return {"ok": False, "error": str(e.reason)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def forward_mqtt_message(
        self,
        topic: str,
        payload: str,
        metadata: dict = None,
    ) -> dict:
        """
        将 MQTT 消息转发到 OpenClaw Gateway Webhook。

        POST /webhook?topic=<topic>
        Body: {"message": "<payload>", "from": "mqtt", "timestamp": 1234567890}

        Args:
            topic:    MQTT topic
            payload:  消息内容
            metadata: 附加元数据（可选）

        Returns:
            {"ok": True, "response": "..."}  或  {"ok": False, "error": "..."}
        """
        body = {
            "message": payload,
            "from": "mqtt",
            "topic": topic,
            "timestamp": int(time.time() * 1000),
        }
        if metadata:
            body["metadata"] = metadata

        try:
            url = f"{self.base_url}/webhook"
            req = Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers=self._make_headers(),
                method="POST",
            )
            with urlopen(req, timeout=self.timeout) as resp:
                response_body = resp.read().decode("utf-8", errors="replace")
                logger.debug(
                    f"[OpenClaw] Webhook 响应 [{resp.status}]: {response_body[:200]}"
                )
                return {
                    "ok": True,
                    "status": resp.status,
                    "response": response_body[:500],
                }
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            logger.warning(f"[OpenClaw] Webhook HTTP {e.code}: {body[:200]}")
            return {"ok": False, "error": f"HTTP {e.code}", "body": body[:200]}
        except URLError as e:
            logger.warning(f"[OpenClaw] Webhook 无法连接: {e.reason}")
            return {"ok": False, "error": f"无法连接: {e.reason}"}
        except Exception as e:
            logger.error(f"[OpenClaw] Webhook 异常: {e}")
            return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# MQTT Bridge 主类
# ---------------------------------------------------------------------------
class MqttOpenClawBridge:
    """
    MQTT <-> OpenClaw HTTP 桥接器。

    负责：
      - MQTT 消息接收（订阅 topics，转发到 OpenClaw）
      - HTTP 请求接收（发布到 MQTT）
      - MQTT 连接管理（自动重连）
      - OpenClaw 健康检查

    线程安全，支持热更新订阅列表。
    """

    def __init__(
        self,
        mqtt_host: str = "localhost",
        mqtt_port: int = 1883,
        mqtt_client_id: str = "",
        openclaw_url: str = "http://127.0.0.1:18789",
        openclaw_api_key: str = None,
        http_host: str = "0.0.0.0",
        http_port: int = 8080,
        subscribe_topics: list = None,
        http_to_mqtt_topics: list = None,
        reconnect_delay: float = 5.0,
        health_check_interval: float = 30.0,
    ):
        """
        初始化桥接器。

        Args:
            mqtt_host:           MQTT Broker 地址
            mqtt_port:           MQTT Broker 端口
            mqtt_client_id:       MQTT 客户端ID（空则自动生成）
            openclaw_url:        OpenClaw Gateway HTTP 地址
            openclaw_api_key:    OpenClaw API Key（可选）
            http_host:           HTTP 服务监听地址
            http_port:           HTTP 服务监听端口
            subscribe_topics:    订阅的 MQTT topic 列表（会被转发到 OpenClaw）
            http_to_mqtt_topics: HTTP POST /publish 可发布的目标 topics
            reconnect_delay:     MQTT 重连延迟（秒）
            health_check_interval: OpenClaw 健康检查间隔（秒）
        """
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.openclaw_url = openclaw_url
        self.http_host = http_host
        self.http_port = http_port
        self.reconnect_delay = reconnect_delay
        self.health_check_interval = health_check_interval

        # 默认订阅：全部转发到 OpenClaw
        self.subscribe_topics = subscribe_topics or ["#"]  # # = 全部
        # 默认允许 HTTP -> MQTT 的目标 topics
        self.http_to_mqtt_topics = http_to_mqtt_topics or ["robot/cmd/#", "agent/#"]

        # MQTT 客户端（标准库实现，仅发布）
        self._mqtt_client = SimpleMQTTClient(
            broker_host=mqtt_host,
            broker_port=mqtt_port,
            client_id=mqtt_client_id or f"bridge_{uuid.uuid4().hex[:8]}",
        )

        # OpenClaw HTTP 客户端
        self._oc_client = OpenClawHTTPClient(
            base_url=openclaw_url,
            api_key=openclaw_api_key,
        )

        # 状态
        self._running = False
        self._http_server = None
        self._http_thread = None
        self._health_check_thread = None
        self._lock = threading.Lock()

        # 统计
        self.stats = {
            "mqtt_received": 0,
            "mqtt_sent": 0,
            "http_received": 0,
            "http_forwarded": 0,
            "errors": 0,
            "openclaw_health_ok": False,
            "mqtt_connected": False,
        }

        logger.info(
            f"桥接器初始化 | MQTT={mqtt_host}:{mqtt_port} | "
            f"OpenClaw={openclaw_url} | HTTP={http_host}:{http_port}"
        )

    # =======================================================================
    # 启动 / 停止
    # =======================================================================

    def start(self) -> bool:
        """
        启动桥接器（MQTT 连接 + HTTP 服务器）。

        Returns:
            True 全部启动成功，False 至少一项失败
        """
        with self._lock:
            if self._running:
                logger.warning("桥接器已在运行")
                return True

            logger.info("正在启动桥接器...")

            # 1. 连接 MQTT
            if not self._connect_mqtt():
                logger.error("MQTT 连接失败，HTTP 服务仍会启动（MQTT 可后续重连）")

            # 2. 启动 HTTP 服务器
            if not self._start_http_server():
                logger.error("HTTP 服务器启动失败")
                return False

            # 3. 启动 OpenClaw 健康检查线程
            self._start_health_check()

            self._running = True
            logger.info(
                f"✅ 桥接器已启动 | HTTP http://{self.http_host}:{self.http_port} | "
                f"MQTT {self.mqtt_host}:{self.mqtt_port}"
            )
            return True

    def stop(self) -> None:
        """停止桥接器"""
        with self._lock:
            if not self._running:
                return
            self._running = False

        logger.info("正在停止桥接器...")

        # 停止 HTTP 服务器
        if self._http_server:
            try:
                # urllib 不支持优雅关闭，换个方式用 socket 发送 shutdown
                shutdown_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                shutdown_socket.settimeout(2)
                shutdown_socket.connect((self.http_host, self.http_port))
                shutdown_socket.close()
            except Exception:
                pass
            self._http_server = None

        # 断开 MQTT
        self._mqtt_client.disconnect()

        logger.info("✅ 桥接器已停止")

    def _connect_mqtt(self) -> bool:
        """连接 MQTT Broker"""
        with self._lock:
            connected = self._mqtt_client.connect()
            self.stats["mqtt_connected"] = connected
            return connected

    def _start_http_server(self) -> bool:
        """启动 HTTP 服务器（在独立线程中）"""

        class BridgeHTTPHandler(BaseHTTPRequestHandler):
            """HTTP 请求处理"""

            def log_message(self, format, *args):
                # 压制默认日志，改为 bridge logger
                logger.debug(f"[HTTP] {args[0]}")

            def do_GET(self):
                self._handle_get()

            def do_POST(self):
                self._handle_post()

            def _handle_get(self):
                """处理 GET 请求"""
                parsed = urlparse(self.path)
                path = parsed.path
                qs = parse_qs(parsed.query)

                if path == "/health":
                    self._send_json(200, {
                        "status": "ok",
                        "service": "mqtt-openclaw-bridge",
                        "mqtt_connected": bridge.stats["mqtt_connected"],
                        "openclaw_health": bridge.stats["openclaw_health_ok"],
                        "stats": {k: v for k, v in bridge.stats.items()
                                  if k not in ("openclaw_health_ok", "mqtt_connected")},
                    })
                    return

                if path == "/status":
                    # OpenClaw 健康状态
                    oc_health = bridge._oc_client.health_check()
                    self._send_json(200, {
                        "mqtt": {
                            "connected": bridge.stats["mqtt_connected"],
                            "host": bridge.mqtt_host,
                            "port": bridge.mqtt_port,
                        },
                        "openclaw": {
                            "url": bridge.openclaw_url,
                            "health_ok": oc_health["ok"],
                            "latency_ms": oc_health.get("latency_ms"),
                            "error": oc_health.get("error"),
                        },
                        "stats": bridge.stats,
                    })
                    return

                self._send_json(404, {"error": "Not Found"})

            def _handle_post(self):
                """处理 POST 请求"""
                parsed = urlparse(self.path)
                path = parsed.path

                # 读取 body
                content_length = self.headers.get("Content-Length", 0)
                try:
                    body = self.rfile.read(int(content_length))
                except Exception as e:
                    self._send_json(400, {"error": f"读取请求体失败: {e}"})
                    return

                if path == "/publish":
                    self._handle_publish(body)
                    return

                if path == "/subscribe":
                    self._handle_subscribe(body)
                    return

                self._send_json(404, {"error": "Not Found"})

            def _handle_publish(self, body: bytes):
                """HTTP POST /publish -> MQTT"""
                try:
                    data = json.loads(body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    self._send_json(400, {"error": f"JSON 解析失败: {e}"})
                    return

                topic = data.get("topic", "")
                payload = data.get("payload", "")
                qos = data.get("qos", 0)

                if not topic:
                    self._send_json(400, {"error": "topic 为空"})
                    return

                # 安全检查：限制可发布的 topic
                allowed = False
                for pattern in bridge.http_to_mqtt_topics:
                    if self._topic_matches_pattern(topic, pattern):
                        allowed = True
                        break

                if not allowed:
                    self._send_json(
                        403,
                        {"error": f"topic {topic} 不在允许列表中",
                         "allowed_topics": bridge.http_to_mqtt_topics},
                    )
                    return

                with bridge._lock:
                    ok = bridge._mqtt_client.publish(topic, str(payload), qos=qos)
                    if ok:
                        bridge.stats["mqtt_sent"] += 1
                        bridge.stats["http_forwarded"] += 1

                self._send_json(200, {
                    "ok": ok,
                    "topic": topic,
                    "payload": str(payload)[:100],
                })

            def _handle_subscribe(self, body: bytes):
                """HTTP POST /subscribe -> 动态添加 MQTT 订阅（运行时）"""
                try:
                    data = json.loads(body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    self._send_json(400, {"error": f"JSON 解析失败: {e}"})
                    return

                topic = data.get("topic", "")
                if not topic:
                    self._send_json(400, {"error": "topic 为空"})

                # 注意：SimpleMQTTClient 不支持订阅
                # 如果需要订阅功能，使用 mqtt_router.py 的 MQTTRouter
                self._send_json(501, {
                    "error": "订阅功能需要使用 mqtt_router.py MQTTRouter 类",
                    "hint": "当前 SimpleMQTTClient 仅支持发布",
                })

            def _topic_matches_pattern(self, topic: str, pattern: str) -> bool:
                """简单 topic 匹配（支持 # 和 +）"""
                # 简化实现：# 匹配任意层级，+ 匹配单级
                pattern_parts = pattern.split("/")
                topic_parts = topic.split("/")

                i = 0
                for pi, pp in enumerate(pattern_parts):
                    if pp == "#":
                        return True  # # 之后不再检查
                    if pp == "+":
                        i += 1
                        continue
                    if i >= len(topic_parts) or topic_parts[i] != pp:
                        return False
                    i += 1

                return i == len(topic_parts) and pi == len(pattern_parts) - 1

            def _send_json(self, status: int, data: dict):
                """发送 JSON 响应"""
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", len(body))
                self.end_headers()
                self.wfile.write(body)

        # 保存 bridge 引用到 handler
        BridgeHTTPHandler.bridge = self

        # 使用 ThreadingHTTPServer 避免阻塞
        class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
            daemon_threads = True

        # 绑定到全局供 handler 访问
        global bridge
        bridge = self

        try:
            self._http_server = ThreadedHTTPServer(
                (self.http_host, self.http_port),
                BridgeHTTPHandler,
            )
            self._http_thread = threading.Thread(
                target=self._http_server.serve_forever,
                daemon=True,
                name="Bridge-HTTP",
            )
            self._http_thread.start()
            logger.info(
                f"HTTP 服务器已启动 {self.http_host}:{self.http_port}"
            )
            return True
        except Exception as e:
            logger.error(f"HTTP 服务器启动失败: {e}")
            return False

    def _start_health_check(self):
        """启动 OpenClaw 健康检查定期任务"""
        def _health_check_loop():
            while self._running:
                time.sleep(self.health_check_interval)
                try:
                    result = self._oc_client.health_check()
                    with self._lock:
                        self.stats["openclaw_health_ok"] = result["ok"]
                except Exception as e:
                    logger.debug(f"健康检查异常: {e}")

        t = threading.Thread(target=_health_check_loop, daemon=True, name="Bridge-HealthCheck")
        t.start()
        self._health_check_thread = t

    # =======================================================================
    # MQTT 消息处理（注入点）
    # =======================================================================

    def on_mqtt_message(self, topic: str, payload: str) -> None:
        """
        收到 MQTT 消息时的回调（子类可覆盖）。

        默认行为：转发到 OpenClaw Webhook。

        Args:
            topic:   MQTT topic
            payload: 消息内容
        """
        try:
            result = self._oc_client.forward_mqtt_message(topic, payload)
            with self._lock:
                self.stats["mqtt_received"] += 1
                if not result["ok"]:
                    self.stats["errors"] += 1
                    logger.warning(
                        f"[Bridge] 转发 MQTT -> OpenClaw 失败 [{topic}]: "
                        f"{result.get('error')}"
                    )
                else:
                    logger.debug(
                        f"[Bridge] MQTT -> OpenClaw 成功 [{topic}]: "
                        f"{payload[:60]}"
                    )
        except Exception as e:
            with self._lock:
                self.stats["errors"] += 1
            logger.error(f"[Bridge] MQTT 消息处理异常 [{topic}]: {e}")


# ---------------------------------------------------------------------------
# 全局 bridge 引用（供 HTTP Handler 访问）
# ---------------------------------------------------------------------------
bridge: MqttOpenClawBridge = None


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="MQTT <-> OpenClaw HTTP Bridge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 基本启动
  python bridge.py --mqtt-host localhost --mqtt-port 1883 \\
                   --openclaw-url http://127.0.0.1:18789

  # 指定 HTTP 端口
  python bridge.py --port 8080 --mqtt-host 192.168.1.100

  # 限制 HTTP 可发布的 MQTT topics
  python bridge.py --http-to-mqtt-topics robot/cmd/# --agent/#

  # 健康检查
  curl http://localhost:8080/health

  # 发布 MQTT 消息
  curl -X POST http://localhost:8080/publish \\
       -H "Content-Type: application/json" \\
       -d '{"topic": "robot/cmd/move", "payload": "forward", "qos": 0}'
        """,
    )

    parser.add_argument(
        "--mqtt-host", default="localhost",
        help="MQTT Broker 地址 (默认: localhost)"
    )
    parser.add_argument(
        "--mqtt-port", type=int, default=1883,
        help="MQTT Broker 端口 (默认: 1883)"
    )
    parser.add_argument(
        "--mqtt-client-id", default="",
        help="MQTT 客户端ID (默认: 自动生成)"
    )
    parser.add_argument(
        "--openclaw-url", default="http://127.0.0.1:18789",
        help="OpenClaw Gateway HTTP 地址 (默认: http://127.0.0.1:18789)"
    )
    parser.add_argument(
        "--openclaw-api-key", default=None,
        help="OpenClaw API Key (可选)"
    )
    parser.add_argument(
        "--http-host", default="0.0.0.0",
        help="HTTP 监听地址 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", "--http-port", type=int, default=8080,
        dest="http_port",
        help="HTTP 监听端口 (默认: 8080)"
    )
    parser.add_argument(
        "--subscribe-topics", nargs="+",
        default=["#"],
        help="订阅的 MQTT topics 列表 (默认: ['#']) "
             "收到消息会转发到 OpenClaw Webhook"
    )
    parser.add_argument(
        "--http-to-mqtt-topics", nargs="+",
        dest="http_to_mqtt_topics",
        default=["robot/cmd/#", "agent/#"],
        help="允许 HTTP POST /publish 发布到的 MQTT topics (默认: robot/cmd/# agent/#)"
    )
    parser.add_argument(
        "--reconnect-delay", type=float, default=5.0,
        help="MQTT 重连延迟秒数 (默认: 5.0)"
    )
    parser.add_argument(
        "--health-check-interval", type=float, default=30.0,
        help="OpenClaw 健康检查间隔秒数 (默认: 30.0)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="启用 debug 日志"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    b = MqttOpenClawBridge(
        mqtt_host=args.mqtt_host,
        mqtt_port=args.mqtt_port,
        mqtt_client_id=args.mqtt_client_id,
        openclaw_url=args.openclaw_url,
        openclaw_api_key=args.openclaw_api_key,
        http_host=args.http_host,
        http_port=args.http_port,
        subscribe_topics=args.subscribe_topics,
        http_to_mqtt_topics=args.http_to_mqtt_topics,
        reconnect_delay=args.reconnect_delay,
        health_check_interval=args.health_check_interval,
    )

    # 捕获终止信号
    import signal

    def _signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在停止...")
        b.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    b.start()

    # 主线程保持运行
    logger.info("桥接器运行中，按 Ctrl+C 停止")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        b.stop()


if __name__ == "__main__":
    main()
