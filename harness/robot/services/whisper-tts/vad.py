#!/usr/bin/env python3
"""
vad.py - Voice Activity Detection (VAD) 静音检测服务

功能：检测音频中的语音活动，支持多种 VAD 算法
依赖：pyaudio, numpy (pip install)
特性：
    - 多算法支持：能量检测、WebRTC VAD、Silero VAD
    - 帧级和语音级检测
    - 实时流式处理
    - 静音阈值自动调整
    - CLI 和 API 双接口
"""

import subprocess
import os
import sys
import wave
import struct
import threading
import time
import io
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


# ---------------------------------------------------------------------------
# 异常定义
# ---------------------------------------------------------------------------
class VADError(Exception):
    """VAD 服务的通用错误基类"""
    pass


class VADUnavailableError(VADError):
    """VAD 引擎不可用时抛出"""
    pass


class AudioProcessingError(VADError):
    """音频处理失败时抛出"""
    pass


# ---------------------------------------------------------------------------
# VAD 算法枚举
# ---------------------------------------------------------------------------
class VADEngine(Enum):
    """支持的 VAD 算法"""
    ENERGY = "energy"           # 能量检测（基础，简单快速）
    WEBRTC = "webrtc"          # WebRTC VAD（精确，跨平台）
    SILERO = "silero"          # Silero VAD（深度学习模型，精度最高）


@dataclass
class VADConfig:
    """VAD 配置参数"""
    # 通用参数
    sample_rate: int = 16000           # 采样率 (Hz)
    frame_duration_ms: int = 30        # 帧时长 (ms)
    channels: int = 1                   # 声道数
    
    # 能量检测参数
    energy_threshold: float = 0.01     # 能量阈值 (0-1)
    energy_threshold_dynamic: bool = True  # 是否动态调整阈值
    energy_min_threshold: float = 0.005  # 动态阈值最小值
    energy_max_threshold: float = 0.1   # 动态阈值最大值
    
    # WebRTC VAD 参数
    webrtc_aggressiveness: int = 1      # 激进程度 (0-3)
    
    # Silero VAD 参数
    silero_threshold: float = 0.5       # Silero 置信度阈值
    silero_min_speech_duration_ms: int = 250  # 最小语音时长 (ms)
    silero_min_silence_duration_ms: int = 200  # 最小静音时长 (ms)
    
    # 语音检测参数
    min_speech_duration_ms: int = 250   # 最小语音片段时长
    min_silence_duration_ms: int = 200  # 判定为静音的最小静音时长
    max_speech_duration_s: float = 60.0 # 最大语音片段时长
    
    # 前端处理
    preprocessing_enabled: bool = True  # 是否启用预处理
    noise_reduction: bool = True        # 降噪


# 默认配置
DEFAULT_CONFIG = VADConfig()


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def calculate_rms(audio_data: bytes, sample_width: int = 2) -> float:
    """
    计算音频数据的 RMS 能量
    
    Args:
        audio_data: 原始音频字节数据
        sample_width: 采样宽度（字节）
    
    Returns:
        float: RMS 能量值 (0-1)
    """
    if not audio_data:
        return 0.0
    
    num_samples = len(audio_data) // sample_width
    if num_samples == 0:
        return 0.0
    
    fmt = "<" + str(num_samples) + "h"
    try:
        samples = struct.unpack(fmt, audio_data)
    except struct.error:
        return 0.0
    
    sum_squares = sum(sample ** 2 for sample in samples)
    rms = (sum_squares / num_samples) ** 0.5 / 32768.0
    return max(0.0, min(1.0, rms))


def rms_to_db(rms: float) -> float:
    """RMS 转换为分贝"""
    if rms <= 0:
        return -100.0
    return 20 * (rms ** 0.5) if rms > 0 else -100


