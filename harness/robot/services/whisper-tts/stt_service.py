#!/usr/bin/env python3
"""
STT Service - Whisper 语音识别服务

功能：使用 OpenAI Whisper 进行语音转文字（Speech-to-Text）
依赖：whisper CLI 工具（需单独安装）
"""

import subprocess
import os
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union


class STTService:
    """
    Whisper 语音识别服务类
    
    使用 subprocess 调用系统安装的 whisper CLI 进行语音识别。
    支持多种模型和语言配置。
    """
    
    # 可用的模型大小
    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large"]
    
    def __init__(
        self,
        model: str = "base",
        language: Optional[str] = None,
        output_dir: Optional[str] = None
    ):
        """
        初始化 STT 服务
        
        Args:
            model: Whisper 模型大小，默认 "base"
                   可选: tiny, base, small, medium, large
            language: 语言代码，如 "zh", "en"，None 则自动检测
            output_dir: 输出目录，默认与音频同目录
        
        Raises:
            ValueError: 当模型不支持时抛出
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"不支持的模型: {model}. "
                f"可选: {', '.join(self.AVAILABLE_MODELS)}"
            )
        self.model = model
        self.language = language
        self.output_dir = output_dir
    
    def _check_whisper_available(self) -> bool:
        """
        检查 whisper CLI 是否可用
        
        Returns:
            bool: whisper 命令是否可用
        """
        try:
            # 尝试执行 whisper --help 检查是否安装
            result = subprocess.run(
                ["whisper", "--help"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        except Exception:
            return False
    
    def recognize(
        self,
        audio_path: Union[str, Path],
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        识别语音文件并返回文字结果
        
        Args:
            audio_path: 音频文件路径（支持 mp3, wav, m4a, flac 等格式）
            output_format: 输出格式，可选 json, text, srt, vtt, csv
            
        Returns:
            Dict[str, Any]: 包含识别结果的字典
                - text: 识别出的文字
                - language: 检测/使用的语言
                - success: 是否成功
                - error: 错误信息（如果失败）
                
        Raises:
            FileNotFoundError: 当音频文件不存在时抛出
            RuntimeError: 当 whisper 不可用或执行失败时抛出
        """
        audio_path = Path(audio_path)
        
        # 检查音频文件是否存在
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 检查 whisper 是否可用
        if not self._check_whisper_available():
            raise RuntimeError(
                "whisper CLI 不可用。请先安装 whisper:\n"
                "  macOS: brew install whisper\n"
                "  Linux: pip install whisper\n"
                "  Windows: pip install whisper"
            )
        
        # 构建命令
        cmd = [
            "whisper",
            str(audio_path),
            "--model", self.model,
            "--output_format", output_format
        ]
        
        # 添加语言参数（如果指定）
        if self.language:
            cmd.extend(["--language", self.language])
        
        # 添加输出目录（如果指定）
        if self.output_dir:
            cmd.extend(["--output_dir", self.output_dir])
        
        try:
            # 执行 whisper
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr or "未知错误",
                    "text": "",
                    "language": self.language or "unknown"
                }
            
            # 解析输出
            if output_format == "json":
                try:
                    # whisper 会输出 JSON 到 stderr 或文件
                    output_text = result.stdout or result.stderr
                    # 尝试解析为 JSON
                    data = json.loads(output_text)
                    return {
                        "success": True,
                        "text": data.get("text", ""),
                        "language": data.get("language", self.language or "unknown"),
                        "segments": data.get("segments", [])
                    }
                except json.JSONDecodeError:
                    # 如果不是 JSON，直接返回文本
                    return {
                        "success": True,
                        "text": output_text.strip(),
                        "language": self.language or "unknown"
                    }
            else:
                # 其他格式直接返回文本
                return {
                    "success": True,
                    "text": result.stdout.strip(),
                    "language": self.language or "unknown"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "识别超时（超过5分钟）",
                "text": "",
                "language": self.language or "unknown"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"识别失败: {str(e)}",
                "text": "",
                "language": self.language or "unknown"
            }
    
    def recognize_to_file(
        self,
        audio_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        识别语音并保存到文件
        
        Args:
            audio_path: 音频文件路径
            output_path: 输出文件路径，默认在同目录生成同名 .txt 文件
            
        Returns:
            Dict[str, Any]: 识别结果字典
        """
        audio_path = Path(audio_path)
        
        # 如果没有指定输出路径，使用同目录的 .txt 文件
        if output_path is None:
            output_path = audio_path.with_suffix(".txt")
        else:
            output_path = Path(output_path)
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 设置输出目录为文件所在目录
        original_output_dir = self.output_dir
        self.output_dir = str(audio_path.parent)
        
        result = self.recognize(audio_path, output_format="text")
        
        # 恢复原始输出目录设置
        self.output_dir = original_output_dir
        
        if result.get("success"):
            # 写入文件
            output_path.write_text(result["text"], encoding="utf-8")
            result["output_file"] = str(output_path)
        
        return result


def main():
    """
    命令行入口
    
    用法:
        python stt_service.py <音频文件> [选项]
        
    选项:
        --model MODEL      Whisper 模型 (tiny/base/small/medium/large)
        --language LANG   语言代码 (zh/en/ja/ko/...)
        --output FILE     输出文件路径
        
    示例:
        python stt_service.py audio.wav --model base --language zh
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Whisper 语音识别服务"
    )
    parser.add_argument(
        "audio",
        help="音频文件路径"
    )
    parser.add_argument(
        "--model", "-m",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper 模型大小 (默认: base)"
    )
    parser.add_argument(
        "--language", "-l",
        default=None,
        help="语言代码，如 zh, en (默认: 自动检测)"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="输出文件路径 (默认: 与音频同目录)"
    )
    
    args = parser.parse_args()
    
    # 创建服务实例
    service = STTService(
        model=args.model,
        language=args.language
    )
    
    # 执行识别
    print(f"正在识别音频: {args.audio}")
    print(f"使用模型: {args.model}")
    
    if args.output:
        result = service.recognize_to_file(args.audio, args.output)
    else:
        result = service.recognize(args.audio)
    
    # 输出结果
    if result.get("success"):
        print(f"\n识别成功!")
        print(f"语言: {result.get('language', 'unknown')}")
        print(f"\n识别结果:")
        print(result.get("text", ""))
        
        if args.output:
            print(f"\n已保存到: {result.get('output_file')}")
    else:
        print(f"\n识别失败: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
