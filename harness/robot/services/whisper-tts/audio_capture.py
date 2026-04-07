#!/usr/bin/env python3
"""
audio_capture.py - 音频录制服务

功能：录制系统/麦克风音频，支持多种音频源和格式
依赖：pyaudio（pip install pyaudio）
特性：支持麦克风录制、音频监控、VAD（语音活动检测）、流式录制
"""

import subprocess
import os
import sys
import wave
import struct
import threading
import time
import io
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, Callable
from dataclasses import dataclass
from enum import Enum


# ---------------------------------------------------------------------------
# 异常定义
# ---------------------------------------------------------------------------
class AudioCaptureError(Exception):
    """音频录制服务的通用错误基类"""
    pass


class AudioSourceUnavailableError(AudioCaptureError):
    """音频源不可用时抛出"""
    pass


class RecordingError(AudioCaptureError):
    """录制失败时抛出"""
    pass


# ---------------------------------------------------------------------------
# 音频格式定义
# ---------------------------------------------------------------------------
class AudioFormat(Enum):
    """支持的音频格式"""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"


@dataclass
class AudioConfig:
    """音频配置"""
    sample_rate: int = 16000          # 采样率 (Hz)
    channels: int = 1                 # 声道数 (1=单声道, 2=立体声)
    chunk_size: int = 1024            # 每次读取的帧数
    dtype: str = "int16"              # 采样格式


# 默认配置
DEFAULT_CONFIG = AudioConfig()


