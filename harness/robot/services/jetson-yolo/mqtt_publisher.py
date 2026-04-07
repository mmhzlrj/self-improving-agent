#!/usr/bin/env python3
"""
MQTT Publisher for YOLO Detection Results

该模块负责将 YOLO 检测结果通过 MQTT 协议发布到指定的 MQTT Broker。
适用于 Jetson 设备上的 YOLO 检测结果实时推送场景。

依赖:
    - paho-mqtt (pip install paho-mqtt)

使用方法:
    python mqtt_publisher.py --broker 192.168.1.100 --port 1883 --topic yolo/detections
"""

import argparse
import json
import time
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: paho-mqtt not installed. Install with: pip install paho-mqtt")
    sys.exit(1)


class YOLOMQTTPublisher:
    """
    YOLO 检测结果 MQTT 发布器
    
    将 YOLO 检测结果转换为 JSON 格式并通过 MQTT 发布。
    支持 QoS 配置、自动重连、连接状态回调等功能。
    """
    
    def __init__(
        self,
        broker: str = "localhost",
        port: int = 1883,
        topic: str = "yolo/detections",
        client_id: str = "yolo_publisher",
        qos: int = 1,
        retain: bool = False,
        keepalive: int = 60,
        clean_session: bool = True
    ):
        """
        初始化 MQTT 发布器
        
        Args:
            broker: MQTT Broker 地址
            port: MQTT Broker 端口
            topic: 发布主题
            client_id: 客户端 ID
            qos: 服务质量等级 (0, 1, 2)
            retain: 是否保留消息
            keepalive: 心跳间隔 (秒)
            clean_session: 是否清理会话
        """
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client_id = client_id
        self.qos = qos
        self.retain = retain
        self.keepalive = keepalive
        self.clean_session = clean_session
        
        # 创建 MQTT 客户端
        self.client = mqtt.Client(
            client_id=client_id,
            clean_session=clean_session,
            protocol=mqtt.MQTTv311
        )
        
        # 设置回调
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        
        # 连接状态
        self._is_connected = False
        self._last_error: Optional[str] = None
    
    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            self._is_connected = True
            print(f"[{datetime.now().isoformat()}] Connected to MQTT broker {self.broker}:{self.port}")
        else:
            self._is_connected = False
            self._last_error = f"Connection failed with code {rc}"
            error_msg = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }.get(rc, "Unknown error")
            print(f"[ERROR] MQTT connection failed: {error_msg} (rc={rc})")
    
    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self._is_connected = False
        if rc != 0:
            print(f"[WARNING] Unexpected disconnection from MQTT broker (rc={rc})")
        else:
            print(f"[{datetime.now().isoformat()}] Disconnected from MQTT broker")
    
    def _on_publish(self, client, userdata, mid):
        """发布回调"""
        print(f"[DEBUG] Message {mid} published successfully")
    
    def connect(self, timeout: int = 10) -> bool:
        """
        连接到 MQTT Broker
        
        Args:
            timeout: 连接超时时间 (秒)
            
        Returns:
            连接是否成功
        """
        try:
            print(f"Connecting to MQTT broker {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, keepalive=self.keepalive)
            self.client.loop_start()
            
            # 等待连接建立
            wait_time = 0
            while not self._is_connected and wait_time < timeout:
                time.sleep(0.1)
                wait_time += 0.1
            
            if not self._is_connected:
                self._last_error = f"Connection timeout after {timeout}s"
                return False
            
            return True
            
        except Exception as e:
            self._last_error = str(e)
            print(f"[ERROR] Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """断开 MQTT 连接"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self._is_connected = False
            print(f"[{datetime.now().isoformat()}] Disconnected from MQTT broker")
        except Exception as e:
            print(f"[ERROR] Error during disconnect: {e}")
    
    def publish_detection(
        self,
        detections: List[Dict[str, Any]],
        frame_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        发布检测结果
        
        Args:
            detections: 检测结果列表，每项包含:
                - class_name: 类别名称
                - confidence: 置信度
                - bbox: 边界框 [x1, y1, x2, y2]
            frame_id: 帧 ID (可选)
            timestamp: 时间戳 (可选，默认使用当前时间)
            metadata: 额外元数据 (可选)
            
        Returns:
            发布是否成功
        """
        if not self._is_connected:
            print("[ERROR] Not connected to MQTT broker")
            return False
        
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # 构建消息 payload
        payload = {
            "timestamp": timestamp,
            "detections": detections,
            "detection_count": len(detections)
        }
        
        if frame_id is not None:
            payload["frame_id"] = frame_id
        
        if metadata is not None:
            payload["metadata"] = metadata
        
        try:
            # 序列化并发布
            json_payload = json.dumps(payload, ensure_ascii=False)
            result = self.client.publish(
                topic=self.topic,
                payload=json_payload,
                qos=self.qos,
                retain=self.retain
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[DEBUG] Published {len(detections)} detections to {self.topic}")
                return True
            else:
                self._last_error = f"Publish failed with code {result.rc}"
                print(f"[ERROR] Failed to publish: {result.rc}")
                return False
                
        except Exception as e:
            self._last_error = str(e)
            print(f"[ERROR] Error publishing detection: {e}")
            return False
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._is_connected
    
    def get_last_error(self) -> Optional[str]:
        """获取最后错误信息"""
        return self._last_error


def publish_sample_detections(publisher: YOLOMQTTPublisher):
    """
    发布示例检测结果（用于测试）
    
    Args:
        publisher: MQTT 发布器实例
    """
    # 模拟 YOLO 检测结果
    sample_detections = [
        {
            "class_name": "person",
            "confidence": 0.95,
            "bbox": [100, 50, 300, 400]
        },
        {
            "class_name": "bottle",
            "confidence": 0.82,
            "bbox": [350, 200, 400, 350]
        },
        {
            "class_name": "cup",
            "confidence": 0.78,
            "bbox": [450, 220, 500, 300]
        }
    ]
    
    print("\nPublishing sample detections...")
    success = publisher.publish_detection(
        detections=sample_detections,
        frame_id="frame_001",
        metadata={"width": 640, "height": 480}
    )
    
    if success:
        print("Sample detections published successfully!")
    else:
        print("Failed to publish sample detections")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="MQTT Publisher for YOLO Detection Results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python mqtt_publisher.py --broker 192.168.1.100 --port 1883 --topic yolo/detections
  python mqtt_publisher.py -b localhost -p 1883 -t robot/yolo --qos 2
  python mqtt_publisher.py -b 192.168.1.100 --test  # 运行测试模式
        """
    )
    
    parser.add_argument(
        "-b", "--broker",
        default="localhost",
        help="MQTT broker address (default: localhost)"
    )
    
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=1883,
        help="MQTT broker port (default: 1883)"
    )
    
    parser.add_argument(
        "-t", "--topic",
        default="yolo/detections",
        help="MQTT topic to publish to (default: yolo/detections)"
    )
    
    parser.add_argument(
        "-c", "--client-id",
        default="yolo_publisher",
        help="MQTT client ID (default: yolo_publisher)"
    )
    
    parser.add_argument(
        "-q", "--qos",
        type=int,
        default=1,
        choices=[0, 1, 2],
        help="MQTT QoS level (default: 1)"
    )
    
    parser.add_argument(
        "-r", "--retain",
        action="store_true",
        help="Enable message retention"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (publish sample detections)"
    )
    
    args = parser.parse_args()
    
    # 创建发布器
    publisher = YOLOMQTTPublisher(
        broker=args.broker,
        port=args.port,
        topic=args.topic,
        client_id=args.client_id,
        qos=args.qos,
        retain=args.retain
    )
    
    # 连接
    if not publisher.connect():
        print("Failed to connect to MQTT broker")
        sys.exit(1)
    
    try:
        if args.test:
            # 测试模式：发布示例数据
            publish_sample_detections(publisher)
        else:
            # 交互模式
            print(f"\nMQTT Publisher running...")
            print(f"  Broker: {args.broker}:{args.port}")
            print(f"  Topic: {args.topic}")
            print(f"  QoS: {args.qos}")
            print(f"  Retain: {args.retain}")
            print("\nPress Ctrl+C to exit\n")
            
            # 持续运行，每5秒发布一次模拟数据
            while True:
                publish_sample_detections(publisher)
                time.sleep(5)
                
    except KeyboardInterrupt:
        print("\n\nReceived interrupt signal, shutting down...")
    finally:
        publisher.disconnect()
        print("Shutdown complete")


if __name__ == "__main__":
    main()