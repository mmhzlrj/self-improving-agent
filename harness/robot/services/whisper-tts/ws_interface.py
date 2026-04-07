#!/usr/bin/env python3
"""
WebSocket Interface for Whisper-TTS Service
WebSocket服务器/客户端，支持语音流

功能特性：
- WebSocket服务器：接收客户端语音流，处理后返回
- WebSocket客户端：连接远程服务器，发送语音流并接收响应
- 支持音频流式传输（pcm, wav, mp3, opus）
- 异步IO支持，高并发处理
- 连接池管理
- 心跳保活机制
- TLS/SSL加密支持
- CLI命令行界面
"""

import asyncio
import base64
import json
import logging
import ssl
import struct
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, AsyncIterator
from pathlib import Path
import argparse
import sys

# WebSocket库
try:
    import websockets
    from websockets.server import WebSocketServerProtocol, serve as ws_serve
    from websockets.client import connect as ws_connect
    from websockets.exceptions import (
        ConnectionClosed,
        InvalidStatusCode,
        NegotiationError,
    )
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logging.warning("websockets库未安装，请运行: pip install websockets")

# 可选的音频处理库
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import wave
    WAV_AVAILABLE = True
except ImportError:
    WAV_AVAILABLE = False

logger = logging.getLogger(__name__)


class AudioFormat(str, Enum):
    """支持的音频格式"""
    PCM = "pcm"           # 原始PCM字节流
    WAV = "wav"           # WAV格式
    MP3 = "mp3"           # MP3格式
    OPUS = "opus"         # Opus编码
    BASE64 = "base64"     # Base64编码音频


class MessageType(str, Enum):
    """WebSocket消息类型"""
    # 客户端 -> 服务器
    AUDIO = "audio"                   # 音频数据
    AUDIO_CHUNK = "audio_chunk"       # 音频分块
    TRANSCRIBE = "transcribe"          # 转写请求
    SYNTHESIZE = "synthesize"          # 合成请求
    STOP = "stop"                     # 停止处理
    PING = "ping"                     # 心跳
    
    # 服务器 -> 客户端
    TEXT = "text"                     # 识别/合成文本
    AUDIO_RESPONSE = "audio_response" # 音频响应
    TRANSCRIPT = "transcript"         # 转写结果
    PARTIAL = "partial"               # 部分结果
    COMPLETE = "complete"             # 处理完成
    ERROR = "error"                   # 错误信息
    PONG = "pong"                     # 心跳响应
    READY = "ready"                   # 服务就绪


@dataclass
class WSConfig:
    """WebSocket配置"""
    # 服务器配置
    host: str = "localhost"
    port: int = 8765
    ssl_cert: Optional[str] = None     # TLS证书路径
    ssl_key: Optional[str] = None     # TLS私钥路径
    
    # 客户端配置
    remote_url: Optional[str] = None   # 远程WebSocket服务器URL
    remote_auth: Optional[str] = None # 远程认证token
    
    # 通用配置
    max_connections: int = 100        # 最大连接数
    heartbeat_interval: float = 30.0  # 心跳间隔(秒)
    heartbeat_timeout: float = 300.0  # 心跳超时(秒)
    audio_format: AudioFormat = AudioFormat.PCM
    sample_rate: int = 16000          # 采样率
    channels: int = 1                 # 声道数
    sample_width: int = 2             # 采样宽度(字节)
    max_frame_size: int = 10 * 1024 * 1024  # 最大帧大小(10MB)
    read_buffer_size: int = 8192      # 读取缓冲区大小
    
    # 音频处理配置
    enable_vad: bool = True           # 启用VAD
    vad_threshold: float = 0.5        # VAD阈值
    silence_timeout: float = 0.5      # 静音超时(秒)
    
    # 日志配置
    log_level: str = "INFO"


@dataclass
class AudioFrame:
    """音频帧"""
    data: bytes
    format: AudioFormat = AudioFormat.PCM
    sample_rate: int = 16000
    channels: int = 1
    sample_width: int = 2
    timestamp: float = field(default_factory=time.time)
    is_final: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "data": base64.b64encode(self.data).decode() if isinstance(self.data, bytes) else self.data,
            "format": self.format.value,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "sample_width": self.sample_width,
            "timestamp": self.timestamp,
            "is_final": self.is_final,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AudioFrame":
        data = d["data"]
        if isinstance(data, str):
            data = base64.b64decode(data)
        return cls(
            data=data,
            format=AudioFormat(d.get("format", "pcm")),
            sample_rate=d.get("sample_rate", 16000),
            channels=d.get("channels", 1),
            sample_width=d.get("sample_width", 2),
            timestamp=d.get("timestamp", time.time()),
            is_final=d.get("is_final", False),
            metadata=d.get("metadata", {}),
        )


