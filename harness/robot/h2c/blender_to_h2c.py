"""
Blender → H2C 自动化脚本
完整链路：.blend → .stl → .gcode.3mf → H2C 打印

依赖：
    pip install bambulabs_api
    Blender（需安装并可从命令行调用 blender）
    Bambu Studio Linux AppImage（需下载并赋予执行权限）

用法：
    python blender_to_h2c.py model.blend
    python blender_to_h2c.py model.blend --no-print  # 只切片，不上传
"""

import os
import sys
import json
import shutil
import logging
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Tuple

# 本模块
from h2c_control import H2CController

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("BlenderToH2C")


# ============================================================
# 配置（用户需要填写）
# ============================================================

# TODO: 你的 Bambu Studio AppImage 路径
BAMBU_STUDIO_PATH = "/path/to/Bambu_Studio_linux.AppImage"

# TODO: H2C 切片参数预设文件（.json），可从 Bambu Studio 保存
# 在 Bambu Studio 里配好 H2C 的耗材、热端、打印参数，导出为 JSON
H2C_PRESET_FILE = "H2C_standard.json"   # 与 config.json 同目录

# TODO: Blender 可执行文件路径
BLENDER_BIN = "blender"                 # 如果 blender 在 PATH 中直接用 "blender"


# ============================================================
# Blender 导出
# ============================================================

