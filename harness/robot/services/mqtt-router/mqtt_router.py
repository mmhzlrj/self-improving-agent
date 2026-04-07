"""
mqtt_router.py - MQTT 连接 + 消息路由主逻辑

功能：
  - MQTT Broker 连接管理（连接/断开/重连）
  - 消息订阅与路由分发
  - Topic 过滤器支持（支持通配符 # / +）
  - 回调注册机制
  - 错误处理与日志记录

依赖：paho-mqtt (pip install paho-mqtt)
      标准库：logging, typing, time, threading, re
"""

import logging
import re
import threading
import time
from typing import Callable, Dict, List, Optional, Any

try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise ImportError("paho-mqtt is required. Install with: pip install paho-mqtt")

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logger = logging.getLogger("mqtt_router")


# ---------------------------------------------------------------------------
# 异常定义
# ---------------------------------------------------------------------------
class MqttRouterError(Exception):
    """MQTT 路由器的通用错误基类"""
    pass


class ConnectionError(MqttRouterError):
    """连接失败时抛出"""
    pass


class SubscriptionError(MqttRouterError):
    """订阅失败时抛出"""
    pass


# ---------------------------------------------------------------------------
# Topic 工具函数
# ---------------------------------------------------------------------------
def match_topic(filter_pattern: str, topic: str) -> bool:
    """
    判断 topic 是否匹配 filter_pattern。
    
    支持 MQTT 标准的通配符：
      - #  : 匹配任意层级（必须在 filter 最后）
      - +  : 匹配单一层级（可用于任意位置）
    
    Args:
        filter_pattern: 订阅过滤器，如 "home/+/temperature" 或 "sensor/#"
        topic:          实际 topic，如 "home/room1/temperature"
    
    Returns:
        bool: 是否匹配
    
    Examples:
        >>> match_topic("home/+/temperature", "home/room1/temperature")
        True
        >>> match_topic("home/#", "home/room1/temperature")
        True
        >>> match_topic("home/+/temperature", "home/room1/humidity")
        False
    """
    # 将 filter 转换为正则表达式
    # # -> [^/]+（匹配一级，但不能跨 slash）
    # + -> [^/]+（匹配一级）
    # 注意：MQTT # 实际匹配多级，但标准做法是逐级展开
    parts = filter_pattern.split("/")
    regex_parts = []
    for i, part in enumerate(parts):
        if part == "#":
            # # 只能在最后，表示匹配后续所有层级
            if i != len(parts) - 1:
                raise ValueError("'#' wildcard must be at the end of the filter")
            regex_parts.append("(?:[^/]+/)*[^/]+")  # 匹配零或多级
        elif part == "+":
            regex_parts.append("[^/]+")  # 匹配恰好一级
        else:
            # 转义特殊正则字符
            escaped = re.escape(part)
            regex_parts.append(escaped)
    
    regex = "^" + "/".join(regex_parts) + "$"
    return bool(re.match(regex, topic))