def bytes_to_samples(audio_bytes: bytes, channels: int = 1) -> List[int]:
    """将字节数据转换为采样值列表"""
    num_samples = len(audio_bytes) // 2  # 16-bit
    fmt = "<" + str(num_samples) + "h"
    try:
        return list(struct.unpack(fmt, audio_bytes))
    except struct.error:
        return []


def samples_to_bytes(samples: List[int]) -> bytes:
    """将采样值列表转换为字节数据"""
    if not samples:
        return b""
    fmt = "<" + str(len(samples)) + "h"
    return struct.pack(fmt, *samples)


# ---------------------------------------------------------------------------
# 能量检测 VAD
# ---------------------------------------------------------------------------
class EnergyVAD:
    """
    基于能量检测的 VAD
    
    原理：计算每个帧的 RMS 能量，高于阈值判定为语音
    优点：计算简单，速度快，适用于安静环境
    缺点：在噪声环境下效果较差
    """
    
    def __init__(self, config: VADConfig):
        self.config = config
        self._reset()
    
    def _reset(self):
        """重置内部状态"""
        self.current_threshold = self.config.energy_threshold
        self.frame_count = 0
        self.energy_history: List[float] = []
        self.noise_level = 0.0
    
    def update_threshold(self, rms: float):
        """
        动态更新能量阈值
        
        基于滑动窗口的噪声估计
        """
        if not self.config.energy_threshold_dynamic:
            return
        
        self.energy_history.append(rms)
        # 保持最近 100 帧的历史
        if len(self.energy_history) > 100:
            self.energy_history.pop(0)
        
        # 使用中位数作为噪声基准
        if len(self.energy_history) >= 10:
            sorted_energy = sorted(self.energy_history)
            mid = len(sorted_energy) // 2
            self.noise_level = sorted_energy[mid]
            # 阈值 = 噪声基准 + 固定偏移
            self.current_threshold = max(
                self.config.energy_min_threshold,
                min(self.config.energy_max_threshold,
                    self.noise_level * 3.0)
            )
    
    def detect_frame(self, audio_frame: bytes) -> bool:
        """
        检测单帧是否为语音
        
        Args:
            audio_frame: 音频帧数据
        
        Returns:
            bool: True 表示语音，False 表示静音
        """
        rms = calculate_rms(audio_frame)
        self.update_threshold(rms)
        self.frame_count += 1
        return rms > self.current_threshold


