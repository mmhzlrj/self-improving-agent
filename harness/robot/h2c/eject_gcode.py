"""
G-code Eject 方案 - 打印完成后自动推模型出去

原理：
    打印完成 → 等待热端冷却到安全温度 → 热端横向推动模型 → 模型掉落收集容器

用途：
    - 作为 Bambu Studio 的 end G-code
    - 配合 blender_to_h2c.py 实现"打印完自动收菜"

适用机型：H2C（CoreXY 结构，热端可在 X/Y 方向推动模型）

安全说明：
    - 默认推动距离 50mm，速度 1000mm/min，适合 PLA/ABS
    - PETG/TPU 等材料粘性更强，可能需要增加 push_distance
    - 高温材料（PA、PC）不建议自动推，可能损伤喷嘴
"""

from typing import Optional


# ============================================================
# 核心：生成 Eject G-code
# ============================================================

def generate_eject_gcode(
    push_distance: float = 50.0,
    push_speed: float = 1000.0,
    cooldown_temp: float = 60.0,
    z_lift: float = 20.0,
    push_axis: str = "X",
    direction: str = "positive",
    bed_type: str = "Textured PEI Plate",
    use_m600: bool = False,
) -> str:
    """
    生成推模型 G-code。

    工作流程：
        1. 打印完成（G-code 正常结束）
        2. 等待热端冷却到 cooldown_temp °C（防止高温推模型拉丝）
        3. Z 轴抬起 z_lift mm（防止喷嘴刮蹭模型）
        4. 热端横向推动模型 push_distance mm
        5. 归位（可选）

    参数：
        push_distance: 推动距离（mm），默认 50mm
                      模型越大/粘性越强 → 需要更大距离
        push_speed:    推动速度（mm/min），默认 1000 mm/min
                      PLA: 1000-1500 | ABS: 800-1200 | PETG: 600-1000
        cooldown_temp: 等待冷却的目标温度（°C），默认 60°C
        z_lift:        推之前抬起的 Z 高度（mm），默认 20mm
                      确保喷嘴离开模型表面
        push_axis:     推动轴，"X" 或 "Y"，默认 "X"
                      选朝向机器前方（门方向）的轴
        direction:     推动方向，"positive"（+）或 "negative"（-）
        bed_type:      打印板类型（仅作注释）
        use_m600:      是否插入 M600（换丝命令，实际上可用于提示打印机暂停）

    返回：
        G-code 字符串，可直接粘贴到 Bambu Studio end G-code
    """

    # 方向符号
    dir_sign = "+" if direction == "positive" else "-"

    # G-code 模板
    gcode_lines = [
        "; ===== H2C EJECT G-code 自动生成 =====",
        f"; 参数：push={push_distance}mm speed={push_speed}mm/min "
        f"cooldown={cooldown_temp}°C z_lift={z_lift}mm axis={push_axis}{dir_sign}",
        f"; 板类型：{bed_type}",
        "",
        "; 步骤1：打印结束，等待热端冷却",
        f"M104 S0          ; 关闭热端加热（允许冷却）",
        f"M109 S{cooldown_temp}  ; 等待热端降到 {cooldown_temp}°C",
        "",
        "; 步骤2：抬起 Z 轴（离开模型）",
        "G91              ; 相对坐标",
        f"G1 Z{z_lift:.1f} F3000   ; 抬起来回",
        "",
        "; 步骤3：移动到推模型起始位置",
        "G90              ; 绝对坐标",
        f"G1 X0 Y0 F3000  ; 移到打印板角落（X0 Y0 = 左前角）",
        "",
        "; 步骤4：横向推动模型",
        f"G91              ; 相对坐标",
        f"G1 {push_axis}{dir_sign}{push_distance:.1f} F{push_speed:.0f}",
        "",
        "; 步骤5：热端归位（可选，防止撞到收集容器）",
        "G90",
        "G28 X0 Y0        ; X/Y 归位",
        "",
        "; ===== EJECT 完成 =====",
    ]

    return "\n".join(gcode_lines)