@dataclass 
class StreamSession:
    """流式会话"""
    session_id: str
    audio_chunks: List[AudioFrame] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_chunk(self, chunk: AudioFrame):
        self.audio_chunks.append(chunk)
        self.last_activity = time.time()
    
    def get_audio_bytes(self) -> bytes:
        """合并所有音频块"""
        return b"".join(chunk.data for chunk in self.audio_chunks)
    
    def clear(self):
        self.audio_chunks.clear()
        self.last_activity = time.time()


class WebSocketHandler:
    """WebSocket消息处理器基类"""
    
    def __init__(self, config: WSConfig):
        self.config = config
        self.sessions: Dict[str, StreamSession] = {}
    
    async def on_connect(self, ws: "WebSocketServerProtocol"):
        """客户端连接时调用"""
        client_ip = ws.remote_address[0] if ws.remote_address else "unknown"
        logger.info(f"客户端连接: {client_ip}")
    
    async def on_disconnect(self, ws: "WebSocketServerProtocol", reason: str):
        """客户端断开时调用"""
        client_ip = ws.remote_address[0] if ws.remote_address else "unknown"
        logger.info(f"客户端断开: {client_ip}, 原因: {reason}")
    
    async def on_message(self, ws: "WebSocketServerProtocol", msg_type: MessageType, data: Any, session_id: Optional[str] = None) -> Optional[Dict]:
        """处理接收到的消息，返回响应数据"""
        if msg_type == MessageType.PING:
            return {"type": MessageType.PONG.value, "timestamp": time.time()}
        
        if msg_type == MessageType.AUDIO or msg_type == MessageType.AUDIO_CHUNK:
            return await self._handle_audio(ws, data, session_id)
        
        if msg_type == MessageType.TRANSCRIBE:
            return await self._handle_transcribe(ws, data, session_id)
        
        if msg_type == MessageType.SYNTHESIZE:
            return await self._handle_synthesize(ws, data, session_id)
        
        if msg_type == MessageType.STOP:
            return await self._handle_stop(ws, session_id)
        
        return {"type": MessageType.ERROR.value, "message": f"未知消息类型: {msg_type}"}
    
    async def _handle_audio(self, ws, data: Any, session_id: Optional[str]) -> Dict:
        """处理音频数据"""
        try:
            if isinstance(data, dict):
                frame = AudioFrame.from_dict(data)
            else:
                frame = AudioFrame(data=data, format=self.config.audio_format)
            
            if session_id and session_id in self.sessions:
                self.sessions[session_id].add_chunk(frame)
            
            return {
                "type": MessageType.PARTIAL.value,
                "session_id": session_id,
                "timestamp": frame.timestamp,
                "chunk_size": len(frame.data),
            }
        except Exception as e:
            logger.error(f"处理音频数据失败: {e}")
            return {"type": MessageType.ERROR.value, "message": str(e)}
    
    async def _handle_transcribe(self, ws, data: Any, session_id: Optional[str]) -> Dict:
        """处理转写请求"""
        return {
            "type": MessageType.TRANSCRIPT.value,
            "session_id": session_id,
            "text": "",
            "is_final": True,
        }
    
    async def _handle_synthesize(self, ws, data: Any, session_id: Optional[str]) -> Dict:
        """处理合成请求"""
        return {
            "type": MessageType.TEXT.value,
            "session_id": session_id,
            "text": "",
        }
    
    async def _handle_stop(self, ws, session_id: Optional[str]) -> Dict:
        """处理停止请求"""
        if session_id and session_id in self.sessions:
            self.sessions[session_id].is_active = False
        return {"type": MessageType.COMPLETE.value, "session_id": session_id}