# ---------------------------------------------------------------------------
# WebRTC VAD 包装器
# ---------------------------------------------------------------------------
class WebRTCVAD:
    """
    WebRTC VAD 包装器
    
    需要 webrtcvad 库: pip install webrtcvad
    支持 10ms, 20ms, 30ms 帧时长
    4 种激进程度模式
    """
    
    def __init__(self, config: VADConfig):
        self.config = config
        self._vad = None
        self._check_available()
    
    def _check_available(self) -> bool:
        """检查 WebRTC VAD 是否可用"""
        try:
            import webrtcvad
            self._vad = webrtcvad.Vad()
            self._vad.set_mode(self.config.webrtc_aggressiveness)
            return True
        except ImportError:
            self._vad = None
            return False
    
    def is_available(self) -> bool:
        """VAD 是否可用"""
        return self._vad is not None
    
    def detect_frame(self, audio_frame: bytes, sample_rate: int = 16000) -> bool:
        """
        检测单帧是否为语音
        
        Args:
            audio_frame: 音频帧数据
            sample_rate: 采样率
        
        Returns:
            bool: True 表示语音，False 表示静音
        """
        if not self._vad:
            return False
        
        try:
            # WebRTC VAD 只支持特定帧时长
            frame_duration = self.config.frame_duration_ms
            if frame_duration not in [10, 20, 30]:
                frame_duration = 30
            
            # 计算该帧的样本数
            num_samples = int(sample_rate * frame_duration / 1000)
            bytes_per_sample = 2  # 16-bit
            expected_len = num_samples * bytes_per_sample
            
            # 截断或填充到固定长度
            if len(audio_frame) > expected_len:
                audio_frame = audio_frame[:expected_len]
            elif len(audio_frame) < expected_len:
                audio_frame = audio_frame + b'\x00' * (expected_len - len(audio_frame))
            
            return self._vad.is_speech(audio_frame, sample_rate)
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Silero VAD 包装器
# ---------------------------------------------------------------------------
class SileroVAD:
    """
    Silero VAD 包装器
    
    使用 Silero AI 的深度学习 VAD 模型
    需要: pip install torch torchaudio
    模型会自动下载
    """
    
    def __init__(self, config: VADConfig):
        self.config = config
        self._model = None
        self._torch = None
        self._check_available()
    
    def _check_available(self) -> bool:
        """检查 Silero VAD 是否可用"""
        try:
            import torch
            import torchaudio
            self._torch = torch
            return True
        except ImportError:
            self._torch = None
            return False
    
    def is_available(self) -> bool:
        """VAD 是否可用"""
        return self._torch is not None
    
    def _load_model(self):
        """加载 Silero VAD 模型"""
        if self._model is not None:
            return
        
        try:
            # Silero VAD 模型
            torch = self._torch
            torch.hub.set_dir(os.path.expanduser("~/.cache/torch/hub"))
            self._model, utils = torch.hub.load(
                'snakers4/silero-vad',
                'silero_vad'
            )
            self._model.eval()
            self._get_speech_timestamps = utils[0]
        except Exception as e:
            print(f"警告: Silero VAD 模型加载失败: {e}")
            self._model = None
    
    def detect_speech_timestamps(
        self,
        audio_data: Union[bytes, List[int]],
        sample_rate: int = 16000
    ) -> List[Dict[str, Any]]:
        """
        检测语音片段时间戳
        
        Args:
            audio_data: 音频数据（字节或采样值列表）
            sample_rate: 采样率
        
        Returns:
            List[Dict]: 语音片段列表，每项包含 start/end 时间戳
        """
        if not self.is_available():
            return []
        
        self._load_model()
        if self._model is None:
            return []
        
        try:
            # 转换为 torch Tensor
            torch = self._torch
            
            if isinstance(audio_data, bytes):
                # 字节转采样值
                samples = bytes_to_samples(audio_data)
            else:
                samples = audio_data
            
            # 转换为 Tensor
            tensor = torch.tensor(samples, dtype=torch.float32) / 32768.0
            
            # 调整到模型期望的采样率
            if sample_rate != 16000:
                # 简单的重采样
                ratio = 16000 / sample_rate
                new_length = int(len(tensor) * ratio)
                indices = torch.linspace(0, len(tensor) - 1, new_length).long()
                tensor = tensor[indices]
            
            # 获取语音时间戳
            speech_timestamps = self._get_speech_timestamps(
                tensor,
                model=self._model,
                threshold=self.config.silero_threshold,
                min_speech_duration_ms=self.config.silero_min_speech_duration_ms,
                min_silence_duration_ms=self.config.silero_min_silence_duration_ms,
                sampling_rate=16000
            )
            
            return [
                {
                    "start": item["start"] / 16000,  # 转换为秒
                    "end": item["end"] / 16000,
                    "duration": (item["end"] - item["start"]) / 16000
                }
                for item in speech_timestamps
            ]
        except Exception as e:
            print(f"Silero VAD 检测失败: {e}")
            return []