def generate_eject_gcode_with_wipe(
    wipe_count: int = 3,
    wipe_distance: float = 30.0,
    wipe_speed: float = 1500.0,
    cooldown_temp: float = 60.0,
    z_lift: float = 20.0,
) -> str:
    """
    进阶版 Eject：先多次推刮（Wipe）松动模型，再推出。

    适合高粘附力的材料（PETG、VAAPR 表面）或大型扁平模型。

    参数：
        wipe_count:     推刮次数，默认 3 次
        wipe_distance:  每次推刮的距离，默认 30mm
        wipe_speed:     推刮速度，默认 1500mm/min
        cooldown_temp:  冷却目标温度
        z_lift:         Z 轴抬起高度
    """
    wipe_lines = []
    for i in range(wipe_count):
        wipe_lines.append(
            f"G1 X+{wipe_distance:.1f} F{wipe_speed:.0f}   ; 推刮 #{i+1}"
        )
        wipe_lines.append(
            f"G1 X-{wipe_distance:.1f} F{wipe_speed:.0f}   ; 回退 #{i+1}"
        )

    gcode_lines = [
        "; ===== H2C EJECT G-code（推刮版）=====",
        f"; 参数：wipe={wipe_count}x push speed={wipe_speed}mm/min cooldown={cooldown_temp}°C",
        "",
        "; 步骤1：冷却",
        f"M104 S0",
        f"M109 S{cooldown_temp}",
        "",
        "; 步骤2：抬 Z",
        "G91",
        f"G1 Z{z_lift:.1f} F3000",
        "",
        "; 步骤3：多次推刮松动模型",
        "G90",
        "G1 X0 Y0 F3000",
        "G91",
    ] + wipe_lines + [
        "",
        "; 步骤4：最终推出",
        "G90",
        "G1 X0 Y0 F3000",
        "G91",
        f"G1 X+{wipe_distance * 2:.1f} F1000",
        "",
        "; 归位",
        "G90",
        "G28 X0 Y0",
        "",
        "; ===== EJECT 完成 =====",
    ]

    return "\n".join(gcode_lines)


def generate_cooling_gcode(
    wait_temp: float = 50.0,
    fan_speed: int = 100,
) -> str:
    """
    仅冷却 G-code（不推动模型）。
    适合模型打印完后手动取出场景。

    参数：
        wait_temp:  等待冷却到目标温度（°C）
        fan_speed:  冷却风扇速度 0-100
    """
    gcode_lines = [
        "; ===== H2C 冷却 G-code =====",
        f"; 等待热端降到 {wait_temp}°C",
        "",
        "M106 S0              ; 先关闭风扇",
        f"M109 S{wait_temp}   ; 等待热端降温",
        f"M106 S{fan_speed * 2.55:.0f}  ; 全速吹风冷却",
        "G4 S30               ; 再等 30 秒",
        "M106 S0              ; 关风扇",
        "",
        "; 冷却完成，可取出模型",
    ]
    return "\n".join(gcode_lines)


# ============================================================
# H2C End G-code 模板（直接在 Bambu Studio 中使用）
# ============================================================

H2C_END_GCODE_TEMPLATE = """\
; ===== H2C End G-code =====
; 在这里粘贴 eject_gcode.py 生成的代码
; 以下是基础版 end G-code， eject 部分请用 generate_eject_gcode() 生成后替换

; 关闭热端
M104 S0

; 关闭热床
M140 S0

; 关闭风扇
M106 S0

; X/Y 归位
G28 X0 Y0

; 打印完成提示
M300 S1000 P500

; ===== 在此之上插入 EJECT G-code =====
"""


# ============================================================
# CLI 入口
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="H2C Eject G-code 生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：

  # 生成基础版 eject G-code
  python eject_gcode.py

  # 定制参数
  python eject_gcode.py --push-distance 80 --cooldown-temp 55 --push-axis Y

  # 推刮版（适合 PETG / 大面积扁平模型）
  python eject_gcode.py --wipe --wipe-count 5

  # 仅冷却
  python eject_gcode.py --cooling-only

  # 输出到文件
  python eject_gcode.py > eject_end.gcode
        """,
    )
    parser.add_argument(
        "--push-distance", type=float, default=50.0,
        help="推动距离（mm），默认 50",
    )
    parser.add_argument(
        "--push-speed", type=float, default=1000.0,
        help="推动速度（mm/min），默认 1000",
    )
    parser.add_argument(
        "--cooldown-temp", type=float, default=60.0,
        help="冷却目标温度（°C），默认 60",
    )
    parser.add_argument(
        "--z-lift", type=float, default=20.0,
        help="Z 轴抬起高度（mm），默认 20",
    )
    parser.add_argument(
        "--push-axis", choices=["X", "Y"], default="X",
        help="推动轴（默认 X，朝门方向）",
    )
    parser.add_argument(
        "--direction", choices=["positive", "negative"], default="positive",
        help="推动方向（默认 positive/+）",
    )
    parser.add_argument(
        "--wipe", action="store_true",
        help="使用推刮版（多次推刮松动）",
    )
    parser.add_argument(
        "--wipe-count", type=int, default=3,
        help="推刮次数（--wipe 时生效），默认 3",
    )
    parser.add_argument(
        "--cooling-only", action="store_true",
        help="仅生成冷却 G-code，不推动",
    )
    args = parser.parse_args()

    if args.cooling_only:
        gcode = generate_cooling_gcode()
    elif args.wipe:
        gcode = generate_eject_gcode_with_wipe(
            wipe_count=args.wipe_count,
            cooldown_temp=args.cooldown_temp,
            z_lift=args.z_lift,
        )
    else:
        gcode = generate_eject_gcode(
            push_distance=args.push_distance,
            push_speed=args.push_speed,
            cooldown_temp=args.cooldown_temp,
            z_lift=args.z_lift,
            push_axis=args.push_axis,
            direction=args.direction,
        )

    print(gcode)


if __name__ == "__main__":
    main()
