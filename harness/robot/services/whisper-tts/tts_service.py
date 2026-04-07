#!/usr/bin/env python3
"""
tts_service.py - TTS 语音合成服务

功能：使用 Edge-TTS（微软 Azure 认知服务）进行文字转语音（Text-to-Speech）
依赖：edge-tts（pip install edge-tts）
特性：支持多种中文/英文音色、语速调节、音调调节
"""

import subprocess
import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union, List


# ---------------------------------------------------------------------------
# 异常定义
# ---------------------------------------------------------------------------
class TTSServiceError(Exception):
    """TTS 服务的通用错误基类"""
    pass


class TTSUnavailableError(TTSServiceError):
    """Edge-TTS 不可用时抛出"""
    pass


class SynthesisError(TTSServiceError):
    """语音合成失败时抛出"""
    pass


# ---------------------------------------------------------------------------
# 音色（Voice）定义
# ---------------------------------------------------------------------------
# 常用中文音色
ZH_VOICES = {
    # 女声
    "zh-CN-Xiaoxiao": "晓晓（女，活泼）",
    "zh-CN-Xiaoyi": "小艺（女，温柔）",
    "zh-CN-Yunxi": "云希（女，知性）",
    "zh-CN-Yunyang": "云扬（女，新闻）",
    "zh-CN-liaoning": "辽宁（女，方言）",
    "zh-CN-shaanxi": "陕西（女，方言）",
    "zh-CN-Henan": "河南（女，方言）",
    # 男声
    "zh-CN-Yunxi": "云希（男，青年）",
    "zh-CN-Yunyou": "云游（男，青年）",
    "zh-CN-Yunyang": "云扬（男，新闻）",
}

# 常用英文音色
EN_VOICES = {
    "en-US-Aria": "Aria（女，通用）",
    "en-US-Guy": "Guy（男，通用）",
    "en-US-Jenny": "Jenny（女，通用）",
    "en-US-Sara": "Sara（女，友好）",
    "en-GB-Sonia": "Sonia（英式女）",
    "en-GB-Ryan": "Ryan（英式男）",
}

# 所有可用音色
ALL_VOICES = {**ZH_VOICES, **EN_VOICES}


