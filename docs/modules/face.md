# 面部表情模块

> 0-1 三元素「0」「-」「1」动态显示，MQTT 指令控制，拓竹 H2C 3D 打印面部支架

## 概述

面部表情系统是 0-1 机器人的情感交互窗口，通过「0」「-」「1」三个核心视觉元素的动态组合，传达机器人的当前状态和情绪。这三个元素分别对应：主眼睛（LED 点阵/IPS 屏幕）、间隔/嘴巴（NeoPixel 灯光带）、辅助信息（小型 OLED/LED）。Phase 5 阶段目标为实现完整的面部表情控制和 MQTT 指令对接。

## 硬件参数

| 组件 | 形态 | 功能 | 数量 |
|------|------|------|------|
| 「0」主眼睛 | LED 点阵（8×8/16×16）和 IPS 屏幕（SSD1306 OLED）| 动态表情显示 | 2（左眼+右眼）|
| 「-」间隔/嘴巴 | NeoPixel WS2812B 灯带 | 情绪光效（颜色+呼吸节奏）| 1 条（12 颗灯珠）|
| 「1」辅助信息 | 小型 OLED（128×32）或单色 LED | 状态指示、字符显示 | 1 |
| 面部支架 | 拓竹 H2C 3D 打印（PLA/PETG）| 结构承载 | 1 |
| 主控 | ESP32-C3（Cyber Bricks 系列）| 灯光控制 + MQTT 通信 | 1 |

## 0-1 三元素设计理念

0-1 面部由「0」「-」「1」三个符号构成，动态显示 AI 状态：

| 元素 | 显示内容 | 颜色/形态 |
|------|---------|---------|
| 「0」| 主眼睛，动态表情符号 | LED 点阵白色/淡蓝色 |
| 「-」| 线性灯光带，情绪光效 | NeoPixel RGB，呼吸节奏 |
| 「1」| 辅助状态信息 | OLED 绿色字符 |

**表情定义**（NeoPixel 灯光颜色）：

| 表情 | 颜色 | 说明 |
|------|------|------|
| idle（待机）| 淡蓝（0, 50, 100）| 缓慢呼吸闪烁 |
| thinking（思考）| 淡黄（50, 50, 0）| 稳定黄色 |
| happy（开心）| 绿色（0, 100, 50）| 快速闪烁 |
| sad（悲伤）| 淡紫（30, 0, 80）| 缓慢闪烁 |
| alert（警告）| 红色（100, 0, 0）| 快速闪烁 |

## 技术方案

**控制架构**：
```
OpenClaw Gateway
    ↓ MQTT (QoS 1)
ESP32-C3 主控（Cyber Bricks 系列）
    ├─ NeoPixel WS2812B → 灯光带（PWM GPIO15）
    ├─ I2C → OLED SSD1306（眼睛显示）
    └─ UART → 备用扩展
```

**拓竹 H2C 加工方案**：

| 零件 | 拓竹工具 | 材料 | 说明 |
|------|---------|------|------|
| 面部外壳 | H2C 3D 打印 | PLA | 基础结构 |
| 眼睛屏幕支架 | H2C 3D 打印 | PETG | 耐温要求 |
| 透光板 | Bambu Suite 激光切割 | 亚克力 3mm | 柔光效果 |
| 固定螺丝 | 拓竹配套 | M2/M3 螺丝 | 标准件 |

**MQTT 表情控制代码**：
```python
from neopixel import NeoPixel
from machine import Pin
import time, paho.mqtt.client as mqtt

N = 12  # NeoPixel 灯珠数量
pin = Pin(15, Pin.OUT)
strip = NeoPixel(pin, N)

EXPRESSIONS = {
    "idle":     [(0, 50, 100)],
    "thinking": [(50, 50, 0)],
    "happy":   [(0, 100, 50)],
    "sad":     [(30, 0, 80)],
    "alert":   [(100, 0, 0)],
}

def show_expression(name, duration=3.0):
    colors = EXPRESSIONS.get(name, EXPRESSIONS["idle"])
    for _ in range(int(duration * 10)):
        for i in range(N):
            strip[i] = colors[i % len(colors)]
        strip.write()
        time.sleep(0.1)

def on_message(client, userdata, msg):
    try:
        expr = msg.payload.decode()
        show_expression(expr)
    except Exception as e:
        print(f"表情指令解析失败: {e}")

client = mqtt.Client()
client.on_message = on_message
client.connect("192.168.x.x", 1883, 60)
client.subscribe("0-1/expression")
client.loop_start()
```

## 当前状态

| 项目 | 状态 |
|------|------|
| 0-1 三元素设计理念 | ✅ 确定 |
| 拓竹 H2C 面部支架方案 | ✅ 确定 |
| NeoPixel 灯带控制代码 | ✅ 已编写 |
| MQTT 表情指令订阅 | ✅ 已编写，待实测 |
| 面部结构 3D 建模 | 🔄 待设计 |
| OLED 眼睛显示 | 🔄 待集成 |
| ESP32-C3 主控板 | ✅ 可用（Cyber Bricks 系列）|

**Phase 5 里程碑**：
- [ ] 完成面部 3D 模型设计和 H2C 打印
- [ ] NeoPixel 灯带安装和颜色测试
- [ ] ESP32-C3 MQTT 固件烧录
- [ ] MQTT 指令 → 表情切换实测
- [ ] 与 OpenClaw 情感交互模块对接

## 问题记录

**NeoPixel 颜色不均匀**
- **现象**：灯带颜色不一致，部分灯珠亮度偏低
- **原因**：WS2812B 数据信号线过长导致衰减
- **解决方案**：
  1. 信号线控制在 1 米以内
  2. 灯带供电单独接 5V/3A 电源（不要从 ESP32 取电）
  3. 信号线加 330Ω 电阻（ESD 保护）

**OLED 显示雪花点**
- **现象**：SSD1306 OLED 显示乱码/雪花点
- **原因**：I2C 通信受 ESP32 WiFi 干扰
- **解决方案**：
  1. I2C 上拉电阻 4.7kΩ 改 10kΩ（减弱干扰）
  2. 显示更新时短暂关闭 WiFi
  3. 降低 I2C 速率（100kHz 而非 400kHz）

## 参考链接

- [ROBOT-SOP.md - Phase 5 面部表情系统](../harness/robot/ROBOT-SOP.md#phase-5面部表情系统)
- [ROBOT-SOP.md - 拓竹软件生态](../harness/robot/ROBOT-SOP.md#拓竹软件生态)