# ---------------------------------------------------------------------------
# 主 VAD 类
# ---------------------------------------------------------------------------
class VAD:
    """
    Voice Activity Detection (VAD) 静音检测服务
    
    支持多种 VAD 算法，自动选择可用的最佳引擎
    提供帧级和语音级检测
    """

    def __init__(
        self,
        config: Optional[VADConfig] = None,
        engine: VADEngine = VADEngine.ENERGY
    ):
        """
        初始化 VAD 服务
        
        Args:
            config: VAD 配置，默认使用 DEFAULT_CONFIG
            engine: 使用的 VAD 算法引擎
        """
        self.config = config or DEFAULT_CONFIG
        self.engine = engine
        
        # 初始化各引擎
        self._energy_vad = EnergyVAD(self.config)
        self._webrtc_vad = WebRTCVAD(self.config)
        self._silero_vad = SileroVAD(self.config)
        
        # 状态
        self._is_speaking = False
        self._speech_frames: List[bytes] = []
        self._current_speech_start = 0
        self._silence_frames = 0
        
        # 帧大小计算
        self._frame_size = int(self.config.sample_rate * self.config.frame_duration_ms / 1000 * 2)  # bytes
    
    @property
    def frame_size(self) -> int:
        """帧大小（字节）"""
        return self._frame_size
    
    @property
    def frame_duration_ms(self) -> int:
        """帧时长（毫秒）"""
        return self.config.frame_duration_ms
    
    def get_available_engines(self) -> List[VADEngine]:
        """获取当前可用的 VAD 引擎"""
        engines = [VADEngine.ENERGY]  # 能量检测始终可用
        if self._webrtc_vad.is_available():
            engines.append(VADEngine.WEBRTC)
        if self._silero_vad.is_available():
            engines.append(VADEngine.SILERO)
        return engines
    
    def detect_frame(self, audio_frame: bytes) -> bool:
        """
        检测单帧是否为语音
        
        Args:
            audio_frame: 音频帧数据
        
        Returns:
            bool: True 表示语音，False 表示静音
        """
        if self.engine == VADEngine.WEBRTC:
            if self._webrtc_vad.is_available():
                return self._webrtc_vad.detect_frame(
                    audio_frame, self.config.sample_rate
                )
        
        # 默认使用能量检测
        return self._energy_vad.detect_frame(audio_frame)
    
    def detect_speech_timestamps(
        self,
        audio_data: Union[bytes, List[int]],
        sample_rate: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        检测音频中的语音片段时间戳
        
        Args:
            audio_data: 音频数据（字节或采样值列表）
            sample_rate: 采样率
        
        Returns:
            List[Dict]: 语音片段列表
        """
        sr = sample_rate or self.config.sample_rate
        
        if self.engine == VADEngine.SILERO and self._silero_vad.is_available():
            return self._silero_vad.detect_speech_timestamps(audio_data, sr)
        
        # 回退到帧级检测
        return self._frame_level_detection(audio_data, sr)
    
    def _frame_level_detection(
        self,
        audio_data: Union[bytes, List[int]],
        sample_rate: int
    ) -> List[Dict[str, Any]]:
        """
        基于帧级检测的语音片段识别
        
        Args:
            audio_data: 音频数据
            sample_rate: 采样率
        
        Returns:
            List[Dict]: 语音片段列表
        """
        if isinstance(audio_data, bytes):
            samples = bytes_to_samples(audio_data)
        else:
            samples = audio_data
        
        # 重采样（如果需要）
        if sample_rate != self.config.sample_rate:
            ratio = self.config.sample_rate / sample_rate
            new_length = int(len(samples) * ratio)
            indices = [int(i * ratio) for i in range(new_length)]
            samples = [samples[i] for i in indices if i < len(samples)]
        
        # 转换为帧
        bytes_per_sample = 2
        frame_size = int(sample_rate * self.config.frame_duration_ms / 1000) * bytes_per_sample
        
        speech_timestamps = []
        speech_start = None
        silence_frames = 0
        min_speech_frames = int(self.config.min_speech_duration_ms / self.config.frame_duration_ms)
        min_silence_frames = int(self.config.min_silence_duration_ms / self.config.frame_duration_ms)
        
        for i in range(0, len(samples) * bytes_per_sample - frame_size, frame_size):
            frame_bytes = samples_to_bytes(samples[i // bytes_per_sample:(i + frame_size) // bytes_per_sample])
            is_speech = self.detect_frame(frame_bytes)
            
            if is_speech:
                if speech_start is None:
                    speech_start = i / bytes_per_sample / sample_rate
                silence_frames = 0
            else:
                if speech_start is not None:
                    silence_frames += 1
                    if silence_frames >= min_silence_frames:
                        # 语音片段结束
                        speech_end = (i - silence_frames * frame_size) / bytes_per_sample / sample_rate
                        duration = speech_end - speech_start
                        if duration >= self.config.min_speech_duration_ms / 1000:
                            speech_timestamps.append({
                                "start": speech_start,
                                "end": speech_end,
                                "duration": duration
                            })
                        speech_start = None
                        silence_frames = 0
        
        # 处理最后一段语音
        if speech_start is not None:
            speech_end = len(samples) / sample_rate
            duration = speech_end - speech_start
            if duration >= self.config.min_speech_duration_ms / 1000:
                speech_timestamps.append({
                    "start": speech_start,
                    "end": speech_end,
                    "duration": duration
                })
        
        return speech_timestamps
    
    def process_audio_file(
        self,
        audio_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        keep_speech_only: bool = True
    ) -> Dict[str, Any]:
        """
        处理音频文件，检测语音片段
        
        Args:
            audio_path: 输入音频文件路径
            output_path: 输出文件路径（保留语音片段的音频）
            keep_speech_only: 是否只保留语音部分
        
        Returns:
            Dict[str, Any]: 处理结果
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {audio_path}",
                "speech_timestamps": []
            }
        
        try:
            # 读取 WAV 文件
            with wave.open(str(audio_path), 'rb') as wf:
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                
                # 读取所有帧
                frames = []
                while True:
                    frame = wf.readframes(1024)
                    if not frame:
                        break
                    frames.append(frame)
                
                audio_data = b''.join(frames)
            
            # 检测语音时间戳
            speech_timestamps = self.detect_speech_timestamps(audio_data, sample_rate)
            
            result = {
                "success": True,
                "audio_path": str(audio_path),
                "sample_rate": sample_rate,
                "channels": channels,
                "duration": len(audio_data) / (sample_rate * channels * sample_width),
                "speech_timestamps": speech_timestamps,
                "speech_count": len(speech_timestamps),
                "total_speech_duration": sum(s["duration"] for s in speech_timestamps)
            }
            
            # 如果需要输出文件
            if output_path and keep_speech_only:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 只保留语音部分
                with wave.open(str(audio_path), 'rb') as wf:
                    orig_sample_rate = wf.getframerate()
                    orig_channels = wf.getnchannels()
                    orig_sample_width = wf.getsampwidth()
                    
                    speech_frames = []
                    current_pos = 0
                    frame_duration = self.config.frame_duration_ms / 1000.0
                    
                    for segment in speech_timestamps:
                        start_time = segment["start"]
                        end_time = segment["end"]
                        
                        # 计算帧位置
                        start_frame = int(start_time / frame_duration)
                        end_frame = int(end_time / frame_duration)
                        
                        # 读取对应帧
                        wf.setpos(start_frame)
                        while wf.tell() < end_frame:
                            f = wf.readframes(1024)
                            if not f:
                                break
                            speech_frames.append(f)
                
                # 写入输出文件
                with wave.open(str(output_path), 'wb') as wf:
                    wf.setnchannels(orig_channels)
                    wf.setsampwidth(orig_sample_width)
                    wf.setframerate(orig_sample_rate)
                    for frame in speech_frames:
                        wf.writeframes(frame)
                
                result["output_path"] = str(output_path)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"处理失败: {str(e)}",
                "speech_timestamps": []
            }
    
    def stream_detect(
        self,
        callback: Callable[[bool, float], None]
    ):
        """
        创建流式检测上下文管理器
        
        用于实时音频流处理
        
        Args:
            callback: 回调函数，参数为 (is_speech, timestamp)
                     is_speech: True 表示语音，False 表示静音
                     timestamp: 当前时间戳（秒）
        
        Returns:
            StreamDetector: 流式检测器对象
        """
        return StreamDetector(self, callback, self.config)


