# 机械臂模块

> Cyber Bricks ESP32-C3 驱动，MQTT 指令控制，4 DOF 自由度，执行物理抓取动作

## 概述

机械臂模块是 0-1 机器人的执行层核心，负责"数字大脑→物理动作"的最终落地。Cyber Bricks 套件（含 ESP32-C3 主控板 XA003/XA004/XA005、电机驱动、舵机）作为执行节点，通过 MQTT 接收 OpenClaw Gateway 发来的指令，驱动舵机和电机完成抓取、放置等物理任务。Phase 4 阶段目标为跑通"OpenClaw → Cyber Bricks"的完整指令链路。

## 硬件参数

| 参数 | 规格 |
|------|------|
| 主控板 | Cyber Bricks ESP32-C3（XA003/XA004/XA005）|
| 自由度 | 4 DOF（四自由度） |
| 通信方式 | WiFi MQTT（QoS 1） |
| 控制频率 | 50Hz |
| 执行器 | 舵机（角度控制）+ 直流电机（速度控制）|
| 固件 | MicroPython |
| 控制架构 | OpenClaw Gateway → MQTT Broker → Jetson Nano → UART → Cyber Bricks |

## 技术方案

**通信架构**：
```
OpenClaw Gateway (MacBook)
    ↓ MQTT (QoS 1)
Jetson Nano (MQTT Broker + 指令解析)
    ↓ 有线 UART (115200)
Cyber Brick 1 (电机+舵机执行)
    ↓ 有线 UART
Cyber Brick 2 (备用执行节点)
```

**星闪 H3863 通信层（备选方案二）**：
- BearPi-Pico H3863（星闪 SLE 1.0，12Mbps，≤1ms 延迟）作为 Jetson Nano 与 Cyber Bricks 之间的无线通信层
- 星闪 SLE 替代 WiFi MQTT，将控制延迟从 <50ms 降低至 <5ms
- A+B 双设备配对：A 端（Jetson Nano 侧）存储 LUKS 密钥，B 端（随身端）做物理近场凭证

**MicroPython 固件**（Cyber Bricks 接收端）：
```python
import network, paho.mqtt.client as mqtt
from machine import Pin, PWM, UART
import ujson

uart = UART(1, 115200, tx=Pin(4), rx=Pin(5))
servo1 = PWM(Pin(15))
servo1.freq(50)
motor_in1 = Pin(12, Pin.OUT)
motor_in2 = Pin(13, Pin.OUT)

def set_servo(angle):
    duty = int(40 + angle * 95 / 90)
    servo1.duty(duty)

def set_motor(speed):
    if speed > 0:
        motor_in1.value(1); motor_in2.value(0)
    elif speed < 0:
        motor_in1.value(0); motor_in2.value(1)
    else:
        motor_in1.value(0); motor_in2.value(0)

def on_message(topic, msg):
    cmd = ujson.loads(msg)
    if cmd['type'] == 'servo': set_servo(cmd['angle'])
    elif cmd['type'] == 'motor': set_motor(cmd['speed'])
    elif cmd['type'] == 'stop': set_motor(0)

mqtt_client = mqtt.Client()
mqtt_client.on_message = lambda c,u,m: on_message(m.topic, m.payload)
mqtt_client.connect("192.168.x.x", 1883)
mqtt_client.subscribe("0-1/cyberbrick1")
mqtt_client.loop_start()
```

## 当前状态

| 项目 | 状态 |
|------|------|
| Cyber Bricks 硬件 | ✅ 已有 2 套（拓竹赠送）|
| MicroPython 固件 | ✅ 已编写，待烧录 |
| MQTT Broker (Jetson Nano) | ✅ 可部署 |
| OpenClaw → Cyber Bricks 指令链路 | 🔄 Phase 4：待实测 |
| 星闪 H3863 无线控制 | 🔄 备选方案，待采购 H3863 |
| 4 DOF 机械结构 | 🔄 待搭建（Phase 4）|

**Phase 4 里程碑**：
- [ ] Jetson Nano 安装并配置 MQTT Broker
- [ ] Cyber Bricks 烧录 MicroPython 固件
- [ ] UART 有线连接 Jetson Nano 与 Cyber Brick 1
- [ ] 实测 MQTT 指令 → 舵机/电机响应
- [ ] 有线 GPIO 应急停止验证

## 问题记录

**舵机抖转问题**
- **现象**：舵机接收到指令后出现非预期小幅抖动
- **原因**：信号线受到电磁干扰（ESP32-C3 PWM 输出与无线信号共地干扰）
- **解决方案**：
  1. 舵机信号线使用带屏蔽层的杜邦线
  2. 供电与信号地分开走线
  3. 信号线加磁环（EMI 抑制）
  4. 舵机单独供电（5V/2A），避免与 ESP32 共用电源
- **优先级**：中（不影响链路验证，影响运动精度）

**H3863 星闪通信延迟评估**
- WiFi MQTT 延迟：<50ms
- 星闪 SLE 延迟：<5ms（端到端 ≤1ms）
- 舵机响应时间：约 20-50ms
- **结论**：星闪对机械臂控制的延迟收益有限（舵机机械响应是瓶颈），WiFi MQTT 在 Phase 4 阶段足够

## 参考链接

- [ROBOT-SOP.md - Phase 4 运动控制模块](../harness/robot/ROBOT-SOP.md#phase-4运动控制模块)
- [ROBOT-SOP.md - 星闪通信模块 H3863 方案](../harness/robot/ROBOT-SOP.md#星闪通信模块bearpi-pico-h3863详细方案)
- [ROBOT-SOP.md - Cyber Bricks 问题排查](../harness/robot/ROBOT-SOP.md#cyber-bricks-问题)