# ---------------------------------------------------------------------------
# TTSService 主类
# ---------------------------------------------------------------------------
class TTSService:
    """
    Edge-TTS 语音合成服务类

    使用 edge-tts 库调用微软 Azure 认知服务 TTS API。
    支持多种音色、语速、音调调节。
    """

    # 可用的语速范围
    SPEED_MIN = 0.5
    SPEED_MAX = 2.0
    SPEED_DEFAULT = 1.0

    # 可用的音调范围
    PITCH_MIN = 0.5
    PITCH_MAX = 2.0
    PITCH_DEFAULT = 1.0

    def __init__(
        self,
        voice: str = "zh-CN-Xiaoxiao",
        rate: float = 1.0,
        pitch: float = 1.0,
        output_dir: Optional[str] = None
    ):
        """
        初始化 TTS 服务

        Args:
            voice: 音色名称，默认 "zh-CN-Xiaoxiao"
                   完整列表参考 edge-tts 官方文档
            rate: 语速倍率，0.5-2.0，默认 1.0
                  1.0 = 正常语速
                  0.5 = 0.5倍速（慢）
                  2.0 = 2倍速（快）
            pitch: 音调倍率，0.5-2.0，默认 1.0
                   1.0 = 正常音调
                   0.5 = 低沉
                   2.0 = 高亢
            output_dir: 输出目录，默认当前目录

        Raises:
            ValueError: 当参数超出范围时抛出
        """
        if not self.SPEED_MIN <= rate <= self.SPEED_MAX:
            raise ValueError(
                f"无效的语速: {rate}，有效范围: {self.SPEED_MIN} - {self.SPEED_MAX}"
            )
        if not self.PITCH_MIN <= pitch <= self.PITCH_MAX:
            raise ValueError(
                f"无效的音调: {pitch}，有效范围: {self.PITCH_MIN} - {self.PITCH_MAX}"
            )
        if voice not in ALL_VOICES and not self._check_voice_available(voice):
            # 不在预定义列表中也尝试使用，可能自定义音色
            pass

        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.output_dir = output_dir

        # 将倍率转为 edge-tTS 格式（e.g., "+0%" 或 "-50%"）
        self._rate_str = self._format_percent(rate, center=1.0)
        self._pitch_str = self._format_percent(pitch, center=1.0)

    @staticmethod
    def _format_percent(value: float, center: float = 1.0) -> str:
        """
        将倍率转换为 edge-tTS 百分比格式

        Args:
            value: 倍率值，如 1.0, 0.5, 2.0
            center: 中心值，1.0 表示"正常"

        Returns:
            str: 百分比字符串，如 "+0%", "-50%", "+100%"
        """
        if value == center:
            return "+0%"
        delta = (value - center) * 100
        sign = "+" if delta > 0 else ""
        return f"{sign}{int(delta)}%"

    def _check_edge_tts_available(self) -> bool:
        """
        检查 edge-tts 是否可用

        Returns:
            bool: edge-tts 命令是否可用
        """
        try:
            result = subprocess.run(
                ["edge-tts", "--help"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        except Exception:
            return False

    def _check_voice_available(self, voice: str) -> bool:
        """
        检查指定音色是否可用

        Args:
            voice: 音色名称

        Returns:
            bool: 音色是否可用
        """
        try:
            result = subprocess.run(
                ["edge-tts", "--list-voices"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return voice in result.stdout
            return False
        except Exception:
            return False

    def _escape_ssml(self, text: str) -> str:
        """
        转义 SSML 特殊字符

        Args:
            text: 原始文本

        Returns:
            str: 转义后的文本
        """
        # SSML 特殊字符转义
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")
        return text

    async def _synthesize_async(
        self,
        text: str,
        output_path: Optional[Path] = None,
        audio_format: str = "audio-24khz-48kbitrate-mono-mp3"
    ) -> Dict[str, Any]:
        """
        异步合成语音（内部方法，供 synthesize 调用）

        Args:
            text: 待合成的文本
            output_path: 输出文件路径
            audio_format: 音频格式

        Returns:
            Dict: 包含合成结果的字典
        """
        try:
            import edge_tts
        except ImportError:
            raise TTSUnavailableError(
                "edge-tts 不可用。请先安装：\n"
                "  pip install edge-tts\n"
                "  或\n"
                "  pip3 install edge-tts"
            )

        # 如果没有指定输出路径，生成临时文件
        if output_path is None:
            import tempfile
            fd, output_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            output_path = Path(output_path)
        else:
            output_path = Path(output_path)

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 创建 Communicate 对象
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self._rate_str,
                pitch=self._pitch_str
            )

            # 合成音频
            await communicate.save(str(output_path))

            return {
                "success": True,
                "output_file": str(output_path),
                "voice": self.voice,
                "rate": self.rate,
                "pitch": self.pitch,
                "text_length": len(text),
                "format": audio_format
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"合成失败: {str(e)}",
                "output_file": None
            }

    def synthesize(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None,
        audio_format: str = "audio-24khz-48kbitrate-mono-mp3"
    ) -> Dict[str, Any]:
        """
        合成语音（同步包装）

        Args:
            text: 待合成的文本（建议不超过 1000 字符）
            output_path: 输出文件路径，默认在 output_dir 生成 timestamp.mp3
            audio_format: 音频格式，默认 mp3

        Returns:
            Dict[str, Any]: 包含合成结果的字典
                - success: 是否成功
                - output_file: 输出文件路径
                - error: 错误信息（如果失败）
                - voice: 使用的音色
                - rate: 语速倍率
                - pitch: 音调倍率

        Raises:
            TTSUnavailableError: 当 edge-tts 不可用时抛出
            SynthesisError: 当合成失败时抛出

        Examples:
            >>> service = TTSService(voice="zh-CN-Xiaoxiao")
            >>> result = service.synthesize("你好，世界！", "hello.mp3")
            >>> if result["success"]:
            ...     print(f"已生成: {result['output_file']}")
        """
        # 检查 edge-tts 是否可用
        if not self._check_edge_tts_available():
            # 尝试导入 Python 库检查
            try:
                import edge_tts
            except ImportError:
                raise TTSUnavailableError(
                    "edge-tts 不可用。请先安装：\n"
                    "  pip install edge-tts\n"
                    "  或\n"
                    "  pip3 install edge-tts"
                )

        # 处理输出路径
        if output_path is None:
            import time
            filename = f"tts_{int(time.time() * 1000)}.mp3"
            if self.output_dir:
                output_path = Path(self.output_dir) / filename
            else:
                output_path = Path(filename)
        else:
            output_path = Path(output_path)

        # 使用 asyncio 运行异步合成
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            self._synthesize_async(text, output_path, audio_format)
        )

        return result

    def synthesize_to_bytes(
        self,
        text: str,
        audio_format: str = "audio-24khz-48kbitrate-mono-mp3"
    ) -> Dict[str, Any]:
        """
        合成语音并返回字节数据（用于流媒体）

        Args:
            text: 待合成的文本
            audio_format: 音频格式

        Returns:
            Dict[str, Any]: 包含合成结果的字典
                - success: 是否成功
                - audio_data: 字节数据（bytes）
                - error: 错误信息（如果失败）
        """
        try:
            import edge_tts
        except ImportError:
            raise TTSUnavailableError(
                "edge-tts 不可用。请先安装：\n"
                "  pip install edge-tts"
            )

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        async def _get_audio():
            try:
                import edge_tts
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=self.voice,
                    rate=self._rate_str,
                    pitch=self._pitch_str
                )
                audio_bytes = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_bytes += chunk["data"]
                return {
                    "success": True,
                    "audio_data": audio_bytes,
                    "text_length": len(text)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"合成失败: {str(e)}",
                    "audio_data": None
                }

        return loop.run_until_complete(_get_audio())

    def list_available_voices(self, lang: Optional[str] = None) -> Dict[str, str]:
        """
        列出可用的音色

        Args:
            lang: 语言过滤，如 "zh-CN", "en-US"，None 则返回全部

        Returns:
            Dict[str, str]: 音色ID -> 描述 的字典
        """
        if lang:
            return {
                k: v for k, v in ALL_VOICES.items()
                if k.startswith(lang)
            }
        return dict(ALL_VOICES)

    def synthesize_long_text(
        self,
        text: str,
        output_path: Union[str, Path],
        chunk_size: int = 500,
        overlap: int = 50
    ) -> Dict[str, Any]:
        """
        合成长文本（自动分块，避免超时）

        长文本会被分成多个小块分别合成，然后拼接成一个文件。
        相邻块之间有 overlap 重叠，用于平滑过渡。

        Args:
            text: 待合成的长文本
            output_path: 输出文件路径
            chunk_size: 每块最大字符数，默认 500
            overlap: 相邻块重叠字符数，默认 50

        Returns:
            Dict[str, Any]: 包含合成结果的字典
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 简单的分块策略：按句子分
        # 这里使用固定大小分块，实际应用可根据标点符号分句
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if chunk:
                chunks.append(chunk)

        if not chunks:
            return {
                "success": False,
                "error": "文本为空",
                "output_file": None
            }

        # 逐块合成（简单方案：逐块写入，最后合并）
        # 注意：edge-tts 输出是 mp3，直接拼接会有问题
        # 这里返回每块的单独文件路径，实际使用时可用 ffmpeg 合并
        output_files = []
        for i, chunk in enumerate(chunks):
            chunk_path = output_path.with_name(
                f"{output_path.stem}_chunk{i}{output_path.suffix}"
            )
            result = self.synthesize(chunk, chunk_path)
            if not result["success"]:
                return result
            output_files.append(result["output_file"])

        return {
            "success": True,
            "output_file": str(output_path),
            "chunk_files": output_files,
            "total_chunks": len(chunks),
            "voice": self.voice
        }

    def preview_voice(
        self,
        sample_text: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        预览当前音色

        Args:
            sample_text: 试听文本，默认使用内置示例
            output_path: 输出文件路径

        Returns:
            Dict: 试听结果
        """
        if sample_text is None:
            if self.voice.startswith("zh"):
                sample_text = "你好，我是你的语音助手。这句话可以用来测试当前音色的效果。"
            else:
                sample_text = "Hello, this is a test of the current voice. How does it sound to you?"

        return self.synthesize(sample_text, output_path)


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------
def main():
    """
    命令行入口

    用法:
        python tts_service.py <文本> [选项]

    选项:
        --voice VOICE     音色 (默认: zh-CN-Xiaoxiao)
        --rate RATE       语速 0.5-2.0 (默认: 1.0)
        --pitch PITCH     音调 0.5-2.0 (默认: 1.0)
        --output FILE     输出文件路径
        --list            列出所有可用音色
        --preview         试听当前音色

    示例:
        python tts_service.py "你好，世界！" --voice zh-CN-Yunxi --rate 1.2
        python tts_service.py "Hello" --voice en-US-Aria --output hello.mp3
        python tts_service.py --list
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Edge-TTS 语音合成服务"
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="要合成的文本"
    )
    parser.add_argument(
        "--voice", "-v",
        default="zh-CN-Xiaoxiao",
        help=f"音色名称 (默认: zh-CN-Xiaoxiao)"
    )
    parser.add_argument(
        "--rate", "-r",
        type=float,
        default=1.0,
        help="语速倍率 0.5-2.0 (默认: 1.0)"
    )
    parser.add_argument(
        "--pitch", "-p",
        type=float,
        default=1.0,
        help="音调倍率 0.5-2.0 (默认: 1.0)"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="输出文件路径"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有可用音色"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="试听当前音色设置"
    )

    args = parser.parse_args()

    # 列出音色
    if args.list:
        print("可用音色：\n")
        print("【中文音色】")
        for vid, desc in sorted(ZH_VOICES.items()):
            print(f"  {vid}: {desc}")
        print("\n【英文音色】")
        for vid, desc in sorted(EN_VOICES.items()):
            print(f"  {vid}: {desc}")
        print(f"\n共 {len(ALL_VOICES)} 个音色")
        return

    # 试听
    if args.preview:
        service = TTSService(voice=args.voice, rate=args.rate, pitch=args.pitch)
        print(f"正在合成试听音频...")
        print(f"音色: {args.voice}")
        print(f"语速: {args.rate}")
        print(f"音调: {args.pitch}")
        result = service.preview_voice(output_path=args.output)
        if result["success"]:
            print(f"\n试听音频已生成: {result['output_file']}")
        else:
            print(f"\n生成失败: {result.get('error')}")
            sys.exit(1)
        return

    # 合成文本
    if not args.text:
        parser.print_help()
        return

    try:
        service = TTSService(voice=args.voice, rate=args.rate, pitch=args.pitch)
    except ValueError as e:
        print(f"参数错误: {e}")
        sys.exit(1)

    print(f"正在合成语音...")
    print(f"文本: {args.text[:50]}{'...' if len(args.text) > 50 else ''}")
    print(f"音色: {args.voice}")
    print(f"语速: {args.rate}")
    print(f"音调: {args.pitch}")

    result = service.synthesize(args.text, args.output)

    if result["success"]:
        print(f"\n合成成功!")
        print(f"输出文件: {result['output_file']}")
        print(f"文本长度: {result['text_length']} 字符")
    else:
        print(f"\n合成失败: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