class StreamDetector:
    """
    流式 VAD 检测器
    
    用于实时音频流的语音检测
    """
    
    def __init__(
        self,
        vad: VAD,
        callback: Callable[[bool, float], None],
        config: VADConfig
    ):
        self.vad = vad
        self.callback = callback
        self.config = config
        self._is_running = False
        self._audio_frames: List[bytes] = []
        self._start_time = 0.0
    
    def __enter__(self):
        self._is_running = True
        self._start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._is_running = False
    
    def process_frame(self, audio_frame: bytes):
        """
        处理一帧音频
        
        Args:
            audio_frame: 音频帧数据
        """
        if not self._is_running:
            return
        
        is_speech = self.vad.detect_frame(audio_frame)
        timestamp = time.time() - self._start_time
        self.callback(is_speech, timestamp)
    
    def process_audio_chunk(self, audio_data: bytes):
        """
        处理一段音频数据
        
        自动分割为帧并处理
        
        Args:
            audio_data: 音频数据
        """
        if not self._is_running:
            return
        
        frame_size = self.vad.frame_size
        timestamp = time.time() - self._start_time
        
        for i in range(0, len(audio_data) - frame_size, frame_size):
            frame = audio_data[i:i + frame_size]
            is_speech = self.vad.detect_frame(frame)
            self.callback(is_speech, timestamp + i / (self.config.sample_rate * 2))


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------
def detect_silence(
    audio_path: Union[str, Path],
    threshold: float = 0.01,
    min_silence_duration: float = 2.0
) -> Dict[str, Any]:
    """
    检测音频中的静音区域
    
    Args:
        audio_path: 音频文件路径
        threshold: 能量阈值
        min_silence_duration: 最小静音时长（秒）
    
    Returns:
        Dict[str, Any]: 检测结果
    """
    config = VADConfig(energy_threshold=threshold)
    vad = VAD(config)
    return vad.process_audio_file(audio_path)