class WhisperTTSWebSocketServer:
    """Whisper-TTS WebSocket服务器"""
    
    def __init__(self, config: Optional[WSConfig] = None, handler: Optional[WebSocketHandler] = None):
        self.config = config or WSConfig()
        self.handler = handler or WebSocketHandler(self.config)
        self.server = None
        self.running = False
        self.connections: Dict[str, Any] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    
    async def start(self):
        """启动WebSocket服务器"""
        if not WEBSOCKETS_AVAILABLE:
            raise RuntimeError("websockets库不可用，请安装: pip install websockets")
        
        self.running = True
        
        # SSL配置
        ssl_context = None
        if self.config.ssl_cert and self.config.ssl_key:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(self.config.ssl_cert, self.config.ssl_key)
        
        logger.info(f"启动WebSocket服务器: {self.config.host}:{self.config.port}")
        
        self.server = await ws_serve(
            self._handle_client,
            self.config.host,
            self.config.port,
            ssl=ssl_context,
            max_size=self.config.max_frame_size,
            ping_interval=self.config.heartbeat_interval,
            ping_timeout=self.config.heartbeat_timeout,
        )
        
        logger.info(f"WebSocket服务器已启动，监听 {self.config.host}:{self.config.port}")
        
        try:
            await asyncio.Future()  # 永久运行
        except asyncio.CancelledError:
            await self.stop()
    
    async def stop(self):
        """停止WebSocket服务器"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("WebSocket服务器已停止")
    
    async def _handle_client(self, ws: "WebSocketServerProtocol", path: str):
        """处理客户端连接"""
        client_id = str(uuid.uuid4())
        self.connections[client_id] = ws
        
        await self.handler.on_connect(ws)
        
        try:
            async for raw_msg in ws:
                try:
                    # 解析消息
                    if isinstance(raw_msg, str):
                        msg = json.loads(raw_msg)
                        msg_type = MessageType(msg.get("type", ""))
                        msg_data = msg.get("data")
                        session_id = msg.get("session_id")
                    else:
                        # 二进制音频数据
                        msg_type = MessageType.AUDIO
                        msg_data = raw_msg
                        session_id = None
                    
                    # 处理消息
                    response = await self.handler.on_message(ws, msg_type, msg_data, session_id)
                    
                    # 发送响应
                    if response:
                        await ws.send(json.dumps(response))
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}")
                    await ws.send(json.dumps({"type": MessageType.ERROR.value, "message": "Invalid JSON"}))
                except Exception as e:
                    logger.error(f"处理消息失败: {e}", exc_info=True)
                    await ws.send(json.dumps({"type": MessageType.ERROR.value, "message": str(e)}))
                    
        except ConnectionClosed as e:
            reason = f"连接关闭: {e.code} {e.reason}"
        except Exception as e:
            reason = f"异常: {e}"
        finally:
            await self.handler.on_disconnect(ws, reason)
            if client_id in self.connections:
                del self.connections[client_id]
    
    async def broadcast(self, message: Dict):
        """广播消息到所有连接"""
        if self.connections:
            msg_str = json.dumps(message)
            await asyncio.gather(
                *[ws.send(msg_str) for ws in self.connections.values()],
                return_exceptions=True,
            )
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.connections)


class WhisperTTSWebSocketClient:
    """Whisper-TTS WebSocket客户端"""
    
    def __init__(self, config: Optional[WSConfig] = None):
        self.config = config or WSConfig()
        self.ws = None
        self.connected = False
        self.session_id = str(uuid.uuid4())
        self._receive_task = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._handlers: Dict[MessageType, Callable] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    
    async def connect(self, url: Optional[str] = None):
        """连接到WebSocket服务器"""
        if not WEBSOCKETS_AVAILABLE:
            raise RuntimeError("websockets库不可用，请安装: pip install websockets")
        
        server_url = url or self.config.remote_url
        if not server_url:
            raise ValueError("未指定服务器URL")
        
        # 构建URL
        if not server_url.startswith("ws://") and not server_url.startswith("wss://"):
            protocol = "wss://" if self.config.ssl_cert else "ws://"
            server_url = f"{protocol}{server_url}:{self.config.port}"
        
        # SSL配置
        ssl_context = None
        if server_url.startswith("wss://"):
            ssl_context = ssl.create_default_context()
            if self.config.ssl_cert:
                ssl_context.load_verify_locations(self.config.ssl_cert)
        
        # 认证头
        headers = {}
        if self.config.remote_auth:
            headers["Authorization"] = f"Bearer {self.config.remote_auth}"
        
        try:
            logger.info(f"连接WebSocket服务器: {server_url}")
            self.ws = await ws_connect(
                server_url,
                ssl=ssl_context,
                extra_headers=headers,
                max_size=self.config.max_frame_size,
                ping_interval=self.config.heartbeat_interval,
                ping_timeout=self.config.heartbeat_timeout,
            )
            self.connected = True
            logger.info(f"已连接到服务器")
            
            # 启动接收任务
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            # 发送就绪消息
            await self.send_message(MessageType.READY, {"session_id": self.session_id})
            
        except InvalidStatusCode as e:
            logger.error(f"连接失败，状态码: {e.code}")
            raise
        except Exception as e:
            logger.error(f"连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开连接"""
        self.connected = False
        
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self.ws:
            await self.ws.close()
            self.ws = None
        
        logger.info("已断开连接")
    
    async def _receive_loop(self):
        """接收消息循环"""
        try:
            async for raw_msg in self.ws:
                try:
                    if isinstance(raw_msg, str):
                        msg = json.loads(raw_msg)
                        msg_type = MessageType(msg.get("type", ""))
                        msg_data = msg.get("data", msg)
                        
                        # 调用处理器
                        if msg_type in self._handlers:
                            await self._handlers[msg_type](msg_data)
                        
                        # 放入队列
                        await self._message_queue.put((msg_type, msg_data))
                    else:
                        # 二进制音频数据
                        await self._message_queue.put((MessageType.AUDIO_RESPONSE, raw_msg))
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}")
                except Exception as e:
                    logger.error(f"处理消息失败: {e}", exc_info=True)
                    
        except ConnectionClosed as e:
            logger.warning(f"连接关闭: {e.code} {e.reason}")
            self.connected = False
        except asyncio.CancelledError:
            pass
    
    async def send_message(self, msg_type: MessageType, data: Any = None, session_id: Optional[str] = None):
        """发送消息"""
        if not self.ws or not self.connected:
            raise RuntimeError("未连接到服务器")
        
        msg = {
            "type": msg_type.value,
            "session_id": session_id or self.session_id,
            "timestamp": time.time(),
        }
        
        if data is not None:
            msg["data"] = data
        
        await self.ws.send(json.dumps(msg))
    
    async def send_audio(self, audio_data: bytes, is_final: bool = True, metadata: Optional[Dict] = None):
        """发送音频数据"""
        msg = {
            "type": MessageType.AUDIO.value,
            "session_id": self.session_id,
            "timestamp": time.time(),
            "is_final": is_final,
            "data": base64.b64encode(audio_data).decode() if isinstance(audio_data, bytes) else audio_data,
            "metadata": metadata or {},
        }
        
        await self.ws.send(json.dumps(msg))
    
    async def send_audio_chunk(self, audio_frame: AudioFrame):
        """发送音频帧"""
        await self.ws.send(json.dumps({
            "type": MessageType.AUDIO_CHUNK.value,
            "session_id": self.session_id,
            **audio_frame.to_dict(),
        }))
    
    async def stream_audio(self, audio_source: AsyncIterator[bytes], chunk_size: int = 4096):
        """流式发送音频"""
        async for chunk in audio_source:
            await self.send_audio(chunk, is_final=False)
        await self.send_audio(b"", is_final=True)
    
    def on_message(self, msg_type: MessageType, handler: Callable):
        """注册消息处理器"""
        self._handlers[msg_type] = handler
    
    async def receive(self, timeout: Optional[float] = None) -> Optional[tuple]:
        """接收消息（阻塞）"""
        try:
            if timeout:
                return await asyncio.wait_for(self._message_queue.get(), timeout)
            return await self._message_queue.get()
        except asyncio.TimeoutError:
            return None
    
    async def wait_for_response(self, expected_type: MessageType, timeout: float = 30.0) -> Optional[Dict]:
        """等待特定类型的响应"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.connected:
                return None
            
            try:
                msg_type, data = await self.receive(timeout=1.0)
                if msg_type == expected_type:
                    return data
            except asyncio.TimeoutError:
                continue
        
        return None


class AudioStreamClient(WhisperTTSWebSocketClient):
    """音频流客户端，专门用于流式音频处理"""
    
    async def transcribe_stream(self, audio_source: AsyncIterator[bytes]) -> AsyncIterator[str]:
        """流式转写音频源"""
        await self.connect()
        
        try:
            # 启动接收任务
            receive_task = asyncio.create_task(self._receive_loop())
            
            # 发送音频流
            async for chunk in audio_source:
                await self.send_audio(chunk, is_final=False)
            
            await self.send_audio(b"", is_final=True)
            
            # 接收转写结果
            partial_text = ""
            async for msg_type, data in self._message_queue:
                if msg_type == MessageType.PARTIAL:
                    text = data.get("text", "")
                    if text:
                        partial_text = text
                        yield text
                elif msg_type == MessageType.TRANSCRIPT:
                    text = data.get("text", "")
                    if text:
                        yield text
                    break
                elif msg_type == MessageType.ERROR:
                    raise RuntimeError(data.get("message", "Unknown error"))
                    
        finally:
            await self.disconnect()
    
    async def synthesize_stream(self, text: str) -> AsyncIterator[bytes]:
        """流式合成文本为音频"""
        await self.connect()
        
        try:
            # 发送合成请求
            await self.send_message(MessageType.SYNTHESIZE, {"text": text})
            
            # 接收音频流
            async for msg_type, data in self._message_queue:
                if msg_type == MessageType.AUDIO_RESPONSE:
                    if isinstance(data, bytes) and len(data) > 0:
                        yield data
                elif msg_type == MessageType.COMPLETE:
                    break
                elif msg_type == MessageType.ERROR:
                    raise RuntimeError(data.get("message", "Unknown error"))
                    
        finally:
            await self.disconnect()


class ConnectionPool:
    """WebSocket连接池"""
    
    def __init__(self, config: WSConfig, pool_size: int = 5):
        self.config = config
        self.pool_size = pool_size
        self.available: List[WhisperTTSWebSocketClient] = []
        self.in_use: List[WhisperTTSWebSocketClient] = []
        self.lock = asyncio.Lock()
    
    async def initialize(self):
        """初始化连接池"""
        for _ in range(self.pool_size):
            client = WhisperTTSWebSocketClient(self.config)
            await client.connect()
            self.available.append(client)
        logger.info(f"连接池已初始化，共{self.pool_size}个连接")
    
    async def acquire(self) -> WhisperTTSWebSocketClient:
        """获取连接"""
        async with self.lock:
            while not self.available:
                await asyncio.sleep(0.1)
            
            client = self.available.pop()
            self.in_use.append(client)
            return client
    
    async def release(self, client: WhisperTTSWebSocketClient):
        """释放连接"""
        async with self.lock:
            if client in self.in_use:
                self.in_use.remove(client)
                if client.connected:
                    self.available.append(client)
                else:
                    # 重新连接
                    await client.connect()
                    self.available.append(client)
    
    async def close(self):
        """关闭连接池"""
        async with self.lock:
            for client in self.available + self.in_use:
                await client.disconnect()
            self.available.clear()
            self.in_use.clear()


# CLI命令行界面
async def run_server(config: WSConfig):
    """运行服务器"""
    server = WhisperTTSWebSocketServer(config)
    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()


async def run_client(config: WSConfig, command: str, input_data: Optional[str] = None):
    """运行客户端"""
    client = WhisperTTSWebSocketClient(config)
    
    try:
        await client.connect()
        
        if command == "send":
            # 发送测试消息
            await client.send_message(MessageType.PING)
            response = await client.wait_for_response(MessageType.PONG)
            print(f"收到响应: {response}")
            
        elif command == "transcribe":
            # 转写测试
            if input_data and Path(input_data).exists():
                async def audio_gen():
                    with open(input_data, "rb") as f:
                        while chunk := f.read(4096):
                            yield chunk
                
                async for text in client.transcribe_stream(audio_gen()):
                    print(f"转写: {text}")
            
        elif command == "synthesize":
            # 合成测试
            text = input_data or "你好，这是一个测试。"
            async for audio in client.synthesize_stream(text):
                sys.stdout.buffer.write(audio)
        
    finally:
        await client.disconnect()


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="Whisper-TTS WebSocket Interface")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 服务器命令
    server_parser = subparsers.add_parser("server", help="启动WebSocket服务器")
    server_parser.add_argument("--host", default="localhost", help="监听地址")
    server_parser.add_argument("--port", type=int, default=8765, help="监听端口")
    server_parser.add_argument("--ssl-cert", help="TLS证书路径")
    server_parser.add_argument("--ssl-key", help="TLS私钥路径")
    server_parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    # 客户端命令
    client_parser = subparsers.add_parser("client", help="WebSocket客户端")
    client_parser.add_argument("--url", help="服务器URL")
    client_parser.add_argument("--command", choices=["send", "transcribe", "synthesize"], default="send")
    client_parser.add_argument("--input", help="输入文件")
    client_parser.add_argument("--auth", help="认证token")
    client_parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    args = parser.parse_args()
    
    if args.command == "server":
        config = WSConfig(
            host=args.host,
            port=args.port,
            ssl_cert=args.ssl_cert,
            ssl_key=args.ssl_key,
            log_level=args.log_level,
        )
        asyncio.run(run_server(config))
        
    elif args.command == "client":
        config = WSConfig(
            remote_url=args.url,
            remote_auth=args.auth,
            log_level=args.log_level,
        )
        asyncio.run(run_client(config, args.command, args.input))
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