# ---------------------------------------------------------------------------
# 音频录制器类
# ---------------------------------------------------------------------------
class AudioCapture:
    """
    音频录制服务类
    
    支持多种录制模式：
    - 麦克风录制：从系统默认麦克风录制音频
    - 音频监控：实时监控音频电平
    - 流式录制：边录边写，支持长时间录制
    - VAD 录制：仅在检测到语音时录制
    """

    # 支持的采样率
    VALID_SAMPLE_RATES = [8000, 11025, 16000, 22050, 44100, 48000]

    def __init__(
        self,
        source: str = "default",
        config: Optional[AudioConfig] = None,
        output_dir: Optional[str] = None
    ):
        """
        初始化音频录制服务

        Args:
            source: 音频源，默认为系统默认设备
                   在 macOS 上可以是设备名称或索引
            config: 音频配置，默认使用 DEFAULT_CONFIG
            output_dir: 输出目录，默认当前目录

        Raises:
            AudioSourceUnavailableError: 当指定音频源不可用时抛出
        """
        self.source = source
        self.config = config or DEFAULT_CONFIG
        self.output_dir = output_dir

        # 内部状态
        self._is_recording = False
        self._recording_thread: Optional[threading.Thread] = None
        self._audio_frames: List[bytes] = []
        self._stream = None
        self._pyaudio = None

        # 检查 pyaudio 可用性
        self._pyaudio_available = self._check_pyaudio_available()

    def _check_pyaudio_available(self) -> bool:
        """
        检查 pyaudio 是否可用

        Returns:
            bool: pyaudio 是否可用
        """
        try:
            import pyaudio
            return True
        except ImportError:
            return False

    def _check_sox_available(self) -> bool:
        """
        检查 sox (rec 命令) 是否可用

        Returns:
            bool: sox 命令是否可用
        """
        try:
            result = subprocess.run(
                ["rec", "--help"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_ffmpeg_available(self) -> bool:
        """
        检查 ffmpeg 是否可用

        Returns:
            bool: ffmpeg 命令是否可用
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def list_audio_sources(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的音频输入设备

        Returns:
            List[Dict[str, Any]]: 设备列表，每项包含 id, name, channels 等信息
        """
        sources = []

        if self._pyaudio_available:
            import pyaudio
            p = pyaudio.PyAudio()
            try:
                for i in range(p.get_device_count()):
                    try:
                        info = p.get_device_info_by_index(i)
                        # 只返回输入设备
                        if info["maxInputChannels"] > 0:
                            sources.append({
                                "id": i,
                                "name": info["name"],
                                "channels": info["maxInputChannels"],
                                "sample_rate": int(info["defaultSampleRate"]),
                                "api": p.get_host_api_info_by_index(info["hostApi"])["name"]
                            })
                    except Exception:
                        continue
            finally:
                p.terminate()

        return sources

    def _init_pyaudio(self):
        """
        初始化 pyaudio 流

        Returns:
            tuple: (pyaudio instance, stream)
        """
        import pyaudio

        if self._pyaudio is None:
            self._pyaudio = pyaudio.PyAudio()

        # 选择合适的采样格式
        format_map = {
            "int16": pyaudio.paInt16,
            "int32": pyaudio.paInt32,
            "float32": pyaudio.paFloat32,
        }
        pa_format = format_map.get(self.config.dtype, pyaudio.paInt16)

        stream = self._pyaudio.open(
            format=pa_format,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            input_device_index=self._get_device_index(),
            frames_per_buffer=self.config.chunk_size
        )

        return self._pyaudio, stream

    def _get_device_index(self) -> Optional[int]:
        """
        获取设备索引

        Returns:
            int or None: 设备索引，None 表示使用默认设备
        """
        if self._pyaudio_available:
            import pyaudio
            p = pyaudio.PyAudio()

            # 如果 source 是数字字符串，转换为索引
            if isinstance(self.source, str) and self.source.isdigit():
                return int(self.source)

            # 如果 source 是设备名称，查找对应索引
            if isinstance(self.source, str) and not self.source == "default":
                for i in range(p.get_device_count()):
                    try:
                        info = p.get_device_info_by_index(i)
                        if self.source.lower() in info["name"].lower():
                            return i
                    except Exception:
                        continue

            p.terminate()

        return None

    def _recording_worker(self, output_path: Path, callback: Optional[Callable] = None):
        """
        录制工作线程

        Args:
            output_path: 输出文件路径
            callback: 录制进度回调函数
        """
        import pyaudio

        self._audio_frames = []
        frames_count = 0
        total_duration = 0.0

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            input_device_index=self._get_device_index(),
            frames_per_buffer=self.config.chunk_size
        )

        try:
            while self._is_recording:
                try:
                    data = stream.read(self.config.chunk_size, exception_on_overflow=False)
                    self._audio_frames.append(data)
                    frames_count += 1
                    total_duration = frames_count * self.config.chunk_size / self.config.sample_rate

                    if callback:
                        callback(frames_count, total_duration)

                except Exception as e:
                    if self._is_recording:
                        # 忽略溢出错误，继续录制
                        continue
                    else:
                        break

        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

        # 写入文件
        if self._audio_frames and output_path:
            self._write_wav(output_path)

    def _write_wav(self, output_path: Path):
        """
        将录制的音频帧写入 WAV 文件

        Args:
            output_path: 输出文件路径
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with wave.open(str(output_path), 'wb') as wf:
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(b''.join(self._audio_frames))

    def _write_mp3(self, output_path: Path):
        """
        将录制的音频帧转换为 MP3 并写入文件（需要 ffmpeg）

        Args:
            output_path: 输出文件路径
        """
        if not self._check_ffmpeg_available():
            raise AudioCaptureError("ffmpeg 不可用，无法生成 MP3 格式")

        # 先写入临时 WAV
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        self._write_wav(tmp_path)

        try:
            # 使用 ffmpeg 转换为 MP3
            cmd = [
                "ffmpeg", "-y",
                "-i", str(tmp_path),
                "-b:a", "192k",
                str(output_path)
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                raise RecordingError(f"MP3 转换失败: {result.stderr}")
        finally:
            # 删除临时文件
            if tmp_path.exists():
                tmp_path.unlink()

    def start_recording(
        self,
        output_path: Optional[Union[str, Path]] = None,
        format: AudioFormat = AudioFormat.WAV,
        callback: Optional[Callable[[int, float], None]] = None
    ) -> Dict[str, Any]:
        """
        开始录制音频（非阻塞）

        Args:
            output_path: 输出文件路径，默认在 output_dir 生成 timestamp.wav
            format: 音频格式，默认 WAV
            callback: 进度回调函数，参数为 (帧数, 时长秒)

        Returns:
            Dict[str, Any]: 包含录制状态的字典
                - success: 是否成功开始
                - output_file: 输出文件路径
                - error: 错误信息（如果失败）
        """
        if not self._pyaudio_available:
            return {
                "success": False,
                "error": "pyaudio 不可用。请先安装：\n"
                         "  macOS: pip install pyaudio && brew install portaudio\n"
                         "  Linux: pip install pyaudio\n"
                         "  Windows: pip install pipwin && pipwin install pyaudio",
                "output_file": None
            }

        if self._is_recording:
            return {
                "success": False,
                "error": "已经在录制中，请先停止当前录制",
                "output_file": None
            }

        # 处理输出路径
        if output_path is None:
            import time
            filename = f"recording_{int(time.time() * 1000)}.{format.value}"
            if self.output_dir:
                output_path = Path(self.output_dir) / filename
            else:
                output_path = Path(filename)
        else:
            output_path = Path(output_path)

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 对于非 WAV 格式，先录 WAV，转换在 stop 时处理
        self._output_path = output_path
        self._output_format = format

        # 开始录制线程
        self._is_recording = True
        self._recording_thread = threading.Thread(
            target=self._recording_worker,
            args=(output_path.with_suffix(".wav") if format != AudioFormat.WAV else output_path, callback)
        )
        self._recording_thread.start()

        return {
            "success": True,
            "output_file": str(output_path),
            "format": format.value,
            "sample_rate": self.config.sample_rate,
            "channels": self.config.channels
        }

    def stop_recording(self) -> Dict[str, Any]:
        """
        停止录制

        Returns:
            Dict[str, Any]: 包含录制结果的字典
                - success: 是否成功
                - output_file: 输出文件路径
                - duration: 录制时长（秒）
                - frames: 总帧数
                - error: 错误信息（如果失败）
        """
        if not self._is_recording:
            return {
                "success": False,
                "error": "没有正在进行的录制",
                "output_file": None,
                "duration": 0,
                "frames": 0
            }

        # 停止录制
        self._is_recording = False

        # 等待线程结束
        if self._recording_thread and self._recording_thread.is_alive():
            self._recording_thread.join(timeout=5)

        duration = len(self._audio_frames) * self.config.chunk_size / self.config.sample_rate

        result = {
            "success": True,
            "duration": duration,
            "frames": len(self._audio_frames),
            "sample_rate": self.config.sample_rate,
            "channels": self.config.channels
        }

        # 如果需要转换为其他格式
        if hasattr(self, "_output_format") and self._output_format != AudioFormat.WAV:
            output_path = Path(self._output_path)
            wav_path = output_path.with_suffix(".wav")

            try:
                if self._output_format == AudioFormat.MP3:
                    self._write_mp3(output_path)
                    result["output_file"] = str(output_path)
                elif self._output_format == AudioFormat.FLAC:
                    self._write_flac(output_path)
                    result["output_file"] = str(output_path)
            except Exception as e:
                result["success"] = False
                result["error"] = str(e)
                result["output_file"] = str(wav_path)
        else:
            result["output_file"] = str(self._output_path)

        # 清理
        self._audio_frames = []
        self._output_path = None

        return result

    def record(
        self,
        duration: Optional[float] = None,
        output_path: Optional[Union[str, Path]] = None,
        format: AudioFormat = AudioFormat.WAV,
        callback: Optional[Callable[[int, float], None]] = None
    ) -> Dict[str, Any]:
        """
        录制音频（阻塞模式）

        Args:
            duration: 录制时长（秒），None 表示手动停止
            output_path: 输出文件路径
            format: 音频格式
            callback: 进度回调函数

        Returns:
            Dict[str, Any]: 包含录制结果的字典
        """
        if not self._pyaudio_available:
            return {
                "success": False,
                "error": "pyaudio 不可用",
                "output_file": None
            }

        # 启动录制
        start_result = self.start_recording(output_path, format, callback)
        if not start_result["success"]:
            return start_result

        try:
            if duration is not None:
                # 等待指定时长
                time.sleep(duration)
                return self.stop_recording()
            else:
                # 手动停止模式，返回控制权给调用者
                return start_result

        except KeyboardInterrupt:
            # 用户中断，返回当前进度
            print("\n录制被中断")
            return self.stop_recording()

    def get_audio_level(self) -> Dict[str, Any]:
        """
        获取当前音频电平（用于监控）

        Returns:
            Dict[str, Any]: 包含电平信息的字典
                - rms: RMS 电平 (0-1)
                - db: 分贝值
                - is_silent: 是否为静音
        """
        if not self._pyaudio_available:
            return {"rms": 0, "db": -100, "is_silent": True}

        import pyaudio

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.config.sample_rate,
            input=True,
            input_device_index=self._get_device_index(),
            frames_per_buffer=self.config.chunk_size
        )

        try:
            data = stream.read(self.config.chunk_size, exception_on_overflow=False)
            
            # 计算 RMS 电平
            import struct
            fmt = "<" + str(len(data) // 2) + "h"
            samples = struct.unpack(fmt, data)
            
            sum_squares = sum(sample ** 2 for sample in samples)
            rms = (sum_squares / len(samples)) ** 0.5 / 32768.0
            
            # 转换为分贝
            db = 20 * (rms ** 0.5) if rms > 0 else -100
            
            return {
                "rms": rms,
                "db": db,
                "is_silent": rms < 0.01
            }
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    def vad_record(
        self,
        silence_threshold: float = 0.01,
        silence_duration: float = 2.0,
        output_path: Optional[Union[str, Path]] = None,
        max_duration: float = 60.0
    ) -> Dict[str, Any]:
        """
        VAD 录制：仅在检测到语音时录制

        使用简单的能量检测进行语音活动检测（VAD）。

        Args:
            silence_threshold: 静音阈值 (0-1)
            silence_duration: 超过此时间检测到静音则停止录制
            output_path: 输出文件路径
            max_duration: 最大录制时长

        Returns:
            Dict[str, Any]: 包含录制结果的字典
        """
        if not self._pyaudio_available:
            return {
                "success": False,
                "error": "pyaudio 不可用",
                "output_file": None
            }

        self._audio_frames = []
        is_recording = False
        silence_frames = 0
        total_frames = 0
        max_frames = int(max_duration * self.config.sample_rate / self.config.chunk_size)

        import pyaudio
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            input_device_index=self._get_device_index(),
            frames_per_buffer=self.config.chunk_size
        )

        try:
            while total_frames < max_frames:
                data = stream.read(self.config.chunk_size, exception_on_overflow=False)
                
                # 计算电平
                import struct
                fmt = "<" + str(len(data) // 2) + "h"
                samples = struct.unpack(fmt, data)
                sum_squares = sum(sample ** 2 for sample in samples)
                rms = (sum_squares / len(samples)) ** 0.5 / 32768.0

                if rms > silence_threshold:
                    # 检测到语音
                    if not is_recording:
                        is_recording = True
                        print("检测到语音，开始录制...")
                    silence_frames = 0
                    self._audio_frames.append(data)
                else:
                    # 静音
                    if is_recording:
                        silence_frames += 1
                        self._audio_frames.append(data)
                        
                        # 如果静音持续时间过长，停止录制
                        if silence_frames * self.config.chunk_size / self.config.sample_rate > silence_duration:
                            print("检测到静音，停止录制")
                            break

                total_frames += 1

        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

        # 写入文件
        if self._audio_frames and output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_wav(output_path)

            duration = len(self._audio_frames) * self.config.chunk_size / self.config.sample_rate
            return {
                "success": True,
                "output_file": str(output_path),
                "duration": duration,
                "frames": len(self._audio_frames)
            }
        else:
            return {
                "success": False,
                "error": "未录制到任何音频",
                "output_file": None
            }

    def record_to_bytes(self, duration: float = 5.0) -> Dict[str, Any]:
        """
        录制音频并返回字节数据

        Args:
            duration: 录制时长（秒）

        Returns:
            Dict[str, Any]: 包含录制结果的字典
                - success: 是否成功
                - audio_data: WAV 格式的字节数据
                - duration: 录制时长
        """
        if not self._pyaudio_available:
            return {
                "success": False,
                "error": "pyaudio 不可用",
                "audio_data": None
            }

        self._audio_frames = []
        total_frames = int(duration * self.config.sample_rate / self.config.chunk_size)

        import pyaudio
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            input_device_index=self._get_device_index(),
            frames_per_buffer=self.config.chunk_size
        )

        try:
            for _ in range(total_frames):
                data = stream.read(self.config.chunk_size, exception_on_overflow=False)
                self._audio_frames.append(data)
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

        # 转换为 WAV 字节
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(b''.join(self._audio_frames))

        return {
            "success": True,
            "audio_data": buffer.getvalue(),
            "duration": duration,
            "sample_rate": self.config.sample_rate,
            "channels": self.config.channels
        }


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------
def main():
    """
    命令行入口

    用法:
        python audio_capture.py [选项]

    选项:
        --duration DURATION   录制时长（秒）
        --output FILE         输出文件路径
        --format FORMAT       音频格式 (wav/mp3/flac)
        --list                列出所有音频设备
        --monitor             监控模式（显示音频电平）
        --vad                 VAD 录制模式

    示例:
        python audio_capture.py --duration 10 --output test.wav
        python audio_capture.py --list
        python audio_capture.py --monitor
        python audio_capture.py --vad --output voice.wav
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="音频录制服务"
    )
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=None,
        help="录制时长（秒），不指定则手动停止"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="输出文件路径"
    )
    parser.add_argument(
        "--format", "-f",
        default="wav",
        choices=["wav", "mp3", "flac", "ogg"],
        help="音频格式 (默认: wav)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有可用的音频输入设备"
    )
    parser.add_argument(
        "--monitor", "-m",
        action="store_true",
        help="监控模式：实时显示音频电平"
    )
    parser.add_argument(
        "--vad",
        action="store_true",
        help="VAD 模式：仅在检测到语音时录制"
    )
    parser.add_argument(
        "--source", "-s",
        default="default",
        help="音频源设备（设备名或索引）"
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="采样率 (默认: 16000)"
    )

    args = parser.parse_args()

    # 创建录制器实例
    config = AudioConfig(sample_rate=args.sample_rate)
    capture = AudioCapture(source=args.source, config=config)

    # 列出设备
    if args.list:
        sources = capture.list_audio_sources()
        print("可用的音频输入设备：\n")
        for src in sources:
            print(f"  [{src['id']}] {src['name']}")
            print(f"      通道: {src['channels']}, 采样率: {src['sample_rate']}, API: {src['api']}")
            print()
        return

    # 监控模式
    if args.monitor:
        print("实时音频电平监控（按 Ctrl+C 退出）...\n")
        print("电平表:")
        try:
            while True:
                level = capture.get_audio_level()
                bar_len = int(level['rms'] * 40)
                bar = '█' * bar_len + '░' * (40 - bar_len)
                print(f"\r[{bar}] {level['db']:.1f} dB  ", end='', flush=True)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n监控结束")
        return

    # VAD 录制
    if args.vad:
        print("VAD 录制模式：检测到语音自动开始，静默自动停止\n")
        result = capture.vad_record(
            output_path=args.output,
            max_duration=args.duration or 60.0
        )
        if result["success"]:
            print(f"\n录制完成!")
            print(f"输出文件: {result['output_file']}")
            print(f"录制时长: {result['duration']:.2f} 秒")
        else:
            print(f"\n录制失败: {result.get('error')}")
            sys.exit(1)
        return

    # 普通录制
    print("开始录制音频...")
    if args.duration:
        print(f"录制时长: {args.duration} 秒")

    result = capture.record(
        duration=args.duration,
        output_path=args.output,
        format=AudioFormat(args.format)
    )

    if result["success"]:
        print(f"\n录制完成!")
        print(f"输出文件: {result['output_file']}")
        if "duration" in result:
            print(f"录制时长: {result['duration']:.2f} 秒")
    else:
        print(f"\n录制失败: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