def split_by_silence(
    audio_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    threshold: float = 0.01,
    min_speech_duration: float = 0.5,
    min_silence_duration: float = 2.0
) -> List[str]:
    """
    按静音分割音频为多个片段
    
    Args:
        audio_path: 输入音频文件路径
        output_dir: 输出目录，默认在原文件目录创建 split/ 子目录
        threshold: 能量阈值
        min_speech_duration: 最小语音片段时长（秒）
        min_silence_duration: 判定为静音的最小静音时长（秒）
    
    Returns:
        List[str]: 输出文件路径列表
    """
    audio_path = Path(audio_path)
    output_dir = output_dir or (audio_path.parent / "split")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    config = VADConfig(
        energy_threshold=threshold,
        min_speech_duration_ms=int(min_speech_duration * 1000),
        min_silence_duration_ms=int(min_silence_duration * 1000)
    )
    vad = VAD(config)
    
    result = vad.process_audio_file(audio_path)
    if not result["success"]:
        raise VADError(result.get("error", "Unknown error"))
    
    # 生成输出文件名
    base_name = audio_path.stem
    output_files = []
    
    for i, segment in enumerate(result["speech_timestamps"]):
        output_file = output_dir / f"{base_name}_segment_{i+1:03d}{audio_path.suffix}"
        
        # 使用 ffmpeg 提取片段
        cmd = [
            "ffmpeg", "-y",
            "-i", str(audio_path),
            "-ss", str(segment["start"]),
            "-t", str(segment["duration"]),
            "-acodec", "copy",
            str(output_file)
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
            output_files.append(str(output_file))
        except subprocess.TimeoutExpired:
            print(f"警告: 片段 {i+1} 提取超时")
        except Exception as e:
            print(f"警告: 片段 {i+1} 提取失败: {e}")
    
    return output_files


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------
def main():
    """
    命令行入口
    
    用法:
        python vad.py <音频文件> [选项]
        
        python vad.py audio.wav --engine energy
        python vad.py audio.wav --engine webrtc --aggressiveness 2
        python vad.py audio.wav --engine silero --threshold 0.5
        python vad.py audio.wav --split --output-dir ./segments/
        python vad.py audio.wav --json
        
    选项:
        --engine ENGINE     VAD 引擎: energy, webrtc, silero (默认: energy)
        --threshold THRESH  能量阈值 0-1 (默认: 0.01)
        --aggressiveness 0-3  WebRTC 激进程度 (默认: 1)
        --split            按静音分割为多个文件
        --output-dir DIR   输出目录
        --json             JSON 格式输出
        --stats            显示统计信息
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Voice Activity Detection (VAD) 静音检测服务"
    )
    parser.add_argument(
        "audio",
        help="音频文件路径"
    )
    parser.add_argument(
        "--engine", "-e",
        default="energy",
        choices=["energy", "webrtc", "silero"],
        help="VAD 引擎 (默认: energy)"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.01,
        help="能量阈值 0-1 (默认: 0.01)"
    )
    parser.add_argument(
        "--aggressiveness", "-a",
        type=int,
        default=1,
        choices=[0, 1, 2, 3],
        help="WebRTC 激进程度 0-3 (默认: 1)"
    )
    parser.add_argument(
        "--silero-threshold",
        type=float,
        default=0.5,
        help="Silero 置信度阈值 (默认: 0.5)"
    )
    parser.add_argument(
        "--split", "-s",
        action="store_true",
        help="按静音分割为多个文件"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="输出目录"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="JSON 格式输出"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="显示统计信息"
    )
    
    args = parser.parse_args()
    
    # 创建配置
    config = VADConfig(
        energy_threshold=args.threshold,
        webrtc_aggressiveness=args.aggressiveness,
        silero_threshold=args.silero_threshold
    )
    
    # 创建 VAD
    engine = VADEngine(args.engine)
    vad = VAD(config, engine)
    
    # 检查可用引擎
    available = vad.get_available_engines()
    if args.engine == "webrtc" and VADEngine.WEBRTC not in available:
        print("警告: WebRTC VAD 不可用，回退到能量检测")
        engine = VADEngine.ENERGY
        vad = VAD(config, engine)
    elif args.engine == "silero" and VADEngine.SILERO not in available:
        print("警告: Silero VAD 不可用，回退到能量检测")
        engine = VADEngine.ENERGY
        vad = VAD(config, engine)
    
    # 分割模式
    if args.split:
        output_files = split_by_silence(
            args.audio,
            output_dir=args.output_dir,
            threshold=args.threshold
        )
        print(f"\n分割完成，共 {len(output_files)} 个片段:")
        for f in output_files:
            print(f"  {f}")
        return
    
    # 分析模式
    print(f"正在分析音频: {args.audio}")
    print(f"使用引擎: {engine.value}")
    
    audio_path = Path(args.audio)
    result = vad.process_audio_file(audio_path)
    
    if not result["success"]:
        print(f"\n错误: {result.get('error')}")
        sys.exit(1)
    
    # 输出结果
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n音频时长: {result['duration']:.2f} 秒")
        print(f"采样率: {result['sample_rate']} Hz")
        print(f"声道数: {result['channels']}")
        print(f"\n检测到 {len(result['speech_timestamps'])} 个语音片段:")
        
        for i, seg in enumerate(result['speech_timestamps']):
            print(f"  [{i+1}] {seg['start']:.2f}s - {seg['end']:.2f}s "
                  f"(时长: {seg['duration']:.2f}s)")
        
        if args.stats:
            print(f"\n统计:")
            print(f"  总语音时长: {result['total_speech_duration']:.2f}s")
            print(f"  语音占比: {result['total_speech_duration'] / result['duration'] * 100:.1f}%")


if __name__ == "__main__":
    main()