# ---------------------------------------------------------------------------
# MQTTRouter 主类
# ---------------------------------------------------------------------------
class MQTTRouter:
    """
    MQTT 消息路由器。
    
    管理与 Broker 的连接、订阅和消息路由。
    线程安全，支持多回调注册到同一 topic。
    
    使用示例：
        def on_message(topic, payload):
            print(f"[{topic}] {payload}")
        
        router = MQTTRouter(
            broker_host="localhost",
            broker_port=1883,
            client_id="my_router",
            keepalive=60,
        )
        router.subscribe("sensor/#", on_message)
        router.connect()
        
        # 主线程保持运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            router.disconnect()
    """
    
    # MQTT 错误码 -> 友好描述
    MQTT_ERRORS = {
        mqtt.CONNACK_ACCEPTED:         "连接成功",
        mqtt.CONNACK_REFUSED_PROTOCOL: "协议版本不支持",
        mqtt.CONNACK_REFUSED_ID:       "客户端ID被拒绝",
        mqtt.CONNACK_REFUSED_SERVER:   "服务器不可用",
        mqtt.CONNACK_REFUSED_USERNAME: "用户名/密码错误",
        mqtt.CONNACK_REFUSED_IMPLEMENTATION: "实现不支持",
    }
    
    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "",
        keepalive: int = 60,
        clean_session: bool = True,
        username: Optional[str] = None,
        password: Optional[str] = None,
        reconnect_delay: float = 5.0,
        max_reconnect_delay: float = 300.0,
        qos: int = 1,
    ):
        """
        初始化 MQTT 路由器。
        
        Args:
            broker_host:      Broker 地址
            broker_port:     Broker 端口（默认 1883）
            client_id:        客户端ID（空字符串则自动生成）
            keepalive:        保活心跳间隔（秒）
            clean_session:    是否清理会话
            username:         用户名（可选）
            password:         密码（可选）
            reconnect_delay:  首次重连延迟（秒）
            max_reconnect_delay: 最大重连延迟（秒）
            qos:              默认 QoS 等级（0/1/2）
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.keepalive = keepalive
        self.clean_session = clean_session
        self.username = username
        self.password = password
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay
        self.default_qos = max(0, min(2, qos))
        
        # 生成客户端ID（paho 要求非空且唯一）
        if not client_id:
            import uuid
            client_id = f"mqtt_router_{uuid.uuid4().hex[:8]}"
        self.client_id = client_id
        
        # 创建 paho-mqtt 客户端实例
        self._client: mqtt.Client = mqtt.Client(
            client_id=client_id,
            clean_session=clean_session,
            protocol=mqtt.MQTTv311,
        )
        
        # 设置认证
        if username and password:
            self._client.username_pw_set(username, password)
        
        # 绑定回调
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.on_subscribe = self._on_subscribe
        self._client.on_log = self._on_log
        
        # Topic 过滤器 -> 回调列表
        # 支持一个 filter 挂多个回调
        self._filters: Dict[str, List[Callable]] = {}
        # 实际向 Broker 订阅的 topic 集合（去重）
        self._subscribed_topics: Dict[str, int] = {}  # topic -> qos
        
        # 状态标志
        self._running = False
        self._connected = False
        self._reconnect_count = 0
        
        # 线程锁
        self._lock = threading.Lock()
        
        logger.info(
            f"[{client_id}] MQTTRouter 初始化完成 | "
            f"broker={broker_host}:{broker_port}"
        )
    
    # =======================================================================
    # 公开 API
    # =======================================================================
    
    def connect(self, will_topic: Optional[str] = None, will_payload: Optional[str] = None,
                will_qos: int = 0, will_retain: bool = False) -> None:
        """
        连接到 MQTT Broker。
        
        Args:
            will_topic:   遗嘱消息 topic（可选）
            will_payload: 遗嘱消息内容（可选）
            will_qos:     遗嘱消息 QoS（默认 0）
            will_retain:  遗嘱消息是否保留
        
        Raises:
            ConnectionError: 连接失败时抛出
        """
        # 设置遗嘱消息
        if will_topic:
            self._client.will_set(
                topic=will_topic,
                payload=will_payload or "",
                qos=will_qos,
                retain=will_retain,
            )
        
        try:
            logger.info(
                f"[{self.client_id}] 正在连接 {self.broker_host}:{self.broker_port}..."
            )
            # connect_async: 异步连接，不会阻塞
            self._client.connect_async(
                host=self.broker_host,
                port=self.broker_port,
                keepalive=self.keepalive,
            )
            self._client.loop_start()
        except Exception as e:
            logger.error(f"[{self.client_id}] 连接异常: {e}")
            raise ConnectionError(f"无法连接到 {self.broker_host}:{self.broker_port}") from e
    
    def disconnect(self) -> None:
        """
        断开连接并停止事件循环。
        """
        with self._lock:
            if not self._running:
                logger.info(f"[{self.client_id}] 已经处于断开状态")
                return
            self._running = False
        
        logger.info(f"[{self.client_id}] 正在断开连接...")
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception as e:
            logger.warning(f"[{self.client_id}] 断开连接时出现异常: {e}")
        finally:
            self._connected = False
            logger.info(f"[{self.client_id}] 已断开连接")
    
    def subscribe(
        self,
        topic_filter: str,
        callback: Callable[[str, Any], None],
        qos: Optional[int] = None,
    ) -> None:
        """
        订阅一个 topic 并注册回调。
        
        同一 topic_filter 可以多次调用，追加回调（而非覆盖）。
        
        Args:
            topic_filter: 订阅过滤器，支持 # 和 + 通配符
            callback:     回调函数，签名: callback(topic: str, payload: Any)
            qos:          QoS 等级（0/1/2），默认使用 self.default_qos
        
        Raises:
            SubscriptionError: 订阅失败时抛出
        """
        qos = qos if qos is not None else self.default_qos
        qos = max(0, min(2, qos))
        
        with self._lock:
            # 追加回调
            if topic_filter not in self._filters:
                self._filters[topic_filter] = []
            self._filters[topic_filter].append(callback)
            
            logger.info(
                f"[{self.client_id}] 注册订阅 [{topic_filter}] qos={qos} "
                f"(共 {len(self._filters[topic_filter])} 个回调)"
            )
            
            # 如果已连接，立即向 Broker 订阅
            if self._connected and topic_filter not in self._subscribed_topics:
                self._do_subscribe(topic_filter, qos)
    
    def unsubscribe(self, topic_filter: str, callback: Optional[Callable] = None) -> None:
        """
        取消订阅。
        
        Args:
            topic_filter: 要取消的过滤器
            callback:     要移除的特定回调（不传则移除全部该过滤器的回调）
        """
        with self._lock:
            if topic_filter not in self._filters:
                return
            
            if callback is None:
                # 移除所有回调
                del self._filters[topic_filter]
                logger.info(f"[{self.client_id}] 取消订阅 [{topic_filter}] (全部回调)")
            else:
                try:
                    self._filters[topic_filter].remove(callback)
                    logger.info(f"[{self.client_id}] 从 [{topic_filter}] 移除一个回调")
                    if not self._filters[topic_filter]:
                        del self._filters[topic_filter]
                except ValueError:
                    logger.warning(f"回调不在 [{topic_filter}] 中")
            
            # 如果没有回调了，向 Broker 取消订阅
            if topic_filter not in self._filters and topic_filter in self._subscribed_topics:
                try:
                    result, _ = self._client.unsubscribe(topic_filter)
                    if result == mqtt.MQTT_ERR_SUCCESS:
                        del self._subscribed_topics[topic_filter]
                        logger.info(f"[{self.client_id}] 向 Broker 取消订阅 [{topic_filter}]")
                    else:
                        logger.warning(
                            f"[{self.client_id}] 取消订阅失败: {result}"
                        )
                except Exception as e:
                    logger.error(f"取消订阅异常: {e}")
    
    def publish(
        self,
        topic: str,
        payload: Any = "",
        qos: int = 0,
        retain: bool = False,
    ) -> int:
        """
        发布一条消息。
        
        Args:
            topic:   目标 topic
            payload: 消息内容（会自动转为字符串）
            qos:     QoS 等级（0/1/2）
            retain:  是否保留
        
        Returns:
            mqtt.MQTT_ERR_SUCCESS (0) 表示成功，其他为错误码
        """
        if not self._connected:
            logger.warning(f"[{self.client_id}] 未连接，跳过发布到 {topic}")
            return -1
        
        # 序列化 payload
        if not isinstance(payload, (str, bytes, bytearray)):
            payload = str(payload)
        
        try:
            result = self._client.publish(
                topic=topic,
                payload=payload,
                qos=max(0, min(2, qos)),
                retain=retain,
            )
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"[{self.client_id}] 发布成功 -> {topic} [qos={qos}]")
            else:
                logger.warning(
                    f"[{self.client_id}] 发布失败 -> {topic} [rc={result.rc}]"
                )
            return result.rc
        except Exception as e:
            logger.error(f"发布消息异常: {e}")
            return -1
    
    def is_connected(self) -> bool:
        """返回当前是否已连接到 Broker"""
        return self._connected
    
    # =======================================================================
    # paho-mqtt 回调（内部）
    # =======================================================================
    
    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Dict,
        rc: int,
    ) -> None:
        """连接结果回调"""
        if rc == mqtt.CONNACK_ACCEPTED:
            self._connected = True
            self._reconnect_count = 0
            logger.info(
                f"[{self.client_id}] ✅ 已连接到 {self.broker_host}:{self.broker_port}"
            )
            
            # 恢复订阅
            with self._lock:
                for topic, qos in list(self._subscribed_topics.items()):
                    # topic 已在 subscribed_topics，直接跳过（避免重复订阅）
                    pass
                # 重新订阅所有已注册过滤器（处理重连后的恢复）
                for topic_filter in self._filters:
                    if topic_filter not in self._subscribed_topics:
                        self._do_subscribe(topic_filter, self._subscribed_topics.get(topic_filter, self.default_qos))
        else:
            err_msg = self.MQTT_ERRORS.get(rc, f"未知错误码({rc})")
            logger.error(
                f"[{self.client_id}] ❌ 连接被拒绝: {err_msg} [rc={rc}]"
            )
    
    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        rc: int,
    ) -> None:
        """断开连接回调"""
        self._connected = False
        was_running = self._running
        
        if rc == 0:
            logger.info(f"[{self.client_id}] 主动断开连接")
        else:
            logger.warning(
                f"[{self.client_id}] ⚠️ 非正常断开 [rc={rc}]，"
                f"将在 {self.reconnect_delay}s 后尝试重连..."
            )
            if was_running:
                self._schedule_reconnect()
    
    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """收到消息回调"""
        topic = msg.topic
        payload: Any = msg.payload
        
        # 尝试解码 payload
        try:
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
        except UnicodeDecodeError:
            payload = repr(payload)
        
        logger.debug(f"[{self.client_id}] 📩 收到 [{topic}]: {payload[:100]}")
        
        # 路由到匹配的过滤器
        with self._lock:
            filters = dict(self._filters)  # 复制避免持有锁时调用回调
        
        matched = False
        for filter_pattern, callbacks in filters.items():
            if match_topic(filter_pattern, topic):
                matched = True
                for cb in callbacks:
                    try:
                        cb(topic, payload)
                    except Exception as e:
                        logger.error(
                            f"[{self.client_id}] 回调异常 [{filter_pattern}]: {e}"
                        )
        
        if not matched:
            logger.debug(f"[{self.client_id}] 无匹配过滤器: {topic}")
    
    def _on_subscribe(
        self,
        client: mqtt.Client,
        userdata: Any,
        mid: int,
        granted_qos: List[int],
    ) -> None:
        """订阅确认回调"""
        logger.debug(f"[{self.client_id}] 订阅确认 [mid={mid}, qos={granted_qos}]")
    
    def _on_log(
        self,
        client: mqtt.Client,
        userdata: Any,
        level: int,
        buf: str,
    ) -> None:
        """MQTT 日志回调"""
        # 映射日志级别
        level_map = {
            mqtt.MQTT_LOG_DEBUG: logging.DEBUG,
            mqtt.MQTT_LOG_INFO:  logging.INFO,
            mqtt.MQTT_LOG_NOTICE: logging.INFO,
            mqtt.MQTT_LOG_WARNING: logging.WARNING,
            mqtt.MQTT_LOG_ERR:   logging.ERROR,
        }
        log_level = level_map.get(level, logging.INFO)
        logger.log(log_level, f"[{self.client_id}] {buf}")
    
    # =======================================================================
    # 内部辅助方法
    # =======================================================================
    
    def _do_subscribe(self, topic_filter: str, qos: int) -> None:
        """向 Broker 发送订阅请求（须在持有锁或已连接时调用）"""
        try:
            result, mid = self._client.subscribe(topic_filter, qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                self._subscribed_topics[topic_filter] = qos
                logger.info(
                    f"[{self.client_id}] 向 Broker 订阅 [{topic_filter}] qos={qos} [mid={mid}]"
                )
            else:
                logger.error(
                    f"[{self.client_id}] 订阅失败 [{topic_filter}]: rc={result}"
                )
                raise SubscriptionError(
                    f"订阅 [{topic_filter}] 失败，rc={result}"
                )
        except SubscriptionError:
            raise
        except Exception as e:
            logger.error(f"订阅异常 [{topic_filter}]: {e}")
            raise SubscriptionError(f"订阅 [{topic_filter}] 异常") from e
    
    def _schedule_reconnect(self) -> None:
        """计划重连（带指数退避）"""
        self._reconnect_count += 1
        
        # 指数退避：delay * 2^(attempt-1)，上限 max_reconnect_delay
        delay = min(
            self.reconnect_delay * (2 ** (self._reconnect_count - 1)),
            self.max_reconnect_delay,
        )
        logger.info(
            f"[{self.client_id}] 重连倒计时 {delay:.1f}s "
            f"(第 {self._reconnect_count} 次)"
        )
        
        def _reconnect_task():
            time.sleep(delay)
            if self._running and not self._connected:
                try:
                    logger.info(f"[{self.client_id}] 尝试重连...")
                    self._client.reconnect()
                except Exception as e:
                    logger.error(f"[{self.client_id}] 重连失败: {e}")
                    self._schedule_reconnect()
        
        thread = threading.Thread(target=_reconnect_task, daemon=True)
        thread.start()


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------
def create_router(
    broker_host: str = "localhost",
    broker_port: int = 1883,
    **kwargs,
) -> MQTTRouter:
    """
    工厂函数：创建并连接 MQTTRouter。
    
    等同于:
        router = MQTTRouter(broker_host, broker_port, **kwargs)
        router.connect()
    """
    router = MQTTRouter(broker_host=broker_host, broker_port=broker_port, **kwargs)
    router.connect()
    return router