def blender_export_stl(
    blend_file: str,
    output_path: str,
    blender_bin: str = BLENDER_BIN,
) -> bool:
    """
    调用 Blender CLI 将 .blend 文件导出为 .stl

    Blender CLI 用法（headless，无 GUI）：
        blender <file.blend> --background --python-expr "<python code>"

    Args:
        blend_file:   .blend 文件路径
        output_path:  导出的 .stl 路径
        blender_bin:  blender 可执行文件路径

    Returns:
        True = 导出成功
    """
    blend_file = Path(blend_file).resolve()
    output_path = Path(output_path).resolve()

    if not blend_file.exists():
        raise FileNotFoundError(f".blend 文件不存在: {blend_file}")

    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Blender Python API 导出 STL
    export_script = f"""
import bpy

# 清除默认 cube（Blender 启动默认场景有 cube）
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 导入 .blend 文件中的所有 mesh 对象
with bpy.data.libraries.load(r'{blend_file}') as (data_from, data_to):
    # 导入 mesh 和 collection
    for attr in dir(data_to):
        setattr(data_to, attr, getattr(data_from, attr, []))

# 导出 STL（选中所有 mesh）
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_mesh.stl(
    filepath=r'{output_path}',
    use_selection=True,
    global_scale=1.0,
    use_mesh_modifiers=True,
    ascii=False,
)
print(f"STL exported: {output_path}")
"""

    logger.info(f"Blender 导出 STL: {blend_file.name} → {output_path.name}")

    try:
        result = subprocess.run(
            [blender_bin, "--background", "--python-expr", export_script],
            capture_output=True,
            text=True,
            timeout=120,  # Blender 导出最多等 2 分钟
        )
        if result.returncode != 0:
            logger.error(f"Blender 导出失败:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
            return False

        logger.info(f"✅ STL 导出成功: {output_path}")
        return True

    except subprocess.TimeoutExpired:
        logger.error("Blender 导出超时（>120s）")
        return False
    except FileNotFoundError:
        logger.error(
            f"Blender 未找到: {blender_bin}\n"
            "请确认 Blender 已安装且路径正确（或已在 PATH 中）。"
        )
        return False


def blender_export_3mf(
    blend_file: str,
    output_path: str,
    blender_bin: str = BLENDER_BIN,
) -> bool:
    """
    导出 3MF（含颜色/材料信息，需要 Blender 3MF 插件）

    需要安装 Ghostkeeper/Blender3mfFormat 插件：
        1. 下载：https://github.com/Ghostkeeper/Blender3mfFormat
        2. Blender → Edit → Preferences → Add-ons → Install
        3. 启用 "Import-Export: 3MF format"
    """
    # TODO: 3MF 导出需要 Blender 插件支持，暂留接口
    logger.warning("3MF 导出（带颜色）需要额外插件，暂使用 STL 路径")
    return blender_export_stl(blend_file, output_path.replace(".3mf", ".stl"), blender_bin)


# ============================================================
# 切片
# ============================================================

def slice_with_bambu_studio(
    input_file: str,
    output_dir: str,
    bambu_studio_path: str = BAMBU_STUDIO_PATH,
    preset_file: str = H2C_PRESET_FILE,
    export_3mf: bool = True,
) -> Tuple[bool, str]:
    """
    调用 Bambu Studio AppImage CLI 进行切片

    CLI 参考：https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage

    Args:
        input_file:     输入模型文件（.stl 或 .3mf）
        output_dir:     输出目录（切片结果放这里）
        bambu_studio_path: Bambu Studio AppImage 路径
        preset_file:    打印机/耗材预设 JSON 文件
        export_3mf:     True=输出 .gcode.3mf，False=输出 .gcode

    Returns:
        (success, output_file_path)
    """
    input_path = Path(input_file).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not Path(bambu_studio_path).exists():
        raise FileNotFoundError(
            f"Bambu Studio 不存在: {bambu_studio_path}\n"
            "请下载：https://github.com/bambulab/BambuStudio/releases"
        )

    cmd = [
        bambu_studio_path,
        str(input_path),
        "--slice", "1",
        "--arrange", "1",
        "--load-settings", preset_file,
        "--outputdir", str(output_dir),
    ]

    if export_3mf:
        cmd.append("--export-3mf")

    logger.info(f"开始切片: {input_path.name}")
    logger.info(f"  预设: {preset_file}")
    logger.info(f"  命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 切片最多等 5 分钟
        )

        if result.returncode != 0:
            logger.error(f"切片失败:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
            return False, ""

        # 查找输出文件
        # 切片后文件名通常是 input_name_H2C_xxx.gcode 或 .gcode.3mf
        possible_names = [
            input_path.stem + ".gcode.3mf",
            input_path.stem + ".gcode",
            input_path.with_suffix(".gcode.3mf").name,
            input_path.with_suffix(".gcode").name,
        ]

        output_file = ""
        for name in possible_names:
            candidate = output_dir / name
            if candidate.exists():
                output_file = str(candidate)
                break

        if not output_file:
            # 列出输出目录内容辅助调试
            files = list(output_dir.iterdir())
            logger.warning(f"输出目录内容: {[f.name for f in files]}")
            output_file = str(output_dir / possible_names[0])  # 用预期名字返回

        logger.info(f"✅ 切片成功: {output_file}")
        return True, output_file

    except subprocess.TimeoutExpired:
        logger.error("切片超时（>300s）")
        return False, ""
    except FileNotFoundError:
        logger.error(f"Bambu Studio 未找到: {bambu_studio_path}")
        return False, ""


# ============================================================
# 主自动化流程
# ============================================================

def blender_to_h2c(
    blend_file: str,
    output_dir: str = "/tmp/h2c_jobs",
    config_path: str = "config.json",
    upload: bool = True,
    monitor: bool = True,
    blender_bin: str = BLENDER_BIN,
    bambu_studio_path: str = BAMBU_STUDIO_PATH,
    preset_file: str = H2C_PRESET_FILE,
) -> Tuple[bool, str]:
    """
    完整链路：.blend → .stl → .gcode.3mf → H2C

    Args:
        blend_file:        .blend 文件路径
        output_dir:        工作目录（中间文件放这里）
        config_path:       H2C 配置文件路径
        upload:            是否上传并开始打印
        monitor:           打印后是否监控状态
        blender_bin:       blender 路径
        bambu_studio_path: Bambu Studio AppImage 路径
        preset_file:       H2C 切片预设文件

    Returns:
        (success, gcode_path)
    """
    blend_file = Path(blend_file).resolve()
    output_dir = Path(output_dir).resolve()
    stl_dir = output_dir / "stl"
    gcode_dir = output_dir / "gcode"

    stl_dir.mkdir(parents=True, exist_ok=True)
    gcode_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Blender 导出 STL ---
    stl_file = stl_dir / f"{blend_file.stem}.stl"
    logger.info("=" * 50)
    logger.info(f"Step 1/3: Blender 导出 STL")
    logger.info(f"  输入: {blend_file}")
    if not blender_export_stl(str(blend_file), str(stl_file), blender_bin=blender_bin):
        return False, ""

    # --- Step 2: Bambu Studio 切片 ---
    logger.info("=" * 50)
    logger.info(f"Step 2/3: Bambu Studio 切片")
    success, gcode_path = slice_with_bambu_studio(
        str(stl_file),
        str(gcode_dir),
        bambu_studio_path=bambu_studio_path,
        preset_file=preset_file,
        export_3mf=True,
    )
    if not success:
        return False, ""

    logger.info(f"  切片结果: {gcode_path}")

    # --- Step 3: 上传并打印 ---
    if not upload:
        logger.info("Step 3: 跳过上传（--no-print）")
        return True, gcode_path

    logger.info("=" * 50)
    logger.info(f"Step 3/3: 上传并开始打印")

    # 加载 H2C 配置
    config_p = Path(config_path)
    if config_p.exists():
        h2c = H2CController(config_path=str(config_p))
    else:
        logger.warning(f"配置文件 {config_path} 不存在，使用内置参数")
        h2c = H2CController()

    if not h2c.connect():
        return False, gcode_path

    try:
        # 上传并开始打印（含重试）
        ok = h2c.upload_and_print(gcode_path)
        if not ok:
            return False, gcode_path

        # 监控打印过程
        if monitor:
            h2c.monitor(
                on_complete=lambda: logger.info("🎉 打印任务完成！"),
                on_error=lambda e: logger.error(f"监控异常: {e}"),
            )

        return True, gcode_path

    finally:
        h2c.disconnect()


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Blender → H2C 全自动打印流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 基本用法（需要先配置 config.json）
  python blender_to_h2c.py model.blend

  # 只切片，不上传打印
  python blender_to_h2c.py model.blend --no-print

  # 指定配置文件和输出目录
  python blender_to_h2c.py model.blend -o /tmp/myprint --config my_h2c.json

  # 指定 Blender 路径
  python blender_to_h2c.py model.blend --blender /Applications/blender.app/Contents/MacOS/blender
        """,
    )
    parser.add_argument("blend_file", help=".blend 文件路径")
    parser.add_argument(
        "-o", "--output-dir",
        default="/tmp/h2c_jobs",
        help="工作目录（默认: /tmp/h2c_jobs）",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="H2C 配置文件路径（默认: config.json）",
    )
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="只做 Blender 导出 + 切片，不上传到打印机",
    )
    parser.add_argument(
        "--no-monitor",
        action="store_true",
        help="上传后不监控打印状态",
    )
    parser.add_argument(
        "--blender",
        default="blender",
        help="Blender 可执行文件路径（默认: blender）",
    )
    parser.add_argument(
        "--bambu-studio",
        default=BAMBU_STUDIO_PATH,
        help="Bambu Studio AppImage 路径",
    )
    parser.add_argument(
        "--preset",
        default=H2C_PRESET_FILE,
        help="H2C 切片预设 JSON 文件",
    )
    args = parser.parse_args()

    success, gcode_path = blender_to_h2c(
        blend_file=args.blend_file,
        output_dir=args.output_dir,
        config_path=args.config,
        upload=not args.no_print,
        monitor=not args.no_monitor,
        blender_bin=args.blender,
        bambu_studio_path=args.bambu_studio,
        preset_file=args.preset,
    )

    if success:
        logger.info(f"\n🎉 完成！G-code: {gcode_path}")
        sys.exit(0)
    else:
        logger.error("\n❌ 失败，请检查上面的错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
